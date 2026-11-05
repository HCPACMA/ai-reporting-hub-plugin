import re
from namestrip import strip
EXTRA = [(re.compile(r'Al[\s-]?Jazira?h?\s+Takaful', re.I), 'Sigma Takaful'), (re.compile(r'Jazira?h?', re.I), 'Sigma'),
         (re.compile(r'اكسا'), 'فيكتور'), (re.compile(r'\bNext\s?Care\b', re.I), 'OrbitTPA')]
def nm(s, A):
    if not isinstance(s, str): return s
    for p, r in EXTRA: s = p.sub(r, s)
    return A.names(s)
def tx(s, A, money=True):
    if not isinstance(s, str): return s
    for p, r in EXTRA: s = p.sub(r, s)
    return strip(A.text(s, money=money), A)
def user(v, A):
    if not isinstance(v, str) or not v: return v
    x = re.match(r'^(.*?)\s*(\(\s*[^()]*\s*\))\s*$', v)
    if not x: return A.person(v, 'user')
    return A.person(x.group(1), 'user') + ' ' + x.group(2)
def transform(d, A):
    S = A.S
    for x in d['dups']:
        x['amt'] = S(x['amt']); x['extra'] = S(x['extra']); x['ref'] = A.ref(x['ref']); x['cust'] = nm(x['cust'], A)
    for r in d['rows']:
        r['user'] = user(r['user'], A); r['cust'] = nm(r['cust'], A)
        r['amt'] = S(r['amt']); r['bank'] = S(r['bank'])
        r['desc'] = tx(r['desc'], A)
        for sp in r['split']:
            sp['amt'] = S(sp['amt']); sp['desc'] = tx(sp['desc'], A)
        for o in r['other']:
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, (int, float)) and not isinstance(v, bool): o[k] = S(v)
                    elif isinstance(v, str): o[k] = tx(v, A)
        t = r['tr']
        if t:
            t['amt'] = S(t.get('amt')); t['payer'] = tx(t.get('payer'), A, False); t['ref'] = A.ref(t.get('ref'))
            t['det'] = tx(t.get('det'), A); t['hand'] = nm(t.get('hand'), A)
        for dc in r['docs']:
            for k in ('paid', 'cl', 'amt'): dc[k] = S(dc[k])
            dc['brn'] = nm(dc['brn'], A); dc['ins'] = nm(dc['ins'], A); dc['n'] = tx(dc['n'], A)
        for i in r['iss']:
            i['en'] = tx(i['en'], A)
    return d
