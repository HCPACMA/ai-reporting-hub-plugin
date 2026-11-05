-- Staff sub-account balances for everyone who has an end-of-service date.
-- Monthly debit - credit per staff sub-account and account, from the first posting onward, so the
-- page can show the balance as at any month end.  Accounts: 1265xxx (advances, custody, deductions),
-- 2121xxx (dues payable) and 2111003 (vacation provision).
-- {P} = schema prefix; {B} = bucket count (Riyadh needs ~120, the branches ~20).
-- The staff master lives in the Riyadh database, so on the branch databases drop the IN (...) filter
-- and match the staff numbers afterwards.
SELECT bkt, COUNT(*) n, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (
 SELECT MOD(ROWNUM,{B}) bkt, s||'|'||a||'|'||ym||'|'||net r FROM (
  SELECT t.SUB_ACCOUNT_NO s, t.ACCOUNT_NO a, TO_CHAR(t.VM_DATE,'YYYYMM') ym,
         ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2) net
  FROM {P}GL_TRANSACTIONS_DETAILS t
  WHERE t.STATUS<>'C'
    AND (t.ACCOUNT_NO LIKE '1265%' OR t.ACCOUNT_NO LIKE '2121%' OR t.ACCOUNT_NO='2111003')
    AND t.SUB_ACCOUNT_NO IN (SELECT TO_CHAR(STAFF_ID) FROM {P}PS_STAFF_CONTRACT WHERE END_OF_SERVICE_AWARD_DATE IS NOT NULL)
  GROUP BY t.SUB_ACCOUNT_NO, t.ACCOUNT_NO, TO_CHAR(t.VM_DATE,'YYYYMM')
  HAVING ABS(SUM(t.DR_AMOUNT-t.CR_AMOUNT))>0.004)) GROUP BY bkt
-- End-of-service dates (latest per staff member):
-- SELECT b, COUNT(*) n, LISTAGG(STAFF_ID||'|'||d,'~') WITHIN GROUP (ORDER BY STAFF_ID) r FROM
--  (SELECT STAFF_ID, TO_CHAR(MAX(END_OF_SERVICE_AWARD_DATE),'YYYY-MM-DD') d, MOD(ROWNUM,6) b
--     FROM (SELECT STAFF_ID, END_OF_SERVICE_AWARD_DATE FROM {P}PS_STAFF_CONTRACT WHERE END_OF_SERVICE_AWARD_DATE IS NOT NULL)
--    GROUP BY STAFF_ID, MOD(ROWNUM,6)) GROUP BY b
