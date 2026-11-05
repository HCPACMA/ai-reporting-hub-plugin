# Fast refresh — runbook

Folder layout expected under `CFO_ROOT` (default `/home/claude/work`): the page `AlFaihaa_Modeling_Desk.html`,
`gl/` (ledger caches + builders), `anomdb/` (invoice caches, `gen.py`, `gen2.py`, `build_anom_db.py`),
`expdb/` (expense caches, `build_exp_db.py`, `flags_R.sql`), `aud/` (audit SQL + `data_aud_db.json`),
and this kit. `scripts/sql_invoice_aggregates.py` = `anomdb/gen.py`, `scripts/sql_invoice_exceptions.py` = `anomdb/gen2.py`.

1. `python3 refresh.py plan` (add `--weekly` once a week for the heavy line tests).
2. Batch A: for each job, send the four branch SQL files to `cure_run_query` at the same time.
3. After each result: `python3 refresh.py ingest <job> <01|02|03|04> --file <result file>` (big results) or
   `--marker "<a unique piece of the result>"` (small results, read from the session transcript).
4. `python3 refresh.py status` until nothing is missing, then `python3 refresh.py build`.
5. Read `runs/<id>/build.md` (gates + reminders), render-test, republish the same artifact URL.

Batch B (weekly) jobs run one at a time. If a call times out, wait 3 minutes and run it again for a
shorter date range — never retry immediately, the device stays blocked.

Windows: ledger jobs from 1 Jan of the open year (prior year too until 31 March); invoice jobs from the
1st of the previous month. Closed periods are never re-read.

Deep Analysis drivers and the monthly series (added 25 Sep 2026): batch A now also carries
`gl_mon` (account × cc prefix × function × month, posted + open — the source of both `DATA.m` and
`DATA.drv`), `cc_mon` (department revenue and cost) and `inv_vis` (visits and invoice revenue by
doctor/specialty). `build` rebuilds `DATA.drv` (`drv/build_drv.py`, open month = the day before the run)
and `DATA.m` (`scripts/build_monthly_buckets.py --closed=<window start>`), and fails the gate if any month
before the window moved.
