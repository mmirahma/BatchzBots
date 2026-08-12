import pytest
from bot.settlement import calculate_settlement, SettlementResult, Transfer


def make_family(id: int, name: str, weight: float) -> dict:
    return {"id": id, "name": name, "weight": weight}


def test_simple_two_family_split():
    """Two equal families, one pays for a meal both attend."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 2.0)]
    meals = [{"id": 1, "name": "Dinner", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 100.0}]}
    meal_absences = {1: []}
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, [])
    assert result.total_spent == 100.0
    assert len(result.transfers) == 1
    assert result.transfers[0].from_family_id == 2
    assert result.transfers[0].to_family_id == 1
    assert result.transfers[0].amount == pytest.approx(50.0)


def test_weighted_split():
    """Family A (weight 3) and Family B (weight 1). A pays 100."""
    families = [make_family(1, "A", 3.0), make_family(2, "B", 1.0)]
    meals = [{"id": 1, "name": "Lunch", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 100.0}]}
    meal_absences = {1: []}
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, [])
    assert len(result.transfers) == 1
    assert result.transfers[0].amount == pytest.approx(25.0)


def test_meal_absence():
    """Family B skips a meal — only A's share matters."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 2.0)]
    meals = [{"id": 1, "name": "Dinner", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 80.0}]}
    meal_absences = {1: [2]}
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, [])
    assert len(result.transfers) == 0


def test_shared_expense_split():
    """Shared expense split by weight among all families."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 1.0), make_family(3, "C", 1.0)]
    shared_expenses = [{"family_id": 1, "description": "Firewood", "amount": 40.0}]
    result = calculate_settlement(families, [], {}, {}, shared_expenses)
    assert result.total_spent == 40.0
    assert len(result.transfers) == 2
    total_to_a = sum(t.amount for t in result.transfers if t.to_family_id == 1)
    assert total_to_a == pytest.approx(20.0)


def test_multiple_contributors_to_meal():
    """Two families contribute to one meal."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 2.0), make_family(3, "C", 2.0)]
    meals = [{"id": 1, "name": "BBQ", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 30.0}, {"family_id": 2, "amount": 30.0}]}
    meal_absences = {1: []}
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, [])
    assert result.total_spent == 60.0
    total_from_c = sum(t.amount for t in result.transfers if t.from_family_id == 3)
    assert total_from_c == pytest.approx(20.0)


def test_optimized_transfers():
    """Verify transfer optimization reduces number of payments."""
    families = [make_family(1, "A", 1.0), make_family(2, "B", 1.0), make_family(3, "C", 1.0), make_family(4, "D", 1.0)]
    meals = [{"id": 1, "name": "Dinner", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 100.0}]}
    meal_absences = {1: []}
    shared_expenses = [{"family_id": 2, "description": "Wood", "amount": 60.0}]
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, shared_expenses)
    assert len(result.transfers) <= 3
    assert result.total_spent == 160.0


def test_no_expenses():
    """No meals or expenses — no transfers."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 2.0)]
    result = calculate_settlement(families, [], {}, {}, [])
    assert result.total_spent == 0.0
    assert len(result.transfers) == 0


def test_everyone_pays_equally():
    """When everyone pays their exact share — no transfers needed."""
    families = [make_family(1, "A", 1.0), make_family(2, "B", 1.0)]
    meals = [{"id": 1, "name": "M1", "meal_number": 1}, {"id": 2, "name": "M2", "meal_number": 2}]
    meal_contributions = {1: [{"family_id": 1, "amount": 50.0}], 2: [{"family_id": 2, "amount": 50.0}]}
    meal_absences = {1: [], 2: []}
    result = calculate_settlement(families, meals, meal_contributions, meal_absences, [])
    assert len(result.transfers) == 0


def test_meal_grouping_settlement():
    """Test settlement using explicit meal groupings with custom weights."""
    families = [make_family(1, "A", 2.0), make_family(2, "B", 2.0)]
    meals = [{"id": 1, "name": "Dinner", "meal_number": 1}]
    meal_contributions = {1: [{"family_id": 1, "amount": 100.0}]}
    meal_absences = {1: []}
    meal_groupings = {
        1: [
            {"family_id": 1, "weight": 3.0, "is_active": 1},
            {"family_id": 2, "weight": 1.0, "is_active": 1},
        ]
    }
    result = calculate_settlement(
        families, meals, meal_contributions, meal_absences, [], meal_groupings=meal_groupings
    )
    assert len(result.transfers) == 1
    assert result.transfers[0].amount == pytest.approx(25.0)

