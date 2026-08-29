"""Handler for group member discovery, trip roster management, and weight selection."""

import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import (
    get_active_trip, get_families, get_family, add_family,
    update_family_weight, remove_family_from_trip, get_family_expenses,
    save_chat_member, get_known_chat_members,
)
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral, record_user_activity
from bot.handlers.family import WEIGHT_OPTIONS

logger = logging.getLogger(__name__)


async def get_all_group_members(bot, db_path: str, chat_id: int) -> list[dict]:
    """
    Fetch all known group members by combining database records,
    past trip participants, and Telegram group chat administrators.
    """
    known_members = await get_known_chat_members(db_path, chat_id)
    known_map = {m["telegram_user_id"]: dict(m) for m in known_members}

    # Fetch administrators from Telegram Bot API to discover active admins
    try:
        admins = await bot.get_chat_administrators(chat_id)
        for admin in admins:
            user = admin.user
            if not user.is_bot:
                name = user.full_name or user.first_name or "Admin"
                if user.id not in known_map:
                    await save_chat_member(db_path, chat_id, user.id, name, user.username)
                    known_map[user.id] = {
                        "chat_id": chat_id,
                        "telegram_user_id": user.id,
                        "name": name,
                        "username": user.username,
                    }
    except Exception as e:
        logger.warning(f"Could not retrieve chat administrators for chat {chat_id}: {e}")

    # Return sorted list (positive Telegram IDs first, custom/guest members later)
    return list(known_map.values())


def build_members_keyboard(trip: dict, members: list[dict], families: list[dict], lang: str) -> InlineKeyboardMarkup:
    """Build interactive inline keyboard for member selection and roster status."""
    families_by_uid = {f["telegram_user_id"]: f for f in families}
    buttons = []

    # 1. Known Telegram Group Members
    for m in members:
        uid = m["telegram_user_id"]
        name = m.get("name", "Member")
        if uid in families_by_uid:
            fam = families_by_uid[uid]
            label = f"✅ {name[:18]} (w={fam['weight']})"
        else:
            label = f"➕ {name[:18]} (Not in trip)"
        buttons.append([InlineKeyboardButton(label, callback_data=f"mem_sel_{uid}")])

    # 2. Custom / Guest families (negative or unlinked telegram_user_id)
    for fam in families:
        if fam["telegram_user_id"] <= 0 and fam["telegram_user_id"] not in [m["telegram_user_id"] for m in members]:
            label = f"✅ {fam['name'][:18]} (w={fam['weight']}) [Guest]"
            buttons.append([InlineKeyboardButton(label, callback_data=f"mem_sel_{fam['telegram_user_id']}")])

    # 3. Action Buttons
    buttons.append([InlineKeyboardButton(t("btn_custom_member", lang), callback_data="mem_custom")])
    buttons.append([
        InlineKeyboardButton(t("btn_refresh_members", lang), callback_data="mem_refresh"),
        InlineKeyboardButton(t("btn_done", lang), callback_data="mem_done"),
    ])
    buttons.append([InlineKeyboardButton(t("btn_back_admin", lang), callback_data="menu_admin")])

    return InlineKeyboardMarkup(buttons)


async def members_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /members or /addmembers command — display the trip member roster (Admin only)."""
    if not await require_group(update, context):
        return
    await record_user_activity(update, context)

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
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    members = await get_all_group_members(context.bot, db_path, chat_id)
    families = await get_families(db_path, trip["id"])

    keyboard = build_members_keyboard(trip, members, families, lang)
    text = t("members_title", lang, trip_name=trip["name"])

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        await reply_ephemeral(update, context, text, reply_markup=keyboard, parse_mode="Markdown")


async def member_select_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle selection of a specific member to configure weight or remove/skip."""
    query = update.callback_query
    await query.answer()

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

    uid_str = query.data.replace("mem_sel_", "")
    try:
        target_uid = int(uid_str)
    except ValueError:
        return

    # Find member name and current family status
    family = await get_family(db_path, trip["id"], target_uid)
    members = await get_all_group_members(context.bot, db_path, chat_id)
    member_record = next((m for m in members if m["telegram_user_id"] == target_uid), None)

    if family:
        display_name = family["name"]
        status_text = t("status_joined", lang, weight=family["weight"])
    elif member_record:
        display_name = member_record["name"]
        status_text = t("status_not_joined", lang)
    else:
        display_name = f"Member #{target_uid}"
        status_text = t("status_not_joined", lang)

    # Save selected target user in context for custom weight flow
    context.user_data["selected_member_uid"] = target_uid
    context.user_data["selected_member_name"] = display_name

    # Build weight selection buttons
    buttons = []
    row = []
    for w in WEIGHT_OPTIONS:
        label = str(w) if w != int(w) else str(int(w))
        row.append(InlineKeyboardButton(label, callback_data=f"mem_setw_{target_uid}_{w}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(t("btn_custom_weight", lang), callback_data=f"mem_custw_{target_uid}")])

    if family:
        buttons.append([InlineKeyboardButton(t("btn_remove_member", lang), callback_data=f"mem_del_{target_uid}")])

    buttons.append([InlineKeyboardButton(t("btn_back_members", lang), callback_data="mem_list")])

    keyboard = InlineKeyboardMarkup(buttons)
    text = t("member_config_title", lang, name=display_name, status=status_text)

    try:
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


async def member_action_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dispatch actions: set weight, remove member, refresh, custom name prompt, or done."""
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

    if data == "mem_list":
        await members_handler(update, context)
        return

    if data == "mem_refresh":
        await members_handler(update, context)
        return

    if data == "mem_done":
        from bot.handlers.trip import status_handler
        await status_handler(update, context)
        return

    if data == "mem_custom":
        # Prompt for custom family name
        context.user_data["pending_custom_member_name"] = True
        prompt_text = t("prompt_custom_member_name", lang)
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back_members", lang), callback_data="mem_list")]])
        await query.edit_message_text(prompt_text, reply_markup=cancel_btn, parse_mode="Markdown")
        return

    if data.startswith("mem_custw_"):
        uid_str = data.replace("mem_custw_", "")
        target_uid = int(uid_str)
        context.user_data["pending_custom_member_weight"] = target_uid
        name = context.user_data.get("selected_member_name", "Member")
        prompt_text = t("prompt_custom_member_weight", lang, name=name)
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_back_members", lang), callback_data="mem_list")]])
        await query.edit_message_text(prompt_text, reply_markup=cancel_btn, parse_mode="Markdown")
        return

    if data.startswith("mem_setw_"):
        parts = data.split("_")  # mem, setw, <uid>, <weight>
        target_uid = int(parts[2])
        weight = float(parts[3])

        # Retrieve member name
        existing = await get_family(db_path, trip["id"], target_uid)
        if existing:
            await update_family_weight(db_path, existing["id"], weight)
        else:
            members = await get_all_group_members(context.bot, db_path, chat_id)
            rec = next((m for m in members if m["telegram_user_id"] == target_uid), None)
            name = rec["name"] if rec else f"Family #{target_uid}"
            if not name.endswith("'s family") and not name.endswith(" Family"):
                name = name + "'s family"
            await add_family(db_path, trip["id"], name, weight, target_uid)

        # Return to member list
        await members_handler(update, context)
        return

    if data.startswith("mem_del_"):
        target_uid = int(data.replace("mem_del_", ""))
        family = await get_family(db_path, trip["id"], target_uid)
        if not family:
            await members_handler(update, context)
            return

        expenses = await get_family_expenses(db_path, trip["id"], family["id"])
        if expenses:
            # Member has logged expenses: list them and ask for confirmation
            expense_lines = []
            total_amount = 0.0
            for item in expenses:
                total_amount += item["amount"]
                if item["type"] == "meal":
                    expense_lines.append(f"• 🍽 #{item['meal_number']} {item['item_name']} (${item['amount']:.2f})")
                else:
                    expense_lines.append(f"• 🪵 {item['item_name']} (${item['amount']:.2f})")
            expenses_str = "\n".join(expense_lines)

            warn_text = t("member_delete_with_expenses_warning", lang,
                          name=family["name"],
                          total=total_amount,
                          expenses=expenses_str)

            confirm_buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton(t("btn_confirm_remove_member_expenses", lang), callback_data=f"mem_delforce_{target_uid}")],
                [InlineKeyboardButton(t("btn_back_members", lang), callback_data=f"mem_sel_{target_uid}")],
            ])

            await query.edit_message_text(warn_text, reply_markup=confirm_buttons, parse_mode="Markdown")
            return

        # No expenses: remove directly
        await remove_family_from_trip(db_path, trip["id"], family["id"])
        await reply_ephemeral(update, context, t("member_removed_success", lang, name=family["name"]))
        await members_handler(update, context)
        return

    if data.startswith("mem_delforce_"):
        target_uid = int(data.replace("mem_delforce_", ""))
        family = await get_family(db_path, trip["id"], target_uid)
        if family:
            await remove_family_from_trip(db_path, trip["id"], family["id"], force=True)
            await reply_ephemeral(update, context, t("member_and_expenses_deleted_success", lang, name=family["name"]))

        await members_handler(update, context)
        return

    if data.startswith("mem_custfam_w_"):
        # Weight chosen for custom family name
        weight = float(data.replace("mem_custfam_w_", ""))
        custom_name = context.user_data.pop("pending_custom_member_name_val", "Guest Family")
        custom_uid = -int(time.time() % 1000000)

        await add_family(db_path, trip["id"], custom_name, weight, custom_uid)
        await reply_ephemeral(update, context, t("member_added_success", lang, name=custom_name, weight=weight))
        await members_handler(update, context)
        return


async def pending_member_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Handle text inputs for custom member name or custom weight."""
    if not update.message or not update.message.text:
        return False

    if not context.user_data.get("pending_custom_member_name") and "pending_custom_member_weight" not in context.user_data:
        return False

    from bot.handlers._helpers import is_admin_or_owner
    if not await is_admin_or_owner(context.bot, update.effective_chat.id, update.effective_user):
        context.user_data.pop("pending_custom_member_name", None)
        context.user_data.pop("pending_custom_member_weight", None)
        context.user_data.pop("pending_custom_member_name_val", None)
        return False

    text = update.message.text.strip()
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    lang = await get_lang(update, context)

    # 1. Custom family name entered
    if context.user_data.get("pending_custom_member_name"):
        context.user_data.pop("pending_custom_member_name", None)
        custom_name = text
        context.user_data["pending_custom_member_name_val"] = custom_name

        # Prompt weight for this custom family
        buttons = []
        row = []
        for w in WEIGHT_OPTIONS:
            label = str(w) if w != int(w) else str(int(w))
            row.append(InlineKeyboardButton(label, callback_data=f"mem_custfam_w_{w}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([InlineKeyboardButton(t("btn_back_members", lang), callback_data="mem_list")])
        prompt_text = t("prompt_custom_member_weight", lang, name=custom_name)
        await reply_ephemeral(update, context, prompt_text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")
        return True

    # 2. Custom weight number entered for a member
    if "pending_custom_member_weight" in context.user_data:
        target_uid = context.user_data.pop("pending_custom_member_weight")
        try:
            weight = float(text)
            if weight <= 0:
                raise ValueError
        except ValueError:
            await reply_ephemeral(update, context, t("invalid_weight", lang))
            return True

        trip = await get_active_trip(db_path, chat_id)
        if not trip:
            return True

        existing = await get_family(db_path, trip["id"], target_uid)
        if existing:
            await update_family_weight(db_path, existing["id"], weight)
            name = existing["name"]
        else:
            members = await get_all_group_members(context.bot, db_path, chat_id)
            rec = next((m for m in members if m["telegram_user_id"] == target_uid), None)
            name = rec["name"] if rec else f"Family #{target_uid}"
            if not name.endswith("'s family") and not name.endswith(" Family"):
                name = name + "'s family"
            await add_family(db_path, trip["id"], name, weight, target_uid)

        await reply_ephemeral(update, context, t("member_added_success", lang, name=name, weight=weight), parse_mode="Markdown")
        await members_handler(update, context)
        return True

    return False
