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

    from bot.db import get_grouping_members
    expense_groupings = {}
    for e in expenses:
        if e.get("grouping_id"):
            gm_members = await get_grouping_members(db_path, e["grouping_id"])
            expense_groupings[e["id"]] = [
                {"family_id": gm["family_id"], "weight": gm["weight"], "is_active": gm["is_active"]}
                for gm in gm_members
            ]

    expense_data = [{"family_id": e["family_id"], "description": e["description"], "amount": e["amount"], "id": e["id"]} for e in expenses]

    result = calculate_settlement(
        families, meals, meal_contributions, meal_absences, expense_data,
        meal_groupings=meal_groupings, expense_groupings=expense_groupings
    )
    family_names = {f["id"]: f["name"] for f in families}

    # Format output
    text = t("settle_header", lang,
             trip_name=trip["name"],
             family_count=len(families),
             meal_count=len(meals),
             expense_count=len(expenses),
             total_spent=result.total_spent)

    # Bank Status & Visual Bar Graph Section
    if families:
        from telegram.helpers import escape_markdown
        esc = lambda s: escape_markdown(str(s), version=1)

        balances = result.balances
        max_abs = max((abs(b) for b in balances.values()), default=0.0)

        text += t("status_bank_header", lang)
        BAR_LEN = 8
        for f in families:
            bal = round(balances.get(f["id"], 0.0), 2)
            fname = esc(f["name"])

            if abs(bal) < 0.01:
                bar = "▒" * BAR_LEN
                text += f"\n  • {fname}: ⚪ $0.00 `[{bar}]`"
            elif bal > 0:
                ratio = min(bal / max_abs, 1.0) if max_abs > 0 else 1.0
                filled = max(1, int(round(ratio * BAR_LEN)))
                empty = BAR_LEN - filled
                bar = "🟩" * filled + "▒" * empty
                text += f"\n  • {fname}: 🟢 +${bal:.2f} `[{bar}]`"
            else:
                abs_b = abs(bal)
                ratio = min(abs_b / max_abs, 1.0) if max_abs > 0 else 1.0
                filled = max(1, int(round(ratio * BAR_LEN)))
                empty = BAR_LEN - filled
                bar = "🟥" * filled + "▒" * empty
                text += f"\n  • {fname}: 🔴 -${abs_b:.2f} `[{bar}]`"
        text += "\n"

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

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    buttons = [
        [InlineKeyboardButton(t("btn_export_excel", lang), callback_data="export_excel")],
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    from bot.handlers._helpers import schedule_user_message_deletion
    schedule_user_message_deletion(update, context)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.effective_message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
