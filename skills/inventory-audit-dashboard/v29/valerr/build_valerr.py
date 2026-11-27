import csv, json, pickle, os
from collections import defaultdict
H='/home/claude/w'
S=pickle.load(open(f'{H}/pipe/Inventory/alfaihaa/_state.pkl','rb'))
RET={r['pinv'] for r in json.load(open(f'{H}/watch/returns/returns.json'))}
bal=S['balances']; prods=S['products']
nm={}; oh=defaultdict(float); ohv=defaultdict(float); stores=defaultdict(list)
for b in bal:
    nm[b['product']]=b['product_name']
    if b['on_hand']>0:
        oh[b['product']]+=b['on_hand']; ohv[b['product']]+=b['on_hand']*(b['unit_cost'] or 0)
        stores[b['product']].append((b['store_name'],b['on_hand'],b['unit_cost'] or 0))
def name(p): return nm.get(p) or (prods.get(p) or {}).get('name') or p
def sev(r,hi,mid): return 'high' if r>=hi else ('medium' if r>=mid else 'low')
ev=[]
# A: transfer send vs receive cost
for p,d,no,st,q,rc,sc,sno in csv.reader(open(f'{H}/valerr/tr.csv')):
    q=float(q);rc=float(rc);sc=float(sc)
    ratio=(rc/sc if sc>0 else 999) if rc>=sc else (sc/rc if rc>0 else 999)
    ev.append(dict(kind='TR',product=p,product_name=name(p),date=d,doc=no,ref_doc=sno,store=st,qty=q,cost_from=sc,cost_to=rc,
       ratio=round(ratio,1),direction='up' if rc>sc else 'down',effect=round(q*(rc-sc),2),severity=sev(ratio,10,3)))
# B: consecutive purchase price jumps (returned invoices excluded)
nret=0
for p,d,no,c,pc,pd,pno,q,sup in csv.reader(open(f'{H}/valerr/pi.csv')):
    if no in RET or pno in RET: nret+=1; continue
    c=float(c);pc=float(pc);q=float(q)
    ratio=c/pc if c>=pc else pc/c
    ev.append(dict(kind='PI',product=p,product_name=name(p),date=d,doc=no,ref_doc=pno,ref_date=pd,supplier=sup,qty=q,cost_from=pc,cost_to=c,
       ratio=round(ratio,1),direction='up' if c>pc else 'down',effect=round(q*(c-pc),2),severity=sev(ratio,10,3)))
# C: current valuation cost vs last purchase
val={}
for p,vc,pc,pd,vd in csv.reader(open(f'{H}/valerr/val.csv')):
    val[p]=(float(vc),float(pc),pd,vd)
sk={}
def S_(p):
    return sk.setdefault(p,dict(product=p,product_name=name(p),patterns=set(),n_events=0,max_ratio=0.0))
for e in ev:
    s=S_(e['product']); s['patterns'].add(e['kind']); s['n_events']+=1; s['max_ratio']=max(s['max_ratio'],e['ratio'])
for p,(vc,pc,pd,vd) in val.items():
    s=S_(p); s['patterns'].add('VAL')
    s['last_pi_cost']=pc; s['last_pi_date']=pd
    r=(vc/pc if vc>=pc else (pc/vc if vc>0 else 999)); s['max_ratio']=max(s['max_ratio'],round(r,1))
# reference cost: last PI cost (val.csv) else latest PI event cost_to else TR send cost
ref={}
for p in sk:
    if p in val: ref[p]=val[p][1]
    else:
        pis=sorted([e for e in ev if e['product']==p and e['kind']=='PI'],key=lambda e:e['date'])
        trs=sorted([e for e in ev if e['product']==p and e['kind']=='TR'],key=lambda e:e['date'])
        ref[p]=pis[-1]['cost_to'] if pis else (trs[-1]['cost_from'] if trs else None)
rows=[]
for p,s in sk.items():
    q=oh.get(p,0.0); v=ohv.get(p,0.0); uc=(v/q) if q else None; rf=ref[p]
    imp=(v-q*rf) if (q and rf is not None) else 0.0
    # only count impact when valuation cost really deviates from ref (>=2x) -- else noise
    if q and rf and uc and max(uc/rf,rf/uc)<2: imp=0.0
    evs=[e for e in ev if e['product']==p]
    rows.append(dict(product=p,product_name=s['product_name'],patterns=sorted(s['patterns']),n_events=s['n_events'],max_ratio=s['max_ratio'],
        on_hand=round(q,2),valuation_unit_cost=round(uc,4) if uc else None,reference_cost=rf,last_pi_date=s.get('last_pi_date'),
        on_hand_value=round(v,2),value_at_reference=round(q*rf,2) if (q and rf is not None) else 0.0,impact=round(imp,2),
        direction=('inflated' if imp>0 else ('deflated' if imp<0 else ('none'))),
        severity='high' if (abs(imp)>=5000 or s['max_ratio']>=50) else ('medium' if (abs(imp)>=1000 or s['max_ratio']>=5) else 'low'),
        stores=[dict(store=a,qty=b,cost=round(c,4)) for a,b,c in stores.get(p,[])]))
rows.sort(key=lambda r:-abs(r['impact']))
for e in ev: e['on_hand_now']=round(oh.get(e['product'],0.0),2)
ev.sort(key=lambda e:(-abs(e['effect'])))
infl=sum(r['impact'] for r in rows if r['impact']>0); defl=sum(r['impact'] for r in rows if r['impact']<0)
tot_val=sum(ohv.values())
kpi=dict(skus_flagged=len(rows),skus_with_impact=sum(1 for r in rows if r['impact']!=0),events_tr=sum(e['kind']=='TR' for e in ev),
    events_pi=sum(e['kind']=='PI' for e in ev),skus_val_mismatch=len(val),inflated_value=round(infl,2),deflated_value=round(defl,2),
    net_impact=round(infl+defl,2),pct_of_stock_value=round(100*(infl+defl)/tot_val,2) if tot_val else 0,stock_value=round(tot_val,2),
    pi_events_dropped_returned=nret,as_of='2026-10-20',window_pi_from='2025-10-01',window_tr_from='2024-01-01')
out=dict(kpi=kpi,skus=rows,events=ev)
json.dump(out,open(f'{H}/valerr/valuation_errors.json','w'),ensure_ascii=False)
print(kpi)
for r in rows[:12]: print(r['product'],r['product_name'][:28],r['patterns'],r['on_hand'],r['valuation_unit_cost'],r['reference_cost'],r['impact'])
