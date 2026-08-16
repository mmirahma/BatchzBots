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

# Use production DB path matching config.py default ('bachztab.db')
RAW_DB = os.environ.get("BACHZTAB_DB_PATH", "bachztab.db")
DB_PATH = os.path.abspath(os.path.expanduser(RAW_DB))


async def run_simulation():
    print(f"=== Starting Multi-User Simulation on Live Production DB: {DB_PATH} ===")
    await init_db(DB_PATH)

    # Also populate shareit.db if it exists
    alt_db = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shareit.db"))
    db_paths = [DB_PATH]
    if os.path.exists(alt_db) and alt_db not in db_paths:
        db_paths.append(alt_db)

    for target_db in db_paths:
        await init_db(target_db)

        # Find existing group chat_ids from production DB
        chat_ids = []
        env_chat = os.environ.get("TARGET_CHAT_ID")
        if env_chat:
            try:
                chat_ids.append(int(env_chat))
            except ValueError:
                pass

        async with aiosqlite.connect(target_db) as db:
            async with db.execute("SELECT DISTINCT chat_id FROM trips WHERE chat_id IS NOT NULL AND chat_id != -100998877") as cursor:
                rows = await cursor.fetchall()
                for r in rows:
                    if r[0] not in chat_ids:
                        chat_ids.append(r[0])

        if not chat_ids:
            chat_ids = [-1004424770402, -5300784252]

        print(f"\n📍 Target Group Chat IDs for {os.path.basename(target_db)}: {chat_ids}")

        for chat_id in chat_ids:
            # 1. Setup Trip & Join Families
            trip_id = await create_trip(target_db, "High Sierra Camping Sim", chat_id=chat_id)
            f_alpha = await add_family(target_db, trip_id, "Family Alpha", 2.0, telegram_user_id=101)
            f_beta = await add_family(target_db, trip_id, "Family Beta", 1.5, telegram_user_id=102)
            f_gamma = await add_family(target_db, trip_id, "Family Gamma", 1.0, telegram_user_id=103)
            f_delta = await add_family(target_db, trip_id, "Family Delta", 1.0, telegram_user_id=104)

            print(f"   ✅ Created active trip 'High Sierra Camping Sim' (Trip ID: {trip_id}) for Chat ID: {chat_id}")

            # Event #1: Friday Welcome BBQ ($120.00 paid by Alpha, all attend)
            m1_id = await add_meal(target_db, trip_id, "Friday Welcome BBQ", f_alpha, 120.0)

            # Event #2: Saturday Breakfast ($60.00 paid by Beta, Delta skipped)
            m2_id = await add_meal(target_db, trip_id, "Saturday Breakfast", f_beta, 60.0)
            await add_meal_absence(target_db, m2_id, f_delta)

            # Event #3: Saturday Night Dinner ($180.00 paid by Gamma, Beta skipped)
            m3_id = await add_meal(target_db, trip_id, "Saturday Night Dinner", f_gamma, 180.0)
            await add_meal_absence(target_db, m3_id, f_beta)

            # Shared Expense #1: Firewood ($100.00 paid by Alpha)
            se1_id = await add_shared_expense(target_db, trip_id, f_alpha, "Firewood & Campsite Fee", 100.0)

            # Shared Expense #2: Gas ($50.00 paid by Delta)
            se2_id = await add_shared_expense(target_db, trip_id, f_delta, "Gas / Fuel", 50.0)

            # Custom Expense #1: Boat Rental ($160.00 paid by Alpha, split Alpha w=3.0, Gamma w=1.0, Beta & Delta 0)
            g1_id = await create_grouping(target_db, trip_id, "Custom Expense: Boat Rental")
            await add_or_update_grouping_member(target_db, g1_id, f_alpha, weight=3.0, is_active=1)
            await add_or_update_grouping_member(target_db, g1_id, f_beta, weight=0.0, is_active=0)
            await add_or_update_grouping_member(target_db, g1_id, f_gamma, weight=1.0, is_active=1)
            await add_or_update_grouping_member(target_db, g1_id, f_delta, weight=0.0, is_active=0)
            se3_id = await add_shared_expense(target_db, trip_id, f_alpha, "Boat Rental", 160.0, grouping_id=g1_id)

            # Targeted Expense #2: Medicine ($40.00 paid by Beta for Delta)
            g2_id = await create_grouping(target_db, trip_id, "Targeted: Medicine for Delta")
            await add_or_update_grouping_member(target_db, g2_id, f_delta, weight=1.0, is_active=1)
            se4_id = await add_shared_expense(target_db, trip_id, f_beta, "Medicine for Delta", 40.0, grouping_id=g2_id)

    print("\n=======================================================")
    print("🚀 LIVE PRODUCTION DATABASES POPULATED SUCCESSFULLY!")
    print("=======================================================")
    print("You can now test the bot live in Telegram:")
    print("• Send /status   ➔ Displays Live Monospace Status Tables")
    print("• Send /settle   ➔ Displays Live Net Balances & Debt Transfers")
    print("• Send /meals    ➔ Displays Live Meals/Events Breakdown")
    print("• Tap '✏️ Edit My Expenses' to edit items live in chat!")

    return True


if __name__ == "__main__":
    asyncio.run(run_simulation())
