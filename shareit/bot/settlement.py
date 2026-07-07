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
) -> SettlementResult:
    """
    Calculate the settlement for a trip.

    Args:
        families: List of family dicts with 'id', 'name', 'weight'
        meals: List of meal dicts with 'id'
        meal_contributions: Map of meal_id -> list of {'family_id', 'amount'}
        meal_absences: Map of meal_id -> list of absent family_ids
        shared_expenses: List of {'family_id', 'description', 'amount'}

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
            paid[c["family_id"]] += c["amount"]

        attending = [fid for fid in family_ids if fid not in absences]
        if not attending:
            continue
        total_weight = sum(weights[fid] for fid in attending)
        if total_weight == 0:
            continue
        for fid in attending:
            owed[fid] += meal_total * (weights[fid] / total_weight)

    # Process shared expenses (split among ALL families by weight)
    all_weight = sum(weights[fid] for fid in family_ids)
    for expense in shared_expenses:
        amount = expense["amount"]
        total_spent += amount
        paid[expense["family_id"]] += amount
        if all_weight == 0:
            continue
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
