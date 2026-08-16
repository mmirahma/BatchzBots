from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from bot.db import (
    create_trip, get_active_trip, end_trip,
    get_families, get_meals, get_meal_contributions, get_shared_expenses,
)
from bot.i18n import t
from bot.handlers._helpers import get_lang, require_group, reply_ephemeral


import logging
logger = logging.getLogger(__name__)


def cancel_pending_leave_job(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Cancel any scheduled 48h group departure job when a new trip is instantiated."""
    if chat_id and context and context.job_queue:
        job_name = f"leave_chat_{chat_id}"
        existing = context.job_queue.get_jobs_by_name(job_name)
        for j in existing:
            j.schedule_removal()


async def _leave_chat_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Leave group chat after 48 hours if no new trip was created."""
    data = context.job.data
    chat_id = data.get("chat_id")
    if chat_id:
        try:
            await context.bot.leave_chat(chat_id=chat_id)
            logger.info(f"Bot automatically left chat {chat_id} after 48h deadline.")
        except Exception as e:
            logger.warning(f"Could not leave chat {chat_id} after 48h deadline: {e}")


async def newtrip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /newtrip <name> [family_count] command."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    chat_id = update.effective_chat.id

    cancel_pending_leave_job(chat_id, context)

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

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.handlers.family import WEIGHT_OPTIONS
    from bot.handlers.menu import get_reply_keyboard

    reply_kbd = get_reply_keyboard(lang, is_joined=False)

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
    inline_kbd = InlineKeyboardMarkup(buttons)

    msg_text = f"🏕 *{trip_name}*\n\n✅ {t('trip_created', lang, name=trip_name)}\n\n{t('join_select_weight', lang)}"
    await reply_ephemeral(update, context, msg_text, reply_markup=inline_kbd, parse_mode="Markdown")
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
    """Handle /endtrip command — calculate settlement, send Excel report, end trip, and leave channel."""
    if not await require_group(update, context):
        return
    lang = await get_lang(update, context)
    db_path = context.bot_data["db_path"]
    chat_id = update.effective_chat.id

    trip = await get_active_trip(db_path, chat_id)
    if not trip:
        await reply_ephemeral(update, context, t("no_active_trip", lang))
        return

    from bot.db import (
        get_families, get_meals, get_shared_expenses,
        get_meal_contributions, get_meal_absences, get_meal_grouping_members, get_grouping_members, end_trip
    )
    from bot.settlement import calculate_settlement
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

    expense_groups = {}
    for exp in expenses:
        if exp.get("grouping_id"):
            expense_groups[exp["id"]] = await get_grouping_members(db_path, exp["grouping_id"])

    # 1. Calculate final settlement
    res = calculate_settlement(
        families=families,
        meals=meals,
        meal_contributions=meal_conts,
        meal_absences=meal_abs,
        shared_expenses=expenses,
        meal_groupings=meal_groups,
        expense_groupings=expense_groups,
    )

    # 2. Format & send permanent settlement message
    family_names = {f["id"]: f["name"] for f in families}
    text = t("settle_header", lang,
             trip_name=trip["name"],
             family_count=len(families),
             meal_count=len(meals),
             expense_count=len(expenses),
             total_spent=res.total_spent)

    if res.transfers:
        text += t("settle_transfers_header", lang, count=len(res.transfers))
        for i, transfer in enumerate(res.transfers, 1):
            from_name = family_names.get(transfer.from_family_id, "Family")
            to_name = family_names.get(transfer.to_family_id, "Family")
            text += "\n" + t("settle_transfer", lang, index=i, debtor=from_name, amount=transfer.amount, creditor=to_name)
    else:
        text += "\n\n" + t("nothing_to_settle", lang)

    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

    # 3. Generate & send Excel document attachment
    group_title = update.effective_chat.title if update.effective_chat and update.effective_chat.title else trip["name"]
    excel_file = create_excel_report(
        trip_name=trip["name"],
        families=families,
        meals=meals,
        expenses=expenses,
        meal_contributions=meal_conts,
        meal_absences=meal_abs,
        meal_groupings=meal_groups,
        expense_groupings=expense_groups,
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
    excel_filename = f"{clean_channel}-{clean_trip}.xlsx"

    caption = t("export_caption", lang, trip_name=trip["name"])
    await context.bot.send_document(
        chat_id=chat_id,
        document=excel_file,
        filename=excel_filename,
        caption=caption,
        parse_mode="Markdown",
    )

    # 4. Deactivate trip in database
    await end_trip(db_path, trip["id"])

    # 5. Send trip ended farewell message informing users about 48h departure
    await context.bot.send_message(chat_id=chat_id, text=t("trip_ended_leave_48h", lang, name=trip["name"]), parse_mode="Markdown")

    # 6. Schedule 48-hour delayed group departure (cancelled if /newtrip is created)
    if context and context.job_queue:
        from datetime import timedelta
        job_name = f"leave_chat_{chat_id}"
        cancel_pending_leave_job(chat_id, context)
        context.job_queue.run_once(
            _leave_chat_job,
            when=timedelta(hours=48),
            data={"chat_id": chat_id},
            name=job_name,
        )


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

    # 1. Families Table Section
    if families:
        text += f"\n👨‍👩‍👧 *Families ({len(families)}):*\n```\n"
        text += f"{'Family Name':<28} {'Weight':>6}\n"
        text += "─" * 35 + "\n"
        for f in families:
            fname = f["name"][:27]
            text += f"{fname:<28} {f['weight']:>6.2f}\n"
        text += "```\n"

    # 2. Meals & Events Section
    if meals:
        family_names = {f["id"]: f["name"] for f in families}
        text += f"🍽 *Meals/Events ({len(meals)}):*\n```\n"
        text += f"{'#':<3} {'Meal/Event Name':<18} {'Total':>8} {'Payer(s)':<20}\n"
        text += "─" * 52 + "\n"
        for meal in meals:
            contributions = await get_meal_contributions(db_path, meal["id"])
            total = sum(c["amount"] for c in contributions)
            if contributions:
                paid_parts = [f"{family_names.get(c['family_id'], 'Family')[:10]} (${c['amount']:.2f})" for c in contributions]
                payer_str = ", ".join(paid_parts)
            else:
                payer_str = "None"
            mname = meal["name"][:17]
            text += f"#{meal['meal_number']:<2} {mname:<18} {f'${total:.2f}':>8} {payer_str:<20}\n"
        text += "```\n"

    # 3. General Shared Expenses Section
    if expenses:
        text += f"💸 *Shared General Expenses ({len(expenses)}):*\n```\n"
        text += f"{'Description':<20} {'Total':>8} {'Paid By':<20}\n"
        text += "─" * 50 + "\n"
        for exp in expenses:
            desc = exp["description"][:19]
            payer = exp["family_name"][:19]
            amt_str = f"${exp['amount']:.2f}"
            text += f"{desc:<20} {amt_str:>8} {payer:<20}\n"
        text += "```\n"

    # 4. Bank Status Section
    if families and (meals or expenses):
        from bot.settlement import calculate_settlement
        from bot.db import get_meal_absences, get_meal_grouping_members, get_grouping_members

        meal_conts = {}
        meal_abs = {}
        meal_groups = {}
        for m in meals:
            meal_conts[m["id"]] = await get_meal_contributions(db_path, m["id"])
            meal_abs[m["id"]] = await get_meal_absences(db_path, m["id"])
            meal_groups[m["id"]] = await get_meal_grouping_members(db_path, m["id"])

        expense_groups = {}
        for exp in expenses:
            if exp.get("grouping_id"):
                expense_groups[exp["id"]] = await get_grouping_members(db_path, exp["grouping_id"])

        res = calculate_settlement(
            families=families,
            meals=meals,
            meal_contributions=meal_conts,
            meal_absences=meal_abs,
            shared_expenses=expenses,
            meal_groupings=meal_groups,
            expense_groupings=expense_groups,
        )

        balances = res.balances

        paid_totals = {f["id"]: 0.0 for f in families}
        for m in meals:
            for c in meal_conts.get(m["id"], []):
                if c["family_id"] in paid_totals:
                    paid_totals[c["family_id"]] += c["amount"]
        for e in expenses:
            if e["family_id"] in paid_totals:
                paid_totals[e["family_id"]] += e["amount"]

        text += "🏦 *Bank Status & Family Balances:*\n```\n"
        text += f"{'Family Name':<20} {'Paid':>8} {'Owed':>8} {'Net Balance':<15}\n"
        text += "─" * 53 + "\n"
        for f in families:
            fid = f["id"]
            bal = round(balances.get(fid, 0.0), 2)
            paid_amt = paid_totals.get(fid, 0.0)
            owed_amt = paid_amt - bal
            fname = f["name"][:19]

            if abs(bal) < 0.01:
                bal_str = "⚪ $0.00"
            elif bal > 0:
                bal_str = f"🟢 +${bal:.2f}"
            else:
                bal_str = f"🔴 -${abs(bal):.2f}"

            text += f"{fname:<20} {f'${paid_amt:.2f}':>8} {f'${owed_amt:.2f}':>8} {bal_str:<15}\n"
        text += "```"
    elif not meals and not expenses:
        text += t("status_no_data", lang)

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    excel_button = InlineKeyboardMarkup([[InlineKeyboardButton(t("btn_export_excel", lang), callback_data="export_excel")]])
    await reply_ephemeral(update, context, text, reply_markup=excel_button, parse_mode="Markdown")
