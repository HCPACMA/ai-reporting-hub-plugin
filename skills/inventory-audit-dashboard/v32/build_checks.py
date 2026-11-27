import json,pickle,re,collections
W='/home/claude/w'
A=json.load(open(f'{W}/audit_v29.json'))
S=pickle.load(open(f'{W}/pipe/Inventory/alfaihaa/_state.pkl','rb'))
X=pickle.load(open(f'{W}/new_extract.pkl','rb'))
RET={r['pinv'] for r in json.load(open(f'{W}/watch/returns/returns.json'))}
bal=S['balances']; nm={b['product']:b['product_name'] for b in bal}
out={}
# ---------- 1. savings realized ----------
mat=collections.defaultdict(list)
for m in A['product_supplier_price_matrix']: mat[m['product']].append(m)
rows=[];nr=0
for s in A['supplier_savings_opportunities']:
    ms=sorted(mat.get(s['product'],[]),key=lambda m:m['last_date'],reverse=True)
    r=dict(s)
    if ms:
        l=ms[0]; r['last_supplier']=l['supplier_name']; r['last_date']=l['last_date']
        r['status']='realized' if l['supplier_name']==s['cheapest_supplier'] else 'open'
        # latest-price-based check when latest supplier differs
    else: r['last_supplier']=None; r['last_date']=None; r['status']='open'
    rows.append(r)
k=collections.Counter(r['status'] for r in rows)
out['savings']=dict(rows=rows,kpi=dict(total=len(rows),realized=k['realized'],open=k['open']))
# ---------- 2. count-created (CT) ----------
st_branch={'2':'Riyadh','3':'Buraydah-1','4':'Buraydah-2','5':'Rafha'}
cost={(b['product'],b['store']):(b['unit_cost'] or 0) for b in bal}
onh={(b['product'],b['store']):b['on_hand'] for b in bal}
ovs={(r['product'],r['store']) for r in A['overstock']}; sms={(r['product'],r['store']) for r in A['slow_moving']}
agg={}
for b in X['Batches'][1]:
    if not str(b[6]).startswith('CT'): continue
    q=float(b[10] or 0)
    if q<=0: continue
    st=str(int(float(b[1]))); p=b[4]
    a=agg.setdefault((p,st),dict(ct_qty=0,batches=0,expiry=None)); a['ct_qty']+=q; a['batches']+=1
    e=(b[7] or '')[:10]
    if e and (a['expiry'] is None or e<a['expiry']): a['expiry']=e
ct=[]
for (p,st),a in agg.items():
    oh=onh.get((p,st),0); c=cost.get((p,st),0)
    if oh<=0: continue
    q=min(a['ct_qty'],oh)
    ct.append(dict(product=p,product_name=nm.get(p,p),branch=st_branch.get(st,'Store '+st),store=st,on_hand=oh,ct_qty=q,
      ct_pct=round(100*q/oh,1),unit_cost=round(c,4),ct_value=round(q*c,2),on_hand_value=round(oh*c,2),batches=a['batches'],
      earliest_expiry=a['expiry'],in_overstock=(p,st) in ovs,in_slow=(p,st) in sms))
ct.sort(key=lambda r:-r['ct_value'])
tot_val=sum(b['on_hand']*(b['unit_cost'] or 0) for b in bal if b['on_hand']>0)
out['ct']=dict(rows=ct,kpi=dict(skus=len(ct),value=round(sum(r['ct_value'] for r in ct),2),units=round(sum(r['ct_qty'] for r in ct)),
  pct_of_stock=round(100*sum(r['ct_value'] for r in ct)/tot_val,2),
  in_overstock=sum(r['in_overstock'] for r in ct),in_overstock_value=round(sum(r['ct_value'] for r in ct if r['in_overstock']),2),
  in_slow=sum(r['in_slow'] for r in ct),in_slow_value=round(sum(r['ct_value'] for r in ct if r['in_slow']),2),
  mostly_ct=sum(r['ct_pct']>=50 for r in ct)))
# ---------- 3. UOM / pack mismatch ----------
U=collections.defaultdict(list)
for l in open('uom_raw.txt'):
    c=[x.strip() for x in l.strip().strip('|').split('|')]
    U[c[0]].append(dict(uom=c[1],factor=float(c[2]),lines=int(float(c[3])),qty=float(c[4]),mn=float(c[5]),mx=float(c[6]),first=c[7],last=c[8]))
ohq=collections.defaultdict(float);ohv=collections.defaultdict(float)
for b in bal:
    if b['on_hand']>0: ohq[b['product']]+=b['on_hand']; ohv[b['product']]+=b['on_hand']*(b['unit_cost'] or 0)
uom=[]
for p,vs in U.items():
    vs.sort(key=lambda v:v['factor'])
    allmin=min(v['mn'] for v in vs); allmax=max(v['mx'] for v in vs); ratio=allmax/allmin if allmin>0 else 999
    sig='MIX'; why=''
    for i,a in enumerate(vs):
        for b in vs[i+1:]:
            f=b['factor']/a['factor']
            for hi,lo,nm_ in ((a['mx'],b['mn'],a),(b['mx'],a['mn'],b)):
                if lo>0 and f>=2 and abs(hi/lo-f)/f<=0.03:
                    sig='FACTOR'; why=f"{hi:g} ÷ {lo:g} = ×{f:g} (pack {a['uom']} vs {b['uom']})"
    if sig!='FACTOR' and ratio>=3: sig='GAP'; why=f'cost per unit varies ×{ratio:.1f} across packs'
    sev={'FACTOR':'high','GAP':'medium','MIX':'low'}[sig]
    last=max(v['last'] for v in vs)
    uom.append(dict(product=p,product_name=nm.get(p) or (S['products'].get(p) or {}).get('name') or p,packs=' / '.join(f"{v['uom']}" for v in vs),
       n_packs=len(vs),lines=sum(v['lines'] for v in vs),min_cost=round(allmin,4),max_cost=round(allmax,4),ratio=round(min(ratio,999),1),
       signal=sig,reason=why,severity=sev,last_purchase=last,on_hand=ohq.get(p,0),on_hand_value=round(ohv.get(p,0),2),
       variants=[dict(uom=v['uom'],factor=v['factor'],lines=v['lines'],qty=v['qty'],min_cost=round(v['mn'],4),max_cost=round(v['mx'],4),last=v['last']) for v in vs]))
order={'high':0,'medium':1,'low':2}
uom.sort(key=lambda r:(order[r['severity']],-r['on_hand_value']))
c=collections.Counter(r['severity'] for r in uom)
out['uom']=dict(rows=uom,kpi=dict(skus=len(uom),high=c['high'],medium=c['medium'],low=c['low'],value_high=round(sum(r['on_hand_value'] for r in uom if r['severity']=='high'),2),
   value_all=round(sum(r['on_hand_value'] for r in uom),2),since='2025-01-01'))
json.dump(out,open('checks.json','w'),ensure_ascii=False)
print(out['savings']['kpi']); print(out['ct']['kpi']); print(out['uom']['kpi'])
for r in uom[:8]: print(r['product'],r['severity'],r['reason'],r['on_hand_value'])
for r in ct[:6]: print(r['product'],r['branch'],r['ct_qty'],r['on_hand'],r['ct_value'],r['in_overstock'],r['in_slow'])
