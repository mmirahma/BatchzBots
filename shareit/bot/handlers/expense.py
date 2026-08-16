from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import add_shared_expense
from bot.i18n import t
from bot.handlers._helpers import require_group, require_family, reply_ephemeral, get_lang

EXPENSE_PRESETS = [
    [("Firewood 🪵", "pexp_Firewood"), ("Park Entry 🏞", "pexp_Park Entry")],
    [("Groceries 🛒", "pexp_Groceries"), ("Ice 🧊", "pexp_Ice")],
    [("Campsite Fee ⛺️", "pexp_Campsite Fee"), ("Gas / Fuel ⛽️", "pexp_Gas")],
    [("Custom ✏️", "pexp_Custom")],
]

AMOUNT_PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0]


async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /expense <description> <amount> command."""
    if not await require_group(update, context):
        return
    trip, family, lang = await require_family(update, context)
    if not family:
        return

    if not context.args or len(context.args) < 2:
        await prompt_expense_preset(update, context)
        return

    try:
        amount = float(context.args[-1])
    except ValueError:
        await reply_ephemeral(update, context, t("usage_expense", lang))
        return

    if amount <= 0:
        await reply_ephemeral(update, context, t("usage_expense", lang))
        return

    description = " ".join(context.args[:-1])
    db_path = context.bot_data["db_path"]
    expense_id = await add_shared_expense(db_path, trip["id"], family["id"], description, amount)

    context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
    await reply_ephemeral(update, context,
        t("expense_logged", lang, description=description, amount=amount, family=family["name"])
    )


async def prompt_expense_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with unified expense menu: existing meals, new meal, or general expense."""
    from bot.db import get_active_trip, get_meals
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    meals = await get_meals(db_path, trip["id"]) if trip else []

    buttons = []
    # Add buttons for existing meals if any
    for m in meals:
        label = f"💳 #{m['meal_number']} {m['name']}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"contrib_{m['meal_number']}")])

    buttons.append([InlineKeyboardButton(t("btn_new_meal_expense", lang), callback_data="exp_new_meal")])
    buttons.append([InlineKeyboardButton(t("btn_general_expense", lang), callback_data="exp_general")])

    title = t("expense_menu_title", lang)
    if update.callback_query:
        await update.callback_query.edit_message_text(title, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, title, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def expense_menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle choice between New Meal Expense and General Shared Expense."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "exp_new_meal":
        from bot.handlers.meal import prompt_meal_preset
        await prompt_meal_preset(update, context)
    elif data == "exp_general":
        await prompt_general_expense_categories(update, context)


async def prompt_general_expense_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show general shared expense category preset buttons."""
    lang = await get_lang(update, context)
    buttons = [
        [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
        for row in EXPENSE_PRESETS
    ]
    await update.callback_query.edit_message_text(
        t("expense_select_preset", lang), reply_markup=InlineKeyboardMarkup(buttons)
    )


async def expense_preset_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle expense preset category selection."""
    import time as _time
    query = update.callback_query
    await query.answer()
    category = query.data.replace("pexp_", "")
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    if category == "Custom":
        context.user_data["pending_expense_prompt"] = {
            "category": "Custom",
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }
        await query.edit_message_text(t("expense_ask_custom_desc", lang), parse_mode="Markdown")
    else:
        context.user_data["pending_expense_desc"] = category
        context.user_data["pending_expense_prompt"] = {
            "category": category,
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }
        context.user_data["pending_expense_amount_prompt"] = {
            "desc": category,
            "chat_id": chat_id,
            "timestamp": _time.time(),
        }

        buttons = []
        row = []
        for amt in AMOUNT_PRESETS:
            label = f"${int(amt)}"
            row.append(InlineKeyboardButton(label, callback_data=f"pexpamt_{amt:.2f}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        await query.edit_message_text(
            t("expense_ask_desc", lang, category=category),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )


async def expense_amount_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle expense amount preset selection."""
    query = update.callback_query
    await query.answer()
    try:
        amount = float(query.data.replace("pexpamt_", ""))
    except ValueError:
        return

    description = context.user_data.pop("pending_expense_desc", "Shared Expense")
    context.user_data.pop("pending_expense_amount_prompt", None)
    context.user_data.pop("pending_expense_prompt", None)

    trip, family, lang = await require_family(update, context)
    if not family:
        return

    db_path = context.bot_data["db_path"]
    expense_id = await add_shared_expense(db_path, trip["id"], family["id"], description, amount)

    context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
    await query.edit_message_text(
        t("expense_logged", lang, description=description, amount=amount, family=family["name"])
    )

