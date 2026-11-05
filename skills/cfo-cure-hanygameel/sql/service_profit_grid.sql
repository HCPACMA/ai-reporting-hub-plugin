-- Invoice-line fact grid for service costing / profitability, one call per branch per date chunk.
-- {P} schema prefix · {D0} {D1} date range (D1 exclusive) · {PFX} service-code prefixes, e.g. '003','007'
-- Grain: month × service × customer group × contract type × doctor × clinic speciality
-- Packed output row: ym|product|cust_group|contract_type|doctor|speciality|qty|qty_free|gross_ex_vat|discount|patient_share|lines|invoices
--
-- RULES THAT MATTER
--  * revenue = gross_ex_vat − discount − patient_share(on company-billed lines); this is the same NET the
--    rest of the desk uses and ties to NextGen [Total Revenue] within 0.01 %.
--  * EXSYS re-invoices the insurance patient share as its own BILL_TO='P' line inside the same credit
--    contract, so those lines are EXCLUDED from qty — otherwise every credit service is costed twice.
--    (Verified: service 003689, Sep 2026 Riyadh — R|P lines total 4,351 = the patient share on the R|C lines.)
--  * BILL_TO='G' lines are gratis: real consumption, zero revenue. Kept in qty, reported separately as qty_free.
--  * LISTAGG caps a cell at 4000 chars and the MCP caps a result at 200 rows, so 70 rows per bucket and
--    at most ~14,000 rows per call. Split the date range when a branch exceeds that.
SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) s FROM (
  SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY ym,pc,grp,doc)-1)/70) bkt,
         ym||'|'||pc||'|'||grp||'|'||ctp||'|'||doc||'|'||sp||'|'||qty||'|'||qg||'|'||gr||'|'||ds||'|'||ps||'|'||ln||'|'||iv r
  FROM (
    SELECT TO_CHAR(c.PATIENT_INVOICE_DATE,'YYYYMM') ym, c.PRODUCT_CODE pc,
           ct2.CUSTOMER_GROUP_NO grp, ct2.CONTRACT_TYPE ctp, m.DOCTOR_ID doc,
           TO_CHAR(NVL(m.SPECIALTY_NO,0)) sp,
           TO_CHAR(ROUND(SUM(CASE WHEN ct2.CONTRACT_TYPE='R' AND c.BILL_TO='P' THEN 0 ELSE c.QTY END),1)) qty,
           TO_CHAR(ROUND(SUM(CASE WHEN c.BILL_TO='G' THEN c.QTY ELSE 0 END),1)) qg,
           TO_CHAR(ROUND(SUM(c.BILL_AMOUNT-NVL(c.VAT_AMT,0)),1)) gr,
           TO_CHAR(ROUND(SUM(c.BILL_DISCOUNT),1)) ds,
           TO_CHAR(ROUND(SUM(DECODE(c.BILL_TO,'P',0,NVL(c.BILL_PATIENT_SHARE,0))),1)) ps,
           TO_CHAR(COUNT(*)) ln, TO_CHAR(COUNT(DISTINCT c.PATIENT_INVOICE_NO)) iv
      FROM {P}RC_PATIENT_INVOICE_CHARGES c
      JOIN {P}RC_PATIENT_INVOICES m
        ON m.ORGANIZATION_NO=c.ORGANIZATION_NO AND m.PATIENT_INVOICE_NO=c.PATIENT_INVOICE_NO
      JOIN {P}RC_PATIENT_EPISODES e
        ON e.ORGANIZATION_NO=m.ORGANIZATION_NO AND e.PATIENT_FILE_NO=m.PATIENT_FILE_NO AND e.EPISODE_NO=m.EPISODE_NO
      JOIN {P}RC_CONTRACTS ct2 ON ct2.CONTRACT_NO=e.CONTRACT_NO
     WHERE c.PATIENT_INVOICE_DATE>=DATE '{D0}' AND c.PATIENT_INVOICE_DATE<DATE '{D1}'
       AND c.STATUS<>'C' AND SUBSTR(c.PRODUCT_CODE,1,3) IN ({PFX})
     GROUP BY TO_CHAR(c.PATIENT_INVOICE_DATE,'YYYYMM'), c.PRODUCT_CODE,
              ct2.CUSTOMER_GROUP_NO, ct2.CONTRACT_TYPE, m.DOCTOR_ID, NVL(m.SPECIALTY_NO,0)))
GROUP BY bkt ORDER BY bkt
