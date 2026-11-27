import json,sys
ent=json.load(open('raw/otf_entries.2026-10.json'))['entries']
OV={2:[[22,32]],3:[[0,8]],4:[[0,8]],14:[[10,17]],15:[],29:[],74:[]}
out={}
for i,e in enumerate(ent):
    if e['kind']!='doctor': continue
    w=OV.get(i,e['win'])
    for j,(s,en) in enumerate(w):
        out.setdefault(e['br'],[]).append((i,j,e['st'],s,en,e['dd']))
res={}
for br,L in out.items():
    cases=[];conds=[]
    for i,j,st,s,en,dd in L:
        sh="(PATIENT_INVOICE_DATE-%s/24)"%s
        days=",".join("DATE '2026-10-%02d'"%d for d in dd)
        c="(DOCTOR_ID='%s' AND TRUNC(%s) IN (%s) AND (%s-TRUNC(%s))*24<%s)"%(st,sh,days,sh,sh,en-s)
        conds.append(c); cases.append("WHEN %s THEN '%s_%s_'||TO_CHAR(TRUNC(%s),'DD')"%(c,i,j,sh))
    sql=("SELECT K, LISTAGG(T||':'||REV||':'||EP,';') WITHIN GROUP (ORDER BY T) V FROM (SELECT K, T, ROUND(SUM(NV),2) REV, COUNT(DISTINCT FE) EP FROM (SELECT CASE "+" ".join(cases)+" END K, CASE WHEN PATIENT_INVOICE_TYPE='R' THEN 'R' WHEN PATIENT_INVOICE_TYPE IN ('C','D') THEN 'C' ELSE 'X' END T, INV_NET-NVL(VAT_AMT,0) NV, PATIENT_FILE_NO||'-'||EPISODE_NO FE FROM EXSYS.RC_NET_PATIENT_INVOICES_ITEMS WHERE SPECIALTY_NO<>30 AND PATIENT_INVOICE_DATE>=DATE '2026-09-30' AND PATIENT_INVOICE_DATE<DATE '2026-11-02' AND DOCTOR_ID IN ("+",".join(sorted(set("'%s'"%x[2] for x in L)))+")) WHERE K IS NOT NULL GROUP BY K,T) GROUP BY K ORDER BY K")
    res[br]=sql; open('raw/otf_sql_%s.sql'%br,'w').write(sql); print(br,len(sql),len(L))
