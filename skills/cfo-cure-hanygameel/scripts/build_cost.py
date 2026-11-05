"""Build DATA.cost for the Modeling Desk Costing section."""
import json, gzip, base64, collections, costcalc

B36 = '0123456789abcdefghijklmnopqrstuvwxyz'
def b36(n):
    if n == 0: return '0'
    s = ''
    while n: s = B36[n % 36] + s; n //= 36
    return s
def num(x):
    f = float(x)
    return str(int(round(f))) if abs(f - round(f)) < 0.05 else ('%.1f' % f)

rows, U, IC = costcalc.build()
svcmeta = {}
for l in open('services.txt'):
    l = l.strip()
    if not l: continue
    p = l.split('|')
    if len(p) < 3: continue
    svcmeta[p[0]] = [p[2], p[1]]          # name, speciality no
LK  = json.load(open('lookups.json'))
DOC = json.load(open('doctors.json'))
BR  = {'01': 'Riyadh', '02': 'Bur-1', '03': 'Bur-2', '04': 'Rafha'}

YM = ['%d%02d' % (y, m) for y in (2025, 2026) for m in range(1, 13)]
YM = [x for x in YM if '202509' <= x <= '202609']
ymi = {v: i for i, v in enumerate(YM)}

# ---- dictionaries built from what the grid actually uses
svcs, grps, docs, spcs = set(), set(), set(), set()
raw = {}
for b in BR:
    lines = [l.strip() for l in open('Q_%s.txt' % b) if l.strip()]
    raw[b] = [l.split('|') for l in lines]
    for p in raw[b]:
        svcs.add(p[1]); grps.add(p[2]); docs.add(b + ':' + p[4]); spcs.add(p[5])
SV = sorted(svcs); svi = {v: i for i, v in enumerate(SV)}
GR = sorted(grps, key=lambda x: int(x)); gri = {v: i for i, v in enumerate(GR)}
DC = sorted(docs); dci = {v: i for i, v in enumerate(DC)}
SP = sorted(spcs, key=lambda x: int(x)); spi = {v: i for i, v in enumerate(SP)}
CT = ['C', 'D', 'R']; cti = {v: i for i, v in enumerate(CT)}

# columnar layout: 12 columns, each a comma-joined list; columns joined by '|'
packed = {}
for b in BR:
    col = [[] for _ in range(12)]
    for p in raw[b]:
        ym, pc, grp, ctp, doc, sp, qty, qg, gr, ds, ps, ln, iv = p
        vals = [b36(ymi[ym]), b36(svi[pc]), b36(gri[grp]), str(cti[ctp]),
                b36(dci[b + ':' + doc]), b36(spi[sp]),
                num(qty), num(qg), num(gr), num(ds), num(ps), iv]
        for i, v in enumerate(vals): col[i].append(v)
    packed[b] = '|'.join(','.join(c) for c in col)

grid_raw = json.dumps(packed, separators=(',', ':'))
grid_z = base64.b64encode(gzip.compress(grid_raw.encode(), 9)).decode()

# ---- service cost table
uc = {}
for s, v in U.items():
    uc[s] = [round(v['unit'], 4), v['st'], v['dept'], v['n'], v['bad'], v['ld'], v.get('chk', 0)]

# ---- map detail lines (service -> item)
ml = []
for r in rows:
    ml.append([r['svc'], r['item'], r['iname'], r['share'], r['tests'], r['cost0'],
               r['lc'], r['ld'], round(r['unit'], 4) if r['unit'] is not None else None,
               r['status'], r['q12'], r['nd'], r['note']])

out = {
    'run': '2026-09-23',
    'ym': YM,
    'brn': BR,
    'sv': SV,
    'svn': {s: svcmeta.get(s, [U[s]['name'] if s in U else s, '0']) for s in set(SV) | set(U)},
    'gr': GR, 'grn': LK['GRP'],
    'dc': DC, 'dcn': DOC,
    'sp': SP, 'spn': LK['SPEC'],
    'ct': CT,
    'uc': uc,
    'map': ml,
    'gz': grid_z,
}
s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
open('data_cost.json', 'w').write(s)
print('grid rows', sum(len(v) for v in raw.values()))
print('grid raw %.1f MB  gz %.0f KB' % (len(grid_raw) / 1e6, len(grid_z) / 1024))
print('payload %.0f KB' % (len(s) / 1024))
