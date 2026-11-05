#!/usr/bin/env python3
"""Build data/review_screens.json for the pages 'Leaves and letters' and 'Additions and deductions by item'.

    python3 scripts/review_screens.py --month 2026-10 --letters ../Admin_Decisions_Review_Oct2026.xlsx \
        --leaves raw/hr27_leaves_oct2026.txt --items raw/hr28_items_oct2026.txt --names raw/hr19_names_oct.txt

leaves  line: staff|type|from|to|actual_return|POST_FLAG|days|VAC_MONTH/YEAR   (PS_STAFF_VACATIONS)
items   line: staff|salary_item|amount|status|note                             (PR_STAFF_ADDING_DEDUCTION and PR_STAFF_ADDING)
letters: sheet 'نتائج الخطابات' of the review workbook (page, folder, staff, name, type, letter, system, result, action)
"""
import argparse, json, os, re
import openpyxl

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ST = {'مطابق': 'ok', 'مطابق مع ملاحظة': 'note', 'خطأ': 'err', 'مؤجل (مستحقات)': 'def', 'متابعة': 'fut', 'خارج النطاق': 'out'}
RANK = {'err': 0, 'note': 1, 'fut': 2, 'def': 3, 'ok': 4, 'out': 5}
ITEM = {'-7': ('deduct', 'Absence / permission / penalty deduction', 'خصم غياب / إذن / جزاء'),
        '28': ('add', 'Day-31 entitlement', 'استحقاق يوم 31'),
        '24': ('add', 'Other entitlement', 'استحقاق آخر'),
        '-6': ('add', 'Additional (overtime) entitlement', 'استحقاق إضافي'),
        '18': ('add', 'Percentage entitlement', 'استحقاق نسبة')}


def names_of(path):
    d = {}
    for l in open(path, encoding='utf8'):
        m = re.match(r'\s*(\d{3,6})\|(.+)', l)
        if m:
            d[m.group(1)] = ' '.join(m.group(2).split())
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--month', required=True); ap.add_argument('--letters', required=True)
    ap.add_argument('--leaves', required=True); ap.add_argument('--items', required=True)
    ap.add_argument('--names', required=True); ap.add_argument('--out', default=os.path.join(KIT, 'data', 'review_screens.json'))
    ap.add_argument('--agg', default='', help='extra aggregate rows item:count:amount,...')
    a = ap.parse_args()
    names = names_of(a.names)
    ws = openpyxl.load_workbook(a.letters, data_only=True)['نتائج الخطابات']
    letters = []
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r[0] and not r[2]:
            continue
        pg, day, st, nm, typ, let, sy, res, act = [('' if x is None else str(x)) for x in r[:9]]
        code = st.strip()
        letters.append(dict(pg=pg, day=day, st=code, name=nm or names.get(code, ''), type=typ, letter=let, sys=sy, s=ST[res], action=act))
    by = {}
    for L in letters:
        by.setdefault(L['st'], []).append(L)
    def worst(code):
        ls = by.get(code, [])
        if not ls:
            return None, 0, ''
        w = min(ls, key=lambda x: RANK[x['s']])
        return w['s'], len(ls), w['pg']
    leaves = []
    for l in open(a.leaves, encoding='utf8'):
        p = l.strip().split('|')
        if len(p) < 8:
            continue
        s, ls, pg = worst(p[0])
        leaves.append(dict(st=p[0], name=names.get(p[0], ''), type=p[1], frm=p[2], to=p[3], ret=p[4], flag=p[5], days=int(p[6]), vm=p[7], ls=ls, lc=len(by.get(p[0], [])), pg=pg))
    items = []
    for l in open(a.items, encoding='utf8'):
        p = l.strip().split('|', 4)
        if len(p) < 5:
            continue
        s, ls, pg = worst(p[0])
        kind = ITEM.get(p[1], ('add', p[1], p[1]))[0]
        items.append(dict(st=p[0], name=names.get(p[0], ''), item=p[1], amt=float(p[2]), flag=p[3], note=p[4], ls=s, lc=len(by.get(p[0], [])), pg=pg, kind=kind))
    agg = []
    for x in [y for y in a.agg.split(',') if y]:
        i, c, m = x.split(':')
        agg.append(dict(item=i, n=int(c), amt=float(m)))
    out = dict(month=a.month, letters=letters, leaves=leaves, items=items, agg=agg,
               itemNames={k: dict(kind=v[0], en=v[1], ar=v[2]) for k, v in ITEM.items()})
    json.dump(out, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('letters', len(letters), 'leaves', len(leaves), 'items', len(items), '->', a.out)


if __name__ == '__main__':
    main()
