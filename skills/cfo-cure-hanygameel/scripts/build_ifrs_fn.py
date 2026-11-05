# -*- coding: utf-8 -*-
"""DATA.ifrs rebuilt from the same ledger pull as the rest of the desk (drv/gl_all.json:
posted + open vouchers, account x cost-centre prefix x function x month), so the IFRS 18 tab can
present operating expenses either by nature or by function.

  ser  : 'acct|cc2'   -> monthly DR-CR   (all P&L accounts the tab uses)
  fser : 'acct|cc2|f' -> monthly DR-CR   (expense accounts 3xxxxxx, f = COR / GA / INS / HO / X)
Keeps the account names (acc) and the nature map (nat) already in the page.
Gate: every expense account with a balance must sit in a nature group, or the build stops."""
import json, re, collections, os, sys
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
P = lambda *a: os.path.join(ROOT, *a)
H = open(P('AlFaihaa_Modeling_Desk.html'), encoding='utf-8').read()
I = json.loads(re.search(r'\nDATA\.ifrs = (.*);\n', H).group(1))
DRV = json.loads(re.search(r'\nDATA\.drv = (.*);\n', H).group(1))
NM = json.load(open(P('gl/acc_names.json')))

last = DRV['asOf'][:7]
M = []
y, m = 2023, 1
while '%d-%02d' % (y, m) <= last:
    M.append('%d-%02d' % (y, m)); m += 1
    if m == 13: y, m = y + 1, 1
MI = {x.replace('-', ''): i for i, x in enumerate(M)}
N = len(M)

use = lambda a: a[0] == '3' or a.startswith('43')
ser = collections.defaultdict(lambda: [0.0] * N)
fser = collections.defaultdict(lambda: [0.0] * N)
for br, a, cc, f, ym, v in json.load(open(P('drv/gl_all.json'))):
    if not use(a) or ym not in MI: continue
    i = MI[ym]
    ser[a + '|' + cc][i] += v
    if a[0] == '3': fser[a + '|' + cc + '|' + f][i] += v

acc = dict(I['acc'])
for k in ser:
    a = k.split('|')[0]
    if a not in acc: acc[a] = [NM.get(a, a), NM.get(a, a)]
# gate: every expense account used in operating must be in a nature group (or one of the category accounts)
grouped = set(x for g in I['nat'] for x in g[3]) | {'3280005', '3290001', '3390000', '3290003'}
miss = sorted(set(k.split('|')[0] for k, v in ser.items() if k[0] == '3' and k.split('|')[0] not in grouped and any(abs(x) > 0.5 for x in v)))
if miss:
    print('UNGROUPED EXPENSE ACCOUNTS (add to the nature map):', miss); sys.exit(1)

r2 = lambda v: [round(x, 2) for x in v]
out = {'months': M, 'acc': acc, 'nat': I['nat'],
       'ser': {k: r2(v) for k, v in ser.items() if any(abs(x) > 0.004 for x in v)},
       'fser': {k: r2(v) for k, v in fser.items() if any(abs(x) > 0.004 for x in v)},
       'fn': {'COR': ['تكلفة الإيرادات', 'Cost of revenue'],
              'GA': ['مصروفات عمومية وإدارية', 'General and administrative expenses']},
       'fnMap': {'COR': 'COR', 'GA': 'GA', 'INS': 'GA', 'HO': 'GA', 'X': 'GA'}}
json.dump(out, open(P('ifrs/data_ifrs.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
# tie: function split must equal the account totals
d = 0.0
for k, v in out['ser'].items():
    if k[0] != '3': continue
    fs = [0.0] * N
    for f in ('COR', 'GA', 'INS', 'HO', 'X'):
        s = out['fser'].get(k + '|' + f)
        if s: fs = [a + b for a, b in zip(fs, s)]
    d = max(d, max(abs(a - b) for a, b in zip(fs, v)))
print('months', M[0], M[-1], 'ser', len(out['ser']), 'fser', len(out['fser']), 'max split gap', round(d, 2),
      'bytes', os.path.getsize(P('ifrs/data_ifrs.json')))
