"""Price changes between consecutive invoices — same product, same supplier.
Inputs : pi_rows_with_inv.json  [product, supplier_no, PINV_NO, yymmdd, primary_qty, net_unit_cost, supplier_invoice_no]
         attachments.json       [PINV_NO, image_id, yymmdd, file_name]
Output : price_changes.json (data block embedded as AUDIT.price_changes)
Rule   : per (product, supplier) the lines are grouped by purchase invoice (volume-weighted net price per primary unit);
         consecutive invoices whose price differs by >= 0.01 SAR and >= 0.05% form one event.
         SAR effect = (new price - old price) x quantity on the new invoice (positive = paid more).
Returns: purchase returns (IM_PURCHASE_INVOICE_RETURN_M.PINV_NO) are netted out of the invoice lines first; an invoice line returned in
         full is not a price (it never stayed), a partial return reduces the quantity.  Events that touch a returned line are listed
         separately (events_returned) and are excluded from every headline figure.
"""
import json, sys
from collections import defaultdict
from datetime import datetime
sys.path.insert(0, '../returns')
import net as RN

AS_OF = datetime(2026, 10, 20)
WINDOW_DAYS = 90
NEW_DAYS = 14

rows = json.load(open('pi_rows_with_inv.json'))
att = json.load(open('attachments.json'))
names = json.load(open('/home/claude/w/watch/product_names_state.json'))
names['105262'] = 'OMISEC 40MG VIAL'
sup = json.load(open('../supplier_names.json'))

def iso(d):
    return datetime.strptime(d, '%y%m%d').strftime('%Y-%m-%d')

# attachments per invoice
att_by = defaultdict(list)
for doc, iid, d, fn in att:
    att_by[doc].append([int(iid), fn.lstrip('\\')])
for v in att_by.values():
    v.sort()

def build(rows, rinfo):
    g = defaultdict(lambda: [0.0, 0.0, None, None])
    skipped = 0
    for p, s, inv, d, q, c, o in rows:
        q = float(q); c = float(c)
        if q <= 0 or c <= 0:
            skipped += 1; continue
        x = g[(p, s, inv)]
        x[0] += q; x[1] += q * c; x[2] = d; x[3] = o
    by = defaultdict(list)
    for (p, s, inv), (q, v, d, o) in g.items():
        by[(p, s)].append((d, inv, q, v / q, o))

    def side(t):
        d, inv, q, px, o = t
        return {'inv': inv, 'd': iso(d), 'px': round(px, 6), 'q': round(q, 4), 'so': o, 'att': att_by.get(inv, [])}

    events = []
    for (p, s), l in by.items():
        l.sort()
        for i, (a, b) in enumerate(zip(l, l[1:])):
            diff = b[3] - a[3]
            if abs(diff) < 0.01 or abs(b[3] / a[3] - 1) < 0.0005:
                continue
            pct = (b[3] / a[3] - 1) * 100
            days = (datetime.strptime(b[0], '%y%m%d') - datetime.strptime(a[0], '%y%m%d')).days
            events.append({
                'id': f'pc__{p}__{s}__{b[1][-6:]}',
                'p': p, 'pn': names.get(p, p), 's': s, 'sn': sup.get(s, s),
                'from': side(a), 'to': side(b),
                'pct': round(pct, 2), 'sar': round(diff * b[2], 2), 'days': days,
                'dir': 'up' if diff > 0 else 'down',
                'x': (b[3] / a[3] >= 3 or b[3] / a[3] <= 1 / 3),
                'latest': i == len(l) - 2,
                'n_inv': len(l),
            })
    return g, by, skipped, events

RET = RN.load_returns('../returns/returns.json')
_, rinfo = RN.net_rows(rows, RET)
net_rows, RET_INV = RN.exclude_returned_invoices(rows, RET)   # whole invoice excluded (rule of 21 Oct 2026)
g, by, skipped, events = build(net_rows, rinfo)
g_all, by_all, _, events_all = build(rows, rinfo)

def ret_side(inv, p):
    i = rinfo.get((inv, p))
    if not i:
        if inv in RET_INV:   # another line of a returned invoice: the whole invoice is excluded
            return {'qty': 0, 'of': 0, 'full': False, 'docs': [], 'd': '', 'val': 0}
        return None
    return {'qty': round(i['ret_qty'], 4), 'of': round(i['inv_qty'], 4), 'full': i['full'], 'docs': i['docs'], 'd': i['ret_date'], 'val': round(i['ret_val'], 2)}

# gross events that touch a returned invoice line (the line the price came from or went to)
events_returned = []
for e in events_all:
    rf, rt = ret_side(e['from']['inv'], e['p']), ret_side(e['to']['inv'], e['p'])
    if rf or rt:
        e = dict(e); e['ret_from'] = rf; e['ret_to'] = rt
        full = (rt and rt['full']) or (rf and rf['full'])
        e['ret_status'] = 'full' if full else 'partial'
        events_returned.append(e)
events.sort(key=lambda e: (e['to']['d'], e['id']), reverse=True)
events_returned.sort(key=lambda e: (e['to']['d'], e['id']), reverse=True)

win_start = (AS_OF - __import__('datetime').timedelta(days=WINDOW_DAYS - 1)).strftime('%Y-%m-%d')  # same window start as the watch-list (90 days incl. as-of)
new_start = (AS_OF - __import__('datetime').timedelta(days=NEW_DAYS)).strftime('%Y-%m-%d')
rec = [e for e in events if e['to']['d'] >= win_start]
kpi = {
    'as_of': AS_OF.strftime('%Y-%m-%d'), 'window_start': win_start, 'window_days': WINDOW_DAYS,
    'new_since': new_start, 'new_days': NEW_DAYS,
    'events_total': len(events), 'events_window': len(rec),
    'up_window': sum(1 for e in rec if e['dir'] == 'up'), 'down_window': sum(1 for e in rec if e['dir'] == 'down'),
    'extreme_window': sum(1 for e in rec if e['x']),
    'up_sar_window': round(sum(e['sar'] for e in rec if e['dir'] == 'up' and not e['x']), 2),
    'down_sar_window': round(sum(e['sar'] for e in rec if e['dir'] == 'down' and not e['x']), 2),
    'up_extreme_sar_window': round(sum(e['sar'] for e in rec if e['dir'] == 'up' and e['x']), 2),
    'new_events': sum(1 for e in events if e['to']['d'] >= new_start),
    'pairs_tracked': len(by), 'pairs_with_2plus_invoices': sum(1 for l in by.values() if len(l) >= 2),
    'invoices_total': len({k[2] for k in g}), 'invoices_with_scan': len({k[2] for k in g if k[2] in att_by}),
    'lines_excluded_zero': skipped,
    'events_both_scanned_window': sum(1 for e in rec if e['from']['att'] and e['to']['att']),
}
kpi.update({
    'returns_lines': len(RET), 'returns_docs': len({r['ret_no'] for r in RET}), 'returns_value': round(sum(r['val'] for r in RET), 2),
    'invoice_lines_returned_full': sum(1 for v in rinfo.values() if v['full']), 'invoice_lines_returned_partial': sum(1 for v in rinfo.values() if not v['full']),
    'events_returned_total': len(events_returned),
    'events_returned_window': sum(1 for e in events_returned if e['to']['d'] >= win_start),
    'events_returned_sar_window': round(sum(e['sar'] for e in events_returned if e['to']['d'] >= win_start and e['dir'] == 'up'), 2),
    'events_gross_total': len(events_all),
})
out = {'kpi': kpi, 'events': events, 'events_returned': events_returned}
json.dump(out, open('price_changes.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(json.dumps(kpi, indent=1))
print(len(json.dumps(out, ensure_ascii=False)) // 1024, 'KB')
