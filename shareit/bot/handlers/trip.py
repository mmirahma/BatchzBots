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
        await reply_ephemeral(update, context, t("no_active_trip", lang))
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
        family_names = {f["id"]: f["name"] for f in families}
        if meals:
            text += "\n" + t("status_meals", lang, count=len(meals))
            for meal in meals:
                contributions = await get_meal_contributions(db_path, meal["id"])
                total = sum(c["amount"] for c in contributions)
                text += "\n" + t("status_meal_item", lang, number=meal["meal_number"], name=esc(meal["name"]), total=total)
                if contributions:
                    paid_parts = [f"{esc(family_names.get(c['family_id'], 'Family'))} (${c['amount']:.2f})" for c in contributions]
                    text += t("status_meal_paid_by", lang, paid_list=", ".join(paid_parts))
        if expenses:
            text += "\n" + t("status_expenses", lang, count=len(expenses))
            for exp in expenses:
                text += "\n" + t("status_expense_item", lang, description=esc(exp["description"]), amount=exp["amount"], family=esc(exp["family_name"]))

        # Bank Status & Visual Bar Graph Section
        if families:
            from bot.settlement import calculate_settlement
            from bot.db import get_meal_absences, get_meal_grouping_members

            meal_conts = {}
            meal_abs = {}
            meal_groups = {}
            for m in meals:
                meal_conts[m["id"]] = await get_meal_contributions(db_path, m["id"])
                meal_abs[m["id"]] = await get_meal_absences(db_path, m["id"])
                meal_groups[m["id"]] = await get_meal_grouping_members(db_path, m["id"])

            res = calculate_settlement(
                families=families,
                meals=meals,
                meal_contributions=meal_conts,
                meal_absences=meal_abs,
                shared_expenses=expenses,
                meal_groupings=meal_groups,
            )

            balances = res.balances
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
    else:
        text += t("status_no_data", lang)

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    excel_button = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_export_excel", lang), callback_data="export_excel")]])
    await reply_ephemeral(update, context, text, reply_markup=excel_button, parse_mode="Markdown")
