# CFO-Cure Kit — specification

This is the reusable spec for rebuilding the Al Faihaa **Modeling Desk / CFO Command Center** for any company that runs the EXSYS (Cure) healthcare ERP on Oracle. Every number comes from the company database through the **Cure MCP** (`cure_run_query`, read-only SELECT). Power BI is not used at all — not as a source and not as a tie-out. Every check ties one database figure to another (invoices ↔ GL sales, ledger ↔ published closed years, cash flow ↔ balance-sheet cash).

## 0. Environment and conventions

| Item | Rule |
|---|---|
| Branch databases | One Oracle DB per branch. Branch parameter values come from `cure_branch_status`. The branch that is not the schema owner needs the `EXSYS.` prefix (`{P}`); the others need none |
| Cost centre / branch dimension | 00 HQ, 01…n are branches. Treat the branch as a dimension everywhere, together with the global filter |
| Posting status | `GL_TRANSACTIONS_DETAILS.STATUS`: P posted, O open (unposted), C cancelled. Use P+O; drop C |
| Entries to exclude | Year-end closing (`DESCRIPTION LIKE '%قفال الحسابات الختامية%'`) and the monthly VAT closing JV (`'%اقفال ضريبة%'`) |
| MCP limits | About 200 rows per result, so pack rows with `LISTAGG` or `a;b;c` strings. The device call limit is 60 s; a timeout blocks the MCP for about 2–3 min, so wait, then split the date range |
| Big results | Outputs over ~50k characters are saved to a file by the host; parse them with `scripts/parse.py`. Smaller outputs can be recovered from the session transcript with `scripts/lastres.py '<unique first-row prefix>' out.txt`, so nothing has to be re-typed |
| `WITH` clauses | The Cure MCP rejects SQL that doesn't start with `SELECT`, so use inline views |
| Local compute | The finance PC has Python + statsmodels + pandas. The cloud sandbox has no PyPI, so run modelling on the PC with Start-Process in the background and poll the log |
| Refresh | `refresh/refresh.py` — incremental, parallel per branch, one build/validate/patch command. See §12 |
| Privacy | Never store patient names, only file numbers. Staff names are fine in audit views |

## 1. Modeling Desk (single-file HTML artifact)

The shell is a sidebar with groups, a global **time-intelligence bar**, and sections registered in `SECTIONS` (`{id,label,icon,group}`), each rendering into `#sec-<id>`.

- **TI (`templates/ti.js`)**
  - Grains: M-to-M, Q-to-Q, Y-to-Y, and a date range.
  - Branch / cost-centre selector and a "compare with same period last year" switch.
  - The default window ends at the last closed month (an open month is detected automatically).
  - Modules subscribe with `TI.on(render)` and read `audWindow()` → `{a,b,c}` as yyyymm.
- **CFO Command Center:** Executive, P&L, Cash, Working Capital, Budget, Risks, Ask, and an Arabic **Board report** with Najdi and Egyptian audio scripts (`templates/board.js`).
- **Statements / Valuation / Strategy / Departments / Cost centres:** monthly GL buckets rebased from Oracle. See the project docs `modeling-desk-*`.
- **Build pattern:**
  - Payloads are embedded as `DATA.<name> = {...};` lines after `DATA.aud`.
  - CSS goes before `/* ===== Accounting Audit section ===== */`.
  - Module JS goes before the tail `renderStrips();\nactivate('cfo-exec');`.
  - Render-test with Playwright, then republish the same file path.

## 2. Accounting Audit group

| Tab | Source | Key rule |
|---|---|---|
| Terminated staff balances | Staff master (end-of-service date) + sub-ledger balances | Balance beyond ±1 after the termination date |
| Control accounts | Accounts that must be zero at month end | Month-end balance outside ±0.03 |
| Unattached entries | `ATTACH_FILE_PATH` empty, excluding FOR_SHIFT | Filters on entry user code/name, VM type, sub-system, and filters in the columns |
| VAT audit | GL revenue vs invoices, credit memos, VAT keyword lines | See §3 |
| Anomaly · Invoices | Invoice lines | See §4 |
| Anomaly · Expenses | Expense GL lines | See §5 |

## 3. VAT return ↔ trial balance reconciliation

- **Return (`sql/vat_return_monthly.sql`):** read from the MV, using the box formulas in the file.
- **TB (`sql/tb_movements_monthly.sql`):** exclusions as in §0.
- **Reconciliation:**
  - **Output VAT:** 21230071 (Cr − Dr) vs return VAT.
  - **Input VAT:** 1263000 (Dr − Cr) + 21230072 vs return input, less the prior-month VAT payment (21230072 debit).
  - **Sales:**
    - Start from TB revenue (4x).
    - Deduct 4300001–4300009 (net).
    - Add medicine cost reversed on revenue (JV `ادوية عن شهر`).
    - Add rent invoiced with VAT (4300003 credits in vouchers that also hit 21230071).
    - Add credit notes in revenue (CN+VCN) minus the return's CN.
    - Add the manual items (discount, advance revenue, inter-branch lab, other; saved per browser).
- **Filters:** year and month. A year is the sum of its months. A month where adjusted TB sales fall more than 10 % below the return is flagged "revenue not posted yet".
- **Check (Al Faihaa, July 2026):** output −16.68, input 0, adjusted sales 6,207,595.38, all identical to the finance workbook.

## 4. Invoice anomalies

- **Daily revenue flag (year-to-date control band):** a day outside mean ± 2σ of its year-to-date daily totals (expanding window from 1 January, population σ, blanks ignored). Pharmacy and Fridays are excluded by default.
  - Options: 2 / 2.5 / 3σ, and a rolling-90-day baseline.
  - Tie: Riyadh credit 2025 = 12,711,443 on both sides.
- **Doctors:** a month compared with the same doctor's earlier months, with at least 6 months of history, |z| ≥ k, and a gap ≥ 5,000.
- **Cashiers** (50+ lines). A cashier is flagged for any of:
  - cash discount % above max(2 × branch average, branch average + 10 points), on 5,000+ of cash gross
  - returns above 3 × the branch rate and 20+ returns
  - 20+ heavy discounts (discount ≥ 30 % of the line)
  - 20+ lines, and at least 5 % of the cashier's lines, billed between 00:00 and 06:00
- **Exception lines:**
  - Heavy cash discounts (credit excluded).
  - Returns.
  - After-hours lines.
  - Price outliers: unit gross > max(avg + 4σ, 3 × avg) per service × branch × payment type, 30+ lines.
  - Same service, same patient, same day in 2+ episodes.
  - Repeated discount beneficiaries.

## 5. Expense anomalies

- **Monthly spike (year-to-date control band):** the month's net vs the year's YTD mean ± kσ, from the 3rd month on.
- **Line tests** (`sql/expense_redflags.sql`), with score weights:

| Code | Weight | Test |
|---|---|---|
| RND | 1 | ≥ 1,000 and a multiple of 500 |
| WKD | 1 | Manual journal on a Friday |
| OUT | 3 | > avg + 3σ and > 3 × avg |
| DUP | 2 | Same account and amount, different voucher, within ±7 days |
| SLF | 1 | Entered and posted by the same user |
| NDS | 1 | No description |
| NAT | 1 | Manual journal ≥ 1,000 with no attachment |
| THR | 2 | Just under 5k / 10k / 20k / 50k |
| REV | 1 | Manual credit to an expense account |

- **Payroll-type accounts** (319xxxx, GOSI, board remuneration): RND / WKD / DUP / THR are shown but not scored.

## 6. Forecasting group (SARIMA)

1. **Pull:** run `sql/invoice_revenue_monthly.sql` per branch, from the first month of history to the current month, in chunks. Then build `monthly_invoice_revenue.csv` with columns `branch,ym,cash_np,cash_ph,credit_np,credit_ph,other,eps_cash,eps_credit,refund_cash,refund_credit,cash,credit`.
2. **Tie:** annual totals must match the daily invoice series of the anomaly tab (same tables) within 0.1 %. Al Faihaa 2025: 73,579,425 vs 73,580,303.
3. **Model:** `scripts/sarima_forecast.py <folder>` on the finance PC.
   - Series: branch × cash/credit plus group cash/credit/total.
   - Model: log SARIMAX with a Ramadan / Eid / Friday / COVID calendar.
   - Candidates ranked by AICc on T−12. The top 6 are re-scored by a rolling 12-month backtest (0.6 × 1-step MAPE + 0.4 × 3-step MAPE).
   - Bias correction when 5 of the last 6 errors share a sign and the mean error is > 2 %.
4. **Ledger:** `forecast_ledger.csv` is append-only; existing rows are never overwritten.
   - On the first run, reconstructed backtest vintages are written for the last 20 origins.
   - Each run appends a live vintage. `model_registry.json` records the chosen model per series.
5. **Payload:** `scripts/build_fc_payload.py <folder> data_fc.json`. Its justification splits variance into:
   - volume (visits × forecast rate)
   - rate (rate gap × actual visits)
   - calendar notes vs the same month last year
   - refunds above 1.3 × their 12-month average
6. **UI:** the *Revenue Forecast* tab has a chart with 80/95 bands, 1-step backtest dots and current month-to-date, plus a month table and a model card. The *Forecast vs Actual Audit* tab has a horizon selector (1/2/3/6/12), MAPE, bias, 80 % hit rate, total variance, a month table with the justification, and the model log.
7. **Monthly routine:**
   - After month close, re-pull the last 3 months (late postings and refunds).
   - Rebuild the CSV, re-run the model (this is the auto-enhance step), rebuild the payload, and republish.

## 7. Costing group (service cost and profitability)

Answers three questions for every service that consumes warehouse stock: what does it cost me, what do I
earn on it, and how big a discount can a manager give before the service is sold at a loss.

1. **The map.** The company keeps a spreadsheet (`ER & Lab Costing Map.xlsx`) linking each clinic service
   code to the stock items issued to deliver it, with a "service's share of the item" column and, for lab
   lines, the number of tests the pack yields. Normalise it with `scripts/costcalc.py`:
   - Item codes are zero-padded to 7 characters — that is the `PRODUCT_CODE` format.
   - Shares come as decimals (`0.02`) or text (`100%`).
2. **Refresh the cost** (`sql/item_cost_last_dispense.sql`): `IM_STOCK_DISPENSING_D.COST_PRICE` at the item's
   latest `IM_STOCK_DISPENSING_M.SDIS_DATE`. `IM_PRODUCT_MASTER.PRODUCT_AVERAGE_COST` is zero for every
   item at Al Faihaa, so the dispense cost is the only live source. A cost price of 0 is not a cost —
   treat it as "no dispense".
   *Tie-out:* item `0170680` = 173.70 on 2026-09-10, identical to the stale `Cost` column in the map file.
3. **Cost formula** (confirmed by the finance owner, not inferred):
   - Lab: `item cost ÷ (tests per pack × share)`, summed over the service's items.
   - Dressing / ER: `item cost × share`, summed — the share there is already a consumption fraction.
   - Guard: a *lab* line whose share is below 0.05 is a shared reagent measured as a consumption fraction
     (substrate, buffer), so it multiplies instead of dividing. Without this guard three serology tests
     price at 2,700–5,500 SAR each. Flag those lines for the owner rather than hiding the rule.
   - A service with any unusable line is **partial**: its cost is understated, never overstated. Keep it out
     of margin totals, but keep it in the loss list — a partial cost that already shows a loss is certain.
4. **Sales** (`sql/service_profit_grid.sql`), all branches, month grain. The two rules that decide whether
   the numbers are right are in the file header: exclude the `R`+`BILL_TO='P'` patient-share mirror lines
   from quantity, and keep `BILL_TO='G'` gratis lines (cost, no revenue).
   *Tie-out:* Riyadh 12 months to Sep 2026 — gross 14,312,385 vs 14,321,847 live, the gap being invoices
   raised after the extract on an open month.
5. **Payload** (`scripts/build_cost.py`): ~90k grid rows, dictionary-encoded in base36 and stored **columnar**
   (all of column 1, then column 2 …), gzipped and base64'd — 2.8 MB of text becomes 686 KB, about a quarter
   smaller than row-wise packing. `templates/cost.js` inflates it with `DecompressionStream` on load.
6. **UI** — three tabs, Arabic RTL (`dir="rtl"` on the section, `.ps` strip forced back to LTR):
   - *Service Cost*: old vs refreshed cost per service, expandable to the item lines, plus a
     "needs review" card counting the four kinds of broken map line.
   - *Service Profitability*: the full filter set (branch, customer group, payment type, service speciality,
     clinic speciality, doctor, service, from-month → to-month, cost completeness) and a grouping selector
     covering service / customer group / payment type / speciality / doctor / branch / month.
   - *Loss Makers & Discount Ceiling*: break-even discount = `1 − cost ÷ price`, actual discount beside it,
     and a drill-down by customer group for the selected service.
7. **Known limits, state them in the UI.** The customer dimension is the *customer group* (23 insurers /
   payers): `RC_CONTRACTS` opens one contract per insured member (29k in 12 months) so it is not a usable
   dimension. Period filtering is monthly. Cost covers direct consumables only — no labour or overhead.

*Al Faihaa, 12 months to Sep 2026:* 185 mapped services, 141 items, 129 fully costed. Revenue on fully
costed services 13.69M against 2.05M of item cost. Four services sell below item cost, the largest being
HCV antibody (003743): 5,289 tests at an average 2.41 SAR against a 21.44 SAR cost, −100,661 SAR.

## 8. IFRS 18 statement of profit or loss

IFRS 18 replaces IAS 1 for annual periods beginning on or after **1 January 2027** (early adoption
permitted, comparatives restated). It does not change profit; it changes where each line sits. Every
income and expense goes into one of **five** categories — operating, investing, financing, income
taxes, discontinued operations — and two subtotals become mandatory: **operating profit** and
**profit before financing and income taxes**.

**Benchmark.** Build and review against EY, *Good Group (International) Limited — Illustrative
consolidated financial statements under IFRS 18*, v2, May 2025. The statement itself is p.12, the
commentary p.13, other income/expense notes 13.1–13.4, the IFRS 18.83 specified-expenses note 13.5,
the MPM note 16, and the by-nature statement Appendix 2. Reading the illustrative statement before
building is worth more than reading the standard.

### 8.1 Build from accounts, not from buckets

The desk's aggregate buckets are too coarse. On this chart of accounts, four of the items IFRS 18
forces out all sit *inside* one bucket called "Provisions" or "Other operating expenses":
Zakat, interest on employee-benefit obligations, losses on disposal, and the annual insurance claim
true-up. Pull **every** profit-or-loss account monthly by cost centre (`sql/ifrs18_pl_accounts.sql`)
and build the statement from those. Keep only revenue on the bucket series, because that is what
ties to the invoice tables.

Tie-out gate before shipping: account-level expense total vs the bucket total for one closed year
(Al Faihaa FY2025: 56,987,872 vs 56,987,875 — SAR 3), and both mandated subtotals vs the audited
statements (FY2025: 1,922,842 vs 1,922,881, and 1,775,198 vs 1,775,238).

### 8.2 Classification for a clinic group like this one

| Item | Account | Category | Basis |
|---|---|---|---|
| Loan interest | `3290001` | Financing | IFRS 18.60(a) |
| Interest on employee-benefit obligations | `3390000` | **Financing** | IFRS 18.61(a); EY note 13.4 |
| Bank commissions | `3290002` | Operating | A service fee, not a cost of raising finance |
| Rental income | `4300003` | Investing *(switchable)* | IFRS 18.53(c) — returns income independently |
| Differences on bank accounts | `4300009` | **Investing** | IFRS 18.53(b) — cash and cash equivalents |
| Gains on disposal | `4300008` | Operating *(switchable)* | IFRS 18.B60 — same category as before derecognition |
| Losses on disposal | `3380000` | Same switch as the gains | IFRS 18.44 forbids offsetting; B60 requires symmetry |
| Insurance claim deductions | `3280004` | Operating expense *or* contra-revenue *(switchable)* | IFRS 15.50–53 — variable consideration |
| Zakat | `3280005` | Income-taxes position | Not an IAS 12 tax; read from the ledger so any period works |

**The trap that cost a version.** Zakat sits inside the provisions bucket. If the tab deducts the
bucket as an operating expense *and* deducts Zakat again from the audited-FS series, the charge is
taken twice — and the line labelled "profit before Zakat" is actually net profit, which makes it
appear to tie. Always take Zakat from the ledger account, exclude it from operating expenses, and
check **both** subtotals against the audited statements, not just one.

### 8.3 Present expenses by nature

Build the operating block as real nature groups from the accounts (EY Appendix 2 style), not as the
desk's buckets. IFRS 18.B79 forbids labelling a material item "other" — a residual worth 20% of
revenue is a failed disaggregation, not a line item. Target: the residual "other administrative
expenses" under 0.5% of revenue.

### 8.3A Nature or function — a switch, with the note the standard requires

The tab offers both presentations of operating expenses (IFRS 18.78); the switch is the first
control in the tab bar (`#i18-view`: `nat` / `fn`).
- **By function** uses the audited FS mapping by cost centre: COR (clinics and medical
  departments) = Cost of revenue; GA + INS (insurance-claims units) + HO + X = General and
  administrative. The face shows Revenue → Cost of revenue → **Gross profit** (18.B78) → Other
  operating income → G&A. Insurance-claim deductions and losses on disposal stay on the face as
  separate nature lines (18.B79 allows a mixed presentation). Operating profit is identical in both views.
- **Required once any line is by function (18.83):** a single note of the specified expenses —
  depreciation, amortisation, employee benefits, impairment, inventory write-down — each with the
  total and the amount inside every function line (EY Good Group Note 13.5 style), nil items shown with
  the reason, and 18.83(b) disclosure of the part outside operating (EOSB interest in financing) and
  the capitalised amounts (18.B84).
- **Full analysis card** (EY 13.8 style): every nature group × function line, total and comparative,
  "total = face of statement", plus the separately-presented items to reach total operating expenses.
- Data: `DATA.ifrs.fser` ('acct|cc2|f' → monthly DR−CR, posted + open) built by
  `scripts/build_ifrs_fn.py` from `drv/gl_all.json`; gate stops the build if an expense account has no
  nature group; split gap vs `ser` must be 0. `refresh.py build` runs it after the drivers and patches
  `DATA.ifrs`. FY2025 tie: Cost of revenue 36,404,153 vs audited COST 36,401,952.79; G&A 15,843,030 vs
  15,840,806.86 (the known 2,200 depreciation JV and 2,223 reclass).

### 8.4 Required notes and lines

- **IFRS 18.83 — specified expenses by nature**, one note: depreciation, amortisation, employee
  benefits, impairment losses and reversals, write-downs of inventories. State the nil ones as nil
  *with the reason*, and name the amounts sitting outside the operating category.
- **IFRS 18.75** — impairment losses determined under IFRS 9 as a line item on the face. If the
  chart of accounts has no ECL account at all, show the line at nil and raise it as a finding.
- **IFRS 18.75(a)(iii)/(v)** — share of profit of associates and joint ventures; discontinued
  operations. Show as nil lines when absent.
- **MPM note (IFRS 18.121–123)** — a measure is only an MPM if management uses it in public
  communications *outside* the financial statements; say so. For each reconciling item give the
  income-tax effect, the NCI effect, and the method. Where Zakat is computed on the Zakat base, the
  tax effect of an add-back is nil — state that, don't leave it blank.
- **IFRS 18.27(d),(e)** — label the comparative column *Restated*.
- **IFRS 18.10(a)** — call it "statement of profit or loss", not "income statement".
- Category headings are **not** required (EY's statement has none); keep them only when the page's
  job is to explain the classification, and say so.

### 8.5 Always show the bridge and the findings

    net result per the desk's period strip
      + Zakat, previously charged inside provisions
      − reclassified to investing
      − reclassified to financing
      ± GL detail vs the desk's aggregate buckets
      = operating profit under IFRS 18

And carry a findings card naming every reclassification with its amount, tagged *fixed*,
*reclassified* or *raised for management*. A restatement nobody can trace back is a restatement
nobody adopts.

### 8.6 Al Faihaa, FY2025 (after the audit)

Revenue from contracts with customers 57,099,067 · **operating profit 564,292** · profit before
financing and income taxes 2,557,233 · profit before Zakat 1,922,842 (audited 1,922,881) ·
Zakat 147,643 · profit 1,775,198 (audited 1,775,238).

The finding that survives: the four clinics between them earned SAR 564k in FY2025; SAR 1.99M of
rent is what carried the year. That is exactly the burial IFRS 18 exists to stop.

Open items this surfaced: the insurance claim true-up is posted once a year in December, which
distorts every monthly view on the desk; and there is no expected-credit-loss account in the chart
of accounts at all, on a receivable book of SAR 10–17M. The desk's monthly bucket series is also
missing June–July 2026 rental income (~339k) — this tab is unaffected because it uses account
detail, but the bucket extract should be re-run.

## 8A. Refreshing the monthly GL bucket series (DATA.m)

`DATA.m` is the series the whole desk runs on — Statements, Valuation, Departments, Cost Centres,
the period strip. Refreshing it is the one extract with no margin for error, because it moves
published history.

**The classifier.** The desk's 37 buckets are not in the Oracle schema and not in any source system.
The map lives in `scripts/build_monthly_buckets.py` — an explicit account-number classifier
(15 exact accounts, then 36 prefix rules) that was reverse-engineered from the published series and
**verified against it**: every bucket reproduces the published values to under SAR 1.5 on all months
up to the last fully-posted one. Balance-sheet buckets are checked against `ACCOUNTS` parents. One known variance: a SAR 60 line in Jan 2023 that the
original build put in Related-Party Receivable and the classifier puts in Accounts Receivable.

**The basis: posted + open (since 25 Sep 2026).** The series is rebuilt from the `gl_mon` refresh job
(`drv/gen.py gl`): every voucher with `STATUS <> 'C'` (posted **and** open), `VOUCHER_NO <> 'JV1-24/04043'`,
`NOT EXISTS (FINANCIAL_YEARS ...)`, cost centre = first two characters of `COST_CENTER_NO`, one row per
account × cost-centre prefix × function × month. The same pull feeds the Deep Analysis drivers (§13), so
the desk and the drivers can never disagree. The earlier posted-only basis (`sql/gl_monthly_accounts.sql`,
kept for reference) left open vouchers — e.g. June–July 2026 rental income of SAR 325,834 — out of every
tab except IFRS 18; the owner's rule is that all journal entries, open or posted, belong in every figure.
Closed months reproduced within SAR 1 when the basis changed (three cells moved by one riyal from
half-riyal rounding; amounts are now summed in whole halalas, so row order can never move a rounding again).

**The gate.** `build_monthly_buckets.py m_po.txt --closed=<first month of the re-read window> --write`
re-verifies every month before the window against the published series and prints
`VERDICT ALL BUCKETS REPRODUCED` or the buckets that moved; `refresh.py build` fails the gate on anything
else. A new month extends every series automatically. A closed month that moves means either the basis
drifted or vouchers were posted late into a closed period — find out which before publishing.

**What a refresh is actually worth.** Late posting, not staleness, is what moves the numbers. At the
24 Sep 2026 refresh, FY2025 moved by SAR 4 (history reproduced) while **August 2026 — the last
closed month — moved from a net loss of 86,788 to a net profit of 931,370**, because roughly
SAR 1.95M of credit revenue had been posted in the four days since the previous extract. So refresh
the most recent closed month even when nothing else changed, and always report the month-by-month
delta rather than just republishing.

## 8B. DATA.ext — statements from the ledger

`DATA.ext` drives Overview & 3-Statement, Deep Analysis, DCF, LBO, Trading Comps and the top-level
`DATA.trend` / `bs_trend` / `ratios`. It is built from the journal lines only (`gl/build_ext_gl.py`):
`sql/gl_annual_accounts.sql` per database → annual net movement per account × organisation function ×
voucher flag, classified with the `ACCOUNTS` parent (`bs_line` rules) and the organisation-function rules
of §3A. Cancelled vouchers, year-end closing vouchers (`FINANCIAL_YEARS.GL_VOUCHER_NO`) and
JV1-24/04043 are excluded; the balance sheet is cumulative from the 31 Dec 2018 opening voucher.

- `ebitda` on the desk is **net income + depreciation** — it does not add back interest or Zakat.
- **Gates** (in `refresh.py build`): every year's balance sheet balances within SAR 1; a closed year
  whose revenue or net income moves by more than SAR 1 is reported (a posting into a closed year).
- 24 Sep 2026: 2026 YTD revenue 36,186,336, net income 4,505,967, cash −1,940,435, total assets 80,645,821.

## 8C. Peer set — Saudi listed only

The Trading Comps and Competitive Analysis tabs run on `DATA.peers`
(`scripts/build_saudi_peers.py`, `templates/comps.js`, `templates/compet.js`, `templates/peers.css`).

- **Universe:** every healthcare *provider* listed in Saudi Arabia — Tadawul main market and Nomu.
  Equipment, distribution and waste-handling names in the same sector classification are listed in
  their own table with the reason they are out, rather than dropped silently or left to flatter the
  medians.
- **Nomu is the comparable set, TASI is a scale reference.** A clinic group at SAR 57M of revenue
  is Nomu-sized; the smallest TASI name is 20× larger. Medians are reported separately per market
  and never blended.
- Mark every computed multiple as computed, and carry each company's own data date — market caps
  from a free source are often weeks apart, and a multiple moves with the share price.
- State the private-company discount on the page as a number, not in prose. It is the single
  assumption that moves the implied valuation most.
- **Al Faihaa, 24 Sep 2026:** 11th of 13 by revenue; EBITDA margin 6.7% against a Nomu median of
  21.1% and a TASI median of 22.7% — every listed provider on both markets earns more per riyal.
  Implied EV on the Nomu revenue median is about SAR 107M; on the Nomu EBITDA median about SAR 35M.
  The gap between those two numbers is the margin gap, and it is the finding.

## 9. Layout

`main` is full-width (`max-width:none`, fluid side padding) so the tables use the whole window.
Arabic sections set `dir="rtl"` on the section element and force the period strip (`.ps`) back to
`ltr`; numeric cells keep `direction:ltr` so signs stay on the correct side. Wrap any number that sits
inside an Arabic sentence in `<bdi>`, or the percent sign jumps to the wrong end.

## 10. Auditing a cash flow statement

The only test a cash flow has to pass: **closing cash equals the cash line on the balance sheet, every
period.** If it does not, the statement is missing a balance-sheet movement — and the plug that hides
it is worth more than the statement.

**Method** (`gl/drcr.sql` debit/credit groups + the annual accounts of §8B, `scripts/build_cfa_gl.py`)

1. Pull the tie-out per year: opening cash, CFO, CFI, CFF, net change, closing, balance-sheet cash.
2. Pull **every** balance-sheet line and **every** cash-flow line by year.
3. Pair them: for each balance-sheet line, the movement in the balance against the cash-flow line(s)
   that represent it. Every pair must net to zero:

   | Balance-sheet line | Cash-flow lines |
   |---|---|
   | Receivables (net) | change in AR + doubtful-debt provision + bad debts written off |
   | Property & equipment | depreciation + purchases + disposal proceeds + gain − loss |
   | Severance pay | provision + paid + actuarial remeasurement (the OCI pair nets to nil) |
   | Zakat / vacation / unearned revenue | provision + paid |
   | Loans | proceeds + finance paid + finance cost added back in operating |
   | Retained earnings + reserve + dividends payable | net income − dividends paid |

4. Whatever is left is the break, and it names itself.

**A first-principles check before any of that.** Sum the movement in every non-cash balance-sheet line;
it must equal the movement in cash. If it does, the balance sheet is complete and a correct cash flow
*must* tie — so any break is in the statement, not the data. Run this first; it decides where to look.

**What it found at Al Faihaa.** Every line tied in all seven years except the equity block. FY2020 was
out by −160,545 and FY2021 by +416,048, both sitting in retained earnings, the statutory reserve and
dividends payable. The model's `Dividends Paid` item takes the debit movement on dividends payable —
the cash actually paid — but nothing in the statement carried postings made *directly* to retained
earnings or the reserve, so those two years leaked. From FY2023 there are no such postings and the
statement ties on its own, which is why the defect had gone unnoticed.

**The fix**: one calculation item, *Movements taken directly to equity*, computed as
`-( NI - ΔRE - Δreserve - Δdividends payable ) - [CF-20-Dividends Paid]`, included in net cash from
financing. It is zero in a clean year and shows the amount in a year that has direct equity postings,
instead of silently breaking the closing balance (built from the ledger: net income − Δ retained earnings − Δ reserve − Δ dividends payable − dividends paid).

**Open vouchers.** The statement uses posted + open lines; the period strip uses posted only. The
`gl_open` refresh job counts the open vouchers of the current year and their movement on cash
accounts per branch, and the cash-flow findings quote it.

## 11. Adding a feature (keep the kit current)

1. Put new SQL in `sql/` with `{P}`, `{D0}`, `{D1}` placeholders and a header comment naming the tie-out figure.
2. Put the payload builder in `scripts/` and the UI module in `templates/`, following the build pattern in §1.
3. Add a section to this SPEC: source, rules, tie-out.
4. Update the skill `CFO-Cure-HanyGameel`: read the current SKILL.md, add the feature line and file references, and propose the full updated skill.
5. Write or update the matching project doc (`claude/modeling-desk-*.md`).

## 12. Fast refresh (`refresh/refresh.py`)

A refresh used to be slow for four reasons: every dataset was re-read from 2019 or 2024; heavy
line-level queries (window functions over years of lines) timed out and blocked the device for
2–3 minutes; results were copied by hand between steps; and each payload was patched separately.
The refresh tool removes all four.

| Rule | How |
|---|---|
| Read only what can still change | Ledger jobs read from 1 Jan of the open year (1 Jan of the prior year until 31 Mar, for late postings). Invoice jobs read from the 1st of the previous month. Closed periods stay in the caches (`gl/y_*.txt`, `gl/cc_rows.json`, `gl/drcr.json`, `anomdb/*_rows.json`, `expdb/*_exp.txt`, `aud/data_aud_db.json`, `drv/gl_all.json`, `drv/m_po.txt`, `drv/cc_all.json`, `drv/vis_all.json`) |
| Light jobs in parallel | Batch A: 18 GROUP-BY jobs × 4 branches (72 calls). Run the four branch calls of a job at the same time |
| Heavy jobs weekly, one at a time | Batch B (`plan --weekly`): exception lines, price outliers, duplicate services, discount beneficiaries, expense red flags. Never two at once; after a timeout wait 3 minutes, then split the date range |
| No re-typing | `ingest <job> <br> --file <MCP result file>` or `--marker '<text>'`; parsers handle packed LISTAGG buckets, plain columns and single text columns |
| One build | `build` merges, rebuilds every payload, runs the gates (balance sheet balances, closed years unchanged, every doctor named) and patches the HTML. Date stamps move only on a complete batch A |

Sequence: `plan` → run batch A (parallel per job) → `ingest` each → `build` → render-test → republish.

**The fastest option (recommended next step):** add one tool to the Cure MCP on the finance PC,
`cure_export_query(branch, sql, path)`, that writes the full result to a CSV in the connected folder
instead of returning it to the chat. The database connection stays inside the MCP (no credentials are
handled anywhere else), the 200-row cap and the LISTAGG packing disappear, and a whole refresh
becomes about 90 short calls whose output never passes through the conversation.

## 13. Deep Analysis — drivers (revenue, department, cost, net income)

Four tabs inside Deep Analysis that explain **why** a figure moved against the same period last year
(YoY) or the previous equal-length period (MoM / QoQ). Every tab honours the global period, branch and
comparison controls. UI: `templates/drv.js`, `templates/drv.css`; payload `DATA.drv` from
`scripts/drv/build_drv.py`; SQL from `scripts/drv/gen.py` (`gl`, `cc`) and `anomdb/gen.py vis`.

**Sources (all four databases, Cure MCP only)**

| Job | Rows | Feeds |
|---|---|---|
| `gl_mon` | account \| cc prefix \| function \| YYMM \| DR−CR — posted + open, closings and JV1-24/04043 excluded | net income, cost by nature and by function, ledger revenue; also `DATA.m` (§8A) |
| `cc_mon` | YYMM \| full cost centre \| cash 41x \| credit 42x (ex 4200027) \| expense DR \| expense CR (ex zakat 3280005) | department driver |
| `inv_vis` | YYMM \| payment type \| doctor \| specialty \| distinct episodes \| net revenue \| net revenue ex pharmacy | revenue driver (volume, price, mix) |

**Definitions (agreed with the owner, 24 Sep 2026)**
- Revenue = cash 41x + credit 42x, excluding 4200027 (insurance drug sales → other revenue). Zakat = 3280005.
- Function: COR = cost centres 0102/0202/0302/0402 or 01011301-03/02011301/03011301/04011301; GA = 001–004;
  INS = 010100/020102/030100/040100; HO = other 00*; X = unassigned. Nature groups = the IFRS 18 nature map
  (`DATA.ifrs.nat`); accounts outside it show as "Other expenses", so nature total = function total.
- Volume = visits (distinct patient file + episode). Invoice net = bill − discount − insurer share − VAT, refunds negative.
- Open month: shown, marked partial. Revenue MoM compares the same number of days (like-for-like, using each
  segment's daily revenue share from `DATA.anom.daily`); ledger tabs show a banner, and ratio tiles show "—"
  when ledger revenue ≤ 0 (sales not posted yet).

**Price–volume–mix** over segments branch × payment type × specialty, exact (components sum to the change):
Volume = ΔV × p0; Mix = Σ V1s·p0s − V1·p0; Price = Σ V1s·(p1s − p0s) on continuing segments; New/lost = remainder.

**Charts:** waterfall bridges (PVM, branch × payment, department contribution, cost by nature/function, NI bridge),
treemaps (specialty, department revenue, cost), decomposition trees (branch → payment → specialty → doctor;
nature → account; NI → revenue/function → branch/nature), movers lists, nature × function change matrix,
month × driver heatmap vs last year, monthly trends. Colours: favourable #1A7FA8, unfavourable #C9502A (validated
for colour-blind separation on light and dark surfaces).

**Invoice ↔ ledger bridge (shown on the revenue tab).** Ledger revenue < invoice revenue because the Riyadh
ledger debits revenue every month with the cost of medicines dispensed (journal "ادوية عن شهر", the MED line of
`DATA.vatr.adj`, ~1.2–1.3M/month), plus 4200027 and timing. Jan–Aug 2026: invoice revenue +3.1 % YoY while
ledger revenue −3.7 %, mostly because that medicine charge grew from 8.00M to 10.07M.

**Tie-outs (25 Sep 2026):** ledger revenue 2024 56,638,027 · 2025 56,966,108 · 2026 YTD 36,186,337; net income
2024 −3,905,285 · 2025 1,775,238 · 2026 YTD 4,505,978 — equal to the statements rebuilt from the ledger
(`DATA.ext`). Every bridge closes exactly (start + steps = end).

## 14. Zakat (Implementing Regulation for Zakat Collection 1445H)

One sidebar entry (group **Zakat**, RTL Arabic) with in-page tabs: the return, equity and similar items,
liabilities, deductions, net profit and expense classification (with the fines list), zakat provision and
accrual. Years from 2024 (the regulation applies to financial years starting on or after 1 Jan 2024 —
resolution 1007, amended by 1248), plus the open year as an estimate. Company level: the branch filter does
not apply. Builder `zak/build_zakat.py` → `DATA.zak`; UI `templates/zak.js`, `templates/zak.css`; expense
categories `zak/exp_class.json` (the owner's 2025 classification workbook). Source: EXSYS only —
`gl/y_*.txt` closing balances, `DATA.ext`, `drv/gl_all.json`, and `zak/lines.json` (refresh job `zak_lines`:
every 3280005 / 2123003 / 2111004 line and every expense line whose description names a violation or fine).
`refresh.py build` rebuilds it last.

**Owner's rules (25 Sep 2026)**
1. The calculation starts from **net profit before the year's zakat** (book net profit + the year's zakat
   provision entry "اثبات مصروف مخصص الزكاة عن عام Y").
2. **Government fines and violations are not an accepted expense**: they stay in expenses and are added to
   profit before zakat to reach adjusted profit. Taken from 314xxxx lines whose description says مخالفة/غرامة,
   net of the 3140004 → 3140001 reversal and reclassification entries; lawyers' fees, grievance-board fees,
   bank transfer fees and compensation to patients are excluded (shown for review).
3. **Zakat differences for earlier years** (assessment, examination, own correction — e.g. −38,771.19 in April
   2025 for 2024) are an accepted expense or taxable income: they stay inside profit.
4. **Equity includes retained earnings with the year's profit before zakat.** The year's zakat provision is
   therefore not added again; only an unpaid balance for earlier years would be (Art. 24).

| Line | Accounts | Treatment | Article |
|---|---|---|---|
| Equity | capital 2210xxx, reserve 2230xxx, retained earnings incl. the year's profit **before** zakat, actuarial reserve 2240001 | closing balance | 17, 23(1), 38 |
| Provisions → equity | cases & violations 2111004, any 2111xxx except end-of-service / leave; zakat 2123003 only for unpaid earlier years | closing balance | 24 |
| Dividends payable → equity | 2128xxx credit balances | declared, not deposited | 36 |
| Owner current accounts → equity | 2126xxx **credit** balances; debit balances not deducted, no set-off | | 30(2), 31, 34 |
| Non-current liabilities | end-of-service 2111001, leave 2111003 (and 2111002), loan 2113002 net of deferred interest 1262000 less the current portion | capped at deducted assets | 23(2), 24, 29(1) |
| Current liabilities | added only for the excess over current assets | | 29(2)(b), 25 |
| Deductions | net fixed assets 111x/1111x, intangibles 112x/1121x, projects under construction 113x | net book value | 26, 48–50 |
| Not added | insurance discount allowance 1240008 (reduces an asset) | | FAQ Q22 |
| Net profit | before the year's zakat + fines; the difference to book profit is added to the base | | 23(3), 62 |
| Limits | minimum = min(undeducted assets + difference, adjusted profit) when base < adjusted profit; maximum = equity & similar + difference | | 27, 28 |
| Rate | 2.5% ÷ 354 × days of the year (366 in 2024) | | 15 |

**Current portion of the loan**: net repayment of the last closed year (equal instalments), capped at the carrying
amount — 1.5M in 2024 and 2025, matching the audited split.

**Results (EXSYS, 25 Sep 2026)**

| Year | Profit before zakat | Fines | Adjusted profit | Base | Zakat | Year's provision booked | Difference |
|---|---|---|---|---|---|---|---|
| 2024 | −3,692,793 | 16,175 | −3,676,618 | 6,736,968 | 174,134 | 212,487 (then −38,771 in Apr 2025) | −38,353 |
| 2025 | 1,961,653 | 129,650 | 2,091,303 | 8,228,809 | 212,113 | 186,414 | +25,698 |
| 2026 est. | 4,505,967 | 96,500 | 4,602,467 | 11,032,666 | 284,387 | 0 | accrual due 208,031 |

The ledger's own 2024 correction (−38,771.19, "بعد حذف القروض قصيرة الاجل من الاضافات") brings 2024 to 173,715 —
the desk's 2024 base without the fines. 2025 fines in EXSYS are 129,650: the 111,400 provision (2111004,
JV1-25/04114) plus 18,250 booked during the year (civil defence 7,000, storage 10,000, traffic 750, iqama 500).

**Review of the owner's 2025 workbook (25 Sep 2026):** (1) leave provision 867,307 (2111003) not added — per EXSYS the
end-of-service line 8,485,324 is 2111001 alone (owner says it is included; the desk follows the ledger and flags it);
(2) fines: workbook adds 111,400, the ledger shows 129,650; (3) the Art. 23(3) difference row (D24) was blank, so the
difference never reached the base and the min/max tests read 0; (4) the booked comparison used the 2024 provision
(212,486.60); (5) template leftovers: `#REF!`, external `[1]Return` links, shifting VLOOKUP ranges. Overlap to confirm
with the zakat adviser: the 111,400 cases & violations provision is in equity (Art. 24) and the fines behind it are
also added through the profit difference (Art. 23(3)).


## 15. AR Audit · insurance payments (Accounting Audit → `aud-arx`)

Purpose: for every payment voucher on **1240007 عملاء شركات التأمين** registered in a month (creation date, so
back-dated July/August transfers entered in September are in scope), prove from the attached documents that
(1) the attachment exists and is the right one, (2) the remitter on the bank advice is the customer credited
(a known TPA pairing counts as "T", not a failure), (3) the amounts agree, (4) the payment month is the same on
the voucher, the transfer and the claim papers, (5) a claim/remittance/settlement supports the amount, and
(6) the transfer is booked once.

Pipeline (kit `scripts/arx/`, SQL `sql/arx_insurance_payments.sql`):
1. Cure MCP: voucher lines (packed `ARX~` rows; `parse_lines.py` joins wrapped cells), creation dates, `EX_ATTACHMENTS`.
2. PowerShell on the finance PC copies each attachment from the branch file server (X/U/T/Q drives) to
   `Financial\_arx_docs\<BR>_<voucher>_<imageId>.pdf`; rows whose file is missing are recorded (broken attachment).
3. Stage to the container; `pdftotext` for text PDFs, `pdftoppm -r 80` JPEGs for scans (bank advices are scans).
4. Read every page (one reader per branch, brief `AGENT_BRIEF.md`) → `extract/<BR>.json` (per document + per-voucher verdict).
5. `build_arx.py` → `data_arx.json` (checks, coded findings, duplicate groups); `patch.py` → `DATA.arx`, CSS, JS, nav entry.
Document reading cannot run unattended from refresh.py; re-run steps 1–5 each month and add the month to `months`.

Excluded on the same account: credit notes (AR CN) and provision entries — they are not payments.

Sep 2026 result (101 vouchers, 1,385,987.62, 191 documents): 15 exceptions, 54 to review.
- NEXtCARE sent 40,654.76 / 21,616.54 / 35,556.67 on 31-08-2026 in error and SNB returned them 01-09-2026; each branch
  receipted the incoming transfer twice (BR1-26/00260+00263 posted, BR2-26/00182+00184, BR3-26/00169+00171) and the refund
  once → 97,827.97 overstated on 1224005 and on customer 100166.
- Total Care Saudi payments credited to NEXtCARE sub-account 100166 instead of 100186 (BR2-26/00191, BR4-26/00208, 00209 = 11,192.81).
- Broken attachment rows (BR2-26/00171, 00172, 00174); BP3-26/00001 attaches the incoming transfer, not the refund;
  BR1-26/00258 exceeds the attached claim; BR4-26/00199 untraceable to the Malath statements.
- 33 transfers received in an earlier month than the voucher date; 28 with no claim/settlement statement; "75%" narratives are 71.7–72.0%.


## 16. Payment Via NPHIES · Rafha (Accounting Audit → `aud-nph`)

Rafha is the only branch that sends claims and receives payment notices through NPHIES. For every notice with a
positive amount: amount vs claim lines (and vs company net claimed), who paid (named / via TPA / no group), service
month (single / mixed / not linked), and whether an exact-amount receipt exists in the Rafha ledger. An amount box
answers "who sent this transfer?" (single notice, then same-day totals per insurer).

Joins (verified on Rafha): notice `HS_NPHIES_PAYMENT_RECONCLATION` → lines `HS_NPHIES_PAYMENT_RECONC_DTL`
(`req_` stripped) → `HS_NPHIES_CLAIM_REQUEST` (dedup per REQUEST_PREAUTH_ID) → `RC_EPISODE_INVOICES`
(INVOICE_START_DATE = service month, ACCOUNT_NO = 1240007 sub-account the claim books to). Payer = INSURER_ID →
`CUSTOMER_GROUPS.NPHIES_ID`. The SOA_DATA / CLAIM_SUMMARY views are not used (SUMMARY times out). Tawuniya headers were
bulk-loaded (2 dates) → the claim-line payment date is used when one header date carries >200 notices of one insurer.
Pack: `sql/nphies_payment_recon_rafha.sql`; build `scripts/nph/build_nph.py` → `patch.py`.

Discovery (26 Sep 2026): 5,496 cash notices, 3,696,514.32 SAR, 10/03/2024–10/09/2026, 16 payers — 9 named, 5 GlobeMed-
administered licences with no group (7001626717 Amana, 7001527667 Arabian Co-op, 7001537161 Mutakamela, 7001523724 Salama,
7041839510 Orient — carrier from booking account), 2 named only in the message (ACIG 7001535694 → books to 100132,
Gulf General 7001641419). 69.6% header = claim lines (Tawuniya header ≈ 1.7× lines); 1,113 notices not linked to claims;
135 notices found in the Rafha ledger by exact amount.

**v32 — two-way reconciliation.** Notice → ledger status: booked (right company) / booked to another company /
awaiting (≤ 60 days) / not found / duplicate notice / per-claim (Tawuniya, Gulf Union, Bupa claim-level — reconciled by
month). Ledger → notice status (Rafha BR/JV receipts on 1240007 since 2025-01): matched / other company / NPHIES payer
with no notice / after the payer's last notice / before its first / per-claim payer / payer not on NPHIES. Match rule:
same payer's account (booking accounts + its customer group), amount equal or within 2 SAR, single notice or same-day
total, −15…+100 days; exact other-company matches ≥ 100 SAR flagged. Narrative month (Arabic month names) vs service
month compared. UI: status chips, payer/month/search filters, hover-to-preview detail panel, click to pin; payer panel
shows month-by-month NPHIES vs ledger. Sep 2026 run: 200 transfer-level notices — 145 booked (1,175,042.73),
45 not found (177,527.20), 7 awaiting (75,132.17), 3 duplicates; 491 receipts — 123 matched, 58 NPHIES-payer receipts
with no notice (516,887.84), 27 after the payer's last notice, 157 from non-NPHIES payers.
