#!/usr/bin/env python3
"""Build the HR Command Center page from an extract file.

    python3 build_hr.py --extract data/extract.<co>.<date>.json \
        --config config/company.<co>.json --out out/

Writes:
  out/HR_Command_Center.html           standalone page (own <html> skeleton) - open locally or keep as the source file
  out/HR_Command_Center.artifact.html  fragment for the Artifact tool (it adds the skeleton itself)
  out/data.json                        the full data object embedded in the page (for audit / diff)
  out/build.md                         gates and findings summary

The extract is produced by scripts/ingest.py from the Cure MCP results of sql/*.sql.
No network access is needed here; everything the page shows comes from the extract.
"""
import argparse, json, os, re, statistics, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
MONF = ['January','February','March','April','May','June','July','August','September','October','November','December']
MONAR = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر']
def B(en, ar): return {'en': en, 'ar': ar}

def fmt(n): return f"{round(n):,}"
def K(n): return f"{n/1e6:.2f}M" if n >= 1e6 else f"{round(n/1e3)}k" if n >= 1e3 else str(round(n))
def ym_parts(ym): y, m = ym.split('-'); return int(y), int(m)
def ym_short(ym, with_year=False):
    y, m = ym_parts(ym); return f"{MON[m-1]} {y}" if with_year else MON[m-1]
def ym_full(ym): y, m = ym_parts(ym); return f"{MONF[m-1]} {y}"

def ym_short_b(ym, with_year=False):
    y, m = ym_parts(ym); return B(ym_short(ym, with_year), f"{MONAR[m-1]} {y}" if with_year else MONAR[m-1])
def ym_full_b(ym): y, m = ym_parts(ym); return B(ym_full(ym), f"{MONAR[m-1]} {y}")

def labels_for(yms):
    out = []
    for i, ym in enumerate(yms):
        y, m = ym_parts(ym)
        out.append(f"{MON[m-1]} {str(y)[2:]}" if (i == 0 or m == 1) else MON[m-1])
    return out

def next_months(asof, n=12):
    y, m = asof.year, asof.month
    out = []
    for _ in range(n):
        m += 1
        if m > 12: m = 1; y += 1
        out.append(MON[m-1])
    return out

NATMAP = {}
ORGMAP = {}
def branch_of_org(o):
    """001-004 are the branch administration cost centres (01 Riyadh, 02 BUR1, 03 BUR2, 04 Rafha); otherwise the first two characters."""
    if o in ('001', '002', '003', '004'): return '0' + o[2]
    return o[:2]



def load_natmap(kit):
    import glob, re
    for f in sorted(glob.glob(os.path.join(kit, 'raw', 'hr18*.txt'))):
        for l in open(f, encoding='utf8'):
            m = re.match(r'\s*(\d{3,6})\|(\d*)\|(\d*)\|', l)
            if m and m.group(3): NATMAP[m.group(1)] = m.group(3)


def load_orgmap(kit):
    f = os.path.join(kit, 'raw', 'hr32_staff_org.txt')
    if os.path.exists(f):
        for l in open(f, encoding='utf8'):
            if '|' in l: k, o = l.strip().split('|')[:2]; ORGMAP[k] = o


def pack_gosi(g):
    """Compact the output of gosi_check.py for the page (short keys, every text in English and Arabic)."""
    if not g: return None, None
    ST = lambda r: [r['st'].get(c, 'na') for c in ('c1', 'c2', 'c3', 'c4')]
    rows = []
    for r in g['rows']:
        go = r['gosi'] or {}
        rows.append(dict(c=r['code'], n=r['name'], i=r['id'], s=1 if r['saudi'] else 0, na=r.get('nat') or NATMAP.get(r['code'], '420' if r['saudi'] else ''), cc=branch_of_org(ORGMAP.get(r['code'], '')), b=go.get('br', ''), pb=r['pbasic'], ph=r['phous'], ps=r['psoc'], gb=go.get('basic', 0), gh=go.get('hous', 0), gt=go.get('total', 0),
                         at=r['atotal'], af=r['afixed'], pd=r['pded'], ad=r['aded'], ge=r['gexp'], pr=r['prate'], ar=r['arate'], gr=r['grate'], st=ST(r), pro=1 if r['prorated'] else 0, bad=1 if r['bad'] else 0, ex=r.get('exc'),
                         fx=[dict(k=f['k'], en=f['en'], ar=f['ar']) for f in r['fixes']]))
    only = [dict(i=o['id'], n=o['name'], b=o['br'], w=o['wage'], c=o['code'], s=o['status'], fx=o['fix']) for o in g['gosi_only']]
    noacct = [dict(c=n['code'], n=n['name'], g=n['pgross']) for n in g['not_in_acct']]
    S = g['summary']
    gosi = dict(month=g['month'], summary=S, rows=rows, only=only, noacct=noacct, sources=g['sources'])
    tr = g['travel']
    out = [dict(c=t['code'], n=t['name'], tn=t['tname'], i=t['id'], nat=t['nat'], ps=t.get('pst'), pay=t.get('pay', 0), ia=1 if t.get('inacct') else 0, op=t.get('octpay'), v=t.get('verdict', 'ok'), risk=1 if t.get('oct_risk') else 0) for t in tr if t['out']]
    trv = dict(total=len(tr), date=g.get('travel_date', ''), out=out, nostatus=[dict(c=n['code'], n=n['name'], i=n['id'], pay=n['pay'], ia=1 if n['inacct'] else 0) for n in g['nostatus']],
               summary=dict(out_total=S['out_total'], out_posted=S['out_posted'], out_paid=S['out_paid'], oct_risk=sum(1 for o in out if o['risk']), nostatus=S['nostatus']))
    return gosi, trv

def build(ex, cfg, pb, notes=None, labels_ar=None, gosi=None, prepay=None, nursing=None, leavedays=None, review=None, movement=None, salary=None, commission=None):
    asof = dt.date.fromisoformat(ex['asof'])
    yms = ex['ym']
    n = len(yms)
    for k in ['staffPaid','basic','plus','minus','gosiCo','gosiSt','absD','ot','hires','leavers']:
        assert len(ex[k]) == n, f"{k} has {len(ex[k])} values, expected {n}"
    th = cfg['thresholds']; own = cfg['owners']; own_ar = cfg.get('owners_ar', {}); cur = cfg['currency']
    O = lambda k: B(own[k], own_ar.get(k, own[k]))
    HC = ex['HC']; saudi = ex['saudi']
    gross = [a+b for a, b in zip(ex['basic'], ex['plus'])]
    last12 = lambda a: a[-12:]
    hires12 = sum(last12(ex['hires'])); leavers12 = sum(last12(ex['leavers']))
    avg_paid = sum(last12(ex['staffPaid'])) / min(12, n)
    turnover = leavers12 / avg_paid * 100
    peak_i = max(range(n), key=lambda i: ex['hires'][i])
    peak_hire = B(f"peak {ex['hires'][peak_i]} in {ym_short(yms[peak_i], True)}", f"الذروة {ex['hires'][peak_i]} في {ym_short_b(yms[peak_i], True)['ar']}")
    lastname = ym_full_b(yms[-1])

    loan = ex['loanRows']
    unc = lambda grp: sum(r[4] for r in loan if r[0] == grp and r[1].startswith('Pending'))
    unc_staff = lambda grp: sum(r[3] for r in loan if r[0] == grp and r[1].startswith('Pending'))
    loan_leaver_unc = unc('Leavers'); loan_active_unc = unc('Active staff')
    unposted_by = ex.get('unpostedByMonth', {}); unposted = sum(unposted_by.values())
    long_t, short_t = cfg['leave_types']['long'], cfg['leave_types']['short']
    lab = cfg['leave_labels']; lab_ar = cfg.get('leave_labels_ar', lab)
    year = asof.year
    ly = [r for r in ex['leaveRows'] if r[0] == str(year)]
    posted = lambda t: sum(r[4] for r in ly if r[1] == t and r[2] == 'Posted')
    cancelled = sum(r[3] for r in ly if r[2] == 'Cancelled')
    long_rec = {s: sum(r[3] for r in ly if r[1] == long_t and r[2] == s) for s in ['Posted','Cancelled','Open']}
    kp = dict(HC=HC, saudi=saudi, female=ex['female'], salRoll=ex['salRoll'], saudiSal=ex['saudiSal'], nonSaudiSal=ex['nonSaudiSal'],
              unposted=unposted, contractsNext6=sum(ex['expN']), expiredContracts=ex['expiredContracts'], openEnded=ex.get('openEnded',0), expiredIds=ex['expiredIds'],
              loanDedStaff=ex['loanDedStaff'], loanHoldersActive=unc_staff('Active staff'), openLeaveRecords=ex['openLeaveRecords'],
              openLeaveDays=ex['openLeaveDays'], cancelledYear=cancelled, leaveLongDays=posted(long_t), leaveShortDays=posted(short_t),
              loanLeaverPending=loan_leaver_unc)

    # ---- spikes (movement tab) ----
    spikes = []
    mu = statistics.mean(ex['hires']); sd = statistics.pstdev(ex['hires'])
    hi = [i for i in range(n) if ex['hires'][i] >= mu + th['spike_sigma']*sd and ex['hires'][i] >= th['spike_min_multiple']*mu]
    for i in hi:
        h = ex['hires'][i]; mm = ym_short_b(yms[i], True)
        spikes.append(B(f"{h} new first contracts in {mm['en']} against a monthly average of {mu:.0f}. Confirm these are real hires and not contract re-entries, then check each file for bank, IBAN, GOSI and any required loan record.",
                        f"{h} عقد أول جديد في {mm['ar']} مقابل متوسط شهري {mu:.0f}. تأكد أنهم تعيينات حقيقية وليسوا إعادة إدخال عقود، ثم افحص ملف كل موظف: البنك وIBAN والتأمينات وأي سجل قرض مطلوب."))
    lm = statistics.mean(ex['leavers']); lsd = statistics.pstdev(ex['leavers'])
    lo = [i for i in range(n) if ex['leavers'][i] >= lm + th['spike_sigma']*lsd]
    if lo:
        spikes.append(B("Leaver peaks: " + ", ".join(f"{ym_short(yms[i], True)} ({ex['leavers'][i]})" for i in lo) + f". Average is {lm:.0f} a month.",
                        "ذروات المغادرين: " + "، ".join(f"{ym_short_b(yms[i], True)['ar']} ({ex['leavers'][i]})" for i in lo) + f". المتوسط {lm:.0f} شهريًا."))
    if ex.get('leaverMethod','lastpay') == 'lastpay':
        spikes.append(B("Leavers use the last payroll month because the separation date is usually not filled in Cure.", "المغادرون محسوبون بآخر شهر راتب لأن تاريخ انتهاء الخدمة غالبًا غير مسجل في Cure."))
    else:
        spikes.append(B("Leavers use the recorded separation date.", "المغادرون محسوبون بتاريخ انتهاء الخدمة المسجل."))

    # ---- findings (rules) ----
    F = []
    def add(s, a, t, e, x, o): F.append(dict(s=s, a=a, t=t, e=e, x=x, o=o))
    dlab = lambda d: B(f"{d.day} {MON[d.month-1]} {d.year}", f"{d.day} {MONAR[d.month-1]} {d.year}")
    da = dlab(asof)
    if ex['expiredContracts'] > 0:
        c = ex['expiredContracts']
        add('H','Contracts',B(f"{c} active staff hold contracts that ended in the past", f"{c} موظف على رأس العمل عقودهم منتهية"),
            B(f"PS_STAFF_CONTRACT: status A, current, END_DATE before {da['en']}, {c} employees.", f"PS_STAFF_CONTRACT: الحالة A وحالي، END_DATE قبل {da['ar']}، {c} موظف."),
            B("Renew or close each contract and attach the signed renewal. Block payroll for staff without a valid contract.", "جدّد أو أغلق كل عقد وأرفق التجديد الموقّع. أوقف الراتب لمن لا يملك عقدًا ساريًا."), O('contracts'))
    if ex.get('openEnded', 0) > 0:
        c = ex['openEnded']
        add('L','Contracts',B(f"{c} active staff have no contract end date", f"{c} موظف على رأس العمل بلا تاريخ نهاية عقد"),
            B(f"PS_STAFF_CONTRACT: status A, current, END_DATE blank for {c} employees. They are outside the renewal calendar.", f"PS_STAFF_CONTRACT: الحالة A وحالي وEND_DATE فارغ لـ {c} موظف. هم خارج تقويم التجديد."),
            B("Confirm each is a permanent (open-ended) contract and record the basis, so a missing date is never mistaken for a valid one.", "تأكد أن كل واحد عقده دائم (مفتوح المدة) وسجّل الأساس، حتى لا يُفهم التاريخ الفارغ كعقد ساري."), O('contracts'))
    if unposted > 0:
        items = sorted(unposted_by.items()); prev = None; seg = []; seg_ar = []
        for k, v in items:
            y = ym_parts(k)[0]
            seg.append(f"{ym_short(k, y != prev)} ({v})"); seg_ar.append(f"{ym_short_b(k, True)['ar']} ({v})"); prev = y
        add('M','Payroll',B(f"{unposted} payroll rows in closed months are still open", f"{unposted} صف رواتب في شهور مقفلة ما زالت مفتوحة"),
            B(f"PR_SALARY_TRANSACTION_M status O (open, not posted): {', '.join(seg)}. The open draft month is excluded.", f"PR_SALARY_TRANSACTION_M بحالة O (مفتوح وغير مرحّل): {'، '.join(seg_ar)}. شهر المسودة المفتوح مستثنى."),
            B(f"List the {unposted} rows, post or reverse them, and lock closed months so the count stays at zero.", f"اسرد الصفوف الـ {unposted} ورحّلها أو اعكسها، واقفل الشهور المقفلة ليبقى العدد صفرًا."), O('payroll'))
    if loan_leaver_unc > 0:
        add('M','Loans',B("Pending loan installments remain on staff who have left", "أقساط سلف معلّقة على موظفين تركوا العمل"),
            B(f"Installments still pending (status N) on leavers: {fmt(loan_leaver_unc)} across {unc_staff('Leavers')} staff. Active staff carry {fmt(loan_active_unc)} pending. Leavers with posted loans in total: {ex['leaverLoanStaff']}. Rescheduled installments (status R) are not counted because later installments replace them.",
              f"أقساط ما زالت معلّقة (الحالة N) على من تركوا العمل: {fmt(loan_leaver_unc)} على {unc_staff('Leavers')} موظف. على رأس العمل معلّق {fmt(loan_active_unc)}. إجمالي من تركوا العمل ولديهم سلف مرحّلة: {ex['leaverLoanStaff']}. الأقساط المعاد جدولتها (R) غير محسوبة لأن أقساطًا لاحقة تحل محلها."),
            B("Match each leaver to the final settlement. Recover through settlement or write off with approval.", "طابق كل مغادر مع التسوية النهائية. استرد عبر التسوية أو اشطب بموافقة."), O('loans'))
    pa = ex.get('passport', dict(expired=0, soon=0, noexp=0, ok=0))
    bad_ids = ex['expiredIds'] + ex['idNoExpiry']
    if bad_ids / HC > 0.05:
        v = ex.get('idValid', 0)
        add('H','Compliance',B("Residence document dates are not maintained in Cure", "تواريخ وثائق الإقامة غير محدّثة في Cure"),
            B(f"Iqama, national ID and border ID: {v} of {HC} active staff have a valid expiry date on file, {ex['expiredIds']} have an expired date and {ex['idNoExpiry']} have no date. Passports: {pa['expired']} expired and {pa['noexp']} with no date. Staff on payroll cannot all hold expired documents, so the dates are stale.",
              f"الإقامة والهوية الوطنية وهوية الحدود: {v} من {HC} موظفًا لديهم تاريخ انتهاء ساري، و{ex['expiredIds']} تاريخهم منتهٍ، و{ex['idNoExpiry']} بلا تاريخ. جوازات السفر: {pa['expired']} منتهية و{pa['noexp']} بلا تاريخ. لا يمكن أن يكون كل هؤلاء على الراتب بوثائق منتهية، فالتواريخ قديمة."),
            B("Update every document date from the current card, make expiry a required field, and report expiring documents monthly. Until then renewals cannot be tracked from Cure.", "حدّث تاريخ كل وثيقة من البطاقة الحالية، واجعل تاريخ الانتهاء حقلًا إلزاميًا، وارفع تقريرًا شهريًا بالوثائق المنتهية قريبًا. حتى ذلك الحين لا يمكن تتبع التجديدات من Cure."), O('compliance'))
    elif ex['expiredIds'] > 0:
        add('M','Compliance',B(f"{ex['expiredIds']} active staff have an expired identity document", f"{ex['expiredIds']} موظف على رأس العمل لديهم وثيقة هوية منتهية"),
            B(f"Latest residence-document record expired before {da['en']}. {ex['idSoon']} more expire within 180 days.", f"آخر وثيقة إقامة منتهية قبل {da['ar']}. و{ex['idSoon']} آخرون تنتهي خلال 180 يومًا."),
            B("Start renewals now and track each case on the compliance calendar.", "ابدأ التجديدات الآن وتتبع كل حالة في تقويم الالتزام."), O('compliance'))
    gap = ex['gl']['eosb'] - ex['gl']['estB']
    if abs(gap) / max(ex['gl']['estB'], 1) * 100 > th['eosb_gap_pct']:
        d_en, d_ar = ('higher', 'أعلى') if gap > 0 else ('lower', 'أقل')
        g = ex['gl']
        add('M','Provisions',B(f"End-of-service provision is {d_en} than the recomputed award", f"مخصص نهاية الخدمة {d_ar} من المكافأة المعاد حسابها"),
            B(f"GL {cfg['accounts']['eosb']} shows {g['eosb']/1e6:.2f}M credit. Recomputed award for {HC} active staff is {g['estB']/1e6:.2f}M on basic and {g['estW']/1e6:.2f}M with housing and transport. Gap {abs(gap)/1e6:.2f}M, part of which may be leavers unpaid.",
              f"الحساب {cfg['accounts']['eosb']} يظهر رصيدًا دائنًا {g['eosb']/1e6:.2f}M. المكافأة المعاد حسابها لـ {HC} موظفًا {g['estB']/1e6:.2f}M على الأساسي و{g['estW']/1e6:.2f}M مع السكن والمواصلات. الفرق {abs(gap)/1e6:.2f}M وجزء منه قد يكون لمغادرين لم تُسدد مستحقاتهم."),
            B("Split the account by employee, remove leavers settled, and book the true-up at the year-end close.", "قسّم الحساب حسب الموظف، واستبعد من سُويت مستحقاتهم، وسجّل التسوية عند إقفال نهاية العام."), O('provisions'))
    mc = ex['missCounts']
    if mc.get('licence',0) > 0 or mc.get('probation',0) > 0:
        add('M','Master data',B("Professional licence and probation period are blank for active staff", "الترخيص المهني وفترة التجربة فارغان للموظفين على رأس العمل"),
            B(f"LICENSE_ID blank for {mc.get('licence',0)} of {HC} and TEST_PERIOD_DAYS blank for {mc.get('probation',0)}.", f"LICENSE_ID فارغ لـ {mc.get('licence',0)} من {HC} وTEST_PERIOD_DAYS فارغ لـ {mc.get('probation',0)}."),
            B("Load licence numbers and expiry for clinical roles first. Capture probation days on every new contract.", "حمّل أرقام التراخيص وتواريخ انتهائها للوظائف السريرية أولًا، وسجّل أيام التجربة في كل عقد جديد."), O('master'))
    if mc.get('dss',0) > 0:
        add('M','Master data',B("Service start date is empty in the staff master", "تاريخ بدء الخدمة فارغ في الملف الرئيسي للموظفين"),
            B(f"DATE_START_SERVICE is blank for {mc['dss']} of {HC}. Service is derived from the first contract, so rehires and gaps can distort leave and end-of-service.", f"DATE_START_SERVICE فارغ لـ {mc['dss']} من {HC}. تُحسب الخدمة من أول عقد، فإعادة التعيين والانقطاع قد يشوّهان الإجازات ونهاية الخدمة."),
            B("Fill the field from the first contract date and review rehires one by one.", "املأ الحقل من تاريخ أول عقد وراجع حالات إعادة التعيين واحدة واحدة."), O('master'))
    small_defs = [('GOSI date','تاريخ التأمينات',mc.get('gosi',0)), ('email','البريد',mc.get('email',0)), ('birth date','تاريخ الميلاد',mc.get('dob',0)), ('nationality','الجنسية',mc.get('nat',0)), ('ID record','سجل الهوية',mc.get('idrec',0))]
    small = [(k, ka, v) for k, ka, v in small_defs if v / HC * 100 >= th['missing_field_min_pct'] or v > 0]
    if small:
        add('M','Master data',B("Other master fields are incomplete", "حقول رئيسية أخرى غير مكتملة"),
            B("Missing: " + ", ".join(f"{k} {v}" for k, ka, v in small) + f" of {HC} active staff.", "الناقص: " + "، ".join(f"{ka} {v}" for k, ka, v in small) + f" من {HC} موظفًا."),
            B("Close the gaps by branch. Make GOSI date and birth date mandatory on the hire form.", "سدّ الفجوات حسب الفرع، واجعل تاريخ التأمينات وتاريخ الميلاد إلزاميين في نموذج التعيين."), O('master'))
    if ex['openLeaveRecords'] > 0:
        add('M','Leave',B("Open leave records have not been posted", "سجلات إجازة مفتوحة لم تُرحّل"),
            B(f"PS_STAFF_VACATIONS status O: {ex['openLeaveRecords']} records and {ex['openLeaveDays']} days across all years. The payroll run skips leave that crosses month-end without a return date.", f"PS_STAFF_VACATIONS بحالة O: {ex['openLeaveRecords']} سجلًا و{ex['openLeaveDays']} يومًا في كل السنوات. المسير يتخطى الإجازة العابرة لنهاية الشهر بلا تاريخ عودة."),
            B("Post or cancel each record before the monthly run. Report open leave to branch managers every week.", "رحّل كل سجل أو ألغه قبل المسير الشهري، وارفع تقرير الإجازات المفتوحة لمديري الفروع أسبوعيًا."), O('leave'))
    tot_long = sum(long_rec.values())
    if tot_long and long_rec['Cancelled'] / tot_long * 100 > th['cancel_rate_pct']:
        pc = long_rec['Cancelled'] / tot_long * 100
        add('M','Leave',B(f"{pc:.0f} percent of {year} long leaves are cancelled", f"{pc:.0f}% من الإجازات الطويلة لعام {year} ملغاة"),
            B(f"{lab['long']}: {long_rec['Cancelled']} cancelled against {long_rec['Posted']} posted and {long_rec['Open']} open in {year}.", f"{lab_ar['long']}: {long_rec['Cancelled']} ملغاة مقابل {long_rec['Posted']} مرحّلة و{long_rec['Open']} مفتوحة في {year}."),
            B("Review reasons for cancellation by branch and approver. Add manager sign-off before posting.", "راجع أسباب الإلغاء حسب الفرع والمعتمِد، وأضف توقيع المدير قبل الترحيل."), O('hr_manager'))
    med = statistics.median(ex['absD'])
    ab = [i for i in range(n) if ex['absD'][i] > th['absence_spike_multiple']*med]
    if ab:
        add('M','Payroll',B("Absence deductions spike in some months", "خصومات الغياب ترتفع في بعض الشهور"),
            B("Months above " + f"{th['absence_spike_multiple']:g}" + f" times the median ({K(med)}): " + ", ".join(f"{ym_short(yms[i], True)} {K(ex['absD'][i])}" for i in ab) + ".",
              "شهور فوق " + f"{th['absence_spike_multiple']:g}" + f" ضعف الوسيط ({K(med)}): " + "، ".join(f"{ym_short_b(yms[i], True)['ar']} {K(ex['absD'][i])}" for i in ab) + "."),
            B("Test a sample of the spike months for correct unpaid-leave days and review the attendance source.", "اختبر عينة من شهور الارتفاع للتأكد من أيام الإجازة بدون راتب وراجع مصدر الحضور."), O('payroll'))
    for i in hi:
        h = ex['hires'][i]; mm = ym_short_b(yms[i], True)
        add('M','Hiring',B(f"{h} new contracts in {mm['en']}", f"{h} عقد جديد في {mm['ar']}"),
            B(f"First contract start dates: {h} in {mm['en']} against a monthly average near {mu:.0f}.", f"تواريخ بداية أول عقد: {h} في {mm['ar']} مقابل متوسط شهري قرابة {mu:.0f}."),
            B(f"Run the new-hire checklist on all {h}: contract, nationality, ID type, IBAN and bank, salary record, GOSI, and any required loan record.", f"طبّق قائمة فحص التعيين الجديد على الـ {h}: العقد والجنسية ونوع الهوية وIBAN والبنك وسجل الراتب والتأمينات وأي سجل قرض مطلوب."), O('contracts'))
    b = ex['branches']
    if saudi / HC < 0.5:
        add('L','Workforce',B(f"Saudization is {saudi/HC*100:.0f} percent", f"نسبة السعودة {saudi/HC*100:.0f}%"),
            B(f"{saudi} Saudi staff of {HC}. " + ". ".join(f"{x['n']} {x['s']} of {x['h']}" for x in b) + ".", f"{saudi} سعوديًا من {HC}. " + ". ".join(f"{(labels_ar or {}).get(x['n'], x['n'])} {x['s']} من {x['h']}" for x in b) + "."),
            B("Check the Nitaqat band for each establishment and plan localization where regulations allow.", "افحص نطاق نطاقات لكل منشأة وخطّط للتوطين حيث تسمح الأنظمة."), O('hr_manager'))
    omin, omax = min(range(n), key=lambda i: ex['ot'][i]), max(range(n), key=lambda i: ex['ot'][i])
    if ex['ot'][omax] > th['overtime_ratio'] * max(ex['ot'][omin], 1):
        add('L','Payroll',B(f"Overtime swings between {K(ex['ot'][omin])} and {K(ex['ot'][omax])} a month", f"العمل الإضافي يتأرجح بين {K(ex['ot'][omin])} و{K(ex['ot'][omax])} شهريًا"),
            B(f"Lowest {ym_short(yms[omin], True)}, highest {ym_short(yms[omax], True)}.", f"الأدنى {ym_short_b(yms[omin], True)['ar']} والأعلى {ym_short_b(yms[omax], True)['ar']}."),
            B("Set a monthly overtime cap per branch and require pre-approval above it.", "حدّد سقفًا شهريًا للعمل الإضافي لكل فرع واشترط موافقة مسبقة فوقه."), O('branch'))
    if turnover >= th['turnover_low_pct']:
        t0 = ex['tenure'][0][1]
        add('M' if turnover >= th['turnover_medium_pct'] else 'L','Retention',B(f"Turnover runs near {turnover:.0f} percent a year", f"الدوران الوظيفي قرابة {turnover:.0f}% سنويًا"),
            B(f"{leavers12} leavers in the last 12 months against an average of {avg_paid:.0f} paid staff.", f"{leavers12} مغادرًا في آخر 12 شهرًا مقابل متوسط {avg_paid:.0f} موظفًا يتقاضون راتبًا."),
            B(f"Hold exit interviews and review the {t0} staff with under one year of service first.", f"أجرِ مقابلات خروج وابدأ بمراجعة الـ {t0} موظفًا الذين لديهم أقل من سنة خدمة."), O('hr_manager'))
    order = {'H':0,'M':1,'L':2}
    F.sort(key=lambda f: order[f['s']])

    def first_sentence(txt): return txt.split('. ')[0].rstrip('.')
    top3 = [B(f"{f['t']['en']}. {first_sentence(f['x']['en'])}.", f"{f['t']['ar']}. {first_sentence(f['x']['ar'])}.") for f in F[:3]]
    # notes
    zero_long = [r[0] for r in ex['leaveChart'] if r[1] == 0]
    cond = zero_long and len(zero_long) < len(ex['leaveChart'])
    note_chart = B("Posted records only." + (f" {lab['long']} has no records before {int(zero_long[-1])+1}." if cond else ""),
                   "السجلات المرحّلة فقط." + (f" {lab_ar['long']} لا توجد له سجلات قبل {int(zero_long[-1])+1}." if cond else ""))
    ly_p = lambda t: [r for r in ly if r[1] == t and r[2] == 'Posted']
    avg = lambda rows: (sum(r[4] for r in rows) / sum(r[3] for r in rows)) if rows and sum(r[3] for r in rows) else 0
    note_types = B(f"Type names are the Cure codes. {lab['long']} averages about {avg(ly_p(long_t)):.0f} days a record, {lab['short']} about {avg(ly_p(short_t)):.1f} days.",
                   f"أسماء الأنواع هي أكواد Cure. {lab_ar['long']} متوسطه حوالي {avg(ly_p(long_t)):.0f} يومًا للسجل، و{lab_ar['short']} حوالي {avg(ly_p(short_t)):.1f} يومًا.")
    id_note = B(f"Latest expiry per employee across iqama, national ID and border ID. Passports: {pa['expired']} expired, {pa['soon']} expiring within 180 days, {pa['noexp']} with no date, {pa['ok']} valid.",
                f"آخر تاريخ انتهاء لكل موظف عبر الإقامة والهوية الوطنية وهوية الحدود. جوازات السفر: {pa['expired']} منتهية، {pa['soon']} تنتهي خلال 180 يومًا، {pa['noexp']} بلا تاريخ، {pa['ok']} سارية.")

    draft = ex.get('draftMonth')
    draft_note = B(f"{ym_full(draft)} is still a draft run and is left out of the trends.", f"{ym_full_b(draft)['ar']} ما زال مسودة ومستبعد من الاتجاهات.") if draft else B("", "")
    uy = sorted(unposted_by)
    if not uy: unposted_range = B("none", "لا يوجد")
    elif len(uy) == 1: unposted_range = ym_short_b(uy[0], True)
    else:
        sy = ym_parts(uy[0])[0] != ym_parts(uy[-1])[0]
        unposted_range = B(f"{ym_short(uy[0], sy)} to {ym_short(uy[-1], True)}", f"{ym_short_b(uy[0], True)['ar'] if sy else MONAR[ym_parts(uy[0])[1]-1]} إلى {ym_short_b(uy[-1], True)['ar']}")
    comp = lambda k: 100 - mc.get(k, 0) / HC * 100
    ktargets = [
        [B('Expired contracts','العقود المنتهية'), str(ex['expiredContracts']), '0'],
        [B('Residence documents with a valid date on file','وثائق الإقامة بتاريخ ساري'), f"{ex.get('idValid', 0)/HC*100:.0f}%", '100%'],
        [B('Unposted rows in closed months','صفوف غير مرحّلة في شهور مقفلة'), str(unposted), '0'],
        [B('Open leave records','سجلات إجازة مفتوحة'), str(ex['openLeaveRecords']), '0'],
        [B('Turnover, 12 months','الدوران، 12 شهرًا'), f"{turnover:.1f}%", B('Under 20%','أقل من 20%')],
        [B('Licence ID completeness','اكتمال رقم الترخيص'), f"{comp('licence'):.0f}%", '100%'],
        [B('GOSI date completeness','اكتمال تاريخ التأمينات'), f"{comp('gosi'):.0f}%", '100%'],
        [B('Pending loan installments on leavers','أقساط سلف معلّقة على من تركوا العمل'), K(loan_leaver_unc), B('0 after settlement','0 بعد التسوية')]]

    src_en = f"Source: Cure {cfg['cure']['hr_branch_param']} database (PS_STAFF_CONTRACT, STAFF_MASTER, PR_SALARY_TRANSACTION_M and _D, PS_STAFF_VACATIONS, PR_STAFF_LOANS and installments, PS_STAFF_IDS, GL_TRANSACTIONS_DETAILS). Extracted {da['en']}."
    src_ar = f"المصدر: قاعدة بيانات Cure ({cfg['cure']['hr_branch_param']}): PS_STAFF_CONTRACT وSTAFF_MASTER وPR_SALARY_TRANSACTION_M و_D وPS_STAFF_VACATIONS وPR_STAFF_LOANS وأقساطها وPS_STAFF_IDS وGL_TRANSACTIONS_DETAILS. تاريخ الاستخراج {da['ar']}."

    # ---- payroll notes ----
    pn = None
    if notes:
        cur_ym = draft or f"{asof.year}-{asof.month:02d}"
        ms = sorted({x['month'] for x in notes['notes']} | {cur_ym})
        # fill every month between the first note month and the current month
        y, m = ym_parts(ms[0]); allm = []
        while f"{y}-{m:02d}" <= cur_ym:
            allm.append(f"{y}-{m:02d}"); m += 1
            if m > 12: m = 1; y += 1
        pn = dict(notes, months=allm, current=cur_ym,
                  monthNames={k: ym_full_b(k) for k in allm})

    D = dict(
        meta=dict(company=B(cfg['company'], cfg.get('company_ar', cfg['company'])), scope=B(cfg['scope'], cfg.get('scope_ar', cfg['scope'])), currency=cur,
                  asof_label=da, year=str(year), last_month_name=lastname, draft_note=draft_note, unposted_range=unposted_range, source_note=B(src_en, src_ar)),
        accounts=cfg['accounts'], labels=dict(leaveLong=B(lab['long'], lab_ar['long']), leaveShort=B(lab['short'], lab_ar['short'])),
        months=labels_for(yms), planMonths=next_months(asof),
        staffPaid=ex['staffPaid'], basic=ex['basic'], plus=ex['plus'], minus=ex['minus'], gosiCo=ex['gosiCo'], gosiSt=ex['gosiSt'], absD=ex['absD'], ot=ex['ot'],
        hires=ex['hires'], leavers=ex['leavers'], branches=b, jobs=ex['jobs'], age=ex['age'], tenure=ex['tenure'], earn=ex['earn'], ded=ex['ded'],
        expMonths=ex['expMonths'], expN=ex['expN'], leaveRows=ex['leaveRows'], leaveChart=ex['leaveChart'], loanRows=loan,
        miss=ex['miss'], idb=ex['idb'], gl=ex['gl'], kpis=kp,
        derived=dict(turnover=turnover, hires12=hires12, leavers12=leavers12, peakHire=peak_hire, avgPaid=avg_paid),
        findings=F, top3=top3, spikes=spikes, kpiTargets=ktargets,
        notes=dict(leaveChart=note_chart, leaveTypes=note_types, loanStatus=B(cfg['loan_status_note'], cfg.get('loan_status_note_ar', cfg['loan_status_note'])), idNote=id_note),
        plan=cfg['plan_defaults'], playbook=pb, ar=labels_ar or {}, payroll=pn)
    gl = sorted([g for g in (gosi if isinstance(gosi, list) else [gosi]) if g], key=lambda g: g['month'])
    by = {}
    for g in gl:
        gp, tp = pack_gosi(g); by[g['month']] = dict(gosi=gp, travel=tp)
    if by:
        last = gl[-1]['month']; D['gosi'], D['travel'] = by[last]['gosi'], by[last]['travel']
        D['gosiMonths'] = list(by); D['gosiBy'] = by
    else: D['gosi'] = D['travel'] = None; del D['gosi'], D['travel']
    if movement: D['movement'] = movement
    if movement and D.get('gosi'): D['gosiNats'] = movement['nats']; D['gosiBr'] = movement['branches']
    if salary: D['salary'] = salary
    if prepay: D['prepay'] = prepay
    if nursing: D['nursing'] = nursing
    if leavedays: D['leaveDays'] = leavedays
    if review: D['review'] = review
    if commission: D['commission'] = commission
    return D, F

def render(D, template):
    """The page reads everything from the JSON block, so rendering is one substitution."""
    blob = json.dumps(D, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    assert '/*DATA_JSON*/' in template
    return template.replace('/*DATA_JSON*/', blob)

def gates(D):
    msgs, ok = [], True
    br = D['branches']
    if sum(x['h'] for x in br) != D['kpis']['HC']: ok = False; msgs.append(f"FAIL branch headcount {sum(x['h'] for x in br)} != HC {D['kpis']['HC']}")
    else: msgs.append("ok branch headcount ties to active staff")
    if sum(x['s'] for x in br) != D['kpis']['saudi']: ok = False; msgs.append("FAIL branch Saudi count")
    else: msgs.append("ok branch Saudi count ties")
    if abs(sum(x['sal'] for x in br) - D['kpis']['salRoll']) > 1: ok = False; msgs.append("FAIL branch salary roll")
    else: msgs.append("ok branch salary roll ties")
    for name in ['age','tenure']:
        t = sum(r[1] for r in D[name])
        if t != D['kpis']['HC']: ok = False; msgs.append(f"FAIL {name} bands sum {t} != HC")
        else: msgs.append(f"ok {name} bands sum to HC")
    last_earn = sum(r[1] for r in D['earn']); last_ded = sum(r[1] for r in D['ded'])
    if abs(last_earn - D['plus'][-1]) > 1 or abs(last_ded - D['minus'][-1]) > 1: ok = False; msgs.append(f"FAIL last-month items vs totals ({last_earn} vs {D['plus'][-1]}, {last_ded} vs {D['minus'][-1]})")
    else: msgs.append("ok last-month item mix ties to the monthly totals")
    if sum(r[1] for r in D['idb']) != D['kpis']['HC']: ok = False; msgs.append("FAIL identity buckets do not sum to HC")
    else: msgs.append("ok identity buckets sum to HC")
    pn = D.get('payroll')
    if pn:
        ids = [x['id'] for x in pn['notes']]; bad = []
        if len(ids) != len(set(ids)): bad.append('duplicate ids')
        for x in pn['notes']:
            for k in ['id','month','src','cat','pri','t','d','x','owner','status']:
                if k not in x: bad.append(f"{x.get('id')} missing {k}")
            if x['status'] not in ('open','info','done'): bad.append(f"{x['id']} bad status")
            if x['pri'] not in ('H','M','L','I'): bad.append(f"{x['id']} bad priority")
            if x['cat'] not in pn['cats']: bad.append(f"{x['id']} unknown category {x['cat']}")
            if x['src'] not in pn['sources']: bad.append(f"{x['id']} unknown source {x['src']}")
            if x['status'] == 'done' and not x.get('closedIn'): bad.append(f"{x['id']} done without closedIn")
            if x.get('closedIn') and x['closedIn'] < x['month']: bad.append(f"{x['id']} closed before it started")
            for fld in ['t','d','x','owner']:
                if not (x[fld].get('en') and x[fld].get('ar')): bad.append(f"{x['id']} {fld} needs English and Arabic")
        if bad: ok = False; msgs.append("FAIL payroll notes: " + "; ".join(bad[:8]))
        else:
            cur = pn['current']; openn = [x for x in pn['notes'] if x['status'] == 'open' and not x.get('closedIn') and x['month'] <= cur]
            msgs.append(f"ok payroll notes valid: {len(pn['notes'])} notes, {len(openn)} open in {cur}")
    for ym, gt in (D.get('gosiBy') or {}).items():
        gs = gt['gosi']
        S = gs['summary']; bad = []
        if len(gs['rows']) != S['paid']: bad.append('row count != summary')
        if abs(sum(r['pd'] for r in gs['rows']) - S['ded_prog']) > 1: bad.append('program deduction total does not tie')
        for r in gs['rows']:
            if r['bad'] and not r['fx']: bad.append(f"{r['c']} flagged without a correction")
            for f in r['fx']:
                if not (f['en'] and f['ar']): bad.append(f"{r['c']} correction lacks a language")
            if not r['n']: bad.append(f"{r['c']} has no name")
        for o in gs['only']:
            if not (o['fx']['en'] and o['fx']['ar']): bad.append(f"{o['i']} gosi-only fix lacks a language")
        tv = gt['travel']
        if len(tv['out']) != S['out_total']: bad.append('outside-Kingdom count differs from the summary')
        for t in tv['out']:
            if t['v'] == 'ok' and t['c'] and t['pay'] and not t['ia']: bad.append(f"{t['c']} verdict ok but pay {t['pay']}")
        if bad: ok = False; msgs.append(f"FAIL gosi/travel {ym}: " + "; ".join(bad[:8]))
        else: msgs.append(f"ok gosi reconciliation {ym} valid: {len(gs['rows'])} employees, {S['bad']} need correction, {S['out_total']} outside the Kingdom")
    sl = D.get('salary')
    if sl:
        bad = []; n = sum(g[3] for g in sl['groups'])
        if abs(n - D['kpis']['HC']) > 8: bad.append(f"staff in salary groups {n} vs headcount {D['kpis']['HC']}")
        for g in sl['groups']:
            if not (g[5] <= g[4] / g[3] <= g[6] + 0.5): bad.append(f"{g[0]}/{g[1]}: average outside min-max")
            if g[1] not in sl['jobs'] or g[2] not in sl['nats'] or g[0] not in sl['branches']: bad.append(f"{g[1]} label missing")
        if bad: ok = False; msgs.append('FAIL salary screen: ' + '; '.join(bad[:8]))
        else: msgs.append(f"ok salary screen: {len(sl['groups'])} groups, {n} staff, package total {sum(g[4] for g in sl['groups']):,}")
    mv = D.get('movement')
    if mv:
        bad = []
        hm = {}; lm = {}
        for e, ym, b, j, n, c in mv['events']:
            (hm if e == 'H' else lm)[ym] = (hm if e == 'H' else lm).get(ym, 0) + c
        mo = D['months']
        # compare the dimension data with the monthly series used elsewhere (same 24 closed months, allowing one rehire or reversal)
        ym_list = [m for m in mv['months'] if m < mv['current']][-len(D['hires']):]
        for i, ym in enumerate(ym_list):
            if abs(hm.get(ym, 0) - D['hires'][i]) > 1: bad.append(f"hires {ym}: {hm.get(ym, 0)} vs series {D['hires'][i]}")
            if abs(lm.get(ym, 0) - D['leavers'][i]) > 1: bad.append(f"leavers {ym}: {lm.get(ym, 0)} vs series {D['leavers'][i]}")
        if any(r[3] is None for r in mv['events']): bad.append('job family missing')
        if bad: ok = False; msgs.append('FAIL movement analysis: ' + '; '.join(bad[:8]))
        else: msgs.append(f"ok movement analysis: {len(mv['events'])} event rows, {sum(r[5] for r in mv['events'] if r[0]=='H')} hires, {sum(r[5] for r in mv['events'] if r[0]=='L')} leavers, {sum(r[3] for r in mv['active'])} active staff by dimension")
    pp = D.get('prepay')
    if pp:
        pb_ = []
        for r in pp['rows']:
            if not r['iss'] or not r['n']: pb_.append(f"{r['c']} has no issue or no name")
            for i in r['iss']:
                if not (i['en'] and i['ar']): pb_.append(f"{r['c']} issue lacks a language")
        if gs:
            flagged = {r['c'] for r in pp['rows'] if any(i['k'] == 'out' for i in r['iss'])}
            for t in gs and D['travel']['out']:
                if t['c'] and t['op'] and t['c'] not in flagged: pb_.append(f"{t['c']} is outside the Kingdom with an October draft pay but is not flagged")
        if pb_: ok = False; msgs.append("FAIL prepay: " + "; ".join(pb_[:8]))
        else: msgs.append(f"ok pre-payroll check valid: {pp['summary']['flagged']} flagged, {pp['summary']['blocked']} to hold")
    nu = D.get('nursing')
    if nu:
        nb = []
        ks = {'none', 'none_ok', 'extra', 'ok'}
        for r in nu['doctors']:
            if r['st'] not in ks: nb.append(f"{r['c']} bad status")
            if r['k'] != len(r['nurses']): nb.append(f"{r['c']} nurse count differs")
            if r['st'] == 'none' and r['k']: nb.append(f"{r['c']} flagged no nurse but has nurses")
        listed = sum(r['k'] for r in nu['doctors']) + len(nu['orphans'])
        if listed != nu['summary']['nurses']: nb.append(f"nurses listed {listed} differs from {nu['summary']['nurses']}")
        for o in nu['orphans']:
            if not (o['why']['en'] and o['why']['ar']): nb.append(f"{o['c']} orphan lacks a language")
        if nb: ok = False; msgs.append("FAIL nursing: " + "; ".join(nb[:8]))
        else: msgs.append(f"ok nursing valid: {nu['summary']['doctors']} doctors, {nu['summary']['none']} without nurse, {nu['summary']['orphan']} nurses outside a doctor clinic")
    cm = D.get('commission')
    if cm:
        cb = []
        sm = cm['summary']
        if sm['doctors'] != len(cm['rows']): cb.append('doctor count differs from rows')
        if sm['bad'] + sm['warn'] + sm['ok'] != sm['doctors']: cb.append('status counts do not add up')
        for r in cm['rows']:
            if r['st'] not in ('bad', 'warn', 'ok'): cb.append(f"{r['s']} bad status")
            if (r['st'] == 'ok') == bool(r['iss']): cb.append(f"{r['s']} status and issues disagree")
            for i in r['iss']:
                if not (i['t']['en'] and i['t']['ar']): cb.append(f"{r['s']} issue lacks a language")
        for d in cm.get('doctors', []):
            if d['basis'] not in ('cash', 'cash_credit'): cb.append(f"{d['s']} bad basis")
        if cm.get('doctors') and len(cm['doctors']) != sm['doctors']: cb.append('doctor basis list differs from review rows')
        if cb: ok = False; msgs.append("FAIL commission: " + "; ".join(cb[:8]))
        else: msgs.append(f"ok commission review valid: {sm['doctors']} doctors, {sm['bad']} need action, {sm['warn']} notes, month {cm['month']}")
    ld = D.get('leaveDays')
    if ld:
        lb = []
        for r in ld['rows']:
            if r['tot'] != r['sick'] + r['emg'] + r['unp']: lb.append(f"{r['c']} total differs")
        sm = ld['summary']
        if sm['total'] != sm['sick'] + sm['emg'] + sm['unp']: lb.append('summary types do not add to total')
        if sm['total'] != sum(r['tot'] for r in ld['rows']): lb.append('summary total differs from rows')
        if lb: ok = False; msgs.append("FAIL leave days: " + "; ".join(lb[:8]))
        else: msgs.append(f"ok leave days valid: {sm['total']} days, {sm['docs']} doctors")
    if pn:
        nb = []
        for x in pn['notes']:
            if x['src'] == 'user': continue
            if not x.get('people'): nb.append(f"{x['id']} has no people"); continue
            for p in x['people']:
                if not (p.get('code') and p.get('name')): nb.append(f"{x['id']} person without code or name")
                if not p.get('paths') and not p.get('nopath'): nb.append(f"{x['id']} {p.get('code')} has no letter path")
        if nb: ok = False; msgs.append("FAIL notes need code, name and letter path: " + "; ".join(nb[:8]))
        else: msgs.append("ok every payroll note carries employee code, name and letter path")
    rv = D.get('review')
    if rv:
        bad = [x for x in rv['letters'] if x['s'] not in ('ok','note','err','def','fut','out')]
        if bad or not rv['letters']: ok = False; msgs.append('FAIL review screens: bad letter status')
        else: msgs.append(f"ok review screens: {len(rv['letters'])} letters, {len(rv['leaves'])} leave records, {len(rv['items'])} item rows")
    for f in D['findings']:
        for fld in ['t','e','x']:
            if not (f[fld].get('en') and f[fld].get('ar')): ok = False; msgs.append(f"FAIL finding '{f['t']['en'][:40]}' lacks Arabic in {fld}")
    return ok, msgs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--extract', required=True); ap.add_argument('--config', required=True)
    ap.add_argument('--playbook', default=os.path.join(KIT, 'config', 'playbook.json'))
    ap.add_argument('--notes', default=os.path.join(KIT, 'data', 'payroll_notes.json'))
    ap.add_argument('--labels', default=os.path.join(KIT, 'config', 'labels_ar.json'))
    ap.add_argument('--template', default=os.path.join(KIT, 'templates', 'hr_command_center.template.html'))
    ap.add_argument('--gosi', nargs='*', default=None, help='gosi_check json files, one per month (default: data/gosi_check*.json)')
    ap.add_argument('--prepay', default=os.path.join(KIT, 'data', 'prepay.json'))
    ap.add_argument('--nursing', default=os.path.join(KIT, 'data', 'nursing.json'))
    ap.add_argument('--leavedays', default=os.path.join(KIT, 'data', 'leave_days.json'))
    ap.add_argument('--movement', default=os.path.join(KIT, 'data', 'movement.json'))
    ap.add_argument('--salary', default=os.path.join(KIT, 'data', 'salary.json'))
    ap.add_argument('--review', default=os.path.join(KIT, 'data', 'review_screens.json'))
    ap.add_argument('--commission', default=os.path.join(KIT, 'data', 'commission.json'))
    ap.add_argument('--out', default='out')
    a = ap.parse_args()
    ex = json.load(open(a.extract, encoding='utf8')); cfg = json.load(open(a.config, encoding='utf8')); pb = json.load(open(a.playbook, encoding='utf8'))
    notes = json.load(open(a.notes, encoding='utf8')) if os.path.exists(a.notes) else None
    labels = json.load(open(a.labels, encoding='utf8')) if os.path.exists(a.labels) else {}
    labels.pop('_comment', None)
    load_natmap(KIT); load_orgmap(KIT)
    gfiles = a.gosi if a.gosi else sorted(__import__('glob').glob(os.path.join(KIT, 'data', 'gosi_check*.json')))
    gosi = [json.load(open(f, encoding='utf8')) for f in gfiles if os.path.exists(f)] or None
    prepay = json.load(open(a.prepay, encoding='utf8')) if os.path.exists(a.prepay) else None
    nursing = json.load(open(a.nursing, encoding='utf8')) if os.path.exists(a.nursing) else None
    leavedays = json.load(open(a.leavedays, encoding='utf8')) if os.path.exists(a.leavedays) else None
    review = json.load(open(a.review, encoding='utf8')) if os.path.exists(a.review) else None
    movement = json.load(open(a.movement, encoding='utf8')) if os.path.exists(a.movement) else None
    salary = json.load(open(a.salary, encoding='utf8')) if os.path.exists(a.salary) else None
    commission = json.load(open(a.commission, encoding='utf8')) if os.path.exists(a.commission) else None
    D, F = build(ex, cfg, pb, notes, labels, gosi, prepay, nursing, leavedays, review, movement, salary, commission)
    ok, msgs = gates(D)
    tpl = open(a.template, encoding='utf8').read()
    frag = render(D, tpl)
    page = ('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + frag + '</body></html>')
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, 'HR_Command_Center.artifact.html'), 'w', encoding='utf8').write(frag)
    open(os.path.join(a.out, 'HR_Command_Center.html'), 'w', encoding='utf8').write(page)
    json.dump(D, open(os.path.join(a.out, 'data.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    sev = {s: sum(1 for f in F if f['s'] == s) for s in 'HML'}
    md = [f"# Build {ex['asof']}", "", "## Gates"] + [f"- {m}" for m in msgs] + ["", f"## Findings: {sev['H']} high, {sev['M']} medium, {sev['L']} low", ""] + [f"- [{f['s']}] {f['t']['en']} / {f['t']['ar']}" for f in F]
    open(os.path.join(a.out, 'build.md'), 'w', encoding='utf8').write("\n".join(md) + "\n")
    print("\n".join(md))
    if not ok: sys.exit(2)

if __name__ == '__main__':
    main()
