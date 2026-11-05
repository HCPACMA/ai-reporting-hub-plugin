---
name: "cfo-cure-hanygameel"
description: "Build, refresh or extend Hany Gameel's CFO Modeling Desk for any EXSYS (Cure) ERP company: audit tabs, VAT reconciliation, anomaly detection, SARIMA forecasting, service costing, IFRS 18 P&L, cash-flow auditing and revenue/department/cost/net-income driver analysis (YoY, MoM), all pulled from the branch databases via Cure MCP (no Power BI), with a fast incremental refresh."
---

# CFO-Cure (Hany Gameel)

A reusable kit that rebuilds the Al Faihaa CFO Modeling Desk from an EXSYS (Cure) healthcare-ERP database. Everything is pulled live through the **Cure MCP** (`cure_run_query`, SELECT only) from all four branch databases. **Power BI is not used at all** — not as a source, not for definitions, not as a tie-out.

Features:
- time-intelligence dashboard
- Arabic board report with audio scripts (the player sits at the top, above the written sections)
- Accounting Audit: terminated-staff balances, control accounts, unattached entries, VAT audit, VAT return ↔ trial balance reconciliation, invoice anomalies, expense anomalies
- Forecasting: SARIMA cash/credit revenue with a forecast-vs-actual variance ledger
- Costing: warehouse cost per service from the company's costing map, profitability by customer group / doctor / service, loss makers and a discount ceiling
- Statements: an **IFRS 18 statement of profit or loss** built from account-level GL detail — the five categories, both mandated subtotals, expenses by nature, the IFRS 18.83 specified-expenses note and a full MPM note
- **Cash-flow statement auditing**: pairing every balance-sheet movement against the cash-flow lines that represent it, until closing cash ties to the balance sheet without a plug
- **Deep Analysis drivers**: revenue (price–volume–mix on visits), department, cost (by nature and by function) and net income — waterfalls, treemaps, decomposition trees, heatmaps, YoY and previous-period, open month shown as partial with like-for-like days
- **Fast incremental refresh** (`refresh/refresh.py`): closed periods cached, light jobs in parallel per branch, heavy tests weekly, one build/validate/patch command

## Where the kit lives

- **Finance PC:** `D:\Financial Management\Financial Report\AI Reporting HUB\CFO-Cure-Kit\`, with these subfolders:
  - `SPEC.md`: the full specification. Read it first for any build or extension.
  - `sql/`: SQL templates using the placeholders `{P}` (schema prefix), `{D0}`, `{D1}`.
  - `scripts/`: payload builders, SQL generators, the SARIMA model and the result parsers `pk.py` / `parse.py` / `unpack.py` / `lastres.py`.
  - `refresh/`: `refresh.py` and its runbook — the only way to refresh the desk.
  - `scripts/drv/`: the driver SQL generator and payload builder; `DRIVERS.md` is the feature note.
  - `templates/`: the UI modules (JS/CSS); `ModelingDesk_current.html` is the reference page and wins over any module file.
- **Project "AI Reporting HUB":** `claude/cfo-cure-kit-spec.md` (a copy of SPEC.md) plus the feature docs `claude/modeling-desk-*.md`. If the kit folder is missing, rebuild it from these.

## Workflow

1. **Discover the company.**
   - Run `cure_branch_status` to get the branch parameter values.
   - For each branch, test whether it needs the `EXSYS.` prefix.
   - Confirm the account map: VAT 1263000 / 21230071 / 21230072, advance revenue 2123001, revenue 4x, other revenue 43x, expenses `ACCOUNT_TYPE='Expenses'`. If the chart of accounts differs, remap it in SPEC §3 first.
2. **Pull the data.**
   - Fill in the SQL templates for each branch.
   - Chunk the date range so each call stays under the 60 s device limit (a timeout blocks the MCP for about 2–3 min).
   - The MCP returns **at most 200 rows** and `LISTAGG` caps one cell at 4,000 characters — so pack ~70 rows per bucket, which allows ~14,000 packed rows per call, and split the date range when a branch exceeds that. A truncated result looks exactly like a complete one, so always count the months that came back before using it.
   - Parse outputs with `scripts/parse.py` / `scripts/unpack.py` (large results are saved to a file) or `scripts/lastres.py` (from the session transcript). Never re-type numbers.
3. **Tie out before building.**
   - Tie database to database: invoice revenue ↔ GL sales by month, the ledger rebuild ↔ every published closed year, cash flow ↔ balance-sheet cash.
   - VAT boxes must match the VAT_FORM screen.
   - TB movements must match GLTRIAL.
   - A restated statement must tie to the audited financial statements on **every** subtotal it claims, not just one. A single matching line is often the wrong line matching by accident — that is exactly how a double-counted Zakat charge went unnoticed.
   - Record the tie figures in SPEC.
4. **Build.**
   - Run the payload builder, embed the output as `DATA.<name>`, and add the module from `templates/`.
   - Follow the build pattern in SPEC §1. Load the `artifact-design` skill before editing the page.
   - A payload over ~1 MB of text goes columnar (all of column 1, then column 2 …) in base36, gzipped and base64'd, inflated with `DecompressionStream`; columnar beats row-wise packing by about a quarter.
   - Render-test with Playwright, then republish to the **same artifact URL**. After a context compaction that URL is no longer in memory — list the artifacts and read the right one first, or a duplicate gets created.
5. **Refresh (every time the figures are asked for — SPEC §12).**
   - `python3 refresh.py plan` (`--weekly` once a week). Ledger jobs read only from 1 Jan of the open year (prior year too until 31 March); invoice jobs from the 1st of the previous month. Never re-read closed periods.
   - Batch A: send the four branch SQL files of a job at the same time. Batch B (weekly, heavy window queries): one call at a time; after a timeout wait 3 minutes, then shorten the date range.
   - `ingest <job> <br> --file|--marker` after each result, `status` until complete, then `build` — it merges, rebuilds every payload, runs the gates (balance sheet balances, closed years unchanged, every doctor named) and patches the HTML. Date stamps move only after a complete batch A.
   - Re-read the Anomalies & Risks flags after a build: they describe the previous read.
   - `gl_mon` is the single ledger pull behind both `DATA.m` and `DATA.drv`; the build fails if any month before the window moved.
   - Recommend to the owner an export tool in the Cure MCP (`cure_export_query` → CSV in the connected folder) so results skip the 200-row cap and the chat entirely; credentials stay inside the MCP.
6. **Forecast (monthly).**
   - Rebuild `monthly_invoice_revenue.csv`.
   - Run `python sarima_forecast.py <folder>` on the PC in the background (Start-Process, then poll `run.log`; a first run takes about 45 min).
   - Run `build_fc_payload.py`, then republish.
   - Never edit or delete rows in `forecast_ledger.csv`.
7. **Cost and price (SPEC §7).**
   - The costing map is the company's own spreadsheet. Never infer its formula from the numbers — confirm it with the owner, then write the confirmed rule into SPEC.
   - Refresh item cost from the last `IM_STOCK_DISPENSING` movement. `PRODUCT_AVERAGE_COST` is 0 throughout this ERP, and a cost price of 0 means "never dispensed", not "free".
   - Exclude the `CONTRACT_TYPE='R'` + `BILL_TO='P'` patient-share mirror lines from quantity, or every credit service is costed twice. Keep `BILL_TO='G'` gratis lines — cost with no revenue.
   - Mark a service whose map has any broken line as **partial**: its cost is understated, never overstated. Keep it out of margin totals but keep it in the loss list, because an understated cost that already shows a loss is a loss for certain.
8. **Restate under IFRS 18 (SPEC §8).**
   - Build against EY's *Good Group (International) Limited — IFRS 18* illustrative statements: the statement is p.12, the commentary p.13, the specified-expenses note 13.5, the MPM note 16, the by-nature statement Appendix 2. Reading the illustrative statement first is worth more than reading the standard.
   - Build from **account-level** detail, never from the desk's aggregate buckets. Every item the standard forces out of operating — Zakat, interest on employee-benefit obligations, losses on disposal, an annual customer-rebate true-up — hides inside one bucket called "Provisions" or "Other operating expenses".
   - Zakat is the trap. It sits inside the provisions bucket, so charging that bucket **and** deducting the audited Zakat again takes it twice, and mislabels net profit as "profit before Zakat" — which makes the error look like a clean tie-out.
   - Cash and cash equivalents are **investing** (IFRS 18.53(b)). Interest on liabilities that are not purely finance-raising, such as end-of-service obligations, is **financing** (18.61(a)). Disposal gains and losses must sit in the same category as each other (18.44, B60).
   - Present expenses by nature. A residual labelled "other" worth a fifth of revenue is a failed disaggregation (18.B79), not a line item.
   - Carry the required notes: the IFRS 18.83 specified-expenses note with nil items stated as nil *and the reason*; nil lines for IFRS 9 impairment, associates and discontinued operations; and an MPM note giving the tax effect and NCI effect of every reconciling item, plus the statement that the measure is actually used in public communications — without that, it is not an MPM.
9. **Audit a cash flow statement (SPEC §10).**
   - First, sum the movement in every non-cash balance-sheet line and compare it with the movement in cash. If they match, the balance sheet is complete and any break is in the statement, not the data. Run this before anything else; it decides where to look.
   - Then pair each balance-sheet line with the cash-flow line(s) that represent it. Whatever is left names the defect.
   - A statement that needs a plug line to close is hiding the finding, not reporting it.
10. **Explain movements (SPEC §13).**
   - Revenue: price–volume–mix over branch × payment × specialty with visits (distinct file + episode) as volume; the components must sum exactly to the change.
   - Always show the invoice → ledger bridge: the Riyadh ledger debits revenue monthly with medicine cost (journal "ادوية عن شهر"), so the two revenue figures can move in opposite directions.
   - Open month: compare the same number of days; show "—" for ratios while ledger revenue is not yet posted.
   - Every bridge must close (start + steps = end) and nature total must equal function total before publishing.
11. **Record.**
   - Update the matching project doc.

## Rules

- Take data only from the four databases via the Cure MCP. Never from Power BI, never typed from screenshots.
- Use posted + open vouchers (STATUS P/O) in every figure, including the monthly series — never closed-period-only or posted-only. Exclude cancelled vouchers, the year-end closing JV (`%قفال الحسابات الختامية%`) and the monthly VAT closing JV (`%اقفال ضريبة%`). Without those exclusions every account nets to zero over a closed year, which reads as empty data rather than a missing filter.
- SQL must start with SELECT; the Cure MCP rejects WITH. Use inline views instead.
- Treat the branch as a dimension. Every tab honours the global period / branch / last-year comparison.
- Never store patient names, only file numbers. Never handle database credentials.
- A red flag or a forecast variance is a reason to look, not a finding. Label it that way.
- Name every limit on the page itself — the dimension that was too large to carry, the grain that was coarsened, the cost that covers only part of the picture. A number whose limits are hidden gets used as if it had none.
- When a restatement moves a number, put the bridge from the figure people already know to the new one on the same screen. A restatement nobody can trace back is a restatement nobody adopts.
- RTL sections: set `dir="rtl"` on the section element, force the global period strip (`.ps`) back to `ltr`, keep numeric cells at `direction:ltr`, and wrap any Latin numeral or standard reference sitting inside an Arabic sentence in `<bdi>`. Otherwise minus and percent signs jump to the wrong end, and a sentence ending in a Latin numeral has that numeral move to its front.

## Keeping this skill current

Whenever a feature is added to the Modeling Desk, extend the kit in the same turn:

1. Add its SQL, script and template files to the kit folder.
2. Add a section to `SPEC.md` and to the project copy.
3. Propose an improvement to this skill: read the current SKILL.md, add the feature to the description and the feature list, and propose the full updated file.