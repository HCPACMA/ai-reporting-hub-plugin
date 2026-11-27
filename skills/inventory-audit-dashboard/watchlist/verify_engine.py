import json, sys
from datetime import datetime
sys.path.insert(0,'.')
import pricing_engine as pe
SCR='/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad'
h=open(f'{SCR}/dashboard_askai.html',encoding='utf-8').read()
i=h.index('<script id="audit-data" type="application/json">')+len('<script id="audit-data" type="application/json">')
A=json.loads(h[i:h.index('</script>',i)])
old=json.load(open('/mnt/user-data/uploads/Inventory/alfaihaa/watchlist/pi_rows_old_snapshot.json'))
names=json.load(open('/mnt/user-data/uploads/Inventory/alfaihaa/watchlist/product_names_state.json'))
rows=[dict(org=o,product=p,supplier_no=s,supplier_name=sn,date=datetime.fromisoformat(d) if d else None,primary_qty=q,unit_cost=c,item_discount=a,invoice_discount=b) for o,p,s,sn,d,q,c,a,b in old]
B=pe.build_blocks(rows,names)
def cmp(label,a,b):
    ok = json.dumps(a,sort_keys=True,ensure_ascii=False)==json.dumps(b,sort_keys=True,ensure_ascii=False)
    print(('OK   ' if ok else 'DIFF ')+label, len(a) if hasattr(a,'__len__') else a)
    return ok
def norm_matrix(m): return sorted(m,key=lambda r:(r['product'],r['supplier_no']))
res=[]
res.append(cmp('purchases_by_supplier',B['purchases_by_supplier'],A['purchases_by_supplier']))
res.append(cmp('matrix',norm_matrix(B['product_supplier_price_matrix']),norm_matrix(A['product_supplier_price_matrix'])))
res.append(cmp('savings',sorted(B['supplier_savings_opportunities'],key=lambda r:r['product']),sorted(A['supplier_savings_opportunities'],key=lambda r:r['product'])))
res.append(cmp('outliers',norm_matrix(B['price_outliers_flagged']),norm_matrix(A['price_outliers_flagged'])))
res.append(cmp('price_gap_kpi',B['price_gap_savings_identified'],A['kpi']['price_gap_savings_identified']))
V=B['vendor']; AV=A['vendor_concentration']
res.append(cmp('vendor.kpi',V['kpi'],AV['kpi']))
res.append(cmp('vendor.top_suppliers',V['top_suppliers'],AV['top_suppliers']))
res.append(cmp('vendor.by_branch',V['by_branch'],AV['by_branch']))
res.append(cmp('vendor.single_source',sorted(V['single_source_products'],key=lambda r:r['product']),sorted(AV['single_source_products'],key=lambda r:r['product'])))
print('ALL OK' if all(res) else 'SOME DIFF')
if not all(res):
    # show first difference for matrix
    a=norm_matrix(B['product_supplier_price_matrix']); b=norm_matrix(A['product_supplier_price_matrix'])
    for x,y in zip(a,b):
        if x!=y: print(x,'\n',y); break
