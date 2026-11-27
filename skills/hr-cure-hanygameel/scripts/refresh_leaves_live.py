#!/usr/bin/env python3
"""Refresh the Nov leave rows of data/review_screens.json from a live Cure query (st|type|from|to|return|flag|days).
Keeps pg/ls/lc of existing rows; adds missing rows; sets flag/ret/days from Cure; stamps vf. Also sets lday = folder day of the letter
row whose text names the leave start date (so the page links the letter of THAT period, not just the employee's newest file)."""
import json, sys, re
rs, raw, mo, stamp = sys.argv[1:5]
R = json.load(open(rs, encoding='utf-8'))
names = {}
for k in ('letters', 'leaves', 'items'):
    for r in R[k]:
        if r.get('name'): names.setdefault(r['st'], r['name'])
live = [l.split('|') for l in open(raw, encoding='utf-8').read().split('\n') if l.strip()]
vm = '%s/%s' % (mo[5:], mo[:4]); ch = ad = 0
for st, ty, f, t, ret, fl, dy in live:
    row = next((r for r in R['leaves'] if r['st'] == st and r['frm'] == f and r['to'] == t and r['mo'] == mo), None)
    if row:
        if row['flag'] != fl or row['ret'] != ret: ch += 1
        row.update(flag=fl, ret=ret, days=int(float(dy)))
    else:
        ad += 1; R['leaves'].append({'st': st, 'name': names.get(st, ''), 'type': ty, 'frm': f, 'to': t, 'ret': ret, 'flag': fl, 'days': int(float(dy)), 'vm': vm, 'ls': 0, 'lc': 0, 'pg': '', 'mo': mo})
    (row or R['leaves'][-1])['vf'] = stamp
# stale rows of this month that Cure no longer has (period changed): hand their letter ref to the live row, then drop them
stale = [r for r in R['leaves'] if r['mo'] == mo and 'vf' not in r and r['frm'][3:] == mo[5:]]
for r in stale:
    tgt = next((x for x in R['leaves'] if x['st'] == r['st'] and x['mo'] == mo and x.get('vf') and not x['pg']), None)
    if tgt: tgt.update(pg=r['pg'], ls=r['ls'], lc=r['lc'])
    R['leaves'].remove(r)
print('stale dropped', len(stale))
for r in R['leaves']:
    if r['mo'] != mo: continue
    r.pop('lday', None); r.pop('lres', None); r.pop('sdoc', None)
    if r['type'] == '17':
        # annual leave has no leave letter (Hany 24 Nov): it is registered from the dues settlement / return-and-handover letter
        S = [l for l in R['letters'] if l['st'] == r['st'] and l['mo'] == mo and l.get('day') and re.search('مستحقات|عودة|استلام|سنوية|اعتيادية', l['type']) and l['s'] != 'out']
        S.sort(key=lambda l: l['day'].split('-')[::-1])
        if S:
            r['lday'] = S[-1]['day'] + '-' + mo[:4]; r['sdoc'] = S[-1]['type']
            r['lres'] = min((l['s'] for l in S), key=lambda x: {'err': 0, 'note': 1, 'none': 2, 'def': 3, 'fut': 3, 'ok': 4}.get(x, 5))
        else: r['lres'] = 'ok'
        continue
    for l in R['letters']:
        if l['st'] == r['st'] and l.get('day') and (r['frm'] in l['letter'] or (r['frm'] == r['to'] and False)) and l['mo'] == mo:
            r['lday'] = l['day'] + '-' + mo[:4]
json.dump(R, open(rs, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('changed', ch, 'added', ad, 'with lday', sum(1 for r in R['leaves'] if r.get('lday')))
