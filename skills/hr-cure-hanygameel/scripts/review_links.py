#!/usr/bin/env python3
"""Add direct letter-file links to data/review_screens.json.

    python3 scripts/review_links.py --review data/review_screens.json --index data/letters_index.json [--months 11-2026,10-2026]

Adds review['files'] = {employee code: [{rel, win, lbl, day, mt, cx, last}]} for the letter files of the review month
and the month before. Rules (Hany, 24 Nov 2026):
  - a file whose name says cancelled (ملغي / يلغي / يلغى / الغاء) is marked cx and never shown as the letter;
  - when an employee has several letters (an amended letter), the LAST one by date added to the folder (file time) is marked last;
    the page shows only that one and says how many older ones exist.
Letter rows that carry their own day prefer the folder of that day (latest file of that day)."""
import json, argparse, re, datetime
CX = re.compile(r'ملغي|ملغى|يلغي|يلغى|الغاء|إلغاء')
ap = argparse.ArgumentParser()
ap.add_argument('--review', default='data/review_screens.json'); ap.add_argument('--index', default='data/letters_index.json')
ap.add_argument('--months', default=None, help='comma list like 11-2026,10-2026 (default: review month and the month before)')
a = ap.parse_args()
R = json.load(open(a.review, encoding='utf-8')); I = json.load(open(a.index, encoding='utf-8'))
y, m = R['month'].split('-'); y, m = int(y), int(m)
py, pm = (y, m - 1) if m > 1 else (y - 1, 12)
months = a.months.split(',') if a.months else ['%02d-%d' % (m, y), '%02d-%d' % (pm, py)]
base = I['base_windows'].replace('\\\\', '\\'); MT = I.get('mt', {}); out = {}
codes = {r['st'] for k in ('letters', 'leaves', 'items') for r in R.get(k, [])}
for c in sorted(codes):
    L = []
    for rel in I['files'].get(c, []):
        p = rel.split('/')
        if p[0] not in months: continue
        day = p[1] if len(p) > 2 else ''
        t = MT.get(rel, 0)
        L.append({'rel': rel, 'win': base + '\\' + rel.replace('/', '\\'), 'lbl': p[-1], 'day': day, 'mt': datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M') if t else '', 'cx': bool(CX.search(p[-1])), '_t': t})
    if not L: continue
    L.sort(key=lambda f: (f['_t'], f['rel']))
    live = [f for f in L if not f['cx']]
    if live: live[-1]['last'] = True
    for f in L: f.pop('_t')
    out[c] = L
R['files'] = out; json.dump(R, open(a.review, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('letter links for %d of %d employees; %d with more than one letter' % (len(out), len(codes), sum(1 for v in out.values() if len(v) > 1)))
