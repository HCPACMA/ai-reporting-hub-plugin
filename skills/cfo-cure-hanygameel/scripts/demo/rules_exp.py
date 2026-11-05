import re
from namestrip import strip
def user(v, A):
    if not isinstance(v, str) or not v: return v
    x = re.match(r'^(.*?)\s*(\(\s*[^()]*\s*\))\s*$', v)
    if not x: return A.person(v, 'user')
    if x.group(1).lower().startswith('central database user'): return v
    return A.person(x.group(1), 'user') + ' ' + x.group(2)
from rules_aud import SAFE, AR_MON
def narr(r, names, A):
    t = r[11] or ''
    if any(p.fullmatch(t.strip()) for p in SAFE) or re.fullmatch(r'اثبات مصروف اهلاك اصول ثابتة عن شهر \S+ \d{4} م', t.strip()) or t.startswith('EXPENSES'):
        return A.names(t)
    y, m = r[3][:4], int(r[3][5:7])
    return '%s - شهر %s %s' % (A.names(names.get(r[1], 'مصروف')), AR_MON[m-1], y)
def transform(d, A):
    S = A.S
    for cc in d['mon'].values():
        for ac in cc.values():
            for ym, v in ac.items():
                v[0] = S(v[0]); v[1] = S(v[1])
    for r in d['lines']:
        r[4] = S(r[4]); r[5] = S(r[5])
        r[8] = user(r[8], A); r[9] = user(r[9], A)
        r[11] = narr(r, d['names'], A)
        if isinstance(r[10], str) and r[10]: r[10] = strip(A.text(r[10]), A)
    d['names'] = {k: A.names(v) for k, v in d['names'].items()}
    return d
