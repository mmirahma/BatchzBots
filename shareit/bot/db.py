from __future__ import annotations

import aiosqlite


async def init_db(db_path: str) -> None:
    """Initialize the database schema."""
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
            CREATE TABLE IF NOT EXISTS meals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trip_id INTEGER NOT NULL REFERENCES trips(id),
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
                family_id INTEGER NOT NULL REFERENCES families(id),
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        await db.commit()


async def create_trip(db_path: str, name: str, chat_id: int, expected_families: int | None = None) -> int:
    """Create a new trip and return its ID."""
    async with aiosqlite.connect(db_path) as db:
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
            "SELECT * FROM trips WHERE chat_id = ? AND active = 1", (chat_id,)
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


async def add_family(db_path: str, trip_id: int, name: str, weight: float, telegram_user_id: int) -> int:
    """Add a family to a trip and return the family ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO families (trip_id, name, weight, telegram_user_id) VALUES (?, ?, ?, ?)",
            (trip_id, name, weight, telegram_user_id),
        )
        await db.commit()
        return cursor.lastrowid


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
    """Update a family's share weight."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("UPDATE families SET weight = ? WHERE id = ?", (weight, family_id))
        await db.commit()


async def add_meal(db_path: str, trip_id: int, name: str, family_id: int, amount: float) -> int:
    """Create a meal, optionally with an initial contribution. Returns meal ID."""
    async with aiosqlite.connect(db_path) as db:
        async with db.execute(
            "SELECT COALESCE(MAX(meal_number), 0) + 1 FROM meals WHERE trip_id = ?",
            (trip_id,),
        ) as cursor:
            row = await cursor.fetchone()
            meal_number = row[0]
        cursor = await db.execute(
            "INSERT INTO meals (trip_id, name, meal_number) VALUES (?, ?, ?)",
            (trip_id, name, meal_number),
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
    """Mark a family as absent from a meal."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT OR IGNORE INTO meal_absences (meal_id, family_id) VALUES (?, ?)",
            (meal_id, family_id),
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


async def add_shared_expense(db_path: str, trip_id: int, family_id: int, description: str, amount: float) -> int:
    """Add a shared expense and return its ID."""
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute(
            "INSERT INTO shared_expenses (trip_id, family_id, description, amount) VALUES (?, ?, ?, ?)",
            (trip_id, family_id, description, amount),
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
    """Delete a meal and its contributions/absences."""
    async with aiosqlite.connect(db_path) as db:
        await db.execute("DELETE FROM meal_contributions WHERE meal_id = ?", (meal_id,))
        await db.execute("DELETE FROM meal_absences WHERE meal_id = ?", (meal_id,))
        await db.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
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
