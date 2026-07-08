from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.db import (
    create_trip, get_active_trip, end_trip,
    get_families, get_meals, get_meal_contributions, get_shared_expenses,
)
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral


async def newtrip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /newtrip <name> [family_count] command."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    if not context.args:
        await reply_ephemeral(update, context, t("usage_newtrip", lang))
        return

    # Check if last arg is a number (expected family count)
    expected_families = None
    args = list(context.args)
    if len(args) >= 2:
        try:
            expected_families = int(args[-1])
            args = args[:-1]  # Remove the number from the name
        except ValueError:
            pass  # Last arg isn't a number, use all args as trip name

    trip_name = " ".join(args)
    db_path = context.bot_data["db_path"]

    existing = await get_active_trip(db_path, chat_id)
    if existing:
        await reply_ephemeral(update, context, t("trip_already_active", lang))
        return

    await create_trip(db_path, trip_name, chat_id, expected_families)
    await reply_ephemeral(update, context, t("trip_created", lang, name=trip_name))
    if expected_families:
        from datetime import timedelta
        from bot.reminder import _delete_reminder_message
        esc_name = escape_markdown(trip_name, version=1)
        msg = await update.effective_chat.send_message(
            t("reminder", lang, trip_name=esc_name, active=0, expected=expected_families),
            parse_mode="Markdown",
        )
        context.job_queue.run_once(
            _delete_reminder_message,
            when=timedelta(hours=1),
            data={"chat_id": msg.chat_id, "message_id": msg.message_id},
            name=f"delete_initial_reminder_{msg.chat_id}_{msg.message_id}",
        )


async def endtrip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /endtrip command."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    await end_trip(db_path, trip["id"])
    await reply_ephemeral(update, context, t("trip_ended", lang, name=trip["name"]))


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await update.message.reply_text(t("no_active_trip", lang))
        return

    families = await get_families(db_path, trip["id"])
    meals = await get_meals(db_path, trip["id"])
    expenses = await get_shared_expenses(db_path, trip["id"])

    # Escape user-provided strings to prevent Markdown parse errors
    esc = lambda s: escape_markdown(str(s), version=1)

    text = t("status_header", lang, trip_name=esc(trip["name"]))
    text += t("status_families", lang, count=len(families))
    for f in families:
        text += "\n" + t("status_family_item", lang, name=esc(f["name"]), weight=f["weight"])

    if meals or expenses:
        if meals:
            text += "\n" + t("status_meals", lang, count=len(meals))
            for meal in meals:
                contributions = await get_meal_contributions(db_path, meal["id"])
                total = sum(c["amount"] for c in contributions)
                text += "\n" + t("status_meal_item", lang, number=meal["meal_number"], name=esc(meal["name"]), total=total)
        if expenses:
            text += "\n" + t("status_expenses", lang, count=len(expenses))
            for exp in expenses:
                text += "\n" + t("status_expense_item", lang, description=esc(exp["description"]), amount=exp["amount"], family=esc(exp["family_name"]))
    else:
        text += t("status_no_data", lang)

    await update.message.reply_text(text, parse_mode="Markdown")
