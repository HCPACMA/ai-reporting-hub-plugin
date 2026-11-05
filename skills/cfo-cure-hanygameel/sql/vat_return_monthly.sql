-- VAT return (EXSYS screen VAT_FORM) rebuilt from the materialised view. Never use GL_VAT_AMT_BY_PERIOD (calls gl_vat_pkg, times out).
-- Output: YYYYMM;LINE_NO;TRX_TYPE;SUM(AMT);SUM(VAT);SUM(ROUND(VAT/0.15,2));COUNT
-- Box formulas: sales boxes 1-5 net = Σ SI(AMT−VAT) − Σ SR,CN(AMT+VAT), VAT = Σ VAT (negative on SR/CN)
--               box 6 net = Σ PI(AMT−VAT) + Σ PR(ROUND(VAT/0.15,2)); boxes 9/10 net = Σ PI AMT − Σ PR AMT; ignore null LINE_NO.
SELECT TO_CHAR(TRX_DATE,'YYYYMM')||';'||LINE_NO||';'||TRX_TYPE||';'||ROUND(SUM(AMT),2)||';'||ROUND(SUM(NVL(VAT_AMT,0)),2)||';'||ROUND(SUM(ROUND(NVL(VAT_AMT,0)/0.15,2)),2)||';'||COUNT(*) R
FROM {P}GL_VAT_AMT_BY_PERIOD_ITEMS_MV WHERE TRX_DATE>=DATE '{D0}' AND TRX_DATE<DATE '{D1}'
GROUP BY TO_CHAR(TRX_DATE,'YYYYMM'), LINE_NO, TRX_TYPE ORDER BY 1
