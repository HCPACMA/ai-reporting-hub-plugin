-- Year-end provision entries booked on 31-Dec (accounts 3280003 EOSB, 3280004 insurer additional discount, 3280005 zakat), by branch and function.
-- Used by the Desk's "load year-end provisions as an estimate" checkbox (= last year's entry / 12 x months). Accrual vouchers exist in the Riyadh GL only.
-- Output R: year;account;branch(CC first 2 chars);function key;amount (DR-CR). Closing vouchers / cancelled excluded.
SELECT y||';'||a||';'||b||';'||k||';'||ROUND(SUM(amt),2) R FROM (
 SELECT EXTRACT(YEAR FROM t.VM_DATE) y, t.ACCOUNT_NO a, SUBSTR(t.COST_CENTER_NO,1,2) b, t.DR_AMOUNT-t.CR_AMOUNT amt,
  CASE WHEN t.ACCOUNT_NO='3280005' THEN 'zak'
       WHEN SUBSTR(t.COST_CENTER_NO,1,4) IN ('0102','0202','0302','0402') THEN 'COR'
       WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN 'GA'
       WHEN t.COST_CENTER_NO IN ('010100','020102','030100','040100') THEN 'INS'
       WHEN t.COST_CENTER_NO IN ('01011301','01011302','01011303','02011301','03011301','04011301') THEN 'COR'
       WHEN SUBSTR(t.COST_CENTER_NO,1,2)='00' THEN 'HO' ELSE 'GA' END k
 FROM {P}GL_TRANSACTIONS_DETAILS t
 WHERE t.STATUS<>'C' AND t.ACCOUNT_NO IN ('3280003','3280004','3280005') AND t.VM_DATE>=DATE '{D0}' AND t.VM_DATE<DATE '{D1}'
   AND EXTRACT(MONTH FROM t.VM_DATE)=12 AND EXTRACT(DAY FROM t.VM_DATE)=31
   AND NOT EXISTS (SELECT 'X' FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO))
GROUP BY y,a,b,k ORDER BY 1
