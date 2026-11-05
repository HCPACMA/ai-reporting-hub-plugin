"""DATA.drv — Deep Analysis drivers.

ser[acc|cc|fn]      monthly GL amounts                        -> money
dser[dept] = [cash[], credit[], cost[]]                       -> money (all three)
vis[] = [br, payType, speciality, doctor, eps[], rev[], revNP[]]
        eps = visit (episode) counts -> keep; rev / revNP = invoice revenue -> money; doctor -> A.person
"""
NON_PERSON = {'(no doctor)', 'Doctor Ruh', 'Health Certification', 'Home Care',
              'Laser Department', 'Vaccination Department'}


def _s(A, x):
    v = A.S(x)
    if isinstance(x, int) and not isinstance(x, bool) and isinstance(v, float) and v == int(v):
        return int(v)            # keep ints as ints where the scaled value is whole
    return v


def _arr(A, a):
    return [_s(A, x) for x in a]


def transform(d, A):
    d['br'] = {k: A.names(v) for k, v in (d.get('br') or {}).items()}
    d['src'] = A.text(d.get('src'), money=False)
    d['ser'] = {k: _arr(A, v) for k, v in d['ser'].items()}
    d['acc'] = {k: [A.names(x) for x in v] for k, v in d['acc'].items()}
    d['dept'] = {k: [v[0]] + [A.names(x) for x in v[1:]] for k, v in d['dept'].items()}
    d['dser'] = {k: [_arr(A, s) for s in v] for k, v in d['dser'].items()}
    out = []
    for r in d['vis']:
        br, pt, sp, doc, eps, rev, revnp = r
        doc2 = A.names(doc) if doc in NON_PERSON else A.person(doc, 'dr')
        out.append([br, pt, A.names(sp), doc2, eps, _arr(A, rev), _arr(A, revnp)])
    d['vis'] = out
    return d
