# Standing the HR Command Center up at another company

Work through the list in order. Each item names what to run and what a good answer looks like. Anything that does not match Al Faihaa goes into `config/company.<co>.json` or, if it needs new logic, into `SPEC.md` section 8.

## A. Connection and schema
1. `cure_branch_status`: list the branch parameters. Test `SELECT COUNT(*) FROM PR_SALARY_TRANSACTION_M` on each; the database with rows is the payroll database (`cure.hr_branch_param`).
2. Test whether the schema needs a prefix (`EXSYS.`) on that branch (`cure.schema_prefix`; empty string if not).
3. `cure_describe_table` on `PS_STAFF_CONTRACT`, `STAFF_MASTER`, `PR_SALARY_TRANSACTION_M`, `_D`, `PS_STAFF_VACATIONS`, `PR_STAFF_LOANS`, `PR_STAFF_LOANS_INSTALLMENTS`, `PS_STAFF_IDS`, `PR_SALARY_ITEM`, `CODES_MASTER`. Column names in `sql/` must exist; a missing one means a different EXSYS version.

## B. Definitions to confirm with the HR manager
4. Active staff rule: count `STATUS='A' AND CURRENT_CONTRACT='Y'` and compare with the headcount HR quotes. A gap means a different rule.
5. Blank contract end dates: run `hr10`. Rows with `BLANK` are open-ended; confirm they are permanent contracts.
6. Saudi nationality code: look up `CODES_MASTER` type 105 (`saudi_nationality_code`).
7. Branches: list the first two characters of `ORGANIZATION_NO` for current jobs and name each prefix (`branches`).
8. Job titles: confirm `CODES_MASTER` type 250 holds them (`GS_JOBS` was empty at Al Faihaa).
9. Leave types: run `hr13`, then ask HR what each `VACATION_TYPE` code means. Put the long and short codes and their names in `leave_types` and `leave_labels`.
10. Loan installment statuses: confirm P, R, N with payroll (`loan_status_note`).
11. Identity document type codes: list `ID_TYPE_CODE` in `PS_STAFF_IDS` with `CODES_MASTER`; set `id_types_residence` and `id_type_passport`. Check how many staff have an expiry date before trusting the expiry flags.
12. Housing and transport salary item numbers (`eosb_housing_transport_items`) from `PR_SALARY_ITEM`.
13. GL accounts for end-of-service provision, leave provision and employee payables (`accounts`). Check each has posted entries.
14. Leavers: check whether `SEPARATED_DATE` is filled. If it is, switch `hr08` to it and set `leaverMethod`.

## C. Run and compare
15. Render, run, ingest and build as in the runbook. Fix failed gates first.
16. For every flag, re-query the evidence once. Remove or re-word any rule that does not fit the company (for example the Saudization rule, the licence rule for a non-clinical business).
17. Compare the total payroll with the GL salary expense for one month. They should agree within the known timing differences.

## D. Company text
18. Edit `config/playbook.json` (calendar, checklist, best-practice cards) for the company's own cycle, laws and owners.
19. Set `owners`, `plan_defaults` and `thresholds` to what the company agrees.
19a. Arabic: fill `company_ar`, `scope_ar`, `leave_labels_ar`, `loan_status_note_ar` and `owners_ar` in the company config, and add the company's job, branch and item names to `config/labels_ar.json`. A missing translation shows the English name.
19b. Payroll notes: start the new company with an empty register (copy `data/payroll_notes.json`, keep `cats` and `sources`, set `notes` to `[]` and clear `reviews` and `tables`) and add its own notes with `scripts/notes_tool.py add`. Do not ship Al Faihaa's notes to another company.

## E. Publish and record
20. Publish the page, save the standalone copy, write the project doc with the baseline figures (use `docs/BASELINE_ALFAIHAA_2026-10-12.md` as the model) and list open questions for the client.
