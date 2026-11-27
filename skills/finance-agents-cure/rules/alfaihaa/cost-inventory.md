# Cost & inventory rules (Al Faihaa)

- All warehouses run on the Riyadh database for every branch: item cost is single-sourced from Riyadh. Service codes are unified across branches.
- Costing Map links lab / dressing services to stock items. A lab line with no test count = one test per service.
- Stock item codes sometimes have a leading 0: look up both forms; keep codes as text in Excel.
- A service sold whose linked items were not dispensed for over 2 months is flagged as possibly needing an item update.
- Slow-moving needs ~3 months of consumption history; recently first-bought items are excluded.
- A purchase invoice with a purchase return is excluded from price-difference, savings and supplier-price analyses.
- Review stock-valuation errors such as cost jumps after the balance hits zero.

## Added after the 2026-10 run
- Costing-map lines with no test count are a DATA GAP: list them for the accountant and exclude them from cost-vs-price comparisons (pending the owner's decision on the "one test per service" default).
- Split "cost ≥ price" services into data gaps / free or package services / real pricing cases, with a reason column.
- Item average cost is empty in Cure; use last-issue cost from status-T movements.
- A price jump is measured against the previous normal invoice; flag the anomalous invoice itself, and check for unit-of-measure errors (carton vs piece).
