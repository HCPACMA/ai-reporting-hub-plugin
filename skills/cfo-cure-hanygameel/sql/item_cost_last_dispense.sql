-- Warehouse cost of every mapped stock item at its LAST Stock Dispense movement.
-- {P} = schema prefix (EXSYS. for the schema-owner branch, empty otherwise)
-- {ITEMS} = quoted, comma-separated PRODUCT_CODE list from the costing map (zero-padded, 7 chars)
-- Tie-out: 0170680 ALBUMIN-C-111 = 173.70 on 2026-09-10, identical to the Cost column in the map file.
-- Packed output: bkt + '~'-joined rows  code|name|master_avg_cost|last_dispense_date|last_dispense_cost|qty_12m|dispenses_12m
SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) s FROM (
  SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY pc)-1)/25) bkt,
         pc||'|'||nm||'|'||avgc||'|'||lastd||'|'||lastc||'|'||nq||'|'||nd r
  FROM (
    SELECT p.PRODUCT_CODE pc,
           SUBSTR(TRANSLATE(NVL(p.DESCRIPTION_S,p.DESCRIPTION_P),'|~'||CHR(10)||CHR(13),'  '),1,40) nm,
           TO_CHAR(ROUND(NVL(p.PRODUCT_AVERAGE_COST,0),4)) avgc,
           NVL((SELECT TO_CHAR(MAX(m.SDIS_DATE),'YYYY-MM-DD')
                  FROM {P}IM_STOCK_DISPENSING_D d
                  JOIN {P}IM_STOCK_DISPENSING_M m
                    ON m.ORGANIZATION_NO=d.ORGANIZATION_NO AND m.STORE_ID=d.STORE_ID AND m.SDIS_NO=d.SDIS_NO
                 WHERE d.PRODUCT_CODE=p.PRODUCT_CODE),'') lastd,
           NVL((SELECT TO_CHAR(ROUND(MAX(d.COST_PRICE) KEEP (DENSE_RANK LAST ORDER BY m.SDIS_DATE, m.SDIS_NO),4))
                  FROM {P}IM_STOCK_DISPENSING_D d
                  JOIN {P}IM_STOCK_DISPENSING_M m
                    ON m.ORGANIZATION_NO=d.ORGANIZATION_NO AND m.STORE_ID=d.STORE_ID AND m.SDIS_NO=d.SDIS_NO
                 WHERE d.PRODUCT_CODE=p.PRODUCT_CODE),'') lastc,
           NVL((SELECT TO_CHAR(ROUND(SUM(d.DISPENSE_QTY-NVL(d.RETURNED_QTY,0)),2))
                  FROM {P}IM_STOCK_DISPENSING_D d
                  JOIN {P}IM_STOCK_DISPENSING_M m
                    ON m.ORGANIZATION_NO=d.ORGANIZATION_NO AND m.STORE_ID=d.STORE_ID AND m.SDIS_NO=d.SDIS_NO
                 WHERE d.PRODUCT_CODE=p.PRODUCT_CODE AND m.SDIS_DATE>=ADD_MONTHS(SYSDATE,-12)),'0') nq,
           NVL((SELECT TO_CHAR(COUNT(*))
                  FROM {P}IM_STOCK_DISPENSING_D d
                  JOIN {P}IM_STOCK_DISPENSING_M m
                    ON m.ORGANIZATION_NO=d.ORGANIZATION_NO AND m.STORE_ID=d.STORE_ID AND m.SDIS_NO=d.SDIS_NO
                 WHERE d.PRODUCT_CODE=p.PRODUCT_CODE AND m.SDIS_DATE>=ADD_MONTHS(SYSDATE,-12)),'0') nd
      FROM {P}IM_PRODUCT_MASTER p
     WHERE p.PRODUCT_CODE IN ({ITEMS})))
GROUP BY bkt ORDER BY bkt
