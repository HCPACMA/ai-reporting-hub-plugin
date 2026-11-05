# Modeling Desk — Deep Analysis drivers (revenue, department, cost, net income)

Added 25 Sep 2026 to the Deep Analysis section of the Modeling Desk artifact. Four tabs explain why a figure moved against the same period last year (YoY) or the previous equal-length period (MoM / QoQ). They all follow the global period, branch and comparison controls.

## Data (all four EXSYS databases via Cure MCP; no Power BI)
- **Ledger:** GL_TRANSACTIONS_DETAILS, posted **and open** vouchers (STATUS <> 'C'). Cancelled vouchers, year-end closing vouchers (FINANCIAL_YEARS.GL_VOUCHER_NO) and JV1-24/04043 are excluded. One row per account × cost-centre prefix × function × month, from Jan 2023 to the open month. The same pull now also rebuilds `DATA.m`, so the whole desk is on the posted + open basis.
- **Departments:** revenue (41x cash, 42x credit excluding 4200027) and expense DR/CR by full cost centre and month.
- **Invoices:** visits (distinct patient file + episode), net revenue, and net revenue excluding pharmacy, by branch × payment type × specialty × doctor × month. Only file numbers are held; there are no patient names.

## Owner decisions (24 Sep 2026)
- Open month: shown and marked partial. Revenue MoM compares the same number of days.
- Volume = visits (episodes).
- Revenue = invoices, plus a check against the ledger.
- Function rules unchanged: COR / GA / INS / HO / X.

## Tabs
- **Revenue driver:**
  - Tiles: invoice revenue, visits, revenue per visit, ledger revenue.
  - Price–volume–mix waterfall (exact).
  - Branch × payment waterfall.
  - Specialty treemap.
  - Tree: branch → payment → specialty → doctor.
  - Doctor movers.
  - Monthly revenue and visits trends.
  - Bridge table from invoice revenue to ledger revenue.
- **Department driver:** contribution waterfall, revenue treemap, movers, and a department table with margins. Margins are hidden for departments that are too small to be meaningful.
- **Cost driver:**
  - Toggle between nature and function.
  - Cost bridge and treemap.
  - Account movers.
  - Nature × function change matrix.
  - Nature → account drill tree.
  - Cost % of revenue trend.
- **Net income driver:**
  - NI bridge: revenue, other revenue, COR, GA, INS, HO, X, Zakat.
  - Month × driver heatmap against last year.
  - Decomposition tree.
  - Monthly NI trend.

## Findings (Jan–Aug 2026 vs Jan–Aug 2025)
- **Net income:** 5.26M vs 4.88M (+7.8 %). Net margin 14.4 % vs 12.9 %.
- **Ledger revenue:** −3.7 % (−1.4M).
- **Invoice revenue:** +3.1 %.
  - The gap is mostly the monthly Riyadh journal "ادوية عن شهر", which debits revenue with medicine cost. It grew from 8.00M to 10.07M.
- **Costs fell 1.9M:**
  - Losses on disposal −840K.
  - Medical supplies −758K.
  - Depreciation −291K.
  - Professional fees +270K (against the trend).
- **Sep 2026 (open, like-for-like days 1–24):**
  - Invoice revenue 5.05M vs 4.72M.
  - Volume +475K, price −197K, mix +62K.
  - September sales are not yet posted to the ledger, so ledger-based ratios show "—".

## Tie-outs
- **Ledger revenue:** 2024 56,638,027 · 2025 56,966,108 · 2026 YTD 36,186,337.
- **Net income:** 2024 −3,905,285 · 2025 1,775,238 · 2026 YTD 4,505,978.
- Nature total = function total.
- Every bridge closes exactly.
- `DATA.m` rebuilt on posted + open: every closed month reproduced (3 cells moved by SAR 1 from half-riyal rounding).

## Refresh
`kit/refresh/refresh.py` batch A now includes these jobs: `gl_mon`, `cc_mon` and `inv_vis`. `build` rebuilds `DATA.drv` and `DATA.m` and fails the gate if a closed month moves.

Files in the kit:
- `scripts/drv/` (gen.py, build_drv.py, patch.py)
- `scripts/anomdb_gen.py`
- `templates/drv.js`, `templates/drv.css`
- SPEC §8A (basis change) and §13 (drivers)
