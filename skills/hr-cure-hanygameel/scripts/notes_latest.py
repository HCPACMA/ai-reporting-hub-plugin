#!/usr/bin/env python3
"""Mark the letter files of every note person: mt (date added), cx (cancelled by name), last (the latest non-cancelled one).
Run after letters_index.json is regenerated and before build_hr.py. Idempotent.
    python3 scripts/notes_latest.py --notes data/payroll_notes.json --index data/letters_index.json"""
import json, re, argparse, datetime
CX = re.compile(r'ملغي|ملغى|يلغي|يلغى|الغاء|إلغاء')
ap = argparse.ArgumentParser(); ap.add_argument('--notes', default='data/payroll_notes.json'); ap.add_argument('--index', default='data/letters_index.json')
a = ap.parse_args()
N = json.load(open(a.notes, encoding='utf-8')); MT = json.load(open(a.index, encoding='utf-8')).get('mt', {}); k = 0
for n in N['notes']:
    for p in n.get('people', []):
        P = p.get('paths') or []
        for q in P:
            t = MT.get(q['rel'], 0); q['mt'] = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M') if t else ''
            q['cx'] = bool(CX.search(q['rel'].split('/')[-1])); q.pop('last', None)
        live = [q for q in P if not q['cx']]
        if live:
            max(live, key=lambda q: (q['mt'], q['rel']))['last'] = True; k += 1
json.dump(N, open(a.notes, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('people with a latest letter marked:', k)
