# Payroll notes register

The register holds every payroll exception found in the letters reviews. It is the file `data/payroll_notes.json` and the page group "Payroll notes".

## What goes in a note

One exception, one note: an employee or a group, what was found in Cure or in the letter, what to do, who owns it. Priority H, M or L; I is information only. Category (`cats`) and source (`sources`, the review and its workbook). Amount in SAR when there is one.

## Month to month

A note belongs to the month it was found in (`month`). It stays open and appears in every later month until it is closed with `closedIn`. The new month therefore starts with what is still pending, and the page labels each note New or Carried from <month>. Notes of status `info` (checked and fine) stay in their own month only.

## Sources loaded for September 2026 (reviewed 4 to 8 Oct 2026)

| Source | Workbook | Notes |
|---|---|---|
| Administrative decisions review (letters 31-08 to 27-09, 196 rows) | Admin_Decisions_Review_Sep2026_v2.xlsx | A01 to A30 |
| Dues settlement letters (31 letters) | Settlement_Letters_Review_Sep2026.xlsx | S01 to S15 |
| Leave letters against Cure (344 transactions since 30 Mar 2026) | HR_Vacation_Letter_Audit_Sep2026.xlsx | V01 to V06 |
| Later-dated letters tracker | Admin_Decisions_Review_Sep2026_v2.xlsx | F01 to F09 (October) |

The tracker and Filipino loan tables in `tables`, and the outcome counts in `reviews`, are copied from the same workbooks.

## Maintaining it

`python3 scripts/notes_tool.py list --month 2026-10` · `close A01 --month 2026-10` · `reopen A01` · `add ...` · `apply changes.json`. Run `build_hr.py` afterwards; the build fails if a note lacks English or Arabic text, has an unknown category or source, or is closed without a month.

## v4 additions (2026-10-13)
- Every note carries `people[{code,name,paths[{rel,win,lbl}]}]` (scripts/notes_people.py, from data/letters_index.json made on the PC). Notes without a staff number use a `ppl` hint; no-letter records are `nopath`. The build gate fails if a note has no code, name and path (or nopath).
- GOSI/travel check: scripts/gosi_check.py (4 comparisons per employee + travel report), scripts/gosi_excel.py (workbook). Inputs: accounts payroll xls, GOSI CSVs (company + 4 branches), previous-month GOSI invoice (employee rate), travel xlsx, Cure payroll lines (raw/hr18a/b, hr19, hr20 – run by hand as SELECT queries for now).
- Page: sidebar on the right in Arabic/both; group "التأمينات والسفر".

## Pre-payroll payment page (2026-10-13)
- scripts/prepay_check.py checks the draft payroll of the next month (raw/hr21_oct_draft.txt: staff|basic|plus|minus|social salary|social deduction) against open leaves (raw/hr22_open_leaves.txt: POST_FLAG P/O with ACTUAL_RETURN_DATE empty), the travel report and GOSI. Output data/prepay.json; config/prepay_exceptions.json holds accepted exceptions.
- Rules: a salary is held if the employee is outside the Kingdom or has a posted leave (P) without a recorded return (HRVCRTRN); not in GOSI and unposted leave (O, this year) are warnings. Employees with an open leave and zero draft pay are listed as held correctly.
- SQL used (Riyadh): draft = PR_SALARY_TRANSACTION_M (+ _D sums by SALARY_ITEM_SIGN) for YEAR_SALAR/MONTH_SALRY; leaves = PS_STAFF_VACATIONS. Re-run both after every recalculation of the draft.
- Cost-centre exemption (2026-10-14): staff whose current organization (PS_STAFF_INTERNAL_TRANSFERS.ORGANIZATION_NO, CURRENT_JOB='Y') starts with 0002 are exempt from the "not registered in GOSI" note, on both the pre-payroll and GOSI pages. Configure in config/prepay_exceptions.json (_cost_centre_exempt) and pass raw/hr23_cost_centres_*.txt via --cc.

## Nurses per doctor and leave days (2026-10-14)
- Tab "الممرضات مع الأطباء" (`#nursing`): doctor, nurse count, click a row for nurses (job code, name, total salary). Link = same clinic cost centre (RC_CLINICAL_ENTITIES_NURSE, RC_DOCTOR_ORGANIZERS_LINK are empty in Cure). Rules in `config/jobs_depts.json`: doctor jobs, nurse jobs (102 midwife, N nurse, 223 private duty), max 2 nurses per doctor, jobs expected to have no clinic nurse (157 radiology, 158 lab, 101 administrative) and any department level cost centre.
- Statuses: none (action), none_ok (expected), extra (above max x doctors sharing the cost centre), ok. Nurses outside a doctor clinic: admin (charged to 001-004), nodoc (clinic has no active doctor), dept (emergency, home care, lab, radiology).
- Leave page now has days by branch, department, job and employee, default scope doctors. Types 03 sick, 09 emergency, 17 (named Unpaid Vacation in Cure, carries most days). Posted days only, open apart.
- Refresh: run sql/hr24, hr25, hr26 through cure_run_query into raw/hr24_doc_nurse.txt, hr25_org_names.txt, hr26_leave_days_2026.txt, then `python3 scripts/hr_extra.py`, then build.

## Month-level notes (Hany, 27 Oct 2026)
Every page and every note is judged within its own month. The notes page shows only the notes of the selected month; notes are no longer carried forward. The exception is decisions that concern a future period (category `fut`), which stay visible in later months until closed. Day-31 item (28) is judged only in 31-day months and only for staff who start work in that month.

## Branch rule (Hany, 28 Oct 2026)
The branch of an employee, and of any figure about him, is the branch of the cost centre linked to him (current job organization, first two characters of ORGANIZATION_NO): 00 head office and administration, 01 Riyadh, 02 Buraydah 1, 03 Buraydah 2, 04 Rafha. The GOSI file an employee sits in is a separate column; the GOSI page now filters on both (raw/hr32_staff_org.txt holds the staff to organization map).
