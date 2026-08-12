from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Transfer:
    from_family_id: int
    to_family_id: int
    amount: float


@dataclass
class SettlementResult:
    balances: dict[int, float]
    transfers: list[Transfer]
    total_spent: float


def calculate_settlement(
    families: list[dict],
    meals: list[dict],
    meal_contributions: dict[int, list[dict]],
    meal_absences: dict[int, list[int]],
    shared_expenses: list[dict],
    meal_groupings: dict[int, list[dict]] | None = None,
    expense_groupings: dict[int, list[dict]] | None = None,
) -> SettlementResult:
    """
    Calculate the settlement for a trip.

    Args:
        families: List of family dicts with 'id', 'name', 'weight'
        meals: List of meal dicts with 'id'
        meal_contributions: Map of meal_id -> list of {'family_id', 'amount'}
        meal_absences: Map of meal_id -> list of absent family_ids
        shared_expenses: List of {'family_id', 'description', 'amount'}
        meal_groupings: Map of meal_id -> list of {'family_id', 'weight', 'is_active'}
        expense_groupings: Map of expense_id -> list of {'family_id', 'weight', 'is_active'}

    Returns:
        SettlementResult with balances, optimized transfers, and total spent
    """
    family_ids = [f["id"] for f in families]
    weights = {f["id"]: f["weight"] for f in families}
    paid = {fid: 0.0 for fid in family_ids}
    owed = {fid: 0.0 for fid in family_ids}
    total_spent = 0.0

    # Process meals
    for meal in meals:
        meal_id = meal["id"]
        contributions = meal_contributions.get(meal_id, [])
        absences = meal_absences.get(meal_id, [])
        meal_total = sum(c["amount"] for c in contributions)
        total_spent += meal_total

        for c in contributions:
            if c["family_id"] in paid:
                paid[c["family_id"]] += c["amount"]

        group_members = (meal_groupings or {}).get(meal_id)
        if group_members:
            # Use grouping associations
            attending = [
                m for m in group_members
                if m.get("is_active", 1) != 0 and m["family_id"] not in absences and m["family_id"] in owed
            ]
            total_weight = sum(m["weight"] for m in attending)
            if total_weight > 0:
                for m in attending:
                    owed[m["family_id"]] += meal_total * (m["weight"] / total_weight)
        else:
            # Fallback to default family weights minus absences
            attending = [fid for fid in family_ids if fid not in absences]
            if attending:
                total_weight = sum(weights[fid] for fid in attending)
                if total_weight > 0:
                    for fid in attending:
                        owed[fid] += meal_total * (weights[fid] / total_weight)

    # Process shared expenses
    all_weight = sum(weights[fid] for fid in family_ids)
    for expense in shared_expenses:
        amount = expense["amount"]
        total_spent += amount
        if expense["family_id"] in paid:
            paid[expense["family_id"]] += amount

        expense_id = expense.get("id")
        group_members = (expense_groupings or {}).get(expense_id) if expense_id else None

        if group_members:
            attending = [m for m in group_members if m.get("is_active", 1) != 0 and m["family_id"] in owed]
            total_weight = sum(m["weight"] for m in attending)
            if total_weight > 0:
                for m in attending:
                    owed[m["family_id"]] += amount * (m["weight"] / total_weight)
        else:
            if all_weight > 0:
                for fid in family_ids:
                    owed[fid] += amount * (weights[fid] / all_weight)

    # Net balances (positive = owed money, negative = owes money)
    balances = {fid: paid[fid] - owed[fid] for fid in family_ids}
    transfers = _optimize_transfers(balances)
    return SettlementResult(balances=balances, transfers=transfers, total_spent=total_spent)


def _optimize_transfers(balances: dict[int, float]) -> list[Transfer]:
    """Minimize number of transfers using greedy debt settlement."""
    creditors = [[fid, bal] for fid, bal in balances.items() if bal > 0.01]
    debtors = [[fid, -bal] for fid, bal in balances.items() if bal < -0.01]
    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])
    transfers = []

    while creditors and debtors:
        cr = creditors[0]
        dr = debtors[0]
        amount = round(min(cr[1], dr[1]), 2)
        if amount > 0:
            transfers.append(Transfer(from_family_id=dr[0], to_family_id=cr[0], amount=amount))
        cr[1] -= amount
        dr[1] -= amount
        if cr[1] < 0.01:
            creditors.pop(0)
        if dr[1] < 0.01:
            debtors.pop(0)
        creditors.sort(key=lambda x: -x[1])
        debtors.sort(key=lambda x: -x[1])

    return transfers
