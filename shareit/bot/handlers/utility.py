import aiosqlite
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family
from bot.i18n import t
from bot.handlers._helpers import get_lang, reply_ephemeral


async def prompt_lang_preset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Prompt user with language selection buttons."""
    lang = await get_lang(update, context)
    buttons = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="plang_en"),
            InlineKeyboardButton("🇮🇷 فارسی", callback_data="plang_fa"),
        ]
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            t("lang_prompt", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await reply_ephemeral(
            update, context, t("lang_prompt", lang), reply_markup=InlineKeyboardMarkup(buttons)
        )


async def lang_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle language selection callback."""
    query = update.callback_query
    await query.answer()
    new_lang = query.data.replace("plang_", "")

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await query.edit_message_text(t("no_active_trip", new_lang))
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        await query.edit_message_text(t("join_first", new_lang))
        return

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE families SET language = ? WHERE id = ?",
            (new_lang, family["id"]),
        )
        await db.commit()

    await query.edit_message_text(t("lang_switched", new_lang))


async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang <en|fa> command or show buttons."""
    if not context.args or context.args[0] not in ("en", "fa"):
        await prompt_lang_preset(update, context)
        return

    new_lang = context.args[0]
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", new_lang))
        return

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        await reply_ephemeral(update, context, t("join_first", new_lang))
        return

    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE families SET language = ? WHERE id = ?",
            (new_lang, family["id"]),
        )
        await db.commit()

    await reply_ephemeral(update, context, t("lang_switched", new_lang))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    lang = await get_lang(update, context)
    await reply_ephemeral(update, context, t("help", lang), parse_mode="Markdown")

