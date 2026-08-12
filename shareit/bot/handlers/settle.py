from telegram import Update
from telegram.ext import ContextTypes

from bot.db import (
    get_active_trip, get_families, get_meals,
    get_meal_contributions, get_meal_absences, get_shared_expenses,
    get_meal_grouping_members,
)
from bot.settlement import calculate_settlement
from bot.i18n import t
from bot.handlers._helpers import require_group, get_lang, reply_ephemeral


async def settle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /settle command — calculate and display final transfers."""
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
    expenses = await get_shared_expenses(db_path, trip["id"])

    if not meals and not expenses:
        await reply_ephemeral(update, context, t("nothing_to_settle", lang))
        return

    # Build data for settlement calculation
    meal_contributions = {}
    meal_absences = {}
    meal_groupings = {}
    for meal in meals:
        contributions = await get_meal_contributions(db_path, meal["id"])
        meal_contributions[meal["id"]] = [{"family_id": c["family_id"], "amount": c["amount"]} for c in contributions]
        absences = await get_meal_absences(db_path, meal["id"])
        meal_absences[meal["id"]] = absences
        group_members = await get_meal_grouping_members(db_path, meal["id"])
        meal_groupings[meal["id"]] = [
            {"family_id": gm["family_id"], "weight": gm["weight"], "is_active": gm["is_active"]}
            for gm in group_members
        ]

    expense_data = [{"family_id": e["family_id"], "description": e["description"], "amount": e["amount"], "id": e["id"]} for e in expenses]

    result = calculate_settlement(
        families, meals, meal_contributions, meal_absences, expense_data, meal_groupings=meal_groupings
    )
    family_names = {f["id"]: f["name"] for f in families}

    # Format output
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
