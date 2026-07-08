from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import (
    add_meal, add_meal_contribution, add_meal_absence,
    get_meals, get_meal_contributions, get_meal_by_number,
    get_meal_by_name, get_active_trip, get_family,
)
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family, reply_ephemeral


async def meal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /meal <name> [amount] command. Without amount, creates an empty meal slot."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args:
        await reply_ephemeral(update, context, t("usage_meal", lang))
        return

    # Try to parse last arg as amount
    amount = None
    try:
        amount = float(context.args[-1])
        name = " ".join(context.args[:-1])
        if not name:
            # Only a number was provided, treat it as the name
            name = context.args[-1]
            amount = None
    except ValueError:
        name = " ".join(context.args)

    if amount is not None and amount <= 0:
        await reply_ephemeral(update, context, t("usage_meal", lang))
        return

    db_path = context.bot_data["db_path"]

    # If a meal with this name already exists, treat as a contribution
    existing_meal = await get_meal_by_name(db_path, trip["id"], name)
    if existing_meal:
        if amount is None:
            # Meal already exists, nothing to do
            await reply_ephemeral(update, context, t("meal_already_exists", lang, number=existing_meal["meal_number"], name=existing_meal["name"]))
            return
        # Duplicate check
        contributions = await get_meal_contributions(db_path, existing_meal["id"])
        if any(c["family_id"] == family["id"] and c["amount"] == amount for c in contributions):
            await reply_ephemeral(update, context, t("duplicate_contribution", lang, number=existing_meal["meal_number"], amount=amount))
            return
        await add_meal_contribution(db_path, existing_meal["id"], family["id"], amount)
        contributions = await get_meal_contributions(db_path, existing_meal["id"])
        total = sum(c["amount"] for c in contributions)
        context.user_data["last_action"] = {"type": "contribution", "meal_id": existing_meal["id"], "family_id": family["id"], "trip_id": trip["id"]}
        await reply_ephemeral(update, context,
            t("contribution_added", lang, family=family["name"], amount=amount, number=existing_meal["meal_number"], name=existing_meal["name"], total=total)
        )
        return

    meal_id = await add_meal(db_path, trip["id"], name, family["id"], amount)

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)
    meal_number = meal["meal_number"] if meal else "?"

    context.user_data["last_action"] = {"type": "meal", "meal_id": meal_id, "trip_id": trip["id"]}
    if amount:
        await reply_ephemeral(update, context,
            t("meal_logged", lang, number=meal_number, name=name, amount=amount, family=family["name"])
        )
    else:
        await reply_ephemeral(update, context,
            t("meal_created", lang, number=meal_number, name=name)
        )


async def contribute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contribute [meal#] [amount] command. Shows meal buttons if no args."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]

    if not context.args:
        # Show meal selection buttons
        meals = await get_meals(db_path, trip["id"])
        if not meals:
            await reply_ephemeral(update, context, t("no_meals_yet", lang))
            return
        buttons = [
            [InlineKeyboardButton(f"#{m['meal_number']} {m['name']}", callback_data=f"contrib_{m['meal_number']}")]
            for m in meals
        ]
        await update.message.reply_text(
            t("contribute_select_meal", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    if len(context.args) < 2:
        await reply_ephemeral(update, context, t("usage_contribute", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
        amount = float(context.args[1])
    except (ValueError, IndexError):
        await reply_ephemeral(update, context, t("usage_contribute", lang))
        return

    if amount <= 0:
        await reply_ephemeral(update, context, t("usage_contribute", lang))
        return

    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await reply_ephemeral(update, context, t("meal_not_found", lang, number=meal_number))
        return

    # Duplicate check: same family, same meal, same amount
    contributions = await get_meal_contributions(db_path, meal["id"])
    if any(c["family_id"] == family["id"] and c["amount"] == amount for c in contributions):
        await reply_ephemeral(update, context, t("duplicate_contribution", lang, number=meal_number, amount=amount))
        return

    await add_meal_contribution(db_path, meal["id"], family["id"], amount)
    contributions = await get_meal_contributions(db_path, meal["id"])
    total = sum(c["amount"] for c in contributions)

    context.user_data["last_action"] = {"type": "contribution", "meal_id": meal["id"], "family_id": family["id"], "trip_id": trip["id"]}
    await reply_ephemeral(update, context,
        t("contribution_added", lang, family=family["name"], amount=amount, number=meal_number, name=meal["name"], total=total)
    )


async def contribute_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for meal selection in /contribute."""
    from datetime import timedelta
    from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS

    query = update.callback_query
    await query.answer()

    try:
        meal_number = int(query.data.replace("contrib_", ""))
    except ValueError:
        return

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    family = await get_family(db_path, trip["id"], user_id)
    lang = family.get("language", "en") if family else "en"

    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        return

    # Store pending contribution in user_data with timestamp
    import time as _time
    context.user_data["pending_contribute"] = {
        "meal_id": meal["id"],
        "meal_number": meal_number,
        "meal_name": meal["name"],
        "trip_id": trip["id"],
        "chat_id": chat_id,
        "timestamp": _time.time(),
    }

    await query.edit_message_text(
        t("contribute_ask_amount", lang, name=meal["name"], number=meal_number)
    )
    # Schedule deletion of prompt
    context.job_queue.run_once(
        _delete_message_job,
        when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
        data={"chat_id": chat_id, "message_id": query.message.message_id},
        name=f"ephemeral_{chat_id}_{query.message.message_id}",
    )


async def contribute_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text amount after meal selection for /contribute."""
    import time as _time

    pending = context.user_data.get("pending_contribute")
    if not pending:
        return

    # Expire after 2 minutes
    if _time.time() - pending.get("timestamp", 0) > 120:
        context.user_data.pop("pending_contribute", None)
        return

    # Only process in the same chat
    if update.effective_chat.id != pending["chat_id"]:
        return

    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        return  # Not a number, ignore silently

    if amount <= 0:
        await reply_ephemeral(update, context, t("usage_contribute", "en"))
        return

    db_path = context.bot_data["db_path"]
    trip_id = pending["trip_id"]
    user_id = update.effective_user.id

    family = await get_family(db_path, trip_id, user_id)
    if not family:
        context.user_data.pop("pending_contribute", None)
        return

    lang = family.get("language", "en")
    meal_id = pending["meal_id"]
    meal_number = pending["meal_number"]
    meal_name = pending["meal_name"]

    # Duplicate check
    contributions = await get_meal_contributions(db_path, meal_id)
    if any(c["family_id"] == family["id"] and c["amount"] == amount for c in contributions):
        await reply_ephemeral(update, context, t("duplicate_contribution", lang, number=meal_number, amount=amount))
        context.user_data.pop("pending_contribute", None)
        return

    await add_meal_contribution(db_path, meal_id, family["id"], amount)
    contributions = await get_meal_contributions(db_path, meal_id)
    total = sum(c["amount"] for c in contributions)

    context.user_data["last_action"] = {"type": "contribution", "meal_id": meal_id, "family_id": family["id"], "trip_id": trip_id}
    context.user_data.pop("pending_contribute", None)

    await reply_ephemeral(update, context,
        t("contribution_added", lang, family=family["name"], amount=amount, number=meal_number, name=meal_name, total=total)
    )


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skip command — shows inline buttons for meal selection."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]
    meals = await get_meals(db_path, trip["id"])

    if not meals:
        await reply_ephemeral(update, context, t("nothing_to_settle", lang))
        return

    buttons = [
        [InlineKeyboardButton(f"#{m['meal_number']} {m['name']}", callback_data=f"skip_{m['id']}")]
        for m in meals
    ]
    await update.message.reply_text(t("skip_prompt", lang), reply_markup=InlineKeyboardMarkup(buttons))


async def skip_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for meal skip."""
    from datetime import timedelta
    from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS

    query = update.callback_query
    await query.answer()

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return

    lang = family.get("language", "en")
    try:
        meal_id = int(query.data.replace("skip_", ""))
    except ValueError:
        return
    await add_meal_absence(db_path, meal_id, family["id"])

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)

    context.user_data["last_action"] = {"type": "absence", "meal_id": meal_id, "family_id": family["id"], "trip_id": trip["id"]}
    if meal:
        await query.edit_message_text(
            t("skip_confirmed", lang, family=family["name"], number=meal["meal_number"], name=meal["name"])
        )
        # Schedule deletion of the confirmation message
        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
            data={"chat_id": chat_id, "message_id": query.message.message_id},
            name=f"ephemeral_{chat_id}_{query.message.message_id}",
        )
