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


async def record_user_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Record active, mentioned, replied, forwarded, or joined Telegram users as known group members."""
    db_path = context.bot_data.get("db_path") if context and context.bot_data else None
    if not db_path:
        return

    chat = update.effective_chat
    if not chat or chat.type not in ("group", "supergroup"):
        return

    from bot.db import save_chat_member, get_known_chat_members

    bot_id = context.bot.id if context and context.bot else 0
    bot_uname = (context.bot.username or "").lower() if context and context.bot else ""

    async def _save(uid: int, full_name: str, username: str | None = None):
        if not uid or uid == bot_id:
            return
        name = full_name.strip() if full_name else (f"@{username}" if username else f"User #{uid}")
        try:
            await save_chat_member(db_path, chat.id, uid, name, username)
        except Exception as e:
            logger.warning(f"Failed to record chat member {uid} in chat {chat.id}: {e}")

    # 1. Message sender / callback query user
    user = update.effective_user
    if user and not user.is_bot:
        await _save(user.id, user.full_name or user.first_name, user.username)

    message = update.effective_message
    if message:
        # 2. Replied-to user (e.g. admin replies to an inactive member's message)
        if message.reply_to_message and message.reply_to_message.from_user:
            rep_user = message.reply_to_message.from_user
            if not rep_user.is_bot:
                await _save(rep_user.id, rep_user.full_name or rep_user.first_name, rep_user.username)

        # 3. Forwarded user (e.g. admin forwards a message from a member)
        if message.forward_from and not message.forward_from.is_bot:
            fwd_user = message.forward_from
            await _save(fwd_user.id, fwd_user.full_name or fwd_user.first_name, fwd_user.username)

        # 4. New chat members (users who joined or were added to group)
        if message.new_chat_members:
            for new_user in message.new_chat_members:
                if not new_user.is_bot:
                    await _save(new_user.id, new_user.full_name or new_user.first_name, new_user.username)

        # 5. Tagged / Mentioned users in text or caption
        entities = list(message.entities or ()) + list(message.caption_entities or ())
        text = message.text or message.caption or ""
        for entity in entities:
            # 5a. Direct text mention with embedded User object
            if entity.type == "text_mention" and getattr(entity, "user", None):
                m_user = entity.user
                if not m_user.is_bot:
                    await _save(m_user.id, m_user.full_name or m_user.first_name, m_user.username)
            # 5b. Username mention @username
            elif entity.type == "mention" and text:
                uname = text[entity.offset:entity.offset + entity.length].lstrip("@").strip()
                if uname and uname.lower() != bot_uname:
                    placeholder_uid = -(abs(hash(uname.lower())) % 900000 + 100000)
                    try:
                        known_members = await get_known_chat_members(db_path, chat.id)
                        already_known = any(
                            (m.get("username") or "").lower() == uname.lower() and m["telegram_user_id"] > 0
                            for m in known_members
                        )
                        if not already_known:
                            await _save(placeholder_uid, f"@{uname}", uname)
                    except Exception as e:
                        logger.warning(f"Failed to record mention @{uname}: {e}")

    # 6. ChatMemberUpdated updates
    if update.chat_member and update.chat_member.new_chat_member:
        cm_user = update.chat_member.new_chat_member.user
        if cm_user and not cm_user.is_bot:
            await _save(cm_user.id, cm_user.full_name or cm_user.first_name, cm_user.username)


async def reply_ephemeral(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs) -> Message | None:
    """Send a reply that auto-deletes after 1 minute, and schedule deletion of user trigger message."""
    await record_user_activity(update, context)
    target = update.effective_message
    if not target and update.callback_query:
        target = update.callback_query.message

    msg = None
    if target:
        try:
            msg = await target.reply_text(text, **kwargs)
        except Exception:
            msg = None

    if not msg and update.effective_chat:
        msg = await context.bot.send_message(chat_id=update.effective_chat.id, text=text, **kwargs)

    if not msg:
        return None

    schedule_message_deletion(msg.chat_id, msg.message_id, context)
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


async def is_admin_or_owner(bot, chat_id: int, user) -> bool:
    """
    Check if the user is 'Maysam Mir' or the creator / owner of the group chat.
    """
    if not user:
        return False

    # Check for Maysam Mir by name, username, etc.
    full_name = (user.full_name or f"{user.first_name or ''} {user.last_name or ''}").strip().lower()
    username = (user.username or "").strip().lower()

    if (
        "maysam mir" in full_name
        or ("maysam" in full_name and "mir" in full_name)
        or "میثم" in full_name
        or username in ("mmirahma", "maysammir", "maysam_mir")
        or "maysam" in username
    ):
        return True

    # Check if user is Telegram group chat creator / owner
    if bot and chat_id:
        try:
            member = await bot.get_chat_member(chat_id, user.id)
            if getattr(member, "status", "") in ("creator",):
                return True
        except Exception:
            pass

        try:
            admins = await bot.get_chat_administrators(chat_id)
            for admin in admins:
                admin_user = getattr(admin, "user", None)
                if admin_user and admin_user.id == user.id and getattr(admin, "status", "") == "creator":
                    return True
        except Exception as e:
            logger.warning(f"Could not verify chat administrator status for user {user.id} in chat {chat_id}: {e}")

    return False
