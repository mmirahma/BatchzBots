from telegram import Update
from telegram.ext import ContextTypes

from bot.db import get_active_trip, get_family, add_family, update_family_weight
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /join <weight> command."""
    if not await require_group(update):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await update.message.reply_text(t("no_active_trip", lang))
        return

    if not context.args:
        await update.message.reply_text(t("usage_join", lang))
        return

    try:
        weight = float(context.args[0])
    except ValueError:
        await update.message.reply_text(t("usage_join", lang))
        return

    if weight <= 0:
        await update.message.reply_text(t("usage_join", lang))
        return

    user = update.effective_user
    name = user.full_name + "'s family"

    existing = await get_family(db_path, trip["id"], user_id)
    if existing:
        await update_family_weight(db_path, existing["id"], weight)
        await update.message.reply_text(t("family_updated", lang, name=existing["name"], weight=weight))
    else:
        await add_family(db_path, trip["id"], name, weight, user_id)
        await update.message.reply_text(t("family_joined", lang, name=name, weight=weight))
