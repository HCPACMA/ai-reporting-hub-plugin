import sys
P=sys.argv[1]; D0=sys.argv[2]; D1=sys.argv[3]; kind=sys.argv[4]; N=int(sys.argv[5]) if len(sys.argv)>5 else 400
GP=(P or '')+'GET_PARAMETER' if P else 'GET_PARAMETER'
PT=f"CASE WHEN E.CONTRACT_NO = TO_NUMBER({GP}('AD_CASH_CONTRACT')) THEN 'Cash' WHEN M.PATIENT_INVOICE_TYPE='R' THEN 'Credit' ELSE 'Cash' END"
NET="(NVL(C.BILL_AMOUNT,0)-NVL(C.BILL_DISCOUNT,0)-DECODE(C.BILL_TO,'P',0,NVL(C.BILL_PATIENT_SHARE,0))-NVL(C.VAT_AMT,0))"
GRS="(NVL(C.BILL_AMOUNT,0)-DECODE(C.BILL_TO,'P',0,NVL(C.BILL_PATIENT_SHARE,0))-NVL(C.VAT_AMT,0))"
EJ=f"JOIN {P}RC_PATIENT_EPISODES E ON E.PATIENT_FILE_NO=M.PATIENT_FILE_NO AND E.ORGANIZATION_NO=M.ORGANIZATION_NO AND E.EPISODE_NO=M.EPISODE_NO"
INV=(f"SELECT M.PATIENT_INVOICE_DATE dt, M.STAFF_ID cid, M.PATIENT_FILE_NO pf, M.EPISODE_NO ep, M.DOCTOR_ID did, C.PRODUCT_CODE pc, {PT} pt, E.CONTRACT_NO cno, NVL(C.QTY,1) q, {GRS} g, NVL(C.BILL_DISCOUNT,0) d, {NET} n "
     f"FROM {P}RC_PATIENT_INVOICES M JOIN {P}RC_PATIENT_INVOICE_CHARGES C ON M.ORGANIZATION_NO=C.ORGANIZATION_NO AND M.PATIENT_INVOICE_NO=C.PATIENT_INVOICE_NO {EJ} "
     f"WHERE M.STATUS='P' AND C.STATUS='P' AND C.BILL_TO IN ('C','G','P') AND M.PATIENT_INVOICE_DATE>=DATE '{D0}' AND M.PATIENT_INVOICE_DATE<DATE '{D1}'")
REF=(f"SELECT R.REFUND_INVOICE_DATE dt, R.STAFF_ID cid, M.PATIENT_FILE_NO pf, M.EPISODE_NO ep, M.DOCTOR_ID did, C.PRODUCT_CODE pc, {PT} pt, E.CONTRACT_NO cno, NVL(C.QTY,1) q, -{GRS} g, -NVL(C.BILL_DISCOUNT,0) d, -{NET} n "
     f"FROM {P}RC_PATIENT_REFUND_INVOICES R JOIN {P}RC_PATIENT_RETURN_INV_CHARGES C ON R.ORGANIZATION_NO=C.ORGANIZATION_NO AND R.REFUND_INVOICE_NO=C.REFUND_INVOICE_NO "
     f"JOIN {P}RC_PATIENT_INVOICES M ON R.ORGANIZATION_NO=M.ORGANIZATION_NO AND R.PATIENT_INVOICE_NO=M.PATIENT_INVOICE_NO {EJ} "
     f"WHERE M.STATUS='P' AND C.STATUS='P' AND R.STATUS='P' AND C.BILL_TO IN ('C','G','P') AND R.REFUND_INVOICE_DATE>=DATE '{D0}' AND R.REFUND_INVOICE_DATE<DATE '{D1}'")
NM=lambda x: f"TRANSLATE(NVL({P}GET_STAFF_MAIDEN_NAME({x}),{x}),'|~'||CHR(10)||CHR(13),'    ')"
SV=f"TRANSLATE(SUBSTR(NVL((SELECT PM.DESCRIPTION_P FROM {P}IM_PRODUCT_MASTER PM WHERE PM.PRODUCT_CODE=z.pc),z.pc),1,50),'|~'||CHR(10)||CHR(13),'    ')"
CN=f"TRANSLATE(SUBSTR(NVL((SELECT CN.DESCRIPTION_P FROM {P}RC_CONTRACTS CN WHERE CN.CONTRACT_NO=z.cno),'-'),1,60),'|~'||CHR(10)||CHR(13),'    ')"
def pack(inner, fields, B=80):
    return f"SELECT bkt, COUNT(*) n, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (SELECT MOD(ROWNUM,{B}) bkt, {fields} r FROM ({inner}) z) GROUP BY bkt"
if kind=='exc':
    inner=(f"SELECT * FROM (SELECT x.*, ROW_NUMBER() OVER (PARTITION BY k ORDER BY sk) rk FROM ("
           f"SELECT K.k, L.*, CASE WHEN K.k='HD' THEN -L.d ELSE -L.n END sk FROM ({INV}) L, (SELECT 'HD' k FROM DUAL UNION ALL SELECT 'NT' FROM DUAL) K "
           f"WHERE (K.k='HD' AND L.pt='Cash' AND L.g>=200 AND L.d>=0.3*L.g) OR (K.k='NT' AND TO_NUMBER(TO_CHAR(L.dt,'HH24'))<6) "
           f"UNION ALL SELECT 'RT', R.*, R.n FROM ({REF}) R) x) WHERE rk<={N}")
    fields=(f"z.k||'|'||TO_CHAR(z.dt,'YYYY-MM-DD')||'|'||TO_CHAR(z.dt,'HH24')||'|'||{NM('z.cid')}||'|'||z.pf||'|'||{NM('z.did')}||'|'||{SV}||'|'||z.pt||'|'||{CN}||'|'||z.q||'|'||ROUND(z.g,2)||'|'||ROUND(z.d,2)||'|'||ROUND(z.n,2)")
    q=pack(inner,fields,150)
elif kind=='price':
    inner=(f"SELECT * FROM (SELECT y.*, ROW_NUMBER() OVER (ORDER BY y.u/y.av DESC) rk FROM (SELECT L.*, L.g/NULLIF(L.q,0) u, AVG(L.g/NULLIF(L.q,0)) OVER (PARTITION BY L.pc, L.pt) av, "
           f"STDDEV_POP(L.g/NULLIF(L.q,0)) OVER (PARTITION BY L.pc, L.pt) sdv, COUNT(*) OVER (PARTITION BY L.pc, L.pt) cnt FROM ({INV}) L WHERE L.q>0 AND L.g>0) y "
           f"WHERE y.cnt>=30 AND y.av>0 AND y.u > GREATEST(y.av+4*y.sdv, 3*y.av)) WHERE rk<={N}")
    fields=(f"z.pc||'|'||z.pt||'|'||TO_CHAR(z.dt,'YYYY-MM-DD')||'|'||{NM('z.cid')}||'|'||z.pf||'|'||{NM('z.did')}||'|'||{SV}||'|'||{CN}||'|'||z.q||'|'||ROUND(z.g,2)||'|'||ROUND(z.d,2)||'|'||ROUND(z.n,2)||'|'||z.cnt||'|'||ROUND(z.av,2)||'|'||ROUND(GREATEST(z.av+4*z.sdv,3*z.av),2)")
    q=pack(inner,fields,90)
elif kind=='dup':
    inner=(f"SELECT * FROM (SELECT y.*, ROW_NUMBER() OVER (ORDER BY y.n DESC) rk FROM (SELECT TRUNC(L.dt) dt, L.pf, L.pc, MAX(L.pt) pt, COUNT(DISTINCT L.ep) eps, SUM(L.n) n, MAX(L.cid) cid "
           f"FROM ({INV}) L GROUP BY TRUNC(L.dt), L.pf, L.pc HAVING COUNT(DISTINCT L.ep)>=2 AND SUM(L.n)>0) y) WHERE rk<={N}")
    fields=(f"TO_CHAR(z.dt,'YYYY-MM-DD')||'|'||z.pf||'|'||{SV}||'|'||z.pt||'|'||z.eps||'|'||ROUND(z.n,2)||'|'||{NM('z.cid')}")
    q=pack(inner,fields,60)
elif kind=='disc':
    inner=(f"SELECT * FROM (SELECT y.*, ROW_NUMBER() OVER (ORDER BY y.d DESC) rk FROM (SELECT L.pf, L.cid, COUNT(*) ln, SUM(L.g) g, SUM(L.d) d, MIN(L.dt) f0, MAX(L.dt) f1 "
           f"FROM ({INV}) L WHERE L.pt='Cash' AND L.d>0 GROUP BY L.pf, L.cid HAVING COUNT(*)>=2) y) WHERE rk<={N}")
    fields=(f"z.pf||'|'||{NM('z.cid')}||'|'||z.ln||'|'||ROUND(z.g,2)||'|'||ROUND(z.d,2)||'|'||TO_CHAR(z.f0,'YYYY-MM-DD')||'|'||TO_CHAR(z.f1,'YYYY-MM-DD')")
    q=pack(inner,fields,40)
print(q)
