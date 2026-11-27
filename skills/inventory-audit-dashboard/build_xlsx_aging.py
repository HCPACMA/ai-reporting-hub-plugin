#!/usr/bin/env python3
"""Add the Aging Bucket / Never-Dispensed sheet to Alfaihaa_Inventory_Audit_Full_Data.xlsx.
User request (2026-09-21): a filterable Aging Bucket tab with Never-Dispensed by branch and
through all branches -- code, name, store, branch, qty, entry date/type (purchase or transfer),
days aged, and an aging-bucket breakdown (0-30/31-60/61-90/91-120/121-180/180+)."""
import json
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))
wb = load_workbook(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
if "Aging Bucket" in wb.sheetnames:
    del wb["Aging Bucket"]  # idempotent rerun

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT, size=13, bold=True, color="0F6E5C")
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="425953")
DATA_FONT = Font(name=FONT, size=10)
BOLD_FONT = Font(name=FONT, size=10, bold=True)
THIN = Side(style="thin", color="D8E0DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AMBER_FILL = PatternFill("solid", fgColor="FBF0DD")
RED_FILL = PatternFill("solid", fgColor="FBE7E3")
BLUE_FILL = PatternFill("solid", fgColor="E4EEFB")

MONEY0 = '#,##0;(#,##0);"-"'
QTY0 = '#,##0;(#,##0);"-"'
DATE = 'yyyy-mm-dd'

BUCKET_ORDER = ["0-30", "31-60", "61-90", "91-120", "121-180", "181-365", "365+", "Unknown"]
BUCKET_FILL = {"0-30": None, "31-60": None, "61-90": AMBER_FILL, "91-120": AMBER_FILL,
               "121-180": RED_FILL, "181-365": RED_FILL, "365+": RED_FILL, "Unknown": AMBER_FILL}


def new_sheet(name, title, note, index=None):
    ws = wb.create_sheet(name, index) if index is not None else wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = note
    ws["A2"].font = NOTE_FONT
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[2].height = 40
    return ws


def write_table(ws, headers, rows, keys, formats, widths, start_row=5, freeze=True, autofilter=True):
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


ND = AUDIT["never_dispensed"]

insert_at = wb.sheetnames.index("Receiving Flags") + 1
ws = new_sheet(
    "Aging Bucket", "Aging Bucket — Never-Dispensed Stock",
    "On-hand stock that has never once been dispensed (DS) from its current store. Two independent date bases are shown side by "
    "side: \"current store\" columns measure from that key's most recent purchase or transfer-in receipt INTO ITS CURRENT STORE; "
    "\"original batch\" columns measure from that product's earliest-ever transaction anywhere in the branch (live-queried against "
    "the ERP) -- the batch's true age, which can predate the current-store entry by years when stock was transferred between "
    "stores (see \"Original batch — first seen at\" when that differs from the current store). Filter/sort on whichever basis "
    "matters via AutoFilter. Entry type \"Opening balance (pre-extract)\" = no purchase/transfer-in row exists anywhere in this "
    "extract for that key, so the item was already on hand before the extract's own transaction window began -- its shown age is a "
    "calculable LOWER BOUND (from the window's start date), not the true entry date, which may be older still. \"Never dispensed — "
    "ALL branches\" = this exact product code has zero dispense activity at ANY store across all 4 branches -- the case flagged by "
    "management: stock that only ever circulates between warehouses on a transfer, never reaching a clinic/patient anywhere.",
    index=insert_at,
)


def write_bucket_summary(ws, srow, title, by_branch_rows, all_branches_rows):
    ws.cell(row=srow, column=1, value=title).font = TITLE_FONT
    ws.row_dimensions[srow].height = 18
    srow += 1
    sum_headers = ["Aging bucket",
                   "Rows (this branch)", "Qty (this branch)", "Value SAR (this branch)",
                   "Rows (all-branches scope)", "Qty (all-branches scope)", "Value SAR (all-branches scope)"]
    for j, h in enumerate(sum_headers, start=1):
        c = ws.cell(row=srow, column=j, value=h)
        c.font = HEAD_FONT
        c.fill = HEAD_FILL
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.row_dimensions[srow].height = 30
    sum_start = srow + 1
    by_branch_map = {r["bucket"]: r for r in by_branch_rows}
    all_branch_map = {r["bucket"]: r for r in all_branches_rows}
    r = sum_start
    for bk in BUCKET_ORDER:
        b1 = by_branch_map.get(bk, {"count": 0, "qty": 0, "value": 0})
        b2 = all_branch_map.get(bk, {"count": 0, "qty": 0, "value": 0})
        ws.cell(row=r, column=1, value=bk).font = BOLD_FONT
        ws.cell(row=r, column=2, value=b1["count"]).font = DATA_FONT
        c = ws.cell(row=r, column=3, value=b1["qty"]); c.font = DATA_FONT; c.number_format = QTY0
        c = ws.cell(row=r, column=4, value=b1["value"]); c.font = DATA_FONT; c.number_format = MONEY0
        ws.cell(row=r, column=5, value=b2["count"]).font = DATA_FONT
        c = ws.cell(row=r, column=6, value=b2["qty"]); c.font = DATA_FONT; c.number_format = QTY0
        c = ws.cell(row=r, column=7, value=b2["value"]); c.font = DATA_FONT; c.number_format = MONEY0
        fill = BUCKET_FILL.get(bk)
        for col in range(1, 8):
            ws.cell(row=r, column=col).border = BORDER
            if fill:
                ws.cell(row=r, column=col).fill = fill
        r += 1
    total_row = r
    ws.cell(row=total_row, column=1, value="Total").font = BOLD_FONT
    for col, key in [(2, "count"), (3, "qty"), (4, "value"), (5, "count"), (6, "qty"), (7, "value")]:
        c = ws.cell(row=total_row, column=col, value=f"=SUM({get_column_letter(col)}{sum_start}:{get_column_letter(col)}{total_row - 1})")
        c.font = BOLD_FONT
        if key != "count":
            c.number_format = QTY0 if key == "qty" else MONEY0
    for col in range(1, 8):
        ws.cell(row=total_row, column=col).border = BORDER
    return total_row


# --- bucket-summary blocks: current-store basis, then original-batch basis, stacked ---
total_row = write_bucket_summary(ws, 4, "Aging bucket breakdown — by current store entry",
                                  ND["bucket_summary_by_branch_scope"], ND["bucket_summary_all_branches_scope"])
total_row2 = write_bucket_summary(ws, total_row + 2, "Aging bucket breakdown — by original batch date",
                                   ND["bucket_summary_original_batch_by_branch_scope"], ND["bucket_summary_original_batch_all_branches_scope"])

for col, w in zip("ABCDEFG", [14, 15, 15, 17, 18, 18, 19]):
    ws.column_dimensions[col].width = w

# --- detail table ---
detail_title_row = total_row2 + 2
ws.cell(row=detail_title_row, column=1, value="Detail — all never-dispensed rows").font = TITLE_FONT
detail_start = detail_title_row + 1

rows = []
for r_ in ND["rows"]:
    rows.append({
        **r_,
        "scope_label": "ALL branches" if r_["never_dispensed_anywhere"] else "This branch only",
        "original_batch_store_label": r_.get("original_batch_store_name") or "(same store)",
    })
rows.sort(key=lambda r: -(r["days_in_stock"] if r["days_in_stock"] is not None else 10**9))

lr = write_table(
    ws,
    ["Branch", "Store", "Code", "Product", "On hand", "Value (SAR)",
     "Entered current store", "Entry type", "Days aged (current store)", "Aging bucket (current store)",
     "Original batch date", "Original batch type", "Original batch — first seen at",
     "Days aged (original batch)", "Aging bucket (original batch)", "Never-dispensed scope"],
    rows,
    ["branch", "store_name", "product", "product_name", "on_hand", "on_hand_cost",
     "entry_date_display", "entry_type", "days_in_stock", "aging_bucket",
     "original_batch_date", "original_batch_type", "original_batch_store_label",
     "original_batch_days_in_stock", "original_batch_aging_bucket", "scope_label"],
    [None, None, None, None, QTY0, MONEY0, None, None, QTY0, None, None, None, None, QTY0, None, None],
    [12, 18, 10, 34, 10, 13, 18, 24, 12, 14, 15, 16, 18, 12, 14, 18],
    start_row=detail_start,
)

# conditional formatting: aging-bucket severity (both bases) + all-branches scope highlight
bucket_col = 10       # "Aging bucket (current store)"
bucket_col_ob = 15    # "Aging bucket (original batch)"
scope_col = 16        # "Never-dispensed scope"
for col_idx in (bucket_col, bucket_col_ob):
    for sev_bucket, fill in [("365+", RED_FILL), ("181-365", RED_FILL), ("121-180", AMBER_FILL), ("Unknown", AMBER_FILL)]:
        ws.conditional_formatting.add(
            f"A{detail_start + 1}:P{lr}",
            FormulaRule(formula=[f'${get_column_letter(col_idx)}{detail_start + 1}="{sev_bucket}"'], fill=fill),
        )
ws.conditional_formatting.add(
    f"{get_column_letter(scope_col)}{detail_start + 1}:{get_column_letter(scope_col)}{lr}",
    CellIsRule(operator="equal", formula=['"ALL branches"'], fill=RED_FILL),
)

print(f"Aging Bucket sheet written — {len(rows)} detail rows, bucket summary rows at {total_row} and {total_row2}")

# ---------------------------------------------------------------------------
# Wire the new KPIs into the Summary sheet, right before "Value by branch / store"
# ---------------------------------------------------------------------------
sm = wb["Summary"]
# find the blank row right before "Value by branch / store" (idempotent: locate it fresh each run)
vbs_row = None
for i in range(1, 60):
    if sm.cell(row=i, column=2).value == "Value by branch / store":
        vbs_row = i
        break
new_metrics = [
    ("Never-dispensed value — this branch (SAR)", f"='Aging Bucket'!D{total_row}", MONEY0),
    ("Never-dispensed rows — this branch", f"='Aging Bucket'!B{total_row}", "#,##0"),
    ("Never-dispensed value — all branches (SAR)", f"='Aging Bucket'!G{total_row}", MONEY0),
    ("Never-dispensed distinct SKUs — all branches", AUDIT["kpi"]["never_dispensed_all_branches_sku_count"], "#,##0"),
]
# idempotent rerun: if these KPI rows are already there (from a prior run), overwrite them in
# place rather than inserting a duplicate set
existing_row = None
for i in range(1, vbs_row):
    if sm.cell(row=i, column=2).value == new_metrics[0][0]:
        existing_row = i
        break
insert_row = existing_row if existing_row else vbs_row - 1  # blank spacer row just above the table
if existing_row is None:
    sm.insert_rows(insert_row, amount=len(new_metrics))
for k, (label, value, fmt) in enumerate(new_metrics):
    r_ = insert_row + k
    sm.cell(row=r_, column=2, value=label).font = Font(name=FONT, size=10)
    c = sm.cell(row=r_, column=3, value=value)
    c.font = Font(name=FONT, size=11, bold=True)
    c.number_format = fmt
print(f"Summary sheet: {len(new_metrics)} Aging Bucket KPI rows {'updated in place at' if existing_row else 'inserted before'} row {insert_row}")

wb.save(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
print("saved.")
for s in wb.sheetnames:
    print(" -", s, wb[s].dimensions)
