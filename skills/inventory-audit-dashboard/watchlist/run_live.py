"""Live purchasing refresh with purchase returns netted out (see ../returns/net.py).
Inputs : ../pc/pi_rows_with_inv.json (PI lines with invoice no.), ../returns/returns.json (PR lines linked by PINV_NO)
Output : live_result.json = {blocks, watchlist, returns} - blocks and watch-list are built on NET lines;
         'returns' carries the gross -> net bridge and the alerts that disappear because the quantity was returned."""
import json, sys
from datetime import datetime
sys.path.insert(0, '.'); sys.path.insert(0, 'returns')
import pricing_engine as pe
import net as RN

AS_OF = datetime(2026, 10, 3)
sup = json.load(open('supplier_names.json'))
names = json.load(open('/mnt/user-data/uploads/Inventory/alfaihaa/watchlist/product_names_state.json'))
raw = json.load(open('price_changes/pi_rows_with_inv.json'))
RET = RN.load_returns('returns/returns.json')
net_raw, rinfo = RN.net_rows(raw, RET)

def to_rows(lst):
    return [dict(org='01', product=p, supplier_no=s, supplier_name=sup.get(s, s), date=datetime.strptime(d, '%y%m%d'),
                 primary_qty=float(q), unit_cost=float(c), item_discount=0.0, invoice_discount=0.0, inv=inv)
            for p, s, inv, d, q, c, o in lst]
rows_g, rows_n = to_rows(raw), to_rows(net_raw)

B = pe.build_blocks(rows_n, names)
WL = pe.build_watchlist(rows_n, names, AS_OF, supname=dict(sup))
WLg = pe.build_watchlist(rows_g, names, AS_OF, supname=dict(sup))

def val(rs): return sum(r['primary_qty'] * r['unit_cost'] for r in rs if r['primary_qty'] > 0 and r['unit_cost'] > 0)
ret_prod = {r['p'] for r in RET}
net_ids = {a['id'] for a in WL['alerts']}
cleared = []
for a in WLg['alerts']:
    if a['id'] not in net_ids and a['product'] in ret_prod:
        rl = [r for r in RET if r['p'] == a['product']]
        a = dict(a); a['returns'] = [{'ret_no': r['ret_no'], 'pinv': r['pinv'], 'qty': r['qty'], 'val': r['val'], 'd': r['ret_date']} for r in rl]
        cleared.append(a)
changed = []
gm = {a['id']: a for a in WLg['alerts']}
for a in WL['alerts']:
    g = gm.get(a['id'])
    if g and abs(g['impact'] - a['impact']) >= 1 and a['product'] in ret_prod:
        changed.append({'id': a['id'], 'impact_gross': g['impact'], 'impact_net': a['impact']})
WL['returns_effect'] = {
    'alerts_gross': len(WLg['alerts']), 'alerts_net': len(WL['alerts']),
    'unique_sar_gross': WLg['kpi']['unique_sar_90d'], 'unique_sar_net': WL['kpi']['unique_sar_90d'],
    'cleared_by_return': cleared, 'cleared_sar': round(sum(a['impact'] for a in cleared), 2),
    'reduced_by_return': changed,
}
ret_bridge = {
    'lines_gross': len([r for r in rows_g if r['primary_qty'] > 0 and r['unit_cost'] > 0]),
    'lines_net': len([r for r in rows_n if r['primary_qty'] > 0 and r['unit_cost'] > 0]),
    'spend_gross': round(val(rows_g), 2), 'spend_net': round(val(rows_n), 2),
    'returns_value': round(sum(r['val'] for r in RET), 2), 'returns_lines': len(RET), 'returns_docs': len({r['ret_no'] for r in RET}),
    'invoice_lines_returned_full': sum(1 for v in rinfo.values() if v['full']),
    'invoice_lines_returned_partial': sum(1 for v in rinfo.values() if not v['full']),
}
json.dump({'blocks': B, 'watchlist': WL, 'returns': ret_bridge}, open('live_result.json', 'w'), ensure_ascii=False)
print(json.dumps(ret_bridge, indent=1)); print(json.dumps(WL['kpi'], indent=1))
print('returns_effect', {k: v for k, v in WL['returns_effect'].items() if k not in ('cleared_by_return', 'reduced_by_return')})
for a in WL['returns_effect']['cleared_by_return']: print('cleared', a['type'], a['product'], a['product_name'][:30], a['supplier_name'][:20], a['impact'])
for a in WL['returns_effect']['reduced_by_return']: print('reduced', a)
print('vendor', B['vendor']['kpi'], B['price_gap_savings_identified'])
