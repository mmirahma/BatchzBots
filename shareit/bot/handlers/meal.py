from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import (
    add_meal, add_meal_contribution, add_meal_absence,
    get_meals, get_meal_contributions, get_meal_by_number,
    get_meal_by_name, get_active_trip, get_family,
)
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family


async def meal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /meal <name> [amount] command. Without amount, creates an empty meal slot."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args:
        await update.message.reply_text(t("usage_meal", lang))
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
        await update.message.reply_text(t("usage_meal", lang))
        return

    db_path = context.bot_data["db_path"]

    # If a meal with this name already exists, treat as a contribution
    existing_meal = await get_meal_by_name(db_path, trip["id"], name)
    if existing_meal:
        if amount is None:
            # Meal already exists, nothing to do
            await update.message.reply_text(t("meal_already_exists", lang, number=existing_meal["meal_number"], name=existing_meal["name"]))
            return
        await add_meal_contribution(db_path, existing_meal["id"], family["id"], amount)
        contributions = await get_meal_contributions(db_path, existing_meal["id"])
        total = sum(c["amount"] for c in contributions)
        context.user_data["last_action"] = {"type": "contribution", "meal_id": existing_meal["id"], "family_id": family["id"], "trip_id": trip["id"]}
        await update.message.reply_text(
            t("contribution_added", lang, family=family["name"], amount=amount, number=existing_meal["meal_number"], name=existing_meal["name"], total=total)
        )
        return

    meal_id = await add_meal(db_path, trip["id"], name, family["id"], amount)

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)
    meal_number = meal["meal_number"] if meal else "?"

    context.user_data["last_action"] = {"type": "meal", "meal_id": meal_id, "trip_id": trip["id"]}
    if amount:
        await update.message.reply_text(
            t("meal_logged", lang, number=meal_number, name=name, amount=amount, family=family["name"])
        )
    else:
        await update.message.reply_text(
            t("meal_created", lang, number=meal_number, name=name)
        )


async def contribute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /contribute <meal#> <amount> command."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(t("usage_contribute", lang))
        return

    try:
        meal_number = int(context.args[0].lstrip("#"))
        amount = float(context.args[1])
    except (ValueError, IndexError):
        await update.message.reply_text(t("usage_contribute", lang))
        return

    if amount <= 0:
        await update.message.reply_text(t("usage_contribute", lang))
        return

    db_path = context.bot_data["db_path"]
    meal = await get_meal_by_number(db_path, trip["id"], meal_number)
    if not meal:
        await update.message.reply_text(t("meal_not_found", lang, number=meal_number))
        return

    await add_meal_contribution(db_path, meal["id"], family["id"], amount)
    contributions = await get_meal_contributions(db_path, meal["id"])
    total = sum(c["amount"] for c in contributions)

    context.user_data["last_action"] = {"type": "contribution", "meal_id": meal["id"], "family_id": family["id"], "trip_id": trip["id"]}
    await update.message.reply_text(
        t("contribution_added", lang, family=family["name"], amount=amount, number=meal_number, name=meal["name"], total=total)
    )


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /skip command — shows inline buttons for meal selection."""
    if not await require_group(update):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]
    meals = await get_meals(db_path, trip["id"])

    if not meals:
        await update.message.reply_text(t("nothing_to_settle", lang))
        return

    buttons = [
        [InlineKeyboardButton(f"#{m['meal_number']} {m['name']}", callback_data=f"skip_{m['id']}")]
        for m in meals
    ]
    await update.message.reply_text(t("skip_prompt", lang), reply_markup=InlineKeyboardMarkup(buttons))


async def skip_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button press for meal skip."""
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
    meal_id = int(query.data.replace("skip_", ""))
    await add_meal_absence(db_path, meal_id, family["id"])

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)

    context.user_data["last_action"] = {"type": "absence", "meal_id": meal_id, "family_id": family["id"], "trip_id": trip["id"]}
    if meal:
        await query.edit_message_text(
            t("skip_confirmed", lang, family=family["name"], number=meal["meal_number"], name=meal["name"])
        )
