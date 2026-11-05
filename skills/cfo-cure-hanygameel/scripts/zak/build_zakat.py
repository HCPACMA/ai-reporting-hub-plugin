# -*- coding: utf-8 -*-
"""DATA.zak — Zakat under the Implementing Regulation for Zakat Collection 1445H
(Minister of Finance resolution 1007 of 19/08/1445H, amended by 1248 of 11/10/1446H),
which applies to financial years starting on or after 1 January 2024.

Source: the four EXSYS ledgers only (gl/y_*.txt: annual movements by account, posted + open
vouchers, cancelled and closing vouchers excluded), gl/accounts.json (parents),
gl/acc_names.json, drv/gl_all.json (monthly, for the open year), DATA.ext (net income and
retained earnings rebuilt from the same ledger). Nothing is typed in.
Classification of expenses into the return's categories: zak/exp_class.json (the owner's
2025 classification workbook, account -> category, cost of revenue vs G&A).
"""
import json, re, collections, datetime as dt, os, sys
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
P = lambda *a: os.path.join(ROOT, *a)
ACC = json.load(open(P('gl/accounts.json'))); NM = json.load(open(P('gl/acc_names.json')))
par = lambda a: ACC.get(a, ('-', '?'))[0]
H = open(P('AlFaihaa_Modeling_Desk.html'), encoding='utf-8').read()
E = json.loads(re.search(r'\nDATA\.ext = (.*);\n', H).group(1))
CLS = json.load(open(P('zak/exp_class.json')))

R = []
for f in ['y_riy.txt', 'y_bur1.txt', 'y_bur2.txt', 'y_rafha.txt']:
    for l in open(P('gl', f)):
        l = l.strip()
        if l:
            y, a, fn, fl, v = l.split('|')
            if fl == 'N': R.append((int(y), a, fn, float(v)))
mov = collections.defaultdict(lambda: collections.defaultdict(float))     # a -> y -> movement (DR+)
pl = collections.defaultdict(lambda: collections.defaultdict(float))      # (a, fn) -> y -> movement
for y, a, fn, v in R:
    mov[a][y] += v
    if a[0] in '34': pl[(a, fn)][y] += v
bal = lambda a, Y: sum(v for y, v in mov[a].items() if y <= Y)           # closing balance, DR+

# as-of: the ledger's last day read (the drivers payload carries it)
DRV = json.loads(re.search(r'\nDATA\.drv = (.*);\n', H).group(1))
ASOF = dt.date.fromisoformat(DRV['asOf'])
YEARS = [y for y in (2024, 2025, 2026) if y <= ASOF.year]
OPENY = ASOF.year
def days(y):
    return (dt.date(y, 12, 31) - dt.date(y, 1, 1)).days + 1
RATE = lambda d: 0.025 / 354 * d                                            # Art. 15(2)

# journal lines read from the ledgers for zakat (zak/lines.json, refresh job zak_lines): 3280005, 2123003, 2111004
# and every expense line whose description names a violation or fine
LN = [r for r in json.load(open(P('zak/lines.json'))) if r[2] != 'JV1-24/04043']
FINE = re.compile('مخالف|غرامة|غرامات')
NOTFINE = re.compile('ترافع|اتعاب|أتعاب|محامي|استعلام|تعويض|ديوان|عمولة|رسوم تحويل')
def cur_charge(Y):   # the year's own zakat charge: the year-end provision entry for that year
    return sum(r[5] for r in LN if r[3] == '3280005' and r[1][:4] == str(Y) and 'اثبات مصروف مخصص الزكاة' in r[6])
def fines(Y):        # government fines and violations: not an accepted expense (owner's rule; Art. 62)
    return [r for r in LN if r[3].startswith('314') and r[1][:4] == str(Y) and FINE.search(r[6]) and not NOTFINE.search(r[6])]
def fine_review(Y):  # lines that mention a violation but are fees, lawyers or compensation: accepted, shown for review
    return [r for r in LN if r[3].startswith('314') and r[1][:4] == str(Y) and FINE.search(r[6]) and NOTFINE.search(r[6])]

def nm(a): return NM.get(a, a)
def ext(key, grp, y):
    i = E['years'].index(y); return E[grp][key][i]

def year(Y):
    accs = [a for a in mov if a[0] in '12' and abs(bal(a, Y)) >= 0.005]
    B = {a: bal(a, Y) for a in accs}
    L = lambda pred: [(a, B[a]) for a in sorted(accs) if pred(a)]
    cr = lambda v: -v
    o = {'y': Y, 'days': days(Y), 'open': Y == OPENY}
    # ---------------------------------------------------------------- equity and items treated as equity
    eq = []
    for a, v in L(lambda a: par(a) == '2210000'): eq.append(['cap', a, nm(a), cr(v), '23(1)'])
    for a, v in L(lambda a: par(a) == '2230000'): eq.append(['res', a, nm(a), cr(v), '23(1)'])
    cc = cur_charge(Y)
    re_ = ext('retained_earnings', 'bs', Y) + cc          # retained earnings incl. the year's profit BEFORE the year's zakat
    eq.append(['re', '2220001+P&L', 'الأرباح المبقاة شاملة صافي ربح العام قبل الزكاة', re_, '23(1), 38'])
    for a, v in L(lambda a: par(a) == '2240000'): eq.append(['oci', a, nm(a), cr(v), '38'])
    # Art. 24: provisions (except end-of-service and leave) are equity, closing balance
    for a, v in L(lambda a: par(a) == '2111000' and a not in ('2111001', '2111002', '2111003')):
        if cr(v) > 0: eq.append(['prov', a, nm(a), cr(v), '24'])
    # zakat provision: the year's own charge is already inside retained earnings (profit before zakat);
    # only an unpaid balance for earlier years is added (Art. 24). A debit remainder is a refund due (not deducted).
    zp = -bal('2123003', Y)
    o['zakProv'] = {'close': zp, 'current': cc, 'prior': zp - cc}
    if zp - cc > 0.5: eq.append(['prov', '2123003', 'مخصص الزكاة — رصيد سنوات سابقة غير مسدد', zp - cc, '24'])
    # Art. 36: dividends declared and not deposited
    for a, v in L(lambda a: par(a) == '2128000'):
        if cr(v) > 0: eq.append(['div', a, nm(a), cr(v), '36'])
    # Art. 30: owner / partner current accounts without a fixed term or market return -> equity (credit balances);
    # Art. 34: no set-off, so debit balances are not deducted (they stay in non-deducted assets)
    own_dr = []
    for a, v in L(lambda a: par(a) == '2126000'):
        if cr(v) > 0: eq.append(['own', a, nm(a), cr(v), '30, 34'])
        elif v > 0: own_dr.append([a, nm(a), v])
    o['eq'] = eq; o['eqTot'] = sum(r[3] for r in eq)
    o['eqBook'] = sum(r[3] for r in eq if r[0] in ('cap', 'res', 're', 'oci'))
    # ---------------------------------------------------------------- non-current liabilities (Art. 29(1))
    li = []
    for a, v in L(lambda a: a in ('2111001', '2111002', '2111003')):
        if cr(v) > 0: li.append(['emp', a, nm(a), cr(v), '24, 29(1)(b)'])
    loans = sum(cr(v) for a, v in L(lambda a: par(a) == '2112000'))
    dint = sum(v for a, v in L(lambda a: a == '1262000'))                  # deferred interest: contra to the loan
    carry = loans - dint
    # current portion: the next 12 months of an equal-instalment loan = the net reduction over the year just ended
    prev = sum(-bal(a, Y - 1) for a in mov if par(a) == '2112000') - bal('1262000', Y - 1)
    if Y == OPENY:
        # open year: use the last closed year's repayment as the next-12-months schedule
        pp = sum(-bal(a, Y - 2) for a in mov if par(a) == '2112000') - bal('1262000', Y - 2)
        red = pp - prev
    else:
        red = prev - carry
    cur_part = max(0.0, min(carry, red))
    if carry > 0:
        li.append(['loan', '2113002-1262000', 'القروض طويلة الأجل (الجزء غير المتداول) — القيمة الدفترية بعد الفوائد المؤجلة', carry - cur_part, '29(1)(a)'])
    o['loan'] = {'gross': loans, 'dint': dint, 'carry': carry, 'current': cur_part, 'noncurrent': carry - cur_part}
    # ---------------------------------------------------------------- deductions (Art. 26, 48-50)
    ded = []
    fa = L(lambda a: par(a) in ('1110000', '1111000'))
    ded.append(['fa', 'صافي الأصول الثابتة', sum(v for a, v in fa), '26(4), 48, 49(1)', [[a, nm(a), v] for a, v in fa]])
    it = L(lambda a: par(a) in ('1120000', '1121000'))
    ded.append(['int', 'الأصول غير الملموسة (صافي)', sum(v for a, v in it), '26(5), 50', [[a, nm(a), v] for a, v in it]])
    wip = L(lambda a: par(a).startswith('113'))
    ded.append(['wip', 'مشروعات تحت التنفيذ لغرض الاستخدام', sum(v for a, v in wip), '49(5)', [[a, nm(a), v] for a, v in wip]])
    o['ded'] = ded; o['dedTot'] = sum(r[2] for r in ded)
    # ---------------------------------------------------------------- current assets / liabilities (Art. 29(2)(b), 25)
    ca = []
    for a, v in L(lambda a: a[0] == '1' and not par(a).startswith('11') and a != '1262000' and par(a) != '1300000'):
        ca.append([a, nm(a), v])
    for a, n_, v in own_dr: ca.append([a, n_ + ' (رصيد مدين للمالك — لا يحسم)', v])
    o['ca'] = ca; o['caTot'] = sum(r[2] for r in ca)
    moved = set(r[1] for r in eq) | {'2111001', '2111002', '2111003', '2123003'}
    cl = []
    for a, v in L(lambda a: a[0] == '2' and par(a) not in ('2210000', '2230000', '2240000', '2220000', '2200000', '2112000')
                  and a not in moved and not (par(a) == '2126000')):
        cl.append([a, nm(a), cr(v)])
    for a, v in L(lambda a: par(a) == '1300000'):        # sales control / clearing accounts (credit = liability)
        cl.append([a, nm(a), cr(v)])
    if cur_part: cl.append(['2113002', 'الجزء المتداول من القرض', cur_part])
    o['cl'] = cl; o['clTot'] = sum(r[2] for r in cl)
    excess = max(0.0, o['clTot'] - o['caTot'])
    o['clExcess'] = excess
    # ---------------------------------------------------------------- liabilities added, capped at deducted assets (Art. 23(2), 25(4))
    liTot = sum(r[3] for r in li) + excess
    if excess: li.append(['clx', '—', 'زيادة الالتزامات المتداولة عن الأصول المتداولة', excess, '29(2)(b)'])
    o['li'] = li; o['liRaw'] = liTot; o['liAdd'] = min(liTot, o['dedTot'])
    # ---------------------------------------------------------------- net profit (Art. 23(3), 62-65)
    ni = ext('net_income', 'is_', Y); zk = -ext('zakat_expenses', 'is_', Y)
    prior = zk - cc                                       # prior-year zakat differences booked this year: taxable income / accepted expense
    start = ni + cc                                       # net profit before the year's zakat
    o['np'] = {'afterZakat': ni, 'zakatAccount': zk, 'currentCharge': cc, 'priorAdj': prior, 'book': start}
    fl = fines(Y)
    o['fines'] = [[r[1], r[2], r[3], r[5], r[6]] for r in fl]
    G = collections.OrderedDict()
    for r in fl:
        m_ = re.search(r'رقم\s*/?\s*(\d{8,})', r[6])
        d_ = re.sub(r'^\s*(اقفال|عكس)\s+', '', r[6].strip()); d_ = d_.split(' ف حساب')[0]; d_ = re.sub(r'^قيمة\s+', '', d_).strip()
        k = m_.group(1) if m_ else re.sub(r'\s+', ' ', d_)[:45]
        g = G.setdefault(k, [d_, 0.0, 0]); g[1] += r[5]; g[2] += 1
    o['finesG'] = sorted([[v[0], round(v[1], 2), v[2]] for v in G.values() if abs(v[1]) >= 0.5], key=lambda x: -x[1])
    o['fineReview'] = [[r[1], r[2], r[3], r[5], r[6]] for r in fine_review(Y)]
    adj = [['fines', 'غرامات ومخالفات حكومية (مصروف غير جائز الحسم)', round(sum(r[5] for r in fl), 2), '62']]
    o['adj'] = adj; o['adjTot'] = sum(r[2] for r in adj)
    o['npAdj'] = start + o['adjTot']
    # ---------------------------------------------------------------- base, limits, zakat
    base = o['eqTot'] + o['liAdd'] + o['adjTot'] - o['dedTot']
    ta = ext('total_assets', 'bs', Y)
    undeducted = ta - o['dedTot']
    mn = min(undeducted + o['adjTot'], o['npAdj'])
    mx = o['eqTot'] + o['adjTot']
    rule = 'base'
    fin = base
    if o['npAdj'] > 0 and base < o['npAdj']:
        fin, rule = mn, 'min'                                            # Art. 27(2)
    elif o['npAdj'] <= 0 and base <= 0:
        fin, rule = 0.0, 'none'                                          # Art. 27(3)
    if fin > mx:
        fin, rule = mx, 'max'                                            # Art. 28
    o.update(base=base, totalAssets=ta, undeducted=undeducted, minBase=mn, maxBase=mx, finalBase=fin, rule=rule)
    d = days(Y); o['rate'] = RATE(d); o['zakat'] = max(0.0, fin) * RATE(d)
    # booked in the ledger
    o['booked'] = cc
    # provision roll-forward
    op_ = -bal('2123003', Y - 1); cl_ = -bal('2123003', Y)
    o['provRoll'] = {'open': op_, 'charge': zk, 'paid': op_ + zk - cl_, 'close': cl_}
    if Y == OPENY:
        el = (ASOF - dt.date(Y, 1, 1)).days + 1
        o['elapsed'] = el
        o['accrualToDate'] = o['zakat'] * el / d
    return o

out = {'asOf': ASOF.isoformat(), 'years': YEARS, 'openYear': OPENY, 'y': {}}
for Y in YEARS: out['y'][Y] = year(Y)

# expense classification by year (cost of revenue vs G&A), with the owner's categories
EXTRA = {'3280004': 'خصم إضافي لشركات التأمين (مخصص مكون)', '3280005': 'الزكاة', '3290001': 'تكاليف تمويل (فوائد قروض)',
         '3380000': 'خسائر رأسمالية', '3390000': 'تكلفة الفائدة على التزامات منافع الموظفين', '3280003': 'تكلفة الخدمة الحالية',
         '3280001': 'استهلاك ممتلكات وآلات ومعدات'}
REVIEW = {'3210000': 'إكراميات — تقبل إذا كانت فعلية ومرتبطة بالنشاط ومؤيدة بمستندات (م 62)',
          '3250001': 'ضيافة — شروط المادة 62', '3250002': 'احتفالات — شروط المادة 62', '3260000': 'إفطار رمضان — شروط المادة 62',
          '3290003': 'عملات مزيفة — خسارة فعلية؟ (م 62)', '3200000': 'مكافآت مجلس الإدارة — مقبولة بما لا يتعارض مع الأنظمة (م 63(5))',
          '3280004': 'مخصص مكون خلال العام — مقبول (م 63(9)); رصيده يخفض الذمم ولا يضاف (س 22)',
          '3280005': 'الزكاة — زكاة العام تستبعد (البداية صافي الربح قبل الزكاة)؛ فروق الربط عن سنوات سابقة مصروف جائز الحسم أو إيراد خاضع',
          '3380000': 'خسائر رأسمالية — مرتبطة بأصول النشاط (م 62)', '3140001': 'رسوم حكومية — الغرامات والمخالفات بداخله تضاف لصافي الربح (انظر جدول الغرامات)'}
exp = []
for (a, fn), ys in pl.items():
    if a[0] != '3': continue
    side = 'COR' if fn == 'COR' else 'GA'
    cat = CLS[side].get(a) or CLS['GA' if side == 'COR' else 'COR'].get(a) or EXTRA.get(a) or 'غير مصنف'
    vals = [round(ys.get(Y, 0.0), 2) for Y in YEARS]
    if any(abs(v) >= 0.5 for v in vals): exp.append([a, nm(a), side, cat, vals])
# merge duplicates (same account/side from several functions)
m = collections.OrderedDict()
for a, n_, s, c, v in exp:
    k = (a, s)
    if k in m: m[k][4] = [x + y for x, y in zip(m[k][4], v)]
    else: m[k] = [a, n_, s, c, v]
out['exp'] = sorted(m.values(), key=lambda r: (r[2], r[3], r[0]))
out['review'] = REVIEW
# open-year monthly booked zakat
G = json.load(open(P('drv/gl_all.json')))
mz = collections.defaultdict(float)
for br, a, cc, f, ym, v in G:
    if a == '3280005' and ym[:4] == str(OPENY): mz[ym] += v
out['openMonthlyBooked'] = [[f'{OPENY}{m:02d}', round(mz.get(f'{OPENY}{m:02d}', 0.0), 2)] for m in range(1, ASOF.month + 1)]
out['src'] = 'EXSYS GL_TRANSACTIONS_DETAILS, four databases, posted and open vouchers (STATUS <> C), cancelled and closing vouchers excluded'

def rnd(x):
    if isinstance(x, float): return round(x, 2)
    if isinstance(x, list): return [rnd(i) for i in x]
    if isinstance(x, dict): return {k: rnd(v) for k, v in x.items()}
    return x
out = rnd(out)
json.dump(out, open(P('zak/data_zak.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
for Y in YEARS:
    o = out['y'][Y]
    print(Y, 'equity&similar', o['eqTot'], 'liab', o['liAdd'], 'ded', o['dedTot'], 'base', o['base'], 'rule', o['rule'],
          'final', o['finalBase'], 'zakat', o['zakat'], 'booked', o['booked'], 'CA', o['caTot'], 'CL', o['clTot'], 'loan', o['loan'])
print('bytes', os.path.getsize(P('zak/data_zak.json')))
