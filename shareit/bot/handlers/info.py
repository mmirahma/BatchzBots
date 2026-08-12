from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.db import (
    get_active_trip, get_families, get_meals,
    get_meal_contributions, get_meal_absences,
    get_shared_expenses, get_past_trips, get_trip_by_id,
    get_meal_grouping_members,
)
from bot.settlement import calculate_settlement
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral


async def meals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /meals — show detailed meal breakdown and active groupings."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    families = await get_families(db_path, trip["id"])
    meals = await get_meals(db_path, trip["id"])

    if not meals:
        await reply_ephemeral(update, context, t("no_meals_yet", lang))
        return

    esc = lambda s: escape_markdown(str(s), version=1)
    family_names = {f["id"]: f["name"] for f in families}
    text = t("meals_header", lang, trip_name=esc(trip["name"]), count=len(meals))

    for meal in meals:
        contributions = await get_meal_contributions(db_path, meal["id"])
        group_members = await get_meal_grouping_members(db_path, meal["id"])
        total = sum(c["amount"] for c in contributions)

        text += f"\n\n*#{meal['meal_number']} {esc(meal['name'])}*"
        if total > 0:
            text += f" — ${total:.2f}"

        # Who paid
        if contributions:
            paid_parts = [f"{esc(family_names.get(c['family_id'], '?'))} ${c['amount']:.2f}" for c in contributions]
            text += "\n  💳 Paid: " + ", ".join(paid_parts)

        # Active Grouping
        if group_members:
            active_parts = [f"{esc(m['family_name'])} ({m['weight']})" for m in group_members if m.get("is_active", 1) != 0]
            skipped_parts = [esc(m['family_name']) for m in group_members if m.get("is_active", 1) == 0]
            if active_parts:
                text += "\n  👥 Grouping: " + ", ".join(active_parts)
            if skipped_parts:
                text += "\n  🚫 Skipped: " + ", ".join(skipped_parts)

    await reply_ephemeral(update, context, text, parse_mode="Markdown")


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history — show past trip settlements."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    past_trips = await get_past_trips(db_path, chat_id)
    if not past_trips:
        await reply_ephemeral(update, context, t("no_history", lang))
        return

    # If an argument is given, show that specific trip
    if context.args:
        try:
            trip_idx = int(context.args[0]) - 1
            if trip_idx < 0 or trip_idx >= len(past_trips):
                await reply_ephemeral(update, context, t("history_invalid", lang, count=len(past_trips)))
                return
            trip = past_trips[trip_idx]
        except ValueError:
            await reply_ephemeral(update, context, t("history_usage", lang))
            return

        # Show full settlement for this past trip
        families = await get_families(db_path, trip["id"])
        meals = await get_meals(db_path, trip["id"])
        expenses = await get_shared_expenses(db_path, trip["id"])

        meal_contributions = {}
        meal_absences = {}
        for meal in meals:
            contributions = await get_meal_contributions(db_path, meal["id"])
            meal_contributions[meal["id"]] = [{"family_id": c["family_id"], "amount": c["amount"]} for c in contributions]
            abs_list = await get_meal_absences(db_path, meal["id"])
            meal_absences[meal["id"]] = abs_list

        expense_data = [{"family_id": e["family_id"], "description": e["description"], "amount": e["amount"]} for e in expenses]
        result = calculate_settlement(families, meals, meal_contributions, meal_absences, expense_data)
        family_names = {f["id"]: f["name"] for f in families}

        text = t("settle_header", lang,
                 trip_name=trip["name"],
                 family_count=len(families),
                 meal_count=len(meals),
                 expense_count=len(expenses),
                 total_spent=result.total_spent)

        if result.transfers:
            text += t("settle_transfers_header", lang, count=len(result.transfers))
            for i, transfer in enumerate(result.transfers, 1):
                text += "\n" + t("settle_transfer", lang,
                                 index=i,
                                 from_name=family_names.get(transfer.from_family_id, "?"),
                                 to_name=family_names.get(transfer.to_family_id, "?"),
                                 amount=transfer.amount)
            text += t("settle_footer", lang)
        else:
            text += t("settle_no_transfers", lang)

        await reply_ephemeral(update, context, text)
        return

    # Show list of past trips
    text = t("history_list", lang, count=len(past_trips))
    for i, trip in enumerate(past_trips, 1):
        families = await get_families(db_path, trip["id"])
        meals = await get_meals(db_path, trip["id"])
        text += f"\n  {i}. {trip['name']} — {len(families)} families, {len(meals)} meals"

    text += t("history_hint", lang)
    await reply_ephemeral(update, context, text)
