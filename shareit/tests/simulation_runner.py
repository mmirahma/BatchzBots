"""Automated Multi-User Simulation & Production DB Population Runner."""

import asyncio
import os
import sys
import aiosqlite
from telegram import Update, User, Chat, Message, CallbackQuery

# Add shareit directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.db import (
    init_db, create_trip, get_active_trip, add_family, get_families,
    add_meal, add_meal_contribution, add_meal_absence, get_meals,
    get_meal_contributions, get_meal_absences, get_meal_grouping_members,
    add_shared_expense, get_shared_expenses, create_grouping,
    add_or_update_grouping_member, get_grouping_members,
    update_shared_expense_amount, delete_shared_expense
)
from bot.settlement import calculate_settlement

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shareit.db"))


class DummyBot:
    """Mock bot context for handler execution."""
    def __init__(self):
        self.sent_messages = []

    async def send_message(self, chat_id, text, **kwargs):
        msg = Message(message_id=len(self.sent_messages) + 1, date=None, chat=Chat(id=chat_id, type="group"), text=text)
        self.sent_messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})
        return msg

    async def send_document(self, chat_id, document, **kwargs):
        return Message(message_id=len(self.sent_messages) + 1, date=None, chat=Chat(id=chat_id, type="group"))


class DummyJobQueue:
    def run_once(self, callback, when, data=None, name=None):
        pass


class SimulationContext:
    def __init__(self, db_path):
        self.bot_data = {"db_path": db_path}
        self.user_data = {}
        self.bot = DummyBot()
        self.job_queue = DummyJobQueue()


async def run_simulation():
    print(f"=== Starting Multi-User Simulation on Production DB: {DB_PATH} ===")
    await init_db(DB_PATH)

    chat_id = -100998877
    user_alpha = User(id=101, is_bot=False, first_name="Alice & Bob (Alpha)")
    user_beta = User(id=102, is_bot=False, first_name="Charlie (Beta)")
    user_gamma = User(id=103, is_bot=False, first_name="David (Gamma)")
    user_delta = User(id=104, is_bot=False, first_name="Eva (Delta)")

    # 1. Setup Trip & Join Families
    trip_id = await create_trip(DB_PATH, "High Sierra Camping Sim", chat_id=chat_id)
    f_alpha = await add_family(DB_PATH, trip_id, "Family Alpha", 2.0, telegram_user_id=101)
    f_beta = await add_family(DB_PATH, trip_id, "Family Beta", 1.5, telegram_user_id=102)
    f_gamma = await add_family(DB_PATH, trip_id, "Family Gamma", 1.0, telegram_user_id=103)
    f_delta = await add_family(DB_PATH, trip_id, "Family Delta", 1.0, telegram_user_id=104)

    print("\n✅ Scenario 1: Trip Created & 4 Families Joined")
    print(f"   Alpha (w=2.0), Beta (w=1.5), Gamma (w=1.0), Delta (w=1.0). Total Weight = 5.5")

    # Event #1: Friday Welcome BBQ ($120.00 paid by Alpha, all attend)
    m1_id = await add_meal(DB_PATH, trip_id, "Friday Welcome BBQ", f_alpha, 120.0)

    # Event #2: Saturday Breakfast ($60.00 paid by Beta, Delta skipped)
    m2_id = await add_meal(DB_PATH, trip_id, "Saturday Breakfast", f_beta, 60.0)
    await add_meal_absence(DB_PATH, m2_id, f_delta)

    # Event #3: Saturday Night Dinner ($180.00 paid by Gamma, Beta skipped)
    m3_id = await add_meal(DB_PATH, trip_id, "Saturday Night Dinner", f_gamma, 180.0)
    await add_meal_absence(DB_PATH, m3_id, f_beta)

    print("\n✅ Scenario 2: General Shared Expenses Added")
    # Shared Expense #1: Firewood ($80.00 paid by Alpha)
    se1_id = await add_shared_expense(DB_PATH, trip_id, f_alpha, "Firewood & Campsite Fee", 80.0)

    # Shared Expense #2: Gas ($50.00 paid by Delta)
    se2_id = await add_shared_expense(DB_PATH, trip_id, f_delta, "Gas / Fuel", 50.0)

    print("\n✅ Scenario 3: Custom-Weighted & Targeted Expenses Added")
    # Custom Expense #1: Boat Rental ($160.00 paid by Alpha, split Alpha w=3.0, Gamma w=1.0, Beta & Delta 0)
    g1_id = await create_grouping(DB_PATH, trip_id, "Custom Expense: Boat Rental")
    await add_or_update_grouping_member(DB_PATH, g1_id, f_alpha, weight=3.0, is_active=1)
    await add_or_update_grouping_member(DB_PATH, g1_id, f_beta, weight=0.0, is_active=0)
    await add_or_update_grouping_member(DB_PATH, g1_id, f_gamma, weight=1.0, is_active=1)
    await add_or_update_grouping_member(DB_PATH, g1_id, f_delta, weight=0.0, is_active=0)
    se3_id = await add_shared_expense(DB_PATH, trip_id, f_alpha, "Boat Rental", 160.0, grouping_id=g1_id)

    # Targeted Expense #2: Medicine ($45.00 paid by Beta for Delta)
    g2_id = await create_grouping(DB_PATH, trip_id, "Targeted: Medicine for Delta")
    await add_or_update_grouping_member(DB_PATH, g2_id, f_delta, weight=1.0, is_active=1)
    se4_id = await add_shared_expense(DB_PATH, trip_id, f_beta, "Medicine for Delta", 45.0, grouping_id=g2_id)

    print("\n✅ Scenario 4: Edit My Expenses & Correction Flow")
    # Alpha edits Firewood from $80.00 to $100.00
    await update_shared_expense_amount(DB_PATH, se1_id, 100.0)
    # Beta updates Medicine from $45.00 to $40.00
    await update_shared_expense_amount(DB_PATH, se4_id, 40.0)

    # Perform Settlement Calculation Audit
    families = await get_families(DB_PATH, trip_id)
    meals = await get_meals(DB_PATH, trip_id)
    expenses = await get_shared_expenses(DB_PATH, trip_id)

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

    result = calculate_settlement(
        families=families,
        meals=meals,
        meal_contributions=meal_conts,
        meal_absences=meal_abs,
        shared_expenses=expenses,
        meal_groupings=meal_groups,
        expense_groupings=expense_groups,
    )

    print("\n=======================================================")
    print("📊 MATHEMATICAL VERIFICATION & NET BALANCES (Precision: $0.01)")
    print("=======================================================")
    print(f"Total Trip Expenditure: ${result.total_spent:.2f}")

    family_names = {f["id"]: f["name"] for f in families}
    for fid, bal in result.balances.items():
        name = family_names[fid]
        sign = "+" if bal >= 0 else "-"
        print(f"• {name:<20}: Net Balance = {sign}${abs(bal):.2f}")

    print("\n💰 RECOMMENDED SETTLEMENT TRANSFERS:")
    for t in result.transfers:
        payer = family_names[t.from_family_id]
        receiver = family_names[t.to_family_id]
        print(f"👉 {payer} pays ${t.amount:.2f} to {receiver}")

    return {
        "trip_id": trip_id,
        "total_spent": result.total_spent,
        "balances": result.balances,
        "transfers": result.transfers,
        "families": families,
        "meals": meals,
        "expenses": expenses,
    }


if __name__ == "__main__":
    asyncio.run(run_simulation())
