-- Salary items per month by sign (+ earnings, - deductions). Columns: y, m, sg, stf, amt
-- The detail table holds allowances and deductions only. Basic salary is in the header (hr05a). Gross = basic + the + items.
SELECT YEAR_SALAR Y, MONTH_SALRY M, SALARY_ITEM_SIGN SG, COUNT(DISTINCT STAFF_ID) STF, ROUND(SUM(ITEM_AMOUNT)) AMT FROM {P}PR_SALARY_TRANSACTION_D WHERE YEAR_SALAR*100+MONTH_SALRY>={FROM_YM} GROUP BY YEAR_SALAR, MONTH_SALRY, SALARY_ITEM_SIGN ORDER BY 1,2,3
