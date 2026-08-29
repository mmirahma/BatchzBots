"""Handler for interactive 'Edit My Expenses' workflow."""

import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import (
    get_active_trip, get_family, get_family_expenses, get_all_trip_expenses,
    update_shared_expense_amount, delete_shared_expense,
    update_meal_contribution_amount_by_id, delete_meal_contribution_by_id,
)
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral


async def edit_my_expenses_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all logged expenses for the user's family with inline edit buttons."""
    if not await require_group(update, context):
        return

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        await reply_ephemeral(update, context, t("join_first", lang))
        return

    expenses = await get_family_expenses(db_path, trip["id"], family["id"])
    if not expenses:
        await reply_ephemeral(update, context, t("no_expenses_to_edit", lang))
        return

    buttons = []
    for item in expenses:
        item_id = item["item_id"]
        item_type = item["type"]
        amount = item["amount"]
        if item_type == "meal":
            label = f"🍽 #{item['meal_number']} {item['item_name']} (${amount:.2f})"
        else:
            label = f"🪵 {item['item_name']} (${amount:.2f})"
        cb_data = f"edexp_{item_type}_{item_id}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])

    reply_markup = InlineKeyboardMarkup(buttons)
    msg_text = t("edit_expenses_title", lang)

    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, msg_text, reply_markup=reply_markup, parse_mode="Markdown")


async def edit_expense_select_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle selecting a specific expense to edit from the inline list (edexp_meal_12 or edexp_expense_5)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    if len(parts) != 3:
        return
    item_type = parts[1]
    try:
        item_id = int(parts[2])
    except ValueError:
        return

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return
    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return

    expenses = await get_family_expenses(db_path, trip["id"], family["id"])
    target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
    if not target_item:
        await query.edit_message_text(t("no_expenses_to_edit", lang))
        return

    # Set pending edit state for text input (if user types a custom amount)
    context.user_data["pending_edit_expense"] = {
        "type": item_type,
        "item_id": item_id,
        "name": target_item["item_name"],
        "chat_id": chat_id,
        "timestamp": time.time(),
    }

    # Build preset amount buttons
    PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0]
    buttons = []
    row = []
    for amt in PRESETS:
        label = f"${int(amt)}"
        cb_data = f"edexpamt_{item_type}_{item_id}_{amt:.2f}"
        row.append(InlineKeyboardButton(label, callback_data=cb_data))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(t("btn_delete_expense", lang), callback_data=f"edexpdel_{item_type}_{item_id}")])
    buttons.append([InlineKeyboardButton(t("btn_back_to_list", lang), callback_data="edexp_list")])

    if item_type == "meal":
        item_title = f"Meal/Event #{target_item['meal_number']} '{target_item['item_name']}'"
    else:
        item_title = f"Expense '{target_item['item_name']}'"

    msg_text = t("edit_expense_prompt", lang, name=item_title, amount=target_item["amount"])
    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def edit_expense_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle amount preset selection or delete action for an expense item."""
    query = update.callback_query
    await query.answer()

    data = query.data
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if data == "edexp_list":
        await edit_my_expenses_handler(update, context)
        return

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return
    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return

    if data.startswith("edexpdel_"):
        # Delete item
        parts = data.split("_")
        item_type = parts[1]
        item_id = int(parts[2])
        expenses = await get_family_expenses(db_path, trip["id"], family["id"])
        target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
        item_name = target_item["item_name"] if target_item else "Expense"

        if item_type == "meal":
            await delete_meal_contribution_by_id(db_path, item_id)
        else:
            await delete_shared_expense(db_path, item_id)

        context.user_data.pop("pending_edit_expense", None)
        await reply_ephemeral(update, context, t("expense_deleted", lang, name=item_name))
        await edit_my_expenses_handler(update, context)
        return

    if data.startswith("edexpamt_"):
        # Update amount preset
        parts = data.split("_")
        item_type = parts[1]
        item_id = int(parts[2])
        amount = float(parts[3])

        expenses = await get_family_expenses(db_path, trip["id"], family["id"])
        target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
        item_name = target_item["item_name"] if target_item else "Expense"

        if amount <= 0:
            if item_type == "meal":
                await delete_meal_contribution_by_id(db_path, item_id)
            else:
                await delete_shared_expense(db_path, item_id)
            await reply_ephemeral(update, context, t("expense_deleted", lang, name=item_name))
        else:
            if item_type == "meal":
                await update_meal_contribution_amount_by_id(db_path, item_id, amount)
            else:
                await update_shared_expense_amount(db_path, item_id, amount)
            await reply_ephemeral(update, context, t("expense_updated", lang, name=item_name, amount=amount))

        context.user_data.pop("pending_edit_expense", None)
        await edit_my_expenses_handler(update, context)
        return


async def pending_edit_expense_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text input when user or admin types a custom amount during edit expense flow."""
    pending = context.user_data.get("pending_edit_expense")
    if not pending:
        return False

    # Expire after 2 minutes
    if time.time() - pending.get("timestamp", 0) > 120:
        context.user_data.pop("pending_edit_expense", None)
        return False

    if update.effective_chat.id != pending["chat_id"]:
        return False

    text = update.message.text.strip()
    try:
        amount = float(text)
    except ValueError:
        return False  # Not a number

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    item_type = pending["type"]
    item_id = pending["item_id"]
    item_name = pending["name"]
    is_admin = pending.get("is_admin", False)

    if amount <= 0:
        if item_type == "meal":
            await delete_meal_contribution_by_id(db_path, item_id)
        else:
            await delete_shared_expense(db_path, item_id)
        await reply_ephemeral(update, context, t("expense_deleted", lang, name=item_name))
    else:
        if item_type == "meal":
            await update_meal_contribution_amount_by_id(db_path, item_id, amount)
        else:
            await update_shared_expense_amount(db_path, item_id, amount)
        await reply_ephemeral(update, context, t("expense_updated", lang, name=item_name, amount=amount))

    context.user_data.pop("pending_edit_expense", None)
    if is_admin:
        await admin_edit_all_expenses_handler(update, context)
    else:
        await edit_my_expenses_handler(update, context)
    return True


async def admin_edit_all_expenses_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display all logged expenses across all families for the trip with admin edit buttons."""
    if not await require_group(update, context):
        return

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    from bot.handlers._helpers import is_admin_or_owner
    if not await is_admin_or_owner(context.bot, chat_id, update.effective_user):
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(t("admin_only", lang))
        else:
            await reply_ephemeral(update, context, t("admin_only", lang))
        return

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        if update.callback_query:
            await update.callback_query.edit_message_text(t("no_active_trip", lang))
        else:
            await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    expenses = await get_all_trip_expenses(db_path, trip["id"])
    if not expenses:
        empty_text = t("no_expenses_to_edit", lang)
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back_admin", lang), callback_data="menu_admin")]])
        if update.callback_query:
            await update.callback_query.edit_message_text(empty_text, reply_markup=back_btn)
        else:
            await reply_ephemeral(update, context, empty_text, reply_markup=back_btn)
        return

    buttons = []
    for item in expenses:
        item_id = item["item_id"]
        item_type = item["type"]
        amount = item["amount"]
        fam_name = item.get("family_name", "Family")
        if item_type == "meal":
            label = f"🍽 #{item['meal_number']} {item['item_name']} (${amount:.2f}) — {fam_name}"
        else:
            label = f"🪵 {item['item_name']} (${amount:.2f}) — {fam_name}"
        cb_data = f"admexp_{item_type}_{item_id}"
        buttons.append([InlineKeyboardButton(label, callback_data=cb_data)])

    buttons.append([InlineKeyboardButton(t("btn_back_admin", lang), callback_data="menu_admin")])
    reply_markup = InlineKeyboardMarkup(buttons)
    msg_text = t("admin_edit_expenses_title", lang, trip_name=trip["name"])

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(msg_text, reply_markup=reply_markup, parse_mode="Markdown")
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        await reply_ephemeral(update, context, msg_text, reply_markup=reply_markup, parse_mode="Markdown")


async def admin_expense_select_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle selecting a specific expense across any family to edit (admexp_meal_12 or admexp_expense_5)."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")
    if len(parts) != 3:
        return
    item_type = parts[1]
    try:
        item_id = int(parts[2])
    except ValueError:
        return

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    from bot.handlers._helpers import is_admin_or_owner
    if not await is_admin_or_owner(context.bot, chat_id, update.effective_user):
        await query.edit_message_text(t("admin_only", lang))
        return

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await query.edit_message_text(t("no_active_trip", lang))
        return

    expenses = await get_all_trip_expenses(db_path, trip["id"])
    target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
    if not target_item:
        await query.edit_message_text(t("no_expenses_to_edit", lang))
        return

    # Set pending edit state for text input (if admin types a custom amount)
    context.user_data["pending_edit_expense"] = {
        "type": item_type,
        "item_id": item_id,
        "name": target_item["item_name"],
        "chat_id": chat_id,
        "timestamp": time.time(),
        "is_admin": True,
    }

    # Build preset amount buttons
    PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0, 200.0]
    buttons = []
    row = []
    for amt in PRESETS:
        label = f"${int(amt)}"
        cb_data = f"admexpamt_{item_type}_{item_id}_{amt:.2f}"
        row.append(InlineKeyboardButton(label, callback_data=cb_data))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(t("btn_delete_expense", lang), callback_data=f"admexpdel_{item_type}_{item_id}")])
    buttons.append([InlineKeyboardButton(t("btn_back_all_expenses", lang), callback_data="admexp_list")])

    if item_type == "meal":
        item_title = f"Meal/Event #{target_item['meal_number']} '{target_item['item_name']}'"
    else:
        item_title = f"Expense '{target_item['item_name']}'"

    fam_name = target_item.get("family_name", "Family")
    msg_text = t("admin_edit_expense_prompt", lang, name=item_title, family_name=fam_name, amount=target_item["amount"])
    await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def admin_expense_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle amount preset selection or delete action for any family's expense item by admin."""
    query = update.callback_query
    await query.answer()

    data = query.data
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    from bot.handlers._helpers import is_admin_or_owner
    if not await is_admin_or_owner(context.bot, chat_id, update.effective_user):
        await query.edit_message_text(t("admin_only", lang))
        return

    if data == "admexp_list":
        await admin_edit_all_expenses_handler(update, context)
        return

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return

    if data.startswith("admexpdel_"):
        parts = data.split("_")
        item_type = parts[1]
        item_id = int(parts[2])
        expenses = await get_all_trip_expenses(db_path, trip["id"])
        target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
        item_name = target_item["item_name"] if target_item else "Expense"

        if item_type == "meal":
            await delete_meal_contribution_by_id(db_path, item_id)
        else:
            await delete_shared_expense(db_path, item_id)

        context.user_data.pop("pending_edit_expense", None)
        await reply_ephemeral(update, context, t("expense_deleted", lang, name=item_name))
        await admin_edit_all_expenses_handler(update, context)
        return

    if data.startswith("admexpamt_"):
        parts = data.split("_")
        item_type = parts[1]
        item_id = int(parts[2])
        amount = float(parts[3])

        expenses = await get_all_trip_expenses(db_path, trip["id"])
        target_item = next((e for e in expenses if e["type"] == item_type and e["item_id"] == item_id), None)
        item_name = target_item["item_name"] if target_item else "Expense"

        if amount <= 0:
            if item_type == "meal":
                await delete_meal_contribution_by_id(db_path, item_id)
            else:
                await delete_shared_expense(db_path, item_id)
            await reply_ephemeral(update, context, t("expense_deleted", lang, name=item_name))
        else:
            if item_type == "meal":
                await update_meal_contribution_amount_by_id(db_path, item_id, amount)
            else:
                await update_shared_expense_amount(db_path, item_id, amount)
            await reply_ephemeral(update, context, t("expense_updated", lang, name=item_name, amount=amount))

        context.user_data.pop("pending_edit_expense", None)
        await admin_edit_all_expenses_handler(update, context)
        return
