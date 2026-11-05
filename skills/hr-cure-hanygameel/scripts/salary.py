#!/usr/bin/env python3
"""Salary bands by job for the Salaries screen (min, max, average; filter by branch, nationality, job).

    python3 scripts/salary.py --config config/company.<co>.json --extract data/extract.<co>.<date>.json \
        --raw raw/hr31_salary_by_dims.txt --asof 2026-10-26 --labels config/labels_ar.json --out data/salary.json

raw lines: branch|job|nat|n|sum_pkg|min_pkg|max_pkg|sum_basic|min_basic|max_basic. Groups are exact: the page combines them into average (sum over n), min and max for any filter."""
import argparse, json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True); ap.add_argument('--extract', required=True); ap.add_argument('--raw', required=True)
    ap.add_argument('--asof', required=True); ap.add_argument('--labels', default=None); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfgall = json.load(open(a.config, encoding='utf8')); ex = json.load(open(a.extract, encoding='utf8'))
    lab = json.load(open(a.labels, encoding='utf8')) if a.labels else {}
    mv = cfgall.get('movement', {}); jar = cfgall.get('salary', {}).get('job_ar', {}); merge = mv.get('nat_merge', {}); nats = mv.get('nationalities', {})
    br = {b['k']: {'en': b['n'], 'ar': lab.get(b['n'], b['n'])} for b in ex['branches']}
    G = []
    for l in open(a.raw, encoding='utf8'):
        l = l.strip()
        if l.count('|') < 9: continue
        p = l.split('|'); p[2] = merge.get(p[2], p[2]); G.append(p[:3] + [int(float(x)) for x in p[3:10]])
    jobs = sorted({g[1] for g in G}); ns = sorted({g[2] for g in G}); bs = sorted({g[0] for g in G})
    out = dict(asof=a.asof, saudi=str(cfgall.get('saudi_nationality_code', 420)),
               branches={k: br.get(k, {'en': 'Branch ' + k, 'ar': 'فرع ' + k}) for k in bs},
               jobs={j: {'en': j, 'ar': jar.get(j, j)} for j in jobs},
               nats={k: nats.get(k, {'en': 'Code ' + k, 'ar': 'رمز ' + k}) for k in ns}, groups=G)
    json.dump(out, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
    print('salary: %d groups, %d staff, package total %d' % (len(G), sum(g[3] for g in G), sum(g[4] for g in G)))

if __name__ == '__main__':
    main()
