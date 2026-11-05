#!/usr/bin/env python3
"""Fill the placeholders of sql/*.sql for one company and one as-of date.

    python3 render_sql.py --config config/company.<co>.json --asof 2026-10-12 --out sql_out/

Placeholders: {P} schema prefix, {ASOF}, {SAUDI}, {FROM_YM}, {FROM_YM_DASH}, {FROM_DATE}, {LASTY}, {LASTM},
{D30} {D90} {D180}, {ID_RES} {ID_PASS}, {ACC_EOSB} {ACC_LEAVE} {ACC_PAY}, {HT_ITEMS}.
Send each rendered file's text to cure_run_query (branch = cure.hr_branch_param) and save the reply to raw/<job>.txt.
The Cure MCP rejects text containing UPDATE, CREATE, TRUNCATE or WITH, so the files avoid them; a placeholder value must not add them.
"""
import argparse, json, os, datetime as dt

def add_months(y, m, k):
    t = y*12 + (m-1) + k
    return t // 12, t % 12 + 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--asof', required=True)
    ap.add_argument('--months', type=int, default=24, help='closed months of history')
    ap.add_argument('--sql', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sql'))
    ap.add_argument('--out', default='sql_out')
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf8')); asof = dt.date.fromisoformat(a.asof)
    fy, fm = add_months(asof.year, asof.month, -a.months)
    ly, lm = add_months(asof.year, asof.month, -1)
    vals = {
        'P': cfg['cure']['schema_prefix'], 'ASOF': a.asof, 'SAUDI': str(cfg['saudi_nationality_code']),
        'FROM_YM': f"{fy}{fm:02d}", 'FROM_YM_DASH': f"{fy}-{fm:02d}", 'FROM_DATE': f"{fy}-{fm:02d}-01",
        'LASTY': str(ly), 'LASTM': str(lm),
        'D30': (asof + dt.timedelta(days=30)).isoformat(), 'D90': (asof + dt.timedelta(days=90)).isoformat(), 'D180': (asof + dt.timedelta(days=180)).isoformat(),
        'ACC_EOSB': cfg['accounts']['eosb'], 'ACC_LEAVE': cfg['accounts']['leave'], 'ACC_PAY': cfg['accounts']['payables'],
        'ID_RES': ','.join("'" + x + "'" for x in cfg['id_types_residence']), 'ID_PASS': "'" + cfg['id_type_passport'] + "'",
        'HT_ITEMS': ','.join(str(i) for i in cfg['eosb_housing_transport_items']),
    }
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(os.listdir(a.sql)):
        if not f.endswith('.sql'): continue
        t = open(os.path.join(a.sql, f), encoding='utf8').read()
        for k, v in vals.items(): t = t.replace('{' + k + '}', v)
        assert '{' not in t.replace('{P}', ''), f"unfilled placeholder in {f}"
        # strip comment lines: only the statement is sent to the tool
        stmt = ' '.join(l for l in t.splitlines() if not l.lstrip().startswith('--')).strip()
        up = stmt.upper()
        for bad in ('UPDATE', 'CREATE', 'TRUNCATE'):
            assert bad not in up, f"{f} contains {bad}"
        assert ' WITH ' not in f" {up} ", f"{f} contains WITH"
        open(os.path.join(a.out, f), 'w', encoding='utf8').write(stmt + '\n')
        print(f, len(stmt), 'chars')

if __name__ == '__main__':
    main()
