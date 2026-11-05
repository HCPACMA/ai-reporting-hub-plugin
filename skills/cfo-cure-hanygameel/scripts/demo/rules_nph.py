from rules_arx import tx, nm, user
def transform(d, A):
    S, D = A.S, A.digits
    for r in d['rows']:
        r[2] = D(r[2])
        for i in (3, 4, 5, 8, 9, 10, 22): r[i] = S(r[i])
        for m in (r[14] or []): m[2] = S(m[2])
        r[17] = tx(r[17], A, money=False)
        if r[21] is not None and isinstance(r[21], str) and r[21].startswith('700'): r[21] = D(r[21])
    d['ins'] = {D(k): v for k, v in d['ins'].items()}
    for v in d['ins'].values():
        v['id'] = D(v['id'])
        for k in ('en', 'ar', 'via', 'carrier'):
            if k in v: v[k] = nm(v[k], A)
        for b in v.get('book', []): b[1] = nm(b[1], A)
    d['subs'] = {k: tx(v, A, money=False) for k, v in d['subs'].items()}
    for g in d['gl']:
        g[3] = S(g[3]); g[5] = tx(g[5], A)
        if isinstance(g[7], dict):
            g[7]['ins'] = D(g[7].get('ins')) if g[7].get('ins') else g[7].get('ins')
            if 'tot' in g[7]: g[7]['tot'] = S(g[7]['tot'])
            g[7]['kind'] = tx(g[7].get('kind'), A)
    d['cover'] = {D(k): v for k, v in d['cover'].items()}
    d['subIns'] = {k: [D(x) for x in v] for k, v in d['subIns'].items()}
    return d
