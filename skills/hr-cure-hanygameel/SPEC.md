# HR-Cure Kit: specification

Rebuilds the **HR Command Center** (animated dashboards, deep-analysis tabs, an audit register and a workforce plan) for any company that runs the EXSYS (Cure) ERP on Oracle. Every number comes from the company database through the **Cure MCP** (`cure_run_query`, read-only SELECT). Power BI is not used. It is the HR sibling of `CFO-Cure-Kit` and follows the same conventions.

Reference build: Al Faihaa Group, data as of 12 Oct 2026 (`docs/BASELINE_ALFAIHAA_2026-10-12.md`).

## 1. Principles

1. **Read-only.** Nothing is written to Cure. Staff numbers appear only in the letter-review workbooks, never in the dashboard extract, which holds aggregates.
2. **Every figure ties.** Each SQL job names its tie-out in its header and `build_hr.py` runs gates (branch headcount equals active staff, age and tenure bands sum to headcount, last-month item mix equals the month totals, identity buckets sum to headcount). A build that fails a gate exits with code 2 and publishes nothing.
3. **State what is not known.** Where the system cannot answer (leaver date, leave type names, installment status meaning) the page says so and the kit lists it as an open question.
4. **Flags carry evidence and an action.** A finding without the Cure evidence and a named owner is not published.
5. **No flag from a guess.** Four of the first sixteen flags in the first build were wrong because a query defaulted a null to a bad value. See section 8 and keep that list current.

## 2. Environment

| Item | Rule |
|---|---|
| Connection | `cure_branch_status` lists branch parameters. Payroll and HR live in one database (head-office branch, `cure.hr_branch_param`). Other branch databases hold no payroll rows |
| Schema prefix | The non-owner branch needs `EXSYS.` (`{P}`) |
| Row limit | About 200 rows per result. All HR jobs return fewer than 100 rows |
| Text rejected by the tool | Any SQL containing `UPDATE`, `CREATE`, `TRUNCATE` or `WITH` (no leading CTE, use inline views; never select `CREATED_BY`). `render_sql.py` checks this |
| Result shape | ASCII table with an extra `_branch` column. Numbers print as `420.0`, codes as text (`00`, `09`). `ingest.py` keeps every cell as text and converts only where a number is needed |
| Timeouts | The device bridge limit is about 60 s. Every HR job is a grouped query that runs in seconds. After a timeout wait 3 minutes before retrying |

## 3. Definitions

| Term | Definition |
|---|---|
| Active staff | `PS_STAFF_CONTRACT.STATUS='A' AND CURRENT_CONTRACT='Y'` |
| Branch | First two characters of `PS_STAFF_INTERNAL_TRANSFERS.ORGANIZATION_NO` of the current job (`CURRENT_JOB='Y'`): 00 HQ, 01 Riyadh, 02 BUR1, 03 BUR2, 04 Rafha at Al Faihaa |
| Salary package | Basic from `PR_STAFF_DEFAULT_SALARY_M` (open record, `DATE_END IS NULL`) plus the fixed items of `_D` for the same `DATE_START` |
| Gross pay (month) | `PR_SALARY_TRANSACTION_M.BASIC_SALARY` plus the `+` items of `PR_SALARY_TRANSACTION_D`. The detail table holds allowances and deductions only |
| Deductions (month) | The `-` items of `_D` (loans, other, shortage, bank fees) |
| Draft month | The latest payroll month in which every row is not posted. It is left out of trends |
| Hire | First contract start (`MIN(START_DATE)` per staff). `DATE_START_SERVICE` is blank at Al Faihaa |
| Leaver | Staff without an active current contract, bucketed by their last payroll month (`SEPARATED_DATE` is rarely filled) |
| Turnover | Leavers in the last 12 months divided by the average staff paid in those months |
| Open-ended contract | Active contract with `END_DATE IS NULL`. Not expired |
| End-of-service estimate | Half a month per year for the first 5 years, then a full month per year, on basic (A) and on basic plus housing and transport (B), as if all active staff left on the as-of date |
| Loan installment status | P paid, R rescheduled (replaced by later installments), N pending. Only N is owed |
| Leave status (`POST_FLAG`) | P posted, C cancelled, O open and not posted |
| GL balances | `GL_TRANSACTIONS_DETAILS.STATUS='P'` only. Net = DR_AMOUNT minus CR_AMOUNT, a credit is negative |

## 4. Data jobs

Each job is one file in `sql/`. Fill placeholders with `scripts/render_sql.py`, run, save the reply as `raw/<job>.txt`.

| Job | Returns | Tie-out |
|---|---|---|
| hr01a / hr01b | Staff, women, Saudi by branch; salary package by branch and Saudi / non-Saudi | Sum of staff equals active staff; salary roll 2,332,560 at Al Faihaa |
| hr02 | Top 12 job families with average package | Job titles from `CODES_MASTER` type 250 |
| hr03 / hr04 | Age decades; completed years of service | Sum equals active staff (missing birth dates shown as a band) |
| hr05a / hr05b | Payroll header and item totals per month | Gross for the last month equals header basic plus `+` items |
| hr06 | Item mix of the last closed month | Per sign equals the month totals of hr05b |
| hr07 / hr08 | Hires and leavers per month | Hires per month sum to first contracts in the window |
| hr09 / hr10 | Contract end months; contract status matrix | `BLANK` rows are open-ended contracts |
| hr11 | Residence documents and passports, expiry buckets | Residence buckets sum to active staff |
| hr12 | Blank-field counts | `active` equals active staff |
| hr13 / hr14 | Leave by type, status, year; open leave | Open leave count equals `POST_FLAG='O'` rows |
| hr15 | Loan installments by status, active vs leavers | Counts per status add to installment rows of posted loans |
| hr16 | Posted GL balances of EOSB, leave provision and payables | Matches the GL trial balance of those accounts |
| hr17 | End-of-service estimate | Years sum is reported for review |

## 5. Page specification

Single self-contained HTML page. All data sits in one JSON block (`<script id="hr-data">`); nothing is fetched. Light and dark tokens, no horizontal scroll, reduced-motion respected.

**Shell.** The page fills the window (`100dvh`): a left sidebar with groups and sub tabs, and a scrolling main area. Cards and charts reflow with `auto-fit` grids and scale with the window. Under 900 px the sidebar becomes a drawer opened from a menu button. The sidebar stays on the left in every language.

**Languages.** Three modes, switched from the sidebar and remembered in the browser: Arabic (RTL), English (LTR) and both (Arabic first, English under it). The main area and the sidebar text flip direction; charts stay left-to-right. All fixed text comes from one dictionary in the template (`d(key, English, Arabic)`); all generated text (findings, notes, playbook) is produced by `build_hr.py` as `{en, ar}` pairs; labels that come from Cure data (job names, items, bands) are translated through `config/labels_ar.json` and shown as they are when no translation exists. A finding without Arabic text fails the build gate.

| Group / page | Content |
|---|---|
| Overview | KPI strip with count-up numbers (includes open payroll notes), headcount line, hires and leavers columns, flag donut, top three actions, this month's high and medium payroll notes |
| Workforce / Summary and branches | Branch table, job families |
| Workforce / People profile | Age bands, years of service, Saudi share |
| Payroll / Cost and controls | Gross and deductions, absence and overtime, GOSI |
| Payroll / Earnings and deductions | Last-month item mix |
| Payroll notes / Monthly notes | The notes register: month selector, filters (status, priority, category, source, search), KPIs, note cards with close and reopen, add-note form, export. Carry-over rule below |
| Payroll notes / Letters review results | Results of each letters review (counts by outcome) and the standing review rules |
| Payroll notes / Later-dated letters | Tracker of deductions and entitlements that fall in a coming payroll |
| Payroll notes / Filipino loans | Loan-screen check for work-start letters |
| Hiring and leavers | Net movement, contract end wave, notes on spikes |
| Leave | Days by type and year, records by status |
| Loans and liabilities | EOSB provision against recomputation, installments by status |
| Audit / Audit register | Findings with severity filter, evidence, action, owner |
| Audit / Data quality | Missing-field bars, identity document buckets |
| HR plan / Workforce projection | Headcount and cost projection with sliders |
| HR plan / Calendar and checklist | Calendar and checklist (ticks kept in the browser) |
| HR plan / Best practice and targets | Best-practice cards, KPI targets |

Motion: counters count up, bars grow, lines draw, columns rise, donuts fill, all re-played when a page opens.

### Payroll notes register

Source file: `data/payroll_notes.json` (built from the Excel letters reviews, one note per item, English and Arabic). Fields: `id`, `month` (YYYY-MM the note belongs to), `src`, `cat`, `pri` (H, M, L, I), `emp`, `amt`, `t` title, `d` detail, `x` action, `owner`, `status`, `closedIn`.

Carry-over rule, identical in the page and in `scripts/notes_tool.py`: a note shows in its own month (state new) and in every later month (state carried) until it is closed. A note closed in month M shows as closed in M and is gone from M+1. Status `info` is shown only in its own month and never carried. The month list runs from the first note month to the current payroll month plus a preview of the next month, so the new month always opens with what is still pending from the last one.

Changes made in the page (close, reopen, add) are kept in the viewer's browser only. The page's export box gives a JSON that `notes_tool.py apply` merges into the file; rebuild and republish so everyone sees it. Each build checks the file (unique ids, known category and source, English and Arabic text, closed notes carry a month).

## 6. Audit rules

Thresholds are in `config/company.<co>.json` under `thresholds`. A rule that finds nothing publishes nothing.

| Finding | Severity | Test |
|---|---|---|
| Expired contract | High | Active, current, `END_DATE` in the past |
| Open-ended contracts | Low | Active, current, `END_DATE` blank |
| Residence document dates not maintained | High | (expired + no date) above 5 percent of active staff; otherwise Medium for expired only |
| Open payroll rows in closed months | Medium | Header `STATUS<>'P'` outside the draft month |
| Pending loan installments on leavers | Medium | Status N on staff who are no longer active |
| EOSB provision vs recomputation | Medium | GL gap above 5 percent of the estimate on basic |
| Licence and probation blank | Medium | Any active staff with blank `LICENSE_ID` or `TEST_PERIOD_DAYS` |
| Service start date blank | Medium | `DATE_START_SERVICE` blank |
| Other master fields incomplete | Medium | GOSI date, email, birth date, nationality, ID record |
| Open leave records | Medium | `POST_FLAG='O'` |
| High leave cancellation | Medium | Cancelled share of long leaves above 10 percent |
| Absence deduction spikes | Medium | Month above 2.5 times the median |
| Hiring spike | Medium | Month at least mean plus 2 sigma and 2 times the mean |
| Saudization | Low | Saudi share below 50 percent, listed by branch |
| Overtime swing | Low | Maximum above 4 times the minimum |
| Turnover | Low or Medium | 15 percent or more; Medium at 30 percent |

## 7. Build pipeline and acceptance

`render_sql.py` -> run jobs -> `ingest.py` -> (update `data/payroll_notes.json` with `notes_tool.py`) -> `build_hr.py` -> `tests/run_tests.py` -> publish. Acceptance for a build: all gates pass, `tests/make_fixtures.py` plus `ingest.py` reproduces the extract exactly (round trip), the page opens on desktop and phone width in both themes and all three languages with no console error other than a blocked font (`tests/run_tests.py` clicks all 17 pages in the three languages when playwright is installed), and each headline figure is re-queried once by hand against Cure.

## 8. Traps found while building (keep adding)

1. **Null defaulting to PAST.** A `CASE ... ELSE 'PAST'` counted 15 open-ended contracts (blank end date) as expired. Test `IS NULL` first (`hr10`).
2. **Maximum over all document types.** A valid passport hid an expired iqama. Keep residence documents and passports in separate groups (`hr11`).
3. **Loan status R.** It means rescheduled, not uncollected. Counting R inflated the loan exposure from 18.7k to 604k on leavers.
4. **Basic salary is not in the item table.** `PR_SALARY_TRANSACTION_D` has allowances only; gross needs the header.
5. **Codes parsed as numbers.** `00` became `0.0` and `09` became `9.0`. Keep result cells as text.
6. **Incomplete extract by hand.** Two open payroll months were left out of a hand-typed extract; ingest from the raw replies instead.
7. **GL balances need `STATUS='P'`.** Open rows (O) distort them.
8. **Flags built on a stale field.** All 385 active staff carry `ID_CURRENT <> 'Y'` for most documents. Never filter on that flag.

9. **Sidebar and RTL.** Putting `dir=rtl` on the grid moved the sidebar to the right. The grid stays `direction:ltr` and `dir` is set on the sidebar and main area separately, so the sidebar is on the left in Arabic too.
10. **Bidirectional text in charts.** Axis labels with Arabic month names keep the chart in a left-to-right box; only legends and tables follow the page direction.

## 9. Limits

Leave type names are Cure codes (name them in `leave_labels` and `leave_labels_ar`). The page shows Arabic for Cure data labels only when they are in `config/labels_ar.json`. Leavers use the last payroll month, so a leaver whose last paid month is the current closed month is counted in it. The end-of-service estimate ignores resignation reductions and contract-type rules. Branch shares come from the current job only. The dashboard shows aggregates, not individual staff.

## 10. Extending

Add SQL in `sql/hrNN_*.sql` with a header naming the tie-out, add its parser block to `ingest.py`, its rule to `build_hr.py`, its section to the template, a gate if it can tie to another figure, and a line here. Then update `SKILL.md`.
