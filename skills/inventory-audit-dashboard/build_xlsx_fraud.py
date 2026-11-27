#!/usr/bin/env python3
"""Add the Fraud Detection sheet to Alfaihaa_Inventory_Audit_Full_Data.xlsx.
User request (2026-09-21): fraud/control checks across 4 categories -- timing & posting-control,
user & segregation-of-duties, pricing & cost, movement-pattern -- mirroring the dashboard's new
"Fraud Detection" tab (see dashboard.html / build_alfaihaa_fraud_detection.py)."""
import json
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))
wb = load_workbook(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
if "Fraud Detection" in wb.sheetnames:
    del wb["Fraud Detection"]  # idempotent rerun

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT, size=13, bold=True, color="0F6E5C")
SUBTITLE_FONT = Font(name=FONT, size=11, bold=True, color="0F6E5C")
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="425953")
DATA_FONT = Font(name=FONT, size=10)
BOLD_FONT = Font(name=FONT, size=10, bold=True)
THIN = Side(style="thin", color="D8E0DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AMBER_FILL = PatternFill("solid", fgColor="FBF0DD")
RED_FILL = PatternFill("solid", fgColor="FBE7E3")

MONEY0 = '#,##0;(#,##0);"-"'
QTY0 = '#,##0;(#,##0);"-"'
PCT1 = '0.0"%"'


def write_table(ws, headers, rows, keys, formats, widths, start_row, freeze=True, autofilter=True):
    for j, h in enumerate(headers, start=1):
        c = ws.cell(row=start_row, column=j, value=h)
        c.font = HEAD_FONT
        c.fill = HEAD_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for i, r in enumerate(rows, start=start_row + 1):
        for j, (k, fmt) in enumerate(zip(keys, formats), start=1):
            v = r.get(k) if isinstance(r, dict) else None
            cell = ws.cell(row=i, column=j, value=v)
            cell.font = DATA_FONT
            cell.border = BORDER
            if fmt:
                cell.number_format = fmt
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    last_row = start_row + len(rows)
    if freeze:
        ws.freeze_panes = ws.cell(row=start_row + 1, column=1)
    if autofilter and rows:
        ws.auto_filter.ref = f"A{start_row}:{get_column_letter(len(headers))}{last_row}"
    return last_row


FD = AUDIT["fraud_detection"]
K = FD["kpi"]

ws = wb.create_sheet("Fraud Detection")
ws.sheet_view.showGridLines = False
ws["A1"] = "Fraud & Control Detection"
ws["A1"].font = TITLE_FONT
ws["A2"] = FD["generated_note"]
ws["A2"].font = NOTE_FONT
ws["A2"].alignment = Alignment(wrap_text=True)
ws.row_dimensions[2].height = 55

# ---------------------------------------------------------------------------
# KPI summary block
# ---------------------------------------------------------------------------
r = 4
ws.cell(row=r, column=1, value="Summary").font = SUBTITLE_FONT
r += 1
kpi_defs = [
    ("Late-posted transactions", K["late_posting_count"], "#,##0", "Value at risk (SAR)", K["late_posting_value"], MONEY0),
    ("After-hours transactions (00:00-02:59)", K["off_hours_count"], "#,##0", "", None, None),
    ("Same-user create+post transactions", K["same_user_create_post_count"], "#,##0", "% of all postings", K["same_user_create_post_pct"], PCT1),
    ("Pricing anomalies (PI lines)", K["price_anomaly_count"], "#,##0", "Value at risk (SAR)", K["price_anomaly_value"], MONEY0),
    ("Frequent-correction SKU/store keys", K["frequent_correction_keys"], "#,##0", "", None, None),
    ("Quantity-matched round-trip transfers", K["round_trip_count"], "#,##0", "", None, None),
    ("Cancelled transactions", K["cancelled_count"], "#,##0", "", None, None),
    ("Purchase returns", K["purchase_return_count"], "#,##0", "Value (SAR)", K["purchase_return_value"], MONEY0),
]
kpi_head_row = r
for j, h in enumerate(["Metric", "Count", "", "Secondary metric", "Value", ""], start=1):
    c = ws.cell(row=kpi_head_row, column=j, value=h)
    c.font = HEAD_FONT
    c.fill = HEAD_FILL
r += 1
for label, count, cfmt, label2, val2, vfmt in kpi_defs:
    ws.cell(row=r, column=1, value=label).font = DATA_FONT
    c = ws.cell(row=r, column=2, value=count); c.font = BOLD_FONT; c.number_format = cfmt
    if label2:
        ws.cell(row=r, column=4, value=label2).font = DATA_FONT
        c = ws.cell(row=r, column=5, value=val2); c.font = BOLD_FONT
        if vfmt:
            c.number_format = vfmt
    for col in range(1, 6):
        ws.cell(row=r, column=col).border = BORDER
    r += 1
kpi_end_row = r - 1
for col, w in zip("ABCDEF", [34, 12, 3, 26, 14, 3]):
    ws.column_dimensions[col].width = w

# ---------------------------------------------------------------------------
# Timing & posting-control anomalies (late posting + off-hours, combined)
# ---------------------------------------------------------------------------
r += 2
ws.cell(row=r, column=1, value="Timing & posting-control anomalies").font = SUBTITLE_FONT
r += 1
ws.cell(row=r, column=1, value=(
    f"Showing {len(FD['timing']['late_posting_rows'])} of {FD['timing']['late_posting_total_count']} transactions posted more than "
    f"{FD['timing']['late_posting_threshold_days']} days after the fact, plus all {len(FD['timing']['off_hours_rows'])} transactions logged "
    f"{FD['timing']['off_hours_window']}."
)).font = NOTE_FONT
r += 1
timing_rows = (
    [{**x, "flag_type": "Late posting", "detail": f"{x['gap_days']}d to post"} for x in FD["timing"]["late_posting_rows"]]
    + [{**x, "flag_type": "After-hours", "detail": f"{x['hour']:02d}:xx"} for x in FD["timing"]["off_hours_rows"]]
)
timing_rows.sort(key=lambda x: -(x.get("value") or 0))
lr = write_table(
    ws,
    ["Flag", "Branch", "Store", "Code", "Product", "Type", "Transaction", "Transaction date", "Detail", "Value (SAR)", "Created by", "Posted by"],
    timing_rows,
    ["flag_type", "branch", "store_name", "product", "product_name", "transaction_type", "transaction_no", "transaction_date", "detail", "value", "created_by", "posted_by"],
    [None, None, None, None, None, None, None, None, None, MONEY0, None, None],
    [14, 12, 16, 10, 32, 16, 20, 20, 14, 13, 20, 20],
    start_row=r,
)
timing_start = r

# ---------------------------------------------------------------------------
# User & segregation-of-duties
# ---------------------------------------------------------------------------
r = lr + 3
ws.cell(row=r, column=1, value="User & segregation-of-duties").font = SUBTITLE_FONT
r += 1
ws.cell(row=r, column=1, value=(
    "Per-user creation vs. posting activity for 2026. A user at 100% has no independent second check on their own entries."
)).font = NOTE_FONT
r += 1
sod_user_start = r
lr = write_table(
    ws,
    ["User", "Created", "Posted", "Same-user (created+posted)", "% of own postings", "Value created (SAR)"],
    FD["sod"]["user_summary"],
    ["user", "created_count", "posted_count", "same_user_count", "same_user_pct", "created_value"],
    [None, "#,##0", "#,##0", "#,##0", PCT1, MONEY0],
    [24, 12, 12, 16, 14, 18],
    start_row=r,
)
sod_pct_col = 5
for rr in range(sod_user_start + 1, lr + 1):
    ws.conditional_formatting.add(
        f"{get_column_letter(sod_pct_col)}{rr}",
        CellIsRule(operator="greaterThanOrEqual", formula=["90"], fill=RED_FILL),
    )

r = lr + 2
ws.cell(row=r, column=1, value="Sample same-user create+post transactions").font = Font(name=FONT, size=10.5, bold=True, color="0F6E5C")
r += 1
lr = write_table(
    ws,
    ["Transaction", "Date", "Branch", "Store", "Code", "Product", "Type", "User (created & posted)", "Value (SAR)"],
    FD["sod"]["same_user_rows"],
    ["transaction_no", "transaction_date", "branch", "store_name", "product", "product_name", "transaction_type", "created_by", "value"],
    [None, None, None, None, None, None, None, None, MONEY0],
    [20, 20, 12, 16, 10, 32, 16, 20, 13],
    start_row=r,
)

# ---------------------------------------------------------------------------
# Pricing & cost anomalies
# ---------------------------------------------------------------------------
r = lr + 3
ws.cell(row=r, column=1, value="Pricing & cost anomalies").font = SUBTITLE_FONT
r += 1
ws.cell(row=r, column=1, value=FD["pricing"]["method"] + f" Showing {len(FD['pricing']['anomaly_rows'])} of {FD['pricing']['anomaly_total_count']} flagged lines.").font = NOTE_FONT
ws.row_dimensions[r].height = 28
r += 1
pricing_start = r
lr = write_table(
    ws,
    ["Branch", "Store", "Code", "Product", "Supplier", "Date", "Unit cost", "Product+supplier median", "Deviation %", "Value at risk (SAR)", "Transaction"],
    FD["pricing"]["anomaly_rows"],
    ["branch", "store_name", "product", "product_name", "supplier_name", "transaction_date", "unit_cost", "group_median_cost", "deviation_pct", "deviation_value", "transaction_no"],
    [None, None, None, None, None, None, '#,##0.00', '#,##0.00', '+0.0"%";-0.0"%"', MONEY0, None],
    [12, 16, 10, 32, 24, 20, 12, 18, 12, 16, 20],
    start_row=r,
)
dev_col = 9
for rr in range(pricing_start + 1, lr + 1):
    ws.conditional_formatting.add(
        f"{get_column_letter(dev_col)}{rr}",
        FormulaRule(formula=[f"ABS({get_column_letter(dev_col)}{rr})>=100"], fill=RED_FILL),
    )
    ws.conditional_formatting.add(
        f"{get_column_letter(dev_col)}{rr}",
        FormulaRule(formula=[f"AND(ABS({get_column_letter(dev_col)}{rr})<100,ABS({get_column_letter(dev_col)}{rr})>=25)"], fill=AMBER_FILL),
    )

# ---------------------------------------------------------------------------
# Movement-pattern anomalies: frequent corrections, round-trips, cancelled
# ---------------------------------------------------------------------------
r = lr + 3
ws.cell(row=r, column=1, value="Movement-pattern anomalies").font = SUBTITLE_FONT
r += 1
ws.cell(row=r, column=1, value=(
    "Frequent corrections on the same SKU/store, quantity-matched round-trip transfers between the same two stores "
    f"(within {FD['movement']['round_trip_window_days']} days), and cancelled-transaction clustering."
)).font = NOTE_FONT
r += 1

ws.cell(row=r, column=1, value="Frequent corrections (2+ on the same SKU/store in 2026)").font = Font(name=FONT, size=10.5, bold=True, color="0F6E5C")
r += 1
lr = write_table(
    ws,
    ["Branch", "Store", "Code", "Product", "Corrections in 2026", "Value (SAR)"],
    FD["movement"]["frequent_corrections"],
    ["branch", "store_name", "product", "product_name", "correction_count", "total_value"],
    [None, None, None, None, "#,##0", MONEY0],
    [12, 16, 10, 32, 16, 14],
    start_row=r,
)

r = lr + 2
ws.cell(row=r, column=1, value="Round-trip transfers (quantity-matched)").font = Font(name=FONT, size=10.5, bold=True, color="0F6E5C")
r += 1
lr = write_table(
    ws,
    ["Code", "Product", "Out -> branch", "Out store", "Out date", "Out qty", "Back -> branch", "Back store", "Back date", "Back qty", "Days between"],
    FD["movement"]["round_trip_transfers"],
    ["product", "product_name", "out_branch", "out_store_name", "out_date", "out_qty", "back_branch", "back_store_name", "back_date", "back_qty", "days_between"],
    [None, None, None, None, None, QTY0, None, None, None, QTY0, "#,##0"],
    [10, 32, 14, 16, 20, 10, 14, 16, 20, 10, 12],
    start_row=r,
)

r = lr + 2
ws.cell(row=r, column=1, value="Cancelled transactions").font = Font(name=FONT, size=10.5, bold=True, color="0F6E5C")
r += 1
lr = write_table(
    ws,
    ["Branch", "Store", "Code", "Product", "Type", "Transaction", "Date", "Created by"],
    FD["movement"]["cancelled_rows"],
    ["branch", "store_name", "product", "product_name", "transaction_type", "transaction_no", "transaction_date", "created_by"],
    [None, None, None, None, None, None, None, None],
    [12, 16, 10, 32, 16, 20, 20, 20],
    start_row=r,
)

print(f"Fraud Detection sheet written -- timing={len(timing_rows)} sod_sample={len(FD['sod']['same_user_rows'])} "
      f"pricing={len(FD['pricing']['anomaly_rows'])} corrections={len(FD['movement']['frequent_corrections'])} "
      f"roundtrip={len(FD['movement']['round_trip_transfers'])} cancelled={len(FD['movement']['cancelled_rows'])}")

# ---------------------------------------------------------------------------
# Wire headline KPIs into the Summary sheet
# ---------------------------------------------------------------------------
sm = wb["Summary"]
vbs_row = None
for i in range(1, 60):
    if sm.cell(row=i, column=2).value == "Value by branch / store":
        vbs_row = i
        break
new_metrics = [
    ("Fraud detection — late-posted transactions (>30d)", K["late_posting_count"], "#,##0"),
    ("Fraud detection — pricing anomalies (SAR at risk)", K["price_anomaly_value"], MONEY0),
    ("Fraud detection — same-user create+post rate", K["same_user_create_post_pct"] / 100, "0.0%"),
    ("Fraud detection — total flagged items (ex. late-posting)", K["total_flags"], "#,##0"),
]
existing_row = None
for i in range(1, vbs_row):
    if sm.cell(row=i, column=2).value == new_metrics[0][0]:
        existing_row = i
        break
insert_row = existing_row if existing_row else vbs_row - 1
if existing_row is None:
    sm.insert_rows(insert_row, amount=len(new_metrics))
for k, (label, value, fmt) in enumerate(new_metrics):
    r_ = insert_row + k
    sm.cell(row=r_, column=2, value=label).font = Font(name=FONT, size=10)
    c = sm.cell(row=r_, column=3, value=value)
    c.font = Font(name=FONT, size=11, bold=True)
    c.number_format = fmt
print(f"Summary sheet: {len(new_metrics)} Fraud Detection KPI rows {'updated in place at' if existing_row else 'inserted before'} row {insert_row}")

wb.save(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
print("saved.")
for s in wb.sheetnames:
    print(" -", s, wb[s].dimensions)
