"""Shared anonymiser + scaler for the Modeling Desk demo.

Every rules_<blob>.py module gets an instance `A` of Anon and must call only these helpers:

  A.S(x)            money -> x * 6.25 (rounded to 2 dp); None/'' pass through; non-numbers pass through
  A.names(s)        replace company / branch / insurer / TPA / bank / peer names in a string (no number changes)
  A.text(s, money=True)
                    names(s) + mask IBANs / long digit refs / VAT numbers / EXTN refs, and (if money=True)
                    scale money-looking numbers written in the text (1,234.56 · 1234.56 · 1,234 · 12.3M / 450K)
  A.person(s, role) deterministic fictional person label; role in {'dr','emp','user','person','pt'}
                    e.g. 'Dr. Demo 017' / 'Employee 0231' / 'User 07'.  Arabic input -> Arabic label.
  A.digits(s)       deterministic same-length digit mask for identifiers (file no., IBAN tails, bank refs, VAT no.)
  A.ref(s)          mask an alphanumeric bank reference (keeps length / prefix shape)

Money = SAR amounts, prices, costs, balances, revenue per visit, fees, tax amounts.
NOT money = counts, visits, days, quantities, ratios/percent/margins/multiples, years, yyyymm, dates,
            account / org / customer codes, model parameters (orders, coefficients, sigma of log models, z-scores).
"""
import re, hashlib

K = 6.25

# ---------------------------------------------------------------- entity table
# (pattern, replacement) — applied in order; English patterns are case-insensitive.
# Longer / more specific phrases first.
_EN = [
    # company & people
    (r"Al[\s\-]?Faihaa?h?(?:\s+Medical)?(?:\s+Group)?", "Demo Care"),
    (r"AL[\s\-]?FAIHAA?", "DEMO CARE"),
    (r"ALFAIHAA?", "DEMOCARE"),
    (r"Faihaa?group", "democaregroup"),
    (r"Faihaa?", "Demo Care"),
    (r"Hany\s+Gameel", "Finance Lead"),
    # branches (display names and codes)
    (r"Buraydah\s*1|Buraidah\s*1|BURAIDA\s*1|BURAYDAH\s*1|Bur-1|Buraydah-1", "Eastgate 1"),
    (r"Buraydah\s*2|Buraidah\s*2|BURAIDA\s*2|BURAYDAH\s*2|Bur-2|Buraydah-2", "Eastgate 2"),
    (r"Buraydah|Buraidah|Buraida|Burayda|Qassim|Al[\s-]?Qassim", "Eastgate"),
    (r"\bBURA\b", "EASTG"),
    (r"Riyad\s+Bank", "Bank Four"),
    (r"Riyadh|Riyad\b", "Central"),
    (r"Rafha", "Northfield"),
    (r"\bBUR1\b", "EG1"), (r"\bBUR2\b", "EG2"), (r"\bRUH\b", "CEN"), (r"\bRAF\b", "NTH"),
    # insurers / TPAs / payers
    (r"Bupa", "Alpha"),
    (r"Tawuniya|Tawuniyah|Al[\s-]?Tawuniya", "Beta"),
    (r"Med[\s-]?Gulf|Mediterranean\s+(?:and|&)\s+Gulf", "Gamma"),
    (r"SAICO|Saudi\s+Arabian\s+Cooperative\s+Insurance", "Delta"),
    (r"Malath", "Epsilon"),
    (r"Saudi\s+Aramco|Aramco", "Zeta Energy"),
    (r"Al[\s-]?Etihad|Etihad", "Eta"),
    (r"Buruj", "Theta"),
    (r"Alinma\s+Tokio\s+Marine|Tokio\s+Marine", "Kappa"),
    (r"Arabian\s+Shield", "Lambda"),
    (r"Arabia\s+Insurance", "Mu Insurance"),
    (r"Wafa", "Nu"),
    (r"Amana", "Xi"),
    (r"Salama", "Omicron"),
    (r"Walaa", "Rho"),
    (r"Al[\s-]?Jazira\s+Takaful|Aljazira\s+Takaful", "Sigma Takaful"),
    (r"NEXt\s?CARE", "OrbitTPA"),
    (r"Globe\s?Med", "VertexTPA"),
    (r"Med\s?Net", "PrismTPA"),
    (r"Total\s+Care(?:\s+Saudi)?", "SummitTPA"),
    (r"Nat\s?Health", "HelixTPA"),
    (r"Al[\s-]?Sagr|Alsagr", "Tau"),
    (r"Mutakamela", "Upsilon"),
    (r"Saudi\s+Enaya|Enaya", "Phi"),
    (r"Al[\s-]?Rajhi\s+Takaful|Al[\s-]?Rajhi\s+(?:Cooperative\s+)?Insurance", "Chi Takaful"),
    (r"Gulf\s+Union(?:\s+Al\s?Ahlia)?|GULF\s+UNION\s+ALAHLIA", "Omega"),
    (r"Gulf\s+Insurance\s+Group|\bGIG\b", "Psi Group"),
    (r"Gulf\s+General", "Oscar"),
    (r"Royal\s*(?:&|and)\s*Sun\s*Alliance|Allianz", "Kilo"),
    (r"Allied\s+Cooperative\s+Insurance\s+Group|\bACIG\b", "Lima"),
    (r"Sinopec", "Quebec Petroleum"),
    (r"Cigna", "Romeo"),
    (r"Orient\s+Insurance", "Sierra Insurance"),
    (r"\bAXA\b", "Victor"),
    (r"Wataniya", "Whiskey"),
    (r"Solidarity", "Yankee"),
    (r"Chubb", "Zulu"),
    # banks
    (r"Arab\s+National\s+Bank|\bANB\b", "Bank Seven"),
    (r"Gulf\s+International\s+Bank|Gulf\s+Internationa\w*", "Bank Ten"),
    (r"Saudi\s+National\s+Bank|\bSNB\b|National\s+Commercial\s+Bank|\bNCB\b|Al\s?Ahli\s+Bank|Alahli\s+Bank|\bNational\s+Bank", "Bank One"),
    (r"The\s+Saudi\s+British\s+Bank|Saudi\s+British\s+Bank|\bSABB\b", "Bank Two"),
    (r"Al[\s-]?Rajhi(?:\s+Bank)?", "Bank Three"),
    (r"Riyad\s+Bank", "Bank Four"),
    (r"Alinma(?:\s+Bank)?", "Bank Five"),
    (r"Al[\s-]?Bilad(?:\s+Bank)?|Bank\s+Albilad", "Bank Six"),
    (r"Saudi\s+Investment\s+Bank|\bSAIB\b", "Bank Eight"),
    (r"Bank\s+Al[\s-]?Jazira|Aljazira\s+Bank", "Bank Nine"),
    (r"Al[\s-]?Ahli(?:a)?\b|Alahli|Alahlia", "Bank One"),
    (r"Sulaiman\s+Al[\s-]?Habib|Al[\s-]?Habib", "Peer Alpha"),
    (r"Mouwasat", "Peer Beta"),
    (r"Dallah", "Peer Gamma"),
    (r"Al[\s-]?Hammadi", "Peer Delta"),
    (r"Care\s+Shield|National\s+Medical\s+Care", "Peer Epsilon"),
    (r"Saudi\s+German", "Peer Zeta"),
    (r"Middle\s+East\s+Healthcare|\bMEAHCO\b", "Peer Zeta"),
    (r"Al[\s-]?Mowasat", "Peer Beta"),
    (r"Apollo\s+Hospitals|Apollo", "Intl Peer A"),
    (r"Sigma\s+Healthcare", "Intl Peer B"),
    (r"\bHMG\b", "PA"),
    (r"Tibbiyah|Arabian\s+International\s+Healthcare", "Excluded Peer 2"),
    (r"Scientific\s+and\s+Medical\s+Equipment\s+House", "Excluded Peer 1"),
    (r"Al[\s-]?Razi(?:\s+Medical)?", "Excluded Peer 3"),
]
_AR = [
    ("مجموعة الفيحاء", "مجموعة ديمو كير"), ("الفيحاء", "ديمو كير"), ("الفيحا", "ديمو كير"), ("فيحاء", "ديمو كير"),
    ("هاني جميل", "مسؤول المالية"),
    ("بريدة 1", "البوابة الشرقية 1"), ("بريدة 2", "البوابة الشرقية 2"),
    ("بريده 1", "البوابة الشرقية 1"), ("بريده 2", "البوابة الشرقية 2"),
    ("بريدة1", "البوابة الشرقية 1"), ("بريدة2", "البوابة الشرقية 2"),
    ("بريده1", "البوابة الشرقية 1"), ("بريده2", "البوابة الشرقية 2"),
    ("بريدة", "البوابة الشرقية"), ("بريده", "البوابة الشرقية"), ("القصيم", "الإقليم الشرقي"),
    ("بنك الرياض", "البنك الرابع"),
    ("الرياض", "المركزي"), ("رياض", "المركزي"),
    ("رفحاء", "الحقل الشمالي"), ("رفحا", "الحقل الشمالي"),
    # insurers / TPAs — specific phrases first
    ("إتحاد الخليج الأهليه", "أوميجا"), ("إتحاد الخليج الأهلية", "أوميجا"), ("اتحاد الخليج الاهلية", "أوميجا"),
    ("إتحاد الخليج", "أوميجا"), ("اتحاد الخليج", "أوميجا"),
    ("مجموعة الخليج للتأمين", "مجموعة بساي للتأمين"), ("الخليجية للتأمين", "أوسكار للتأمين"), ("الخليجية العامة", "أوسكار"),
    ("المتوسط والخليج", "جاما"), ("ميدغلف", "جاما"), ("ميد غلف", "جاما"),
    ("التعاونية للتامين", "بيتا للتأمين"), ("التعاونية للتأمين", "بيتا للتأمين"), ("التعاونيه للتأمين", "بيتا للتأمين"),
    ("العربية السعوديه للتأمين", "دلتا للتأمين"), ("العربية السعودية للتأمين", "دلتا للتأمين"),
    ("سايكو", "دلتا"), ("ملاذ", "إبسيلون"),
    ("الزيت العربيه السعوديه", "زيتا للطاقة"), ("الزيت العربية السعودية", "زيتا للطاقة"), ("أرامكو", "زيتا"), ("ارامكو", "زيتا"),
    ("الإتحاد للتأمين", "إيتا للتأمين"), ("الاتحاد للتأمين", "إيتا للتأمين"), ("الاتحاد للتامين", "إيتا للتأمين"), ("الإتحاد للتامين", "إيتا للتأمين"),
    ("بروج", "ثيتا"),
    ("المجموعة المتحدة للتأمين", "ليما للتأمين"), ("المتحدة للتأمين", "يوتا للتأمين"),
    ("الأنماء طوكيو مارين", "كابا"), ("الإنماء طوكيو مارين", "كابا"), ("طوكيو مارين", "كابا"),
    ("الدرع العربي", "لامدا"),
    ("التأمين العربية التعاونية", "ميو للتأمين التعاوني"), ("العربية للتأمين", "ميو للتأمين"),
    ("وفاء للتأمين", "نيو للتأمين"), ("وفاء", "نيو"),
    ("أمانه", "زاي"), ("أمانة", "زاي"), ("امانة", "زاي"), ("امانه", "زاي"),
    ("سلامة", "أوميكرون"), ("سلامه", "أوميكرون"),
    ("الاهليه للتأمين", "باي للتأمين"), ("الأهلية للتأمين", "باي للتأمين"), ("الاهلية للتأمين", "باي للتأمين"),
    ("ولاء", "رو"),
    ("الجزيره تكافل", "سيجما تكافل"), ("الجزيرة تكافل", "سيجما تكافل"),
    ("نكست كير", "أوربت"), ("نكستكير", "أوربت"), ("نكست", "أوربت"),
    ("جلوب ميد", "فيرتكس"), ("جلوبميد", "فيرتكس"), ("جلوب", "فيرتكس"),
    ("ميدنت", "بريزم"), ("ميد نت", "بريزم"),
    ("العناية الشاملة", "سميت"), ("العنايه الشامله", "سميت"), ("عناية شاملة", "سميت"),
    ("ناتهيلث", "هيليكس"), ("نات هيلث", "هيليكس"),
    ("الصقر", "تاو"),
    ("متكاملة", "أبسيلون"), ("متكامله", "أبسيلون"),
    ("عنايه السعوديه", "فاي"), ("عناية السعودية", "فاي"), ("عناية السعوديه", "فاي"),
    ("الراجحي للتأمين", "كاي للتأمين"), ("الراجحي تكافل", "كاي تكافل"), ("مصرف الراجحي", "البنك الثالث"), ("الراجحي", "البنك الثالث"),
    ("رويال اند صن اليانز", "كيلو"), ("اليانز", "كيلو"),
    ("أسيج", "ليما"), ("اسيج", "ليما"),
    ("صينوبك انترناشيونال بتروليوم سيرفيس كوربوريشن", "كيبيك للخدمات البترولية"), ("صينوبك", "كيبيك"),
    ("سيجنا وورلدو ايد انشورنس", "روميو العالمية للتأمين"), ("سيجنا", "روميو"),
    ("اورينت", "سييرا"), ("أورينت", "سييرا"),
    ("الخلية المتقدمة التشخيصية", "تانجو للتشخيص"),
    ("بوبا", "ألفا"),
    # banks
    ("البنك الأهلي السعودي", "البنك الأول"), ("البنك الاهلي السعودي", "البنك الأول"), ("البنك الأهلي", "البنك الأول"),
    ("البنك الاهلي", "البنك الأول"), ("الأهلي", "الأول"), ("الاهلي", "الأول"),
    ("البنك السعودي البريطاني", "البنك الثاني"), ("ساب", "البنك الثاني"),
    ("مصرف الإنماء", "البنك الخامس"), ("بنك البلاد", "البنك السادس"), ("البلاد", "البنك السادس"),
    ("البنك العربي الوطني", "البنك السابع"), ("البنك السعودي للاستثمار", "البنك الثامن"), ("بنك الجزيرة", "البنك التاسع"),
    ("الحبيب", "بير ألفا"), ("المواساة", "بير بيتا"), ("دله", "بير جاما"), ("دلة", "بير جاما"), ("الحمادي", "بير دلتا"),
]
_EN_C = [(re.compile(p, re.I), r) for p, r in _EN]
# Arabic: "ساب" must be a whole word
_AR_C = []
for a, r in _AR:
    if a in ("ساب", "رياض", "دله", "دلة", "وفاء", "ولاء", "نكست", "جلوب", "الأهلي", "الاهلي", "البلاد", "سلامة", "سلامه", "أمانه", "أمانة", "امانة", "امانه", "الصقر", "بروج", "ملاذ"):
        _AR_C.append((re.compile(r'(?<![ء-ي])' + re.escape(a) + r'(?![ء-ي])'), r))
    else:
        _AR_C.append((re.compile(re.escape(a)), r))

_AR_RE = re.compile(r'[؀-ۿ]')


def _h(s, n=8):
    return int(hashlib.md5(str(s).encode('utf-8')).hexdigest(), 16) % (10 ** n)


class Anon:
    def __init__(self):
        self.people = {}      # (role, key) -> label
        self.counters = {}

    # -------------------------------------------------- numbers
    def S(self, x):
        if isinstance(x, bool) or x is None:
            return x
        if isinstance(x, (int, float)):
            return round(x * K, 2)
        return x

    # -------------------------------------------------- names
    def names(self, s):
        if not isinstance(s, str) or not s:
            return s
        for p, r in _EN_C:
            s = p.sub(r, s)
        if _AR_RE.search(s):
            for p, r in _AR_C:
                s = p.sub(r, s)
        return s

    def digits(self, s):
        """Same-length deterministic digit mask; keeps non-digits."""
        if s is None:
            return s
        s = str(s)
        d = re.sub(r'\D', '', s)
        if not d:
            return s
        h = hashlib.sha256(s.encode()).hexdigest()
        rep = ''.join(str(int(c, 16) % 10) for c in (h * 4))[:len(d)]
        it = iter(rep)
        return ''.join(next(it) if c.isdigit() else c for c in s)

    def ref(self, s):
        if not isinstance(s, str) or not s:
            return s
        h = hashlib.sha256(s.encode()).hexdigest().upper()
        out, i = [], 0
        for c in s:
            if c.isdigit():
                out.append(str(int(h[i % 64], 16) % 10)); i += 1
            elif c.isalpha() and c.isascii():
                ch = h[i % 64]; i += 1
                out.append(chr(65 + int(ch, 16) % 26) if c.isupper() else chr(97 + int(ch, 16) % 26))
            else:
                out.append(c)
        # keep a recognisable EXTN prefix
        if s.startswith('EXTN'):
            return 'EXTN' + ''.join(out[4:])
        return ''.join(out)

    def person(self, s, role='person'):
        if s is None or s == '':
            return s
        key = re.sub(r'\s+', ' ', str(s).strip())
        k = (role, key)
        if k in self.people:
            return self.people[k]
        n = self.counters.get(role, 0) + 1
        self.counters[role] = n
        ar = bool(_AR_RE.search(key))
        lab = {
            'dr':    ('د. ديمو %03d' if ar else 'Dr. Demo %03d') % n,
            'emp':   ('موظف %04d' if ar else 'Employee %04d') % n,
            'user':  ('مستخدم %02d' if ar else 'User %02d') % n,
            'pt':    ('مريض %05d' if ar else 'Patient %05d') % n,
            'person': ('شخص %04d' if ar else 'Person %04d') % n,
        }.get(role, ('شخص %04d' if ar else 'Person %04d') % n)
        self.people[k] = lab
        return lab

    # -------------------------------------------------- free text
    _IBAN = re.compile(r'\bSA\d{2}[\d ]{18,26}\b')
    _EXTN = re.compile(r'\b(?:EXTN|FT|CRF:?)[A-Z0-9]{6,}\b')
    _LONGD = re.compile(r'(?<![\d/.-])\d{9,}(?![\d/])')
    _MONEY = re.compile(r'(?<![\w/.:-])(-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+\.\d{2})(?![\w%/-]|\.\d)')
    _MK = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)\s?(M|K|mn|bn)\b')

    def _fmt_like(self, orig, v):
        dec = len(orig.split('.')[1]) if '.' in orig else 0
        if ',' in orig:
            return f"{v:,.{dec}f}"
        return f"{v:.{dec}f}"

    def text(self, s, money=True):
        if not isinstance(s, str) or not s:
            return s
        s = self.names(s)
        s = self._IBAN.sub(lambda m: self.digits(m.group(0)), s)
        s = self._EXTN.sub(lambda m: self.ref(m.group(0)), s)
        s = self._LONGD.sub(lambda m: self.digits(m.group(0)), s)
        if money:
            s = self._MONEY.sub(lambda m: self._fmt_like(m.group(1), float(m.group(1).replace(',', '')) * K), s)
            s = self._MK.sub(lambda m: self._fmt_like(m.group(1), float(m.group(1)) * K) + ('' if m.group(2) in ('mn', 'bn') else '') + m.group(2), s)
        return s


A = Anon()
