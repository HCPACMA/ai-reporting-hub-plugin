-- Trial-balance movements (GLTRIAL equivalent) for VAT and revenue accounts, one row per account with months packed.
-- STATUS P=posted O=open (C=cancelled, excluded). Excludes the monthly VAT closing JV and the year-end closing JV.
SELECT ACCOUNT_NO||'|'||LISTAGG(YM||':'||DR||':'||CR,',') WITHIN GROUP (ORDER BY YM) R FROM (
 SELECT ACCOUNT_NO, TO_CHAR(VM_DATE,'YYMM') YM, ROUND(SUM(DR_AMOUNT),2) DR, ROUND(SUM(CR_AMOUNT),2) CR
 FROM {P}GL_TRANSACTIONS_DETAILS
 WHERE VM_DATE>=DATE '{D0}' AND VM_DATE<DATE '{D1}' AND STATUS IN ('P','O')
   AND NVL(DESCRIPTION,'x') NOT LIKE '%اقفال ضريبة%' AND NVL(DESCRIPTION,'x') NOT LIKE '%قفال الحسابات الختامية%'
   AND (ACCOUNT_NO IN ('1263000','21230071','21230072','2123001') OR ACCOUNT_NO LIKE '4%')
 GROUP BY ACCOUNT_NO, TO_CHAR(VM_DATE,'YYMM')) GROUP BY ACCOUNT_NO ORDER BY 1
