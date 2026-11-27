# Inventory Analysis & Audit — Al Faihaa Group (live rebuild)

Built 2026-09-17, following `../README.md`'s "Redeploying at a new site" section and the
`ai-reporting-by-hanygameel` skill's playbook. Sourced from `Riyadh_Inventory_Data_2026.xlsx`
(pulled live via Cure MCP on 2026-09-09 — despite the filename, that pull covers **all 4
branches**, not Riyadh only; see the Scope finding below) plus this folder's own build scripts —
no live Cure MCP purchase/adjustment queries were needed, the existing extract already carried
purchase-line supplier/discount/UOM detail.

## Files

| File | What it is |
|---|---|
| `build_alfaihaa_inventory.py` | Phase 1: loads `Riyadh_Inventory_Data_2026.xlsx`, single-pass aggregates the Transactions sheet (cost basis, 6-month consumption, last-dispense date, receiving stats, purchase lines), writes `_state.pkl`. |
| `build_alfaihaa_inventory_2.py` | Phase 2: consumes `_state.pkl` + the Batches sheet, computes the 7 standing checks + supplier price matrix, writes `alfaihaa_inventory_audit.json`. |
| `alfaihaa_inventory_audit.json` | The computed audit data (~1.1MB) — source of truth for both deliverables below. |
| `alfaihaa-inventory-audit.html` | Source of the published interactive dashboard (also published as a Claude Artifact — ask for the link if it's not at hand). |
| `Alfaihaa_Inventory_Audit_Full_Data.xlsx` | Workbook: Summary (live formulas) + Methodology + 9 data tabs. |

**To refresh**: re-pull `Riyadh_Inventory_Data_2026.xlsx` (or a fresher equivalent) via Cure MCP,
then re-run both `build_alfaihaa_inventory*.py` scripts in order, then re-run the xlsx builder
(`build_xlsx.py` + `build_xlsx_2.py` — currently only shipped in the session that built this;
recreate from this JSON's shape if not present) and re-publish the HTML.

## What differs from the original demo-entity build (`../Inventory_Analysis_Audit_Direct.md`)

- **Scope is 4 branches, not 1.** The original doc's site (a different demo entity) had only one
  department with any activity. This pull shows live dispensing/purchasing at all four Al Faihaa
  branches (Riyadh, Buraydah 1, Buraydah 2, Rafha) — which also means the cross-branch peer audit
  (tab 6) is now genuinely meaningful, not a placeholder.
- **Costing has no product-master fallback here.** `IM_PRODUCT_MASTER.PRODUCT_AVERAGE_COST` /
  `EXTERNAL_COST_PRICE` are ~100% NULL for this tenant (worse than the demo site). Valuation uses
  each (branch, store, product)'s most recent transaction unit cost instead — flagged per store
  as `unknown_cost_skus` where even that's missing, never assumed zero.
- **Batch/expiry tracking IS populated here** (1,447 batch rows with real expiry dates) — better
  than the demo site, where it was empty and required a receipt-date proxy. Expiry Risk in this
  build is exact, not a proxy.
- **No UOM-normalization or discount correction was needed** on the purchase data — this
  extract's `primary_unit_cost` is already expressed per primary unit and appears to already be
  net of the line's own discount (see the JSON's `meta.findings` for the full reasoning and the
  residual uncertainty flagged there — spot-check before quoting savings externally).
- **MIN/MAX config-default artifact reproduces exactly** — every balance row shares the same
  (1/2/3) default, same as the demo site. The real overstock number uses 6-month days-of-cover.
- 14 of 55,190 transaction rows were dropped as column-shift parser artifacts (same known Cure
  MCP ASCII-table quirk documented in `../../claude/riyadh-inventory-data-extract.md`).

See the JSON's `meta.findings` array (also rendered in the dashboard's "Methodology notes" panel
and the workbook's Methodology tab) for the complete, current list.
