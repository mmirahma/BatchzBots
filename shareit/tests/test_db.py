import pytest
import pytest_asyncio
import os
import tempfile

from bot.db import (
    init_db, create_trip, get_active_trip, end_trip,
    add_family, get_family, get_families, update_family_weight,
    add_meal, add_meal_contribution, add_meal_absence,
    get_meals, get_meal_contributions, get_meal_absences,
    add_shared_expense, get_shared_expenses,
    delete_meal, update_contribution_amount, get_meal_by_number,
)


@pytest_asyncio.fixture
async def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    await init_db(path)
    yield path
    os.unlink(path)


@pytest.mark.asyncio
async def test_create_and_get_active_trip(db_path):
    trip_id = await create_trip(db_path, "Summer Camp", chat_id=12345)
    assert trip_id == 1
    trip = await get_active_trip(db_path, chat_id=12345)
    assert trip is not None
    assert trip["name"] == "Summer Camp"
    assert trip["chat_id"] == 12345
    assert trip["active"] == 1


@pytest.mark.asyncio
async def test_end_trip(db_path):
    trip_id = await create_trip(db_path, "Summer Camp", chat_id=12345)
    await end_trip(db_path, trip_id)
    trip = await get_active_trip(db_path, chat_id=12345)
    assert trip is None


@pytest.mark.asyncio
async def test_add_and_get_family(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Mohsen's family", 2.5, telegram_user_id=999)
    assert family_id == 1
    family = await get_family(db_path, trip_id, telegram_user_id=999)
    assert family is not None
    assert family["name"] == "Mohsen's family"
    assert family["weight"] == 2.5


@pytest.mark.asyncio
async def test_get_families(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    await add_family(db_path, trip_id, "Family B", 3.0, telegram_user_id=2)
    families = await get_families(db_path, trip_id)
    assert len(families) == 2


@pytest.mark.asyncio
async def test_update_family_weight(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    await update_family_weight(db_path, family_id, 3.5)
    family = await get_family(db_path, trip_id, telegram_user_id=1)
    assert family["weight"] == 3.5


@pytest.mark.asyncio
async def test_meal_workflow(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    meal_id = await add_meal(db_path, trip_id, "Saturday BBQ", family_id, 50.0)
    assert meal_id == 1
    meals = await get_meals(db_path, trip_id)
    assert len(meals) == 1
    assert meals[0]["name"] == "Saturday BBQ"
    contributions = await get_meal_contributions(db_path, meal_id)
    assert len(contributions) == 1
    assert contributions[0]["amount"] == 50.0


@pytest.mark.asyncio
async def test_meal_contribution(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    f1 = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    f2 = await add_family(db_path, trip_id, "Family B", 2.0, telegram_user_id=2)
    meal_id = await add_meal(db_path, trip_id, "Dinner", f1, 40.0)
    await add_meal_contribution(db_path, meal_id, f2, 20.0)
    contributions = await get_meal_contributions(db_path, meal_id)
    assert len(contributions) == 2
    total = sum(c["amount"] for c in contributions)
    assert total == 60.0


@pytest.mark.asyncio
async def test_meal_absence(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    f1 = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    f2 = await add_family(db_path, trip_id, "Family B", 2.0, telegram_user_id=2)
    meal_id = await add_meal(db_path, trip_id, "Lunch", f1, 30.0)
    await add_meal_absence(db_path, meal_id, f2)
    absences = await get_meal_absences(db_path, meal_id)
    assert f2 in absences


@pytest.mark.asyncio
async def test_shared_expense(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    expense_id = await add_shared_expense(db_path, trip_id, family_id, "Firewood", 25.0)
    assert expense_id == 1
    expenses = await get_shared_expenses(db_path, trip_id)
    assert len(expenses) == 1
    assert expenses[0]["description"] == "Firewood"
    assert expenses[0]["amount"] == 25.0


@pytest.mark.asyncio
async def test_delete_meal(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    meal_id = await add_meal(db_path, trip_id, "Breakfast", family_id, 15.0)
    await delete_meal(db_path, meal_id)
    meals = await get_meals(db_path, trip_id)
    assert len(meals) == 0


@pytest.mark.asyncio
async def test_update_contribution_amount(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    meal_id = await add_meal(db_path, trip_id, "Dinner", family_id, 40.0)
    await update_contribution_amount(db_path, meal_id, family_id, 55.0)
    contributions = await get_meal_contributions(db_path, meal_id)
    assert contributions[0]["amount"] == 55.0


@pytest.mark.asyncio
async def test_get_meal_by_number(db_path):
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    family_id = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    await add_meal(db_path, trip_id, "Breakfast", family_id, 10.0)
    await add_meal(db_path, trip_id, "Lunch", family_id, 20.0)
    meal = await get_meal_by_number(db_path, trip_id, 2)
    assert meal is not None
    assert meal["name"] == "Lunch"
    meal = await get_meal_by_number(db_path, trip_id, 99)
    assert meal is None


@pytest.mark.asyncio
async def test_groupings_and_associations(db_path):
    from bot.db import get_meal_grouping_members
    trip_id = await create_trip(db_path, "Camp", chat_id=100)
    f1 = await add_family(db_path, trip_id, "Family A", 2.0, telegram_user_id=1)
    f2 = await add_family(db_path, trip_id, "Family B", 1.5, telegram_user_id=2)
    meal_id = await add_meal(db_path, trip_id, "Dinner", f1, 40.0)

    members = await get_meal_grouping_members(db_path, meal_id)
    assert len(members) == 2
    assert members[0]["weight"] == 2.0
    assert members[1]["weight"] == 1.5
    assert members[0]["is_active"] == 1

    await add_meal_absence(db_path, meal_id, f2)
    members_after = await get_meal_grouping_members(db_path, meal_id)
    m2 = next(m for m in members_after if m["family_id"] == f2)
    assert m2["is_active"] == 0

