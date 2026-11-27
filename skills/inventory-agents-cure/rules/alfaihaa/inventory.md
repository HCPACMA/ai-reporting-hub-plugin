# Inventory standing rules (Al Faihaa)

- All warehouses run on the Riyadh database for every branch; item cost is single-sourced from there. Service codes are unified across branches.
- Cancelled documents (status C) do not exist. Posted (P) and open (O) are reported separately.
- Slow-moving needs about 3 months of consumption history; items first bought recently are excluded.
- Any purchase invoice that has a purchase return is excluded from price-difference, savings and supplier-price analyses.
- Stock-valuation errors to review: cost jumps after the balance hits zero, zero-cost purchase lines, unit-of-measure errors (carton vs piece).
- Item codes can have a leading 0: look up both forms; keep codes as text in Excel.
- Every finding is provable: document no., item code, store, date, quantity and value.
- Read-only: never post, adjust, approve or transfer anything in EXSYS. Purchase or transfer proposals are drafts for people.
- The dashboard's own rules (REFRESH_RUNBOOK.md) stay in force: never run refresh_dashboard_json.py; restate capabilities on every publish; never delete the db review collections.
- Demo copies never carry the company name and never real numbers.
