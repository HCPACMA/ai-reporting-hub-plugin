-- Customer credit notes (AR_CREDIT_NOTE_M), every status (P posted, O open, C cancelled), packed 40 per bucket.
-- Row: seq|date|customer group|customer|net amount|VAT|tax-return flag|status|voucher
SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (
 SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY d,s)-1)/40) bkt,
        s||'|'||d||'|'||g||'|'||c||'|'||a||'|'||v||'|'||f||'|'||st||'|'||vo r
 FROM (SELECT m.CREDIT_NOTE_SEQ s, TO_CHAR(m.CREDIT_NOTE_DATE,'YYYY-MM-DD') d, m.CUSTOMER_GROUP_NO g, m.CUSTOMER_NO c,
              TO_CHAR(ROUND(m.CR_AMOUNT,2)) a, TO_CHAR(ROUND(NVL(m.CR_VAT_AMT,0),2)) v, NVL(m.TAX_RETURN_FLAG,'N') f, m.STATUS st, NVL(m.VOUCHER_NO,'-') vo
       FROM {P}AR_CREDIT_NOTE_M m WHERE m.CREDIT_NOTE_DATE>=DATE '{D0}' AND m.CREDIT_NOTE_DATE<DATE '{D1}'))
GROUP BY bkt ORDER BY bkt
