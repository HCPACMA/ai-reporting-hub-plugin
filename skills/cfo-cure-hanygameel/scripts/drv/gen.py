# SQL generators for the Deep Analysis driver payloads (posted + open, STATUS<>'C').
import sys
FN = """CASE WHEN SUBSTR(t.ACCOUNT_NO,1,1)<>'3' THEN '-'
 WHEN SUBSTR(t.COST_CENTER_NO,1,4) IN ('0102','0202','0302','0402') THEN 'COR'
 WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN 'GA'
 WHEN t.COST_CENTER_NO IN ('010100','020102','030100','040100') THEN 'INS'
 WHEN t.COST_CENTER_NO IN ('01011301','01011302','01011303','02011301','03011301','04011301') THEN 'COR'
 WHEN SUBSTR(t.COST_CENTER_NO,1,2)='00' THEN 'HO' ELSE 'X' END"""
def gl_mon(P, d0, d1, B=190):
    f = ' '.join(FN.split())
    return (f"SELECT bkt, COUNT(*) n, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (SELECT MOD(ROWNUM,{B}) bkt, a||'|'||cc||'|'||f||'|'||ym||'|'||amt r FROM ("
            f"SELECT t.ACCOUNT_NO a, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) cc, {f} f, TO_CHAR(t.VM_DATE,'YYMM') ym, ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2) amt "
            f"FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{d0}' AND t.VM_DATE<DATE '{d1}' AND t.VOUCHER_NO<>'JV1-24/04043' "
            f"AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) "
            f"GROUP BY t.ACCOUNT_NO, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2), {f}, TO_CHAR(t.VM_DATE,'YYMM') HAVING ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2)<>0)) GROUP BY bkt")
def cc_mon(P, d0, d1, B=120):
    return (f"SELECT bkt, COUNT(*) n, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (SELECT MOD(ROWNUM,{B}) bkt, ym||'|'||cc||'|'||cash||'|'||cred||'|'||cdr||'|'||ccr r FROM ("
            f"SELECT TO_CHAR(t.VM_DATE,'YYMM') ym, t.COST_CENTER_NO cc, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '41%' THEN t.CR_AMOUNT-t.DR_AMOUNT ELSE 0 END),2) cash, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '42%' AND t.ACCOUNT_NO<>'4200027' THEN t.CR_AMOUNT-t.DR_AMOUNT ELSE 0 END),2) cred, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '3%' AND t.ACCOUNT_NO<>'3280005' THEN t.DR_AMOUNT ELSE 0 END),2) cdr, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '3%' AND t.ACCOUNT_NO<>'3280005' THEN t.CR_AMOUNT ELSE 0 END),2) ccr "
            f"FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{d0}' AND t.VM_DATE<DATE '{d1}' AND t.VOUCHER_NO<>'JV1-24/04043' "
            f"AND (t.ACCOUNT_NO LIKE '3%' OR t.ACCOUNT_NO LIKE '4%') AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) "
            f"GROUP BY TO_CHAR(t.VM_DATE,'YYMM'), t.COST_CENTER_NO)) GROUP BY bkt")
if __name__ == '__main__':
    k, P, d0, d1 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    print({'gl': gl_mon, 'cc': cc_mon}[k](P, d0, d1))
