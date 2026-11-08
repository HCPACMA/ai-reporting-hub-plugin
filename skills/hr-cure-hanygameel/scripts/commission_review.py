#!/usr/bin/env python3
"""Doctors' commission review: sheet inputs vs Cure (monthly).
Usage: commission_review.py --sheet <xlsm> --month 2026-09 --raw raw --out data/commission.json [--xlsx out/Commission_Review_2026-09.xlsx]
Cure sources (all from the Riyadh/BUR1/BUR2/Rafha databases):
  cm01  DOCTOR_COMMISSION_DATA by doctor: cash (type C), discounted cash (D), credit (R), pharmacy group 19 excluded. NET_AMT, no VAT.
  cm02  PS_STAFF_VACATIONS overlapping the month (POST_FLAG <> C)
  cm03  PR_STAFF_ADDING_DEDUCTION item 18 of the pay month (commission paid one month late)
"""
import argparse, calendar, collections, datetime as dt, json, os, sys
import warnings; warnings.filterwarnings('ignore')
import openpyxl

BR = {'الرياض': 'Riyadh', 'بريدة 1': 'BUR1', 'بريدة 2': 'BUR2', 'رفحا': 'Rafha', 'رفحاء': 'Rafha'}
BRK = {'Riyadh': '01', 'BUR1': '02', 'BUR2': '03', 'Rafha': '04'}
TOL = 1.0


def I(en, ar): return {'en': en, 'ar': ar}


def f(x):
    try: return float(x)
    except Exception: return 0.0


def read_pipe(p):
    return [l.rstrip('\n').split('|') for l in open(p, encoding='utf8') if l.strip()]


def leave_days(rows, ym):
    y, m = map(int, ym.split('-')); dim = calendar.monthrange(y, m)[1]
    a, b = dt.date(y, m, 1), dt.date(y, m, dim)
    out = collections.defaultdict(lambda: {'annual': 0, 'emerg': 0, 'other': 0, 'recs': []})
    for s, vt, pf, df, dto, ar in rows:
        d1, d2 = dt.date.fromisoformat(df), dt.date.fromisoformat(dto)
        if ar and ar != 'None':
            d2 = min(d2, dt.date.fromisoformat(ar) - dt.timedelta(days=1))
        lo, hi = max(d1, a), min(d2, b)
        n = (hi - lo).days + 1 if hi >= lo else 0
        k = 'annual' if vt == '17' else ('emerg' if vt == '09' else 'other')
        out[s][k] += n; out[s]['recs'].append([vt, df, dto, ar, n])
    return dim, out


import re
from openpyxl.utils import column_index_from_string as _ci, get_column_letter as _gl

_EXT = re.compile(r"'اجمالى النسب'!\$?([A-Z]{1,2})\$?(\d+)")
_REF = re.compile(r"(?<![A-Za-z!'])\$?([A-Z]{1,2})\$?(\d+)(?::\$?([A-Z]{1,2})\$?(\d+))?")


def _refs(fm):
    ext = _EXT.findall(fm)
    fm2 = _EXT.sub(' ', fm)
    fm2 = re.sub(r"'[^']*'!\$?[A-Z]{1,2}\$?\d+(:\$?[A-Z]{1,2}\$?\d+)?", ' ', fm2)
    out = []
    for a_, b_, c_, d_ in _REF.findall(fm2):
        if c_:
            for col in range(_ci(a_), _ci(c_) + 1):
                for row in range(int(b_), int(d_) + 1): out.append(_gl(col) + str(row))
        else: out.append(a_ + b_)
    return ext, out


def sheet_basis(wf, S, r):
    """What the doctor's own sheet formula really uses: follows the commission cell back to the cash (L,N) and credit (M,O) inputs."""
    j = S.cell(r, 10).value
    m = re.match(r"=\+?'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)", str(j)) if isinstance(j, str) else None
    if not m or m.group(1) not in wf.sheetnames: return 'manual', None
    ws = wf[m.group(1)]; seen = set(); stack = [m.group(2) + m.group(3)]; cash = cred = False
    while stack:
        c = stack.pop()
        if c in seen: continue
        seen.add(c); v = ws[c].value
        if isinstance(v, str) and v.startswith('='):
            ext, loc = _refs(v)
            for col, _ in ext:
                if col in ('L', 'N'): cash = True
                if col in ('M', 'O'): cred = True
            stack += loc
    return ('cash_credit' if cash and cred else 'cash' if cash else 'credit' if cred else 'fixed'), m.group(1)


def _date(v):
    if isinstance(v, dt.datetime): return v.date()
    if isinstance(v, str):
        for fmt in ('%d/%m/%Y', '%Y-%m-%d'):
            try: return dt.datetime.strptime(v.strip(), fmt).date()
            except Exception: pass
    return dt.date(2019, 1, 1)


def doctor_basis(wf, rules_path):
    """Per doctor: basis of the commission (cash only, or cash and credit) from the rules file, checked against the sheet formula."""
    S = wf['اجمالى النسب']
    wr = openpyxl.load_workbook(rules_path, data_only=True).worksheets[0]
    rules = {}
    for r in range(4, wr.max_row + 1):
        code = wr.cell(r, 4).value
        if code is None: continue
        code = str(code).strip()
        cell = lambda col: wr.cell(r, _ci(col)).value
        ent = {'row': r, 'start': _date(cell('C')), 'cls': str(cell('G') or '').strip(), 'H': cell('H'), 'I': cell('I'), 'min': cell('Q'),
               'note': str(cell('AE') or '').strip(), 'comp_br': any(cell(_gl(c)) not in (None, '') for c in range(_ci('AG'), _ci('AN') + 1)),
               'tot_br': any(cell(_gl(c)) not in (None, '') for c in range(_ci('AO'), _ci('AV') + 1)),
               'br_n': sum(1 for c in range(_ci('R'), _ci('AA') + 1, 2) if wr.cell(r, c).value not in (None, ''))}
        if code not in rules or (ent['start'], ent['row']) >= (rules[code]['start'], rules[code]['row']): rules[code] = ent
    out = []
    for r in range(5, 112):
        code = S.cell(r, 4).value; staff = S.cell(r, 9).value
        if code is None or staff is None: continue
        staff = str(staff).strip(); ru = rules.get(staff)
        kind, sh = sheet_basis(wf, S, r)
        d = {'c': str(code).strip(), 's': staff, 'n': str(S.cell(r, 3).value or '').strip(), 'cl': str(S.cell(r, 6).value or '').strip(),
             'br': BR.get(str(S.cell(r, 7).value or '').strip(), str(S.cell(r, 7).value or '').strip()), 'rule': bool(ru), 'sheetBasis': kind}
        if ru:
            hr = ru['H'] if isinstance(ru['H'], (int, float)) else None
            ir = ru['I'] if isinstance(ru['I'], (int, float)) else 0
            note = ru['note']
            credit = bool((ir and ir > 0) or ru['comp_br'] or ru['tot_br'] or re.search('اجمالي|اجمالى|إجمالي|شركات|الاجل|الآجل|تامين|تأمين', note))
            typ = 'brackets' if (ru['cls'].lower() == 'brackets' or ru['H'] == 'شرائح' or ru['br_n'] >= 2) else ('ratio' if hr else 'other')
            d.update(basis='cash_credit' if credit else 'cash', typ=typ, rc=hr, rk=ir or None, mn=ru['min'] if isinstance(ru['min'], (int, float)) else None,
                     brk=ru['br_n'], note=note[:220], start=str(ru['start']))
        else:
            d.update(basis='cash_credit' if kind == 'cash_credit' else 'cash', typ='other', rc=None, rk=None, mn=None, brk=0, note='', start='')
        # the sheet and the rules file disagree about what the commission is paid on
        d['mismatch'] = bool(ru) and kind in ('cash', 'cash_credit') and kind != d['basis']
        out.append(d)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rules', help='Doctor Commission Rules.xlsx')
    ap.add_argument('--sheet', required=True); ap.add_argument('--month', required=True)
    ap.add_argument('--raw', default='raw'); ap.add_argument('--out', default='data/commission.json')
    ap.add_argument('--xlsx'); ap.add_argument('--paid-month')
    a = ap.parse_args()
    ym = a.month
    y, m = map(int, ym.split('-'))
    pm = a.paid_month or (f'{y}-{m + 1:02d}' if m < 12 else f'{y + 1}-01')

    cure = collections.defaultdict(lambda: {'cash': 0.0, 'disc': 0.0, 'cred': 0.0, 'med': 0.0, 'br': {}})
    for b, i, c, d, cr, md in read_pipe(os.path.join(a.raw, f'cm01_cure_revenue_{ym}.txt')):
        x = cure[i]; x['cash'] += f(c); x['disc'] += f(d); x['cred'] += f(cr); x['med'] += f(md)
        x['br'][b] = x['br'].get(b, 0) + f(c) + f(d) + f(cr)
    dim, lv = leave_days(read_pipe(os.path.join(a.raw, f'cm02_leaves_{ym}.txt')), ym)
    pay = {s: f(v) for s, v in read_pipe(os.path.join(a.raw, f'cm03_item18_{pm}.txt'))}

    wb = openpyxl.load_workbook(a.sheet, data_only=True)
    S = wb['اجمالى النسب']; B = wb['البيانات من الفروع']
    rows = []; seen = set()
    for r in range(5, 112):
        code = S.cell(r, 4).value; staff = S.cell(r, 9).value
        if code is None or staff is None: continue
        code = str(code).strip(); staff = str(staff).strip()
        days = S.cell(r, 5).value
        cashS = f(S.cell(r, 12).value) + f(S.cell(r, 14).value)
        credS = f(S.cell(r, 13).value) + f(S.cell(r, 15).value)
        comm = f(S.cell(r, 10).value)
        c = cure.get(staff, {'cash': 0, 'disc': 0, 'cred': 0, 'med': 0, 'br': {}})
        cashC = round(c['cash'] + c['disc'], 2); credC = round(c['cred'], 2)
        l = lv.get(staff, {'annual': 0, 'emerg': 0, 'other': 0, 'recs': []})
        seen.add(staff)
        iss = []
        sheet_tot, cure_tot = cashS + credS, cashC + credC
        if sheet_tot > 1000 and cure_tot < 0.05 * sheet_tot:
            # department doctors (lab, radiology, dental, prosthetics): revenue is not on the doctor's own invoices
            iss.append({'k': 'dept', 'sev': 'warn', 't': I(f'Sheet revenue {sheet_tot:,.2f} but Cure doctor invoices show {cure_tot:,.2f}: department revenue, verify against the cost-centre ledger {S.cell(r, 8).value}',
                                                           f'إيراد الشيت {sheet_tot:,.2f} بينما فواتير الطبيب في Cure {cure_tot:,.2f}: إيراد قسم، راجعه مع الأستاذ على مركز التكلفة {S.cell(r, 8).value}')})
        else:
            for nm_en, nm_ar, s_, c_ in (('Cash', 'الكاش', cashS, cashC), ('Credit', 'الآجل', credS, credC)):
                dlt = s_ - c_
                if abs(dlt) > TOL:
                    small = abs(dlt) <= 250
                    iss.append({'k': 'rev', 'sev': 'warn' if small else 'bad',
                                't': I(f'{nm_en} revenue in the sheet {s_:,.2f} vs Cure {c_:,.2f} (diff {dlt:+,.2f})',
                                       f'إيراد {nm_ar} في الشيت {s_:,.2f} مقابل Cure {c_:,.2f} (الفرق {dlt:+,.2f})')})
        dcure = dim - l['annual']
        dsheet = f(days) if days is not None else None
        if dsheet is not None and abs(dsheet - dcure) > 0.01:
            iss.append({'k': 'days', 'sev': 'bad', 't': I(f'Working days in the sheet {dsheet:g} vs {dcure} from Cure ({dim} days minus {l["annual"]} annual leave)',
                                                          f'أيام العمل في الشيت {dsheet:g} والصحيح من Cure {dcure} ({dim} يوم ناقص {l["annual"]} إجازة سنوية)')})
        if l['emerg']:
            iss.append({'k': 'emg', 'sev': 'warn', 't': I(f'{l["emerg"]} emergency-leave days in Cure, not deducted from working days (confirm policy)',
                                                          f'{l["emerg"]} يوم إجازة طارئة في Cure لم تُخصم من أيام العمل (تأكد من السياسة)')})
        p = pay.get(staff)
        if p is None and comm > TOL:
            iss.append({'k': 'pay', 'sev': 'bad', 't': I(f'Sheet commission {comm:,.2f} but no item 18 in the {pm} payroll', f'نسبة الشيت {comm:,.2f} ولا يوجد بند 18 في رواتب {pm}')})
        elif p is not None and abs(p - comm) > TOL:
            iss.append({'k': 'pay', 'sev': 'bad', 't': I(f'Payroll item 18 is {p:,.2f} vs sheet commission {comm:,.2f}', f'بند 18 في الرواتب {p:,.2f} مقابل نسبة الشيت {comm:,.2f}')})
        sev = 'bad' if any(i['sev'] == 'bad' for i in iss) else ('warn' if iss else 'ok')
        brs = max(c['br'], key=c['br'].get) if c['br'] else None
        rows.append({'c': code, 's': staff, 'n': str(S.cell(r, 3).value or '').strip(), 'cl': str(S.cell(r, 6).value or '').strip(),
                     'br': BR.get(str(S.cell(r, 7).value or '').strip(), str(S.cell(r, 7).value or '').strip()),
                     'ds': dsheet, 'dc': dcure, 'la': l['annual'], 'le': l['emerg'],
                     'cashS': round(cashS, 2), 'cashC': cashC, 'credS': round(credS, 2), 'credC': credC,
                     'med': round(c['med'], 2), 'comm': round(comm, 2), 'pay': p, 'st': sev, 'iss': iss, 'cure_br': c['br']})
    # Cure doctors with revenue that are not in the commission sheet, and branch rows the sheet ignores
    outside = []
    for s, c in cure.items():
        if s in seen: continue
        tot = c['cash'] + c['disc'] + c['cred']
        if abs(tot) > TOL: outside.append({'s': s, 'cash': round(c['cash'] + c['disc'], 2), 'cred': round(c['cred'], 2), 'med': round(c['med'], 2), 'br': c['br']})
    unm = []
    for rr in B.iter_rows(min_row=2, max_row=400, values_only=True):
        if rr[3] and str(rr[5]).strip() == 'لا':
            unm.append({'name': str(rr[0]).strip(), 'amt': round(f(rr[1]), 2), 'br': BR.get(str(rr[2]).strip(), str(rr[2]).strip()), 'type': rr[3]})
    miss = sum(u['amt'] for u in unm)
    # payroll item 18 with no sheet row
    pay_orphan = [{'s': s, 'v': v} for s, v in pay.items() if s not in seen]
    summ = {'doctors': len(rows), 'bad': sum(r['st'] == 'bad' for r in rows), 'warn': sum(r['st'] == 'warn' for r in rows),
            'ok': sum(r['st'] == 'ok' for r in rows),
            'sheet_total': round(sum(r['comm'] for r in rows), 2), 'paid_total': round(sum(pay.values()), 2),
            'rev_issues': sum(any(i['k'] == 'rev' for i in r['iss']) for r in rows),
            'days_issues': sum(any(i['k'] == 'days' for i in r['iss']) for r in rows),
            'pay_issues': sum(any(i['k'] == 'pay' for i in r['iss']) for r in rows),
            'unmatched_rows': len(unm), 'unmatched_amt': round(miss, 2), 'outside': len(outside), 'pay_orphan': len(pay_orphan)}
    doctors = []
    if a.rules:
        wf = openpyxl.load_workbook(a.sheet)
        doctors = doctor_basis(wf, a.rules)
        sm = {r['s']: r for r in rows}
        for d_ in doctors:
            r_ = sm.get(d_['s'])
            d_['cashS'] = r_['cashS'] if r_ else None; d_['credS'] = r_['credS'] if r_ else None
            d_['comm'] = r_['comm'] if r_ else None
        summ['basis'] = {k: sum(1 for d_ in doctors if d_['basis'] == k) for k in ('cash', 'cash_credit')}
        summ['basis_mismatch'] = sum(1 for d_ in doctors if d_['mismatch'])
        summ['no_rule'] = sum(1 for d_ in doctors if not d_['rule'])
    D = {'month': ym, 'paid': pm, 'dim': dim, 'summary': summ, 'rows': rows, 'doctors': doctors, 'outside': outside, 'unmatched': unm, 'payOrphan': pay_orphan,
         'src': {'rev': 'DOCTOR_COMMISSION_DATA (as in the doctor activity report RCDOCREP): cash = C + D, credit = R, pharmacy group 19 excluded, net of VAT',
                 'days': 'PS_STAFF_VACATIONS (annual leave, actual return date)', 'pay': 'PR_STAFF_ADDING_DEDUCTION item 18'}}
    json.dump(D, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False))
    if a.xlsx: write_xlsx(D, a.xlsx)


def write_xlsx(D, path):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    wb = Workbook(); ws = wb.active; ws.title = 'مراجعة النسب'; ws.sheet_view.rightToLeft = True
    H = PatternFill('solid', fgColor='1F4E78'); HF = Font(name='Arial', bold=True, color='FFFFFF')
    fills = {'bad': PatternFill('solid', fgColor='F8CBAD'), 'warn': PatternFill('solid', fgColor='FFE699'), 'ok': PatternFill('solid', fgColor='C6E0B4')}
    thin = Side(style='thin', color='BBBBBB'); bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    S = D['summary']
    ws['A1'] = f'مراجعة نسب الأطباء — {D["month"]} (تُصرف مع رواتب {D["paid"]})'; ws['A1'].font = Font(name='Arial', bold=True, size=14)
    ws['A2'] = f'الأطباء {S["doctors"]} | يحتاج إجراء {S["bad"]} | ملاحظة {S["warn"]} | سليم {S["ok"]} | إجمالي نسب الشيت {S["sheet_total"]:,.2f} | المصروف بند 18 {S["paid_total"]:,.2f}'
    hd = ['الكود', 'كود Cure', 'الطبيب', 'العيادة', 'الفرع', 'أيام الشيت', 'أيام Cure', 'كاش الشيت', 'كاش Cure', 'آجل الشيت', 'آجل Cure', 'فرق كاش', 'فرق آجل',
          'نسبة الشيت', 'بند 18 بالرواتب', 'الحالة', 'الملاحظات']
    for j, h in enumerate(hd, 1):
        c = ws.cell(4, j, h); c.fill = H; c.font = HF; c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = bd
    lab = {'bad': 'يحتاج إجراء', 'warn': 'ملاحظة', 'ok': 'سليم'}
    for i, r in enumerate(sorted(D['rows'], key=lambda x: ({'bad': 0, 'warn': 1, 'ok': 2}[x['st']], x['n'])), 5):
        vals = [r['c'], r['s'], r['n'], r['cl'], r['br'], r['ds'], r['dc'], r['cashS'], r['cashC'], r['credS'], r['credC'], None, None, r['comm'], r['pay'], lab[r['st']],
                ' | '.join(x['t']['ar'] for x in r['iss'])]
        for j, v in enumerate(vals, 1):
            c = ws.cell(i, j, v); c.font = Font(name='Arial', size=10); c.border = bd
        ws.cell(i, 12, f'=H{i}-I{i}'); ws.cell(i, 13, f'=J{i}-K{i}')
        for j in (8, 9, 10, 11, 12, 13, 14, 15): ws.cell(i, j).number_format = '#,##0.00;[Red]-#,##0.00'
        ws.cell(i, 16).fill = fills[r['st']]; ws.cell(i, 17).alignment = Alignment(wrap_text=True, vertical='top')
    for col, w in zip('ABCDEFGHIJKLMNOPQ', [8, 9, 24, 12, 9, 9, 9, 13, 13, 13, 13, 12, 12, 12, 14, 12, 80]): ws.column_dimensions[col].width = w
    ws.freeze_panes = 'D5'
    w2 = wb.create_sheet('صفوف بلا طبيب'); w2.sheet_view.rightToLeft = True
    for j, h in enumerate(['الاسم في بيانات الفروع', 'المبلغ', 'الفرع', 'النوع'], 1):
        c = w2.cell(1, j, h); c.fill = H; c.font = HF
    for i, u in enumerate(D['unmatched'], 2):
        for j, v in enumerate([u['name'], u['amt'], u['br'], u['type']], 1): w2.cell(i, j, v)
    w3 = wb.create_sheet('إيراد في Cure خارج الشيت'); w3.sheet_view.rightToLeft = True
    for j, h in enumerate(['كود Cure', 'كاش', 'آجل', 'أدوية (مستبعدة)', 'الفروع'], 1):
        c = w3.cell(1, j, h); c.fill = H; c.font = HF
    for i, u in enumerate(D['outside'], 2):
        for j, v in enumerate([u['s'], u['cash'], u['cred'], u['med'], ', '.join(u['br'])], 1): w3.cell(i, j, v)
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True); wb.save(path)


if __name__ == '__main__': main()
