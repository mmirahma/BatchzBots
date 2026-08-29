"""Handler for interactive 'Edit My Expenses' workflow."""

import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import (
    get_active_trip, get_family, get_families, get_family_expenses, get_all_trip_expenses,
    update_shared_expense_amount, delete_shared_expense,
    update_meal_contribution_amount_by_id, delete_meal_contribution_by_id,
    add_meal, add_shared_expense, get_meals,
)
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral

SHARED_EXPENSE_PRESETS = [
    [("Firewood 🪵", "admlog_cat_Firewood"), ("Park Entry 🏞", "admlog_cat_Park Entry")],
    [("Groceries 🛒", "admlog_cat_Groceries"), ("Ice 🧊", "admlog_cat_Ice")],
    [("Campsite Fee ⛺️", "admlog_cat_Campsite Fee"), ("Gas / Fuel ⛽️", "admlog_cat_Gas")],
]

TARGETED_EXPENSE_PRESETS = [
    [("Medicine 💊", "admlog_tgtcat_Medicine"), ("Boat Rental ⛵️", "admlog_tgtcat_Boat Rental")],
    [("Equipment 🎿", "admlog_tgtcat_Equipment"), ("Tickets / Passes 🎟", "admlog_tgtcat_Tickets")],
    [("Groceries 🛒", "admlog_tgtcat_Groceries"), ("Gas / Fuel ⛽️", "admlog_tgtcat_Gas")],
]

MEAL_NAME_PRESETS = [
    [("Breakfast 🍳", "admlog_mname_Breakfast"), ("Lunch 🥪", "admlog_mname_Lunch")],
    [("Dinner 🍖", "admlog_mname_Dinner"), ("BBQ 🥩", "admlog_mname_BBQ")],
    [("Snacks 🍉", "admlog_mname_Snacks"), ("Drinks ☕️", "admlog_mname_Drinks")],
]


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
    """Handle text input when user or admin types custom text/amount during edit/log expense flow."""
    if not update.message or not update.message.text:
        return False

    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    lang = await get_lang(update, context)
    db_path = context.bot_data.get("db_path")

    # A. Check admin_log_expense flow
    log_state = context.user_data.get("admin_log_expense")
    if log_state and log_state.get("chat_id") == chat_id:
        if time.time() - log_state.get("timestamp", 0) > 180:
            context.user_data.pop("admin_log_expense", None)
        else:
            step = log_state.get("step")
            trip = await get_active_trip(db_path, chat_id)
            if not trip:
                context.user_data.pop("admin_log_expense", None)
                return False

            # A1. Admin typed custom shared description
            if step == "shared_desc":
                log_state["desc"] = text
                log_state["step"] = "shared_amount"
                log_state["timestamp"] = time.time()
                PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0, 200.0]
                buttons = []
                row = []
                for amt in PRESETS:
                    label = f"${int(amt)}"
                    row.append(InlineKeyboardButton(label, callback_data=f"admlog_samt_{amt:.2f}"))
                    if len(row) == 3:
                        buttons.append(row)
                        row = []
                if row:
                    buttons.append(row)
                buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_shared")])
                msg_text = t("admin_log_ask_amount", lang, name=text, family_name=log_state["family_name"])
                await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
                return True

            # A2. Admin typed custom meal name
            if step == "meal_name":
                log_state["meal_name"] = text
                log_state["step"] = "meal_amount"
                log_state["timestamp"] = time.time()
                PRESETS = [20.0, 30.0, 50.0, 80.0, 100.0, 150.0, 200.0]
                buttons = []
                row = []
                for amt in PRESETS:
                    label = f"${int(amt)}"
                    row.append(InlineKeyboardButton(label, callback_data=f"admlog_mamt_{amt:.2f}"))
                    if len(row) == 4:
                        buttons.append(row)
                        row = []
                if row:
                    buttons.append(row)
                buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_meal")])
                msg_text = t("admin_log_ask_amount", lang, name=text, family_name=log_state["family_name"])
                await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
                return True

            # A3. Admin typed custom shared amount
            if step == "shared_amount":
                try:
                    amount = float(text)
                    if amount <= 0:
                        return False
                except ValueError:
                    return False
                state = context.user_data.pop("admin_log_expense", None)
                desc = state.get("desc", "Shared Expense")
                fid = state["family_id"]
                fam_name = state["family_name"]
                expense_id = await add_shared_expense(db_path, trip["id"], fid, desc, amount)
                context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}
                await reply_ephemeral(
                    update, context,
                    t("admin_expense_logged_success", lang, description=desc, amount=amount, family_name=fam_name),
                    parse_mode="Markdown",
                )
                await admin_edit_all_expenses_handler(update, context)
                return True

            # A4. Admin typed custom meal amount
            if step == "meal_amount":
                try:
                    amount = float(text)
                    if amount <= 0:
                        return False
                except ValueError:
                    return False
                state = context.user_data.pop("admin_log_expense", None)
                mname = state.get("meal_name", "Meal")
                fid = state["family_id"]
                fam_name = state["family_name"]
                meal_id = await add_meal(db_path, trip["id"], mname, fid, amount)
                meals = await get_meals(db_path, trip["id"])
                meal_num = len(meals)
                context.user_data["last_action"] = {"type": "meal", "meal_id": meal_id, "trip_id": trip["id"]}
                await reply_ephemeral(
                    update, context,
                    t("admin_meal_logged_success", lang, meal_num=meal_num, name=mname, amount=amount, family_name=fam_name),
                    parse_mode="Markdown",
                )
                await admin_edit_all_expenses_handler(update, context)
                return True

            # A5. Admin typed custom targeted description
            if step == "targeted_desc":
                log_state["desc"] = text
                log_state["step"] = "targeted_amount"
                log_state["timestamp"] = time.time()
                PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0, 200.0]
                buttons = []
                row = []
                for amt in PRESETS:
                    label = f"${int(amt)}"
                    row.append(InlineKeyboardButton(label, callback_data=f"admlog_tgtamt_{amt:.2f}"))
                    if len(row) == 3:
                        buttons.append(row)
                        row = []
                if row:
                    buttons.append(row)
                buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_targeted")])
                msg_text = t("admin_log_ask_amount", lang, name=text, family_name=log_state["family_name"])
                await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
                return True

            # A6. Admin typed custom targeted amount
            if step == "targeted_amount":
                try:
                    amount = float(text)
                    if amount <= 0:
                        return False
                except ValueError:
                    return False
                state = context.user_data.pop("admin_log_expense", None)
                desc = state.get("desc", "Custom Expense")
                payer_fid = state["family_id"]
                context.user_data["pending_targeted_payer_fid"] = payer_fid
                context.user_data["pending_targeted_is_admin"] = True

                from bot.handlers.expense import prompt_targeted_expense_family
                await prompt_targeted_expense_family(update, context, desc, amount)
                return True

    # B. Existing pending_edit_expense flow
    pending = context.user_data.get("pending_edit_expense")
    if not pending:
        return False

    # Expire after 2 minutes
    if time.time() - pending.get("timestamp", 0) > 120:
        context.user_data.pop("pending_edit_expense", None)
        return False

    if update.effective_chat.id != pending["chat_id"]:
        return False

    try:
        amount = float(text)
    except ValueError:
        return False

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
    """Display all logged expenses across all families for the trip with admin edit buttons and log option."""
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
    buttons = [
        [InlineKeyboardButton(t("btn_admin_log_expense", lang), callback_data="admexp_log_prompt")],
    ]

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


async def admin_log_flow_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the interactive multi-step workflow for admin logging an expense on behalf of any member."""
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

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await query.edit_message_text(t("no_active_trip", lang))
        return

    # Step 1: Prompt member/family selection
    if data == "admexp_log_prompt":
        context.user_data.pop("admin_log_expense", None)
        families = await get_families(db_path, trip["id"])
        if not families:
            await query.edit_message_text(
                t("no_families", lang),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back_all_expenses", lang), callback_data="admexp_list")]]),
            )
            return

        buttons = []
        for f in families:
            label = f"👤 {f['name']} (w={f['weight']})"
            buttons.append([InlineKeyboardButton(label, callback_data=f"admlog_fam_{f['id']}")])
        buttons.append([InlineKeyboardButton(t("btn_back_all_expenses", lang), callback_data="admexp_list")])

        msg_text = t("admin_log_select_family_title", lang, trip_name=trip["name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 2: Family selected -> Choose between Meal and Shared Expense
    if data.startswith("admlog_fam_"):
        fid = int(data.replace("admlog_fam_", ""))
        families = await get_families(db_path, trip["id"])
        target_family = next((f for f in families if f["id"] == fid), None)
        if not target_family:
            await query.edit_message_text(t("no_families", lang))
            return

        context.user_data["admin_log_expense"] = {
            "family_id": fid,
            "family_name": target_family["name"],
            "trip_id": trip["id"],
            "chat_id": chat_id,
            "timestamp": time.time(),
            "step": "type",
        }

        buttons = [
            [InlineKeyboardButton(t("btn_log_meal_for_member", lang), callback_data="admlog_type_meal")],
            [InlineKeyboardButton(t("btn_log_shared_for_member", lang), callback_data="admlog_type_shared")],
            [InlineKeyboardButton(t("btn_log_targeted_for_member", lang), callback_data="admlog_type_targeted")],
            [InlineKeyboardButton(t("btn_back", lang), callback_data="admexp_log_prompt")],
        ]
        msg_text = t("admin_log_choose_type_title", lang, family_name=target_family["name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 3A: Chosen Shared Expense -> Prompt category presets or text
    if data == "admlog_type_shared":
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["step"] = "shared_desc"
        state["timestamp"] = time.time()
        buttons = [
            [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
            for row in SHARED_EXPENSE_PRESETS
        ]
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data=f"admlog_fam_{state['family_id']}")])

        msg_text = t("admin_log_ask_shared_cat", lang, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 3B: Chosen Meal / Event -> Prompt meal name presets or text
    if data == "admlog_type_meal":
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["step"] = "meal_name"
        state["timestamp"] = time.time()
        buttons = [
            [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
            for row in MEAL_NAME_PRESETS
        ]
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data=f"admlog_fam_{state['family_id']}")])

        msg_text = t("admin_log_ask_meal_name", lang, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 3C: Chosen Custom-Weighted Expense -> Prompt category presets or text
    if data == "admlog_type_targeted":
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["step"] = "targeted_desc"
        state["timestamp"] = time.time()
        buttons = [
            [InlineKeyboardButton(label, callback_data=cb) for label, cb in row]
            for row in TARGETED_EXPENSE_PRESETS
        ]
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data=f"admlog_fam_{state['family_id']}")])

        msg_text = t("admin_log_ask_targeted_desc", lang, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 4A: Shared category preset chosen -> Prompt amount
    if data.startswith("admlog_cat_"):
        cat = data.replace("admlog_cat_", "")
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["desc"] = cat
        state["step"] = "shared_amount"
        state["timestamp"] = time.time()

        PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0, 200.0]
        buttons = []
        row = []
        for amt in PRESETS:
            label = f"${int(amt)}"
            row.append(InlineKeyboardButton(label, callback_data=f"admlog_samt_{amt:.2f}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_shared")])

        msg_text = t("admin_log_ask_amount", lang, name=cat, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 4B: Meal name preset chosen -> Prompt amount
    if data.startswith("admlog_mname_"):
        mname = data.replace("admlog_mname_", "")
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["meal_name"] = mname
        state["step"] = "meal_amount"
        state["timestamp"] = time.time()

        PRESETS = [20.0, 30.0, 50.0, 80.0, 100.0, 150.0, 200.0]
        buttons = []
        row = []
        for amt in PRESETS:
            label = f"${int(amt)}"
            row.append(InlineKeyboardButton(label, callback_data=f"admlog_mamt_{amt:.2f}"))
            if len(row) == 4:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_meal")])

        msg_text = t("admin_log_ask_amount", lang, name=mname, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 4C: Custom-Weighted category preset chosen -> Prompt amount
    if data.startswith("admlog_tgtcat_"):
        cat = data.replace("admlog_tgtcat_", "")
        state = context.user_data.get("admin_log_expense")
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        state["desc"] = cat
        state["step"] = "targeted_amount"
        state["timestamp"] = time.time()

        PRESETS = [10.0, 20.0, 30.0, 50.0, 100.0, 200.0]
        buttons = []
        row = []
        for amt in PRESETS:
            label = f"${int(amt)}"
            row.append(InlineKeyboardButton(label, callback_data=f"admlog_tgtamt_{amt:.2f}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(t("btn_back", lang), callback_data="admlog_type_targeted")])

        msg_text = t("admin_log_ask_amount", lang, name=cat, family_name=state["family_name"])
        await query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return

    # Step 5C: Custom-Weighted amount preset chosen -> Open interactive weight setup!
    if data.startswith("admlog_tgtamt_"):
        amount = float(data.replace("admlog_tgtamt_", ""))
        state = context.user_data.pop("admin_log_expense", None)
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        desc = state.get("desc", "Custom Expense")
        payer_fid = state["family_id"]
        context.user_data["pending_targeted_payer_fid"] = payer_fid
        context.user_data["pending_targeted_is_admin"] = True

        from bot.handlers.expense import prompt_targeted_expense_family
        await prompt_targeted_expense_family(update, context, desc, amount)
        return

    # Step 5A: Shared amount preset chosen -> Save expense!
    if data.startswith("admlog_samt_"):
        amount = float(data.replace("admlog_samt_", ""))
        state = context.user_data.pop("admin_log_expense", None)
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        desc = state.get("desc", "Shared Expense")
        fid = state["family_id"]
        fam_name = state["family_name"]
        expense_id = await add_shared_expense(db_path, trip["id"], fid, desc, amount)
        context.user_data["last_action"] = {"type": "expense", "expense_id": expense_id, "trip_id": trip["id"]}

        await reply_ephemeral(
            update, context,
            t("admin_expense_logged_success", lang, description=desc, amount=amount, family_name=fam_name),
            parse_mode="Markdown",
        )
        await admin_edit_all_expenses_handler(update, context)
        return

    # Step 5B: Meal amount preset chosen -> Save meal!
    if data.startswith("admlog_mamt_"):
        amount = float(data.replace("admlog_mamt_", ""))
        state = context.user_data.pop("admin_log_expense", None)
        if not state:
            await admin_edit_all_expenses_handler(update, context)
            return

        mname = state.get("meal_name", "Meal")
        fid = state["family_id"]
        fam_name = state["family_name"]
        meal_id = await add_meal(db_path, trip["id"], mname, fid, amount)
        meals = await get_meals(db_path, trip["id"])
        meal_num = len(meals)
        context.user_data["last_action"] = {"type": "meal", "meal_id": meal_id, "trip_id": trip["id"]}

        await reply_ephemeral(
            update, context,
            t("admin_meal_logged_success", lang, meal_num=meal_num, name=mname, amount=amount, family_name=fam_name),
            parse_mode="Markdown",
        )
        await admin_edit_all_expenses_handler(update, context)
        return


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
