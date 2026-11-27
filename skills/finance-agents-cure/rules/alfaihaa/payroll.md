# Payroll, HR letters and doctors' commission rules (Al Faihaa)

## Letters
- A letter whose file name says ملغي / يلغي / يلغى is void — never applied. A replacement is its own file.
- Decisions go in Cure screen PRBTCTRX, leaves in HR_STFVC, staff file HR_ASTAF, salary items HRSTFSAL, loans HRSTFLON (PR_STAFF_LOANS / _INSTALLMENTS).
- Work-start letters set the contract start; also check nationality (insurance deduction), ID number and bank details.
- 31-day months: a returning / new employee gets a one-time day-31 entitlement (Cure treats months as 30 days).
- Retroactive raises are often paid by JV on the employee GL sub-account (sub-account no. = staff no.) — check there before flagging a missing arrears item.
- A retro letter can be deducted in the current month if not deducted before; a future-dated one is deferred and tracked until its month runs.
- Leave deduction is on the ACTUAL return date, not the planned dates.
- A JV debiting 2121001 / crediting 2121009 for the same amount is a reclassification, not a double accrual.
- End-of-service settlements are the full award unless HR states a resignation share.

## Doctors' commission
- Paid one month late (September with October salary).
- Doctor revenue: patient invoices net of the month's refunds, after discounts, without VAT; pharmacy sales never count. Cash = cash + discounted cash; credit = insurance, including the patient share collected from insured patients. Source report: RCDOCREP.
- Doctors paid on cash only: credit differences are not a finding.
- Radiology revenue goes to the radiologist who wrote the report; lab revenue (and package lab revenue, shown as zero by a program error) goes to the lab doctor; cupping revenue is subtracted from the cupping doctor's cash revenue.
- Working days for doctors on leave = days of month − Cure leave days. Old sheets may code doctors by clinic number: map to staff IDs.

## Added after the 2026-10 run
- The doctors' commission accrual for month M is usually booked around the 22nd of M+1. If it is missing when the review runs, it is a close blocker (`blocks_close`), not a booking error; re-check after that date.
- Day-31 entitlement: Cure pays it to employees who start OR resume work (return from leave) during a 31-day month; paying it to someone still on leave until month end is a finding.
- Loan / advance accounts are compared on the consolidated balance of all branches.
