# Hiring and turnover analysis (Movement / analysis screen)

Screen: Hiring and leavers > Hiring and turnover analysis. Filters: period, branch, job family, nationality. KPIs, a monthly chart and three bar charts (branch, job family, nationality), plus a coloured Excel download (summary, monthly, by branch, by job, by nationality).

Refresh:
1. `render_sql.py` fills `sql/hr29_movement_events.sql` (hires and leavers by month, branch, job, nationality; page with RN windows of 190 rows) and `sql/hr30_active_by_dims.sql` (active staff by the same dimensions). Save the reply lines to `raw/hr29_movement_events.txt` and `raw/hr30_active_dims.txt` (one `|`-separated line per row, without the table borders).
2. `python3 scripts/movement.py --config config/company.<co>.json --extract data/extract.<co>.<date>.json --events raw/hr29_movement_events.txt --active raw/hr30_active_dims.txt --asof <YYYY-MM-DD> --labels config/labels_ar.json --out data/movement.json`
3. `build_hr.py` picks `data/movement.json` up automatically. The gate compares hires and leavers per month with the monthly series (one rehire of difference is tolerated).

Rules: leavers = last paid month in the period and no active current contract today; hires = first contract start; branch = cost-centre prefix of the current job; job family = first keyword match in `config/company.<co>.json > movement.job_families`; nationality names from CODES_MASTER type 105 (`movement.nationalities`, `nat_merge` joins duplicate codes). Average staff is built back from today's active headcount, so rates are estimates (transfers and rehires are not tracked). Turnover is yellow from 25 percent and red from 40 percent a year.
