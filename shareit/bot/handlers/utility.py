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
        from bot.handlers._helpers import refresh_callback_message_deletion
        refresh_callback_message_deletion(update, context)
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

    from bot.handlers._helpers import refresh_callback_message_deletion
    refresh_callback_message_deletion(update, context)

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
    refresh_callback_message_deletion(update, context)


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
    """Handle /help command or ❓ Help button — display guide and stay for 60 minutes (3600s)."""
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id
    target = update.effective_message

    msg = None
    if target:
        try:
            msg = await target.reply_text(t("help", lang), parse_mode="Markdown")
        except Exception:
            msg = None

    if not msg and update.effective_chat:
        msg = await context.bot.send_message(chat_id=chat_id, text=t("help", lang), parse_mode="Markdown")

    if msg:
        from bot.handlers._helpers import schedule_message_deletion, schedule_user_message_deletion
        schedule_message_deletion(msg.chat_id, msg.message_id, context, delay_seconds=3600)
        schedule_user_message_deletion(update, context)


async def export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command or export_excel button tap — generate and send permanent itemized Excel file."""
    if update.callback_query:
        await update.callback_query.answer()

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    lang = await get_lang(update, context)

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    from bot.settlement import calculate_trip_settlement_from_db
    from bot.export import create_excel_report

    families, meals, expenses, result = await calculate_trip_settlement_from_db(db_path, trip["id"])

    group_title = update.effective_chat.title if update.effective_chat and update.effective_chat.title else trip["name"]

    excel_file = create_excel_report(
        trip_name=trip["name"],
        families=families,
        meals=meals,
        expenses=expenses,
        group_title=group_title,
        settlement_result=result,
    )

    raw_channel = update.effective_chat.title if update.effective_chat and update.effective_chat.title else "Group"
    raw_trip = trip["name"] if trip and trip.get("name") else "Trip"

    clean_channel = "".join(c for c in raw_channel if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    clean_trip = "".join(c for c in raw_trip if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")

    if not clean_channel:
        clean_channel = "Group"
    if not clean_trip:
        clean_trip = "Trip"

    filename = f"{clean_channel}-{clean_trip}.xlsx"
    caption = t("export_caption", lang, trip_name=group_title)

    from bot.handlers._helpers import schedule_user_message_deletion
    schedule_user_message_deletion(update, context)

    # Note: Excel report document is permanent (no autodestruct per settlement records policy)
    await context.bot.send_document(
        chat_id=chat_id,
        document=excel_file,
        filename=filename,
        caption=caption,
        parse_mode="Markdown",
    )

