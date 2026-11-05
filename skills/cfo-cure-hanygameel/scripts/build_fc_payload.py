"""Build DATA.fc for the Modeling Desk Forecasting section from the device outputs.
Inputs (same folder): monthly_invoice_revenue.csv, forecast_ledger.csv, model_registry.json
Output: data_fc.json
"""
import sys, os, json, csv, datetime as dt, collections
F = sys.argv[1] if len(sys.argv) > 1 else '.'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'data_fc.json'
reg = json.load(open(os.path.join(F, 'model_registry.json')))
rows = list(csv.DictReader(open(os.path.join(F, 'monthly_invoice_revenue.csv'))))
led = list(csv.DictReader(open(os.path.join(F, 'forecast_ledger.csv'))))

# ---- actuals per series (revenue, visits, refunds, pharmacy share)
act = collections.defaultdict(dict)
def add(key, ym, rev, eps, rf, ph):
    d = act[key].setdefault(ym, [0, 0, 0, 0]); d[0] += rev; d[1] += eps; d[2] += rf; d[3] += ph
for r in rows:
    ym = r['ym']; br = r['branch']; f = lambda k: float(r[k] or 0)
    for k, eps, rf, ph in (('cash', 'eps_cash', 'refund_cash', 'cash_ph'), ('credit', 'eps_credit', 'refund_credit', 'credit_ph')):
        for key in (f'{br}|{k}', f'ALL|{k}', 'ALL|total'):
            add(key, ym, f(k), f(eps), f(rf), f(ph))
act = {k: {ym: [round(x) for x in v] for ym, v in d.items()} for k, d in act.items()}

# ---- calendar (same table as the model)
RAM = {2019: "2019-05-06", 2020: "2020-04-24", 2021: "2021-04-13", 2022: "2022-04-02", 2023: "2023-03-23", 2024: "2024-03-11", 2025: "2025-03-01", 2026: "2026-02-18", 2027: "2027-02-08", 2028: "2028-01-28"}
FITR = {2019: "2019-06-04", 2020: "2020-05-24", 2021: "2021-05-13", 2022: "2022-05-02", 2023: "2023-04-21", 2024: "2024-04-10", 2025: "2025-03-30", 2026: "2026-03-20", 2027: "2027-03-10", 2028: "2028-02-27"}
ADHA = {2019: "2019-08-11", 2020: "2020-07-31", 2021: "2021-07-20", 2022: "2022-07-09", 2023: "2023-06-28", 2024: "2024-06-16", 2025: "2025-06-06", 2026: "2026-05-27", 2027: "2027-05-16", 2028: "2028-05-05"}
ram, eid = set(), set()
for y, s in RAM.items():
    d = dt.date.fromisoformat(s); e = dt.date.fromisoformat(FITR[y])
    while d < e: ram.add(d); d += dt.timedelta(1)
for dct, n in ((FITR, 4), (ADHA, 5)):
    for s in dct.values():
        d = dt.date.fromisoformat(s)
        for i in range(n): eid.add(d + dt.timedelta(i))
def cal(ym):
    y, m = int(ym[:4]), int(ym[4:]); d = dt.date(y, m, 1); days = []
    while d.month == m: days.append(d); d += dt.timedelta(1)
    return [sum(x in ram for x in days), sum(x in eid for x in days), sum(x.weekday() == 4 for x in days)]
calendar = {}
for y in range(2019, 2029):
    for m in range(1, 13): calendar[f'{y}{m:02d}'] = cal(f'{y}{m:02d}')

# ---- ledger compact: key -> list of [vintage, target, f, lo80, hi80, lo95, hi95, fc_eps, kind]
L = collections.defaultdict(list)
for r in led:
    v = r['vintage'].replace('-', ''); t = r['target'].replace('-', '')
    fv = lambda k: round(float(r[k])) if r[k] not in ('', 'nan', 'None') else None
    L[r['series']].append([v, t, fv('forecast'), fv('lo80'), fv('hi80'), fv('lo95'), fv('hi95'), fv('fc_eps'), r['kind'], float(r['bias'] or 0), r['model']])

last_full = reg['last_full'].replace('-', '')
# ---- justification for each (vintage, target) where the actual month is complete
def justify(key, v, t, f, fe):
    a = act.get(key, {}).get(t)
    if not a or t > last_full or f is None: return None
    A, Ae, Arf = a[0], a[1], a[2]
    var = A - f; pct = var / f if f else 0
    parts = []
    if fe and Ae:
        rf_ = f / fe; ra = A / Ae
        vol = (Ae - fe) * rf_; rate = (ra - rf_) * Ae
        parts.append(['Visits', vol, f'{Ae:,.0f} visits vs {fe:,.0f} expected ({(Ae/fe-1)*100:+.1f}%)'])
        parts.append(['Revenue per visit', rate, f'{ra:,.0f} vs {rf_:,.0f} expected ({(ra/rf_-1)*100:+.1f}%)'])
    # calendar vs same month last year
    ly = f'{int(t[:4])-1}{t[4:]}'
    c, cl = calendar.get(t, [0, 0, 0]), calendar.get(ly, [0, 0, 0])
    notes = []
    if c[0] != cl[0]: notes.append(f'{c[0]} Ramadan days vs {cl[0]} in {ly[:4]}')
    if c[1] != cl[1]: notes.append(f'{c[1]} Eid holiday days vs {cl[1]} in {ly[:4]}')
    if c[2] != cl[2]: notes.append(f'{c[2]} Fridays vs {cl[2]}')
    # refunds vs trailing 12-month average
    prev = [act[key][p][2] for p in sorted(act[key]) if p < t][-12:]
    if prev:
        avg = sum(prev) / len(prev)
        if avg and abs(Arf) > 1.3 * abs(avg): notes.append(f'refunds {abs(Arf):,.0f} vs {abs(avg):,.0f} normal')
    return {'a': A, 'var': round(var), 'pct': round(pct, 4), 'parts': [[p[0], round(p[1]), p[2]] for p in parts], 'notes': notes}

J = {}
for key, lst in L.items():
    for v, t, f, *_rest in lst:
        fe = _rest[4]
        j = justify(key, v, t, f, fe)
        if j: J[f'{key}|{v}|{t}'] = j

out = {'run': reg['run'], 'last_full': last_full, 'reg': reg['series'], 'act': act, 'led': L, 'just': J,
       'cal': {k: v for k, v in calendar.items() if '2019' <= k[:4] <= '2028'}, 'brn': {'01': 'Riyadh', '02': 'Bur-1', '03': 'Bur-2', '04': 'Rafha', 'ALL': 'Group'}}
s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
open(OUT, 'w').write(s); print('bytes', len(s), 'series', len(L), 'just', len(J))
