"""HR Command Center DEMO builder.
Fictional names, money x6.25, counts/dates/codes unchanged. Mirrors the CFO Modeling Desk demo conventions.
Usage (from HR-Cure-Kit):  python3 scripts/demo/hr_demo.py [--out ../Demo]
"""
import os, sys, re, json, copy, hashlib, argparse
HERE = os.path.dirname(os.path.abspath(__file__)); KIT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(KIT, 'scripts'))
import anon as AN
from build_hr import render

K = 6.25
ARB = re.compile(r'[\u0600-\u06FF]')

# ------------------------------------------------------------------ company / branch names (restricted subset)
_en_end = next(i for i, (p, r) in enumerate(AN._EN) if p == 'Bupa')
_ar_end = next(i for i, (a, r) in enumerate(AN._AR) if a == 'رفحا')
EN = [(re.compile(p, re.I), r) for p, r in AN._EN[:_en_end] if 'Riyad\\s+Bank' not in p]
EN += [(re.compile(r'\bHany\b', re.I), 'Finance Lead'), (re.compile(r'\bBur\s*([12])\b', re.I), r'Eastgate \1'), (re.compile(r'Gameel', re.I), 'Demo')]
AR = [(re.compile(re.escape(a)), r) for a, r in AN._AR[:_ar_end + 1] if a != 'بنك الرياض'] + [(re.compile(r'(?<![ء-ي])هاني(?![ء-ي])'), 'مسؤول المالية')]

def brand(s):
    for p, r in EN: s = p.sub(r, s)
    if ARB.search(s):
        for p, r in AR: s = p.sub(r, s)
    return s

# ------------------------------------------------------------------ money
MONEY = [r'^(basic|plus|minus|gosiCo|gosiSt|absD|ot)\[\]$', r'^branches\[\]\.sal$', r'^jobs\[\]#2$', r'^earn\[\]#1$', r'^ded\[\]#1$', r'^loanRows\[\]#4$',
         r'^gl\.(eosb|leave|pay|estB|estW)$', r'^kpis\.(salRoll|saudiSal|nonSaudiSal|loanLeaverPending)$', r'^plan\.cost$',
         r'^payroll\.notes\[\]\.amt$',
         r'^gosi\.rows\[\]\.(pb|ph|ps|gb|gh|gt|at|af|pd|ad|ge)$', r'^gosi\.summary\.(ded_prog|ded_acct|ded_gosi_exp)$', r'^gosi\.only\[\]\.w$', r'^gosi\.noacct\[\]\.g$',
         r'^travel\.out\[\]\.(pay|op)$', r'^travel\.nostatus\[\]\.pay$',
         r'^salary\.groups\[\]#[4-9]$', r'^prepay\.rows\[\]\.(gross|ded|net)$', r'^prepay\.summary\.amount_blocked$',
         r'^nursing\.doctors\[\]\.(cost|sal)$', r'^nursing\.doctors\[\]\.nurses\[\]\.sal$', r'^nursing\.orphans\[\]\.sal$', r'^nursing\.summary\.(nurse_cost|nurse_cost_orphan)$',
         r'^review\.items\[\]\.amt$',
         r'^commission\.rows\[\]\.(cashS|cashC|credS|credC|med|comm|pay)$', r'^commission\.rows\[\]\.cure_br\.[^.]+$',
         r'^commission\.doctors\[\]\.(cashS|credS|comm|mn)$', r'^commission\.outside\[\]\.(cash|cred|med)$', r'^commission\.outside\[\]\.br\.[^.]+$',
         r'^commission\.unmatched\[\]\.amt$', r'^commission\.summary\.(sheet_total|paid_total|unmatched_amt)$']
MONEY = [re.compile(p) for p in MONEY]

def norm_path(p):
    p = p.lstrip('.')
    p = re.sub(r'^gosiBy\.[\d-]+\.', '', p)
    p = re.sub(r'^commissions\.[\d-]+\b', 'commission', p)
    return p

def is_money(p): return any(m.match(p) for m in MONEY)

def S(x):
    if isinstance(x, bool) or x is None or not isinstance(x, (int, float)): return x
    v = round(x * K, 2)
    return int(v) if v == int(v) and isinstance(x, int) else v

# ------------------------------------------------------------------ people
SKIP_FIELDS = {'rel', 'win', 'lbl', 'file', 'folder', 'day', 'frm', 'to', 'ret', 'vm', 'start', 'month', 'mo', 'period', 'id', 'closedIn', 'asOfReview', 'asof', 'current'}
CODE_KEYS = ('s', 'st', 'code', 'c', 'emp')
NAME_KEYS = ('n', 'name', 'tn')
HON = r'(?:د\s*[./]\s*|د\.\s*|الدكتور[ةه]?\s+|Dr\.?\s+|Doctor\s+)?'
FUZZ = {'ا': '[اأإآ]', 'أ': '[اأإآ]', 'إ': '[اأإآ]', 'آ': '[اأإآ]', 'ه': '[هة]', 'ة': '[هة]', 'ى': '[ىي]', 'ي': '[ىي]'}

def k_is_dash(c): return c in ('—', '-', '', None)

def tokpat(t): return ''.join(FUZZ.get(c, re.escape(c)) for c in t)

EXTRA = ['حمزة', 'Reema Alhudathi', 'Hailah Mohamed', 'Hamad Alanazi', 'Majed Alanezi', 'Nasser Alomran', 'Samah Alshahrani', 'Alhanouf Aldosari', 'Aljawhara Alanazi',
         'Yousef Tarek', 'Ziyad Alharbi', 'Ruby Alharbi', 'Said Eid', 'Eslam Abdelatif', 'هيلان جريس', 'حمزة الحمزه', 'يوسف طارق ابراهيم']

class People:
    def __init__(self, D, names_json):
        self.pairs = {}            # name(normalised) -> code
        self.nsyn = 0
        self.docs = set()
        self.codes = set()
        self._collect(D, [])
        for c, n in names_json.items(): self._add(c, n)
        for r in D['commission']['rows'] + D['nursing']['doctors']:
            self.docs.add(r.get('s') or r['c'])
        for r in D['leaveDays']['rows']:
            if r.get('grp') == 'doc': self.docs.add(r['c'])
        for n in EXTRA: self.syn(n)
        self.build()

    @staticmethod
    def nz(n): return re.sub(r'\s+', ' ', n.strip())

    def _add(self, c, n):
        if not (isinstance(c, str) and re.fullmatch(r'\d{1,5}|X\d{3}', c) and isinstance(n, str) and n.strip()): return
        n = self.nz(n)
        if re.fullmatch(r'[\d\W]+', n): return
        if c[0] != 'X': self.codes.add(c)
        self.pairs.setdefault(n, c)

    def syn(self, n):
        if not isinstance(n, str) or not n.strip() or re.fullmatch(r'[\d\W]+', n.strip()): return
        n = self.nz(n)
        if n in self.pairs: return
        if re.fullmatch(r'(?:HQ|BUR|Rafha|Riyadh).*', n): return
        self.nsyn += 1; self.pairs[n] = 'X%03d' % self.nsyn

    def _collect(self, v, path):
        if isinstance(v, dict):
            code = next((v[k] for k in CODE_KEYS if isinstance(v.get(k), str) and re.fullmatch(r'\d{3,5}', v[k])), None)
            if code:
                for k in NAME_KEYS:
                    if isinstance(v.get(k), str): self._add(code, v[k])
            else:
                path_s = '.'.join(path)
                if re.search(r'(gosi|travel|people|ppl|prepay|nursing|leaveDays|review|commission)', path_s) and any(k in v for k in ('i', 'c', 'code', 'st', 's')):
                    for k in NAME_KEYS:
                        if isinstance(v.get(k), str): self.syn(v[k])
                if 'code' in v and k_is_dash(v.get('code')) and isinstance(v.get('name'), str): self.syn(v['name'])
                if isinstance(v.get('name'), str) and re.fullmatch(r'\d+-.+', v['name']): self.syn(re.sub(r'^\d+-\s*', '', v['name']))
            for k, x in v.items(): self._collect(x, path + [k])
        elif isinstance(v, list):
            for x in v: self._collect(x, path)

    def label(self, name, code):
        ar = bool(ARB.search(name)); doc = code in self.docs
        if code[0] == 'X': return ('موظف ' if ar else 'Employee ') + code
        if doc: return ('د. ديمو ' if ar else 'Dr. Demo ') + code
        return ('موظف ' if ar else 'Employee ') + code

    def build(self):
        entries = {}  # normalised name -> code
        for n, c in self.pairs.items():
            entries[n] = c
            n2 = re.sub(r'^(?:د\s*[./]\s*|د\.\s*|Dr\.?\s+)', '', n).strip()
            if n2 != n and n2: entries.setdefault(n2, c)
        # contiguous pair variants for long names, only when unique
        pv = {}
        for n, c in list(entries.items()):
            t = n.split()
            if len(t) >= 3:
                for i in range(len(t) - 1):
                    pv.setdefault(' '.join(t[i:i + 2]), set()).add(c)
                pv.setdefault(t[0] + ' ' + t[-1], set()).add(c)
        full = set(entries)
        for v, cs in pv.items():
            if len(cs) == 1 and len(v) >= 8 and v not in full: entries[v] = next(iter(cs))
        self.entries = entries
        alts = []
        for n in sorted(entries, key=lambda x: -len(x)):
            alts.append('(?:' + r'\s+'.join(tokpat(t) for t in n.split()) + ')')
        self.lab = {}
        for n, c in entries.items(): self.lab[re.sub(r'\s+', ' ', n).lower()] = (n, c)
        self.rx = re.compile(r'(?<![ء-يA-Za-z0-9])([لبوفك]?)(' + HON + ')(' + '|'.join(alts) + r')(?![ء-يA-Za-z0-9])', re.I)

    def sub(self, s):
        def f(m):
            nm = re.sub(r'\s+', ' ', m.group(3)).lower()
            hit = self.lab.get(nm)
            if not hit:   # fuzzy letters: find by normalising
                nn = self._canon(nm); hit = self.canon.get(nn)
            if not hit: return m.group(0)
            n, c = hit
            return m.group(1) + self.label(n, c)
        return self.rx.sub(f, s)

    def _canon(self, s): return re.sub('[أإآ]', 'ا', s).replace('ة', 'ه').replace('ى', 'ي')

    def finish(self):
        self.canon = {self._canon(k): v for k, v in self.lab.items()}
        return self

# ------------------------------------------------------------------ text money
CUR_A = re.compile(r'^\s?(?:SAR|SR|ريال|ر\.س|ر\.\s?س)', re.I)
CUR_B = re.compile(r'(?:SAR|SR|ريال|≈|~)\s?$', re.I)
UNIT_A = re.compile(r'^\s?(?:%|days?\b|يوم|أيام|ايام|hours?\b|h\b|ساعة|ساعات|rows?\b|صف|صفوف|staff|employees?|موظف|records?|سجل|سجلات|months?\b|شهر|أشهر|of\b|من\b|doctors?|nurses?|طبيب|ممرض|cases?|حالة|حالات|items?|files?|letters?|خطاب|ملف|people|persons?|تعيين|عقد|contracts?|iqama|هوية)', re.I)
PROT_L = re.compile(r'(?:records?|سجلات|سجل|loans?|قرض|قروض|JV)\s?\d{3,5}(?:\s?(?:,|،|and|و|/)\s?\d{3,5})*\s?(?:,|،|and|و)\s?$', re.I)
PROT_B = re.compile(r'(?:record|سجل|loan|قرض|#|JV|type|نوع|item|بند|رقم|id|no\.?|code|كود|cost centre|مركز تكلفة|v|rows? of|of|من|top|first|last|[Pp]age|ص|صفحة)\s?$', re.I)
NUM = re.compile(r'(?<![\w/.:#\-])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+)(?![\w/:]|-\d|\.\d)')

def scale_notes(s):
    def f(m):
        o = m.group(0)
        if re.fullmatch(r'\d{1,3}\.\d{3}', o):
            return f"{int(o.replace('.', '')) * K:,.0f}".replace(',', '.')
        v = float(o.replace(',', ''))
        if v < 500 or re.fullmatch(r'20[12]\d', o) and not re.match(r'\s?(ريال|SAR)', s[m.end():m.end() + 6]): return o
        return fmt(o, v * K)
    return re.sub(r'(?<![\d/.:])\d{1,3}(?:,\d{3})+(?:\.\d+)?|(?<![\d/.:])\d+(?:\.\d+)?(?![\d%])(?!\s?%)', f, s)

def fmt(orig, v):
    dec = len(orig.split('.')[1]) if '.' in orig else 0
    if v != int(v) or dec: dec = 2
    return (f"{v:,.{dec}f}" if ',' in orig else f"{v:.{dec}f}")

def scale_text(s, plain, codes):
    def f(m):
        o = m.group(1); st, en = m.span(1)
        before, after = s[max(0, st - 14):st], s[en:en + 14]
        if o.startswith('0') and '.' not in o and len(o) > 1: return o
        cur = bool(CUR_A.match(after) or CUR_B.search(before))
        if not cur and UNIT_A.match(after): return o
        if ',' in o or '.' in o:
            if o.count('.') == 1 and ',' not in o and len(o.split('.')[1]) == 1 and not cur: return o   # 1.5 style
            return fmt(o, float(o.replace(',', '')) * K)
        if cur: return fmt(o, int(o) * K)
        if plain and 3 <= len(o) <= 6:
            if o in codes or re.fullmatch(r'(19|20)\d\d', o) or PROT_B.search(before) or PROT_L.search(s[max(0, st - 40):st]): return o
            return fmt(o, int(o) * K)
        return o
    return NUM.sub(f, s)

PLAIN_FIELDS = re.compile(r'^(payroll\.notes\[\]\.(t|d|x)\.(en|ar)|payroll\.tables\..*|review\.letters\[\]\.(letter|sys|action)|review\.items\[\]\.note|commission\.rows\[\]\.iss\[\]\.t\.(en|ar)|gosi\.rows\[\]\.fx\[\]\.(en|ar)|gosi\.only\[\]\.fx\.(en|ar)|prepay\.rows\[\]\.iss\[\]\.(en|ar))')

# ------------------------------------------------------------------ transform
def transform(D, names_json):
    P = People(D, names_json).finish()
    codes = P.codes
    docs_clinic = re.compile(r'(?:Dr\.?\s+.+?\s+Clinic|عيادة\s+(?:د\.?|الدكتور)\s*[^,;()]+)', re.I)
    stats = {'money': 0, 'strings': 0}
    LET = 'C:\\Demo\\Letters'

    def mask_ids(s):
        return re.sub(r'(?<![\d/.-])\d{10,}(?![\d/])', lambda m: AN.A.digits(m.group(0)), s)

    def pstr(s, path, key, parent):
        stats['strings'] += 1
        if key in ('rel', 'lbl') and (ARB.search(s) or re.search(r'[A-Za-z]{4}', s)):
            return brand(P.sub(s))
        if key in ('rel',): return s
        if key == 'win':
            rl = parent.get('rel', '')
            if ARB.search(rl) or re.search(r'[A-Za-z]{4}', rl): rl = brand(P.sub(rl))
            return LET + '\\' + rl.replace('/', '\\')
        if key == 'file' and path.startswith('payroll.notes[].ppl'): return parent.get('code', 'letter') + '.pdf'
        if path == 'payroll.letters_base': return LET
        if path.startswith('gosi.sources.gosi'): return 'Demo/GOSI/Branch-file.csv'
        if path == 'gosi.sources.travel': return 'Demo/Travel/Travel-status.xlsx'
        if key in SKIP_FIELDS and key != 'file': return s
        if key in NAME_KEYS and s.strip():
            code = next((parent[k] for k in CODE_KEYS if isinstance(parent.get(k), str) and re.fullmatch(r'\d{3,5}', parent[k])), None)
            if code and code in codes: return P.label(s, code)
            hit = P.pairs.get(P.nz(s))
            if hit: return P.label(s, hit)
        if re.fullmatch(r'[\d\-/:.\s]+', s): return mask_ids(s) if len(re.sub(r'\D', '', s)) >= 10 else s
        if key == 'on' and path.startswith('nursing') and re.match(r'\s*Dr\b', s, re.I):
            return (P.label('Dr', parent['c']) if parent.get('c') in P.docs else AN.A.person(s, 'dr')) + ' Clinic'
        if path == 'commission.unmatched[].name':
            m = re.fullmatch(r'(\d+)-\s*(.+)', s)
            if m and m.group(1) in codes: return m.group(1) + '-' + P.label(m.group(2), m.group(1))
            if m and P.pairs.get(P.nz(m.group(2))): return m.group(1) + '-' + P.label(m.group(2), P.pairs[P.nz(m.group(2))])
        s = P.sub(s)
        s = brand(s)
        s = scale_notes(s) if path == 'commission.doctors[].note' else scale_text(s, bool(PLAIN_FIELDS.match(path)), codes)
        return mask_ids(s)

    # dict walker needs the parent for sibling lookups -> second pass with sibling access
    def walk2(v, path, key=None, parent=None):
        np_ = norm_path(path)
        if isinstance(v, dict):
            out = {}
            for k, x in v.items():
                nk = k
                if isinstance(k, str) and not re.fullmatch(r'[\d\-.]+', k): nk = brand(k)
                out[nk] = walk2(x, path + '.' + k, k, v)
            return out
        if isinstance(v, list):
            out = []
            for x in v:
                if isinstance(x, list) and len(x) <= 40:
                    out.append([walk2(y, path + '[]#' + str(i)) for i, y in enumerate(x)])
                else: out.append(walk2(x, path + '[]'))
            return out
        if isinstance(v, str): return pstr(v, np_, key, parent or {})
        if is_money(np_) and isinstance(v, (int, float)) and not isinstance(v, bool):
            stats['money'] += 1; return S(v)
        return v
    R = walk2(D, '')
    # fix-ups
    R['payroll']['letters_base'] = LET
    return R, P, stats

# ------------------------------------------------------------------ template patch
def patch_template(t):
    def rep(a, b, n=1):
        nonlocal t
        assert t.count(a) >= 1, a[:60]
        t = t.replace(a, b) if n == 0 else t.replace(a, b, n)
    # branch display (lines using literal branch names)
    lines = t.split('\n')
    for i, l in enumerate(lines):
        if ('Riyadh' in l and ("BRN=" in l or "'BUR1'" in l)) :
            lines[i] = brand(l)
    t = '\n'.join(lines)
    rep('<title>Human Resources</title>', '<title>HR Command Center Demo</title>')
    rep('<b>Al Faihaa</b><small>Medical Center</small>', '<b>Demo Care</b><small>Medical Center</small>')
    rep('<span class="cu-av">HG</span><b>هاني جميل</b>', '<span class="cu-av">DU</span><b>مستخدم تجريبي</b>')
    rep('مجمع الفيحاء الطبي - الرياض (مجموعة الفيحاء للخدمات الطبية) هاني جميل', 'مجمع ديمو كير الطبي - المركزي (مجموعة ديمو كير للخدمات الطبية) مستخدم تجريبي')
    rep('<style>', '<style>\n.demo-bn{background:#fde68a;color:#5b4300;border-bottom:2px solid #d9a400;padding:7px 14px;font:600 13px/1.4 system-ui,sans-serif;text-align:center;position:relative;z-index:50}.demo-bn b{background:#5b4300;color:#fde68a;border-radius:4px;padding:1px 7px;margin:0 6px;letter-spacing:.5px}\n', 1)
    rep('document.body.insertBefore(hd,document.body.firstChild);',
        "var bn=document.createElement('div');bn.className='demo-bn';bn.innerHTML='<span dir=ltr><b>DEMO DATA</b> Fictional names; amounts are scaled and do not reflect any real company.</span> &nbsp;&nbsp;|&nbsp;&nbsp; <span dir=rtl><b>بيانات تجريبية</b> أسماء وهمية والمبالغ معدّلة ولا تعكس أي شركة حقيقية</span>';document.body.insertBefore(hd,document.body.firstChild);document.body.insertBefore(bn,hd);")
    return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(KIT, '..', 'Demo'))
    a = ap.parse_args()
    D = json.load(open(os.path.join(KIT, 'out', 'data.json'), encoding='utf8'))
    nm = json.load(open(os.path.join(KIT, 'data', 'names.json'), encoding='utf8'))
    R, P, st = transform(D, nm)
    R['meta']['demo'] = True
    json.dump(R, open(os.path.join(KIT, 'out', 'data.demo.json'), 'w', encoding='utf8'), ensure_ascii=False)
    tpl = patch_template(open(os.path.join(KIT, 'templates', 'hr_command_center.template.html'), encoding='utf8').read())
    frag = render(R, tpl)
    page = ('<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light}body{margin:0;font:14px system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>' + frag + '</body></html>')
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(KIT, 'out', 'HR_Command_Center_Demo.artifact.html'), 'w', encoding='utf8').write(frag)
    open(os.path.join(a.out, 'HR_Command_Center_Demo.html'), 'w', encoding='utf8').write(page)
    print('names', len(P.pairs), 'variants', len(P.entries), 'money fields scaled', st['money'], 'strings', st['strings'])

if __name__ == '__main__':
    main()
