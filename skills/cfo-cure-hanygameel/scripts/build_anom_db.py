# DATA.anom from the EXSYS invoice tables (no Power BI). Inputs are the parsed query results in this folder.
import json, datetime as dt, collections, os
D0=dt.date(2024,1,1)
daily_rows=json.load(open('daily_rows.json'))
last=max(dt.date(int(ym[:4]),int(ym[4:]),int(d.split(':')[0])) for br,pt,sp,ym,dl in daily_rows for d in dl.split(','))
last=min(last, dt.date.today()-dt.timedelta(days=1))  # drop today's partial day
ND=(last-D0).days+1
daily=collections.defaultdict(lambda:[0]*ND); dnp=collections.defaultdict(lambda:[0]*ND)
for br,pt,sp,ym,dl in daily_rows:
    k=f'{br}|{pt}|{sp.strip()}'
    for d in dl.split(','):
        dd,n1,n2=d.split(':'); i=(dt.date(int(ym[:4]),int(ym[4:]),int(dd))-D0).days
        if 0<=i<ND: daily[k][i]+=int(float(n1)); dnp[k][i]+=int(float(n2))
names=json.load(open('doc_names.json'))
for f in ('doc_names_extra.json',):
    if os.path.exists(f): names.update(json.load(open(f)))
doc=[];docNP=[]
for br,ym,pt,did,sp,n1,n2,nd in json.load(open('doc_rows.json')):
    nm=names.get(did,did); sp=sp.strip()
    if abs(float(n1))>0.5: doc.append([int(ym),br,pt,nm,sp,round(float(n1),2),int(nd)])
    if abs(float(n2))>0.5: docNP.append([int(ym),br,pt,nm,sp,round(float(n2),2),int(nd)])
cash=[]
for r in json.load(open('cash_rows.json')):
    br,ym,cid,cn,pt=r[:5]; v=[float(x) for x in r[5:]]
    cash.append([br,int(ym),cid,' '.join(cn.split()),pt,int(v[0])]+[round(x,2) for x in v[1:4]]+[int(v[4]),round(v[5],2),int(v[6]),round(v[7],2),int(v[8]),round(v[9],2)])
lines=[]
by=collections.defaultdict(list)
for r in json.load(open('exc_rows.json')):
    br,k,d,h,cn,pf,dn,sv,pt,ct,q,g,ds,n=r
    by[k].append([k,br,d,h,' '.join(cn.split()),pf,' '.join(dn.split()),' '.join(sv.split()),pt,' '.join(ct.split()),float(q),float(g),float(ds),float(n)])
for k,v in by.items():
    if k=='HD': v.sort(key=lambda x:-x[12])
    elif k=='RT': v.sort(key=lambda x:x[13])
    else: v.sort(key=lambda x:-x[13])
    lines+=v[:400]
price=[]
if os.path.exists('price_rows.json'):
    for br,rows in json.load(open('price_rows.json')).items():
        for pc,pt,d,cn,pf,dn,sv,ct,q,g,ds,n,cnt,av,thr in rows:
            price.append([br,pc,pt,d,' '.join(cn.split()),pf,' '.join(dn.split()),' '.join(sv.split()),' '.join(ct.split()),float(q),float(g),float(ds),float(n),int(float(cnt)),float(av),float(thr)])
price.sort(key=lambda r: -(r[10]/(r[9] or 1))/(r[14] or 1)); price=price[:500]
dup=[]
if os.path.exists('dup_rows.json'):
    for br,rows in json.load(open('dup_rows.json')).items():
        for d,pf,sv,pt,eps,n,cn in rows: dup.append([br,d,pf,' '.join(sv.split()),pt,'NORMAL',int(float(eps)),float(n),' '.join(cn.split())])
    dup.sort(key=lambda r:-r[7]); dup=dup[:600]
discpat=[]
if os.path.exists('disc_rows.json'):
    for br,rows in json.load(open('disc_rows.json')).items():
        for pf,cn,ln,g,ds,f0,f1 in rows: discpat.append([br,pf,' '.join(cn.split()),int(float(ln)),float(g),float(ds),f0,f1])
    discpat.sort(key=lambda r:-r[5]); discpat=discpat[:500]
A={'d0':D0.isoformat(),'nd':ND,'asOf':last.isoformat(),'daily':dict(daily),'dailyNP':dict(dnp),'doc':doc,'docNP':docNP,'cash':cash,'lines':lines,'price':price,'dup':dup,'discpat':discpat,
   'src':'EXSYS invoice tables via Cure: RC_PATIENT_INVOICES / RC_PATIENT_INVOICE_CHARGES and refunds, RC_PATIENT_EPISODES, RC_SERVICES, RC_CLINICAL_STAFF / RC_CLINICAL_SPECIALITIES, IM_PRODUCT_MASTER, RC_CONTRACTS'}
json.dump(A,open('data_anom_db.json','w'),ensure_ascii=False,separators=(',',':'))
print('nd',ND,'last',last,'series',len(daily),'doc',len(doc),'cash',len(cash),'lines',len(lines),'price',len(price),'dup',len(dup),'discpat',len(discpat),'bytes',os.path.getsize('data_anom_db.json'))
