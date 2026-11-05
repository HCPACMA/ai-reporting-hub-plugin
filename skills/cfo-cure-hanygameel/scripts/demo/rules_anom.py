from contracts import contract
import re
NONP = re.compile(r'department|care\b|laborator|radiolog|^doctor\b|vaccin|certific|laser|\(no|pharmac|dressing|x-?ray|clinic|emergency|nurs', re.I)
def dr(s, A):
    if not isinstance(s, str) or not s.strip() or NONP.search(s): return A.names(s)
    return A.person(s, 'dr')
def emp(s, A):
    if not isinstance(s, str) or not s.strip() or NONP.search(s): return A.names(s)
    return A.person(s, 'emp')
def transform(d, A):
    S = A.S
    for k in ('daily', 'dailyNP'):
        d[k] = {kk: [S(x) for x in v] for kk, v in d[k].items()}
    for k in ('doc', 'docNP'):
        for r in d[k]:
            r[3] = dr(r[3], A); r[5] = S(r[5])
    for r in d['cash']:
        r[3] = emp(r[3], A)
        for i in (6, 7, 8, 10, 12, 14): r[i] = S(r[i])
    for r in d['lines']:
        r[4] = emp(r[4], A); r[5] = A.digits(r[5]); r[6] = dr(r[6], A); r[9] = contract(r[9], A)
        for i in (11, 12, 13): r[i] = S(r[i])
    for r in d['price']:
        r[4] = emp(r[4], A); r[5] = A.digits(r[5]); r[6] = dr(r[6], A); r[8] = contract(r[8], A)
        for i in (10, 11, 12, 14, 15): r[i] = S(r[i])
    for r in d['dup']:
        r[2] = A.digits(r[2]); r[7] = S(r[7]); r[8] = emp(r[8], A); r[5] = contract(r[5], A)
    for r in d['discpat']:
        r[1] = A.digits(r[1]); r[2] = emp(r[2], A); r[4] = S(r[4]); r[5] = S(r[5])
    return d
