"""Shared helpers for command handlers."""

import logging
from datetime import timedelta

from telegram import Update, Message
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family
from bot.i18n import t

logger = logging.getLogger(__name__)

EPHEMERAL_DELETE_SECONDS = 60  # 1 minute


def schedule_message_deletion(chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE, delay_seconds: int = EPHEMERAL_DELETE_SECONDS) -> None:
    """Schedule deletion of any message after delay_seconds (default 60s). Resets existing timer if present."""
    if chat_id and message_id and context and context.job_queue:
        job_name = f"ephemeral_{chat_id}_{message_id}"
        existing = context.job_queue.get_jobs_by_name(job_name)
        for j in existing:
            j.schedule_removal()

        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=delay_seconds),
            data={"chat_id": chat_id, "message_id": message_id},
            name=job_name,
        )


def schedule_user_message_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Schedule deletion of user's incoming message after 1 minute (60s)."""
    if update.effective_message and update.effective_chat and not update.callback_query:
        if update.effective_user and not update.effective_user.is_bot:
            schedule_message_deletion(update.effective_chat.id, update.effective_message.message_id, context)


async def reply_ephemeral(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs) -> Message | None:
    """Send a reply that auto-deletes after 1 minute, and schedule deletion of user trigger message."""
    target = update.effective_message
    if not target and update.callback_query:
        target = update.callback_query.message

    if target:
        msg = await target.reply_text(text, **kwargs)
    elif update.effective_chat:
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)
    else:
        return None

    if msg:
        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
            data={"chat_id": msg.chat_id, "message_id": msg.message_id},
            name=f"ephemeral_{msg.chat_id}_{msg.message_id}",
        )

    # Schedule deletion of user's command message after 1 minute as well
    schedule_user_message_deletion(update, context)

    return msg


async def _delete_message_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a scheduled ephemeral message."""
    data = context.job.data
    try:
        await context.bot.delete_message(chat_id=data["chat_id"], message_id=data["message_id"])
    except Exception as e:
        logger.warning(f"Could not delete ephemeral message (chat_id={data['chat_id']}, message_id={data['message_id']}): {e}")


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
        elif update.effective_message:
            await update.effective_message.reply_text(t("group_only", "en"))
        return False
    return True


async def require_family(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple:
    """
    Get active trip and family for the current user.
    Returns (trip, family, lang). If not joined, prompts with Join buttons.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.handlers.family import WEIGHT_OPTIONS

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
        # Prompt directly with Join weight buttons
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
        msg_text = f"⚠️ {t('join_first', lang)}\n\n{t('join_select_weight', lang)}"
        await reply_ephemeral(update, context, msg_text, reply_markup=InlineKeyboardMarkup(buttons))
        return trip, None, lang

    return trip, family, lang
