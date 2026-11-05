# -*- coding: utf-8 -*-
"""Build DATA.norm: the effect of the vouchers listed in Financial\\Normalization.xlsx (job `norm`, norm/vouchers.json) on every
payload of the Desk, so the Normalization switch can subtract them at load time (statements, IFRS 18, drivers, monthly buckets, Branches & Departments).
Usage: python3 build_norm.py <run dir>  ->  <run dir>/data_norm.json (refresh.py patches DATA.norm)
Sign convention everywhere: amt = DR - CR (expense positive, revenue negative); a payload series holding DR-CR gets `series -= amt`."""
import re, json, os, sys, collections
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work'); RID = sys.argv[1]
S = open(os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html'), encoding='utf8').read()
def blob(k): return json.loads(re.search(r"^DATA\." + k + r"\s*=\s*(.*);\s*$", S, re.M).group(1))
ifrs, ext, bd = blob('ifrs'), blob('ext'), blob('bd')
V = json.load(open(os.path.join(ROOT, 'norm', 'vouchers.json'), encoding='utf8'))
BR = {'01': 'Riyadh', '02': 'BUR1', '03': 'BUR2', '04': 'Rafha'}
rows = []
for br in BR:
    p = os.path.join(RID, 'staged', f'norm_{br}.json')
    if not os.path.exists(p): sys.exit(f'norm_{br} not staged')
    for r in json.load(open(p))[1:]:
        rows.append(dict(br=BR[br], v=r[0], d=r[1], ym=r[2], cc=r[3], f=r[4], a=r[5], amt=float(r[6]), bc=(r[8] if len(r) > 8 else r[3])))
# month key in the payloads: 'YYYY-MM'
mk = lambda ym: '20' + ym[:2] + '-' + ym[2:]
# account -> monthly bucket (same rule as build_monthly_buckets.py)
EXACT = {'4200027': 'B11', '3280001': 'B13', '3370000': 'B09', '3200000': 'B05', '3280003': 'B30', '3280004': 'B30', '3280005': 'B30', '3290001': 'B04', '3290002': 'B04'}
PREF = [('312', 'B23'), ('314', 'B18'), ('318', 'B37'), ('319', 'B33'), ('332', 'B19'), ('333', 'B16'), ('41', 'B08'), ('42', 'B10'), ('43', 'B27'), ('3', 'B26')]
def bucket(a):
    if a in EXACT: return EXACT[a]
    for p, b in PREF:
        if a.startswith(p): return b
    return 'B99'
nat_of = {}
for n in ifrs['nat']:
    for a in n[3]: nat_of[a] = n[0]
add = lambda d, *ks_v: None
def acc(d, keys, mo, amt):
    for k in keys[:-1]: d = d.setdefault(k, {})
    d[keys[-1]] = d.get(keys[-1], {}) ; d[keys[-1]][mo] = round(d[keys[-1]].get(mo, 0) + amt, 2)
N = dict(m={}, ifrs_fser={}, ifrs_ser={}, drv={}, bd_ln={}, bd_nat={}, ext={})
BL = {'B08': 'cash', 'B10': 'cred', 'B27': 'oth'}
EXT_LINE = {'COR': 'cost_of_revenue', 'GA': 'ga_expenses', 'INS': 'insurance_expenses', 'HO': 'headoffice_expenses', 'X': 'ga_expenses'}
for r in rows:
    mo = mk(r['ym']); a, cc, f, amt = r['a'], r['cc'], r['f'], r['amt']; y = mo[:4]
    b = bucket(a)
    N['m'].setdefault(f'{b}|{cc}', {}); N['m'][f'{b}|{cc}'][mo] = round(N['m'][f'{b}|{cc}'].get(mo, 0) + amt, 2)
    if a.startswith('3'):
        for tgt, key in ((N['ifrs_fser'], f'{a}|{cc}|{f}'), (N['ifrs_ser'], f'{a}|{cc}'), (N['drv'], f'{a}|{cc}|{f}')):
            tgt.setdefault(key, {}); tgt[key][mo] = round(tgt[key].get(mo, 0) + amt, 2)
        if a == '3280005': lk = 'zak'
        else: lk = f.lower() if f != 'X' else 'ga'
        nc = nat_of.get(a) or ('fin' if a.startswith('329') or a.startswith('339') else 'admin')
        bcc = r['bc']; N['bd_nat'].setdefault(bcc, {}).setdefault(nc, {}); N['bd_nat'][bcc][nc][mo] = round(N['bd_nat'][bcc][nc].get(mo, 0) + amt, 2)
        if a == '3280001': N['bd_ln'].setdefault(bcc, {}).setdefault('dep', {}); N['bd_ln'][bcc]['dep'][mo] = round(N['bd_ln'][bcc]['dep'].get(mo, 0) + amt, 2)
    else:
        lk = BL.get(b, 'oth'); amt_ln = -amt   # revenue lines hold CR-DR in bd.ln
        bcc = r['bc']; N['bd_ln'].setdefault(bcc, {}).setdefault(lk, {}); N['bd_ln'][bcc][lk][mo] = round(N['bd_ln'][bcc][lk].get(mo, 0) - amt, 2)
        continue
    N['bd_ln'].setdefault(bcc, {}).setdefault(lk, {}); N['bd_ln'][bcc][lk][mo] = round(N['bd_ln'][bcc][lk].get(mo, 0) + amt, 2)
# statements (annual): lines hold revenue positive / costs negative -> line += amt (revenue: amt is DR-CR, negative)
E_ = collections.defaultdict(lambda: collections.defaultdict(float))
for r in rows:
    a, f, amt, y = r['a'], r['f'], r['amt'], r['ym'][:2]; y = '20' + y
    if a.startswith('4'):
        ln = 'other_revenue' if (a.startswith('43') or a == '4200027') else ('cash_revenue' if a.startswith('41') else 'credit_revenue')
        E_[y][ln] += amt
        if ln != 'other_revenue': E_[y]['total_revenue'] += amt; E_[y]['gross_margin'] += amt
        else: E_[y]['nibz'] += amt; E_[y]['net_income'] += amt; E_[y]['ebitda'] += amt; continue
    else:
        if a == '3280005': E_[y]['zakat_expenses'] += amt; E_[y]['net_income'] += amt; E_[y]['ebitda'] += amt; continue
        ln = EXT_LINE[f] if f in EXT_LINE else 'ga_expenses'
        if a == '3280001': E_[y]['depreciation'] += amt
        E_[y][ln] += amt
        if ln == 'cost_of_revenue': E_[y]['gross_margin'] += amt
        else: E_[y]['total_ga_rollup'] += amt
        E_[y]['profit_from_operation'] += amt
    E_[y]['nibz'] += amt; E_[y]['net_income'] += amt
    if a != '3280001': E_[y]['ebitda'] += amt
N['ext'] = {y: {k: round(v, 2) for k, v in d.items()} for y, d in E_.items()}
# voucher register (what the toggle removes) with a date check against the workbook
reg = []
for x in V:
    mine = [r for r in rows if r['v'] == x['v']]
    tot = round(sum(r['amt'] for r in mine), 2); dbd = min((r['d'] for r in mine), default=None); fl = []
    if not mine: fl.append('not found in the ledger (cancelled or wrong number)')
    elif dbd != x.get('date'): fl.append(f"workbook date {x.get('date')} differs from ledger date {dbd}; the ledger date is used")
    reg.append(dict(v=x['v'], tag=x['tag'], note=x['note'], wb=x.get('date'), db=dbd, br=sorted({r['br'] for r in mine}), amt=tot, fl=fl))
out = dict(asOf=bd['asOf'], vouchers=reg, total=round(sum(g['amt'] for g in reg), 2), m=N['m'], ifrs={'fser': N['ifrs_fser'], 'ser': N['ifrs_ser']}, drv=N['drv'],
           bd={'ln': N['bd_ln'], 'nat': N['bd_nat']}, ext=N['ext'], years=ext['years'])
json.dump(out, open(os.path.join(RID, 'data_norm.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(f"norm: {len(reg)} vouchers · P&L effect SAR {out['total']:,.2f} · by year " + ' '.join(f"{y}:{sum(v for k,v in d.items() if k=='net_income'):+,.0f}" for y, d in sorted(N['ext'].items())) +
      (' · FLAGS ' + '; '.join(f"{g['v']}: {', '.join(g['fl'])}" for g in reg if g['fl']) if any(g['fl'] for g in reg) else ''))
