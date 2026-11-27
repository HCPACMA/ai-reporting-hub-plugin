# Al Faihaa Inventory Audit — Refresh Runbook (Version 27, 6 Oct 2026)

Dashboard (private Artifact): https://claude.ai/artifact/RaDyJGR7djUZyCLMA9SS5Y  ·  Excel: `Inventory\Alfaihaa_Inventory_Audit_Full_Data.xlsx`
Methodology and history: project doc `claude/alfaihaa-inventory-audit.md`; full re-extract recipe: `claude/cfo-cure-kit-spec.md` section 17.
This replaces the September runbook, whose 2,000-row paging assumption was wrong (the tool returns 200 rows per call).

## Rules that must not be broken
1. **Never run `refresh_dashboard_json.py`** - it swaps the whole embedded JSON and wipes the keys added after 23 Sep (`demand_forecast`, `rebalancing`, `abc_xyz`, `transfer_workflow`, `watchlist`, `price_changes`, `live_check`, `returns_review`, `scan_review`). Re-embed only the keys that were rebuilt (`apply_v27.py` shows how: parse `<script id="audit-data" type="application/json">`, replace keys, write back).
2. Restate capabilities on every publish: `{"downloads": {}, "sample": {}, "db": {}, "user": {"scopes": ["profile"]}}`. The db collections (`watchlist_status`, `returns_review`, `scan_review`, `fraud_feedback`) hold people's reviews - never delete or rewrite them.
3. If the device or Cure_MCP is unreachable, or a pull cannot be completed, stop and report; do not publish a partial or mixed rebuild.
4. Deliver the openpyxl-built workbook, never a LibreOffice re-save (it rewrites the scan hyperlinks). Excel recalculates on open.
5. The scheduled weekly task was paused on 2026-10-02 and has not been re-created (needs Hany's OK).

## Level A - quick refresh (about 12 calls: purchasing, returns, live stock)
PI lines (`IM_PRODUCTS_TRANSACTIONS`, T_TYPE = PI, STATUS = P) -> attachments (`EX_ATTACHMENTS`, TRANSACTION_TYPE = PI) -> purchase returns (`IM_PURCHASE_INVOICE_RETURN_M/_D`) -> `build_returns.py` -> set AS_OF in `watch/run_live.py` and `pc/build_pc.py` -> run both -> live stock (`VINV_STORE_PRODUCTS`, `ONHAND_QTY <> 0`) -> `build_live_check.py` -> re-embed `watchlist`, `price_changes`, `live_check`, purchasing blocks -> verify -> publish -> `build_xlsx_refresh.py`. First compare the posted PI set with the previous cut: if no purchase invoice was posted, say so instead of announcing changes.

## Level B - full re-extract of every tab (Version 27, about 40 calls for the tables plus about 15 for forecast / XYZ / transfers)
1. **Pull** the five tables with packed queries (`LISTAGG(s,'~') ... FLOOR((n-1)/K)`; K so a cell stays under 4,000 characters; 40+ groups or an `RPAD` pad per call so the result is saved to a file). Parse each file with `pk_parse.py <file> <name>` into `raw/`. Tie every table to `COUNT(*)`. Retry a failed range, never skip it.
2. `assemble.py` -> `Riyadh_Inventory_Data_2026.xlsx` (halves duplicated CRC lines; maps created_by through `created_by_map.json`; statuses P / C / O -> Posted / CANCEL / Open).
3. Core pipeline in `pipeline_run/Inventory/alfaihaa/`: `build_alfaihaa_inventory.py` -> `_2.py` (set the as-of text) -> fraud and ABC/vendor/cycle-count scripts -> `build_fraud_workflow.py`. Cycle-count adjustments (`IM_STOCK_ADJUSTMENTS_M/_D`, G / L): re-check for new rows.
4. Purchasing: Level A steps.
5. Forecast: `raw_series_v27.py` (monthly Dispense + Transfer-sent series, partial month dropped) -> `run_forecast_v27.py` -> `build_forecast_v27.py`. Rebalancing: `build_rebalance_v27.py`. XYZ: `build_xyz_v27.py` (Dispense only, 24 months, X <= 0.5, Y <= 1.0, default H = 3). Transfer workflow: `build_feedback_data_v27.py` (asserts the document count and 0 quantity mismatches; join `RCV_D.SEND_LINE_NO = SND_D.LINE_NO`, compare `SND_QTY` with `RCV_QTY`). Live check: `build_live_check_v27.py`.
6. `assemble_v27.py` -> `audit_v27.json`; `apply_v27.py` -> dashboard HTML (keep a `.pre_` backup); static texts (header date, "since the snapshot" cards) updated in the same script.
7. Verify: JSON parse, `node --check`, `verify_v27.py` (every tab on desktop and mobile, no JS errors), Board tab figures tie to the Overview.
8. Publish with the Artifact tool, same file path or the URL above; read the live artifact first if the tool asks.
9. Excel: `build_xlsx.py`, `build_xlsx_2.py`, `build_xlsx_board.py`, `build_xlsx_aging.py`, `build_xlsx_fraud.py`, `build_xlsx_abc_vendor_cyclecount.py` (work folder with `pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json` and `_state.pkl` beside them), then `build_xlsx_refresh.py <workbook> audit_v27.json <out.xlsx>`. Deliver with `SendUserFile`, commit to `Inventory\Alfaihaa_Inventory_Audit_Full_Data.xlsx` with `expectedMtimeMs`.
10. Sync the working files to `Inventory\alfaihaa\` (`Riyadh_Inventory_Data_2026.xlsx`, `alfaihaa_inventory_audit.json`, `_state.pkl`, `fraud_workflow.json`, `audit_v27.json`) and the scripts to `Inventory\alfaihaa\v27\`.
11. Update the project docs (`alfaihaa-inventory-audit.md`, `cfo-cure-kit-spec.md`, roadmap, extract doc) and report: stock value and change, KPI deltas per tab, what did not change and why (for example no new purchase postings), connection issues, open decisions.

## Query-tool limits
Only SELECT; text containing CREATE / UPDATE / TRUNCATE / WITH is rejected (use inline views, `STAFF_ID` instead of `CREATED_BY`); no `DISTINCT` in `LISTAGG`; no `JSON_OBJECT`; unfiltered full-table aggregates time out at about 60 s; a call can hit the 60 s bridge limit - retry the same range.

## Open decisions (Hany)
Weekly scheduled refresh (OK to create, keys-only re-embed) · lead time H for ABC x XYZ · mandatory reason on purchase returns · supplier item code and name on PI lines · attach the 187 early scans (3 Jan - 28 Mar) in the ERP · extend the AI scan read beyond 128 invoices.

## Cure skin (7 Nov 2026)
Before publishing, run `python3 "_theme/cure/apply_cure_skin.py" inv <dashboard.html>` (idempotent). Source: _theme/cure, snippet copy: alfaihaa/cure_skin.html.

## AI Inventory Department tab (21 Nov 2026)
The dashboard loads `inv-dept.js` (beside index.html, with `inv-office.html`) from one include `<!--INV-DEPT:start -->…<!--INV-DEPT:end -->` placed after `<!--CURE-SKIN:end -->`. Before republishing a local copy of the page, make sure that include is there, or the tab is dropped. The tab is built by `Inventory-Agents-Kit/scripts/build_inv_tab.py` (live + demo). Local copies: after every publish save the same files in `Inventory\alfaihaa\` (live) and `Inventory\` (demo), and run `Inventory-Agents-Kit/scripts/make_standalone.py <page>` so one copied file works on another computer.
