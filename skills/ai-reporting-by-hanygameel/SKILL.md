---
name: ai-reporting-by-hanygameel
description: "Use to stand up Hany Gameel's full AI Reporting HUB analytics suite (GL/Financial Modeling Desk, CFO Command Center, Inventory audit, Department Assessment, NPHIES RCM audit) at a new healthcare site running EXSYS via Savan-style read-only Oracle access."
---

# AI Reporting HUB by HanyGameel — replication playbook

This skill packages the full "AI Reporting HUB" analytics practice — everything built against the **EXSYS** Oracle ERP/HIS (chart of accounts, inventory, NPHIES revenue-cycle billing) through a read-only **Savan**-style MCP connection — so the same suite can be rebuilt at a **new** EXSYS site (a different hospital/clinic/branch, a different Oracle instance/DSN, a different schema owner) without re-discovering the schema, the ledger quirks, or the audit logic from scratch.

EXSYS itself does not change between sites — same table names, same module structure (`GL_*`, `IM_*`, `RC_*`, `HS_NPHIES_*`, `ORGANIZATIONS`, `PERIODS`). What changes per site is the **connection** (DSN/host/port/service name, schema owner, credentials), the **data** (account numbers used, org-hierarchy depth, whether NPHIES/insurance billing is even live there, whether inventory batch-tracking is switched on), and **site-specific configuration** (digit-length convention for department vs. cost-center orgs, which GL accounts map to which P&L line, whether budget tables are populated). Treat every number and every table-emptiness finding below as **provenance from the original site(s)** (Al-Faiha Medical Services Group, Safan Medical Complex, and "Riyadh Medical Group" — the working alias used in these dashboards), not as a fact to assume true elsewhere. Re-verify each one against the new site before reusing it.

## 0. Non-negotiable principles (carry these into every rebuild)

1. **Never invent a financial number, KPI definition, accounting policy, database field, or business rule.** If EXSYS doesn't hold it (budget, forecast, batch tracking, a crossmatch table), say so in the deliverable — build the framework wired to the real columns and leave it empty/labeled rather than fabricating a figure.
2. **Every audit/RCM flag is a screening signal for human review, never a determination.** Never output language implying proven fraud, proven clinical error, or "reject this claim." State plainly what would need manual verification.
3. **State data-quality gaps in-tab, not just in a private note.** When a table is empty, a column is 0%-populated, or a config default is universal (e.g., every product sharing the same MIN/MAX stock), say so next to the affected metric so the reader doesn't mistake a config artifact for a real finding.
4. **Reconcile before you build on top.** Every downstream model (3-statement, DCF, Cash Flow, CFO Command Center) sits on the GL tie-out. Get the GL source-direct refresh balancing to the riyal (or to zero variance) before layering anything else on it.
5. **Abstract the data-source name in anything user-facing.** Dashboards/workbooks show a friendly source label (the original build used "Cure+"); never surface the raw DB host/IP in the UI. Pick an equivalent neutral label for the new site.

## 1. Prerequisites for a new site

- Read-only access to the site's Oracle EXSYS database through an MCP tool with the Savan tool shape: `run_query` (parameterized SQL, typically capped at ~1000 rows/call — plan on pagination), `describe_object`, `get_object_ddl`, `list_objects`, `list_schemas`, `search_columns`, `preview_table`, plus attachment tools if scanned documents/certificates are in scope.
- Confirm the DSN (host:port/service name), schema owner, and login (the original build used `192.168.8.27:1521/Exsys`, user `HANI` — a new site will have its own).
- Confirm what modules are actually licensed/used at the new site: GL is near-universal; Inventory (`IM_*`) and NPHIES/insurance RCM (`RC_*`, `HS_NPHIES_*`) are separate modules that may or may not be active. Don't build an RCM audit against a site with no NPHIES billing.
- If the new site will get a scheduled daily refresh, confirm where the local device/folder for output files lives (the original used `D:\Reports\AI Reporting HUB\<module>\`) and set up an equivalent path.

## 2. EXSYS/Savan platform quirks — verify each one at the new site before relying on it

These are true of the sites this suite has been built on so far. Confirm, don't assume:

- **Unqualified table names only.** A literal `EXSYS.TABLE_NAME` prefix trips the Savan query guard (it blocks the substring `SYS.`). Always query bare table names; the connection already defaults to the right schema.
- **Row cap per call (~1000 rows).** Any full-detail pull (transactions, vitals, episodes) needs `OFFSET n ROWS FETCH NEXT 1000 ROWS ONLY` pagination, run sequentially or at low concurrency (2–3 parallel) — the device bridge can time out under higher concurrency.
- **Chart-of-accounts number ranges** (verify per site's own CoA — don't assume the same ranges): assets `1xxxxxx`, liabilities+equity `2xxxxxx`, expense `3xxxxxx`, revenue `4xxxxxx`; `GL_ACCOUNT.ACCOUNT_TYPE` = A/E/L/R confirms it regardless of the numbering.
- **Periods**: `PERIODS.PERIOD_NO` maps to fiscal year in blocks of 12 (e.g. 1–12 = year 1, 13–24 = year 2) — confirm the mapping and the current period ceiling at the new site.
- **Year-end closing voucher.** A single journal voucher (pattern like `JV1-YY/00160`) sweeps the full year's revenue/expense to retained earnings in the closing period. Reading a closed year's P&L means summing that year's periods **excluding** the closing voucher; an open year is read directly. Find the actual voucher number/period at the new site — don't assume it's period 12.
- **Org hierarchy for department/cost-center reporting.** `ORGANIZATIONS.ORGANIZATION_NO_PARENT` gives the tree; the digit-length convention that separates "department" from "cost center" (6-digit vs 8-digit in the source sites) is a site-specific convention to confirm by inspecting the actual org codes, not a fixed rule. In the inventory module, `ORGANIZATION_NO` doubles as the cost-center code directly (`CC_TYPE='C'`).
- **Presentation overlays are policy choices, not schema facts** — confirm at each site whether: loans should be shown net of a deferred-interest contra account; whether a related-party account with a debit balance should be reclassified from liabilities to a current asset. Both were true at the source sites; verify against each new site's own accounting policy before repeating.
- **Budget/forecast tables are frequently empty.** Check `BD_BUDGETS`, `BD_BUDGET_DETAILS`, and `GL_PERIOD_SUMMARIES.BUDGET_AMOUNT` before building a Budget-vs-Actual view — if empty, ship the view wired to the exact columns (`PERIOD_NO`, `ORGANIZATION_NO`, `ACCOUNT_NO`, `AMOUNT`) but empty and labeled, so it auto-populates the day someone loads a budget.
- **Inventory balance source of truth**: prefer `VINV_QTY_STORE` (a view derived live from `IM_ALL_TRANSACTIONS`) over `IM_STORE_PRODUCTS.QTY_ON_HAND`, which can be entirely unpopulated even though the ERP UI appears to use it. Confirm per site with `savan_preview_table`.
- **Inventory MIN/MAX/REORDER defaults.** Check whether every product shares one identical default (e.g. `MIN=1/MAX=3/REORDER=2`) — if so, the ERP's own overstock alert is a config artifact, not a real signal; use a days-of-cover-from-actual-consumption calculation instead (see §4.6) and flag the config gap.
- **Batch/lot tracking may not be populated** (`IM_STORE_PRODUCT_BATCHS` can have zero rows even with active inventory). If so, expiry risk has to be inferred from expiry dates stamped on receipt transaction lines as a proxy — state clearly that it flags risk, it doesn't prove remaining quantity by lot.
- **Purchase costing needs two corrections before any supplier price comparison is trustworthy**: (1) net out the line-level discount (`DISCOUNT_RATE`/`DISCOUNT_AMOUNT` on the purchase-invoice-detail table) — raw list price can overstate true cost by ~2×on discounted lines and can make a cheaper supplier look more expensive; (2) normalize quantity and unit cost to the product's **primary UOM** using the UOM conversion factor table — comparing raw purchase-UOM prices (e.g. a box price vs. a piece price for the same product) can produce false 10×"price wins" that are really a receiving-entry UOM mistake. Run a per-product median-outlier check (flag lines >3× or <1/3× the product's own median unit cost) and exclude those from "best price" rankings while still showing them, flagged, in the full detail matrix.
- **Column-name idiosyncrasies exist and should be preserved, not corrected** — e.g. a vitals table spelling "height" as `HIGHT`. Don't silently rename in queries; match the live schema exactly.
- **Sentinel/default values pollute clinical and inventory data** — e.g. a height field defaulting to a small placeholder for adults, or a ceiling value used as "unknown." Always sample real data (`preview_table`) and look for suspiciously repeated values before setting plausibility ranges for outlier/implausible-value checks.
- **NPHIES/CHI ICD↔drug crossmatch reference tables are commonly empty.** Don't depend on them for medication-necessity or diagnosis-appropriateness logic — build and maintain an explicit, editable rule-book (ATC-code-first, brand/keyword-dictionary fallback) instead, and say so in the methodology note.
- **External reference APIs (e.g. SFDA drug pricing) may not be reachable from a cloud sandbox** even though they're reachable from a networked on-site machine. Build a fetch script that runs where network access exists, cache the result to a JSON file, and have the scheduled refresh reuse the cache (skipping only the affected tab, with a stated reason, if the cache is ever missing) rather than failing the whole refresh.

## 3. Build order (each layer depends on the one before it)

1. **GL Source-Direct Refresh** — chart-of-accounts map, period/fiscal-year mapping, closing-voucher handling, and a full trial-balance tie-out. Everything else is downstream of this reconciling correctly.
2. **Financial Modeling Desk** — 3-statement, DCF, comps, LBO, competitive analysis, deck QC, built on the reconciled GL.
3. **CFO Command Center** — the executive dashboard layer (KPI semantic layer, P&L by nature, balance sheet snapshot, anomalies/risks, Ask-the-CFO), also built on the reconciled GL.
4. **Cash Flow & Deep Analysis** — indirect cash flow rebuilt from balance-sheet deltas (don't trust a raw yearly cash-flow measure table if it doesn't reconcile standalone), DuPont decomposition, leverage/working-capital trend.
5. **Department & Cost Center Assessment** — org-hierarchy drill with time-intelligence controls (YTD, MoM, YoY — annualized if a migration year has all its activity lumped in one period).
6. **Peer Operating Benchmarks** — public-source competitive context (capacity, growth, leverage, forward multiples) to complement trailing comps; clearly cite public sources when no market-data connector is available.
7. **Inventory schema map + Inventory Analysis/Audit** — valuation, overstock (real days-of-cover method, not the ERP's raw config), slow-moving/dead stock, expiry risk, receiving/data-quality flags, cross-department peer audit, dispense-by-cost-center trend, purchases-by-supplier best-price audit (with the two costing corrections from §2).
8. **NPHIES RCM Audit** (only if the site bills NPHIES/insurance) — the multi-tab clinical/billing integrity dashboard: diagnosis↔service/medication coding gaps, inactive/invalid ICD codes, financial/statement mismatches, patient-data consistency (vitals plausibility + height drift), fraud-probability screening (shared insurance card across patient files), SFDA pricing compliance + SFDA code currency, PBM pre-authorization status, diagnosis-appropriateness/medication-necessity (curated + strict rule-books), and drug-drug interaction screening.
9. **Clinical Audit Agent** (optional, per-claim companion skill) — given one episode/claim, pulls that claim's full clinical + billing picture and returns a structured audit report, with the same safety rails as the dashboard (never invent data, never conclude fraud, escalate to physician/coder review).

## 4. Module playbooks

### 4.1 GL Source-Direct Refresh
**Key objects:** `GL_TRANSACTIONS_VIEW` (posted lines: date, period, org, account, DR/CR, status), `GL_ACCOUNT` (chart of accounts + type), `PERIODS` (period→fiscal year), `ORGANIZATIONS` (org hierarchy).
**Logic:** Filter `STATUS='P'`. Sum a fiscal year's periods excluding the closing voucher to get true P&L; an open year reads directly. Map account ranges/types to statement lines using the site's real CoA rather than the source-site's example ranges. Apply presentation overlays (net-of-interest loans, related-party reclass) only if they match the new site's accounting policy.
**Deliverable:** a "GL Source" tab in the model workbook holding the trial balance that every other tab computes off; a reconciliation note (source vs. any existing BI tool, if one exists) showing variance to the riyal/unit.

### 4.2 Financial Modeling Desk
**Inputs:** the reconciled GL trial balance (§4.1) plus, if available, an existing BI semantic model as a cross-check (not a data source of record).
**Build:** 3-statement (articulating, balances), DCF (with a WACC × growth sensitivity grid), trading comps (pull a peer set for the sector/geography, apply a size/illiquidity discount if the subject is materially smaller than listed peers), LBO (entry/exit multiple × leverage × IRR/MOIC sensitivity), a competitive-positioning tab, and a deck/model QC pass (formula errors, cross-tab link integrity).
**Deliverable:** an interactive workbench (tabs: Overview/3-Statement, DCF, Comps, LBO, Competitive, QC) plus an Excel workbook with a clear color convention (input / formula / cross-tab link / key assumption) and zero formula errors.
**Caveat pattern:** if a BI tool's own indirect cash-flow measures don't reconcile standalone (e.g. because opening balances are zero in a migration year), rebuild cash flow cleanly from balance-sheet deltas instead of surfacing the unreliable measure.

### 4.3 CFO Command Center
**Structure:** a data-availability map first (what EXSYS actually holds vs. what's requested — mark Budget/Forecast etc. as unavailable rather than fabricating), then a KPI semantic layer (name · definition · formula · source table · period · aggregation, one row per KPI, grouped Profitability / Liquidity / Working Capital / Performance), then the dashboard itself.
**Recommended tabs:** Executive Summary (KPI cards with trend + driver cards), P&L & Drill-down (statement vs. a stated baseline, with a department→cost-center→account→transaction drill), Cash & Treasury, Working Capital (DSO/DIO/DPO/CCC with visible formulas), Budget vs Actual (framework only if source is empty — auto-populates once loaded), Anomalies & Risks (with editable materiality thresholds), Ask-the-CFO (answers structured as summary · key numbers · risk · action · data quality, from live GL only).
**Anomaly-flagging habits worth repeating:** posting-lag artifacts (expense posted before matching revenue in the most recent open period — exclude that period from trend, note why), unposted depreciation/zakat vs. prior year, related-party balances material relative to total assets, single-payer receivables concentration, thin cash-cover ratio, YoY swings large enough to suggest a reclassification rather than real change (verify before quoting externally).

### 4.4 Cash Flow & Deep Analysis
**Method:** indirect cash flow rebuilt from balance-sheet movement (prior-year close → current) plus YTD P&L, not from a possibly-unreliable BI cash-flow measure. Validate the result ties to the actual cash-account movement within a small tolerance.
**Deep-analysis lens:** DuPont ROE decomposition (margin × asset turnover × equity multiplier), margin-compression trend, leverage trend (net debt/EBITDA), working-capital drag (AR/inventory growth vs. revenue growth, payer-mix shift), and a running quality-of-earnings watch-list.

### 4.5 Department & Cost Center Assessment
**Logic:** revenue by org (cash vs. credit account ranges — confirm the site's own account numbers) plus total expense booked to that org, grouped by the confirmed department-parent level and by individual cost-center org. Margin shown should be **contribution** before unallocated central overhead, stated as such. Overhead-only orgs (G&A, non-medical, support) will legitimately run negative contribution — that's by design, not a finding.
**Time intelligence:** YTD / specific month / prior full year, compare vs. prior year (annualized if the prior year's activity is lumped into one migration period) or vs. prior month. State plainly when a fiscal year has no real monthly detail because of a data-migration lump.

### 4.6 Inventory schema map + Inventory Analysis/Audit
**Key objects:** `IM_PRODUCT_MASTER` (+`IM_PRODUCT_UOMS`, `IM_PRODUCT_CATEGORIES` for the GL account map), `IM_STORE` (store/warehouse per org), `IM_STORE_PRODUCTS` (maintained balance — verify populated) vs. `VINV_QTY_STORE` (transaction-derived balance — usually the reliable one), `IM_ALL_TRANSACTIONS` (the single movement spine: date, org, store, product, batch, expiry, action type, status, qty, cost, source document type/id), `IM_STORE_PRODUCT_BATCHS` (batch-level balance, if populated), `IM_PURCHASE_INVOICE_M/D` (receipts — apply the two costing corrections from §2), `IM_STOCK_ADJUSTMENTS_M/D`, `IM_STOCK_COUNT_M/D`.
**Standing checks to rebuild, in priority order:**
1. Valuation & position — value on hand by store, off the transaction-derived balance.
2. Overstock — days-of-cover from actual trailing consumption (exclude the receiving-error/outlier guard, see §2), not the ERP's raw MIN/MAX default.
3. Slow-moving/dead stock — no outbound movement in N days (90 is a reasonable starting window); treat as an overlapping but distinct watchlist from #2.
4. Expiry risk — nearest upcoming expiry from receipt-line proxy (or true batch data if tracking is on) inside a per-product or default window.
5. Data-quality/loss-control — flag outlier single-line quantities at receiving (e.g. >20× a product's trailing average receipt) same-day, not just retroactively.
6. Cross-org/department peer audit — compare days-of-cover and overstock-% across peer orgs sharing a department ancestor, normalized by outbound volume; needs 2+ active peer orgs to be meaningful.
7. Dispense by cost center — monthly qty/cost trend per store/cost-center, with period-over-period and (once 2 years of history exist) YoY comparison.
8. Purchases by supplier — best-cost-by-supplier and cheapest/most-expensive price paid, computed only after netting discount and normalizing UOM (§2), with the outlier-excluded "clean" ranking shown separately from the full unfiltered matrix (which keeps flagged lines visible with a warning badge rather than hiding them).

### 4.7 NPHIES RCM Audit (only where NPHIES/insurance billing is live)
**Key objects:** `RC_SERVICES`, `RC_PATIENT_MEDICATION_ORDER_MV`, `RC_PATIENT_DIAGNOSIS_MV`, `RC_PATIENT_READINGS` (vitals), `RC_CONTRACTS`, `RC_PATIENT_CONTRACTS` (`PATIENT_CARD_NO`), `RC_PATIENTS`, `RC_CLINICAL_REQUEST_DETAILS`, `CUSTOMER_GROUPS`, `MR_PATIENT_VISITS`, `MR_PATIENT_CHRONIC_DETAILS`, `HS_NPHIES_PBM_REQUEST(_DTL)`, `DOCTOR_COMMISSION_DATA` (invoiced sales lines), `PH_SFDA_PRODUCTS` (ATC codes), plus reference tables `HS_NPHIES_ICD_DRUG_CROSSMATCH` / `PH_ICD_CHI_GENERIC_CROSSMATCH` — check these for emptiness before depending on them (see §2).
**Tabs to rebuild, each independently gated by whatever data actually exists at the new site:**
- **Diagnosis ↔ Service/Medication coding gaps** — flag episodes with medications/services but zero coded diagnosis.
- **Inactive/invalid ICD codes** — diagnoses coded against an inactive or invalid ICD entry.
- **Financial/statement mismatches** — SOA/claim financial inconsistencies.
- **Patient data consistency (vitals)** — implausible single readings (temperature, BP, pulse, SpO2, height, respiratory rate — set plausibility ranges from real data sampling, watch for sentinel values) plus within-patient adult-height drift over a lookback window (with an adult-only floor to exclude pediatric growth and sentinel noise).
- **Fraud-probability screening** — one insurance card number linked to more than one patient file, scored by how many identity attributes (gender, DOB, nationality) diverge across those files; band the score (e.g. Duplicate-file / Low / Medium / High) and frame every hit as needing manual ID verification, never as a determination.
- **SFDA pricing compliance** — invoiced drug unit price vs. the SFDA public reference price (via `SFDA_CODE`, matched against current or old register number), variance and revenue/compliance impact both ways (over- and under-priced).
- **SFDA code currency** — active drug catalog classified Active / Needs Code Update (matches only an old register number) / Not Found, as a ready ERP-cleanup list.
- **PBM pre-authorization status** — approved/rejected/pending/error outcomes on pharmacy pre-auth requests; if the channel is barely used or errors out entirely at a given site, say that plainly rather than showing a misleadingly sparse or empty tab.
- **Diagnosis appropriateness / medication necessity** — map each dispensed drug to a therapeutic class (ATC code first, brand/keyword dictionary fallback) and check whether the episode's diagnoses include an accepted indication for that class; ship **two rule-books** (a balanced "curated" one and a tighter "strict" one that also assesses supplements) since crossmatch reference tables are usually empty; always frame a flag as a documentation/necessity screening signal.
- **Drug–drug interaction screening** — pairwise-screen every multi-medication episode against a severity-tiered (contraindicated/major/moderate/minor) interaction rule table, tagging each drug by active-ingredient/class and staying route-aware (topical/local forms shouldn't trigger systemic-interaction flags); state the rule table's provenance (e.g. modeled on a licensed database's structure when the licensed data itself isn't reachable) in the methodology note.
**Cross-cutting UX pattern worth repeating:** a global payment-type filter (Cash/Credit/Discounted-cash/All) applied per-tab using the best available payment-type signal for that tab (true invoice payment type on billed tabs, contract-customer-group inference on clinical/pre-billing tabs, "always shown" on payer-neutral tabs) — document the scope honestly per tab rather than pretending uniform coverage.

### 4.8 Peer Operating Benchmarks
When a market-data connector isn't available, build this from public sources (peer company annual reports, earnings calls, analyst initiations, exchange filings) — capacity/expansion plans, growth, leverage, forward multiples — and cite the public sources used. Position the subject honestly against peers (e.g. single-site outpatient vs. multi-hospital operators is a structural, not like-for-like, comparison) and apply/carry forward any size or liquidity discount already used in the comps/DCF work.

### 4.9 Clinical Audit Agent (optional companion skill)
A per-claim, on-demand skill (not a dashboard tab): given one episode/invoice/claim reference, pull that claim's full clinical and billing picture (demographics, chronic history, chief complaint, all vitals, diagnoses + ICD validity, services, medications + dosage narrative, SOA financials, prior related claims) and return a structured audit report (consistency matrix, lab/radiology/procedure/medication audit, drug-interaction analysis, missing-documentation list, billing/coding issues, key findings). Carry the same safety rails as the dashboard modules: never invent patient data, state "insufficient information" when data is missing, never conclude fraud or output a reject decision, never treat cost alone as evidence of unnecessary care, keep clinical concerns separate from coding/documentation concerns, and always escalate to physician/coder review.

## 5. Deliverable & refresh conventions

- **Two parallel deliverables per module family**: an interactive HTML dashboard/workbench (published so it's revisitable and shareable) and an Excel workbook with live formulas, a Methodology sheet documenting sources/logic/caveats, and a Summary sheet with severity/KPI rollups.
- **A build pipeline script per module** that re-runs the SQL, rebuilds the JSON/data objects, and regenerates both deliverables byte-for-byte reproducibly — this is what a scheduled daily/periodic refresh task calls.
- **Pagination discipline** for any pull that can exceed the row cap: page sequentially (or at very low concurrency) with a stable order key so pages tile without gaps or overlap, and dedupe on rebuild.
- **Never surface the raw DB host/IP** in any UI or workbook — use a neutral source label.
- **Log every data-quality finding as a numbered, reusable finding** (as this project's own source docs do) so the next person building on top of the same table doesn't rediscover the same gotcha the hard way.

## 6. Step-by-step checklist for a brand-new EXSYS site

1. Confirm read-only Savan-style Oracle access to the new site's EXSYS instance; capture DSN/schema/user.
2. Run a discovery pass: list schemas/objects, describe the core tables (`GL_ACCOUNT`, `GL_TRANSACTIONS_VIEW`, `PERIODS`, `ORGANIZATIONS`, and — if in scope — the `IM_*` and `RC_*`/`HS_NPHIES_*` families), and `preview_table` each one before writing a query against it.
3. Re-verify every item in §2 against this site specifically (don't inherit the source sites' numbers/patterns without checking).
4. Build and reconcile the GL Source-Direct trial balance (§4.1) to zero variance.
5. Build the Financial Modeling Desk and CFO Command Center (§4.2–4.3) on top of the reconciled GL.
6. Build Cash Flow & Deep Analysis and Department Assessment (§4.4–4.5).
7. If inventory is in scope: build the schema map, then the Inventory Analysis/Audit standing checks (§4.6), applying the purchase-costing corrections before any supplier comparison.
8. If NPHIES/insurance billing is in scope: build the RCM Audit tabs (§4.7) one at a time, gating each on whether its source data actually exists at this site.
9. Add Peer Operating Benchmarks (§4.8) from public sources if a market-data connector isn't available.
10. Offer the Clinical Audit Agent (§4.9) as a companion per-claim skill if RCM is in scope.
11. Wire up a scheduled refresh (daily or as appropriate) that reruns the build pipeline(s) and republishes both the dashboard(s) and workbook(s); point it at the new site's own output folder.
12. Before sharing anything externally, re-read §0's non-negotiable principles against the finished deliverable — no invented numbers, every flag framed as a screening signal, every known data gap stated in-tab, no raw host/IP visible anywhere.