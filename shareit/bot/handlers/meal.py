from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import (
    add_meal, add_meal_contribution, add_meal_absence,
    get_meals, get_meal_contributions, get_meal_by_number,
    get_meal_by_name, get_active_trip, get_family, get_meal_grouping_members,
)
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family, reply_ephemeral, get_lang


def _format_grouping_summary(members: list[dict]) -> tuple[str, float]:
    lines = []
    total_weight = 0.0
    for m in members:
        if m.get("is_active", 1) != 0:
            weight = m.get("weight", 0.0)
            total_weight += weight
            lines.append(f"  • {m['family_name']} (weight: {weight})")
        else:
            lines.append(f"  • {m['family_name']} (0) [Skipped]")
    return "\n".join(lines) if lines else "_No members_", total_weight


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

    members = await get_meal_grouping_members(db_path, meal_id)
    members_list_str, total_weight = _format_grouping_summary(members)
    grouping_summary_str = t("grouping_header", lang, number=meal_number, name=name, members_list=members_list_str, total_weight=total_weight)

    context.user_data["last_action"] = {"type": "meal", "meal_id": meal_id, "trip_id": trip["id"]}
    if amount:
        base_msg = t("meal_logged", lang, number=meal_number, name=name, amount=amount, family=family["name"])
    else:
        base_msg = t("meal_created", lang, number=meal_number, name=name)

    await reply_ephemeral(update, context, base_msg + grouping_summary_str, parse_mode="Markdown")


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
        await update.effective_message.reply_text(
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
    """Handle plain text inputs for pending meal description or contribute amount."""
    import time as _time

    # Check pending meal description prompt first
    pending_desc = context.user_data.get("pending_meal_desc")
    if (
        pending_desc
        and _time.time() - pending_desc.get("timestamp", 0) <= 120
        and update.effective_chat.id == pending_desc.get("chat_id")
    ):
        text = update.message.text.strip()
        category = pending_desc.get("category", "Meal")

        is_amount = False
        try:
            val = float(text)
            is_amount = True
        except ValueError:
            is_amount = False

        if is_amount and category != "Custom" and context.user_data.get("pending_meal_name"):
            # User typed an amount directly (e.g. "50")
            context.user_data.pop("pending_meal_desc", None)
            amount_val = val if val > 0 else None
            name = context.user_data.pop("pending_meal_name", category)
            trip, family, lang = await require_family(update, context)
            if family:
                db_path = context.bot_data["db_path"]
                meal_id = await add_meal(db_path, trip["id"], name, family["id"], amount_val)
                meals = await get_meals(db_path, trip["id"])
                meal = next((m for m in meals if m["id"] == meal_id), None)
                meal_number = meal["meal_number"] if meal else "?"
                members = await get_meal_grouping_members(db_path, meal_id)
                members_list_str, total_weight = _format_grouping_summary(members)
                grouping_summary_str = t("grouping_header", lang, number=meal_number, name=name, members_list=members_list_str, total_weight=total_weight)
                base_msg = t("meal_logged", lang, number=meal_number, name=name, amount=val, family=family["name"]) if amount_val else t("meal_created", lang, number=meal_number, name=name)
                await update.effective_message.reply_text(base_msg + grouping_summary_str, parse_mode="Markdown")
            return
        elif not is_amount:
            # User typed a description string (e.g. "Pancakes & Bacon")
            context.user_data.pop("pending_meal_desc", None)
            name = text if category == "Custom" else f"{category} - {text}"
            context.user_data["pending_meal_name"] = name

            lang = await get_lang(update, context)
            buttons = []
            row = []
            for amt in AMOUNT_PRESETS:
                label = f"${int(amt)}"
                row.append(InlineKeyboardButton(label, callback_data=f"pamt_{amt:.2f}"))
                if len(row) == 3:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)
            buttons.append([InlineKeyboardButton("Create Slot ($0)", callback_data="pamt_0.0")])

            await update.effective_message.reply_text(
                t("select_amount_preset", lang, name=name),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
            return

    # Check pending contribute amount
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
    await update.effective_message.reply_text(
        t("contribute_added", lang, number=meal_number, name=meal_name, amount=amount, total=total)
    )
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
    await update.effective_message.reply_text(t("skip_prompt", lang), reply_markup=InlineKeyboardMarkup(buttons))


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
        members = await get_meal_grouping_members(db_path, meal_id)
        members_list_str, total_weight = _format_grouping_summary(members)
        msg_text = t(
            "skip_confirmed_with_grouping", lang,
            family=family["name"],
            number=meal["meal_number"],
            name=meal["name"],
            members_list=members_list_str,
            total_weight=total_weight,
        )
        await query.edit_message_text(msg_text, parse_mode="Markdown")
        # Schedule deletion of the confirmation message
        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
            data={"chat_id": chat_id, "message_id": query.message.message_id},
            name=f"ephemeral_{chat_id}_{query.message.message_id}",
        )


MEAL_PRESETS = [
    [("Breakfast 🥞", "pmeal_Breakfast"), ("Lunch 🥪", "pmeal_Lunch")],
    [("Dinner 🍖", "pmeal_Dinner"), ("Snacks 🍎", "pmeal_Snacks")],
    [("Drinks 🥤", "pmeal_Drinks"), ("Custom ✏️", "pmeal_Custom")],
]

AMOUNT_PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0]


async def prompt_meal_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with meal name preset buttons."""
    from bot.handlers._helpers import get_lang
    lang = await get_lang(update, context)
    buttons = [
        [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
        for row in MEAL_PRESETS
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            t("meal_select_preset", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.effective_message.reply_text(
            t("meal_select_preset", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )


async def meal_preset_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle meal category preset selection and prompt for description."""
    import time as _time
    from bot.handlers._helpers import get_lang

    query = update.callback_query
    await query.answer()
    meal_name = query.data.replace("pmeal_", "")
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    if meal_name == "Custom":
        context.user_data["pending_meal_desc"] = {
            "category": "Custom",
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }
        await query.edit_message_text(t("meal_ask_custom_desc", lang), parse_mode="Markdown")
    else:
        context.user_data["pending_meal_desc"] = {
            "category": meal_name,
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }
        buttons = [[InlineKeyboardButton(t("btn_skip_desc", lang), callback_data="pdesc_skip")]]
        await query.edit_message_text(
            t("meal_ask_desc_explicit", lang, category=meal_name),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )


async def meal_skip_desc_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle skipping meal description prompt."""
    from bot.handlers._helpers import get_lang

    query = update.callback_query
    await query.answer()

    pending_desc = context.user_data.pop("pending_meal_desc", {})
    category = pending_desc.get("category", "Meal")
    context.user_data["pending_meal_name"] = category

    lang = await get_lang(update, context)
    buttons = []
    row = []
    for amt in AMOUNT_PRESETS:
        label = f"${int(amt)}"
        row.append(InlineKeyboardButton(label, callback_data=f"pamt_{amt:.2f}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Create Slot ($0)", callback_data="pamt_0.0")])

    await query.edit_message_text(
        t("select_amount_preset", lang, name=category),
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def meal_amount_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle meal amount preset selection."""
    query = update.callback_query
    await query.answer()
    try:
        amount = float(query.data.replace("pamt_", ""))
    except ValueError:
        return

    name = context.user_data.pop("pending_meal_name", "Meal")
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]
    amount_val = amount if amount > 0 else None
    meal_id = await add_meal(db_path, trip["id"], name, family["id"], amount_val)

    meals = await get_meals(db_path, trip["id"])
    meal = next((m for m in meals if m["id"] == meal_id), None)
    meal_number = meal["meal_number"] if meal else "?"

    members = await get_meal_grouping_members(db_path, meal_id)
    members_list_str, total_weight = _format_grouping_summary(members)
    grouping_summary_str = t("grouping_header", lang, number=meal_number, name=name, members_list=members_list_str, total_weight=total_weight)

    if amount_val:
        base_msg = t("meal_logged", lang, number=meal_number, name=name, amount=amount_val, family=family["name"])
    else:
        base_msg = t("meal_created", lang, number=meal_number, name=name)

    await query.edit_message_text(base_msg + grouping_summary_str, parse_mode="Markdown")

