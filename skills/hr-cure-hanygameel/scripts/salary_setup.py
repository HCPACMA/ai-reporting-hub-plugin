#!/usr/bin/env python3
"""Salary setup screen (Cure HRSTFSAL): one row per employee with the CURRENT salary record, its allowances, the last payroll
GOSI shares, and the earlier salary periods (for contract-active staff). Reads the three Cure replies saved as raw/hr33a/b/c*.json
(each {"result": "<json list of {l: 'a|b|c'}>"}), raw/hr33d_job_codes.txt (code|job), raw/hr33e_salary_items.txt (item|ar|en|sign).

python3 scripts/salary_setup.py --config config/company.alfaihaa.json --raw raw --asof 2026-11-26 --out data/salary_setup.json

Row: [st, name, nat, job, branch, act, onjob, sep, cend, start, basic, social, day, hour, varsoc, co, staff, note, items, hist]
 act   = the employee has a contract with STATUS=A (active record)      onjob = current contract A and CURRENT_CONTRACT=Y and not separated
 items = [[item, amount], ...] of the current period      hist = [[start, end, basic, day, hour, [[item, amount]]], ...]"""
import json, argparse, os
ap = argparse.ArgumentParser()
ap.add_argument('--config', required=True); ap.add_argument('--raw', default='raw'); ap.add_argument('--asof', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args()
cfg = json.load(open(a.config, encoding='utf-8')); mv = cfg.get('movement', {}); jar = cfg.get('salary', {}).get('job_ar', {}); merge = mv.get('nat_merge', {}); nat_names = mv.get('nationalities', {})
def lines(f):
    r = json.load(open(os.path.join(a.raw, f), encoding='utf-8'))['result']
    return [x['l'] for x in json.loads(r)]
def items(s):
    return [[int(float(p.split(':')[0])), float(p.split(':')[1])] for p in s.split(';') if ':' in p] if s else []
def num(x):
    try: return round(float(x), 2)
    except Exception: return 0
def branch(o):
    if o in ('001', '002', '003', '004'): return '0' + o[2]
    return o[:2] if o and o != '?' else '??'
jobs = {}
for l in open(os.path.join(a.raw, 'hr33d_job_codes.txt'), encoding='utf-8'):
    if '|' in l: c, d = l.rstrip('\n').split('|', 1); jobs[c] = d.strip()
iname = {}
for l in open(os.path.join(a.raw, 'hr33e_salary_items.txt'), encoding='utf-8'):
    p = l.rstrip('\n').split('|')
    if len(p) >= 4: iname[int(p[0])] = {'ar': p[1], 'en': p[2], 'sign': p[3]}
hist = {}
for l in lines('hr33c_setup_history.json'):
    p = l.split('|', 6)
    hist.setdefault(p[0], []).append([p[1], p[2], num(p[3]), num(p[4]), num(p[5]), items(p[6] if len(p) > 6 else '')])
rows = []; seen_nat = set(); seen_job = set(); seen_br = set()
for f in ('hr33a_setup_active.json', 'hr33b_setup_inactive.json'):
    for l in lines(f):
        p = l.split('|', 16)
        if len(p) < 16: continue
        st, nm, nat, jb, org, fl, cend, start, basic, soc, day, hour, vs, co, sf, note = p[:16]; its = p[16] if len(p) > 16 else ''
        # note may contain extra '|' replaced already; items is the last field
        nat = merge.get(nat, nat); br = branch(org)
        act = 1 if fl[0] == 'A' else 0; onjob = 1 if (fl[0] == 'A' and fl[1] == 'Y' and fl[2] != 'Y') else 0
        rows.append([st, nm.strip(), nat, jb, br, act, onjob, 1 if fl[2] == 'Y' else 0, cend, start, num(basic), num(soc), num(day), num(hour), num(vs), num(co), num(sf), note, items(its), hist.get(st, [])])
        seen_nat.add(nat); seen_job.add(jb); seen_br.add(br)
rows.sort(key=lambda r: (-r[6], -r[5], r[0]))
out = {'asof': a.asof, 'saudi': str(cfg.get('saudi_nationality_code', 420)),
       'items': {str(k): v for k, v in iname.items()},
       'jobs': {c: {'en': jobs.get(c, 'Code ' + c), 'ar': jar.get(jobs.get(c, ''), jobs.get(c, 'رمز ' + c))} for c in sorted(seen_job)},
       'nats': {c: nat_names.get(c, {'en': 'Code ' + c, 'ar': 'رمز ' + c}) for c in sorted(seen_nat)},
       'brs': sorted(seen_br), 'rows': rows}
json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('salary setup: %d staff, %d on the job, %d active record, %d with history; %d items; size %d KB' % (len(rows), sum(r[6] for r in rows), sum(r[5] for r in rows), sum(1 for r in rows if r[19]), len(iname), os.path.getsize(a.out) // 1024))
