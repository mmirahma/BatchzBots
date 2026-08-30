from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Transfer:
    from_family_id: int
    to_family_id: int
    amount: float


@dataclass
class ItemShare:
    item_id: int
    item_name: str
    item_type: str  # "meal" or "expense"
    total_amount: float
    family_shares: dict[int, float]  # family_id -> dollar amount owed
    family_percentages: dict[int, float]  # family_id -> percentage (0.0 to 100.0)
    payer_family_ids: list[int] = field(default_factory=list)
    notes: str = ""


@dataclass
class SettlementResult:
    balances: dict[int, float]
    transfers: list[Transfer]
    total_spent: float
    paid_by_family: dict[int, float] = field(default_factory=dict)
    owed_by_family: dict[int, float] = field(default_factory=dict)
    item_shares: list[ItemShare] = field(default_factory=list)


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
        meals: List of meal dicts with 'id', 'name', 'meal_number'
        meal_contributions: Map of meal_id -> list of {'family_id', 'amount'}
        meal_absences: Map of meal_id -> list of absent family_ids
        shared_expenses: List of {'id', 'family_id', 'description', 'amount'}
        meal_groupings: Map of meal_id -> list of {'family_id', 'weight', 'is_active'}
        expense_groupings: Map of expense_id -> list of {'family_id', 'weight', 'is_active'}

    Returns:
        SettlementResult with balances, optimized transfers, total spent,
        paid_by_family, owed_by_family, and itemized item_shares.
    """
    family_ids = [f["id"] for f in families]
    family_names = {f["id"]: f["name"] for f in families}
    weights = {f["id"]: f["weight"] for f in families}
    paid = {fid: 0.0 for fid in family_ids}
    owed = {fid: 0.0 for fid in family_ids}
    total_spent = 0.0
    item_shares = []

    # Process meals
    for meal in meals:
        meal_id = meal["id"]
        contributions = meal_contributions.get(meal_id, [])
        absences = meal_absences.get(meal_id, [])
        meal_total = sum(c["amount"] for c in contributions)
        total_spent += meal_total

        payers = []
        for c in contributions:
            fid = c["family_id"]
            if fid in paid:
                paid[fid] += c["amount"]
            if fid not in payers:
                payers.append(fid)

        shares = {fid: 0.0 for fid in family_ids}
        percentages = {fid: 0.0 for fid in family_ids}

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
                    fid = m["family_id"]
                    share_amt = meal_total * (m["weight"] / total_weight)
                    shares[fid] = share_amt
                    percentages[fid] = (share_amt / meal_total * 100.0) if meal_total > 0 else (m["weight"] / total_weight * 100.0)
                    owed[fid] += share_amt
        else:
            # Fallback to default family weights minus absences
            attending = [fid for fid in family_ids if fid not in absences]
            if attending:
                total_weight = sum(weights[fid] for fid in attending)
                if total_weight > 0:
                    for fid in attending:
                        share_amt = meal_total * (weights[fid] / total_weight)
                        shares[fid] = share_amt
                        percentages[fid] = (share_amt / meal_total * 100.0) if meal_total > 0 else (weights[fid] / total_weight * 100.0)
                        owed[fid] += share_amt

        meal_num = meal.get("meal_number", meal_id)
        meal_name = meal.get("name", "Meal")
        absent_names = [family_names[fid] for fid in absences if fid in family_names]
        notes_str = f"Skipped: {', '.join(absent_names)}" if absent_names else "-"

        item_shares.append(
            ItemShare(
                item_id=meal_id,
                item_name=f"#{meal_num} {meal_name}",
                item_type="meal",
                total_amount=meal_total,
                family_shares=shares,
                family_percentages=percentages,
                payer_family_ids=payers,
                notes=notes_str,
            )
        )

    # Process shared expenses
    all_weight = sum(weights[fid] for fid in family_ids)
    for expense in shared_expenses:
        amount = expense["amount"]
        total_spent += amount
        payer_fid = expense.get("family_id")
        if payer_fid in paid:
            paid[payer_fid] += amount

        shares = {fid: 0.0 for fid in family_ids}
        percentages = {fid: 0.0 for fid in family_ids}

        expense_id = expense.get("id")
        group_members = (expense_groupings or {}).get(expense_id) if expense_id else None

        if group_members:
            attending = [m for m in group_members if m.get("is_active", 1) != 0 and m["family_id"] in owed]
            total_weight = sum(m["weight"] for m in attending)
            if total_weight > 0:
                for m in attending:
                    fid = m["family_id"]
                    share_amt = amount * (m["weight"] / total_weight)
                    shares[fid] = share_amt
                    percentages[fid] = (share_amt / amount * 100.0) if amount > 0 else (m["weight"] / total_weight * 100.0)
                    owed[fid] += share_amt
        else:
            if all_weight > 0:
                for fid in family_ids:
                    share_amt = amount * (weights[fid] / all_weight)
                    shares[fid] = share_amt
                    percentages[fid] = (share_amt / amount * 100.0) if amount > 0 else (weights[fid] / all_weight * 100.0)
                    owed[fid] += share_amt

        item_shares.append(
            ItemShare(
                item_id=expense_id or 0,
                item_name=expense.get("description", "Expense"),
                item_type="expense",
                total_amount=amount,
                family_shares=shares,
                family_percentages=percentages,
                payer_family_ids=[payer_fid] if payer_fid else [],
                notes="-",
            )
        )

    # Net balances (positive = owed money, negative = owes money)
    balances = {fid: paid[fid] - owed[fid] for fid in family_ids}
    transfers = _optimize_transfers(balances)
    return SettlementResult(
        balances=balances,
        transfers=transfers,
        total_spent=total_spent,
        paid_by_family=paid,
        owed_by_family=owed,
        item_shares=item_shares,
    )


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


async def calculate_trip_settlement_from_db(
    db_path: str, trip_id: int
) -> tuple[list[dict], list[dict], list[dict], SettlementResult]:
    """
    Load all families, meals, expenses, contributions, absences, and groupings
    from the database for a trip and run calculate_settlement.

    Returns:
        (families, meals, expenses, SettlementResult)
    """
    from bot.db import (
        get_families, get_meals, get_shared_expenses,
        get_meal_contributions, get_meal_absences, get_meal_grouping_members, get_grouping_members,
    )

    families = await get_families(db_path, trip_id)
    meals = await get_meals(db_path, trip_id)
    expenses = await get_shared_expenses(db_path, trip_id)

    meal_contributions = {}
    meal_absences = {}
    meal_groupings = {}
    for meal in meals:
        contributions = await get_meal_contributions(db_path, meal["id"])
        meal_contributions[meal["id"]] = [{"family_id": c["family_id"], "amount": c["amount"]} for c in contributions]
        meal_absences[meal["id"]] = await get_meal_absences(db_path, meal["id"])
        group_members = await get_meal_grouping_members(db_path, meal["id"])
        meal_groupings[meal["id"]] = [
            {"family_id": gm["family_id"], "weight": gm["weight"], "is_active": gm["is_active"]}
            for gm in group_members
        ]

    expense_groupings = {}
    for e in expenses:
        if e.get("grouping_id"):
            gm_members = await get_grouping_members(db_path, e["grouping_id"])
            expense_groupings[e["id"]] = [
                {"family_id": gm["family_id"], "weight": gm["weight"], "is_active": gm["is_active"]}
                for gm in gm_members
            ]

    expense_data = [
        {"family_id": e["family_id"], "description": e["description"], "amount": e["amount"], "id": e["id"]}
        for e in expenses
    ]

    result = calculate_settlement(
        families=families,
        meals=meals,
        meal_contributions=meal_contributions,
        meal_absences=meal_absences,
        shared_expenses=expense_data,
        meal_groupings=meal_groupings,
        expense_groupings=expense_groupings,
    )

    return families, meals, expenses, result
