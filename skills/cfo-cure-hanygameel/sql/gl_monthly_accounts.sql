-- SUPERSEDED 25 Sep 2026: DATA.m is now rebuilt on posted + open vouchers (STATUS <> 'C') from the
-- gl_mon refresh job (scripts/drv/gen.py gl). Kept for reference only; see SPEC §8A.
-- Monthly GL movement, one row per account x cost centre x month.  This is the
-- source for the desk's monthly bucket series (DATA.m); scripts/build_monthly_buckets.py
-- applies the bucket classifier to it.
--
-- {P} schema prefix ('EXSYS.' on the Riyadh ledger, empty on the others).
-- {D0}/{D1} date window, {D1} exclusive.
--
-- BASIS — this must match the published series exactly or history moves:
--   STATUS = 'P'                              posted only, NOT P+O
--   VOUCHER_NO <> 'JV1-24/04043'              the Riyadh FY2024 bulk-reversal voucher,
--                                             which is not in FINANCIAL_YEARS and would
--                                             otherwise cancel Riyadh's whole year
--   NOT EXISTS (FINANCIAL_YEARS ...)          strips the year-end closing journals
--   cost centre = first 2 chars of COST_CENTER_NO  (00 HQ, 01..04 branches)
--
-- Note the desk's monthly series is POSTED-ONLY while the IFRS 18 account pull is
-- POSTED+OPEN.  That is a deliberate difference, not a bug, but it means unposted
-- revenue shows in the IFRS 18 tab and not in the rest of the desk.  Do not "fix"
-- one without re-validating the other.
--
-- The MCP caps a result at ~200 rows and LISTAGG at 4000 chars per cell, so pack 60
-- rows per cell and split the date range: the Riyadh ledger alone runs ~12,900 rows
-- over 45 months, which needs two calls.  Always count the months that came back.
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
       AND t.STATUS = 'P'
       AND t.VOUCHER_NO <> 'JV1-24/04043'
       AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy
                        WHERE fy.GL_VOUCHER_NO = t.VOUCHER_NO)
     GROUP BY t.ACCOUNT_NO, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2),
              TO_CHAR(t.VM_DATE,'YYYYMM')))
GROUP BY bkt ORDER BY bkt
