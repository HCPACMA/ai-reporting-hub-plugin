#!/usr/bin/env python3
"""Add direct letter-file links to data/review_screens.json.

    python3 scripts/review_links.py --review data/review_screens.json --index data/letters_index.json [--months 10-2026]

Adds review['files'] = {employee code: [{rel, win, lbl, day}]} for letter files found in the review month
folder(s). Letter rows prefer the folder of their own day; screens fall back to all files of the month."""
import json, argparse, re
ap = argparse.ArgumentParser()
ap.add_argument('--review', default='data/review_screens.json'); ap.add_argument('--index', default='data/letters_index.json')
ap.add_argument('--months', default=None, help='comma list like 10-2026,09-2026 (default: review month)')
a = ap.parse_args()
R = json.load(open(a.review, encoding='utf-8')); I = json.load(open(a.index, encoding='utf-8'))
y, m = R['month'].split('-'); months = a.months.split(',') if a.months else [m + '-' + y]
base = I['base_windows']; out = {}
codes = {r['st'] for k in ('letters', 'leaves', 'items') for r in R.get(k, [])}
for c in sorted(codes):
    for rel in I['files'].get(c, []):
        p = rel.split('/')
        if p[0] not in months: continue
        day = p[1] if len(p) > 2 else ''
        out.setdefault(c, []).append({'rel': rel, 'win': base + '\\' + rel.replace('/', '\\'), 'lbl': p[-1], 'day': day})
R['files'] = out; json.dump(R, open(a.review, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('letter links for %d of %d employees' % (len(out), len(codes)))
