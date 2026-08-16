"""Post populated test trip status and settlement directly to 'bot test group' channel."""

import os
import sys
import asyncio
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.db import (
    init_db, get_active_trip, get_families, get_meals, get_meal_contributions,
    get_meal_absences, get_meal_grouping_members, get_shared_expenses, get_grouping_members
)
from bot.settlement import calculate_settlement

TOKEN = "8987597971:AAFeZs-vbXcTcYAkFoMLAVhgdpVhq_60qyg"
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bachztab.db"))
CHAT_ID = -1004424770402


async def post_live_data():
    trip = await get_active_trip(DB_PATH, CHAT_ID)
    if not trip:
        print("❌ No active trip found for bot test group!")
        return

    families = await get_families(DB_PATH, trip["id"])
    meals = await get_meals(DB_PATH, trip["id"])
    expenses = await get_shared_expenses(DB_PATH, trip["id"])

    meal_conts = {}
    meal_abs = {}
    meal_groups = {}
    for m in meals:
        meal_conts[m["id"]] = await get_meal_contributions(DB_PATH, m["id"])
        meal_abs[m["id"]] = await get_meal_absences(DB_PATH, m["id"])
        meal_groups[m["id"]] = await get_meal_grouping_members(DB_PATH, m["id"])

    expense_groups = {}
    for exp in expenses:
        if exp.get("grouping_id"):
            expense_groups[exp["id"]] = await get_grouping_members(DB_PATH, exp["grouping_id"])

    res = calculate_settlement(
        families=families,
        meals=meals,
        meal_contributions=meal_conts,
        meal_absences=meal_abs,
        shared_expenses=expenses,
        meal_groupings=meal_groups,
        expense_groupings=expense_groups,
    )

    # Construct Status Text
    text = f"🏕 *BachzTab — {trip['name']} Status*\n"
    if families:
        text += f"\n👥 *Families ({len(families)}):*\n```\n"
        text += f"{'Family Name':<28} {'Weight':>6}\n"
        text += "─" * 35 + "\n"
        for f in families:
            fname = f["name"][:27]
            text += f"{fname:<28} {f['weight']:>6.2f}\n"
        text += "```\n"

    if meals:
        family_names = {f["id"]: f["name"] for f in families}
        text += f"🍽 *Meals/Events ({len(meals)}):*\n```\n"
        text += f"{'#':<3} {'Meal/Event Name':<18} {'Total':>8} {'Payer(s)':<20}\n"
        text += "─" * 52 + "\n"
        for meal in meals:
            contributions = meal_conts.get(meal["id"], [])
            total = sum(c["amount"] for c in contributions)
            paid_parts = [f"{family_names.get(c['family_id'], 'Family')[:10]} (${c['amount']:.2f})" for c in contributions]
            payer_str = ", ".join(paid_parts) if paid_parts else "None"
            mname = meal["name"][:17]
            text += f"#{meal['meal_number']:<2} {mname:<18} {f'${total:.2f}':>8} {payer_str:<20}\n"
        text += "```\n"

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

    if families and (meals or expenses):
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

    async with httpx.AsyncClient() as client:
        # 1. Post Status Table
        r1 = await client.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
        )
        print("✅ Status Table Posted to 'bot test group':", r1.status_code, r1.json().get("ok"))

        # 2. Post Settlement Recommendations
        transfers_str = "\n".join([
            f"👉 *{next(f['name'] for f in families if f['id'] == t.from_family_id)}* pays *${t.amount:.2f}* to *{next(f['name'] for f in families if f['id'] == t.to_family_id)}*"
            for t in res.transfers
        ])
        settle_msg = f"💰 *Final Settlement Recommendations — {trip['name']}*\n\n{transfers_str}\n\n📊 Total Spent: *${res.total_spent:.2f}*"

        r2 = await client.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": settle_msg, "parse_mode": "Markdown"}
        )
        print("✅ Settlement Recommendations Posted to 'bot test group':", r2.status_code, r2.json().get("ok"))


if __name__ == "__main__":
    asyncio.run(post_live_data())
