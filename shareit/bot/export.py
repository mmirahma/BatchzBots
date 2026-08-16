"""Excel export generator for BachzTab trip expense breakdown."""

import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def create_excel_report(
    trip_name: str,
    families: list[dict],
    meals: list[dict],
    expenses: list[dict],
    meal_contributions: dict[int, list[dict]],
    meal_absences: dict[int, list[int]],
    meal_groupings: dict[int, list[dict]] | None = None,
    group_title: str | None = None,
) -> io.BytesIO:
    """
    Generate an itemized Excel workbook (.xlsx) containing all meals and expenses,
    cost shares per family, notes on absences, and summary rows (Paid, Owed, Net Balance).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Expense Report"
    ws.views.sheetView[0].showGridLines = True

    # 1. Title Banner
    report_title = group_title or trip_name
    ws.merge_cells("A1:D1")
    ws["A1"] = f"BachzTab — {report_title} Expense Report"
    ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1F4E78")
    ws["A1"].alignment = Alignment(vertical="center")

    ws["A2"] = f"Generated for {len(families)} families. Currency: USD ($)"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="595959")

    # 2. Table Headers (Row 4)
    family_ids = [f["id"] for f in families]
    family_names = {f["id"]: f["name"] for f in families}
    family_weights = {f["id"]: f["weight"] for f in families}

    headers = ["Item / Expense", "Type", "Payer", "Total ($)"]
    for f in families:
        headers.append(f"{f['name']} (w={f['weight']})")
    headers.append("Notes / Absences")

    ws.append([])  # Row 3 empty
    ws.append(headers)  # Row 4 headers

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9"),
    )

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border

    # 3. Data Rows
    current_row = 5
    paid_totals = {fid: 0.0 for fid in family_ids}

    # Process meals
    for m in meals:
        m_id = m["id"]
        conts = meal_contributions.get(m_id, [])
        absent_fids = meal_absences.get(m_id, [])
        m_total = sum(c["amount"] for c in conts)

        for c in conts:
            if c["family_id"] in paid_totals:
                paid_totals[c["family_id"]] += c["amount"]

        if conts:
            payer_str = ", ".join([f"{family_names.get(c['family_id'], 'Family')} (${c['amount']:.2f})" for c in conts])
        else:
            payer_str = "None"

        group_m = (meal_groupings or {}).get(m_id, [])
        if group_m:
            attending = [gm for gm in group_m if gm.get("is_active", 1) != 0 and gm["family_id"] not in absent_fids and gm["family_id"] in family_ids]
            total_w = sum(gm["weight"] for gm in attending)
        else:
            attending_fids = [fid for fid in family_ids if fid not in absent_fids]
            total_w = sum(family_weights[fid] for fid in attending_fids)
            attending = [{"family_id": fid, "weight": family_weights[fid]} for fid in attending_fids]

        shares = {fid: 0.0 for fid in family_ids}
        if total_w > 0:
            for item in attending:
                fid = item["family_id"]
                w = item["weight"]
                shares[fid] = m_total * (w / total_w)

        skipped_names = [family_names[fid] for fid in absent_fids if fid in family_names]
        notes_str = f"Skipped: {', '.join(skipped_names)}" if skipped_names else "-"

        row_data = [
            f"#{m['meal_number']} {m['name']}",
            "Meal/Event",
            payer_str,
            m_total,
        ]
        for fid in family_ids:
            row_data.append(shares[fid])
        row_data.append(notes_str)

        ws.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.border = thin_border
            if col_idx >= 4 and col_idx < 4 + len(family_ids) + 1:
                c.number_format = "$#,##0.00"
                c.alignment = Alignment(horizontal="right")
        current_row += 1

    # Process general shared expenses
    total_family_w = sum(family_weights.values())
    for e in expenses:
        amt = e["amount"]
        payer_fid = e["family_id"]
        if payer_fid in paid_totals:
            paid_totals[payer_fid] += amt

        payer_name = e.get("family_name") or family_names.get(payer_fid, "Family")

        shares = {fid: 0.0 for fid in family_ids}
        if total_family_w > 0:
            for fid in family_ids:
                shares[fid] = amt * (family_weights[fid] / total_family_w)

        row_data = [
            e["description"],
            "General Expense",
            payer_name,
            amt,
        ]
        for fid in family_ids:
            row_data.append(shares[fid])
        row_data.append("-")

        ws.append(row_data)

        for col_idx in range(1, len(row_data) + 1):
            c = ws.cell(row=current_row, column=col_idx)
            c.border = thin_border
            if col_idx >= 4 and col_idx < 4 + len(family_ids) + 1:
                c.number_format = "$#,##0.00"
                c.alignment = Alignment(horizontal="right")
        current_row += 1

    # 4. Summary Rows
    data_start_row = 5
    data_end_row = current_row - 1 if current_row > 5 else 5

    # Summary Row 1: Total Owed (Cost Share)
    row_owed = ["Total Owed (Cost Share)", "-", "-", f"=SUM(D{data_start_row}:D{data_end_row})"]
    for idx, fid in enumerate(family_ids):
        col_letter = get_column_letter(5 + idx)
        row_owed.append(f"=SUM({col_letter}{data_start_row}:{col_letter}{data_end_row})")
    row_owed.append("-")

    ws.append(row_owed)
    owed_row_idx = current_row
    owed_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
    thick_bottom = Border(
        top=Side(style="thin", color="1F4E78"),
        bottom=Side(style="double", color="1F4E78"),
    )

    for col_idx in range(1, len(row_owed) + 1):
        c = ws.cell(row=owed_row_idx, column=col_idx)
        c.font = Font(name="Calibri", size=11, bold=True)
        c.fill = owed_fill
        c.border = thick_bottom
        if col_idx >= 4 and col_idx < 4 + len(family_ids) + 1:
            c.number_format = "$#,##0.00"
            c.alignment = Alignment(horizontal="right")
    current_row += 1

    # Summary Row 2: Total Paid
    row_paid = ["Total Paid by Family", "-", "-", f"=SUM(D{data_start_row}:D{data_end_row})"]
    for fid in family_ids:
        row_paid.append(paid_totals[fid])
    row_paid.append("-")

    ws.append(row_paid)
    paid_row_idx = current_row
    paid_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

    for col_idx in range(1, len(row_paid) + 1):
        c = ws.cell(row=paid_row_idx, column=col_idx)
        c.font = Font(name="Calibri", size=11, bold=True)
        c.fill = paid_fill
        c.border = thin_border
        if col_idx >= 4 and col_idx < 4 + len(family_ids) + 1:
            c.number_format = "$#,##0.00"
            c.alignment = Alignment(horizontal="right")
    current_row += 1

    # Summary Row 3: Net Balance (Bank Status = Paid - Owed)
    row_bal = ["Net Balance (Bank Status)", "-", "-", "$0.00"]
    for idx, fid in enumerate(family_ids):
        col_letter = get_column_letter(5 + idx)
        row_bal.append(f"={col_letter}{paid_row_idx}-{col_letter}{owed_row_idx}")
    row_bal.append("Match Bank Calculation")

    ws.append(row_bal)
    bal_row_idx = current_row
    bal_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    double_bottom = Border(
        top=Side(style="thin", color="1F4E78"),
        bottom=Side(style="double", color="1F4E78"),
    )

    for col_idx in range(1, len(row_bal) + 1):
        c = ws.cell(row=bal_row_idx, column=col_idx)
        c.font = Font(name="Calibri", size=11, bold=True, color="1F4E78")
        c.fill = bal_fill
        c.border = double_bottom
        if col_idx >= 4 and col_idx < 4 + len(family_ids) + 1:
            c.number_format = "$#,##0.00;($#,##0.00);$0.00"
            c.alignment = Alignment(horizontal="right")
    current_row += 1

    # 5. Adjust Column Widths
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if cell.number_format and "$" in cell.number_format:
                val_str += "    "
            max_len = max(max_len, len(val_str))
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output
