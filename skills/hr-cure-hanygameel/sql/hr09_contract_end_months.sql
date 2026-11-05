-- Active staff by contract end month (future and past). Columns: exp_y, n. Blank END_DATE is excluded; count it with hr10.
SELECT x.EXP_Y, COUNT(*) N FROM (SELECT TO_CHAR(c.END_DATE,'YYYY-MM') EXP_Y FROM {P}PS_STAFF_CONTRACT c WHERE c.STATUS='A' AND c.CURRENT_CONTRACT='Y' AND c.END_DATE IS NOT NULL) x GROUP BY x.EXP_Y ORDER BY 1
