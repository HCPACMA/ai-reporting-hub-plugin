-- Account-level detail for the four accounts IFRS 18 forces out of the aggregate buckets.
-- {P} = schema prefix.  Run per branch; the Riyadh ledger carries every cost centre, the
-- others only their own small local postings.
--   3290001 فوائد قروض          -> FINANCING category (cost of raising finance)
--   3290002 عمولات بنكية        -> stays OPERATING (a service fee, not a financing cost)
--   4300003 إيرادات إيجارات     -> INVESTING (an asset returning income independently) — judgment
--   4300008 أرباح رأسمالية      -> OPERATING when the asset was used in operations — judgment
--   4300001/2/4/5/6/9           -> other OPERATING income
-- Packed row: account|cost_centre|yyyymm|DR-CR
SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) s FROM (
  SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY a,cc,ym)-1)/60) bkt, a||'|'||cc||'|'||ym||'|'||amt r
  FROM (
    SELECT t.ACCOUNT_NO a, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) cc,
           TO_CHAR(t.VM_DATE,'YYYYMM') ym,
           TO_CHAR(ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2)) amt
      FROM {P}GL_TRANSACTIONS_DETAILS t
     WHERE t.VM_DATE>=DATE '{D0}' AND t.VM_DATE<DATE '{D1}'
       AND t.STATUS IN ('P','O')
       AND (t.ACCOUNT_NO IN ('3290001','3290002') OR SUBSTR(t.ACCOUNT_NO,1,3)='430')
       AND t.DESCRIPTION NOT LIKE '%قفال الحسابات الختامية%'
       AND t.DESCRIPTION NOT LIKE '%اقفال ضريبة%'
     GROUP BY t.ACCOUNT_NO, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2), TO_CHAR(t.VM_DATE,'YYYYMM')))
GROUP BY bkt ORDER BY bkt
