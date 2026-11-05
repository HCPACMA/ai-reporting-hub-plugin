#!/usr/bin/env python3
"""Maintain data/payroll_notes.json, the payroll notes register shown in the HR Command Center.

    python3 scripts/notes_tool.py list  --month 2026-10 [--state open|new|carried|closed|all]
    python3 scripts/notes_tool.py close A01 A02 --month 2026-10
    python3 scripts/notes_tool.py reopen A01
    python3 scripts/notes_tool.py apply changes.json          # the JSON copied from the page (Export my changes)
    python3 scripts/notes_tool.py add --month 2026-10 --src admin --cat ded --pri M --emp 6388 \
         --title-en "..." --title-ar "..." --detail-en "..." --detail-ar "..." --action-en "..." --action-ar "..." \
         --owner-en Payroll --owner-ar الرواتب [--amount 225]

Carry-over rule (same as the page): a note shows in its own month and in every later month until it is closed.
status open = carried until closed, info = shown only in its own month, done = closed in closedIn.
Run build_hr.py afterwards so the page picks up the change. Every note needs English and Arabic text.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(HERE)
PATH = os.path.join(KIT, 'data', 'payroll_notes.json')

def load(): return json.load(open(PATH, encoding='utf8'))
def save(d): json.dump(d, open(PATH, 'w', encoding='utf8'), ensure_ascii=False, indent=1); print('saved', PATH)

def state_in(n, month):
    if n['month'] > month: return None
    if n['status'] == 'info': return 'info' if n['month'] == month else None
    if n['status'] == 'done':
        c = n.get('closedIn')
        if c and c < month: return None
        if c and c == month: return 'closed'
    return 'carried' if n['month'] < month else 'new'

def cmd_list(a):
    d = load(); rows = []
    for n in d['notes']:
        s = state_in(n, a.month)
        if not s: continue
        if a.state == 'open' and s not in ('new', 'carried'): continue
        if a.state not in ('open', 'all') and s != a.state: continue
        rows.append((s, n))
    order = {'H': 0, 'M': 1, 'L': 2, 'I': 3}
    rows.sort(key=lambda x: (order[x[1]['pri']], x[1]['id']))
    for s, n in rows:
        amt = f" {n['amt']:,.0f}" if n.get('amt') else ''
        print(f"{n['id']:5} {n['pri']} {s:8} {n['emp'][:22]:22} {n['t']['en'][:70]}{amt}")
    print(f"-- {len(rows)} notes in {a.month} ({a.state})")

def cmd_close(a):
    d = load(); ids = {n['id']: n for n in d['notes']}
    for i in a.ids:
        if i not in ids: sys.exit(f"unknown id {i}")
        ids[i]['status'] = 'done'; ids[i]['closedIn'] = a.month
    save(d)

def cmd_reopen(a):
    d = load(); ids = {n['id']: n for n in d['notes']}
    for i in a.ids:
        if i not in ids: sys.exit(f"unknown id {i}")
        ids[i]['status'] = 'open'; ids[i]['closedIn'] = None
    save(d)

def next_id(d, prefix):
    nums = [int(n['id'][len(prefix):]) for n in d['notes'] if n['id'].startswith(prefix) and n['id'][len(prefix):].isdigit()]
    return f"{prefix}{(max(nums) + 1 if nums else 1):02d}"

def cmd_add(a):
    d = load()
    n = dict(id=a.id or next_id(d, a.src[0].upper()), month=a.month, src=a.src, cat=a.cat, pri=a.pri, emp=a.emp, amt=a.amount,
             t=dict(en=a.title_en, ar=a.title_ar), d=dict(en=a.detail_en or a.title_en, ar=a.detail_ar or a.title_ar),
             x=dict(en=a.action_en or '-', ar=a.action_ar or '-'), owner=dict(en=a.owner_en, ar=a.owner_ar), status='open', closedIn=None)
    d['notes'].append(n); save(d); print('added', n['id'])

def cmd_apply(a):
    d = load(); ch = json.load(open(a.file, encoding='utf8')); ids = {n['id']: n for n in d['notes']}
    for i, o in ch.get('overrides', {}).items():
        if i in ids:
            ids[i]['status'] = o['status']; ids[i]['closedIn'] = o.get('closedIn')
    added = 0
    for u in ch.get('userNotes', []):
        src = 'admin' if u.get('src') in (None, 'user') else u['src']
        nid = next_id(d, 'U'); u = dict(u, id=nid, src=src); d['notes'].append(u); ids[nid] = u; added += 1
    save(d); print(f"applied {len(ch.get('overrides', {}))} status changes and {added} new notes")

def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('list'); p.add_argument('--month', required=True); p.add_argument('--state', default='open'); p.set_defaults(f=cmd_list)
    p = sp.add_parser('close'); p.add_argument('ids', nargs='+'); p.add_argument('--month', required=True); p.set_defaults(f=cmd_close)
    p = sp.add_parser('reopen'); p.add_argument('ids', nargs='+'); p.set_defaults(f=cmd_reopen)
    p = sp.add_parser('apply'); p.add_argument('file'); p.set_defaults(f=cmd_apply)
    p = sp.add_parser('add'); p.set_defaults(f=cmd_add)
    for k in ['month', 'src', 'cat', 'pri', 'emp', 'title-en', 'title-ar', 'owner-en', 'owner-ar']: p.add_argument('--' + k, required=True)
    for k in ['id', 'detail-en', 'detail-ar', 'action-en', 'action-ar']: p.add_argument('--' + k)
    p.add_argument('--amount', type=float)
    a = ap.parse_args(); a.f(a)

if __name__ == '__main__':
    main()
