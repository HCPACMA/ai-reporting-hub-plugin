#!/usr/bin/env python3
"""Parse the monthly overtime statement into entries (employee x row) with dates, hours and the working window from the reason.
    python3 scripts/ot_feas_parse.py --stmt "<Summary of Overtime October 2026.xlsx>" --month 2026-10 --out raw/otf_entries.2026-10.json
Sheet -> branch: Riyadh=Riyadh, Faiha 1=BUR1, Faiha 2=BUR2, Rafha=Rafha. ID 3xxx = doctor, 6xxx = nurse/technician/other.
"""
import argparse, json, re, calendar, openpyxl
ap = argparse.ArgumentParser(); ap.add_argument('--stmt', required=True); ap.add_argument('--month', required=True); ap.add_argument('--out', required=True)
a = ap.parse_args()
Y, M = int(a.month[:4]), int(a.month[5:])
MON = calendar.month_name[M].lower()
BR = {'riyadh': 'Riyadh', 'faiha 1': 'BUR1', 'faiha 2': 'BUR2', 'rafha': 'Rafha'}
TM = re.compile(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm|nn|mn)?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm|nn|mn)', re.I)

def hr(h, m, ap_):
    h = int(h); m = int(m or 0); ap_ = (ap_ or '').lower()
    if ap_ == 'mn': h = 0 if h == 12 else h
    elif ap_ == 'nn': h = 12
    elif ap_ == 'pm': h = h % 12 + 12
    elif ap_ == 'am': h = h % 12
    return h + m / 60.0

def windows(reason):
    out = []
    for m in TM.finditer(reason or ''):
        h1, m1, a1, h2, m2, a2 = m.groups()
        if int(h2) > 12 and a2 and a2.lower() in ('am', 'pm'): h2 = str(int(h2) % 10)   # typo like 98am
        e = hr(h2, m2, a2)
        s = hr(h1, m1, a1 or a2)
        if e <= s: e += 24
        out.append([round(s, 2), round(e, 2)])
    return out

def octdays(txt):
    """days of the target month named in the date cell (days listed after the month name; other months ignored)"""
    t = (txt or '').replace('\n', ' ')
    cur = None; days = []
    for tok in re.findall(r'[A-Za-z]+|\d+', t):
        if tok.isalpha():
            cur = tok.lower() if tok.lower() in [calendar.month_name[i].lower() for i in range(1, 13)] or tok.lower().startswith(MON[:3]) else cur
            if tok.lower().startswith(MON[:3]): cur = MON
            elif tok.lower() in [calendar.month_name[i].lower() for i in range(1, 13)]: cur = tok.lower()
            continue
        if cur in (MON, None):
            n = int(tok)
            if 1 <= n <= 31: days.append(n)
    # ranges like "1-30" were split into 1 and 30; expand 2-number ranges written with a dash
    if re.search(r'\d\s*-\s*\d', t) and len(days) == 2 and days[0] < days[1]:
        days = list(range(days[0], days[1] + 1))
    return sorted(set(days))

wb = openpyxl.load_workbook(a.stmt, data_only=True); E = []
for ws in wb.worksheets:
    br = BR.get(ws.title.strip().lower())
    if not br: continue
    cur = None
    for r in ws.iter_rows(values_only=True):
        r = list(r) + [None] * 12
        if isinstance(r[0], (int, float)) and r[2] is not None and str(r[2]).strip().isdigit():
            cur = {'no': int(r[0]), 'name': str(r[1]).strip(), 'st': str(int(float(r[2]))), 'sheet': ws.title.strip(), 'br': br}
            off = 0
        elif cur is not None and r[0] is None and r[1] is None and r[2] is None and (r[4] or r[3]):
            off = 0
        elif cur is not None and r[0] and not isinstance(r[0], (int, float)) and isinstance(r[1], str) and re.search(r'\d', r[1]):
            off = -3   # continuation row where day sits in column A
        else:
            continue
        d, dt, nd, each, hrs, rsn = r[3 + off], r[4 + off], r[5 + off], r[6 + off], r[7 + off], r[8 + off]
        if dt is None or hrs is None: continue
        try: hrs = float(hrs); each = float(each); nd = float(nd)
        except Exception: continue
        E.append({**{k: cur[k] for k in ('st', 'name', 'sheet', 'br')}, 'day': str(d or '').strip(), 'date': str(dt).replace('\n', ' ').strip(),
                  'days': nd, 'each': each, 'hrs': hrs, 'reason': ' '.join(str(rsn or '').split()), 'dd': octdays(str(dt)), 'win': windows(str(rsn or ''))})
for e in E:
    e['kind'] = 'doctor' if e['st'].startswith('3') else ('nurse' if e['st'].startswith('6') else 'other')
json.dump({'month': a.month, 'entries': E}, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(E), 'entries;', sum(1 for e in E if e['kind'] == 'doctor'), 'doctor rows;', sum(1 for e in E if not e['win']), 'rows without window')
