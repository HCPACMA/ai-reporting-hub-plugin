# -*- coding: utf-8 -*-
"""Build DATA.bd (Branches & Departments) from the payloads already in the Desk (DATA.m, DATA.ifrs, DATA.ext)
plus the per-database balance pull staged by refresh.py (job bd_bal).
Usage: python3 build_bd.py <run dir>      -> <run dir>/data_bd.json   (refresh.py patches it into the HTML)
Gates (printed as VERDICT ...): every closed year must tie to the Income Statement within SAR 15."""
import re, json, collections, sys, os, glob, datetime as dt
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
HTML = os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html')
RID = sys.argv[1]
S = open(HTML, encoding='utf8').read()
def blob(k): return json.loads(re.search(r"^DATA\." + k + r"\s*=\s*(.*);\s*$", S, re.M).group(1))
m, f, ext = blob('m'), blob('ifrs'), blob('ext')
try: old = blob('bd')
except Exception: old = None
P = json.load(open(os.path.join(RID, 'plan.json')))
asof = dt.date.fromisoformat(P['asof']); y0 = asof.year
M = m['months']; N = len(M); assert M == f['months'], 'DATA.m and DATA.ifrs months differ'
CCS = ['01', '02', '03', '04', '00']; z = lambda: [0.0] * N
nat_of = {}
for n in f['nat']:
    for a in n[3]: nat_of[a] = n[0]
ZAK = ['3280005']; unm = set()
D = {cc: {k: z() for k in ['cash', 'cred', 'oth', 'cor', 'ins', 'ga', 'ho', 'zak', 'dep']} for cc in CCS}
NAT = {cc: collections.defaultdict(z) for cc in CCS}
for key, ser in f['fser'].items():
    ac, cc, fn = key.split('|')
    if cc not in D: cc = '00'
    tgt = 'zak' if ac in ZAK else fn.lower()
    for i, v in enumerate(ser):
        D[cc][tgt][i] += v
        if ac == '3280001': D[cc]['dep'][i] += v
        if ac not in ZAK:
            nc = nat_of.get(ac) or ('fin' if ac.startswith('329') or ac.startswith('339') else 'admin')
            if ac not in nat_of: unm.add(ac)
            NAT[cc][nc][i] += v
for cc in CCS:
    for b, t in (('B08', 'cash'), ('B10', 'cred'), ('B27', 'oth')):
        s = m['series'].get(b + '|' + cc)
        if s:
            for i, v in enumerate(s): D[cc][t][i] += -v
for cc in m['ccs']:
    s = m['series'].get('B11|' + cc)
    if s:
        for i, v in enumerate(s): D[cc]['oth'][i] += -v          # net of 4200027 follows its cost-centre prefix (branch lines are re-attributed below)
# ---- 3-character branch cost centres 001-004 (job bd_cc3): the 2-character prefix '00' hides them inside head office.
#      General & administrative expenses and other revenue posted on 001-004 belong to that branch; only cost centre 000 is head office.
moved = collections.defaultdict(float)
for br in ('01', '02', '03', '04'):
    p_ = os.path.join(RID, 'staged', f'bd_cc3_{br}.json')
    if not os.path.exists(p_): continue
    for a_, c3, ym, v in json.load(open(p_)):
        v = float(v); k = f'20{ym[:2]}-{ym[2:]}'; cc = '0' + c3[2]
        if k not in M or cc not in D: continue
        i = M.index(k)
        if a_[0] == '3':
            tgt = 'zak' if a_ in ZAK else 'ga'
            D['00'][tgt][i] -= v; D[cc][tgt][i] += v
            if a_ == '3280001': D['00']['dep'][i] -= v; D[cc]['dep'][i] += v
            if a_ not in ZAK:
                nc = nat_of.get(a_) or ('fin' if a_.startswith('329') or a_.startswith('339') else 'admin')
                NAT['00'][nc][i] -= v; NAT[cc][nc][i] += v
            moved['exp'] += v
        else:
            tgt = 'cash' if a_.startswith('41') else ('cred' if (a_.startswith('42') and a_ != '4200027') else 'oth')
            D['00'][tgt][i] -= -v; D[cc][tgt][i] += -v
            moved['rev'] += -v
print(f'branch cost centres 001-004 re-attributed from head office: expenses {moved["exp"]:,.0f}, other revenue {moved["rev"]:,.0f}')
rnd = lambda a: [round(x) for x in a]
# ---- gate: closed years tie to the Income Statement
bad = []; rows = []
def yr(arr, y, a_, b_): return sum(arr[M.index(f'{y}-{a_:02d}'):M.index(f'{y}-{b_:02d}') + 1])
for y in ext['years']:
    if f'{y}-01' not in M: continue
    last = 12 if y < y0 else None
    if last is None: continue
    ni = sum(yr(D[c]['cash'], y, 1, 12) + yr(D[c]['cred'], y, 1, 12) + yr(D[c]['oth'], y, 1, 12) - sum(yr(D[c][k], y, 1, 12) for k in ('cor', 'ins', 'ga', 'ho', 'zak')) for c in CCS)
    e = ext['is_']['net_income'][ext['years'].index(y)]
    rows.append(f'{y}:{ni - e:+.0f}')
    if abs(ni - e) > 15: bad.append(f'FY{y} net income differs from the Income Statement by {ni - e:,.0f}')
# ---- last closed month (same rule as the time-intelligence block)
rev = [sum(D[c]['cash'][i] + D[c]['cred'][i] for c in CCS) for i in range(N)]
med = sorted(rev)[N // 2]; last = N - 1
while last > 0 and rev[last] <= med * 0.5: last -= 1
# ---- ledger-held balances per database (job bd_bal): year-ends of the three previous years + the last closed day
dates = [f'{y}-12-31' for y in range(y0 - 4, y0)] + [str(asof - dt.timedelta(days=1))]
dbo = {}
stg = {br: os.path.join(RID, 'staged', f'bd_bal_{br}.json') for br in ('01', '02', '03', '04')}
if all(os.path.exists(p) for p in stg.values()):
    for br, p in stg.items():
        v = {r[0]: [float(x) if x not in ('', 'None') else 0.0 for x in r[1:7]] for r in json.load(open(p))}
        g = lambda *ks: [sum(v.get(k, [0] * 6)[i] for k in ks) for i in range(6)]
        dbo[br] = {'cash': rnd(g('121', '122')), 'ar': rnd(g('124')), 'oth': rnd(g('125', '126')), 'inv': rnd(g('123')), 'fa': rnd(g('111', '112', '113'))}
    print('db balances: staged', dates)
elif old:
    dbo = old['db']; dates = old['dbDates']; print('db balances: carried forward from the previous build', dates)
# ---- open (STATUS='O') vouchers on P&L accounts, already included in the figures above (posted + open, like the Statements)
opn = {}; brmap = {'01': 'Riyadh', '02': 'BUR1', '03': 'BUR2', '04': 'Rafha'}
for br in ('01', '02', '03', '04'):
    p_ = os.path.join(RID, 'staged', f'bd_open_{br}.json')
    if not os.path.exists(p_): continue
    for r in json.load(open(p_))[1:]:
        ym, cc, n_, rv, ex = r[0], r[1], float(r[2]), float(r[3]), float(r[4])
        k = f'20{ym[:2]}-{ym[2:]}'
        if k not in M or cc not in CCS: continue
        o = opn.setdefault(cc, {'n': z(), 'rev': z(), 'exp': z()}); i = M.index(k)
        o['n'][i] += n_; o['rev'][i] += rv; o['exp'][i] += ex
if opn: print('open vouchers: staged', sum(sum(o['n']) for o in opn.values()), 'voucher-months')
natLab = {n[0]: [n[2], n[1]] for n in f['nat']}; natLab['fin'] = ['Finance & other charges', 'أعباء تمويلية وأخرى']
bd = {'months': M, 'asOf': m['asOf'], 'last': last, 'dbDates': dates, 'br': {c: m['ccName'][c] for c in CCS},
      'ln': {c: {k: rnd(v) for k, v in D[c].items()} for c in CCS}, 'nat': {c: {k: rnd(v) for k, v in NAT[c].items()} for c in CCS}, 'natLab': natLab, 'db': dbo, 'open': {c: {k: rnd(v) for k, v in o.items()} for c, o in opn.items()}}
json.dump(bd, open(os.path.join(RID, 'data_bd.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
ytd = ''
if f'{y0}-01' in M:
    a = M.index(f'{y0}-01'); ni = sum(sum(D[c][k][a:last + 1]) * (1 if k in ('cash', 'cred', 'oth') else -1) for c in CCS for k in ('cash', 'cred', 'oth', 'cor', 'ins', 'ga', 'ho', 'zak'))
    ni_all = sum(sum(D[c][k][a:]) * (1 if k in ('cash', 'cred', 'oth') else -1) for c in CCS for k in ('cash', 'cred', 'oth', 'cor', 'ins', 'ga', 'ho', 'zak'))
    st_ = ext["is_"]["net_income"][ext["years"].index(y0)] if y0 in ext['years'] else None
    ytd = f' · {y0} YTD to {M[last]} net {ni:,.0f}; all months {ni_all:,.0f} vs statements {st_:,.0f} (diff {ni_all - st_:+,.0f})' if st_ is not None else ''
    if st_ is not None and abs(ni_all - st_) > 15: print(f'NOTE {y0} YTD (posted + open) differs from the Statements by {ni_all - st_:,.0f} — statements may be stale')
for b_ in bad: print('GATE ' + b_)
print('VERDICT ' + ('REPRODUCED' if not bad else 'FAILED') + f' · tie by year {" ".join(rows)}{ytd} · last closed {M[last]} · unmapped natures {sorted(unm) or "none"}')
