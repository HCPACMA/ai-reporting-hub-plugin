-- Annual net movement per account, organisation function and voucher flag — the basis for the
-- income statement, the balance sheet (cumulative from the opening voucher) and the cash flow.
-- {P} = schema prefix ('EXSYS.' on Riyadh, '' on the branch databases). Run once per database.
-- Output rows: year|account|function|flag|amount   (amount = DR - CR)
--   function: COR / GA / INS / HO for expense accounts, '-' otherwise (organisation rules, see SPEC §3A)
--   flag:     F = a year-end closing voucher (FINANCIAL_YEARS.GL_VOUCHER_NO), X = JV1-24/04043, N = ordinary
-- Cancelled vouchers (STATUS='C') are excluded; posted and open vouchers are both kept.
-- LISTAGG caps a cell at 4,000 characters — keep about 60-70 packed rows per bucket and count the
-- rows that come back (the bucket count column) before using them.
SELECT bkt, COUNT(*) n, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (
 SELECT MOD(ROWNUM,{B}) bkt, y||'|'||a||'|'||f||'|'||fl||'|'||amt r FROM (
  SELECT EXTRACT(YEAR FROM t.VM_DATE) y, t.ACCOUNT_NO a,
    CASE WHEN SUBSTR(t.ACCOUNT_NO,1,1)<>'3' THEN '-'
         WHEN SUBSTR(t.COST_CENTER_NO,1,4) IN ('0102','0202','0302','0402') THEN 'COR'
         WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN 'GA'
         WHEN t.COST_CENTER_NO IN ('010100','020102','030100','040100') THEN 'INS'
         WHEN t.COST_CENTER_NO IN ('01011301','01011302','01011303','02011301','03011301','04011301') THEN 'COR'
         WHEN SUBSTR(t.COST_CENTER_NO,1,2)='00' THEN 'HO' ELSE 'X' END f,
    CASE WHEN t.VOUCHER_NO='JV1-24/04043' THEN 'X'
         WHEN EXISTS (SELECT 'X' FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) THEN 'F'
         ELSE 'N' END fl,
    ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2) amt
  FROM {P}GL_TRANSACTIONS_DETAILS t
  WHERE t.STATUS<>'C'
  GROUP BY EXTRACT(YEAR FROM t.VM_DATE), t.ACCOUNT_NO,
    CASE WHEN SUBSTR(t.ACCOUNT_NO,1,1)<>'3' THEN '-'
         WHEN SUBSTR(t.COST_CENTER_NO,1,4) IN ('0102','0202','0302','0402') THEN 'COR'
         WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN 'GA'
         WHEN t.COST_CENTER_NO IN ('010100','020102','030100','040100') THEN 'INS'
         WHEN t.COST_CENTER_NO IN ('01011301','01011302','01011303','02011301','03011301','04011301') THEN 'COR'
         WHEN SUBSTR(t.COST_CENTER_NO,1,2)='00' THEN 'HO' ELSE 'X' END,
    CASE WHEN t.VOUCHER_NO='JV1-24/04043' THEN 'X'
         WHEN EXISTS (SELECT 'X' FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) THEN 'F'
         ELSE 'N' END)) GROUP BY bkt
