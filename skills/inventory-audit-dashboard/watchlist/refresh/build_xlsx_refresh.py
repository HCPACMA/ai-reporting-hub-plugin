#!/usr/bin/env python3
"""Refresh Alfaihaa_Inventory_Audit_Full_Data.xlsx to dashboard Version 25 (2026-10-03, purchase returns netted).
Input : workbook (device copy) + audit_v25.json (the AUDIT payload embedded in the published dashboard)
Does  : rebuilds the four purchasing sheets from live purchase-invoice data, corrects Summary figures,
        adds Live Check, Data Status, Price & Vendor Watch, Price Changes (with one-click scan links),
        Demand Forecast, Rebalancing, ABC x XYZ and Transfer Workflow sheets, and Returns & Identity Review.  Idempotent."""
import json, sys
from urllib.parse import quote
from openpyxl import load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC, AUD, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SCAN_BASE = sys.argv[4] if len(sys.argv) > 4 else r"X:\VOUCHERS_DOCUMENTS\PI"
A = json.load(open(AUD, encoding="utf-8"))
wb = load_workbook(SRC)

FONT = "Arial"
HEAD_FILL = PatternFill("solid", fgColor="0F6E5C"); HEAD_FONT = Font(name=FONT, size=10, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, size=13, bold=True, color="0F6E5C"); SUB = Font(name=FONT, size=11, bold=True, color="0F6E5C")
NOTE = Font(name=FONT, size=9, italic=True, color="425953"); DATA = Font(name=FONT, size=10); BOLD = Font(name=FONT, size=10, bold=True)
LINK = Font(name=FONT, size=10, color="0563C1", underline="single")
THIN = Side(style="thin", color="D8E0DD"); BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
AMBER = PatternFill("solid", fgColor="FBF0DD"); RED = PatternFill("solid", fgColor="FBE7E3"); GREEN = PatternFill("solid", fgColor="E3F3EC")
M0 = '#,##0;(#,##0);"-"'; M2 = '#,##0.00;(#,##0.00);"-"'; M4 = '#,##0.0000;(#,##0.0000);"-"'; Q1 = '#,##0.0;(#,##0.0);"-"'; P1 = '0.0"%"'; PCT = '0.0%'

def fresh(name, title, note, index=None, tab=None):
    if name in wb.sheetnames:
        pos = wb.sheetnames.index(name); del wb[name]
        index = pos if index is None else index
    ws = wb.create_sheet(name, index) if index is not None else wb.create_sheet(name)
    ws.sheet_view.showGridLines = False
    ws["A1"] = title; ws["A1"].font = TITLE
    ws["A2"] = note; ws["A2"].font = NOTE; ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:H2"); ws.row_dimensions[2].height = 52
    if tab: ws.sheet_properties.tabColor = tab
    return ws

def section(ws, row, text):
    ws.cell(row, 1, text).font = SUB
    return row + 1

def kv(ws, row, pairs, fmts=None):
    for i, (k, v) in enumerate(pairs):
        ws.cell(row + i, 1, k).font = DATA
        c = ws.cell(row + i, 2, v); c.font = BOLD
        if fmts and fmts.get(k): c.number_format = fmts[k]
        elif isinstance(v, float): c.number_format = M2
        elif isinstance(v, int): c.number_format = M0
    return row + len(pairs) + 1

def table(ws, row, headers, rows, fmts=None, widths=None, freeze=False, filt=True, fills=None):
    fmts = fmts or {}
    for j, h in enumerate(headers, 1):
        c = ws.cell(row, j, h); c.fill = HEAD_FILL; c.font = HEAD_FONT; c.alignment = Alignment(vertical="center", wrap_text=True); c.border = BORDER
    for i, r in enumerate(rows, 1):
        for j, v in enumerate(r, 1):
            c = ws.cell(row + i, j, v); c.font = DATA; c.border = BORDER
            if j in fmts and isinstance(v, (int, float)): c.number_format = fmts[j]
        if fills:
            f = fills(r)
            if f:
                for j in range(1, len(headers) + 1): ws.cell(row + i, j).fill = f
    if widths:
        for j, w in enumerate(widths, 1):
            cur = ws.column_dimensions[get_column_letter(j)].width
            ws.column_dimensions[get_column_letter(j)].width = max(w, cur or 0) if cur else w
    if filt and rows: ws.auto_filter.ref = f"A{row}:{get_column_letter(len(headers))}{row + len(rows)}"
    if freeze: ws.freeze_panes = ws.cell(row + 1, 1)
    return row + len(rows) + 2

W = A["watchlist"]; WK = W["kpi"]; PC = A["price_changes"]; PK = PC["kpi"]; L = A["live_check"]; T = L["total"]
RV = A["returns_review"]; RB = RV["bridge"]
V = A["vendor_concentration"]; VK = V["kpi"]; TW = A["transfer_workflow"]; TK = TW["kpi"]
AS_OF = L["as_of"]

# ---------------------------------------------------------------- purchasing sheets (live data)
ws = fresh("Purchases by Supplier", "Purchases by Supplier, Month over Month",
           f"Net purchase cost by supplier per month — {A['meta']['purchase_invoice_lines']:,} posted purchase lines, 1 Jan to 29 Sep 2026, re-pulled live from the ERP (IM_PRODUCTS_TRANSACTIONS, PI, posted), net of purchase returns (SAR {RB['returns_value']:,.0f} returned on {RB['returns_lines']} lines; gross SAR {RB['spend_gross']:,.0f}).")
table(ws, 5, ["Supplier no.", "Supplier", "Month", "Qty", "Total cost (SAR)", "Line count"],
      [[r["supplier_no"], r["supplier_name"], r["month"], r["qty"], r["total_cost"], r["line_count"]] for r in A["purchases_by_supplier"]],
      {4: M0, 5: M0, 6: M0}, [12, 34, 10, 12, 16, 10], freeze=True)

ws = fresh("Price Matrix", "Product x Supplier Price Matrix",
           "All purchase lines, outlier-flagged ones included for transparency (median x3 / x1/3 per product). Live purchase data to 29 Sep 2026.")
table(ws, 5, ["Code", "Product", "Supplier", "Min price", "Avg price (wtd)", "Max price", "Qty", "Lines", "Last purchase", "Outlier lines"],
      [[r["product"], r["product_name"], r["supplier_name"], r["min_price"], r["avg_price"], r["max_price"], r["tot_qty"], r["line_cnt"], r["last_date"], r["outlier_lines"]] for r in A["product_supplier_price_matrix"]],
      {4: M4, 5: M4, 6: M4, 7: M0, 8: M0, 10: M0}, [10, 34, 30, 11, 13, 11, 10, 8, 13, 10], freeze=True)

ws = fresh("Savings Opportunities", "Best-Price Savings Opportunities",
           "Products bought from 2+ suppliers, outlier lines excluded — cheapest vs priciest qty-weighted average net price. NOTE: 'Gap (SAR/unit)' is a per-unit difference, NOT money; the money figure (price paid above the best price x quantity) is on the Price & Vendor Watch sheet.")
table(ws, 5, ["Code", "Product", "Cheapest supplier", "Cheapest price", "Priciest supplier", "Priciest price", "Gap (SAR/unit)", "Gap %"],
      [[r["product"], r["product_name"], r["cheapest_supplier"], r["cheapest_price"], r["priciest_supplier"], r["priciest_price"], round(r["priciest_price"] - r["cheapest_price"], 4), r["gap_pct"] / 100] for r in A["supplier_savings_opportunities"]],
      {4: M4, 6: M4, 7: M4, 8: PCT}, [10, 34, 28, 13, 28, 13, 14, 9], freeze=True)

ws = fresh("Vendor Concentration", "Vendor Concentration & Dependency",
           "Supplier spend = purchase-invoice-line net unit cost x quantity, 2026 posted lines (live, to 29 Sep). HHI = sum of squared supplier shares on a 0-10,000 scale: <1,500 low, 1,500-2,500 moderate, >2,500 high. Single-source = products bought from exactly one supplier in 2026.")
r = section(ws, 4, "Summary")
r = kv(ws, r, [("Total 2026 purchase spend (SAR)", VK["total_spend_2026"]), ("Active suppliers", VK["supplier_count"]), ("HHI (concentration index)", VK["hhi"]),
               ("Concentration level", VK["concentration_level"]), ("Top-5 supplier share", VK["top5_share_pct"] / 100), ("Top-10 supplier share", VK["top10_share_pct"] / 100),
               ("Single-source products", VK["single_source_product_count"]), ("Single-source est. spend (SAR)", VK["single_source_spend_est"]), ("Single-source share of total spend", VK["single_source_share_pct"] / 100)],
        {"Top-5 supplier share": PCT, "Top-10 supplier share": PCT, "Single-source share of total spend": PCT, "HHI (concentration index)": '0.0'})
r = section(ws, r, "Top suppliers by 2026 spend")
r = table(ws, r, ["Supplier", "Spend (SAR)", "Share", "Cumulative", "Products", "PI lines"],
          [[s["supplier_name"], s["spend"], s["share_pct"] / 100, s["cum_pct"] / 100, s["product_count"], s["line_count"]] for s in V["top_suppliers"]],
          {2: M0, 3: PCT, 4: PCT, 5: M0, 6: M0}, [34, 16, 10, 12, 10, 10], filt=False)
r = section(ws, r, "By branch")
r = table(ws, r, ["Branch", "Total spend (SAR)", "Suppliers", "HHI", "Top supplier", "Top supplier share"],
          [[b["branch"], b["total_spend"], b["supplier_count"], b["hhi"], b["top_supplier_name"], b["top_supplier_share_pct"] / 100] for b in V["by_branch"]],
          {2: M0, 3: M0, 4: '0.0', 6: PCT}, filt=False)
r = section(ws, r, "Single-source dependency (ranked by estimated spend)")
r = table(ws, r, ["Code", "Product", "Supplier", "Est. spend (SAR)", "Qty", "PI lines", "Last purchase"],
          [[s["product"], s["product_name"], s["supplier_name"], s["spend_est"], s["qty"], s["line_count"], s["last_date"]] for s in V["single_source_products"]],
          {4: M0, 5: M0, 6: M0}, [12, 34, 30, 16, 10, 10, 13], filt=False)

# ---------------------------------------------------------------- Summary corrections
S = wb["Summary"]
S["B4"] = f"Snapshot as of 2026-09-08 · live checks and purchasing refreshed {AS_OF} (dashboard Version 25)"
def setrow(label_start, label=None, value=None, fmt=None):
    for rr in range(6, 34):
        v = S.cell(rr, 2).value
        if isinstance(v, str) and v.startswith(label_start):
            if label: S.cell(rr, 2).value = label
            if value is not None:
                S.cell(rr, 3).value = value
                if fmt: S.cell(rr, 3).number_format = fmt
            return rr
    raise SystemExit("summary row not found: " + label_start)
setrow(("Supplier price-gap savings", "Price & vendor watch"), "Price & vendor watch — paid above best price, last 90 days (SAR)", WK["unique_sar_90d"], M0)
setrow("Fraud detection — same-user", "Fraud detection — same-user create+post, excl. designed transfer-receipt step (count)", TK["same_user_excl_tr"], M0)
setrow("Vendor — HHI", None, VK["hhi"], '0.0')
setrow("Vendor — single-source", None, VK["single_source_product_count"], M0)
# stock-today lines under the metric block
nxt = 34
for rr in range(34, 60):
    if S.cell(rr, 2).value == "Value by branch / store": nxt = rr; break
# extra KPI rows are kept on the Live Check / Data Status sheets to avoid shifting the existing chart block

# ---------------------------------------------------------------- Fraud Detection: correct the same-user row
F = wb["Fraud Detection"]
for rr in range(5, 15):
    if F.cell(rr, 1).value in ("Same-user create+post transactions", "Same-user create+post, excl. designed transfer-receipt step"):
        F.cell(rr, 1).value = "Same-user create+post, excl. designed transfer-receipt step"
        F.cell(rr, 2).value = TK["same_user_excl_tr"]; F.cell(rr, 5).value = TK["same_user_excl_tr_pct"]
        F.cell(rr, 3).value = f"(was {TK['same_user_total']:,}; {TK['tr_same_user_lines']:,} are the receiving step)"; F.cell(rr, 3).font = NOTE
        break
else: raise SystemExit("fraud row not found")

# ---------------------------------------------------------------- Live Check
ws = fresh("Live Check", "Live Check — stock today against the 8 September snapshot",
           L["basis"], index=wb.sheetnames.index("Valuation by Store") + 1, tab="0F6E5C")
r = kv(ws, 4, [("As of", L["as_of"]), ("Snapshot as of", L["snapshot_as_of"]), ("Stock value today (SAR)", T["val_live"]), ("Snapshot value (SAR)", T["val_snap"]),
               ("Change (SAR)", T["delta_val"]), ("Change %", T["delta_pct"] / 100), ("SKU-store lines today", T["sku_live"]), ("SKU-store lines in snapshot", T["sku_snap"]),
               ("New lines since snapshot", L["new_lines_since_snapshot"]), ("Lines now at zero", L["dropped_lines_since_snapshot"]),
               ("Lines costed by estimate (new products)", T["est_lines"]), ("Value of estimated lines (SAR)", T["est_val"])], {"Change %": PCT, "As of": '@', "Snapshot as of": '@'})
r = section(ws, r, "By store")
r = table(ws, r, ["Branch", "Store", "SKUs 8 Sep", "SKUs today", "Qty 8 Sep", "Qty today", "Value 8 Sep (SAR)", "Value today (SAR)", "Change (SAR)", "Estimated-cost lines"],
          [[x["branch"], x["store_name"], x["sku_snap"], x["sku_live"], x["qty_snap"], x["qty_live"], x["val_snap"], x["val_live"], round(x["val_live"] - x["val_snap"], 2), x["est_lines"]] for x in L["rows"]],
          {3: M0, 4: M0, 5: M0, 6: M0, 7: M0, 8: M0, 9: M0, 10: M0}, [20, 20, 12, 12, 12, 12, 16, 16, 14, 14], filt=False)
r = section(ws, r, "Activity since the snapshot (2026-09-09 to 2026-10-03)")
act = L["activity"]
r = kv(ws, r, [("Dispense lines", act["dispense"]), ("Transfers sent (TS)", act["transfer_sent"]), ("Transfers received (TR)", act["transfer_received"]),
               ("Purchase lines (all statuses)", act["purchase_lines_all_status"]), ("Purchase lines dated from 1 Oct (not yet posted)", act["purchase_lines_since_oct1"]),
               ("Purchase returns (PR)", act["returns_pr"]), ("Corrections (CRC)", act["receipts_crc"])])
mh = ["Code", "Product", "Value 8 Sep (SAR)", "Value today (SAR)", "Change (SAR)"]
r = section(ws, r, "Biggest value decreases")
r = table(ws, r, mh, [[x["product"], x["name"], x["val_snap"], x["val_live"], x["delta"]] for x in L["top_down"]], {3: M0, 4: M0, 5: M0}, filt=False)
r = section(ws, r, "Biggest value increases")
r = table(ws, r, mh, [[x["product"], x["name"], x["val_snap"], x["val_live"], x["delta"]] for x in L["top_up"]], {3: M0, 4: M0, 5: M0}, filt=False)

# ---------------------------------------------------------------- Price & Vendor Watch
ws = fresh("Price & Vendor Watch", "Price & Vendor Watch-list",
           f"SAR-ranked alerts from live purchase-invoice data (as of {WK['as_of']}, last {WK['window_days']} days from {WK['window_start']}). supplier_gap = paid >=10% above the best supplier's price; price_up = same supplier now >=10% above its earlier 2026 price; entry_outlier = a line 3x or more away from the product median (likely a keying/unit slip).", tab="B8791A")
r = kv(ws, 4, [("Alerts", WK["alerts"]), ("Paid above best price, 90 days (SAR)", WK["unique_sar_90d"]), ("Annualised (SAR)", WK["unique_sar_annualized"]),
               ("New alerts since last cut", WK["new_alerts"]), ("Worse than last cut", WK["worse_alerts"]), ("Cleared since last cut", WK["cleared_alerts"]),
               ("Spend, last 90 days (SAR)", WK["spend_90d"]), ("Spend, previous 90 days (SAR)", WK["spend_prev_90d"]), ("Active suppliers (90d)", WK["suppliers_90d"]),
               ("New suppliers (90d)", WK["new_suppliers_90d"]), ("Sole-source spend share (90d)", WK["sole_source_share_pct"] / 100)], {"Sole-source spend share (90d)": PCT})
r = section(ws, r, "Alerts, ranked by SAR impact")
def _alert(a):
    if a["type"] == "supplier_gap":
        paid, ref, what, pct = a["paid"], a["best"], "best price - " + a.get("best_supplier_name", ""), a["pct"]
    elif a["type"] == "price_up":
        paid, ref, what, pct = a["to"], a["from"], "same supplier, earlier 2026 price", a["pct"]
    else:
        paid, ref, what, pct = a["price"], a["ref_price"], "product median (ratio %.1fx)" % a["ratio"], (a["ratio"] - 1) * 100
    return [a["type"], a["product"], a["product_name"], a["supplier_name"], paid, ref, what, pct / 100, a["qty"], a["date"], a["impact"], a["annualized"], "yes" if a["sole_source"] else "", a["chg"]]
r = table(ws, r, ["Type", "Code", "Product", "Supplier", "Price paid (SAR/unit)", "Reference price", "Reference is", "Above reference %", "Qty", "Last purchase", "Impact (SAR)", "Annualised (SAR)", "Sole source", "Since last cut"],
          [_alert(a) for a in W["alerts"]],
          {5: M4, 6: M4, 8: '0.0%', 9: M0, 11: M0, 12: M0}, [14, 10, 32, 30, 14, 13, 34, 12, 10, 13, 13, 15, 10, 12], freeze=False,
          fills=lambda x: RED if x[13] in ("new", "worse") else None)
r = section(ws, r, "Weekly trend of open SAR impact")
r = table(ws, r, ["Cut", "Alerts", "Unique SAR", "price_up SAR", "supplier_gap SAR", "entry_outlier SAR"],
          [[t["cut"], t["alerts"], t["unique_sar"], t["price_up"], t["supplier_gap"], t["entry_outlier"]] for t in W["trend"]], {3: M0, 4: M0, 5: M0, 6: M0}, filt=False)
r = section(ws, r, "Supplier share movement (last 90 days vs previous 90)")
r = table(ws, r, ["Supplier", "Spend 90d (SAR)", "Spend prev 90d (SAR)", "Share %", "Prev share %", "Lines", "Products", "New supplier", "Alerts", "price_up SAR", "gap SAR"],
          [[s["supplier_name"], s["spend_90d"], s["spend_prev_90d"], s["share_pct"], s["share_prev_pct"], s["lines"], s["products"], "yes" if s["new_supplier"] else "", s["alerts"], s["price_up_sar"], s["gap_sar"]] for s in W["suppliers"]],
          {2: M0, 3: M0, 4: '0.0', 5: '0.0', 6: M0, 7: M0, 9: M0, 10: M0, 11: M0}, filt=False)
r = section(ws, r, "Sole-source products (one supplier, last 90 days)")
r = table(ws, r, ["Code", "Product", "Supplier", "Spend 90d (SAR)", "Price now", "Price before", "Change %", "Last purchase", "Days since"],
          [[s["product"], s["product_name"], s["supplier_name"], s["spend_90d"], s["price_now"], s["price_before"], s["pct"], s["last_date"], s["days_since"]] for s in W["sole_source"]],
          {4: M0, 5: M4, 6: M4, 7: '0.0', 9: M0}, filt=False)

# ---------------------------------------------------------------- Price Changes (one-click scan links)
ws = fresh("Price Changes", "Price changes between invoices — same product, same supplier",
           f"Every time a supplier invoiced a product at a different net price from its previous invoice (any size, up or down), 2026 to {PK['as_of']}, net of purchase returns (changes that touch a returned line are on the Returns & Identity Review sheet and are not counted here). Scan columns are clickable in Excel on a PC that can reach {SCAN_BASE} — one click opens the PDF. 'no scan attached' = the ERP has no attachment for that invoice (scanning began 31 Mar 2026). SAR effect = (newer price - earlier price) x units on the newer invoice. 'Check entry' = move of 3x or more (likely a keying/unit slip).", tab="B8791A")
r = kv(ws, 4, [("Changes in 2026", PK["events_total"]), (f"Newer invoice in last 90 days (from {PK['window_start']})", PK["events_window"]), ("Increases (90d)", PK["up_window"]), ("Decreases (90d)", PK["down_window"]),
               ("Paid more, excl. check-entry (90d, SAR)", PK["up_sar_window"]), ("Paid less (90d, SAR)", PK["down_sar_window"]), ("Check-entry moves (90d)", PK["extreme_window"]), ("Both invoices scanned (90d)", PK["events_both_scanned_window"])])
HDR = ["Newer date", "Code", "Product", "Supplier", "Earlier PI", "Earlier date", "Earlier price", "Earlier supplier inv.", "Earlier scan", "Newer PI", "Newer price", "Units", "Newer supplier inv.", "Newer scan", "Change %", "SAR effect", "Direction", "Check entry", "Last 90 days", "Latest for pair", "Other scans"]
rows = []; linkcells = []
def scanref(att):
    if not att: return None, None, ""
    first = att[0][1]; extra = "; ".join(a[1] for a in att[1:])
    return first, "file:///" + SCAN_BASE.replace("\\", "/").replace(" ", "%20") + "/" + quote(first, safe="()"), extra
for e in PC["events"]:
    f1, u1, x1 = scanref(e["from"]["att"]); f2, u2, x2 = scanref(e["to"]["att"])
    rows.append([e["to"]["d"], e["p"], e["pn"], e["sn"], e["from"]["inv"], e["from"]["d"], e["from"]["px"], e["from"]["so"], f1 or "no scan attached",
                 e["to"]["inv"], e["to"]["px"], e["to"]["q"], e["to"]["so"], f2 or "no scan attached", e["pct"] / 100, e["sar"], e["dir"], "yes" if e["x"] else "",
                 "yes" if e["to"]["d"] >= PK["window_start"] else "", "yes" if e["latest"] else "", "; ".join(filter(None, [x1, x2]))])
    linkcells.append((u1, u2))
start = r + 1
r2 = table(ws, r, HDR, rows, {7: M4, 11: M4, 12: M0, 15: '0.0%;-0.0%', 16: M2}, [12, 10, 32, 28, 17, 12, 12, 14, 34, 17, 12, 9, 14, 34, 10, 12, 10, 10, 10, 10, 30], freeze=False,
           fills=lambda x: AMBER if x[17] == "yes" else None)
for i, (u1, u2) in enumerate(linkcells):
    for col, u in ((9, u1), (14, u2)):
        if u:
            c = ws.cell(start + i, col); c.hyperlink = u; c.font = LINK
ws.freeze_panes = ws.cell(start, 4)

# ---------------------------------------------------------------- Demand Forecast
D = A["demand_forecast"]; DK = D["kpi"]
ws = fresh("Demand Forecast", "SKU-level demand forecast — top 50 Tier-A SKUs",
           "Holt-Winters / Holt / naive-average on 24+ months of monthly Dispense; 3-month forecast with an 80% band, backtested per SKU. Reclassified = the forecast changes the overstock verdict versus the trailing-average rule. " + D["methodology"][:300], tab="2F6F9F")
r = kv(ws, 4, [("SKUs forecasted", DK["skus_forecasted"]), ("Value covered (SAR)", DK["total_value_forecasted"]), ("Reclassified vs naive rule", DK["reclassified_count"]),
               ("SAR moved out of overstock", DK["sar_moved_out_of_overstock"]), ("SAR newly flagged", DK["sar_newly_flagged"]), ("Median backtest MAPE %", DK["median_backtest_mape_pct"])])
r = table(ws, r, ["Code", "Product", "On hand", "On-hand value (SAR)", "Model", "Confidence", "Backtest MAPE %", "Trend %", "Months history", "Avg last 3m", "Fcst m1", "Fcst m2", "Fcst m3", "Fcst 3m total", "CI low", "CI high", "Cover (naive, months)", "Cover (forecast, months)", "Naive flag", "Forecast flag", "Reclassified"],
          [[i["product"], i["product_name"], i["on_hand_qty"], i["on_hand_value"], i["model"], i["confidence"], i["backtest_mape_pct"], i["trend_pct"], i["n_months_history"], i["avg_last3"], *i["forecast"], i["forecast_total_3mo"], i["ci_low_3mo"], i["ci_high_3mo"], i["naive_cover_months"], i["forecast_cover_months"], i["naive_flag"], i["forecast_flag"], "yes" if i["reclassified"] else ""] for i in D["items"]],
          {3: M0, 4: M0, 7: '0.0', 8: '0.0', 9: M0, 10: M0, 11: M0, 12: M0, 13: M0, 14: M0, 15: M0, 16: M0, 17: '0.0', 18: '0.0'}, [10, 34, 11, 14, 18, 11, 12, 9, 10, 11, 9, 9, 9, 12, 9, 9, 12, 12, 11, 11, 11], freeze=True,
          fills=lambda x: AMBER if x[20] == "yes" else None)

# ---------------------------------------------------------------- Rebalancing
R = A["rebalancing"]; RK = R["kpi"]
ws = fresh("Rebalancing", "Suggested inter-branch transfers (Riyadh hub -> branches)",
           "Riyadh on-hand above 4 months of its own Dispense is treated as transferable surplus; each receiving branch's need = its share of the company 3-month forecast minus its own on-hand. Suggestions only: nothing is posted in the ERP. " + R["methodology"][:250], tab="2F6F9F")
r = kv(ws, 4, [("Transfers suggested", RK["recommendation_count"]), ("Distinct SKUs", RK["distinct_skus_recommended"]), ("Total units", RK["total_transfer_qty"]), ("Total value (SAR)", RK["total_transfer_value"])])
table(ws, r, ["Code", "Product", "From", "To", "Transfer qty", "Transfer value (SAR)", "Riyadh on hand", "Riyadh surplus", "To-branch on hand", "To-branch fcst 3m", "To-branch deficit", "Share of demand", "Model", "Confidence"],
      [[x["product"], x["product_name"], x["from_branch"], x["to_branch"], x["transfer_qty"], x["transfer_value"], x["riyadh_on_hand_qty"], x["riyadh_surplus_qty"], x["to_branch_on_hand_qty"], x["to_branch_forecast_3mo"], x["to_branch_deficit_qty"], x["to_branch_share_of_demand"], x["forecast_model"], x["confidence"]] for x in R["recommendations"]],
      {5: M0, 6: M0, 7: M0, 8: M0, 9: M0, 10: M0, 11: M0, 12: PCT}, [10, 34, 10, 12, 12, 14, 12, 12, 12, 12, 12, 12, 16, 11], freeze=True)

# ---------------------------------------------------------------- ABC x XYZ
X = A["abc_xyz"]; XK = X["kpi"]
ws = fresh("ABC x XYZ", "ABC x XYZ — value tier crossed with demand variability",
           f"CV of monthly Dispense, {XK['window']}: X = steady (CV<{XK['cv_cutoffs']['X']}), Y = variable (<{XK['cv_cutoffs']['Y']}), Z = erratic. Excess depends on the assumed replenishment lead time H (default {XK['default_H']:.0f} months) - see the sensitivity table; the real lead time is still an open input.", tab="2F6F9F")
r = kv(ws, 4, [("SKUs ranked", XK["skus_ranked"]), ("SKUs classified", XK["skus_classified"]), ("No demand in window", XK["skus_no_demand"]), ("New (under 12 months)", XK["skus_new"]),
               ("Excess vs policy at default H (SAR)", XK["excess_value_default"]), ("Excess SKUs at default H", XK["excess_skus_default"]), ("At-risk SKUs at default H", XK["at_risk_skus_default"]), ("A/Z SKUs", XK["az_skus"]), ("A/Z value (SAR)", XK["az_value"])])
r = section(ws, r, "Cells")
r = table(ws, r, ["Cell", "Tier", "Variability", "SKUs", "Value (SAR)", "Excess vs policy (SAR)", "At-risk SKUs", "Target service %"],
          [[c["cell"], c["tier"], c["xyz"], c["skus"], c["value"], c.get("excess_value"), c.get("at_risk"), c.get("service_pct")] for c in X["cells"]], {4: M0, 5: M0, 6: M0, 7: M0}, [10, 34, 12, 10, 14, 18, 12, 14], filt=False)
r = section(ws, r, "Sensitivity to lead time H")
r = table(ws, r, ["H (months)", "Excess value (SAR)", "Excess SKUs", "At-risk SKUs"], [[s["H"], s["excess_value"], s["excess_skus"], s["at_risk_skus"]] for s in XK["sensitivity"]], {2: M0, 3: M0, 4: M0}, filt=False)
r = section(ws, r, "SKU detail")
table(ws, r, ["Code", "Product", "Tier", "XYZ", "Cell", "Qty", "Value (SAR)", "Unit cost", "Mean monthly", "SD monthly", "CV", "Months", "Target qty", "Excess qty", "Excess value (SAR)", "At risk"],
      [[i["product"], i["product_name"], i["tier"], i["xyz"], i["cell"], i["qty"], i["value"], i["unit_cost"], i["mean_m"], i["sd_m"], i["cv"], i["n_months"], i["target_qty"], i["excess_qty"], i["excess_value"], "yes" if i["at_risk"] else ""] for i in X["items"]],
      {6: M0, 7: M0, 8: M2, 9: Q1, 10: Q1, 11: '0.00', 12: M0, 13: M0, 14: M0, 15: M0}, None)

# ---------------------------------------------------------------- Transfer workflow
ws = fresh("Transfer Workflow", "Transfer workflow and the corrected same-user finding",
           "Transfers are posted in three steps: (1) the sender posts, (2) the receiver creates and posts the receipt, (3) the store accountant does the consolidated GL posting. So the receiver's create+post is the designed step, not a segregation-of-duties breach, and Send-Transfer 'late posting' is the monthly consolidation.", tab="A8452B")
r = kv(ws, 4, [("Sent documents posted", TK["docs_sent_posted"]), ("Received documents posted", TK["docs_received_posted"]), ("GL-consolidated", TK["gl_consolidated"]), ("GL pending", TK["gl_pending"]),
               ("Cancelled sends", TK["cancelled_sends"]), ("Quantity-checked lines", TK["qty_lines_checked"]), ("Quantity mismatches", TK["qty_mismatch_lines"]),
               ("Same-user create+post, all types (before)", TK["same_user_total"]), ("... of which the receiving step (TR)", TK["tr_same_user_lines"]), ("Same-user create+post, excl. TR (after)", TK["same_user_excl_tr"]),
               ("... as % of postings excl. TR", TK["same_user_excl_tr_pct"] / 100), ("Sent and received by the same person (documents)", TK["same_person_docs"]), ("... of which Buraydah 1 <-> 2", TK["same_person_bur_docs"])], {"... as % of postings excl. TR": PCT})
r = section(ws, r, "Steps")
r = table(ws, r, ["Step", "Who", "Document", "What it does"], [[s["n"], s["who"], s["doc"], s["does"]] for s in TW["steps"]], None, [8, 28, 28, 70], filt=False)
r = section(ws, r, "Routes")
r = table(ws, r, ["Route", "Documents", "Avg days to receive", "Max days", "GL vouchers", "Same person", "Sender staff", "Receiver staff"],
          [[x["route"], x["docs"], x["avg_days"], x["max_days"], x["gl_vouchers"], x["same_person"], x["sender_staff"], x["receiver_staff"]] for x in TW["routes"]], {2: M0, 3: '0.0', 4: '0.0', 5: M0, 6: M0}, filt=False)
r = section(ws, r, "Same-user create+post by user (excluding the receiving step)")
r = table(ws, r, ["User", "Posted total", "Posted excl. TR", "TR same-user", "Same-user excl. TR", "% of own non-TR postings"],
          [[u["user"], u["posted_total"], u["posted_excl_tr"], u["tr_same_user"], u["same_user_excl_tr"], u["same_user_excl_tr_pct"] / 100] for u in TW["user_summary_excl_tr"]], {2: M0, 3: M0, 4: M0, 5: M0, 6: PCT}, filt=False)
r = section(ws, r, "Lines still flagged (same user, excl. receiving step)")
table(ws, r, ["Branch", "Store", "Code", "Product", "Type", "Document", "Date", "Created by", "Posted by", "Value (SAR)"],
      [[x["branch"], x["store_name"], x["product"], x["product_name"], x["transaction_type"], x["transaction_no"], x["transaction_date"][:10], x["created_by"], x["posted_by"], x["value"]] for x in TW["sod_rows_excl_tr"]], {10: M0}, None)


# ---------------------------------------------------------------- Returns & Identity Review
ws = fresh("Returns & Identity Review", "Purchase returns and item-identity review",
           "A purchase return is matched to its purchase invoice by the invoice number on the return document (IM_PURCHASE_INVOICE_RETURN_M.PINV_NO); the returned quantity is removed from that invoice line before any price test. "
           "A line can also be received under another item's code (the supplier invoice names a different item from the ERP) and then returned; the ERP keeps no supplier item description, so the name is confirmed on the scan. "
           "Each returned line scores a point per flag (price far from the usual = 2, whole line returned, stock moved before the return, return in a later month, SAR 5,000 or more); High = 4+, Medium = 2-3. No return document carries a reason.", tab="A8452B")
r = kv(ws, 4, [("Return documents 2026", RB["returns_docs"]), ("Returned lines", RB["returns_lines"]), ("Value returned (SAR)", RB["returns_value"]),
               ("Invoice lines returned in full", RB["invoice_lines_returned_full"]), ("Invoice lines returned in part", RB["invoice_lines_returned_partial"]),
               ("Purchases gross (SAR)", RB["spend_gross"]), ("Purchases net of returns (SAR)", RB["spend_net"]),
               ("Price-change events left out (all 2026)", RV["kpi"]["events_returned_total"]), ("... of which in the last 90 days", RV["kpi"]["events_returned_window"]),
               ("Watch-list alerts removed by a return", RV["watch"]["cleared"]), ("... SAR", RV["watch"]["cleared_sar"]),
               ("Watch-list unique SAR without / with the returns", f"{RV['watch']['unique_sar_gross']:,.0f} / {RV['watch']['unique_sar_net']:,.0f}")])
r = section(ws, r, "Returned lines, ranked by review score (set the Review status column by hand)")
LV = {"high": RED, "medium": AMBER}
rows = []
for x in sorted(RV["lines"], key=lambda x: (-x["score"], -x["val"])):
    f = x["flags"]
    rows.append([x["level"].title(), x["score"], x["p"], x["pn"], x["sn"], x["pinv"], x["pi_date"], x["pi_price"], x["ret_no"], x["ret_date"], x["days"], x["ret_tot_qty"], x["pi_qty"], x["val"],
                 x["med"], x["ratio"], x["ref_src"] or "no history", x["moved_qty"], x["disp_qty"], "yes" if f["price_off"] else "", "yes" if f["full"] else "partial", "yes" if f["moved"] else "", "yes" if f["cross_month"] else "", "", ""])
r = table(ws, r, ["Level", "Score", "Code", "Product", "Supplier", "Purchase invoice", "Received", "Price paid", "Return doc", "Returned", "Days", "Qty returned", "Qty invoiced", "SAR returned",
                  "Reference price", "Price / reference", "Reference is", "Moved before return", "of which dispensed", "Price far from usual", "Returned in full", "Stock moved", "Later month", "Review status", "Notes"],
          rows, {2: M0, 8: M4, 11: M0, 12: M0, 13: M0, 14: M0, 15: M4, 16: '0.00', 18: M0, 19: M0}, [9, 7, 10, 34, 28, 17, 12, 11, 16, 12, 7, 11, 11, 12, 12, 11, 30, 12, 12, 10, 10, 10, 10, 22, 30], freeze=False,
          fills=lambda x: LV.get(x[0].lower()))
r = section(ws, r, "Price changes left out because the quantity was returned (not counted on Price Changes or the watch-list)")
r = table(ws, r, ["Status", "Code", "Product", "Supplier", "Earlier PI", "Earlier price", "Earlier qty returned", "Newer PI", "Newer price", "Newer qty returned", "Newer date", "Change %", "SAR (not counted)"],
          [["returned in full" if e["ret_status"] == "full" else "partly returned", e["p"], e["pn"], e["sn"], e["from"]["inv"], e["from"]["px"], (e["ret_from"] or {}).get("qty"), e["to"]["inv"], e["to"]["px"], (e["ret_to"] or {}).get("qty"), e["to"]["d"], e["pct"] / 100, e["sar"]] for e in RV["events_returned"]],
          {6: M4, 7: M0, 9: M4, 10: M0, 12: '0.0%;-0.0%', 13: M0}, None, filt=False)

# ---------------------------------------------------------------- Data Status
ws = fresh("Data Status", "Data status and refresh log",
           f"Which figures are live and which still rest on the 8 September snapshot. Refreshed {AS_OF} from the Cure MCP (read-only).", index=1, tab="425953")
rows = [
    ["Purchase invoices (watch-list, price changes, vendor, price matrix, savings)", f"Live - {A['meta']['purchase_invoice_lines']:,} posted lines to 29 Sep 2026, net of {RB['returns_lines']} returned lines (SAR {RB['returns_value']:,.0f})", f"Re-pulled 2026-10-03; purchase returns netted out (net SAR {RB['spend_net']:,.0f} against SAR {RB['spend_gross']:,.0f} gross)"],
    ["Purchase returns (IM_PURCHASE_INVOICE_RETURN_M / IM_PRODUCTS_TRANSACTIONS PR)", f"Live - {RB['returns_docs']} documents, {RB['returns_lines']} lines to 28 Sep 2026", "Matched to the purchase invoice by PINV_NO; see Returns & Identity Review"],
    ["Scan attachments (EX_ATTACHMENTS, PI)", "Live - 355 files on 315 invoices", "Re-pulled 2026-10-03: no new attachment since 2026-10-02"],
    ["Stock on hand and valuation (Live Check)", "Live - VINV_STORE_PRODUCTS, 1,249 non-zero lines", f"Value SAR {T['val_live']:,.0f} vs snapshot SAR {T['val_snap']:,.0f} ({T['delta_pct']:+.1f}%)"],
    ["Overstock, slow-moving, expiry, aging, never-dispensed, cross-branch, receiving flags, ABC/Pareto", "Snapshot 2026-09-08", "Needs the full re-extract (about 700 calls); not refreshed"],
    ["Fraud detection flags", "Snapshot 2026-09-08 + transfer-workflow correction 2026-10-01", "Same-user flags corrected to exclude the designed receiving step"],
    ["Demand forecast, rebalancing, ABC x XYZ", "Built 2026-10-01 on the snapshot extract plus live monthly Dispense", "Rebuild after the next full extract"],
    ["Cycle-count variance", "Live pull 2026-09-22", "Not re-pulled"],
]
r = table(ws, 4, ["Dataset", "Basis", "Note"], rows, None, [58, 58, 70], filt=False)
r = section(ws, r, "Tie-outs")
r = kv(ws, r, [("Purchase lines (posted) 2026, gross", 3099), ("Purchase returns lines / documents", f"{RB['returns_lines']} / {RB['returns_docs']}"), ("Purchases gross (SAR)", RB["spend_gross"]), ("Purchases returned (SAR)", RB["returns_value"]), ("Purchases net of returns (SAR)", RB["spend_net"]), ("Purchase invoices (posted)", 506), ("Last posted purchase date", "2026-09-29"), ("Live non-zero stock lines", T["sku_live"]),
               ("Stock lines costed by estimate (new products)", T["est_lines"])])
wb.move_sheet("Data Status", offset=0)
from openpyxl.workbook.properties import CalcProperties
wb.calculation = CalcProperties(fullCalcOnLoad=True)
wb.save(OUT)
print("saved", OUT, wb.sheetnames)
