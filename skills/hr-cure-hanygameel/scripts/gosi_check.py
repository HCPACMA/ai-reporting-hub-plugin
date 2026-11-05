#!/usr/bin/env python3
"""GOSI reconciliation + in/out-of-Kingdom check for one month (Al Faihaa layout).

    python3 scripts/gosi_check.py --root <payroll year folder> --month 2026-09 \
        --cure raw/hr18a_gosi_payroll.txt raw/hr18b_gosi_payroll.txt --names raw/hr19_names.txt \
        --oct raw/hr20_draft_next.txt --out data/gosi_check.json

--root is the folder that holds the month sub-folders ("09 Sep 2026" ...). Inputs found inside the month folder:
  accounts payroll    "مسير شركة الفيحاء عن شهر ... .xls" (+ cash payroll "رواتب الكاش ... الفيحاء .xls")
  GOSI wage files     "التأمينات الإجتماعية/شركة *الفيحاء*.csv" and "فرع *.csv" (CONTRIBUTOR NAME, IDENTIFIER, BASIC WAGE, HOUSING, COMMISSION, OTHER ALLOWANCE)
  GOSI invoice        "التأمينات الإجتماعية/الفواتير التفصيلية/*اغسطس*.xlsx" of the PREVIOUS month (employee rate per person, sheet الاشتراكات)
  travel status       "داخل وخارج المملكة/الفيحاء *.xlsx" (رقم الاقامة, الاسم, الجنسية, خارج المملكة)
Cure input (raw replies of sql/hr18*.sql): lines  staff|id_no|nationality|basic|social_salary|si_staff|si_company|housing|adds|status
The four comparisons (per employee code):
  C1 basic + housing in program vs GOSI        C2 insurance salary in program vs GOSI basic + housing
  C3 accounts total pay vs GOSI total wage     C4 employee GOSI deduction: program vs accounts vs GOSI (rate x wage)
"""
import argparse, csv, glob, json, os, re, shutil, subprocess, sys, tempfile, unicodedata
import openpyxl

TOL = 1.0
CAP = 45000.0           # GOSI contribution wage ceiling
PIPE = re.compile(r'(\d{3,6})\|(\d*)\|(\d*)\|(-?[\d.]+)\|(-?[\d.]+)\|(-?[\d.]*)\|(-?[\d.]*)\|(-?[\d.]+)\|(-?[\d.]+)\|([POC])')


def num(x):
    try:
        return float(str(x).replace(',', '').strip() or 0)
    except Exception:
        return 0.0


def nz(s):
    return ' '.join(unicodedata.normalize('NFKC', str(s or '')).split())


def read_cure(files):
    d = {}
    for f in files:
        for line in open(f, encoding='utf8'):
            m = PIPE.search(line)
            if not m:
                continue
            g = m.groups()
            d[g[0]] = dict(stf=g[0], id=g[1], nat=g[2], basic=num(g[3]), soc=num(g[4]), si_st=num(g[5]), si_co=num(g[6]),
                           hous=num(g[7]), adds=num(g[8]), status=g[9])
    return d


def read_names(f):
    d = {}
    if f and os.path.exists(f):
        for line in open(f, encoding='utf8'):
            m = re.search(r'(\d{3,6})\|([^|]+)\|?', line)
            if m:
                d[m.group(1)] = nz(m.group(2))
    return d


def xls_to_xlsx(path, tmp):
    try:
        import xlrd  # noqa
        wb = xlrd.open_workbook(path)
        out = openpyxl.Workbook(); out.remove(out.active)
        for s in wb.sheets():
            ws = out.create_sheet(s.name[:30])
            for i in range(s.nrows):
                ws.append(s.row_values(i))
        p = os.path.join(tmp, os.path.basename(path) + '.xlsx'); out.save(p); return p
    except ImportError:
        subprocess.run(['soffice', '--headless', '--convert-to', 'xlsx', '--outdir', tmp, path], check=True, capture_output=True, timeout=180)
        return os.path.join(tmp, os.path.splitext(os.path.basename(path))[0] + '.xlsx')


def read_accounts(files, tmp):
    out = {}
    for path, kind in files:
        wb = openpyxl.load_workbook(xls_to_xlsx(path, tmp), data_only=True)
        ws = wb.worksheets[0]; rows = list(ws.iter_rows(values_only=True))
        hi = next(i for i, r in enumerate(rows) if r and str(r[0]).strip() == 'رقم الموظف')
        h = [nz(x) for x in rows[hi]]
        for r in rows[hi + 1:]:
            c = str(r[0]).strip() if r and r[0] is not None else ''
            if not c.isdigit():
                continue
            rec = {h[i]: r[i] for i in range(len(h))}; rec['src'] = kind
            out.setdefault(c, rec)
    return out


def gosi_files(gdir):
    G = {}
    for f in sorted(os.listdir(gdir)):
        if not f.lower().endswith('.csv') or 'منازلنا' in f:
            continue
        n = ' '.join(f.split())
        br = ('فرع الرياض' if 'الرياض' in n else 'فرع رفحاء' if 'رفحاء' in n else 'فرع بريدة 1' if '1 بريدة' in n
              else 'فرع بريدة 2' if '2 بريدة' in n else 'شركة الفيحاء (المركز)')
        for r in csv.DictReader(open(os.path.join(gdir, f), encoding='utf-8-sig')):
            i = r['IDENTIFIER'].strip()
            G[i] = dict(name=nz(r['CONTRIBUTOR NAME']), basic=num(r['BASIC WAGE']), hous=num(r['HOUSING']), comm=num(r['COMMISSION']),
                        oth=num(r['OTHER ALLOWANCE']), br=br, file=f)
    return G


def invoice_rates(idir):
    out = {}
    if not os.path.isdir(idir):
        return out
    for f in sorted(os.listdir(idir)):
        if 'منازلنا' in f or not f.endswith('.xlsx') or f.startswith('~'):
            continue
        wb = openpyxl.load_workbook(os.path.join(idir, f), read_only=True, data_only=True)
        if 'الاشتراكات' not in wb.sheetnames:
            continue
        for r in wb['الاشتراكات'].iter_rows(values_only=True):
            if r and len(r) > 31 and r[23] and str(r[23]).strip().isdigit() and r[31] not in (None, ''):
                out[str(r[23]).strip()] = dict(wage=num(r[29]), ded=num(r[30]), rate=round(num(r[31]), 4))
            elif r and len(r) > 25 and r[23] and str(r[23]).strip().isdigit() and isinstance(r[16], (int, float)) and r[16]:
                # 30-column layout (from Sept-2026 invoices): employee share = cols 10-14, wage = col 16
                ded = sum(num(r[i]) for i in (10, 11, 12, 13, 14) if isinstance(r[i], (int, float)))
                out[str(r[23]).strip()] = dict(wage=num(r[16]), ded=ded, rate=round(ded / num(r[16]), 4))
    return out


def fmt(x):
    return f'{x:,.0f}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True); ap.add_argument('--month', required=True)
    ap.add_argument('--cure', nargs='+', required=True); ap.add_argument('--names'); ap.add_argument('--oct', help='raw reply of the next (draft) month rows: staff|YYYYMM|status|basic')
    ap.add_argument('--sep-start', default='4409-4466', help='staff-number range of employees who joined during the month (prorated pay)')
    ap.add_argument('--exceptions', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'gosi_exceptions.json'))
    ap.add_argument('--cc', nargs='*', default=[], help='cost-centre files org|staff'); ap.add_argument('--cc-config', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'prepay_exceptions.json'))
    ap.add_argument('--out', required=True); ap.add_argument('--names-out', help='write the code to name map used (accounts payroll names plus the Cure names file)')
    a = ap.parse_args()
    CCOF = {}
    for f in a.cc:
        for l in open(f, encoding='utf8'):
            if '|' in l: o, c = l.strip().split('|')[:2]; CCOF[c] = o
    CCX = json.load(open(a.cc_config, encoding='utf8')).get('_cost_centre_exempt', {}).get('gosi') if os.path.exists(a.cc_config) else None
    EXC = {k: v for k, v in (json.load(open(a.exceptions, encoding='utf8')) if os.path.exists(a.exceptions) else {}).items() if not k.startswith('_')}
    y, m = [int(x) for x in a.month.split('-')]
    mdir = next(os.path.join(a.root, d) for d in os.listdir(a.root) if d.startswith(f'{m:02d} '))
    gdir = os.path.join(mdir, 'التأمينات الإجتماعية')
    pm = m - 1 or 12
    pdir = next((os.path.join(a.root, d) for d in os.listdir(a.root) if d.startswith(f'{pm:02d} ')), None)
    idir = next((d for d in (os.path.join(gdir, 'الفواتير التفصيلية'), os.path.join(mdir, 'الفواتير التفصيلية')) if os.path.isdir(d)), os.path.join(gdir, 'الفواتير التفصيلية'))
    cure = read_cure(a.cure); names = read_names(a.names)
    tmp = tempfile.mkdtemp()
    accf = []
    for f in os.listdir(mdir):
        if f.endswith('.xls') and f.startswith('مسير شركة الفيحاء'):
            accf.append((os.path.join(mdir, f), 'payroll'))
        elif f.endswith('.xls') and f.startswith('رواتب الكاش') and 'الفيحاء' in f:
            accf.append((os.path.join(mdir, f), 'cash'))
    acct = read_accounts(accf, tmp)
    for k, v in acct.items():
        n = nz(v.get('اسم الموظف') or v.get('اسم الموظف2'))
        if n:
            names.setdefault(k, n)
    G = gosi_files(gdir); rates = invoice_rates(idir)
    lo, hi = [int(x) for x in a.sep_start.split('-')]
    ids = {v['id']: k for k, v in cure.items() if v['id']}
    rows = []
    for k in sorted(cure):
        p = cure[k]
        if p['status'] != 'P':
            continue
        g = G.get(p['id']); ac = acct.get(k); sa = p['nat'] == '420'
        r = dict(code=k, name=names.get(k, ''), id=p['id'], saudi=sa, nat=p['nat'],
                 pbasic=p['basic'], phous=p['hous'], psoc=p['soc'], pded=p['si_st'], pco=p['si_co'], pgross=p['basic'] + p['adds'],
                 atotal=None, afixed=None, aded=None, asrc=None, gosi=None)
        if ac:
            tot = num(ac.get('إجمالي الرواتب')); ot = num(ac.get('الإضافي')); once = num(ac.get('استحقاقات مرة واحدة')); doc = num(ac.get('نسبة الاطباء'))
            r.update(atotal=tot, afixed=tot - ot - once - doc, aded=num(ac.get('تأمينات')), asrc=ac['src'], aot=ot)
        pb = p['basic'] + p['hous']
        prorated = bool(sa and lo <= int(k) <= hi and p['soc'] > 0 and 0 < pb < p['soc'] * 0.95)
        r['prorated'] = prorated; ratio = pb / p['soc'] if prorated else 1.0; r['ratio'] = round(ratio, 4)
        if g:
            gbh = g['basic'] + g['hous']; gt = gbh + g['comm'] + g['oth']
            r['gosi'] = dict(br=g['br'], basic=g['basic'], hous=g['hous'], comm=g['comm'], oth=g['oth'], total=gt, bh=gbh, name=g['name'])
        fixes = []; st = {}
        # ---- C1 and C2
        if not g:
            st['c1'] = st['c2'] = st['c3'] = 'miss'
            if p['soc'] > 0 or p['si_co'] > 0:
                fixes.append(dict(k='nogosi', en='Insurance salary %s in the program but the employee is not in the GOSI wage files: register in GOSI or fix the program' % fmt(p['soc']),
                                  ar='له راتب تأميني %s في البرنامج ولا يظهر في ملفات التأمينات: يُسجَّل في التأمينات أو يُصحَّح البرنامج' % fmt(p['soc'])))
            else:
                st['c1'] = st['c2'] = st['c3'] = 'na'
        else:
            gbh = r['gosi']['bh']; ref = p['soc'] if prorated else pb
            d1 = round(ref - gbh, 2)
            st['c1'] = 'ok' if abs(d1) <= TOL else 'diff'
            d2 = round(p['soc'] - gbh, 2)
            st['c2'] = 'ok' if abs(d2) <= TOL else 'diff'
            r['d1'] = d1; r['d2'] = d2
            if st['c1'] == 'diff' and st['c2'] == 'ok':
                st['c1'] = 'note'
                fixes.append(dict(k='c1note', en='Basic+housing differ (%s in program, %s in GOSI) but the insurance salary matches: GOSI holds allowances inside "basic". No action' % (fmt(ref), fmt(gbh)),
                                  ar='الأساسي+السكن يختلفان (%s برنامج، %s تأمينات) لكن الراتب التأميني مطابق: التأمينات تضع البدلات ضمن الأساسي. لا إجراء' % (fmt(ref), fmt(gbh))))
                r['fix_level'] = 0
            if st['c2'] == 'diff':
                if p['soc'] == 0 and sa:
                    fixes.append(dict(k='c2zero', en='Saudi registered in GOSI at %s but the program insurance salary is 0 and nothing is deducted: set the insurance salary and start the deduction' % fmt(gbh),
                                      ar='سعودي مسجل في التأمينات بأجر %s بينما الراتب التأميني في البرنامج صفر ولا يُخصم شيء: يُضبط الراتب التأميني ويبدأ الخصم' % fmt(gbh)))
                elif p['soc'] < gbh:
                    fixes.append(dict(k='c2low', en='Program insurance salary %s is below GOSI basic+housing %s (diff %s): raise the program insurance salary%s' % (fmt(p['soc']), fmt(gbh), fmt(gbh - p['soc']), ' and the deduction' if sa else ''),
                                      ar='الراتب التأميني في البرنامج %s أقل من أساسي+سكن التأمينات %s (فرق %s): يُرفع الراتب التأميني في البرنامج%s' % (fmt(p['soc']), fmt(gbh), fmt(gbh - p['soc']), ' والخصم' if sa else '')))
                else:
                    fixes.append(dict(k='c2high', en='Program insurance salary %s is above GOSI basic+housing %s (diff %s): update the wage in GOSI to %s' % (fmt(p['soc']), fmt(gbh), fmt(p['soc'] - gbh), fmt(p['soc'])),
                                      ar='الراتب التأميني في البرنامج %s أعلى من أساسي+سكن التأمينات %s (فرق %s): يُحدَّث الأجر في التأمينات إلى %s' % (fmt(p['soc']), fmt(gbh), fmt(p['soc'] - gbh), fmt(p['soc']))))
            elif st['c1'] == 'diff':
                fixes.append(dict(k='c1', en='Basic+housing %s in program vs %s in GOSI' % (fmt(ref), fmt(gbh)), ar='الأساسي+السكن %s في البرنامج مقابل %s في التأمينات' % (fmt(ref), fmt(gbh))))
            # ---- C3
            if r['atotal'] is None:
                st['c3'] = 'miss'
            else:
                d3 = round(r['afixed'] - r['gosi']['total'], 2); r['d3'] = d3
                if abs(d3) <= TOL:
                    st['c3'] = 'ok'
                elif prorated:
                    st['c3'] = 'info'
                else:
                    st['c3'] = 'diff'
                    if d3 > 0:
                        fixes.append(dict(k='c3low', en='GOSI total wage %s is below the monthly fixed pay in accounts %s (diff %s): update GOSI or confirm the extra is a non-subject allowance' % (fmt(r['gosi']['total']), fmt(r['afixed']), fmt(d3)),
                                          ar='إجمالي الأجر في التأمينات %s أقل من الراتب الثابت في الحسابات %s (فرق %s): يُحدَّث الأجر في التأمينات أو يُؤكَّد أن الفرق بدل غير خاضع' % (fmt(r['gosi']['total']), fmt(r['afixed']), fmt(d3))))
                    else:
                        fixes.append(dict(k='c3high', en='GOSI total wage %s is above the monthly fixed pay in accounts %s (diff %s): lower the GOSI wage or check the pay' % (fmt(r['gosi']['total']), fmt(r['afixed']), fmt(-d3)),
                                          ar='إجمالي الأجر في التأمينات %s أعلى من الراتب الثابت في الحسابات %s (فرق %s): يُخفَّض الأجر في التأمينات أو يُراجع الراتب' % (fmt(r['gosi']['total']), fmt(r['afixed']), fmt(-d3))))
        # ---- C4 (employee share, Saudis only)
        gw = min(r['gosi']['bh'], CAP) if g else 0.0
        inv = rates.get(p['id']); grate = inv['rate'] if inv else None
        r['grate'] = grate; r['gwage'] = gw
        r['prate'] = round(p['si_st'] / p['soc'], 4) if p['soc'] else 0.0
        r['arate'] = round(r['aded'] / (gw * ratio), 4) if (r['aded'] and gw) else (0.0 if r['aded'] is not None else None)
        r['gexp'] = None
        if not sa:
            st['c4'] = 'ok' if p['si_st'] == 0 and not r['aded'] else 'diff'
            if st['c4'] == 'diff':
                fixes.append(dict(k='c4non', en='Non-Saudi with a GOSI employee deduction %s: remove' % fmt(max(p['si_st'], r['aded'] or 0)), ar='غير سعودي وعليه خصم تأمينات %s: يُلغى' % fmt(max(p['si_st'], r['aded'] or 0))))
        else:
            if gw > 0 and grate is not None:
                r['gexp'] = round(gw * grate * ratio)
            if r['aded'] is not None and abs(p['si_st'] - r['aded']) > TOL:
                st['c4'] = 'diff'
                fixes.append(dict(k='c4pa', en='Deduction differs between program %s and accounts %s' % (fmt(p['si_st']), fmt(r['aded'])), ar='الخصم يختلف بين البرنامج %s والحسابات %s' % (fmt(p['si_st']), fmt(r['aded']))))
            elif r['gexp'] is not None and abs(p['si_st'] - r['gexp']) > TOL:
                st['c4'] = 'diff'
                diff = r['gexp'] - p['si_st']
                if p['soc'] == 0:
                    fixes.append(dict(k='c4zero', en='No deduction taken; GOSI expects %s (rate %.2f%% on %s)' % (fmt(r['gexp']), grate * 100, fmt(gw)),
                                      ar='لم يُخصم شيء والتأمينات تتوقع %s (نسبة %.2f%% على %s)' % (fmt(r['gexp']), grate * 100, fmt(gw))))
                elif abs(r['prate'] - grate) > 0.0005 and abs(p['soc'] - gw) <= TOL:
                    fixes.append(dict(k='c4rate', en='Program deducts %.2f%% (%s) but GOSI bills %.2f%% (%s): %s %s a month; set the rate to %.2f%%' % (r['prate'] * 100, fmt(p['si_st']), grate * 100, fmt(r['gexp']), 'under-deducted by' if diff > 0 else 'over-deducted by', fmt(abs(diff)), grate * 100),
                                      ar='البرنامج يخصم %.2f%% (%s) والتأمينات تفوتر %.2f%% (%s): %s %s شهرياً؛ يُضبط المعدل إلى %.2f%%' % (r['prate'] * 100, fmt(p['si_st']), grate * 100, fmt(r['gexp']), 'نقص في الخصم' if diff > 0 else 'زيادة في الخصم', fmt(abs(diff)), grate * 100)))
                else:
                    fixes.append(dict(k='c4base', en='Deduction %s vs GOSI-expected %s: the deduction base differs (program insurance salary %s, GOSI wage %s)' % (fmt(p['si_st']), fmt(r['gexp']), fmt(p['soc']), fmt(gw)),
                                      ar='الخصم %s مقابل المتوقع من التأمينات %s: أساس الخصم مختلف (التأميني في البرنامج %s، أجر التأمينات %s)' % (fmt(p['si_st']), fmt(r['gexp']), fmt(p['soc']), fmt(gw))))
            elif grate is None and gw > 0:
                st['c4'] = 'pending'
                fixes.append(dict(k='c4pend', en='New subscriber: no rate in last invoice. Program takes %.2f%% (%s); confirm against the next GOSI invoice' % (r['prate'] * 100 / max(ratio, 0.01), fmt(p['si_st'])),
                                  ar='مشترك جديد: لا يوجد معدل في آخر فاتورة. البرنامج يخصم %.2f%% (%s)؛ يُؤكَّد من فاتورة التأمينات القادمة' % (r['prate'] * 100 / max(ratio, 0.01), fmt(p['si_st']))))
            else:
                st['c4'] = 'ok' if (gw > 0 or p['si_st'] == 0) else 'na'
        ex = EXC.get(p['id']) or EXC.get(r['code'])
        if CCX and not g and any(CCOF.get(r['code'], '').startswith(pf) for pf in CCX['prefixes']):
            r['exc'] = dict(ar=CCX['ar'], en=CCX['en']); ex = None
            fixes = [f for f in fixes if f['k'] != 'nogosi']
        if ex:
            hit = False
            for c in ex['checks']:
                if st.get(c) in ('diff', 'pending', 'note', 'info'):
                    st[c] = 'acc'; hit = True
                    fixes = [f for f in fixes if not f['k'].startswith(c) and not (c == 'c1' and f['k'] == 'c1note')]
            for f in fixes:
                if f['k'] in ex:
                    f['ar'], f['en'] = ex[f['k']]['ar'], ex[f['k']]['en']
            if hit:
                r['exc'] = dict(ar=ex['ar'], en=ex['en'])
        r['st'] = st; r['fixes'] = fixes
        r['bad'] = any(f['k'] not in ('c1note',) and not f['k'].startswith('c4pend') for f in fixes) or any(v in ('diff',) for v in st.values())
        rows.append(r)
    paid_ids = {r['id'] for r in rows}
    gosi_only = []
    for i, g in sorted(G.items(), key=lambda t: t[1]['name']):
        if i in paid_ids:
            continue
        k = ids.get(i)
        gosi_only.append(dict(id=i, name=g['name'], br=g['br'], wage=g['basic'] + g['hous'], total=g['basic'] + g['hous'] + g['comm'] + g['oth'], code=k, status=cure[k]['status'] if k else None))
    for go in gosi_only:
        if go['code'] and go['status'] != 'P':
            go['kind'] = 'held'
            go['fix'] = dict(en='September salary is held (not paid) in the program but the employee is still in the GOSI file at %s: confirm whether on leave abroad (no action) or left (cancel the subscription)' % fmt(go['wage']),
                             ar='راتب سبتمبر معلّق (غير مصروف) في البرنامج وما زال في ملف التأمينات بأجر %s: يُؤكَّد هل هو في إجازة خارج المملكة (لا إجراء) أم ترك العمل (يُلغى الاشتراك)' % fmt(go['wage']))
        else:
            go['kind'] = 'inactive'
            go['fix'] = dict(en='Not an active employee in the program but still in the GOSI file at %s: report the leaver to GOSI and cancel the subscription' % fmt(go['wage']),
                             ar='غير نشط في البرنامج وما زال في ملف التأمينات بأجر %s: يُبلَّغ عن ترك العمل ويُلغى الاشتراك' % fmt(go['wage']))
    # ---- program vs accounts presence
    not_in_acct = [dict(code=k, name=names.get(k, ''), pgross=cure[k]['basic'] + cure[k]['adds']) for k in sorted(cure) if cure[k]['status'] == 'P' and k not in acct and cure[k]['basic'] > 0]
    # ---- travel
    travel = []
    tf = next((os.path.join(mdir, 'داخل وخارج المملكة', f) for f in sorted(os.listdir(os.path.join(mdir, 'داخل وخارج المملكة'))) if f.endswith('.xlsx') and not f.startswith('~') and 'منازلنا' not in f and (f.startswith('الفيحاء') or 'حالة السفر' in f)), None)
    octm = {}
    if a.oct and os.path.exists(a.oct):
        for line in open(a.oct, encoding='utf8'):
            mm = re.search(r'(\d{3,6})\|(\d{6})\|([POC])\|(-?[\d.]+)', line)
            if mm and mm.group(2) == f'{y + (m == 12)}{(m % 12) + 1:02d}':
                octm[mm.group(1)] = dict(status=mm.group(3), basic=num(mm.group(4)))
    seen = set()
    if tf:
        ws = openpyxl.load_workbook(tf, data_only=True).worksheets[0]
        for r in list(ws.iter_rows(values_only=True))[1:]:
            if not r[0]:
                continue
            i = str(r[0]).strip(); out = nz(r[3]) == 'نعم'; k = ids.get(i); seen.add(i)
            rec = dict(id=i, tname=nz(r[1]), nat=nz(r[2]), out=out, code=k, name=names.get(k, '') if k else '')
            if k:
                pr = cure[k]
                rec.update(pst=pr['status'], pay=pr['basic'] + pr['adds'] if pr['status'] == 'P' else 0.0, inacct=k in acct,
                           anet=num(acct[k].get('الصافي')) if k in acct else 0.0, octst=octm.get(k, {}).get('status'), octpay=octm.get(k, {}).get('basic'))
            else:
                rec.update(pst=None, pay=0.0, inacct=False, anet=0.0, note='inactive')
            if out:
                if k and rec['pay'] > 0 and not rec['inacct']:
                    rec['verdict'] = 'posted'
                elif k and rec['inacct'] and rec['anet'] > 0:
                    rec['verdict'] = 'paid'
                else:
                    rec['verdict'] = 'ok'
                if rec.get('octpay'):
                    rec['oct_risk'] = True
            travel.append(rec)
    nostatus = [dict(code=k, name=names.get(k, ''), id=cure[k]['id'], pay=cure[k]['basic'] + cure[k]['adds'], inacct=k in acct)
                for k in sorted(cure) if cure[k]['status'] == 'P' and cure[k]['nat'] != '420' and cure[k]['id'] and cure[k]['id'] not in seen]
    # ---- summary
    def cnt(c, v):
        return sum(1 for r in rows if r['st'].get(c) == v)
    summ = dict(paid=len(rows), in_gosi=sum(1 for r in rows if r['gosi']), saudi=sum(1 for r in rows if r['saudi']),
                c1_diff=cnt('c1', 'diff'), c1_note=cnt('c1', 'note'), c2_diff=cnt('c2', 'diff'), c3_diff=cnt('c3', 'diff'), c3_info=cnt('c3', 'info'),
                c4_diff=cnt('c4', 'diff'), c4_pending=cnt('c4', 'pending'), missing_gosi=sum(1 for r in rows if r['st'].get('c1') == 'miss' and any(f['k'] == 'nogosi' for f in r['fixes'])),
                gosi_only=len(gosi_only), bad=sum(1 for r in rows if r['bad']),
                ded_prog=sum(r['pded'] for r in rows), ded_acct=sum((r['aded'] or 0) for r in rows),
                ded_gosi_exp=sum((r['gexp'] or 0) for r in rows), out_total=sum(1 for t in travel if t['out']),
                out_posted=sum(1 for t in travel if t.get('verdict') == 'posted'), out_paid=sum(1 for t in travel if t.get('verdict') == 'paid'),
                nostatus=len(nostatus), not_in_acct=len(not_in_acct))
    rel = lambda p: os.path.relpath(p, a.root).replace(os.sep, '/')
    res = dict(month=a.month, summary=summ, rows=rows, gosi_only=gosi_only, not_in_acct=not_in_acct, travel=travel, nostatus=nostatus,
               sources=dict(accounts=[rel(p) for p, _ in accf], gosi=sorted({rel(os.path.join(gdir, g['file'])) for g in G.values()}), invoice_rates=len(rates), travel=rel(tf) if tf else None))
    json.dump(res, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    if a.names_out:
        json.dump(names, open(a.names_out, 'w', encoding='utf8'), ensure_ascii=False, indent=0, sort_keys=True)
    print(json.dumps(summ, ensure_ascii=False))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
