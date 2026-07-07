"""Shared helpers for command handlers."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family
from bot.i18n import t


async def get_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Get the user's language preference."""
    db_path = context.bot_data.get("db_path")
    if not db_path:
        return "en"
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        return "en"
    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        return "en"
    return family.get("language", "en")


async def require_group(update: Update) -> bool:
    """Check if the command is in a group chat. Returns False if not."""
    if update.effective_chat.type == "private":
        await update.message.reply_text(t("group_only", "en"))
        return False
    return True


async def require_family(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """
    Get active trip and family for the current user.
    Returns (trip, family, lang). Sends error messages if not found.
    """
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    lang = await get_lang(update, context)

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await update.message.reply_text(t("no_active_trip", lang))
        return None, None, lang

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        await update.message.reply_text(t("join_first", lang))
        return trip, None, lang

    return trip, family, lang
