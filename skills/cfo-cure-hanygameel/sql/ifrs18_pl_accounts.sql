-- Every profit-or-loss account, monthly, by cost centre — the series the IFRS 18
-- statement of profit or loss is built from.  {P} = schema prefix ('EXSYS.' for the
-- Riyadh ledger, empty for the others).  Run per branch and merge; the Riyadh ledger
-- carries every cost centre, the others only their own local postings, so merge the
-- Riyadh rows by (account, cost centre, month) and ADD the branch rows on top.
--
-- Do NOT build this statement from the desk's aggregate buckets.  Four of the items
-- IFRS 18 forces out of the operating category all sit inside one bucket:
--   3280005  مخصص الزكاة            -> income-taxes position (and it is double counted
--                                       if the bucket is also charged as an expense)
--   3390000  عمولة التزامات الموظفين -> financing  (IFRS 18.61(a))
--   3380000  خسائر رأسمالية          -> same category as the disposal gains (18.44, B60)
--   3280004  خصم إضافي عملاء التأمين  -> contra-revenue or operating expense (IFRS 15.50)
-- and two more are split across buckets:
--   4300009  فروق حسابات البنوك      -> investing (IFRS 18.53(b), cash and equivalents)
--   3290001 / 3290002                -> financing / operating, both inside one bucket
--
-- The MCP returns ~200 rows and LISTAGG caps a cell at 4000 chars, so bucket ~60 packed
-- rows per cell and split the account range across calls when a branch exceeds ~12,000
-- rows.  A truncated result looks exactly like a complete one — count the months back.
--
-- Packed row: account|cost_centre|yyyymm|DR-CR
SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) s FROM (
  SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY a,cc,ym)-1)/60) bkt,
         a||'|'||cc||'|'||ym||'|'||amt r
  FROM (
    SELECT t.ACCOUNT_NO a,
           SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) cc,
           TO_CHAR(t.VM_DATE,'YYYYMM') ym,
           TO_CHAR(ROUND(SUM(t.DR_AMOUNT - t.CR_AMOUNT),2)) amt
      FROM {P}GL_TRANSACTIONS_DETAILS t
     WHERE t.VM_DATE >= DATE '{D0}' AND t.VM_DATE < DATE '{D1}'
       AND t.STATUS IN ('P','O')
       AND SUBSTR(t.ACCOUNT_NO,1,3) IN ({PREFIXES})      -- e.g. '311','312',...
       AND t.DESCRIPTION NOT LIKE '%قفال الحسابات الختامية%'
       AND t.DESCRIPTION NOT LIKE '%اقفال ضريبة%'
     GROUP BY t.ACCOUNT_NO, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2),
              TO_CHAR(t.VM_DATE,'YYYYMM')
    HAVING ABS(SUM(t.DR_AMOUNT - t.CR_AMOUNT)) > 0.5))
GROUP BY bkt ORDER BY bkt
