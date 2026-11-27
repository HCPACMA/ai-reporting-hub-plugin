#!/usr/bin/env python3
"""Part 2: add the 9 data tabs to Alfaihaa_Inventory_Audit_Full_Data.xlsx."""
import json
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule, FormulaRule

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))
wb = load_workbook(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C")
HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE_FONT = Font(name=FONT, size=13, bold=True, color="0F6E5C")
NOTE_FONT = Font(name=FONT, size=9, italic=True, color="425953")
DATA_FONT = Font(name=FONT, size=10)
THIN = Side(style="thin", color="D8E0DD")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AMBER_FILL = PatternFill("solid", fgColor="FBF0DD")
RED_FILL = PatternFill("solid", fgColor="FBE7E3")

MONEY0 = '#,##0;(#,##0);"-"'
MONEY2 = '#,##0.0000;(#,##0.0000);"-"'
QTY0 = '#,##0;(#,##0);"-"'
QTY1 = '#,##0.0;(#,##0.0);"-"'
PCT1 = '0.0%;(0.0%);"-"'
DATE = 'yyyy-mm-dd'


def new_sheet(name, title, note):
    ws = wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = TITLE_FONT
    ws["A2"] = note
    ws["A2"].font = NOTE_FONT
    ws["A2"].alignment = Alignment(wrap_text=True)
    ws.row_dimensions[2].height = 26
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


# 1. Valuation by Store
ws = new_sheet("Valuation by Store", "Inventory Valuation & Position",
                "On-hand value per branch/store, off each SKU's most recent transaction unit cost (moving-average proxy — see Methodology).")
write_table(ws, ["Branch", "Store", "SKU count", "Qty on hand", "Value (SAR)", "SKUs w/o cost basis"],
            sorted(AUDIT["valuation_by_store"], key=lambda r: -r["total_value"]),
            ["branch", "store_name", "sku_count", "total_qty", "total_value", "unknown_cost_skus"],
            [None, None, QTY0, QTY0, MONEY0, QTY0], [14, 20, 12, 14, 16, 18])

# 2. Overstock
ws = new_sheet("Overstock", "Overstock — Real Days-of-Cover",
                f"On-hand ÷ (6-month trailing dispensed qty ÷ 180); flagged when >365 days of cover, or zero consumption AND not received in "
                f"that same 6-month window (a fresh delivery isn't overstock yet). For comparison, the ERP's own MIN/MAX default flags "
                f"{AUDIT['kpi']['raw_erp_overstock_sku_count_config_artifact']:,} SKUs (SAR {AUDIT['kpi']['raw_erp_overstock_value_config_artifact']:,.0f}) "
                f"— a config artifact, not a real signal (every row shares the same default).")
rows = sorted(AUDIT["overstock"], key=lambda r: -(r["on_hand_cost"] or 0))
lr = write_table(ws, ["Branch", "Store", "Code", "Product", "On hand", "Value (SAR)", "Dispensed /6mo", "Days of cover", "Last received"],
                  rows, ["branch", "store_name", "product", "product_name", "on_hand", "on_hand_cost", "qty_out_6mo", "days_of_cover", "last_received"],
                  [None, None, None, None, QTY0, MONEY0, QTY0, QTY0, DATE], [12, 16, 10, 34, 11, 13, 14, 13, 14])
ws.conditional_formatting.add(f"H6:H{lr}", CellIsRule(operator="greaterThan", formula=["365"], fill=AMBER_FILL))

# 3. Slow-Moving
ws = new_sheet("Slow-Moving", "Slow-Moving & Dead Stock",
               "No dispense in 90+ days as of the data snapshot, and not received within that same 90 days (a recent delivery hasn't had "
               "time to prove it's slow). Overlaps the Overstock tab but tracked as a separate watchlist.")
rows = sorted(AUDIT["slow_moving"], key=lambda r: (r["last_out_date"] or ""))
write_table(ws, ["Branch", "Store", "Code", "Product", "On hand", "Value (SAR)", "Last dispensed", "Last received"],
            rows, ["branch", "store_name", "product", "product_name", "on_hand", "on_hand_cost", "last_out_date", "last_received"],
            [None, None, None, None, QTY0, MONEY0, None, DATE], [12, 16, 10, 34, 11, 13, 16, 14])

# 4. Expiry Risk
ws = new_sheet("Expiry Risk", "Expiry Risk — Value by Branch & Total",
               "Real batch-level balances (batch tracking is populated for this tenant, unlike the original demo-entity build) — not a receipt-date proxy. "
               "Value (SAR) = qty on hand x most recent unit cost, so Risk can be sized in money as well as batch count.")

# --- branch/overall value summary block (near-expiry vs past-expiry) ---
evb = AUDIT.get("expiry_value_by_branch", {"near_expiry": [], "past_expiry": []})
near_by_branch = {r["branch"]: r for r in evb.get("near_expiry", [])}
past_by_branch = {r["branch"]: r for r in evb.get("past_expiry", [])}
branches = sorted(set(near_by_branch) | set(past_by_branch))

srow = 4
ws.cell(row=srow, column=1, value="Risk value by branch").font = TITLE_FONT
ws.row_dimensions[srow].height = 18
srow += 1
sum_headers = ["Branch", "Near-expiry batches", "Near-expiry value (SAR)", "Past-expiry batches", "Past-expiry value (SAR)", "Total risk value (SAR)"]
for j, h in enumerate(sum_headers, start=1):
    c = ws.cell(row=srow, column=j, value=h)
    c.font = HEAD_FONT
    c.fill = HEAD_FILL
    c.alignment = Alignment(vertical="center", wrap_text=True)
sum_start = srow + 1
r = sum_start
for b in branches:
    n = near_by_branch.get(b, {"count": 0, "value": 0})
    p = past_by_branch.get(b, {"count": 0, "value": 0})
    ws.cell(row=r, column=1, value=b).font = DATA_FONT
    ws.cell(row=r, column=2, value=n.get("count", 0)).font = DATA_FONT
    c = ws.cell(row=r, column=3, value=n.get("value") or 0); c.font = DATA_FONT; c.number_format = MONEY0
    ws.cell(row=r, column=4, value=p.get("count", 0)).font = DATA_FONT
    c = ws.cell(row=r, column=5, value=p.get("value") or 0); c.font = DATA_FONT; c.number_format = MONEY0
    c = ws.cell(row=r, column=6, value=f"=C{r}+E{r}"); c.font = DATA_FONT; c.number_format = MONEY0
    for col in range(1, 7):
        ws.cell(row=r, column=col).border = BORDER
    r += 1
total_row = r
ws.cell(row=total_row, column=1, value="Total (all branches)").font = Font(name=FONT, size=10, bold=True)
c = ws.cell(row=total_row, column=2, value=f"=SUM(B{sum_start}:B{total_row-1})"); c.font = Font(name=FONT, size=10, bold=True)
c = ws.cell(row=total_row, column=3, value=f"=SUM(C{sum_start}:C{total_row-1})"); c.font = Font(name=FONT, size=10, bold=True); c.number_format = MONEY0
c = ws.cell(row=total_row, column=4, value=f"=SUM(D{sum_start}:D{total_row-1})"); c.font = Font(name=FONT, size=10, bold=True)
c = ws.cell(row=total_row, column=5, value=f"=SUM(E{sum_start}:E{total_row-1})"); c.font = Font(name=FONT, size=10, bold=True); c.number_format = MONEY0
c = ws.cell(row=total_row, column=6, value=f"=SUM(F{sum_start}:F{total_row-1})"); c.font = Font(name=FONT, size=10, bold=True); c.number_format = MONEY0
for col in range(1, 7):
    ws.cell(row=total_row, column=col).border = BORDER
    ws.cell(row=total_row, column=col).fill = AMBER_FILL

# --- detail table (batch-level, with per-line value) ---
detail_start = total_row + 3
ws.cell(row=detail_start - 1, column=1, value="Batch-level detail").font = TITLE_FONT
combined = ([dict(r, status="near expiry") for r in AUDIT["expiry_risk"]] +
            [dict(r, status="past expiry") for r in AUDIT["past_expiry_on_hand"]])
combined.sort(key=lambda r: r["expiry_date"])
lr = write_table(ws, ["Branch", "Store", "Code", "Product", "Batch", "Qty", "Value (SAR)", "Expiry date", "Status"],
                  combined, ["branch", "store", "product", "product_name", "batch_no", "qty_on_hand", "value", "expiry_date", "status"],
                  [None, None, None, None, None, QTY0, MONEY0, DATE, None], [12, 8, 10, 34, 16, 10, 13, 14, 12],
                  start_row=detail_start)
ws.conditional_formatting.add(f"I{detail_start+1}:I{lr}", FormulaRule(formula=[f'$I{detail_start+1}="past expiry"'], fill=RED_FILL))

# 5. Receiving Flags
ws = new_sheet("Receiving Flags", "Receiving / Data-Quality Flags",
               "Single receipt lines >20x (or <1/20x) that product's own trailing median receipt quantity — a signature of a mis-keyed unit or quantity at receiving, not necessarily a real event.")
rows = sorted(AUDIT["receiving_flags"], key=lambda r: -abs(r["qty"]))
write_table(ws, ["Branch", "Store", "Code", "Type", "Date", "Qty (primary)", "Product median receipt", "Unit cost"],
            rows, ["branch", "store", "product", "t_type", "date", "qty", "product_median_receipt_qty", "cost"],
            [None, None, None, None, DATE, QTY0, QTY0, MONEY2], [12, 8, 10, 8, 18, 14, 18, 12])

# 6. Cross-Branch Audit
ws = new_sheet("Cross-Branch Audit", "Cross-Branch Peer Audit",
               "Inventory value, SKU count and overstock share per store — meaningful across all 4 branches, each contributing at least one active store.")
osval = {}
for o in AUDIT["overstock"]:
    k = (o["branch"], o["store_name"])
    osval[k] = osval.get(k, 0) + (o["on_hand_cost"] or 0)
rows = []
for r in sorted(AUDIT["cross_org_peer_audit"], key=lambda r: -r["total_value"]):
    ov = osval.get((r["branch"], r["store_name"]), 0)
    rows.append({**r, "overstock_value": ov, "overstock_pct": (ov / r["total_value"]) if r["total_value"] else None})
write_table(ws, ["Branch", "Store", "SKUs", "Value (SAR)", "Overstock value (SAR)", "Overstock % of value"],
            rows, ["branch", "store_name", "sku_count", "total_value", "overstock_value", "overstock_pct"],
            [None, None, QTY0, MONEY0, MONEY0, PCT1], [14, 20, 10, 15, 18, 16])

# 7. Dispense by Cost Center
ws = new_sheet("Dispense by CC", "Dispense by Cost Center, Month over Month",
               "Monthly qty & cost of stock dispensed, by branch and cost center.")
rows = sorted(AUDIT["dispense_by_cost_center"], key=lambda r: (r["branch"], r["cost_center_name"] or "", r["month"]))
write_table(ws, ["Branch", "Cost center", "Month", "Qty", "Cost (SAR)"],
            rows, ["branch", "cost_center_name", "month", "qty", "cost"],
            [None, None, None, QTY0, MONEY0], [12, 30, 10, 12, 14])

# 8. Purchases by Supplier
ws = new_sheet("Purchases by Supplier", "Purchases by Supplier, Month over Month",
               "Net purchase cost by supplier per month (posted purchase lines).")
rows = sorted(AUDIT["purchases_by_supplier"], key=lambda r: (r["month"], -r["total_cost"]))
write_table(ws, ["Supplier no.", "Supplier", "Month", "Qty", "Total cost (SAR)", "Line count"],
            rows, ["supplier_no", "supplier_name", "month", "qty", "total_cost", "line_count"],
            [None, None, None, QTY0, MONEY0, QTY0], [12, 32, 10, 12, 15, 10])

# 9. Price Matrix
ws = new_sheet("Price Matrix", "Product x Supplier Price Matrix",
               "All purchase lines, including outlier-flagged ones (median x3 / x1/3 per product) shown for transparency.")
rows = sorted(AUDIT["product_supplier_price_matrix"], key=lambda r: r["product"])
lr = write_table(ws, ["Code", "Product", "Supplier", "Min price", "Avg price (wtd)", "Max price", "Qty", "Lines", "Last purchase", "Outlier lines"],
                  rows, ["product", "product_name", "supplier_name", "min_price", "avg_price", "max_price", "tot_qty", "line_cnt", "last_date", "outlier_lines"],
                  [None, None, None, MONEY2, MONEY2, MONEY2, QTY0, QTY0, DATE, QTY0], [10, 30, 26, 11, 13, 11, 10, 8, 14, 12])
ws.conditional_formatting.add(f"J6:J{lr}", CellIsRule(operator="greaterThan", formula=["0"], fill=AMBER_FILL))

# 10. Savings Opportunities
ws = new_sheet("Savings Opportunities", "Best-Price Savings Opportunities",
               "Products bought from 2+ suppliers, outlier lines excluded — cheapest vs. priciest qty-weighted average net price. Gap SAR = priciest - cheapest price (per-unit; not multiplied by volume).")
rows = sorted(AUDIT["supplier_savings_opportunities"], key=lambda r: -(r["gap_pct"] or 0))
for r in rows:
    r["gap_sar"] = (r["priciest_price"] - r["cheapest_price"]) if r["priciest_price"] is not None and r["cheapest_price"] is not None else None
    r["gap_pct"] = (r["gap_pct"] / 100.0) if r.get("gap_pct") is not None else None
write_table(ws, ["Code", "Product", "Cheapest supplier", "Cheapest price", "Priciest supplier", "Priciest price", "Gap (SAR/unit)", "Gap %"],
            rows, ["product", "product_name", "cheapest_supplier", "cheapest_price", "priciest_supplier", "priciest_price", "gap_sar", "gap_pct"],
            [None, None, None, MONEY2, None, MONEY2, MONEY2, PCT1], [10, 30, 26, 12, 26, 12, 14, 10])

wb.save(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
print("all data tabs written")
for s in wb.sheetnames:
    print(" -", s, wb[s].dimensions)
