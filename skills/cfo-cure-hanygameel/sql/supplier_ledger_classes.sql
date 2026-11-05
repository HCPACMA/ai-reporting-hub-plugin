-- Supplier ledger (account 2122001) per sub-account & month, ALL branches, STATUS<>'C'. Output r = ym:inv:ret:pay:oth  (pre-window months collapsed into '0000-00')
-- STANDING CLASSIFICATION (Hany, 1 Nov 2026) - debits:
--   PAYMENT  (col pay) = description contains «سداد» OR «تحويل» OR «دفعة/دفعه» (but NOT starting «استحقاق» = accrual reclass), e.g. "تحويل لشركة ..." , "دفعة بالحساب"
--   OTHER    (col oth) = purchase returns «م.مشتريات RE01-…», credit notes «اشعار», discounts «خصم», reversals «عكس/حذف», accrual reclass «استحقاق»
-- credits: «مرتجع حوالة» -> ret (returned transfer, nets payments), all other credits -> inv.
-- Dues rule: due = balance at cut-off - ALL payments after the cut-off (col pay - col ret), then capped to 0 <= due <= supplier balance (validation).
SELECT sub||':'||ym||':'||ROUND(SUM(inv),2)||':'||ROUND(SUM(rt),2)||':'||ROUND(SUM(pay),2)||':'||ROUND(SUM(oth),2) r FROM (
 SELECT t.SUB_ACCOUNT_NO sub, CASE WHEN t.VM_DATE<DATE '{D0}' THEN '0000-00' ELSE TO_CHAR(t.VM_DATE,'YYYY-MM') END ym,
  CASE WHEN t.CR_AMOUNT>0 AND t.DESCRIPTION NOT LIKE '%مرتجع حوالة%' THEN t.CR_AMOUNT ELSE 0 END inv,
  CASE WHEN t.CR_AMOUNT>0 AND t.DESCRIPTION LIKE '%مرتجع حوالة%' THEN t.CR_AMOUNT ELSE 0 END rt,
  CASE WHEN t.DR_AMOUNT>0 AND (t.DESCRIPTION LIKE '%سداد%' OR ((t.DESCRIPTION LIKE '%تحويل%' OR t.DESCRIPTION LIKE '%دفعة%' OR t.DESCRIPTION LIKE '%دفعه%') AND t.DESCRIPTION NOT LIKE '%استحقاق%' AND t.DESCRIPTION NOT LIKE '%م.مشتريات%')) THEN t.DR_AMOUNT ELSE 0 END pay,
  CASE WHEN t.DR_AMOUNT>0 AND NOT (t.DESCRIPTION LIKE '%سداد%' OR ((t.DESCRIPTION LIKE '%تحويل%' OR t.DESCRIPTION LIKE '%دفعة%' OR t.DESCRIPTION LIKE '%دفعه%') AND t.DESCRIPTION NOT LIKE '%استحقاق%' AND t.DESCRIPTION NOT LIKE '%م.مشتريات%')) THEN t.DR_AMOUNT ELSE 0 END oth
 FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS<>'C' AND t.ACCOUNT_NO='2122001' AND t.VM_DATE<DATE '{D1}')
GROUP BY sub, ym ORDER BY 1
