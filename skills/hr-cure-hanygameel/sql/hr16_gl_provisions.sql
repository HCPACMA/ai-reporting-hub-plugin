-- Posted GL balances of the HR liability accounts. Columns: acc, n, net (debit minus credit; a credit balance is negative)
-- Always STATUS='P'. An earlier query that included open rows (O) misled.
SELECT g.ACCOUNT_NO ACC, COUNT(*) N, ROUND(SUM(NVL(g.DR_AMOUNT,0)-NVL(g.CR_AMOUNT,0))) NET FROM {P}GL_TRANSACTIONS_DETAILS g WHERE g.STATUS='P' AND g.ACCOUNT_NO IN ('{ACC_EOSB}','{ACC_LEAVE}','{ACC_PAY}') GROUP BY g.ACCOUNT_NO
