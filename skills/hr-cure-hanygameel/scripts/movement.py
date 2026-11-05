#!/usr/bin/env python3
"""Hires and leavers by month, branch, job family and nationality, for the Movement analysis screen.

    python3 scripts/movement.py --config config/company.alfaihaa.json --extract data/extract.alfaihaa.2026-10-12.json \
        --events raw/hr29_movement_events.txt --active raw/hr30_active_dims.txt --asof 2026-10-26 --out data/movement.json

events: lines  ev|ym|branch|job|nat code|n   (ev H hire, L leaver)   active: lines  branch|job|nat code|n
Output: compact lists keyed by short codes plus the label tables. The draft (current) month is kept but flagged so the page can leave it out of rates."""
import argparse, json, re, datetime as dt

def fam(cfg, job):
    j = job.lower()
    for f in cfg['job_families']:
        if any(k in j for k in f['m']): return f['key']
    return cfg['job_families'][-1]['key']

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--extract', required=True)
    ap.add_argument('--events', required=True); ap.add_argument('--active', required=True); ap.add_argument('--asof', required=True)
    ap.add_argument('--labels', default=None); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfgall = json.load(open(a.config, encoding='utf8')); cfg = cfgall['movement']; ex = json.load(open(a.extract, encoding='utf8'))
    lab = json.load(open(a.labels, encoding='utf8')) if a.labels else {}
    br = {b['k']: {'en': b['n'], 'ar': lab.get(b['n'], b['n'])} for b in ex['branches']}
    ev = []; act = []
    for l in open(a.events, encoding='utf8'):
        l = l.strip()
        if not l or l.count('|') < 5: continue
        e, ym, b, j, n, c = l.split('|'); n = cfg.get('nat_merge', {}).get(n, n); ev.append([e, ym, b, fam(cfg, j), n, int(c)])
    for l in open(a.active, encoding='utf8'):
        l = l.strip()
        if not l or l.count('|') < 3: continue
        b, j, n, c = l.split('|'); n = cfg.get('nat_merge', {}).get(n, n); act.append([b, fam(cfg, j), n, int(c)])
    months = sorted({r[1] for r in ev}); asof = dt.date.fromisoformat(a.asof); cur = asof.strftime('%Y-%m')
    used_f = sorted({r[3] for r in ev} | {r[1] for r in act}, key=lambda k: [f['key'] for f in cfg['job_families']].index(k))
    used_n = sorted({r[4] for r in ev} | {r[2] for r in act})
    out = dict(asof=a.asof, current=cur, months=months,
               branches={k: br.get(k, {'en': 'Branch ' + k, 'ar': 'فرع ' + k}) for k in sorted({r[2] for r in ev} | {r[0] for r in act})},
               jobs={f['key']: {'en': f['en'], 'ar': f['ar']} for f in cfg['job_families'] if f['key'] in used_f},
               nats={k: cfg['nationalities'].get(k, {'en': 'Code ' + k, 'ar': 'رمز ' + k}) for k in used_n},
               saudi=str(cfgall.get('saudi_nationality_code', 420)), events=ev, active=act)
    json.dump(out, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('movement: %d months, %d event rows (%d hires, %d leavers), %d active rows (%d staff)' % (len(months), len(ev), sum(r[5] for r in ev if r[0] == 'H'), sum(r[5] for r in ev if r[0] == 'L'), len(act), sum(r[3] for r in act)))

if __name__ == '__main__':
    main()
