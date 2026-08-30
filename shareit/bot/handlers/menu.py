from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import get_active_trip, get_family
from bot.handlers._helpers import require_group, get_lang, reply_ephemeral
from bot.handlers.family import WEIGHT_OPTIONS
from bot.i18n import t


def get_reply_keyboard(lang: str = "en", is_joined: bool = True, is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Build the persistent bottom custom ReplyKeyboard."""
    if not is_joined:
        if is_admin:
            keyboard = [[KeyboardButton(t("btn_join", lang)), KeyboardButton(t("btn_admin", lang))]]
        else:
            keyboard = [[KeyboardButton(t("btn_join", lang))]]
    else:
        if is_admin:
            admin_row = [KeyboardButton(t("btn_admin", lang)), KeyboardButton(t("btn_lang", lang)), KeyboardButton(t("btn_help", lang))]
        else:
            admin_row = [KeyboardButton(t("btn_lang", lang)), KeyboardButton(t("btn_help", lang))]

        keyboard = [
            [KeyboardButton(t("btn_log_expense", lang)), KeyboardButton(t("btn_edit_my_expenses", lang))],
            [KeyboardButton(t("btn_my_share", lang)), KeyboardButton(t("btn_meals", lang))],
            [KeyboardButton(t("btn_status", lang)), KeyboardButton(t("btn_settle", lang))],
            admin_row,
        ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
    )


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu or /start — display the interactive main dashboard with bottom ReplyKeyboard."""
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

    from bot.handlers._helpers import is_admin_or_owner
    is_admin = await is_admin_or_owner(context.bot, chat_id, update.effective_user)

    family = await get_family(db_path, trip["id"], user_id)
    is_joined = family is not None
    reply_kbd = get_reply_keyboard(lang, is_joined=is_joined, is_admin=is_admin)

    if not is_joined:
        from bot.handlers.family import WEIGHT_OPTIONS
        buttons = []
        row = []
        for w in WEIGHT_OPTIONS:
            label = str(w) if w != int(w) else str(int(w))
            row.append(InlineKeyboardButton(label, callback_data=f"join_{w}"))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        inline_kbd = InlineKeyboardMarkup(buttons)
        msg_text = f"🏕 *{trip['name']}*\n\n⚠️ {t('join_first', lang)}\n{t('join_select_weight', lang)}"
        await reply_ephemeral(update, context, msg_text, reply_markup=inline_kbd, parse_mode="Markdown")
        return

    from bot.handlers._helpers import schedule_message_deletion, schedule_user_message_deletion
    schedule_user_message_deletion(update, context)

    msg_text = t("menu_title", lang)
    msg = await context.bot.send_message(chat_id=chat_id, text=msg_text, reply_markup=reply_kbd, parse_mode="Markdown")
    schedule_message_deletion(chat_id, msg.message_id, context)

    if update.callback_query and update.callback_query.message:
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass


async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /admin or 👑 Admin button tap — display admin management dashboard."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    from bot.handlers._helpers import is_admin_or_owner
    if not await is_admin_or_owner(context.bot, chat_id, update.effective_user):
        await reply_ephemeral(update, context, t("admin_only", lang))
        return

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    buttons = [
        [InlineKeyboardButton(t("btn_members", lang), callback_data="menu_members")],
        [InlineKeyboardButton(t("btn_edit_all_expenses", lang), callback_data="menu_admin_expenses")],
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    text = t("admin_menu_title", lang, trip_name=trip["name"])

    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
        except BadRequest as e:
            if "Message is not modified" not in str(e):
                raise
    else:
        await reply_ephemeral(update, context, text, reply_markup=keyboard, parse_mode="Markdown")


async def text_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Intercept persistent bottom ReplyKeyboard button presses and text input."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    lang = await get_lang(update, context)

    # Check against all known button labels in both EN and FA
    btn_expense_en = t("btn_log_expense", "en")
    btn_expense_fa = t("btn_log_expense", "fa")
    btn_my_share_en = t("btn_my_share", "en")
    btn_my_share_fa = t("btn_my_share", "fa")
    btn_skip_en = t("btn_skip", "en")
    btn_skip_fa = t("btn_skip", "fa")
    btn_meals_en = t("btn_meals", "en")
    btn_meals_fa = t("btn_meals", "fa")
    btn_status_en = t("btn_status", "en")
    btn_status_fa = t("btn_status", "fa")
    btn_settle_en = t("btn_settle", "en")
    btn_settle_fa = t("btn_settle", "fa")
    btn_admin_en = t("btn_admin", "en")
    btn_admin_fa = t("btn_admin", "fa")
    btn_lang_en = t("btn_lang", "en")
    btn_lang_fa = t("btn_lang", "fa")
    btn_help_en = t("btn_help", "en")
    btn_help_fa = t("btn_help", "fa")
    btn_join_en = t("btn_join", "en")
    btn_join_fa = t("btn_join", "fa")
    btn_members_en = t("btn_members", "en")
    btn_members_fa = t("btn_members", "fa")

    btn_edit_my_expenses_en = t("btn_edit_my_expenses", "en")
    btn_edit_my_expenses_fa = t("btn_edit_my_expenses", "fa")

    is_button = text in (
        btn_expense_en, btn_expense_fa,
        btn_edit_my_expenses_en, btn_edit_my_expenses_fa,
        btn_my_share_en, btn_my_share_fa,
        btn_skip_en, btn_skip_fa,
        btn_meals_en, btn_meals_fa,
        btn_status_en, btn_status_fa,
        btn_settle_en, btn_settle_fa,
        btn_admin_en, btn_admin_fa,
        btn_members_en, btn_members_fa,
        btn_lang_en, btn_lang_fa,
        btn_help_en, btn_help_fa,
        btn_join_en, btn_join_fa,
    )

    has_pending_input = bool(
        context.user_data.get("pending_meal_desc")
        or context.user_data.get("pending_meal_name")
        or context.user_data.get("pending_meal_amount_prompt")
        or context.user_data.get("pending_expense_prompt")
        or context.user_data.get("pending_expense_desc")
        or context.user_data.get("pending_expense_amount_prompt")
        or context.user_data.get("pending_targeted_expense_desc")
        or context.user_data.get("pending_targeted_expense_amt_prompt")
        or context.user_data.get("pending_targeted_custom_weight")
        or context.user_data.get("pending_contribute")
        or context.user_data.get("pending_edit_expense")
        or context.user_data.get("admin_log_expense")
        or context.user_data.get("pending_custom_member_name")
        or context.user_data.get("pending_custom_member_weight")
    )

    if not is_button and not has_pending_input:
        # Regular chat message between group members — DO NOT DELETE!
        return

    from bot.handlers._helpers import schedule_user_message_deletion
    schedule_user_message_deletion(update, context)

    if is_button:
        # Clear stale pending inputs when user taps a main menu button
        for key in (
            "pending_meal_desc", "pending_meal_name", "pending_meal_amount_prompt",
            "pending_expense_prompt", "pending_expense_desc", "pending_expense_amount_prompt",
            "pending_targeted_expense_desc", "pending_targeted_expense_amt_prompt",
            "pending_targeted_custom_weight",
            "pending_contribute", "pending_edit_expense", "admin_log_expense", "targeted_expense_desc",
            "targeted_expense_weights", "pending_custom_member_name", "pending_custom_member_weight",
            "pending_custom_member_name_val"
        ):
            context.user_data.pop(key, None)

    if text in (btn_expense_en, btn_expense_fa):
        from bot.handlers.expense import prompt_expense_preset
        await prompt_expense_preset(update, context)
    elif text in (btn_edit_my_expenses_en, btn_edit_my_expenses_fa):
        from bot.handlers.edit_expenses import edit_my_expenses_handler
        await edit_my_expenses_handler(update, context)
    elif text in (btn_my_share_en, btn_my_share_fa):
        from bot.handlers.info import my_share_handler
        await my_share_handler(update, context)
    elif text in (btn_skip_en, btn_skip_fa):
        from bot.handlers.meal import skip_handler
        await skip_handler(update, context)
    elif text in (btn_meals_en, btn_meals_fa):
        from bot.handlers.info import meals_handler
        await meals_handler(update, context)
    elif text in (btn_status_en, btn_status_fa):
        from bot.handlers.trip import status_handler
        await status_handler(update, context)
    elif text in (btn_settle_en, btn_settle_fa):
        from bot.handlers.settle import settle_handler
        await settle_handler(update, context)
    elif text in (btn_admin_en, btn_admin_fa):
        await admin_menu_handler(update, context)
    elif text in (btn_members_en, btn_members_fa):
        from bot.handlers.members import members_handler
        await members_handler(update, context)
    elif text in (btn_lang_en, btn_lang_fa):
        from bot.handlers.utility import prompt_lang_preset
        await prompt_lang_preset(update, context)
    elif text in (btn_help_en, btn_help_fa):
        from bot.handlers.utility import help_handler
        await help_handler(update, context)
    elif text in (btn_join_en, btn_join_fa):
        from bot.handlers.family import join_handler
        await join_handler(update, context)
    else:
        from bot.handlers.members import pending_member_text_handler
        if await pending_member_text_handler(update, context):
            return
        from bot.handlers.edit_expenses import pending_edit_expense_text_handler
        if await pending_edit_expense_text_handler(update, context):
            return
        from bot.handlers.expense import pending_targeted_weight_text_handler
        if await pending_targeted_weight_text_handler(update, context):
            return
        from bot.handlers.meal import contribute_amount_handler
        await contribute_amount_handler(update, context)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu callback button clicks."""
    query = update.callback_query
    await query.answer()

    lang = await get_lang(update, context)
    data = query.data

    try:
        if data == "menu_status":
            from bot.handlers.trip import status_handler
            await status_handler(update, context)
        elif data == "menu_meals":
            from bot.handlers.info import meals_handler
            await meals_handler(update, context)
        elif data == "menu_meals_status":
            from bot.handlers.info import meals_status_report_handler
            await meals_status_report_handler(update, context)
        elif data == "menu_delete_meal":
            from bot.handlers.info import delete_meal_menu_handler
            await delete_meal_menu_handler(update, context)
        elif data == "menu_settle":
            from bot.handlers.settle import settle_handler
            await settle_handler(update, context)
        elif data in ("menu_admin", "admin_menu"):
            await admin_menu_handler(update, context)
        elif data == "menu_members":
            from bot.handlers.members import members_handler
            await members_handler(update, context)
        elif data == "menu_admin_expenses":
            from bot.handlers.edit_expenses import admin_edit_all_expenses_handler
            await admin_edit_all_expenses_handler(update, context)
        elif data == "menu_contrib":
            from bot.handlers.meal import contribute_handler
            await contribute_handler(update, context)
        elif data == "menu_skip":
            from bot.handlers.meal import skip_handler
            await skip_handler(update, context)
        elif data == "menu_meal":
            from bot.handlers.meal import prompt_meal_preset
            await prompt_meal_preset(update, context)
        elif data == "menu_expense":
            from bot.handlers.expense import prompt_expense_preset
            await prompt_expense_preset(update, context)
        elif data == "menu_lang":
            from bot.handlers.utility import prompt_lang_preset
            await prompt_lang_preset(update, context)
        elif data == "menu_open":
            await menu_handler(update, context)
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise
