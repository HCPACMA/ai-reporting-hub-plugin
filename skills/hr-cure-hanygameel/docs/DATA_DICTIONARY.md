# Data dictionary (Cure / EXSYS, HR and payroll)

Verified at Al Faihaa on 12 Oct 2026. Re-verify columns at a new site with `cure_describe_table`.

## Staff and contracts
| Table | Use | Notes |
|---|---|---|
| `STAFF_MASTER` | One row per person: names (`STAFF_NAME_1_P`.. and `_S`), `SEX`, `DATE_OF_BIRTH`, `NATIONALITY_CODE`, `EMAIL`, `LICENSE_ID`, `DATE_START_SERVICE` | There is no `STAFF_NAME` column. `LICENSE_ID` and `DATE_START_SERVICE` are blank for every active employee at Al Faihaa |
| `PS_STAFF_CONTRACT` | Contracts: `START_DATE`, `END_DATE`, `STATUS` (A active, I inactive), `CURRENT_CONTRACT` (Y/N), `CONTRACT_ID`, `SEPARATED_FROM_WORK`, `SEPARATED_DATE`, `END_OF_SERVICE_*`, `GOSI_DATE`, `TEST_PERIOD_DAYS` | Active staff = A and Y (385). `END_DATE` blank = open-ended. 154 inactive staff carry a future `END_DATE` (left early) |
| `PS_CONTRACTS` | Contract types that drive leave entitlement (21, 30, 42 or 60 days; 1-year Saudi, 2-year non-Saudi) | |
| `PS_STAFF_INTERNAL_TRANSFERS` | Job, department, `ORGANIZATION_NO` per period; `CURRENT_JOB='Y'` is the current one | Branch = first two characters of `ORGANIZATION_NO` |
| `PS_STAFF_IDS` | Identity documents: `ID_TYPE_CODE` (I iqama, N national ID, B border ID, P passport), `ID_NO`, `ID_WHEN_EXPIRED` | `ID_CURRENT` is 'Y' for 5 rows only; ignore it |
| `CODES_MASTER` | Lookups: type 105 nationalities, type 250 job titles (`USER_CODE` = `STAFF_JOB_ID`), type 335 end-of-service reasons | Columns `CODE_NO`, `USER_CODE`, `CODE_TYPE`, `DESCRIPTION` |
| `ORGANIZATIONS` | Org tree: `ORGANIZATION_NO`, `ORGANIZATION_NO_PARENT`, `DESCRIPTION_P/_S` | The `cure_organizations` tool failed with ORA-00904; query the table |

## Payroll
| Table | Use | Notes |
|---|---|---|
| `PR_STAFF_DEFAULT_SALARY_M` / `_D` | Current salary package: basic and fixed items, open record has `DATE_END IS NULL` | |
| `PR_SALARY_TRANSACTION_M` | Monthly header per staff: `BASIC_SALARY`, `ABSENCE_DEDUCTION`, `OVERTIME_AMOUNT`, `SOCIAL_INSURANCE_COMPANY/_STAFF`, `STATUS` (P posted, O open) | Draft month = latest month with all rows open |
| `PR_SALARY_TRANSACTION_D` | Monthly items: `SALARY_ITEM`, `SALARY_ITEM_SIGN` (+/-), `ITEM_AMOUNT` | No basic salary here |
| `PR_SALARY_ITEM` | Item names `DESCRIPTION_P/_S`, accounts | Items at Al Faihaa: 1 housing, 2 transport, 9 others, 13 other deductions, 16 shortage, 18 percentage of doctors, 21 instead of Friday, 22 food, 24 one-time accruals, 26 lump sum, 27 bank fees, 28 day-31 accrual, -1 loans, -7 hourly decisions |
| `PR_STAFF_ADDING` | Additions and decisions per item (screen PRBTCTRX) | Hourly items all use -7 |
| `PR_STAFF_LOANS` / `_INSTALLMENTS` | Loans (`LOAN_STATUS`: P posted, C cancelled, O open) and installments (`INSTALLMENT_STATUS`: P paid, R rescheduled, N pending) | Screen HRSTFLON |
| `PR_END_OF_SERVICE` | Not used since 2021; awards are manual journals against the provision | |

## Leave
| Table | Use | Notes |
|---|---|---|
| `PS_STAFF_VACATIONS` | Leave records (screen HR_STFVC): `VACATION_TYPE`, `DATE_FROM/TO`, `VACATION_NO_OF_DAY`, `POST_FLAG` (P/C/O) | Type 17 long (avg 17 days), type 09 short (avg 2.4 days) at Al Faihaa |
| `PS_ACCUMULATED_ANNUAL_VACATION`, `PS_STAFF_VACATION_ALLOWANCE` | Leave balances and leave-pay records | Leave pay = entitlement days times daily wage |

## General ledger
`GL_TRANSACTIONS_DETAILS`: `ACCOUNT_NO`, `SUB_ACCOUNT_NO` (staff number for employee accounts), `STATUS` (P posted, O open, C cancelled), `DR_AMOUNT`, `CR_AMOUNT`, `DESCRIPTION`, `VOUCHER_NO`, `COST_CENTER_NO`. No `NOTES`, `DEBIT` or `CREDIT` columns. Accounts: 2121001 employee payables, 2111003 leave provision, 2111001 end-of-service provision (no sub-account).
