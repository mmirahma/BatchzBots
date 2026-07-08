"""Shared helpers for command handlers."""

import logging
from datetime import timedelta

from telegram import Update, Message
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family
from bot.i18n import t

logger = logging.getLogger(__name__)

EPHEMERAL_DELETE_SECONDS = 120  # 2 minutes


async def reply_ephemeral(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs) -> Message:
    """Send a reply that auto-deletes after 2 minutes."""
    msg = await update.message.reply_text(text, **kwargs)
    context.job_queue.run_once(
        _delete_message_job,
        when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
        data={"chat_id": msg.chat_id, "message_id": msg.message_id},
        name=f"ephemeral_{msg.chat_id}_{msg.message_id}",
    )
    return msg


async def _delete_message_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a scheduled ephemeral message."""
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception as e:
        logger.debug(f"Could not delete ephemeral message: {e}")


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


async def require_group(update: Update, context: ContextTypes.DEFAULT_TYPE = None) -> bool:
    """Check if the command is in a group chat. Returns False if not."""
    if update.effective_chat.type == "private":
        if context:
            await reply_ephemeral(update, context, t("group_only", "en"))
        else:
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
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return None, None, lang

    family = await get_family(db_path, trip["id"], user_id)
    if not family:
        await reply_ephemeral(update, context, t("join_first", lang))
        return trip, None, lang

    return trip, family, lang
