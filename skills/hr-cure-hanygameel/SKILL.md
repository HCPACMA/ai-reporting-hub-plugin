---
name: "hr-cure-hanygameel"
description: "Build, refresh or extend Hany Gameel's HR Command Center for any EXSYS (Cure) ERP company: animated HR dashboards, deep-analysis tabs, an evidence-based audit register (payroll, contracts, leave, loans, end-of-service, identity documents, master data) and a workforce plan, all pulled read-only from the Cure database through the Cure MCP, plus the review of HR administrative-decision, leave and dues-settlement letters against payroll."
---

# HR-Cure (Hany Gameel)

Rebuilds the Al Faihaa HR Command Center for an EXSYS (Cure) database. Everything comes from `cure_run_query` (SELECT only). The kit lives on the finance PC at `D:\Financial Management\Financial Report\AI Reporting HUB\HR\HR-Cure-Kit\`; `SPEC.md` is the full specification and the project doc `claude/hr-command-center-artifact.md` carries the latest figures.

## Workflow

1. **Discover the company.** `cure_branch_status` for branch parameters; find the database that holds payroll (`PR_SALARY_TRANSACTION_M` has rows). Confirm the schema prefix, the Saudi nationality code, the cost-centre prefixes per branch, the GL accounts for end-of-service, leave provision and employee payables, the leave type codes, and the identity document type codes. Fill `config/company.<co>.json` (see `ADAPTATION_CHECKLIST.md`).
2. **Render and run the jobs.** `scripts/render_sql.py` fills `sql/hr01a ... hr17`. Send each file to `cure_run_query` and save the reply as `raw/<job>.txt`. The tool rejects text containing UPDATE, CREATE, TRUNCATE or WITH.
3. **Ingest and build.** `scripts/ingest.py` then `scripts/build_hr.py`. A failed gate stops the build. Read `out/build.md`.
4. **Check by hand.** Re-query each headline number once (headcount, last-month gross, GL provision, open payroll rows). Never publish a flag whose evidence you have not seen in Cure.
4a. **Payroll notes.** The page carries a payroll notes register (`data/payroll_notes.json`). Before building, close what is fixed and add the new month's findings with `scripts/notes_tool.py`; open notes move to the next month automatically. Every note and every finding needs English and Arabic text.
5. **Publish.** Load `artifact-design` and `dataviz`, publish `out/HR_Command_Center.artifact.html` with the Artifact tool (same URL on refresh), copy the standalone page to the HR folder, update the project doc.

## Rules that must hold

- Active staff: contract status A and current. Branch from the cost-centre prefix of the current job.
- A blank contract end date is an open-ended contract, never an expired one.
- Loan installment status: P paid, R rescheduled, N pending. Only N is owed.
- Gross pay = payroll header basic + `+` items of the detail table. Draft month (all rows open) is excluded from trends.
- GL balances: STATUS P only.
- Keep residence documents and passports apart; never take a maximum across all document types.
- Keep result cells as text when parsing: codes like `00` and `09` are not numbers.

## Page layout and languages

Left sidebar with groups and sub tabs; Arabic (RTL), English or both, switched in the sidebar. All fixed text sits in the template dictionary; generated text is `{en, ar}` from `build_hr.py`; Cure data labels use `config/labels_ar.json`. Run `tests/run_tests.py` (it clicks every page in the three languages) before publishing.

## Letters review (monthly, separate from the dashboard)

See `docs/LETTERS_REVIEW_PLAYBOOK.md`: decisions go on PRBTCTRX, leaves on HR_STFVC, retro differences are often accrued in the GL, future-dated letters wait in a tracker, Filipino work-start letters need a loan record, and the settlement calculation method with its formulas.

## Files

`SPEC.md` specification and traps · `REFRESH_RUNBOOK.md` monthly steps · `ADAPTATION_CHECKLIST.md` new company · `docs/DATA_DICTIONARY.md` tables and lookups · `docs/LETTERS_REVIEW_PLAYBOOK.md` letters rules · `docs/BASELINE_ALFAIHAA_2026-10-12.md` reference figures · `config/`, `sql/`, `scripts/`, `templates/`, `tests/`.
