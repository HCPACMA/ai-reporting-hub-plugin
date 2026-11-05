import re
from gen import walk
KEEP = {'years', 'openYear', 'y', 'days', 'rate'}
def transform(d, A):
    def keep(p):
        if p[0] in ('years', 'openYear'): return True
        if p[-1] in KEEP: return True
        if len(p) >= 4 and p[2] == 'finesG' and p[-1] == 2: return True   # count of fines
        return False
    def sf(s, p):
        # capital / partner current-account owners: "رأس المال - د.علي ..." -> person label
        if len(p) >= 5 and p[2] == 'eq' and p[-1] == 2 and ' - ' in s:
            head, tail = s.split(' - ', 1)
            return head + ' - ' + A.person(re.sub(r'^د\.?\s*', '', tail.strip()), 'person')
        t = A.text(s, money=True)
        if 'اقام' in t:
            t = re.sub(r'(/\s*)([\u0621-\u064A]+(?:\s+[\u0621-\u064A]+){1,4}?)(\s+ف\s+حساب|\s*$)', lambda m: m.group(1) + A.person(m.group(2), 'emp') + m.group(3), t)
        return t
    return walk(d, A, keep, sf)
