# Monthly letters review (HR administrative decisions, leave and dues settlements)

Companion to the dashboard. Each month the payroll team checks every letter in the month's folder against Cure. Rules below are Hany's standing rules (Sep and Oct 2026). Output of the reference run: `Admin_Decisions_Review_Sep2026_v2.xlsx`, `HR_Vacation_Letter_Audit_Sep2026.xlsx`, `Settlement_Letters_Review_Sep2026.xlsx` in this folder.

## Where the letters are
Accounts share, Payroll, "القرارت الادارية والأجازات اعتبارا من 01-03-2024", split by year, then month, then day folders. A new company needs its own path in the project doc.

## Where each letter type is recorded in Cure
| Letter | Cure screen | Table |
|---|---|---|
| Penalties, hourly permissions, allowances, deductions | PRBTCTRX (addition and deduction by item) | `PR_STAFF_ADDING`; hourly items all use item -7 |
| Leaves | HR_STFVC | `PS_STAFF_VACATIONS` (POST_FLAG C cancelled, P posted) |
| New hire (work-start letter) | HR_ASTAF (file), HRSTFSAL (salary) | `STAFF_MASTER`, `PS_STAFF_CONTRACT`, `PS_STAFF_IDS`, `PR_STAFF_DEFAULT_SALARY_M/_D` |
| Loan or advance | HRSTFLON | `PR_STAFF_LOANS`, `PR_STAFF_LOANS_INSTALLMENTS` |
| Dues settlement ("حساب مستحقات موظف") | Manual journal on the staff sub-account | `GL_TRANSACTIONS_DETAILS` (sub-account = staff number) |

## Standing rules
1. Decisions never go on the leave screen and leaves never go on the decisions screen.
2. Retroactive raise or entitlement differences are often accrued and paid directly in the GL (a JV on the employee's sub-account). Check the GL before flagging missing arrears.
3. A retroactive letter can be deducted in the current month if it was never deducted (letters arrive after the month's salary is paid). A future-dated letter waits for its month and goes on the **future-month tracker**; when that month's payroll runs, verify the deduction or activate the raise.
4. New hire checklist: contract start equals the letter date; nationality (Saudi = 420, affects insurance); ID type (N national, I iqama) and number; IBAN and bank digit for digit; salary items in HRSTFSAL; a one-time day-31 entitlement (item 28) in 31-day months because Cure treats every month as 30 days.
5. Filipino work-start letters carry a USD advance converted to SAR. A loan must exist on HRSTFLON for the months and amounts stated. A later loan starts after the last month of the current loan. If work starts after the 15th, the loan starts the next month.
6. GL balances: STATUS P only; open (O) rows are entered but not posted.

## Settlement calculation method
- Daily wage = monthly salary divided by 30. Salary to the last working day = days times daily wage, less staff insurance pro rata and any visa or re-entry fees ticked.
- Leave pay = entitlement days times daily wage. Entitlement days = 21 per year times the period divided by 365 (30 per year for ten years or more, or a special contract). It must equal `PS_STAFF_VACATION_ALLOWANCE`. Housing paid in kind is deducted.
- End of service = half a month of basic per year for the first five years, plus a full month per year beyond. Resignation before five years reduces it. `PR_END_OF_SERVICE` is not used; the award is a manual JV against provision 2111001.
- Settlement JV: credit 2121001 (accruals) and debit 2111003 (leave provision) or 2111001 (EOSB provision); payment debits 2121001 and credits the bank.
- The payroll run skips staff whose leave crosses month end ("لم يسجل تاريخ العودة من الاجازة"), so salary to the last day must be settled by hand. A leave inside one month is handled as an absence deduction.

## Output of each review
A workbook with: summary (counts by status), per-letter results (staff, letter items, expected, Cure value, status, note), the calculation sheet with live formulas, open items, and the future-month tracker. Statuses used: matches, matches with a note, error, missing entry, deferred to a later month, could not be matched, needs a decision.

## Open items carried from the September 2026 settlement review
3159, 6008, 4382, 6012, 6321, 4023, 6398 (missing or wrong entries); 3106, 4052, 3160 (decisions needed); open vouchers JV1-26/02449, 02450, 02454, 02463, 02664; future-month tracker 6344 and 7014 (and 3176, 4299 to check in October payroll).

## Leave movement review method (Hany, 27 Oct 2026)
1. Open the attachment (letter) of each record on the leave movement screen and check every figure it carries: hours deducted, penalties, leave dates and return date. Hour deductions and penalties must exist as item -7 lines at item level.
2. Leave deduction follows the ACTUAL return date, not the planned one. Example: leave 1-18 Oct, actual return 26 Oct: the days to deduct are the real absence days. Compare the actual return date (`ACTUAL_RETURN_DATE`) with the letter and with the deduction in the payroll draft.
3. Make sure no letter in the administrative decisions folder is missing a movement in Cure (leave, item or decision). List letters with no movement as errors.
4. Do not call a journal a double accrual until you read it. A journal that debits 2121001 (employee dues payable, ذمم عاملين مستحقة) and credits 2121009 (miscellaneous employee dues, مستحقات موظفين متنوعة) for the same amount is a reclassification: the automatic payment entry pays from 2121001, so accounts put the amount there first. Example: JV1-26/02290.
5. Dues settlements (حساب مستحقات الموظفين) are based on the end-of-service award. Unless the HR manager writes that it is a resignation and states what share of the award is paid, treat it as the full award. Do not raise a note only because the letter does not mention the award or the reason.
