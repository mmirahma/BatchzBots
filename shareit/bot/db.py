import os
import aiosqlite


async def init_db(db_path: str) -> None:
    """Initialize the database schema."""
    parent = os.path.dirname(os.path.abspath(os.path.expanduser(db_path)))
    if parent:
        os.makedirs(parent, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                expected_families INTEGER,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL REFERENCES trips(id),
                name TEXT NOT NULL,
                weight REAL NOT NULL,
                telegram_user_id INTEGER NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS groupings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL REFERENCES trips(id),
                name TEXT NOT NULL,
                is_template INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS grouping_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grouping_id INTEGER NOT NULL REFERENCES groupings(id) ON DELETE CASCADE,
                family_id INTEGER NOT NULL REFERENCES families(id),
                weight REAL NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                UNIQUE(grouping_id, family_id)
            );
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL REFERENCES trips(id),
                grouping_id INTEGER REFERENCES groupings(id),
                name TEXT NOT NULL,
                meal_number INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS meal_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
                family_id INTEGER NOT NULL REFERENCES families(id),
                amount REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meal_absences (
                meal_id INTEGER NOT NULL REFERENCES meals(id) ON DELETE CASCADE,
                family_id INTEGER NOT NULL REFERENCES families(id),
                PRIMARY KEY (meal_id, family_id)
            );
            CREATE TABLE IF NOT EXISTS shared_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL REFERENCES trips(id),
                grouping_id INTEGER REFERENCES groupings(id),
                family_id INTEGER NOT NULL REFERENCES families(id),
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        # Migrations for existing DB files without grouping_id column
        async with db.execute("PRAGMA table_info(meals)") as cursor:
            cols = [row[1] for row in await cursor.fetchall()]
            if "grouping_id" not in cols:
                await db.execute("ALTER TABLE meals ADD COLUMN grouping_id INTEGER REFERENCES groupings(id)")

        async with db.execute("PRAGMA table_info(shared_expenses)") as cursor:
            cols = [row[1] for row in await cursor.fetchall()]
            if "grouping_id" not in cols:
                await db.execute("ALTER TABLE shared_expenses ADD COLUMN grouping_id INTEGER REFERENCES groupings(id)")

        await db.commit()


async def create_trip(db_path: str, name: str, chat_id: int, expected_families: int | None = None) -> int:
    """Create a new trip and return its ID, deactivating any prior active trips for this chat."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE trips SET active = 0 WHERE chat_id = ?", (chat_id,))
        cursor = await db.execute(
            "INSERT INTO trips (name, chat_id, expected_families) VALUES (?, ?, ?)",
            (name, chat_id, expected_families),
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_trip(db_path: str, chat_id: int) -> dict | None:
    """Get the active trip for a chat, or None."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trips WHERE chat_id = ? AND active = 1 ORDER BY id DESC LIMIT 1", (chat_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_all_active_trips(db_path: str) -> list[dict]:
    """Get all active trips across all chats."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trips WHERE active = 1") as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_families_with_activity(db_path: str, trip_id: int) -> set[int]:
    """Get family IDs that have logged at least one meal contribution or expense."""
    async with aiosqlite.connect(db_path) as db:
        active_ids = set()
        # Families who contributed to meals
        async with db.execute(
            "SELECT DISTINCT mc.family_id FROM meal_contributions mc "
            "JOIN meals m ON mc.meal_id = m.id WHERE m.trip_id = ?",
            (trip_id,),
        ) as cursor:
            for row in await cursor.fetchall():
                active_ids.add(row[0])
        # Families who logged shared expenses
        async with db.execute(
            "SELECT DISTINCT family_id FROM shared_expenses WHERE trip_id = ?",
            (trip_id,),
        ) as cursor:
            for row in await cursor.fetchall():
                active_ids.add(row[0])
        return active_ids


async def end_trip(db_path: str, trip_id: int) -> None:
    """Mark a trip as inactive."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE trips SET active = 0 WHERE id = ?", (trip_id,))
        await db.commit()


async def resume_last_trip(db_path: str, chat_id: int) -> dict | None:
    """Reactivate the most recently ended trip for a chat, if any."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trips WHERE chat_id = ? ORDER BY id DESC LIMIT 1",
            (chat_id,),
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            trip = dict(row)
            await db.execute("UPDATE trips SET active = 0 WHERE chat_id = ?", (chat_id,))
            await db.execute("UPDATE trips SET active = 1 WHERE id = ?", (trip["id"],))
            await db.commit()
            trip["active"] = 1
            return trip


async def get_past_trips(db_path: str, chat_id: int) -> list[dict]:
    """Get all inactive trips for a chat, ordered by most recent."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trips WHERE chat_id = ? AND active = 0 ORDER BY id DESC",
            (chat_id,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_trip_by_id(db_path: str, trip_id: int) -> dict | None:
    """Get a trip by its ID."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM trips WHERE id = ?", (trip_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_family(db_path: str, trip_id: int, name: str, weight: float, telegram_user_id: int) -> int:
    """Add a family to a trip and sync to active meal groupings. Return the family ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO families (trip_id, name, weight, telegram_user_id) VALUES (?, ?, ?, ?)",
            (trip_id, name, weight, telegram_user_id),
        )
        family_id = cursor.lastrowid
        # Sync to all existing meal groupings for this trip
        async with db.execute("SELECT grouping_id FROM meals WHERE trip_id = ? AND grouping_id IS NOT NULL", (trip_id,)) as m_cursor:
            meal_rows = await m_cursor.fetchall()
            for m_row in meal_rows:
                g_id = m_row[0]
                await db.execute(
                    "INSERT OR IGNORE INTO grouping_members (grouping_id, family_id, weight, is_active) VALUES (?, ?, ?, 1)",
                    (g_id, family_id, weight),
                )
        await db.commit()
        return family_id


async def get_family(db_path: str, trip_id: int, telegram_user_id: int) -> dict | None:
    """Get a family by trip and telegram user ID."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM families WHERE trip_id = ? AND telegram_user_id = ?",
            (trip_id, telegram_user_id),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_families(db_path: str, trip_id: int) -> list[dict]:
    """Get all families for a trip."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM families WHERE trip_id = ?", (trip_id,)
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def update_family_weight(db_path: str, family_id: int, weight: float) -> None:
    """Update a family's share weight in families table and active meal groupings."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE families SET weight = ? WHERE id = ?", (weight, family_id))
        # Update weight in existing groupings for active members
        await db.execute(
            "UPDATE grouping_members SET weight = ? WHERE family_id = ?",
            (weight, family_id),
        )
        await db.commit()


# --- Grouping functions ---

async def create_grouping(db_path: str, trip_id: int, name: str, is_template: int = 0) -> int:
    """Create a new grouping and return its ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO groupings (trip_id, name, is_template) VALUES (?, ?, ?)",
            (trip_id, name, is_template),
        )
        await db.commit()
        return cursor.lastrowid


async def add_or_update_grouping_member(
    db_path: str, grouping_id: int, family_id: int, weight: float, is_active: int = 1
) -> None:
    """Insert or update a member association in a grouping."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO grouping_members (grouping_id, family_id, weight, is_active) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(grouping_id, family_id) DO UPDATE SET weight = excluded.weight, is_active = excluded.is_active",
            (grouping_id, family_id, weight, is_active),
        )
        await db.commit()


async def set_grouping_member_active(db_path: str, grouping_id: int, family_id: int, is_active: int) -> None:
    """Set the active status of a family association in a grouping."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE grouping_members SET is_active = ? WHERE grouping_id = ? AND family_id = ?",
            (is_active, grouping_id, family_id),
        )
        await db.commit()


async def get_grouping_members(db_path: str, grouping_id: int) -> list[dict]:
    """Get all members of a grouping with family names, weights, and active status."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT gm.*, f.name as family_name, f.telegram_user_id "
            "FROM grouping_members gm "
            "JOIN families f ON gm.family_id = f.id "
            "WHERE gm.grouping_id = ? ORDER BY f.id ASC",
            (grouping_id,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_meal_grouping_members(db_path: str, meal_id: int) -> list[dict]:
    """Get all grouping member associations for a specific meal."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT gm.*, f.name as family_name "
            "FROM meals m "
            "JOIN grouping_members gm ON m.grouping_id = gm.grouping_id "
            "JOIN families f ON gm.family_id = f.id "
            "WHERE m.id = ? ORDER BY f.id ASC",
            (meal_id,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


# --- Meals and Expenses ---

async def add_meal(db_path: str, trip_id: int, name: str, family_id: int, amount: float) -> int:
    """Create a meal with an associated grouping, optionally with an initial contribution. Returns meal ID."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT COALESCE(MAX(meal_number), 0) + 1 FROM meals WHERE trip_id = ?",
            (trip_id,),
        ) as cursor:
            row = await cursor.fetchone()
            meal_number = row[0]

        # 1. Create a grouping for this meal
        g_cursor = await db.execute(
            "INSERT INTO groupings (trip_id, name) VALUES (?, ?)",
            (trip_id, f"Meal #{meal_number} {name}"),
        )
        grouping_id = g_cursor.lastrowid

        # 2. Populate grouping_members with all current families and their weights
        async with db.execute("SELECT id, weight FROM families WHERE trip_id = ?", (trip_id,)) as f_cursor:
            families = await f_cursor.fetchall()
            for f_id, f_weight in families:
                await db.execute(
                    "INSERT INTO grouping_members (grouping_id, family_id, weight, is_active) VALUES (?, ?, ?, 1)",
                    (grouping_id, f_id, f_weight),
                )

        # 3. Create the meal linking to grouping_id
        cursor = await db.execute(
            "INSERT INTO meals (trip_id, grouping_id, name, meal_number) VALUES (?, ?, ?, ?)",
            (trip_id, grouping_id, name, meal_number),
        )
        meal_id = cursor.lastrowid

        if family_id is not None and amount is not None and amount > 0:
            await db.execute(
                "INSERT INTO meal_contributions (meal_id, family_id, amount) VALUES (?, ?, ?)",
                (meal_id, family_id, amount),
            )
        await db.commit()
        return meal_id


async def add_meal_contribution(db_path: str, meal_id: int, family_id: int, amount: float) -> None:
    """Add a contribution to an existing meal."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO meal_contributions (meal_id, family_id, amount) VALUES (?, ?, ?)",
            (meal_id, family_id, amount),
        )
        await db.commit()


async def add_meal_absence(db_path: str, meal_id: int, family_id: int) -> None:
    """Mark a family as absent from a meal (updates meal_absences and grouping_members)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO meal_absences (meal_id, family_id) VALUES (?, ?)",
            (meal_id, family_id),
        )
        # Sync is_active = 0 in grouping_members for this meal's grouping
        async with db.execute("SELECT grouping_id FROM meals WHERE id = ?", (meal_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                grouping_id = row[0]
                await db.execute(
                    "UPDATE grouping_members SET is_active = 0 WHERE grouping_id = ? AND family_id = ?",
                    (grouping_id, family_id),
                )
        await db.commit()


async def remove_meal_absence(db_path: str, meal_id: int, family_id: int) -> None:
    """Mark a family as present for a meal (removes from meal_absences and updates grouping_members)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "DELETE FROM meal_absences WHERE meal_id = ? AND family_id = ?",
            (meal_id, family_id),
        )
        # Sync is_active = 1 in grouping_members for this meal's grouping
        async with db.execute("SELECT grouping_id FROM meals WHERE id = ?", (meal_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                grouping_id = row[0]
                async with db.execute("SELECT weight FROM families WHERE id = ?", (family_id,)) as f_cursor:
                    f_row = await f_cursor.fetchone()
                    f_weight = f_row[0] if f_row else 1.0
                await db.execute(
                    "INSERT INTO grouping_members (grouping_id, family_id, weight, is_active) VALUES (?, ?, ?, 1) "
                    "ON CONFLICT(grouping_id, family_id) DO UPDATE SET is_active = 1, weight = ?",
                    (grouping_id, family_id, f_weight, f_weight),
                )
        await db.commit()


async def get_meals(db_path: str, trip_id: int) -> list[dict]:
    """Get all meals for a trip, ordered by meal number."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meals WHERE trip_id = ? ORDER BY meal_number", (trip_id,)
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_meal_contributions(db_path: str, meal_id: int) -> list[dict]:
    """Get all contributions for a meal."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT mc.*, f.name as family_name FROM meal_contributions mc "
            "JOIN families f ON mc.family_id = f.id WHERE mc.meal_id = ? "
            "ORDER BY mc.id ASC",
            (meal_id,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def get_meal_absences(db_path: str, meal_id: int) -> list[int]:
    """Get list of family IDs absent from a meal."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT family_id FROM meal_absences WHERE meal_id = ?", (meal_id,)
        ) as cursor:
            return [row[0] for row in await cursor.fetchall()]


async def add_shared_expense(
    db_path: str, trip_id: int, family_id: int, description: str, amount: float, grouping_id: int | None = None
) -> int:
    """Add a shared expense (optionally linked to a grouping) and return its ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO shared_expenses (trip_id, grouping_id, family_id, description, amount) VALUES (?, ?, ?, ?, ?)",
            (trip_id, grouping_id, family_id, description, amount),
        )
        await db.commit()
        return cursor.lastrowid


async def get_shared_expenses(db_path: str, trip_id: int) -> list[dict]:
    """Get all shared expenses for a trip."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT se.*, f.name as family_name FROM shared_expenses se "
            "JOIN families f ON se.family_id = f.id WHERE se.trip_id = ?",
            (trip_id,),
        ) as cursor:
            return [dict(row) for row in await cursor.fetchall()]


async def delete_meal(db_path: str, meal_id: int) -> None:
    """Delete a meal and its associated grouping, contributions, and absences."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute("SELECT grouping_id FROM meals WHERE id = ?", (meal_id,)) as cursor:
            row = await cursor.fetchone()
            grouping_id = row[0] if row else None

        await db.execute("DELETE FROM meal_contributions WHERE meal_id = ?", (meal_id,))
        await db.execute("DELETE FROM meal_absences WHERE meal_id = ?", (meal_id,))
        await db.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
        if grouping_id:
            await db.execute("DELETE FROM grouping_members WHERE grouping_id = ?", (grouping_id,))
            await db.execute("DELETE FROM groupings WHERE id = ?", (grouping_id,))
        await db.commit()


async def update_contribution_amount(db_path: str, meal_id: int, family_id: int, amount: float) -> None:
    """Update a family's contribution amount for a meal (updates their first contribution)."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "UPDATE meal_contributions SET amount = ? WHERE id = "
            "(SELECT id FROM meal_contributions WHERE meal_id = ? AND family_id = ? ORDER BY id ASC LIMIT 1)",
            (amount, meal_id, family_id),
        )
        await db.commit()


async def get_meal_by_number(db_path: str, trip_id: int, meal_number: int) -> dict | None:
    """Get a meal by its display number within a trip."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meals WHERE trip_id = ? AND meal_number = ?",
            (trip_id, meal_number),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_meal_by_name(db_path: str, trip_id: int, name: str) -> dict | None:
    """Get a meal by name (case-insensitive) within a trip."""
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM meals WHERE trip_id = ? AND LOWER(name) = LOWER(?)",
            (trip_id, name),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def get_family_expenses(db_path: str, trip_id: int, family_id: int) -> list[dict]:
    """Get all meal contributions and general shared expenses paid by a specific family in a trip."""
    results = []
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        # 1. Meal contributions
        async with db.execute(
            "SELECT mc.id as item_id, mc.amount, m.meal_number, m.name as item_name, mc.meal_id, 'meal' as type "
            "FROM meal_contributions mc "
            "JOIN meals m ON mc.meal_id = m.id "
            "WHERE m.trip_id = ? AND mc.family_id = ? ORDER BY m.meal_number ASC",
            (trip_id, family_id),
        ) as cursor:
            for row in await cursor.fetchall():
                results.append(dict(row))

        # 2. General shared expenses
        async with db.execute(
            "SELECT se.id as item_id, se.amount, se.description as item_name, 'expense' as type "
            "FROM shared_expenses se "
            "WHERE se.trip_id = ? AND se.family_id = ? ORDER BY se.id ASC",
            (trip_id, family_id),
        ) as cursor:
            for row in await cursor.fetchall():
                results.append(dict(row))

    return results


async def update_shared_expense_amount(db_path: str, expense_id: int, amount: float) -> None:
    """Update amount of a general shared expense."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE shared_expenses SET amount = ? WHERE id = ?", (amount, expense_id))
        await db.commit()


async def delete_shared_expense(db_path: str, expense_id: int) -> None:
    """Delete a general shared expense."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM shared_expenses WHERE id = ?", (expense_id,))
        await db.commit()


async def delete_meal_contribution_by_id(db_path: str, contribution_id: int) -> None:
    """Delete a specific meal contribution by ID."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM meal_contributions WHERE id = ?", (contribution_id,))
        await db.commit()


async def update_meal_contribution_amount_by_id(db_path: str, contribution_id: int, amount: float) -> None:
    """Update amount of a meal contribution by ID."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE meal_contributions SET amount = ? WHERE id = ?", (amount, contribution_id))
        await db.commit()

