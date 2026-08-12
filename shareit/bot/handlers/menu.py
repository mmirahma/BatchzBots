from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.db import get_active_trip, get_family
from bot.handlers._helpers import require_group, get_lang, reply_ephemeral
from bot.handlers.family import WEIGHT_OPTIONS
from bot.i18n import t


async def build_menu(db_path: str, chat_id: int, user_id: int, lang: str = "en") -> tuple[str, InlineKeyboardMarkup | None]:
    """Build the menu text and inline keyboard depending on whether user has joined."""
    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return t("no_active_trip", lang), None

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        # User hasn't joined: show ONLY Join buttons!
        title = f"🏕 *{trip['name']}*\n\n⚠️ {t('join_first', lang)}\n{t('join_select_weight', lang)}"
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
        return title, InlineKeyboardMarkup(buttons)

    # User is joined: show full menu dashboard!
    title = t("menu_title", lang)
    buttons = [
        [
            InlineKeyboardButton(t("btn_log_expense", lang), callback_data="menu_expense"),
            InlineKeyboardButton(t("btn_skip", lang), callback_data="menu_skip"),
        ],
        [
            InlineKeyboardButton(t("btn_meals", lang), callback_data="menu_meals"),
            InlineKeyboardButton(t("btn_status", lang), callback_data="menu_status"),
        ],
        [
            InlineKeyboardButton(t("btn_settle", lang), callback_data="menu_settle"),
            InlineKeyboardButton(t("btn_lang", lang), callback_data="menu_lang"),
        ],
    ]
    return title, InlineKeyboardMarkup(buttons)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu or /start — display the interactive main dashboard or join button."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    title, keyboard = await build_menu(db_path, chat_id, user_id, lang)
    if keyboard:
        await reply_ephemeral(update, context, title, reply_markup=keyboard, parse_mode="Markdown")
    else:
        await reply_ephemeral(update, context, title)


async def menu_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle menu button clicks."""
    query = update.callback_query
    await query.answer()

    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    data = query.data

    try:
        if data in ("menu_open", "menu_main"):
            title, keyboard = await build_menu(db_path, chat_id, user_id, lang)
            await query.edit_message_text(title, reply_markup=keyboard, parse_mode="Markdown")
            return

        if data == "menu_status":
            from bot.handlers.trip import status_handler
            await status_handler(update, context)
        elif data == "menu_meals":
            from bot.handlers.info import meals_handler
            await meals_handler(update, context)
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
