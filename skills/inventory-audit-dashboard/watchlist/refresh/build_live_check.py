"""Live stock re-valuation vs the 2026-09-08 snapshot (block `live_check`).
Inputs: live_balances.json  [product, org_raw, store, onhand]  (VINV_STORE_PRODUCTS, ONHAND<>0, pulled live)
        _state.pkl balances (snapshot qty + unit cost per org/store/product)
        est_costs: last posted unit cost for products new since the snapshot (live query, flagged estimated)
Value  = live on-hand x snapshot unit cost of the same org/store/product (same proxy as the main audit).
"""
import json, pickle, sys
from collections import defaultdict
AS_OF='2026-10-03'; SNAP='2026-09-08'
live=json.load(open('live_balances.json'))
st=pickle.load(open('/mnt/user-data/uploads/Inventory/alfaihaa/_state.pkl','rb'))
est={'0050462':9.8175,'0050873':112.2,'0100219':0.97,'0100319':652.17,'0170411':2.1839,'0180026':5.5619,'0220091':22.7247,'0220142':155.0,'0250021':96.9995,'0250024':77.5996,'0250028':17.3026,'0320045':180.6899,'0320047':358.5999,'0320105':77.6388,'0330026':24.4,'0330331':4.8384,'0330341':1.0084,'0330361':13.5086,'0360041':55.0154,'0390038':55.9733,'0390096':29.9706,'0390140':7.4791,'0390166':3.0,'0390279':39.27,'0390294':10.2564,'0390475':13.2506,'0390478':4.4377,'102403':128.4464,'104001':4.85,'104228':9.4,'104844':4.159,'105124':19.635,'105262':8.0,'3100068':1.44,'3200126':145.7686,'330391':420.1153}
orgmap={'01011301':'01','01011302':'01','02011301':'02','03011301':'03','04011301':'04'}
bn={'01':'Riyadh','02':'Buraydah 1','03':'Buraydah 2','04':'Rafha'}
snap={(b['org'],b['store'],b['product']):b for b in st['balances']}
stores={'2':'Main Store','7':'Dialysis Store','3':'Buridah-1 Store','4':'Buridah-2 Store','5':'Rafha Store'}
by=defaultdict(lambda:{'sku_live':0,'qty_live':0.0,'val_live':0.0,'est_lines':0,'est_val':0.0,'sku_snap':0,'qty_snap':0.0,'val_snap':0.0})
prod=defaultdict(lambda:[0.0,0.0])  # product -> [val_snap, val_live]
names={b['product']:b['product_name'] for b in st['balances']}
seen=set()
for p,o,s,q in live:
    org=orgmap[o]; k=(org,s,p); b=snap.get(k)
    if b: c=b['unit_cost']; e=False
    else: c=est[p]; e=True
    a=by[(org,s)]; a['sku_live']+=1; a['qty_live']+=q; a['val_live']+=q*c
    if e: a['est_lines']+=1; a['est_val']+=q*c
    prod[p][1]+=q*c; seen.add(k)
for k,b in snap.items():
    a=by[(k[0],k[1])]; a['sku_snap']+=1; a['qty_snap']+=b['on_hand']; a['val_snap']+=b['on_hand_cost']; prod[k[2]][0]+=b['on_hand_cost']
rows=[]
for (org,s),a in sorted(by.items()):
    rows.append({'org':org,'branch':bn[org],'store':s,'store_name':stores[s],**{k:(round(v,2) if isinstance(v,float) else v) for k,v in a.items()}})
tot={k:round(sum(r[k] for r in rows),2) for k in ['sku_live','qty_live','val_live','est_lines','est_val','sku_snap','qty_snap','val_snap']}
tot['delta_val']=round(tot['val_live']-tot['val_snap'],2); tot['delta_pct']=round(100*tot['delta_val']/tot['val_snap'],1)
mv=sorted(((v[1]-v[0],p,v) for p,v in prod.items()),key=lambda x:x[0])
def row(d,p,v): return {'product':p,'name':names.get(p,p),'val_snap':round(v[0],2),'val_live':round(v[1],2),'delta':round(d,2)}
out={'as_of':AS_OF,'snapshot_as_of':SNAP,'rows':rows,'total':tot,
     'new_lines_since_snapshot':sorted([k for k in seen if k not in snap]).__len__(),
     'dropped_lines_since_snapshot':len([k for k in snap if k not in seen]),
     'top_down':[row(*x) for x in mv[:10]],'top_up':[row(*x) for x in mv[::-1][:10]],
     'activity':{'window':'2026-09-09..2026-10-03','dispense':4263,'transfer_sent':315,'transfer_received':338,'purchase_lines_all_status':149,'purchase_lines_since_oct1':12,'receipts_crc':6,'returns_pr':26},
     'basis':'Live on-hand (VINV_STORE_PRODUCTS, pulled 2026-10-03) x snapshot unit cost; 36 products new since the snapshot use the last posted unit cost (flagged estimated). Overstock / slow-moving / expiry / ABC tabs stay on the 2026-09-08 snapshot.'}
json.dump(out,open('live_check.json','w'),ensure_ascii=False,separators=(',',':'))
print(json.dumps(out['total']),out['new_lines_since_snapshot'],out['dropped_lines_since_snapshot'])
for r in rows: print(r['branch'],r['store_name'],r['sku_snap'],r['sku_live'],r['val_snap'],r['val_live'])
print([ (x['product'],x['name'][:25],x['delta']) for x in out['top_down'][:6]])
print([ (x['product'],x['name'][:25],x['delta']) for x in out['top_up'][:6]])
