"""DATA.cost — service costing (ER & Lab costing map) + service profitability grid.

Rendering (AlFaihaa_Modeling_Desk.html ~L3637-4000):
  svn[code] = [service name, specialty code]              -> names only
  grn[grp]  = customer group (insurer / payer) name        -> fictional payer names
  dcn[br][code] = doctor name                               -> A.person(.., 'dr')  (non-person labels kept)
  spn       = specialty names                               -> names only
  uc[code]  = [unit cost SAR, status, dept, n items, n bad, last dispense date, chk flag]
  map[]     = [svc, item code, item name, share (ratio), tests (count), old item cost SAR,
               last dispense cost SAR, date, service share of cost SAR, status, qty dispensed, n dispenses, note]
  gz        = base64(gzip(JSON {br: '|'-joined 12 columns of ','-joined values}))
              cols: 0 ym b36, 1 sv b36, 2 gr b36, 3 ct, 4 dc b36, 5 sp b36, 6 q, 7 qg (free qty),
                    8 val SAR (gross before discount), 9 ds SAR (discount), 10 ps SAR (patient share), 11 iv (invoice lines)
"""
import base64, gzip, json, re

# payer / customer-group names not (or badly) covered by anon.names — keyed by original string
_GRN = {
    "تكافل الراجحي للتامين": "تكافل كاي للتامين",
    "الاثير للخدمات الصحيه": "نوفا للخدمات الصحيه",
    "سهام لادارة الرعايه الصحيه": "كوازار لادارة الرعايه الصحيه",
    "بي ام كير السعوديه": "بلسار كير السعوديه",
    "لا بأس الصحه للتامين": "نيبولا الصحه للتامين",
    "ميدجلف للتامين": "جاما للتامين",
    "شركة بوبا العربية للتأمين التعاوني": "شركة ألفا للتأمين التعاوني",
}

# doctor-table entries that are departments / placeholders, not people
_NON_PERSON = re.compile(r'^(Doctor\b|Home Care$|Vaccination Department$|Health Certifications$|Laser Department$)', re.I)
_DR_PREFIX = re.compile(r'^\s*(?:Dr\s*[./]\s*|Dr\s+|Doctor\s+)', re.I)

_MONEY_COLS = (8, 9, 10)


def _num_str(v):
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def transform(d, A):
    K = A.S(1.0)                       # 6.25; used directly to keep 4-dp unit costs precise
    P = lambda x, nd=6: x if x is None or isinstance(x, bool) or not isinstance(x, (int, float)) else round(x * K, nd)

    # ---- labels
    d['brn'] = {k: A.names(v) for k, v in d.get('brn', {}).items()}
    d['svn'] = {k: [A.names(v[0])] + v[1:] for k, v in d.get('svn', {}).items()}
    d['spn'] = {k: A.names(v) for k, v in d.get('spn', {}).items()}
    d['grn'] = {k: _GRN.get(v, A.names(v)) for k, v in d.get('grn', {}).items()}
    dcn = {}
    for br, docs in d.get('dcn', {}).items():
        out = {}
        for code, name in docs.items():
            if not isinstance(name, str) or _NON_PERSON.match(name.strip()):
                out[code] = A.names(name)
            else:
                out[code] = A.person(_DR_PREFIX.sub('', name).strip(), 'dr')
        dcn[br] = out
    d['dcn'] = dcn

    # ---- unit cost per service
    for code, u in d.get('uc', {}).items():
        u[0] = P(u[0])

    # ---- costing map rows
    for m in d.get('map', []):
        m[2] = A.names(m[2])
        m[5] = P(m[5]); m[6] = P(m[6]); m[8] = P(m[8])
        # m[3] share, m[4] tests, m[10] qty dispensed, m[11] dispense count, m[12] note ("400 test") -> keep

    # ---- packed invoice grid
    if isinstance(d.get('gz'), str) and d['gz'].startswith('H4sI'):
        packed = json.loads(gzip.decompress(base64.b64decode(d['gz'])).decode('utf-8'))
        for br, s in packed.items():
            cols = s.split('|')
            for ci in _MONEY_COLS:
                vals = cols[ci].split(',')
                cols[ci] = ','.join(v if v in ('', '0') else _num_str(float(v) * K) for v in vals)
            packed[br] = '|'.join(cols)
        raw = json.dumps(packed, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        d['gz'] = base64.b64encode(gzip.compress(raw, compresslevel=9, mtime=0)).decode('ascii')
    return d
