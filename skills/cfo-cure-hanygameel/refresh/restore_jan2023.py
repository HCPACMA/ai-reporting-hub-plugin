# After a bootstrap build with ledger window 2023-02-01 the reset removes 2023-01 from gl_all/cc_all/zak lines; put it back from the boot staged data
import json, glob, os, collections
R = '/home/claude/work/'; S = R + 'kit/refresh/runs/20261010boot2/staged/'
J = lambda p: json.load(open(R + p)); JW = lambda p, o: json.dump(o, open(R + p, 'w'), ensure_ascii=False)
g = [r for r in J('drv/gl_all.json') if r[4] != '202301']
for b in ('01', '02', '03', '04'):
    for a, cc, f, ym, v in json.load(open(S + f'gl_mon_{b}.json')):
        if ym == '2301': g.append([b, a, cc, f, '20' + ym, float(v)])
JW('drv/gl_all.json', g)
agg = collections.defaultdict(float)
for br, a, cc, f, ym, v in g: agg[(a, cc, ym)] += v
open(R + 'drv/m_po.txt', 'w').write(''.join(f'{a}|{cc}|{ym}|{round(v, 2)}\n' for (a, cc, ym), v in sorted(agg.items()) if abs(v) >= 0.005))
c = J('drv/cc_all.json')
for b in ('01', '02', '03', '04'):
    c[b] = [r for r in c.get(b, []) if r[0] != '2301'] + [r for r in json.load(open(S + f'cc_mon_{b}.json')) if r[0] == '2301']
JW('drv/cc_all.json', c)
z = [r for r in J('zak/lines.json') if not ('2023-01-01' <= r[1] < '2023-02-01')]
for b in ('01', '02', '03', '04'):
    for d, v, a, s_, amt, ds in json.load(open(S + f'zak_lines_{b}.json')):
        if '2023-01-01' <= d < '2023-02-01': z.append([b, d, v, a, s_, float(amt), ds])
JW('zak/lines.json', sorted(z, key=lambda r: (r[1], r[2])))
print('ok', len(g))
