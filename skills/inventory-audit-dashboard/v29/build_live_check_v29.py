"""Change since the 8 Sep snapshot (block live_check, V29): previous audit state (8 Sep) vs the new full re-extract (5 Oct)."""
import json, pickle
from collections import defaultdict
old=pickle.load(open('_state.pkl','rb'))
new=pickle.load(open('pipe/Inventory/alfaihaa/_state.pkl','rb'))
ext=pickle.load(open('new_extract.pkl','rb'))['Transactions 2026']
AS_OF=str(new['as_of'])[:10]; SNAP=str(old['as_of'])[:10]
bn={'01':'Riyadh','02':'Buraydah 1','03':'Buraydah 2','04':'Rafha'}
by=defaultdict(lambda:{'sku_live':0,'qty_live':0.0,'val_live':0.0,'est_lines':0,'est_val':0.0,'sku_snap':0,'qty_snap':0.0,'val_snap':0.0})
prod=defaultdict(lambda:[0.0,0.0]); names={}
snapk={(b['org'],b['store'],b['product']) for b in old['balances']}; livek=set()
sn={}
for b in new['balances']:
    k=(b['org'],b['store'],b['product']); livek.add(k); names[b['product']]=b['product_name']; sn[(b['org'],b['store'])]=b['store_name']
    a=by[(b['org'],b['store'])]; v=b['on_hand_cost'] or 0.0
    a['sku_live']+=1; a['qty_live']+=b['on_hand']; a['val_live']+=v; prod[b['product']][1]+=v
    if b['cost_is_estimated']: a['est_lines']+=1; a['est_val']+=v
for b in old['balances']:
    a=by[(b['org'],b['store'])]; v=b['on_hand_cost'] or 0.0
    a['sku_snap']+=1; a['qty_snap']+=b['on_hand']; a['val_snap']+=v; prod[b['product']][0]+=v; names.setdefault(b['product'],b['product_name']); sn.setdefault((b['org'],b['store']),b['store_name'])
rows=[{'org':o,'branch':bn[o],'store':s,'store_name':sn[(o,s)],**{k:(round(v,2) if isinstance(v,float) else v) for k,v in a.items()}} for (o,s),a in sorted(by.items())]
tot={k:round(sum(r[k] for r in rows),2) for k in ['sku_live','qty_live','val_live','est_lines','est_val','sku_snap','qty_snap','val_snap']}
tot['delta_val']=round(tot['val_live']-tot['val_snap'],2); tot['delta_pct']=round(100*tot['delta_val']/tot['val_snap'],1)
mv=sorted(((v[1]-v[0],p,v) for p,v in prod.items()),key=lambda x:x[0])
row=lambda d,p,v:{'product':p,'name':names.get(p,p),'val_snap':round(v[0],2),'val_live':round(v[1],2),'delta':round(d,2)}
h,rs=ext; ix={x:i for i,x in enumerate(h)}
cnt=defaultdict(int); pil=0
for r in rs:
    d=r[ix['transaction_date']]
    if d[:10]>SNAP:
        cnt[r[ix['t_type']]]+=1
out={'as_of':AS_OF,'snapshot_as_of':SNAP,'rows':rows,'total':tot,
 'new_lines_since_snapshot':len(livek-snapkeys) if (snapkeys:=snapk) else 0,
 'dropped_lines_since_snapshot':len(snapk-livek),
 'top_down':[row(*x) for x in mv[:10]],'top_up':[row(*x) for x in mv[::-1][:10]],
 'activity':{'window':f'{SNAP}..{AS_OF}','dispense':cnt['DS'],'transfer_sent':cnt['TS'],'transfer_received':cnt['TR'],'purchase_lines_all_status':cnt['PI'],'purchase_lines_since_oct1':sum(1 for r in rs if r[ix['t_type']]=='PI' and r[ix['transaction_date']]>='2026-10-01'),'receipts_crc':cnt['CRC'],'returns_pr':cnt['PR']},
 'basis':f'Every tab now runs on the full live re-extract of {AS_OF} (all 2026 transactions, stock balances, batches). This section compares it with the {SNAP} snapshot the previous version was built on; both are valued at the last posted unit cost of the same branch / store / product.'}
json.dump(out,open('live_check_v29.json','w'),ensure_ascii=False,separators=(',',':'))
print(json.dumps(out['total']),out['new_lines_since_snapshot'],out['dropped_lines_since_snapshot'],out['activity'])
