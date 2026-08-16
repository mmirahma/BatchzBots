from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import get_active_trip, get_family
from bot.handlers._helpers import require_group, get_lang, reply_ephemeral
from bot.handlers.family import WEIGHT_OPTIONS
from bot.i18n import t


def get_reply_keyboard(lang: str = "en", is_joined: bool = True) -> ReplyKeyboardMarkup:
    """Build the persistent bottom custom ReplyKeyboard."""
    if not is_joined:
        keyboard = [[KeyboardButton(t("btn_join", lang))]]
    else:
        keyboard = [
            [KeyboardButton(t("btn_log_expense", lang)), KeyboardButton(t("btn_my_share", lang))],
            [KeyboardButton(t("btn_meals", lang)), KeyboardButton(t("btn_status", lang))],
            [KeyboardButton(t("btn_settle", lang)), KeyboardButton(t("btn_lang", lang))],
        ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
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

    family = await get_family(db_path, trip["id"], user_id)
    is_joined = family is not None
    reply_kbd = get_reply_keyboard(lang, is_joined=is_joined)

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
        if update.callback_query:
            await update.callback_query.edit_message_text(msg_text, reply_markup=inline_kbd, parse_mode="Markdown")
        else:
            await reply_ephemeral(update, context, msg_text, reply_markup=inline_kbd, parse_mode="Markdown")
        return

    msg_text = t("menu_title", lang)
    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, msg_text, reply_markup=reply_kbd, parse_mode="Markdown")


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
    btn_lang_en = t("btn_lang", "en")
    btn_lang_fa = t("btn_lang", "fa")
    btn_join_en = t("btn_join", "en")
    btn_join_fa = t("btn_join", "fa")

    is_button = text in (
        btn_expense_en, btn_expense_fa,
        btn_my_share_en, btn_my_share_fa,
        btn_skip_en, btn_skip_fa,
        btn_meals_en, btn_meals_fa,
        btn_status_en, btn_status_fa,
        btn_settle_en, btn_settle_fa,
        btn_lang_en, btn_lang_fa,
        btn_join_en, btn_join_fa,
    )

    has_pending_input = bool(
        context.user_data.get("pending_meal_desc")
        or context.user_data.get("pending_meal_name")
        or context.user_data.get("pending_expense_desc")
        or context.user_data.get("pending_expense_category")
        or context.user_data.get("pending_contribute")
    )

    if not is_button and not has_pending_input:
        # Regular chat message between group members — DO NOT DELETE!
        return

    from bot.handlers._helpers import schedule_user_message_deletion
    schedule_user_message_deletion(update, context)

    if text in (btn_expense_en, btn_expense_fa):
        from bot.handlers.expense import prompt_expense_preset
        await prompt_expense_preset(update, context)
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
    elif text in (btn_lang_en, btn_lang_fa):
        from bot.handlers.utility import prompt_lang_preset
        await prompt_lang_preset(update, context)
    elif text in (btn_join_en, btn_join_fa):
        from bot.handlers.family import join_handler
        await join_handler(update, context)
    else:
        # Pass through to other text input handlers (e.g. pending meal description / amount)
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
        elif data == "menu_settle":
            from bot.handlers.settle import settle_handler
            await settle_handler(update, context)
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
    except BadRequest as e:
        if "Message is not modified" in str(e):
            pass
        else:
            raise
