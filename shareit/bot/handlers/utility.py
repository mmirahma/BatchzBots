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


async def export_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /export command or export_excel button tap — generate and send itemized Excel file."""
    if update.callback_query:
        await update.callback_query.answer()

    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id
    lang = await get_lang(update, context)

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    from bot.db import (
        get_families, get_meals, get_shared_expenses,
        get_meal_contributions, get_meal_absences, get_meal_grouping_members,
    )
    from bot.export import create_excel_report

    families = await get_families(db_path, trip["id"])
    meals = await get_meals(db_path, trip["id"])
    expenses = await get_shared_expenses(db_path, trip["id"])

    meal_conts = {}
    meal_abs = {}
    meal_groups = {}
    for m in meals:
        meal_conts[m["id"]] = await get_meal_contributions(db_path, m["id"])
        meal_abs[m["id"]] = await get_meal_absences(db_path, m["id"])
        meal_groups[m["id"]] = await get_meal_grouping_members(db_path, m["id"])

    group_title = update.effective_chat.title if update.effective_chat and update.effective_chat.title else trip["name"]

    excel_file = create_excel_report(
        trip_name=trip["name"],
        families=families,
        meals=meals,
        expenses=expenses,
        meal_contributions=meal_conts,
        meal_absences=meal_abs,
        meal_groupings=meal_groups,
        group_title=group_title,
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

    from datetime import timedelta
    from bot.handlers._helpers import _delete_message_job, EPHEMERAL_DELETE_SECONDS, schedule_user_message_deletion

    schedule_user_message_deletion(update, context)

    doc_msg = await context.bot.send_document(
        chat_id=chat_id,
        document=excel_file,
        filename=filename,
        caption=caption,
        parse_mode="Markdown",
    )

    if doc_msg:
        context.job_queue.run_once(
            _delete_message_job,
            when=timedelta(seconds=EPHEMERAL_DELETE_SECONDS),
            data={"chat_id": doc_msg.chat_id, "message_id": doc_msg.message_id},
            name=f"ephemeral_{doc_msg.chat_id}_{doc_msg.message_id}",
        )

