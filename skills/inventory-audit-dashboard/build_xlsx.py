#!/usr/bin/env python3
"""Build Inventory_Audit_Full_Data.xlsx for Al Faihaa Group from alfaihaa_inventory_audit.json."""
import json
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT, size=16, bold=True, color="0F6E5C")
SUB_FONT = Font(name=FONT, size=10, color="425953")
LABEL_FONT = Font(name=FONT, size=10, bold=True)
VAL_FONT = Font(name=FONT, size=14, bold=True)
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="748D86")
WARN_FILL = PatternFill("solid", fgColor="FBF0DD")
CRIT_FILL = PatternFill("solid", fgColor="FBE7E3")
THIN = Side(style="thin", color="D8E0DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

wb = Workbook()
wb.remove(wb.active)


def style_header(ws, row, ncols):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEAD_FILL
        cell.font = HEAD_FONT
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = ws.cell(row=row + 1, column=1)
    ws.auto_filter.ref = f"A{row}:{get_column_letter(ncols)}{row}"


def write_table(ws, headers, rows, start_row=1, col_formats=None, widths=None):
    for j, h in enumerate(headers, start=1):
        ws.cell(row=start_row, column=j, value=h)
    style_header(ws, start_row, len(headers))
    for i, r in enumerate(rows, start=start_row + 1):
        for j, h in enumerate(headers, start=1):
            v = r.get(h_key(h))
            cell = ws.cell(row=i, column=j, value=v)
            cell.font = Font(name=FONT, size=10)
            cell.border = BORDER
            if col_formats and h in col_formats:
                cell.number_format = col_formats[h]
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(j)].width = w
    return start_row + len(rows) + 1


KEYMAP = {}


def h_key(h):
    return KEYMAP.get(h, h)


def add_sheet(name, headers, rows, keymap, col_formats=None, widths=None):
    ws = wb.create_sheet(name)
    global KEYMAP
    KEYMAP = keymap
    write_table(ws, headers, rows, col_formats=col_formats, widths=widths)
    return ws


MONEY = '#,##0.00;(#,##0.00);"-"'
MONEY0 = '#,##0;(#,##0);"-"'
QTY = '#,##0.0;(#,##0.0);"-"'

# ---------------------------------------------------------------------------
# Summary sheet
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Summary")
ws.sheet_view.showGridLines = False
ws["B2"] = "Al Faihaa Group — Inventory Analysis & Audit"
ws["B2"].font = TITLE_FONT
ws["B3"] = "Cure+ (read-only) · EXSYS Inventory Module · Riyadh · Buraydah 1 · Buraydah 2 · Rafha"
ws["B3"].font = SUB_FONT
ws["B4"] = f"As of {AUDIT['meta']['as_of'][:10]}  ·  Generated {AUDIT['meta']['generated_at'][:10]}"
ws["B4"].font = NOTE_FONT

kpi_defs = [
    ("Total inventory value (SAR)", "='Valuation by Store'!E:E", "sum", MONEY0),
    ("SKU-store lines", "='Valuation by Store'!C:C", "sumcount", "#,##0"),
    ("Overstock value (SAR)", "=SUM(Overstock!F:F)", None, MONEY0),
    ("Overstock SKU count", "=COUNTA(Overstock!C6:C100000)", None, "#,##0"),
    ("Slow-moving / dead value (SAR)", "=SUM('Slow-Moving'!F:F)", None, MONEY0),
    ("Slow-moving SKU count", "=COUNTA('Slow-Moving'!C6:C100000)", None, "#,##0"),
    ("Expiry-risk batches", "=COUNTA('Expiry Risk'!D6:D100000)-COUNTIF('Expiry Risk'!H6:H100000,\"past expiry\")", None, "#,##0"),
    ("Past-expiry batches still on hand", "=COUNTIF('Expiry Risk'!H:H,\"past expiry\")", None, "#,##0"),
    ("Receiving / data-quality flags", "=COUNTA('Receiving Flags'!C6:C100000)", None, "#,##0"),
    ("Supplier price-gap savings identified (SAR)", "=SUM('Savings Opportunities'!G:G)", None, MONEY0),
]
row = 6
ws.cell(row=row, column=2, value="Key metric").font = LABEL_FONT
ws.cell(row=row, column=3, value="Value").font = LABEL_FONT
row += 1
kpi_start = row
labels_formulas = [
    ("Total inventory value (SAR)", "=SUM('Valuation by Store'!E6:E100000)", MONEY0),
    ("SKU-store lines with on-hand stock", "=SUM('Valuation by Store'!C6:C100000)", "#,##0"),
    ("Overstock value — days-of-cover method (SAR)", "=SUM(Overstock!F6:F100000)", MONEY0),
    ("Overstock SKU count", "=COUNTA(Overstock!C6:C100000)", "#,##0"),
    ("Slow-moving / dead-stock value (SAR)", "=SUM('Slow-Moving'!F6:F100000)", MONEY0),
    ("Slow-moving SKU count", "=COUNTA('Slow-Moving'!C6:C100000)", "#,##0"),
    ("Near-expiry batches", None, "#,##0"),
    ("Near-expiry value (SAR)", None, MONEY0),
    ("Past-expiry batches, still on hand", None, "#,##0"),
    ("Past-expiry value (SAR)", None, MONEY0),
    ("Total expiry risk value (SAR)", None, MONEY0),
    ("Receiving / data-quality flags", "=COUNTA('Receiving Flags'!C6:C100000)", "#,##0"),
    ("Supplier price-gap savings identified (SAR)", "=SUM('Savings Opportunities'!G6:G100000)", MONEY0),
]
# static values for the expiry-value KPIs (pulled straight from the audit JSON — see the
# Expiry Risk sheet's own "Risk value by branch" table for the live per-branch breakdown)
STATIC_VALUES = {
    "Near-expiry batches": AUDIT["kpi"]["expiry_risk_sku_count"],
    "Near-expiry value (SAR)": AUDIT["kpi"]["expiry_risk_value"],
    "Past-expiry batches, still on hand": AUDIT["kpi"]["past_expiry_on_hand_count"],
    "Past-expiry value (SAR)": AUDIT["kpi"]["past_expiry_value"],
    "Total expiry risk value (SAR)": round(AUDIT["kpi"]["expiry_risk_value"] + AUDIT["kpi"]["past_expiry_value"], 2),
}
for label, formula, fmt in labels_formulas:
    ws.cell(row=row, column=2, value=label).font = Font(name=FONT, size=10)
    value = STATIC_VALUES.get(label, formula)
    c = ws.cell(row=row, column=3, value=value)
    c.font = Font(name=FONT, size=11, bold=True)
    c.number_format = fmt
    row += 1

row += 1
ws.cell(row=row, column=2, value="Value by branch / store").font = LABEL_FONT
row += 1
vbs_header_row = row
for j, h in enumerate(["Branch", "Store", "SKUs", "Value (SAR)"], start=2):
    ws.cell(row=row, column=j, value=h).font = HEAD_FONT
    ws.cell(row=row, column=j).fill = HEAD_FILL
row += 1
vbs_data_start = row
for r in sorted(AUDIT["valuation_by_store"], key=lambda x: -x["total_value"]):
    ws.cell(row=row, column=2, value=r["branch"])
    ws.cell(row=row, column=3, value=r["store_name"])
    ws.cell(row=row, column=4, value=r["sku_count"])
    c = ws.cell(row=row, column=5, value=r["total_value"]); c.number_format = MONEY0
    row += 1

ws.column_dimensions["A"].width = 2
ws.column_dimensions["B"].width = 44
ws.column_dimensions["C"].width = 22
ws.column_dimensions["D"].width = 14
ws.column_dimensions["E"].width = 16

print("Summary sheet written")

# ---------------------------------------------------------------------------
# Methodology sheet
# ---------------------------------------------------------------------------
ws = wb.create_sheet("Methodology")
ws.sheet_view.showGridLines = False
ws["B2"] = "Methodology & Data-Quality Findings"
ws["B2"].font = TITLE_FONT
ws["B3"] = "Rebuild of the Inventory Analysis & Audit module for Al Faihaa Group (see Inventory_Analysis_Audit_Direct.md for the original demo-entity methodology this rebuild follows)."
ws["B3"].font = SUB_FONT
ws["B3"].alignment = Alignment(wrap_text=True)
ws.merge_cells("B3:H3")
ws.row_dimensions[3].height = 30

row = 5
ws.cell(row=row, column=2, value="Source").font = LABEL_FONT
row += 1
src_lines = [
    f"Entity: {AUDIT['meta']['entity']}",
    f"Source: {AUDIT['meta']['source']}",
    f"Branches covered: {', '.join(AUDIT['meta']['branch_names'][b] for b in AUDIT['meta']['branches_covered'])}",
    f"As of (latest transaction in this extract): {AUDIT['meta']['as_of']}",
    f"Workbook generated: {AUDIT['meta']['generated_at']}",
    f"Total transaction rows processed: {AUDIT['meta']['total_transaction_rows']:,} ({AUDIT['meta']['malformed_rows_dropped']} malformed rows dropped)",
    f"Purchase invoice lines: {AUDIT['meta']['purchase_invoice_lines']:,}",
    f"Batch balance rows: {AUDIT['meta']['batch_rows_total']:,}",
]
for line in src_lines:
    ws.cell(row=row, column=2, value=line).font = Font(name=FONT, size=10)
    ws.merge_cells(f"B{row}:H{row}")
    row += 1

row += 1
ws.cell(row=row, column=2, value="Findings & caveats").font = LABEL_FONT
row += 1
for f in AUDIT["meta"]["findings"]:
    cell = ws.cell(row=row, column=2, value="• " + f)
    cell.font = Font(name=FONT, size=9.5)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(f"B{row}:H{row}")
    ws.row_dimensions[row].height = 42
    row += 1

row += 1
ws.cell(row=row, column=2, value="Standing checks (recommended cadence)").font = LABEL_FONT
row += 1
checks = [
    "Weekly: re-run Slow-Moving and Expiry Risk tabs — these should drive action (transfer, discount, write-off) before value is lost.",
    "Monthly: re-run Purchases by Supplier / Savings Opportunities and act on the largest identified price gaps.",
    "Spot-check unusually large single-line receiving quantities going forward, not just retroactively (Receiving Flags tab).",
    "Recalibrate per-product MIN/MAX/REORDER levels — every balance row currently shares the same ERP default; until then the ERP's own overstock alert is a config artifact, not a real signal (see Overview note on the Overstock tab).",
    "Re-verify the four-branch scope operationally — this extract shows live activity at all four branches, which supersedes an earlier note that the inventory module was Riyadh-only.",
    "Any future purchasing analysis should confirm whether primary_unit_cost remains net-of-discount and UOM-normalized at the source (see Purchasing findings above) before trusting a 'cheapest supplier' ranking.",
]
for c_ in checks:
    cell = ws.cell(row=row, column=2, value="• " + c_)
    cell.font = Font(name=FONT, size=9.5)
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(f"B{row}:H{row}")
    ws.row_dimensions[row].height = 28
    row += 1

for col, w in zip("ABCDEFGH", [2, 100, 10, 10, 10, 10, 10, 10]):
    ws.column_dimensions[col].width = w

print("Methodology sheet written")

wb.save(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
print("base workbook saved (Summary + Methodology) — data tabs added in part 2")
