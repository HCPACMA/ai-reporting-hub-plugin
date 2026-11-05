"""DATA.aud — accounting audit (terminated staff, control accounts, unattached JEs, VAT audit).

Positions (from the rendering JS, lines ~2673-2930 of the source page):
  vat[]  = [cc, yyyymm, salesGL, salesInvoices, creditMemos]        -> scale 2,3,4
  ctrl[] = [cc, account, yyyymm, net]                                -> scale 3
  term[] = {no: staff no, nm: name, eos: date, l: [[acct, yyyymm, net]]} -> digits / person / keep / scale l[][2]
  uj[]   = [cc, voucher, date, VMtype, subsys, userCode, narrative, debitTotal, lineCount]
                                                                     -> synth narrative, scale 7, keep 8 (shown as "Lines")
  vchk[] = [voucher, date, debit, credit, narrative, 'P']            -> scale 2,3, synth narrative
  users  = {code: "Name ( code )"}                                   -> person label, keep "( code )"
  cacc / tacc = account names (Arabic)                               -> names
Voucher narratives routinely carry people's names, so they are never kept verbatim unless they match a
strictly name-free system pattern; everything else is re-synthesised from keywords + the posting month.
"""
import re

AR_MON = ['يناير', 'فبراير', 'مارس', 'ابريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']

# user codes that are themselves a person's name -> neutral code (applied to users keys, values and uj[5])
USER_CODE_MAP = {'SHAZLY': 'USR01'}

# ---------------------------------------------------------------- name-free system narratives, kept verbatim
_D = r'[\d/\- ]+'
SAFE = [re.compile(p) for p in [
    r'Stock Dispens ?(?:\(DSP[\d\-]+\))?' + _D,
    _D,
    r'Tailor Receive' + _D,
    r'مريض خارجى نقدى (?:مرتجع مريض|فاتورة) @' + _D,
    r'Loans_payment - قرض - \d\d-\d{4}',
    r'EXPENSES\s+- (?:رسوم تحويل راتب|نسبة الاطباء|خصم الغياب|خصم التأخير|رسوم|خصم|دوام|[ء-ي ]{2,30}) - \d\d-\d{4}',
    r'ADJ-\d+-\d+',
    r'Round Variance For' + _D,
    r'مبيعات' + _D,
    r'مبيعات رقم الفاتورة [\d\-]+',
    r'رقم الفاتورة PUR[\d\-]+',
    r'م\.مشتريات RE[\d\-]+',
    r'إسنهلاك الأصول الثابتة لــ \d\d-\d{4}',
    r'مشتريات الاصول \d+',
    r'FIXED_ASSETS_VANISH \d\d-\d{4}',
    r'ايداع (?:نقدي |نقدى )?(?:في|فى|ل) ?حساب المجمع',
    r'ايداع نقدي بالحساب',
    r'بدل اجازة نقدي',
]]
# EXPENSES middle labels allowed verbatim (anything else goes through synthesis)
EXP_OK = {'رسوم تحويل راتب', 'نسبة الاطباء', 'خصم الغياب', 'خصم التأخير', 'رسوم', 'خصم', 'دوام', 'دوام اضافي',
          'بدل اجازة', 'خصم تأخير', 'اضافي'}

# ---------------------------------------------------------------- keyword categories -> neutral narrative
# (regex on the original, Arabic template); {m} = posting month "مايو 2025"
CATS = [
    (r'مطالبة الحراس|الحراسات', 'استحقاق مطالبة الحراسات الأمنية - شهر {m}'),
    (r'استحقاق مطالبة', 'استحقاق مطالبة شركة - شهر {m}'),
    (r'سداد جزء من\s*مطالبة|جزء من مطالبة', 'سداد جزء من مطالبة شركة تأمين - شهر {m}'),
    (r'\d+\s*%\s*من\s*مطالبة|نسبة من مطالبة', 'سداد نسبة من مطالبة شركة تأمين - شهر {m}'),
    (r'تصفية شركة|مرفوضات', 'سداد تصفية مطالبات شركة تأمين - شهر {m}'),
    (r'مطالبة جمعية', 'سداد مطالبة جمعية - شهر {m}'),
    (r'مطالبة', 'سداد مطالبة شركة تأمين - شهر {m}'),
    (r'بوليصة', 'تعديل بوليصة التأمين الطبي للموظفين - شهر {m}'),
    (r'عجز', 'سداد عجز ايراد الصندوق'),
    (r'ايداع|إيداع|ايداع', 'ايداع نقدي بالحساب'),
    (r'شيك', 'سحب شيك لصندوق الإدارة'),
    (r'احضار|إحضار|احضارالمبلغ|لصندوق|صندوق', 'تحويل نقدية لصندوق الإدارة'),
    (r'حوالة واردة|حواله واردة', 'حوالة واردة'),
    (r'عمولة|رسوم تحويل|رسوم  تحويل', 'عمولة تحويل بنكي'),
    (r'سلف', 'سلفة موظف'),
    (r'قرض|قسط', 'سداد قسط'),
    (r'بدل\s*(?:ال)?[اأإ]جاز[ةه]|مخصص بدل الا[جح]ازة', 'بدل اجازة موظف'),
    (r'تصفية|كامل المستحق|كامل مستحقات|نهاية خدمة|نهاية الخدمة|مكافأة نهاية|مكافاة نهاية', 'سداد مستحقات نهاية خدمة موظف'),
    (r'مكافأة|مكافاة', 'استحقاق مكافأة - شهر {m}'),
    (r'رواتب|راتب', 'سداد رواتب وبدلات - شهر {m}'),
    (r'نسبة|نسب ', 'استحقاق نسبة الاطباء - شهر {m}'),
    (r'اضافي|اضافى|إضافي', 'استحقاق اضافي - شهر {m}'),
    (r'علاوة', 'استحقاق فرق علاوة - شهر {m}'),
    (r'مستحقات|المستحق', 'سداد مستحقات موظف'),
    (r'بدل سفر|تذكرة|تذكره|طيران', 'قيمة تذكرة سفر موظف'),
    (r'تأمينات|التامينات|التأمينات', 'قيمة التأمينات الاجتماعية - شهر {m}'),
    (r'ادوية عن شهر|أدوية عن شهر', 'ادوية عن شهر {m}'),
    (r'ادوية|أدوية|دواء', 'مسحوبات ادوية - شهر {m}'),
    (r'ايجار|إيجار', 'قيمة ايجار - شهر {m}'),
    (r'كهرباء', 'سداد فاتورة كهرباء - شهر {m}'),
    (r'مياه|المياه', 'قيمة مياه للمجمع - شهر {m}'),
    (r'اتصالات|هاتف|جوال|انترنت|إنترنت', 'سداد فاتورة اتصالات - شهر {m}'),
    (r'محروقات|بنزين|وقود', 'قيمة فاتورة محروقات'),
    (r'زيت', 'قيمة غيار زيت سيارة المجمع'),
    (r'سيار', 'قيمة صيانة سيارة المجمع'),
    (r'شحن نقاط|منصة|منصه', 'قيمة شحن نقاط منصة خدمات حكومية'),
    (r'استقدام', 'رسوم استقدام'),
    (r'ممارس|رخص|ترخيص|تعقيب|وزارة|جوازات|اقامة|إقامة|تأشير|الغرفة التجارية|تجديد|تصديق|بلدية', 'رسوم حكومية وتراخيص'),
    (r'ضريبة القيمة|هيئة الزكاة', 'قيد ضريبة القيمة المضافة - شهر {m}'),
    (r'زكاة|زكاه', 'صرف زكاة'),
    (r'مصروف البيت|مصروف للبيت|منزل|البيت', 'مصروفات منزلية'),
    (r'اهلاك|إهلاك|استهلاك', 'اثبات مصروف اهلاك - شهر {m}'),
    (r'نظافة|نظافه', 'اغراض نظافة من المستودع - شهر {m}'),
    (r'اكسجين|أكسجين', 'قيمة تعبئة اكسجين'),
    (r'تحاليل|مختبر|تحليل', 'قيمة تحاليل مخبرية'),
    (r'صيانة|صيانه|قطع غيار|تصليح', 'قيمة صيانة'),
    (r'تركيبات', 'استحقاق قيمة تركيبات'),
    (r'اقفال|إقفال', 'قيد اقفال حساب - شهر {m}'),
    (r'عهدة|عهده', 'عهدة نقدية موظف'),
    (r'شراء|مشتريات|فاتورة شراء', 'قيمة مشتريات'),
    (r'رد مبلغ|مراجع', 'رد مبلغ لمراجع'),
    (r'عكس', 'قيد عكسي - شهر {m}'),
    (r'تسوية|فرق|فروق', 'قيد تسوية فروقات - شهر {m}'),
    (r'فاتورة|فواتير', 'سداد فاتورة مورد'),
    (r'اشتراك', 'رسوم اشتراك - شهر {m}'),
    (r'اتعاب|أتعاب', 'اتعاب مهنية'),
    (r'عقد', 'سداد قيمة عقد خدمات'),
    (r'خصم', 'قيمة خصم - شهر {m}'),
    (r'نقل|شحن|ليموزين|لموزين|تاكسي', 'مصاريف نقل وشحن'),
    (r'ضيافة|شاي|قهوة|قهوه', 'قيمة مستلزمات ضيافة'),
    (r'اكل|غداء|افطار|إفطار', 'قيمة وجبات طعام'),
    (r'سكن', 'قيمة ايجار سكن'),
]
CATS = [(re.compile(p), t) for p, t in CATS]

# fallback by voucher prefix (BR bank receipt, BP bank payment, CR cash receipt, CP cash payment, JV journal)
PREFIX = {
    'BR': 'مقبوضات بنكية - شهر {m}', 'BP': 'مدفوعات بنكية - شهر {m}',
    'CR': 'مقبوضات نقدية - شهر {m}', 'CP': 'مصروفات نقدية متنوعة - شهر {m}',
    'JV': 'قيد يومية - تسوية حسابات - شهر {m}',
}

# VAT-suspect keywords shown by the page (line ~2897); keep one in the synthesised text
VCHK_T = [
    ('محروقات', 'قيمة فاتورة محروقات سيارة المجمع'),
    ('زيت', None),  # special-cased
    ('سياره', 'قيمة صيانة سياره المجمع'),
    ('سيارات', 'قيمة صيانة سيارات المجمع'),
    ('ضيافة', 'قيمة مستلزمات ضيافة (شاي وقهوة)'),
    ('شاي', 'قيمة شاي وقهوة للضيافة'),
    ('قهوة', 'قيمة قهوة للضيافة'),
    ('قهوه', 'قيمة قهوه للضيافة'),
    ('سكن', 'قيمة إيجار سكن لموظف أثناء مهمة عمل'),
    ('منزل', 'مصروفات قسم الرعاية المنزلية'),
    ('سكر', None),  # special-cased
    ('افطار', 'قيمة وجبة افطار'),
    ('إفطار', 'قيمة وجبة إفطار'),
    ('غداء', 'قيمة وجبة غداء'),
    ('غدا', 'قيمة وجبة غدا'),
    ('اكل', 'قيمة اكل وضيافة'),
]


def _mon(date):
    try:
        y, m = int(date[:4]), int(date[5:7])
        return '%s %d' % (AR_MON[m - 1], y)
    except Exception:
        return ''


def _synth(s, voucher, date, A):
    s0 = re.sub(r'\s+', ' ', s or '').strip()
    m = _mon(date)
    if not s0:
        return s
    # verbatim system patterns (no people possible)
    for p in SAFE:
        if p.fullmatch(s0):
            if s0.startswith('EXPENSES'):
                mid = re.sub(r'^EXPENSES\s+- | - \d\d-\d{4}$', '', s0).strip()
                if mid not in EXP_OK:
                    break
            return A.text(s, money=False)
    # structured patterns: keep the id part, drop the person
    x = re.match(r'VAT_CREDIT_NOTE_FROM (\d\d-\d\d-\d{4}) الي (\d\d-\d\d-\d{4})', s0)
    if x:
        kind = 'خصم على مطالبة شركة تأمين'
        if 'تعجيل' in s0:
            kind = 'خصم تعجيل الدفع'
        elif 'حجم' in s0:
            kind = 'عمولة حجم تعامل'
        elif 'مرفوض' in s0 or 'تصفية' in s0:
            kind = 'مرفوضات تصفية مطالبة'
        elif 'كريديت' in s0 or 'ملف' in s0:
            kind = 'إشعار دائن لمراجع'
        return 'VAT_CREDIT_NOTE_FROM %s الي %s %s' % (x.group(1), x.group(2), kind)
    x = re.match(r'الايراد اليومى للشفت (\d+)', s0)
    if x:
        return 'الايراد اليومى للشفت %s' % x.group(1)
    x = re.fullmatch(r'سلفة للموظف (\d+)', s0)
    if x:
        return 'سلفة للموظف %s' % A.digits(x.group(1))
    for p, t in CATS:
        if p.search(s0):
            return t.format(m=m)
    pre = re.match(r'[A-Z]+', voucher or '')
    t = PREFIX.get(pre.group(0) if pre else '', 'قيد يومية - شهر {m}')
    return t.format(m=m)


def _vchk_synth(s, voucher, date, A):
    for kw, t in VCHK_T:
        if kw in (s or ''):
            if kw == 'زيت':
                return 'قيمة زيت تعطير لأجهزة التعطير' if ('عطر' in s or 'تعطير' in s) else 'قيمة غيار زيت سيارة المجمع'
            if kw == 'سكر':
                return 'قيمة سكر زاوية لأعمال السباكة' if ('زاوية' in s or 'غاز' in s or 'سباك' in s) else 'قيمة سكر وشاي للضيافة'
            return t
    return _synth(s, voucher, date, A)


def _user_val(v, A):
    x = re.match(r'^(.*?)\s*(\(\s*[^()]*\s*\))\s*$', v)
    if not x:
        return A.person(v, 'user')
    name, code = x.group(1), x.group(2)
    for k, n in USER_CODE_MAP.items():
        code = code.replace(k, n)
    if name.lower().startswith('central database user'):
        return name + ' ' + code
    return A.person(name, 'user') + ' ' + code


def transform(d, A):
    S = A.S
    for r in d.get('vat', []):
        r[2], r[3], r[4] = S(r[2]), S(r[3]), S(r[4])
    for r in d.get('ctrl', []):
        r[3] = S(r[3])
    for t in d.get('term', []):
        t['no'] = A.digits(t['no'])
        t['nm'] = A.person(t['nm'], 'emp')
        for l in t['l']:
            l[2] = S(l[2])
    for r in d.get('uj', []):
        r[5] = USER_CODE_MAP.get(r[5], r[5])
        r[6] = _synth(r[6], r[1], r[2], A)
        r[7] = S(r[7])
        # r[8] = voucher line count -> keep
    for r in d.get('vchk', []):
        r[2], r[3] = S(r[2]), S(r[3])
        r[4] = _vchk_synth(r[4], r[0], r[1], A)
    if 'users' in d:
        d['users'] = {USER_CODE_MAP.get(k, k): _user_val(v, A) for k, v in d['users'].items()}
    for k in ('cacc', 'tacc'):
        if k in d:
            d[k] = {a: A.names(v) for a, v in d[k].items()}
    if 'src' in d:
        d['src'] = A.names(d['src'])
    return d
