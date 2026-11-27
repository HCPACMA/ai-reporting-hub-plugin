#!/usr/bin/env python3
"""Add ABC/Pareto, Cycle-Count Variance, and Vendor Concentration sheets to
Alfaihaa_Inventory_Audit_Full_Data.xlsx -- the 3 best-practice tabs proposed (but not built)
alongside Fraud Detection, now built on real data (see build_alfaihaa_abc_vendor_cyclecount.py
and the dashboard's matching tabs)."""
import json
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule

HERE = Path(__file__).parent
AUDIT = json.loads((HERE / "pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json").read_text(encoding="utf-8"))
wb = load_workbook(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
for name in ("ABC-Pareto", "Cycle-Count Variance", "Vendor Concentration"):
    if name in wb.sheetnames:
        del wb[name]

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
GREEN_FILL = PatternFill("solid", fgColor="E3F3EC")

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
            if isinstance(v, list):
                v = ", ".join(v)
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


def note(ws, row, col, text, height=40, span=8):
    c = ws.cell(row=row, column=col, value=text)
    c.font = NOTE_FONT
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[row].height = height
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + span - 1)
    return c


# =============================================================================
# SHEET 1: ABC / PARETO VALUE CONCENTRATION
# =============================================================================
A = AUDIT["abc_analysis"]
cw = A["company_wide"]

ws = wb.create_sheet("ABC-Pareto")
ws.sheet_view.showGridLines = False
ws["A1"] = "ABC / Pareto Value Concentration"
ws["A1"].font = TITLE_FONT
note(ws, 2, 1, A["methodology"], height=55)

r = 4
ws.cell(row=r, column=1, value="Tier summary").font = SUBTITLE_FONT
r += 1
tier_fill = {"A": RED_FILL, "B": AMBER_FILL, "C": GREEN_FILL}
r = write_table(ws, ["Tier", "SKUs", "% of SKUs", "Value (SAR)", "% of value"], cw["tiers"],
                 ["tier", "sku_count", "sku_pct", "value", "value_pct"],
                 [None, "#,##0", PCT1, MONEY0, PCT1], [8, 10, 12, 16, 12], r, autofilter=False)
for i, t in enumerate(cw["tiers"]):
    ws.cell(row=r - len(cw["tiers"]) + 1 + i, column=1).fill = tier_fill.get(t["tier"], PatternFill())

r += 3
ws.cell(row=r, column=1, value=f"Ranked items — company-wide ({len(cw['items'])} SKUs; {cw['zero_or_unpriced_value_skus_excluded']} zero/unpriced excluded)").font = SUBTITLE_FONT
r += 1
item_headers = ["Tier", "Code", "Product", "Branches", "Qty on hand", "Value (SAR)", "% of value", "Cumulative %"]
item_keys = ["tier", "product", "product_name", "branches", "qty", "value", "cum_value", "cum_pct"]
# recompute per-row value_pct for display (not stored per item, derive from cum diffs is unnecessary -- use value/total)
for it in cw["items"]:
    it["value_pct_disp"] = round(100.0 * it["value"] / cw["total_value"], 3) if cw["total_value"] else 0.0
item_keys = ["tier", "product", "product_name", "branches", "qty", "value", "value_pct_disp", "cum_pct"]
item_start = r
r = write_table(ws, item_headers, cw["items"], item_keys,
                 [None, None, None, None, QTY0, MONEY0, PCT1, PCT1],
                 [7, 12, 40, 26, 13, 14, 11, 13], r)
ws.conditional_formatting.add(f"A{item_start+1}:A{r}", CellIsRule(operator="equal", formula=['"A"'], fill=RED_FILL))
ws.conditional_formatting.add(f"A{item_start+1}:A{r}", CellIsRule(operator="equal", formula=['"B"'], fill=AMBER_FILL))
ws.conditional_formatting.add(f"A{item_start+1}:A{r}", CellIsRule(operator="equal", formula=['"C"'], fill=GREEN_FILL))

r += 2
ws.cell(row=r, column=1, value="Tier breakdown by branch").font = SUBTITLE_FONT
r += 1
branch_rows = []
for b in A["by_branch"]:
    ta = next(t for t in b["tiers"] if t["tier"] == "A")
    tb = next(t for t in b["tiers"] if t["tier"] == "B")
    tc = next(t for t in b["tiers"] if t["tier"] == "C")
    branch_rows.append({"branch": b["branch"], "sku_count": b["sku_count"], "total_value": b["total_value"],
                         "tier_a": f"{ta['sku_count']} ({ta['value_pct']}%)", "tier_b": f"{tb['sku_count']} ({tb['value_pct']}%)",
                         "tier_c": f"{tc['sku_count']} ({tc['value_pct']}%)"})
write_table(ws, ["Branch", "SKUs", "Total value (SAR)", "Tier A SKUs (% value)", "Tier B SKUs (% value)", "Tier C SKUs (% value)"],
            branch_rows, ["branch", "sku_count", "total_value", "tier_a", "tier_b", "tier_c"],
            [None, "#,##0", MONEY0, None, None, None], [14, 9, 16, 20, 20, 20], r, autofilter=False)

print(f"ABC-Pareto sheet written -- {len(cw['items'])} items ranked")

# =============================================================================
# SHEET 2: CYCLE-COUNT VARIANCE TRACKING
# =============================================================================
C = AUDIT["cycle_count_variance"]
K = C["kpi"]

ws = wb.create_sheet("Cycle-Count Variance")
ws.sheet_view.showGridLines = False
ws["A1"] = "Cycle-Count Variance Tracking"
ws["A1"].font = TITLE_FONT
note(ws, 2, 1, C["methodology"], height=55)
note(ws, 3, 1, "Audit-trail gap: " + C["data_quality_note"], height=55)
ws["A3"].fill = AMBER_FILL

r = 5
ws.cell(row=r, column=1, value="Summary").font = SUBTITLE_FONT
r += 1
kpi_rows = [
    ("Count-adjustment events (2019-2025)", K["total_events"], "#,##0", "Date range", K["date_range"], None),
    ("Gain events", K["gain_events"], "#,##0", "Gain value (SAR)", K["gain_value"], MONEY0),
    ("Loss events", K["loss_events"], "#,##0", "Loss value (SAR)", K["loss_value"], MONEY0),
    ("Net value (SAR)", K["net_value"], MONEY0, "", None, None),
    ("Distinct SKUs with variance", K["distinct_skus_with_variance"], "#,##0", "Recurring (2+ events)", K["recurring_variance_skus"], "#,##0"),
    ("Events logged in 2026", K["events_logged_in_2026"], "#,##0", "Last event date", K["last_event_date"], None),
    ("Unvalued events (no cost basis)", K["unvalued_events"], "#,##0", "", None, None),
    ("Adjustments linked to a formal count session", K["count_id_linked_events"], "#,##0", "of total events", K["total_events"], "#,##0"),
]
kpi_head = r
for j, h in enumerate(["Metric", "Value", "", "Secondary metric", "Value", ""], start=1):
    c = ws.cell(row=kpi_head, column=j, value=h); c.font = HEAD_FONT; c.fill = HEAD_FILL
r += 1
for label, v1, f1, label2, v2, f2 in kpi_rows:
    ws.cell(row=r, column=1, value=label).font = DATA_FONT
    c = ws.cell(row=r, column=2, value=v1); c.font = BOLD_FONT
    if f1: c.number_format = f1
    if label2:
        ws.cell(row=r, column=4, value=label2).font = DATA_FONT
        c = ws.cell(row=r, column=5, value=v2); c.font = BOLD_FONT
        if f2: c.number_format = f2
    for col in range(1, 6):
        ws.cell(row=r, column=col).border = BORDER
    r += 1
for col, w in zip("ABCDEF", [34, 14, 3, 28, 16, 3]):
    ws.column_dimensions[col].width = w

r += 2
ws.cell(row=r, column=1, value="By branch").font = SUBTITLE_FONT
r += 1
r = write_table(ws, ["Branch", "Events", "Gain events", "Loss events", "Gain value (SAR)", "Loss value (SAR)", "Net value (SAR)", "Last event"],
                 C["by_branch"], ["branch", "events", "gain_events", "loss_events", "gain_value", "loss_value", "net_value", "last_event_date"],
                 [None, "#,##0", "#,##0", "#,##0", MONEY0, MONEY0, MONEY0, None], [14, 9, 11, 11, 15, 15, 15, 12], r, autofilter=False)

r += 2
ws.cell(row=r, column=1, value=f"By SKU ({len(C['by_product'])} products)").font = SUBTITLE_FONT
r += 1
recurring_start = r + 1
r = write_table(ws, ["Code", "Product", "Branch(es)", "Events", "Recurring?", "Gain value (SAR)", "Loss value (SAR)", "Net value (SAR)", "Last event"],
                 C["by_product"], ["product", "product_name", "branches", "event_count", "recurring", "gain_value", "loss_value", "net_value", "last_event_date"],
                 [None, None, None, "#,##0", None, MONEY0, MONEY0, MONEY0, None], [11, 38, 24, 9, 10, 15, 15, 15, 12], r)
ws.conditional_formatting.add(f"E{recurring_start}:E{r}", CellIsRule(operator="equal", formula=["TRUE"], fill=AMBER_FILL))

r += 2
ws.cell(row=r, column=1, value=f"By posting user ({len(C['by_user'])} users)").font = SUBTITLE_FONT
r += 1
r = write_table(ws, ["User", "Events", "Gain value (SAR)", "Loss value (SAR)", "Net value (SAR)"],
                 C["by_user"], ["user", "events", "gain_value", "loss_value", "net_value"],
                 [None, "#,##0", MONEY0, MONEY0, MONEY0], [16, 9, 15, 15, 15], r)

r += 2
ws.cell(row=r, column=1, value=f"All events ({len(C['events'])})").font = SUBTITLE_FONT
r += 1
type_start = r + 1
r = write_table(ws, ["Date", "Type", "Branch", "Store", "Code", "Product", "Qty", "Value (SAR)", "Adjustment #", "Batch", "Posted by"],
                 C["events"], ["adjs_date", "type", "branch", "store_name", "product", "product_name", "qty", "value", "adjs_no", "batch_no", "posted_by"],
                 [None, None, None, None, None, None, QTY0, MONEY0, None, None, None],
                 [12, 8, 12, 16, 11, 38, 9, 13, 16, 16, 14], r)
ws.conditional_formatting.add(f"B{type_start}:B{r}", CellIsRule(operator="equal", formula=['"Loss"'], fill=RED_FILL))
ws.conditional_formatting.add(f"B{type_start}:B{r}", CellIsRule(operator="equal", formula=['"Gain"'], fill=GREEN_FILL))

print(f"Cycle-Count Variance sheet written -- {len(C['events'])} events, {len(C['by_product'])} SKUs")

# =============================================================================
# SHEET 3: VENDOR CONCENTRATION & DEPENDENCY
# =============================================================================
V = AUDIT["vendor_concentration"]
Kv = V["kpi"]

ws = wb.create_sheet("Vendor Concentration")
ws.sheet_view.showGridLines = False
ws["A1"] = "Vendor Concentration & Dependency"
ws["A1"].font = TITLE_FONT
note(ws, 2, 1, V["methodology"], height=55)

r = 4
ws.cell(row=r, column=1, value="Summary").font = SUBTITLE_FONT
r += 1
kpi_rows = [
    ("Total 2026 purchase spend (SAR)", Kv["total_spend_2026"], MONEY0, "Active suppliers", Kv["supplier_count"], "#,##0"),
    ("HHI (concentration index)", Kv["hhi"], "#,##0", "Concentration level", Kv["concentration_level"], None),
    ("Top-5 supplier share", Kv["top5_share_pct"] / 100, "0.0%", "Top-10 supplier share", Kv["top10_share_pct"] / 100, "0.0%"),
    ("Single-source products", Kv["single_source_product_count"], "#,##0", "Est. spend (SAR)", Kv["single_source_spend_est"], MONEY0),
    ("Single-source share of total spend", Kv["single_source_share_pct"] / 100, "0.0%", "", None, None),
]
kpi_head = r
for j, h in enumerate(["Metric", "Value", "", "Secondary metric", "Value", ""], start=1):
    c = ws.cell(row=kpi_head, column=j, value=h); c.font = HEAD_FONT; c.fill = HEAD_FILL
r += 1
for label, v1, f1, label2, v2, f2 in kpi_rows:
    ws.cell(row=r, column=1, value=label).font = DATA_FONT
    c = ws.cell(row=r, column=2, value=v1); c.font = BOLD_FONT
    if f1: c.number_format = f1
    if label2:
        ws.cell(row=r, column=4, value=label2).font = DATA_FONT
        c = ws.cell(row=r, column=5, value=v2); c.font = BOLD_FONT
        if f2: c.number_format = f2
    for col in range(1, 6):
        ws.cell(row=r, column=col).border = BORDER
    r += 1
for col, w in zip("ABCDEF", [34, 16, 3, 24, 20, 3]):
    ws.column_dimensions[col].width = w

r += 2
ws.cell(row=r, column=1, value=f"Top suppliers by 2026 spend ({len(V['top_suppliers'])})").font = SUBTITLE_FONT
r += 1
r = write_table(ws, ["Supplier", "Spend (SAR)", "Share", "Cumulative %", "Products", "PI lines", "Branches"],
                 V["top_suppliers"], ["supplier_name", "spend", "share_pct", "cum_pct", "product_count", "line_count", "branches"],
                 [None, MONEY0, PCT1, PCT1, "#,##0", "#,##0", None], [40, 15, 10, 13, 11, 10, 20], r)

r += 2
ws.cell(row=r, column=1, value="Concentration by branch").font = SUBTITLE_FONT
r += 1
note(ws, r, 1, V["purchasing_model_note"], height=55)
ws.cell(row=r, column=1).fill = AMBER_FILL
r += 1
write_table(ws, ["Branch", "Total spend (SAR)", "Suppliers", "HHI", "Top supplier", "Top supplier share"],
            V["by_branch"], ["branch", "total_spend", "supplier_count", "hhi", "top_supplier_name", "top_supplier_share_pct"],
            [None, MONEY0, "#,##0", "#,##0", None, PCT1], [14, 16, 10, 8, 34, 14], r, autofilter=False)

r_after_branch = r + 1 + len(V["by_branch"]) + 2
r = r_after_branch
ws.cell(row=r, column=1, value=f"Single-source dependency risk ({len(V['single_source_products'])} products)").font = SUBTITLE_FONT
r += 1
note(ws, r, 1, "Products bought from exactly one supplier in 2026 -- ranked by estimated spend. These are the items most exposed to a single vendor's pricing, supply, or relationship disruption.", height=28)
r += 1
write_table(ws, ["Code", "Product", "Supplier", "Est. spend (SAR)", "Qty", "Last purchase"],
            V["single_source_products"], ["product", "product_name", "supplier_name", "spend_est", "qty", "last_date"],
            [None, None, None, MONEY0, QTY0, None], [11, 40, 34, 15, 10, 13], r)

print(f"Vendor Concentration sheet written -- {len(V['top_suppliers'])} suppliers, {len(V['single_source_products'])} single-source products")

# =============================================================================
# Wire headline KPIs into the Summary sheet
# =============================================================================
sm = wb["Summary"]
vbs_row = None
for i in range(1, 60):
    if sm.cell(row=i, column=2).value == "Value by branch / store":
        vbs_row = i
        break
new_metrics = [
    ("ABC/Pareto — Tier A SKUs (80% of value)", cw["tiers"][0]["sku_count"], "#,##0"),
    ("Cycle-count — net variance value 2019-2025 (SAR)", K["net_value"], MONEY0),
    ("Cycle-count — recurring-variance SKUs", K["recurring_variance_skus"], "#,##0"),
    ("Vendor — HHI concentration index", Kv["hhi"], "#,##0"),
    ("Vendor — single-source products", Kv["single_source_product_count"], "#,##0"),
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
print(f"Summary sheet: {len(new_metrics)} KPI rows {'updated in place at' if existing_row else 'inserted before'} row {insert_row}")

wb.save(HERE / "Alfaihaa_Inventory_Audit_Full_Data.xlsx")
print("saved.")
for s in wb.sheetnames:
    print(" -", s, wb[s].dimensions)
