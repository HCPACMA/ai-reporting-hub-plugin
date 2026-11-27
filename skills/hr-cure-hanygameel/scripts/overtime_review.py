#!/usr/bin/env python3
"""Overtime review (Hany, 24 Nov 2026): overtime is a monthly accrual booked on the employee account from the ATTACHED
'Summary of Overtime' statement (not from HR letters). Per employee we tie: statement hours/days -> item-level file ->
Cure item -6 -> voucher credit on 2121003/<staff>. Output data/overtime.<month>.json (+ optional coloured xlsx).

python3 scripts/overtime_review.py --stmt STATEMENT.xlsx --item ITEMLEVEL.xlsx --cure raw/ot02..txt --voucher raw/ot01..txt \
   --vno JV1-26/02935 --pstmt PREV_STATEMENT.xlsx --pitem PREV_ITEM.xlsx --month 2026-10 --out data/overtime.2026-10.json --xlsx OUT.xlsx"""
import re, json, argparse, openpyxl
ap = argparse.ArgumentParser()
for k in ('leaves', 'pcure', 'stmt', 'item', 'cure', 'voucher', 'vno', 'pstmt', 'pitem', 'month', 'out', 'xlsx'): ap.add_argument('--' + k)
a = ap.parse_args()
MON = re.compile(r'[A-Za-z]+')
def dates(s):
    s = MON.sub(' ', str(s or '')).replace('&', ',')
    n = 0
    for tok in re.split(r'[,\s]+', s):
        if not tok: continue
        m = re.fullmatch(r'(\d+)-(\d+)', tok)
        if m: n += int(m.group(2)) - int(m.group(1)) + 1
        elif re.fullmatch(r'\d+', tok): n += 1
    return n
def octdays(s, mon=10):
    cur = mon; out = set()
    for tok in re.split(r'[\s,&]+', str(s or '').replace('\n', ' ')):
        if not tok: continue
        t = tok.lower().rstrip('.'); tok = tok.rstrip('.')
        if t.startswith('sep'): cur = 9; continue
        if t.startswith('oct'): cur = 10; continue
        m = re.fullmatch(r'(\d+)-(\d+)', tok)
        if m: rng = range(int(m.group(1)), int(m.group(2)) + 1)
        elif re.fullmatch(r'\d+', tok): rng = [int(tok)]
        else: continue
        if cur == mon: out.update(d for d in rng if 1 <= d <= 31)
    return out
def stmt(path):
    out = {}; cur = None; sheet_tot = {}
    for ws in openpyxl.load_workbook(path, data_only=True):
        for r in ws.iter_rows(min_row=4, values_only=True):
            r = list(r) + [None] * 12
            if isinstance(r[0], str) and r[0].startswith('Total Hours'):
                sheet_tot[ws.title] = (r[7], r[9]); cur = None; continue
            if r[2] not in (None, '') and isinstance(r[2], (int, float)):
                cur = out.setdefault(str(int(r[2])), {'name': r[1], 'sheet': ws.title, 'rows': [], 'sub': None, 'hours': 0.0})
                cur['sub'] = r[9]
            if cur is None or r[7] is None: continue
            row = {'day': str(r[3] or '').replace('\n', ' '), 'date': str(r[4] or '').replace('\n', ' ').strip(), 'days': r[5], 'each': r[6], 'hrs': r[7], 'flags': []}
            try:
                if abs(float(r[5]) * float(r[6]) - float(r[7])) > 0.01: row['flags'].append('E1')
            except Exception: row['flags'].append('E1')
            nd = dates(r[4])
            if nd and r[5] is not None and not re.search(r'\d+\s*-\s*\d+', str(r[4])) and abs(nd - float(r[5])) > 0.01: row['flags'].append('E2'); row['dcount'] = nd
            row['octd'] = sorted(octdays(r[4]))
            cur['rows'].append(row); cur['hours'] += float(r[7])
    return out, sheet_tot
def items(path):
    ws = openpyxl.load_workbook(path, data_only=True).active; out = {}
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[0] in (None, '') or not re.fullmatch(r'\d+', str(r[0]).strip()): continue
        if len(r) < 8 or r[6] is None:  # older layout: id, name, item, period, hours(الرقم), notes
            out[str(r[0]).strip()] = {'basic': 0.0, 'amt': 0.0, 'hrs': float(r[4] or 0), 'status': ''}; continue
        out[str(r[0]).strip()] = {'basic': float(r[5] or 0), 'amt': float(r[6] or 0), 'hrs': float(r[7] or 0), 'status': (r[10] or '').strip()}
    return out
def kv(path):
    return {l.split('|')[0]: float(l.split('|')[1]) for l in open(path, encoding='utf-8') if '|' in l}
LV = {}
if a.leaves:
    for l in open(a.leaves, encoding='utf-8'):
        p = l.strip().split('|')
        if len(p) >= 3: LV.setdefault(p[0], []).append((int(p[1][8:10]), int(p[2][8:10]), p[3] if len(p) > 3 else ''))
S, tot = stmt(a.stmt); I = items(a.item); C = kv(a.cure); V = kv(a.voucher)
PI = items(a.pitem) if a.pitem else {}; PC = kv(a.pcure) if a.pcure else {}
rate = lambda i: (i['amt'] / i['hrs']) if i and i['hrs'] else None
rows = []
for c in sorted(set(S) | set(I) | set(C) | set(V)):
    s, i = S.get(c), I.get(c); fl = []
    if s:
        if any(r['flags'] for r in s['rows']): fl += sorted({f for r in s['rows'] for f in r['flags']})
        if s['sub'] is not None and abs(float(s['sub']) - s['hours']) > 0.01: fl.append('E3')
    if not s: fl.append('E7s')
    if not i: fl.append('E7i')
    if c not in C: fl.append('E7c')
    if c not in V: fl.append('E7v')
    if s and i and abs(i['hrs'] - s['hours']) > 0.01: fl.append('E4')
    if i and c in C and abs(i['amt'] - C[c]) > 0.01: fl.append('E5')
    if c in C and c in V and abs(round(C[c]) - V[c]) > 0.51: fl.append('E6')
    conf = []; chrs = 0.0
    for row in (s or {}).get('rows', []):
        for (f, t, note) in LV.get(c, []):
            hit = [d for d in row['octd'] if f <= d <= t]
            if hit:
                try: h = len(hit) * float(row['each'])
                except Exception: h = 0
                chrs += h; conf.append({'days': hit, 'hrs': h, 'leave': note})
    if conf: fl.append('E9')
    r0 = rate(i); pi = PI.get(c); rp = (PC[c] / pi['hrs']) if pi and pi['hrs'] and c in PC else None; chg = None
    if r0 and rp: chg = r0 / rp - 1
    if chg is not None and abs(chg) > 0.02: fl.append('E8')
    rows.append({'st': c, 'name': (s or {}).get('name') or '', 'sheet': (s or {}).get('sheet') or '', 'hrs_stmt': round(s['hours'], 2) if s else None, 'sub': s['sub'] if s else None, 'hrs_item': i['hrs'] if i else None,
                 'basic': i['basic'] if i else None, 'amt_item': i['amt'] if i else None, 'amt_cure': round(C[c], 2) if c in C else None, 'amt_voucher': V.get(c), 'rate': round(r0, 4) if r0 else None, 'rate_prev': round(rp, 4) if rp else None,
                 'rate_chg': round(chg, 4) if chg is not None else None, 'flags': fl, 'conflict': conf, 'conflict_hrs': chrs, 'rows': (s or {}).get('rows', [])})
res = {'month': a.month, 'voucher': a.vno, 'rows': rows, 'sheet_totals': {k: list(v) for k, v in tot.items()},
       'sums': {'stmt': round(sum(r['hrs_stmt'] or 0 for r in rows), 2), 'cure': round(sum(C.values()), 2), 'voucher': sum(V.values()), 'item': round(sum(i['amt'] for i in I.values()), 2)}}
json.dump(res, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
from collections import Counter
print([(r['st'], r['conflict_hrs'], r['conflict']) for r in rows if r['conflict']]); print('employees', len(rows), 'flagged', sum(1 for r in rows if r['flags']), dict(Counter(f for r in rows for f in r['flags'])), res['sums'])
for r in rows:
    if r['flags']: print(r['st'], r['name'][:22], r['flags'], 'stmt', r['hrs_stmt'], 'sub', r['sub'], 'item', r['hrs_item'], 'cure', r['amt_cure'], 'vch', r['amt_voucher'], 'rate', r['rate'], r['rate_prev'], r['rate_chg'])
