"""Purchase returns (PR) -> returns.json
Rule: a purchase return is linked to its purchase invoice through IM_PURCHASE_INVOICE_RETURN_M.PINV_NO.
Per (purchase invoice, product): returned qty is netted out of that invoice line before any price test.
Identity-review flags (a returned line is a candidate for 'entered under another item'):
  price_off  : the line price is >=3x or <=1/3 of the product's median price on its other 2026 invoices
  full       : the returned qty is the whole invoiced qty (entered and reversed)
  moved      : stock of that product was dispensed / transferred after the receipt and before the return (cost trace)
  cross_month: return posted in a later month than the receipt (period cut-off)
  no_reason  : the return document carries no reason in NOTES (true for 22/22)
"""
import json, statistics, sys
from collections import defaultdict
from datetime import datetime
sys.path.insert(0, '.')
import raw_returns as R

names = json.load(open('/mnt/user-data/uploads/Inventory/alfaihaa/watchlist/product_names_state.json'))
sup = json.load(open('../supplier_names.json'))
pi = json.load(open('../price_changes/pi_rows_with_inv.json'))   # product, supplier, PINV, yymmdd, qty, cost, supplier invoice

def rows(txt): return [l.split('|') for l in txt.splitlines()]
B = {(r[0], r[1]): r for r in rows(R.B)}
C = {(r[0], r[1]): r for r in rows(R.C)}

inv_qty = defaultdict(float); inv_val = defaultdict(float); price_lines = defaultdict(list)
for p, s, inv, d, q, c, o in pi:
    q = float(q); c = float(c)
    if q > 0 and c > 0:
        inv_qty[(inv, p)] += q; inv_val[(inv, p)] += q * c
        price_lines[p].append((inv, c, q))

ret_tot = defaultdict(float)
for r in rows(R.A):
    ret_tot[(r[2], r[4])] += float(r[5])

out = []
for r in rows(R.A):
    ret_no, rd, pinv, s, p, q, c, user, st = r
    q = float(q); c = float(c)
    b = B[(ret_no, p)]; m = C[(ret_no, p)]
    pi_date, pi_q, disp = b[2], float(b[3]), float(b[4])
    n_mv, q_mv, q_rc, v_rc = int(m[2]), float(m[3]), float(m[4]), float(m[5])
    others = [x[1] for x in price_lines[p] if x[0] != pinv]
    med = statistics.median(others) if len(others) >= 2 else None
    pi_price = inv_val[(pinv, p)] / inv_qty[(pinv, p)] if inv_qty[(pinv, p)] else c
    mv = R.D.get((ret_no, p))
    ref = med if med else ((mv[0] + mv[1]) / 2 if mv else None)
    ref_src = 'median of other invoices' if med else ('ERP cost on later stock movements' if mv else None)
    ratio = pi_price / ref if ref else None
    price_off = bool(ratio and (ratio >= 3 or ratio <= 1 / 3))
    full = ret_tot[(pinv, p)] >= pi_q - 1e-9
    d0 = datetime.strptime(pi_date, '%Y-%m-%d'); d1 = datetime.strptime(rd, '%Y-%m-%d')
    flags = {'price_off': price_off, 'full': full, 'moved': q_mv > 0, 'cross_month': pi_date[:7] != rd[:7], 'no_reason': True}
    score = 2 * price_off + 1 * full + 1 * (q_mv > 0) + 1 * flags['cross_month'] + 1 * (q * c >= 5000)
    out.append({
        'ret_no': ret_no, 'ret_date': rd, 'pinv': pinv, 's': s, 'sn': sup.get(s, s), 'p': p, 'pn': names.get(p) or b[5],
        'erp_name': b[5], 'qty': q, 'cost': round(c, 5), 'val': round(q * c, 2),
        'pi_date': pi_date, 'pi_qty': pi_q, 'pi_price': round(pi_price, 5), 'ret_tot_qty': ret_tot[(pinv, p)],
        'days': (d1 - d0).days, 'med': round(ref, 4) if ref else None, 'ref_src': ref_src, 'ratio': round(ratio, 2) if ratio else None,
        'moved_qty': q_mv, 'moved_n': n_mv, 'disp_qty': disp, 'moved_at_ret_cost_qty': q_rc, 'moved_at_ret_cost_val': v_rc,
        'user': user, 'store': st, 'flags': flags, 'score': score,
        'level': 'high' if score >= 4 else ('medium' if score >= 2 else 'low'),
    })
json.dump(out, open('returns.json', 'w'), ensure_ascii=False, indent=0)
tot = sum(o['val'] for o in out)
print(len(out), 'lines', len({o['ret_no'] for o in out}), 'docs', round(tot, 2), 'SAR')
print({k: sum(1 for o in out if o['level'] == k) for k in ('high', 'medium', 'low')})
for o in sorted(out, key=lambda o: -o['score']):
    print(o['score'], o['level'], o['ret_no'], o['p'], o['pn'][:28], o['qty'], o['val'], 'ratio', o['ratio'], 'full', o['flags']['full'], 'mv', o['moved_qty'], 'xm', o['flags']['cross_month'], o['days'])
