#!/usr/bin/env python3
"""Build data/overtime_feas.<month>.json: per doctor x overtime day, revenue (cash C+D / credit R, no pharmacy) inside the overtime window.
inputs: raw/otf_entries.<m>.json, raw/otf_rev_part*.txt, raw/otf_svc.txt, data/overtime.<m>.json (rates)"""
import json, glob, re, sys
m = sys.argv[1] if len(sys.argv) > 1 else '2026-10'
ent = json.load(open('raw/otf_entries.%s.json' % m))['entries']
ot = json.load(open('data/overtime.%s.json' % m))
rate = {r['st']: r.get('rate') or 0 for r in ot['rows']}
OV = {2: [[22, 32]], 3: [[0, 8]], 4: [[0, 8]], 14: [[10, 17]], 15: [], 29: [], 74: []}
NOCLIN = {15: 'CBAHI', 29: 'CBAHI'}
rev = {}
for f in sorted(glob.glob('raw/otf_rev_part*.txt')):
    for ln in open(f, encoding='utf8'):
        ln = ln.strip()
        if not ln: continue
        k, v = ln.split('|'); i, j, d = k.split('_')
        o = rev.setdefault((int(i), int(d)), {'C': 0, 'R': 0, 'Ce': 0, 'Re': 0})
        for part in v.split(';'):
            t, a, e = part.split(':')
            if t in ('C', 'R'): o[t] += float(a); o[t + 'e'] += int(e)   # episodes summed over windows (a visit seen in two windows counts twice - rare)
svc = {}
for ln in open('raw/otf_svc.txt', encoding='utf8'):
    ln = ln.rstrip('\n')
    if not ln: continue
    parts = ln.split('|'); svc[int(parts[0])] = [{'n': p.split('~')[0].strip(), 'rev': float(p.split('~')[1]), 'c': int(p.split('~')[2])} for p in parts[1:]]
def spec(t):
    t = t.lower()
    for k, v in (('obgyn', 'Obgyn'), ('pedia', 'Pedia'), ('dialysis', 'Dialysis'), (' im ', 'IM'), ('gp', 'GP')):
        if k in t + ' ': return v
    return ''
org = {}
for ln in open('raw/hr24_doc_nurse.txt', encoding='utf8'):
    q = ln.strip().split('|')
    if len(q) >= 5: org[q[2]] = q[0]
nurE = []
for i, e in enumerate(ent):
    if e['kind'] != 'doctor':
        nurE.append({'i': i, 'st': e['st'], 'name': e['name'], 'br': e['br'], 'rate': rate.get(e['st'], 0), 'hrs': e['hrs'], 'each': e['each'], 'dd': e['dd'], 'reason': e['reason'], 'win': e['win'], 'org': org.get(e['st'], ''), 'charged': 0.0})
def ovl(w1, w2):
    return sum(max(0, min(a[1], b[1]) - max(a[0], b[0])) for a in w1 for b in w2)
# how many OT doctors share a clinic window on a day (to split a nurse between them)
share = {}
for i, e in enumerate(ent):
    if e['kind'] == 'doctor' and org.get(e['st']):
        for d in e['dd']:
            for n in nurE:
                if n['org'] == org[e['st']] and d in n['dd'] and ovl(OV.get(i, e['win']), n['win']) > 0:
                    share.setdefault((n['i'], d), set()).add(e['st'])
docs = {}
for i, e in enumerate(ent):
    if e['kind'] != 'doctor': continue
    D = docs.setdefault((e['br'], e['st']), {'br': e['br'], 'st': e['st'], 'name': e['name'], 'rate': rate.get(e['st'], 0), 'entries': []})
    w = OV.get(i, e['win'])
    days = []
    for d in e['dd']:
        r = rev.get((i, d), {'C': 0, 'R': 0, 'Ce': 0, 'Re': 0})
        nc = 0.0; nn = []
        for n in nurE:
            if n['org'] and n['org'] == org.get(e['st']) and d in n['dd']:
                o = ovl(w, n['win'])
                if o > 0:
                    hh = min(o, n['each']) / max(1, len(share.get((n['i'], d), {e['st']})))
                    nc += hh * n['rate']; n['charged'] += hh; nn.append('%s %s %.1fh' % (n['st'], n['name'], hh))
        days.append({'nur': round(nc, 2), 'nn': '; '.join(nn), 'd': d, 'hrs': e['each'], 'cash': round(r['C'], 2), 'cashN': r['Ce'], 'cred': round(r['R'], 2), 'credN': r['Re']})
    flag = NOCLIN.get(i) or ('nowin' if not w else '')
    D['entries'].append({'i': i, 'spec': spec(e['reason']), 'reason': e['reason'], 'win': w, 'hrs': e['hrs'], 'each': e['each'], 'flag': flag,
                         'wlen': round(sum(b - a for a, b in w), 2), 'days': [] if flag else days, 'costOnlyHrs': e['hrs'] if flag else 0, 'svc': svc.get(i, [])})
nur = nurE
for n in nur:
    n['chargedCost'] = round(n['charged'] * n['rate'], 2)
out = {'month': m, 'discount': 35, 'doctors': list(docs.values()), 'nurses': nur,
       'note_en': 'Revenue = net of VAT, pharmacy excluded; cash = invoice types C+D, credit = R. Window = the time stated in the overtime statement (overnight windows run past midnight).',
       'note_ar': 'الإيراد = الصافي بدون الضريبة وبدون الصيدلية؛ النقدي = فواتير C+D والآجل = R. النافذة = الوقت المكتوب في كشف الإضافي (النوافذ الليلية تمتد بعد منتصف الليل).'}
json.dump(out, open('data/overtime_feas.%s.json' % m, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
tot = lambda k: sum(d[k] for D in docs.values() for E in D['entries'] for d in E['days'])
print(len(docs), 'doctors; cash', round(tot('cash')), 'credit', round(tot('cred')), 'nurse rows', len(nur))
for D in docs.values():
    h = sum(E['hrs'] for E in D['entries']); c = sum(d['cash'] for E in D['entries'] for d in E['days']); r = sum(d['cred'] for E in D['entries'] for d in E['days'])
    print(D['br'], D['st'], D['name'][:16], 'hrs', h, 'cost', round(h * D['rate']), 'cash', round(c), 'cred', round(r))
