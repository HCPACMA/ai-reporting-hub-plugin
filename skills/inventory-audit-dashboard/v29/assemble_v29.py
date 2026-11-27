import json,glob,pickle,collections,re
from openpyxl import Workbook
old=pickle.load(open('old_extract.pkl','rb'))
dims=pickle.load(open('dims.pkl','rb'))
cbm=json.load(open('created_by_map.json'))
def merge(prefix):
    G={}
    for f in sorted(glob.glob(f'raw/{prefix}_*.json')):
        for g,rows in json.load(open(f))['g'].items():
            g=int(g)
            if g in G and G[g]!=rows: print('CONFLICT',prefix,g)
            G[g]=rows
    ks=sorted(G); assert ks==list(range(ks[0],ks[-1]+1)),(prefix,'gap')
    return [re.sub(r'\s*\|\s*\.{50}\s*$','',r).rstrip() for g in ks for r in G[g]]
def nz(x): return x if x not in ('',None) else None
def ff(x):
    x=nz(x)
    return None if x is None else str(float(x))
# ---------- Products
ph,prows=old['Products+Costing']; pix={h:i for i,h in enumerate(ph)}
oldprod={r[0]:r for r in prows}
P=merge('prod'); print('products',len(P))
prod_out=[];prod={}
for s in P:
    f=s.split('|'); assert len(f)==10,f
    code,ig,cat,desc,uom,act,ned,ctl,avg,ext=f
    row=[None]*len(ph)
    o=oldprod.get(code)
    if o: row=list(o)+[None]*(len(ph)-len(o))
    row[pix['product_code']]=code; row[pix['inv_group']]=ig; row[pix['product_category']]=ff(cat)
    row[pix['description_p']]=nz(desc); row[pix['primary_uom']]=nz(uom); row[pix['active_flag']]=act
    row[pix['near_expiry_days']]=ff(ned); row[pix['control_drug_flag']]=nz(ctl)
    row[pix['product_average_cost']]=nz(avg); row[pix['external_cost_price']]=nz(ext)
    if not row[pix['description_s']]: row[pix['description_s']]=None
    prod_out.append(row); prod[code]=row
assert len(prod)==len(P)==15009
# group / category description maps from old transactions
th,trows=old['Transactions 2026']; tix={h:i for i,h in enumerate(th)}
igd={};catd={}
for r in trows:
    if r[tix['inv_group']] and r[tix['inv_group_description']]: igd[r[tix['inv_group']]]=r[tix['inv_group_description']]
    if r[tix['product_category']] and r[tix['product_category_description']]: catd[r[tix['product_category']]]=r[tix['product_category_description']]
# ---------- Balance
bh,brows=old['Balance+Config']
orgname={'01011301':'Main Store','01011302':'dialysis Store','02011301':'Main Store B1','03011301':'Main Store B2','04011301':'Main Store - RAH'}
storename={'2':'Main Store','7':'Dialysis Store','3':'Buridah-1 Store','4':'Buridah-2 Store','5':'Rafha Store'}
B=merge('bal'); bal_out=[]
for s in B:
    f=s.split('|'); assert len(f)==12,f
    pc,pn,org,st,uom,mn,ro,mx,oh,it,rs,av=f
    bal_out.append([pc,nz(pn),org,orgname[org],st,storename[st],uom,uom,ff(mn),ff(ro),ff(mx),ff(oh),ff(it),ff(rs),ff(av)])
assert len(bal_out)==1403
# ---------- Batches
bth,btrows=old['Batches']
Bt=merge('bat'); bat_out=[]
for s in Bt:
    f=s.split('|'); assert len(f)==12,f
    org,st,ig,cat,pc,pd,bn,ex,ned,uomd,q,qa=f
    bat_out.append([org,ff(st),ig,ff(cat),pc,nz(pd),nz(bn),nz(ex),ff(ned),nz(uomd),ff(q),ff(qa)])
assert len(bat_out)==1430
# ---------- Mfg
mh,mrows=old['Batch-Mfg Detail']
M=merge('mfg'); mfg_out=[]
for s in M:
    f=s.split('|'); assert len(f)==4,f
    mfg_out.append([f[0],f[1],nz(f[2]),f[3]])
assert len(mfg_out)==36494
# ---------- Transactions
T=json.load(open('trx_rows.json'))
# the view repeats every CRC line exactly twice -> halve identical CRC groups (old extract kept each CRC line once)
_c=collections.Counter(x for x in T if x.startswith('CRC|')); _seen=collections.Counter(); _T=[]
for x in T:
    if x.startswith('CRC|'):
        _seen[x]+=1
        if _seen[x]>_c[x]//2: continue
    _T.append(x)
print('CRC halved: removed',len(T)-len(_T)); T=_T
sup=dims['sup']; cc=dims['cc']; org=dims['org']; ttype=dims['ttype']
STAT={'P':'Posted','C':'CANCEL','O':'Open'}
tr_out=[];miss=collections.Counter();bad=0
def sid(x):
    x=nz(x); return None if x is None else str(float(x))
for s in T:
    f=s.split('|')
    if len(f)!=21: bad+=1; continue
    (tt,pc,og,st,tn,td,stt,rcv,ccn,cost,qty,uom,fac,pby,pdt,sp,idc,ivd,sa,bn,ex)=f
    r=[None]*len(th)
    p=prod.get(pc)
    r[tix['t_type']]=tt; r[tix['product_code']]=pc
    if p:
        r[tix['product_desc_p']]=p[pix['description_p']]; r[tix['product_desc_s']]=p[pix['description_s']] or p[pix['description_p']]
        r[tix['inv_group']]=p[pix['inv_group']]; r[tix['inv_group_description']]=igd.get(p[pix['inv_group']])
        r[tix['product_category']]=p[pix['product_category']]; r[tix['product_category_description']]=catd.get(p[pix['product_category']])
    else: miss['prod']+=1
    r[tix['stock_account']]=nz(sa); r[tix['organization_no']]=og; r[tix['organization_name']]=org.get(og)
    if og not in org: miss['org']+=1
    st2=sid(st); r[tix['store_id']]=st2
    sn=dims['store'].get((og,st2)); r[tix['store_name']]=sn
    if sn is None: miss['store']+=1
    r[tix['transaction_no']]=tn; r[tix['transaction_date']]=td; r[tix['status']]=nz(stt)
    r[tix['transaction_type']]=ttype.get(tt,(None,None))[0]
    r2=sid(rcv); r[tix['receive_store_id']]=r2; r[tix['receive_store_name']]=dims['rcv'].get(r2) if r2 else None
    if r2 and r2 not in dims['rcv']: miss['rcv']+=1
    r[tix['cost_centet_no']]=nz(ccn); r[tix['cost_center_name']]=cc.get(ccn) if ccn else None
    if ccn and ccn not in cc: miss['cc']+=1
    r[tix['primary_unit_cost']]=nz(cost); r[tix['line_qty']]=ff(qty); r[tix['uom_code']]=nz(uom); r[tix['uom_factor']]=ff(fac)
    r[tix['created_by']]=cbm.get(tn); 
    if tn not in cbm: miss['cb']+=1
    r[tix['posted_by']]=nz(pby); r[tix['post_date']]=nz(pdt); r[tix['supplier_no']]=nz(sp)
    if sp:
        sd=sup.get(sp)
        if sd: r[tix['supplier_description_p']],r[tix['supplier_description_s']]=sd
        else: miss['sup:'+sp]+=1
    r[tix['item_discount']]=nz(idc); r[tix['invoice_discount']]=nz(ivd)
    r[tix['expiry_date']]=nz(ex); r[tix['batch_no']]=nz(bn)
    r[tix['status_description']]=STAT.get(stt)
    tr_out.append(r)
print('trx',len(tr_out),'bad',bad,'miss',dict(miss))
pickle.dump({'Products+Costing':(ph,prod_out),'Balance+Config':(bh,bal_out),'Batches':(bth,bat_out),'Batch-Mfg Detail':(mh,mfg_out),'Transactions 2026':(th,tr_out)},open('new_extract.pkl','wb'))
