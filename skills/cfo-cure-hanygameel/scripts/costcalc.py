import json, re, collections

def load_map():
    return json.load(open('costing_map.json'))

def parse_tests(note):
    """tests-per-pack from the Arabic/English note column; None when not stated."""
    if not note: return None
    n = str(note)
    nums = [int(x) for x in re.findall(r'(\d+)\s*test', n, flags=re.I)]
    if not nums: return None
    return nums          # may be several ("100 test - 1000 test - 400 test")

def item_costs():
    out = {}
    for l in open('items_cost.txt'):
        l = l.strip()
        if not l: continue
        p = l.split('|')
        if len(p) < 7: continue
        code, nm, avgc, lastd, lastc, q12, nd = p[:7]
        out[code] = {'nm': nm, 'avg': float(avgc or 0), 'ld': lastd,
                     'lc': float(lastc) if lastc else None,
                     'q12': float(q12 or 0), 'nd': int(nd or 0)}
    return out

def build():
    M = load_map(); IC = item_costs()
    rows = []            # enriched map lines
    svc = collections.defaultdict(list)
    for o in M:
        it = IC.get(o['item'])
        tests = parse_tests(o['note'])
        t = tests[0] if tests else None
        lab = o['dept'] == 'المختبر'
        # a lab line whose share is tiny is a consumption fraction of a shared
        # reagent (substrate, buffer), not a yield share — multiply, don't divide
        frac = (not lab) or (o['share'] or 0) < 0.05
        lc = it['lc'] if it else None
        status = 'ok'
        unit = None
        if it is None:            status = 'no_item'
        elif not lc:              status = 'no_dispense'   # zero cost price is not a cost
        elif not o['share']:      status = 'no_share'
        elif (not frac) and t is None: status = 'no_tests'
        else:
            unit = lc * o['share'] if frac else lc / (t * o['share'])
        if status == 'ok' and lab and frac: status = 'frac'
        r = dict(o, iname=(it['nm'] if it else ''), lc=lc, frac=frac,
                 ld=(it['ld'] if it else ''), q12=(it['q12'] if it else 0),
                 nd=(it['nd'] if it else 0), tests=t, unit=unit, status=status,
                 multi=bool(tests and len(tests) > 1))
        rows.append(r); svc[o['svc']].append(r)
    U = {}
    for s, rs in svc.items():
        bad = [r for r in rs if r['status'] not in ('ok', 'frac')]
        chk = [r for r in rs if r['status'] == 'frac']
        tot = sum(r['unit'] for r in rs if r['unit'] is not None)
        U[s] = {'unit': round(tot, 4), 'n': len(rs), 'bad': len(bad), 'chk': len(chk),
                'st': 'ok' if not bad else ('partial' if len(bad) < len(rs) else 'none'),
                'dept': rs[0]['dept'], 'name': rs[0]['sname'],
                'ld': max((r['ld'] for r in rs if r['ld']), default='')}
    return rows, U, IC

if __name__ == '__main__':
    rows, U, IC = build()
    st = collections.Counter(r['status'] for r in rows)
    print('map lines', len(rows), dict(st))
    print('services', len(U), dict(collections.Counter(u['st'] for u in U.values())))
    ok = {k: v for k, v in U.items() if v['st'] == 'ok'}
    xs = sorted(ok.items(), key=lambda kv: -kv[1]['unit'])
    print('most expensive:', [(k, round(v['unit'],2), v['name'][:22]) for k, v in xs[:6]])
    print('cheapest:', [(k, round(v['unit'],3), v['name'][:22]) for k, v in xs[-6:]])
