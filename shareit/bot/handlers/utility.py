import aiosqlite
from telegram import Update
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family
from bot.i18n import t
from bot.handlers._helpers import get_lang, reply_ephemeral


async def lang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang <en|fa> command."""
    if not context.args or context.args[0] not in ("en", "fa"):
        await reply_ephemeral(update, context, "Usage: /lang <en|fa>")
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
    """Handle /help and /start commands."""
    lang = await get_lang(update, context)
    await reply_ephemeral(update, context, t("help", lang), parse_mode="Markdown")
