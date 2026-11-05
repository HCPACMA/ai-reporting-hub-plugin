-- Salary item mix of the last closed month ({LASTY}/{LASTM}). Columns: si, en, sg, n, amt
-- Tie: sum(amt) per sign = the + and - totals of hr05b for that month. Item -1 is loans.
SELECT d.SALARY_ITEM SI, MAX(i.DESCRIPTION_P) EN, d.SALARY_ITEM_SIGN SG, COUNT(*) N, ROUND(SUM(d.ITEM_AMOUNT)) AMT FROM {P}PR_SALARY_TRANSACTION_D d LEFT JOIN {P}PR_SALARY_ITEM i ON i.SALARY_ITEM=d.SALARY_ITEM WHERE d.YEAR_SALAR={LASTY} AND d.MONTH_SALRY={LASTM} GROUP BY d.SALARY_ITEM, d.SALARY_ITEM_SIGN ORDER BY 5 DESC
