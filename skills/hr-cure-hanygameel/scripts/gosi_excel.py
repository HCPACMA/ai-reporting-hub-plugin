#!/usr/bin/env python3
"""Excel deliverable for data/gosi_check.json (output of gosi_check.py).

    python3 scripts/gosi_excel.py --in data/gosi_check.json --out GOSI_Reconciliation_Sep2026.xlsx
"""
import argparse, json
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

FONT = 'Arial'
HEAD = PatternFill('solid', start_color='1F3A5F')
BAD = PatternFill('solid', start_color='FDE9E7')
WARN = PatternFill('solid', start_color='FFF4D6')
OKF = PatternFill('solid', start_color='E6F4EA')
thin = Side(style='thin', color='D0D5DD')
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
ST_AR = {'ok': 'مطابق', 'diff': 'فرق', 'note': 'ملاحظة', 'info': 'شهر جزئي', 'pending': 'بانتظار فاتورة', 'miss': 'غير موجود', 'na': '—', 'acc': 'مقبول (استثناء)'}


def sheet(wb, title, headers, rows, widths=None, first=False):
    ws = wb.active if first else wb.create_sheet()
    ws.title = title[:31]
    ws.sheet_view.rightToLeft = True
    ws.append(headers)
    for c in ws[1]:
        c.font = Font(name=FONT, bold=True, color='FFFFFF'); c.fill = HEAD
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True); c.border = BORDER
    ws.row_dimensions[1].height = 34
    for r in rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.font = Font(name=FONT, size=10); c.border = BORDER
            c.alignment = Alignment(vertical='top', wrap_text=isinstance(c.value, str) and len(c.value) > 30, horizontal='right' if isinstance(c.value, str) else 'center')
            if isinstance(c.value, float):
                c.number_format = '#,##0.00;-#,##0.00;-' if abs(c.value) % 1 else '#,##0;-#,##0;-'
    for i, w in enumerate(widths or [], 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = ws.dimensions
    return ws


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--in', dest='inp', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    d = json.load(open(a.inp, encoding='utf8')); S = d['summary']; rows = d['rows']
    wb = Workbook()
    # ---- summary
    ws = wb.active; ws.title = 'ملخص'; ws.sheet_view.rightToLeft = True
    lines = [
        ('مطابقة التأمينات الاجتماعية مع البرنامج والحسابات — الفيحاء — %s' % d['month'], None),
        ('', None),
        ('موظفون بمرتب مُرحَّل في البرنامج', S['paid']), ('منهم موجودون في ملفات التأمينات', S['in_gosi']), ('منهم سعوديون (عليهم خصم تأمينات)', S['saudi']),
        ('', None),
        ('1) الأساسي + السكن (برنامج مقابل تأمينات) — فروق تحتاج تعديل', S['c1_diff']),
        ('    فروق شكلية: التأمينات تضع البدلات ضمن الأساسي والراتب التأميني مطابق', S['c1_note']),
        ('2) الراتب التأميني في البرنامج مقابل (أساسي+سكن) في التأمينات — فروق', S['c2_diff']),
        ('3) إجمالي الراتب في التأمينات مقابل الحسابات — فروق تحتاج مراجعة', S['c3_diff']),
        ('    منها شهر جزئي (مُلتحقون جدد، متوقع)', S['c3_info']),
        ('4) خصم التأمينات على الموظف — فروق', S['c4_diff']),
        ('    بانتظار فاتورة سبتمبر (مشتركون جدد بلا معدل سابق)', S['c4_pending']),
        ('    إجمالي الخصم في البرنامج', S['ded_prog']), ('    إجمالي الخصم في الحسابات', S['ded_acct']), ('    إجمالي الخصم المتوقع من التأمينات (من له معدل)', S['ded_gosi_exp']),
        ('موظفون في البرنامج لهم راتب تأميني وغير موجودين في ملفات التأمينات', S['missing_gosi']),
        ('مسجلون في التأمينات وغير مصروف لهم راتب في البرنامج هذا الشهر', S['gosi_only']),
        ('مرحّل لهم راتب في البرنامج وغير موجودين في مسير الحسابات', S['not_in_acct']),
        ('', None),
        ('داخل وخارج المملكة: عدد من حالتهم خارج المملكة', S['out_total']), ('    منهم راتب مُرحَّل في البرنامج لموظف خارج المملكة', S['out_posted']),
        ('    منهم مصروف في مسير الحسابات', S['out_paid']), ('    مقيمون بلا سجل في تقرير السفر', S['nostatus']),
        ('', None),
        ('المصادر', None),
    ]
    for t, v in lines:
        ws.append([t, v])
    for p in d['sources']['accounts'] + d['sources']['gosi'] + ([d['sources']['travel']] if d['sources']['travel'] else []):
        ws.append(['    ' + p, None])
    ws.append(['    معدلات الخصم لكل شخص من فواتير التأمينات للشهر السابق (%d شخصاً)' % d['sources']['invoice_rates'], None])
    ws.append(['', None]); ws.append(['ملاحظة: لا توجد في ملفات التأمينات مبالغ مخصومة، لذلك المخصوم في التأمينات = المعدل في فاتورة الشهر السابق × الأجر الخاضع. المشتركون الجدد بلا معدل يُؤكَّدون من فاتورة سبتمبر.', None])
    ws.column_dimensions['A'].width = 95; ws.column_dimensions['B'].width = 14
    for r in ws.iter_rows():
        for c in r:
            c.font = Font(name=FONT, size=11, bold=(c.row == 1 or c.value in ('المصادر',))); c.alignment = Alignment(horizontal='right', wrap_text=True, vertical='top')
            if isinstance(c.value, (int, float)):
                c.alignment = Alignment(horizontal='center'); c.number_format = '#,##0'
    # ---- full comparison
    H = ['الكود', 'الاسم', 'رقم الهوية/الإقامة', 'الجنسية', 'ملف التأمينات', 'الأساسي (برنامج)', 'السكن (برنامج)', 'الراتب التأميني (برنامج)',
         'الأساسي (تأمينات)', 'السكن (تأمينات)', 'إجمالي الأجر (تأمينات)', 'إجمالي الراتب (حسابات)', 'الراتب الثابت (حسابات)',
         'فرق 1: أساسي+سكن', 'فرق 2: التأميني', 'فرق 3: الإجمالي', 'خصم البرنامج', 'خصم الحسابات', 'خصم التأمينات المتوقع',
         'نسبة البرنامج', 'نسبة الحسابات', 'نسبة التأمينات', 'نتيجة 1', 'نتيجة 2', 'نتيجة 3', 'نتيجة 4', 'المطلوب تعديله']
    out = []
    for r in rows:
        g = r['gosi'] or {}
        pr = lambda x: (x if x is not None else None)
        out.append([r['code'], r['name'], r['id'], 'سعودي' if r['saudi'] else 'غير سعودي', g.get('br', 'غير موجود'), r['pbasic'], r['phous'], r['psoc'],
                    g.get('basic'), g.get('hous'), g.get('total'), r['atotal'], r['afixed'], r.get('d1'), r.get('d2'), r.get('d3'), r['pded'], r['aded'], r['gexp'],
                    r['prate'], r['arate'], r['grate'], ST_AR[r['st'].get('c1', 'na')], ST_AR[r['st'].get('c2', 'na')], ST_AR[r['st'].get('c3', 'na')], ST_AR[r['st'].get('c4', 'na')],
                    ' | '.join(f['ar'] for f in r['fixes'] if f['k'] != 'c1note') or ''])
    ws = sheet(wb, 'المقارنة الشاملة', H, out, [8, 26, 13, 9, 18] + [11] * 14 + [9, 9, 9, 10, 10, 10, 10, 70])
    for row in ws.iter_rows(min_row=2):
        for c in row[19:22]:
            if isinstance(c.value, float):
                c.number_format = '0.00%'
        bad = any(row[i].value == 'فرق' for i in range(22, 26)) or row[26].value
        pend = any(row[i].value in ('بانتظار فاتورة',) for i in range(22, 26))
        if row[26].value:
            for c in row:
                c.fill = BAD
        elif pend:
            for c in row:
                c.fill = WARN
    # ---- corrections
    fx = []
    cname = {'nogosi': 'غير موجود في التأمينات', 'c1': '1) أساسي+سكن', 'c1note': '1) أساسي+سكن', 'c2zero': '2) الراتب التأميني', 'c2low': '2) الراتب التأميني', 'c2high': '2) الراتب التأميني',
             'c3low': '3) إجمالي الأجر', 'c3high': '3) إجمالي الأجر', 'c4non': '4) الخصم', 'c4pa': '4) الخصم', 'c4zero': '4) الخصم', 'c4rate': '4) الخصم', 'c4base': '4) الخصم', 'c4pend': '4) الخصم'}
    for r in rows:
        for f in r['fixes']:
            if f['k'] == 'c1note':
                continue
            fx.append([r['code'], r['name'], cname.get(f['k'], f['k']), f['ar'], f['en']])
    for g in d['gosi_only']:
        fx.append([g['code'] or '—', g['name'], 'مسجل في التأمينات فقط', g['fix']['ar'], g['fix']['en']])
    ws = sheet(wb, 'التصحيحات المطلوبة', ['الكود', 'الاسم', 'البند', 'المطلوب (عربي)', 'Action (English)'], fx, [9, 30, 24, 95, 95])
    # ---- GOSI only / not in accounts
    sheet(wb, 'مسجل في التأمينات فقط', ['رقم الهوية', 'الاسم', 'الملف', 'الأجر (أساسي+سكن)', 'إجمالي الأجر', 'الكود', 'حالة الراتب بالبرنامج', 'المطلوب'],
          [[g['id'], g['name'], g['br'], g['wage'], g['total'], g['code'] or '—', {'O': 'معلّق', 'P': 'مرحّل', None: 'غير نشط'}.get(g['status'], g['status']), g['fix']['ar']] for g in d['gosi_only']], [14, 32, 22, 14, 14, 8, 14, 90])
    sheet(wb, 'مرحّل بالبرنامج وليس بالحسابات', ['الكود', 'الاسم', 'إجمالي الراتب المرحّل'], [[n['code'], n['name'], n['pgross']] for n in d['not_in_acct']], [10, 34, 18])
    # ---- travel
    tr = []
    vt = {'posted': 'راتب مُرحَّل في البرنامج وغير موجود بمسير الحسابات — يُوقف/يُعكس', 'paid': 'مصروف في الحسابات — مخالفة', 'ok': 'لا راتب — سليم'}
    for t in d['travel']:
        if not t['out']:
            continue
        tr.append([t['code'] or '—', t['name'] or t['tname'], t['id'], t['nat'], {'P': 'مرحّل', 'O': 'معلّق', None: 'غير نشط'}.get(t['pst'], t['pst']), t['pay'], 'نعم' if t['inacct'] else 'لا',
                   t.get('octpay') if t.get('octpay') is not None else None, vt.get(t['verdict'], ''), 'مسودة أكتوبر بها راتب — يُوقف قبل الترحيل' if t.get('oct_risk') else ''])
    sheet(wb, 'خارج المملكة', ['الكود', 'الاسم', 'رقم الإقامة', 'الجنسية', 'راتب الشهر بالبرنامج', 'المبلغ', 'في مسير الحسابات', 'مسودة الشهر القادم', 'النتيجة', 'تنبيه'], tr, [8, 34, 14, 12, 14, 12, 12, 14, 60, 50])
    sheet(wb, 'بلا سجل سفر', ['الكود', 'الاسم', 'رقم الإقامة', 'راتب الشهر', 'في مسير الحسابات'], [[n['code'], n['name'], n['id'], n['pay'], 'نعم' if n['inacct'] else 'لا'] for n in d['nostatus']], [8, 34, 14, 14, 14])
    wb.save(a.out)
    print('saved', a.out)


if __name__ == '__main__':
    main()
