"""Net purchase invoice lines of purchase returns.
Rule: returned qty per (purchase invoice, product) is removed from that invoice's lines pro rata (prices unchanged);
an invoice line returned in full drops out of every price test.  Returns are matched by PINV_NO (IM_PURCHASE_INVOICE_RETURN_M)."""
import json
from collections import defaultdict

def load_returns(path='returns.json'):
    return json.load(open(path))

def net_rows(rows, returns):
    """rows: [product, supplier_no, PINV, yymmdd, qty, cost, supplier_inv] (strings); returns: list from returns.json
    -> (net rows in the same format, info{(pinv,product): {...}})"""
    ret = defaultdict(lambda: {'qty': 0.0, 'docs': [], 'val': 0.0})
    for r in returns:
        k = (r['pinv'], r['p'])
        ret[k]['qty'] += r['qty']; ret[k]['val'] += r['val']
        if r['ret_no'] not in ret[k]['docs']:
            ret[k]['docs'].append(r['ret_no'])
        ret[k]['date'] = r['ret_date']
    tot = defaultdict(float)
    for p, s, inv, d, q, c, o in rows:
        q = float(q); c = float(c)
        if q > 0 and c > 0:
            tot[(inv, p)] += q
    out = []
    for p, s, inv, d, q, c, o in rows:
        k = (inv, p); qf = float(q)
        if k in ret and tot[k] > 0 and qf > 0 and float(c) > 0:
            keep = max(0.0, 1.0 - ret[k]['qty'] / tot[k])
            if keep <= 1e-9:
                continue
            out.append([p, s, inv, d, repr(round(qf * keep, 6)), c, o])
        else:
            out.append([p, s, inv, d, q, c, o])
    info = {}
    for k, v in ret.items():
        t = tot.get(k, 0.0)
        info[k] = {'ret_qty': v['qty'], 'inv_qty': t, 'full': t > 0 and v['qty'] >= t - 1e-9, 'docs': v['docs'], 'ret_val': v['val'], 'ret_date': v['date']}
    return out, info


def exclude_returned_invoices(rows, returns):
    """Hany's rule (21 Oct 2026): a purchase invoice that has any return is not used in any price analysis
    (alerts, price changes, price matrix, savings, outliers).  Drops EVERY line of such invoices."""
    inv = {r['pinv'] for r in returns}
    return [r for r in rows if r[2] not in inv], inv
