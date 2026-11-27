#!/usr/bin/env python3
"""Demo copy of the «الإدارة المالية» Desk tab and 3D office.

Same rules as the Modeling Desk demo (CFO-Cure-Kit/scripts/demo, kit v180): the company and branches are renamed,
money ×6.25 (anon.py), insurers / TPAs keep their real names. On top of that, for the finance-department data:
  - supplier names (from the AP run's supplier_balances CSV) → «مورد 001…», plus a short list of known names;
  - evidence narrations are dropped (they can carry names), refs/dates/accounts stay, amounts scaled;
  - money fields (amount, totals that are money) scaled; counts stay.
Reads   <hub>/Finance-Dept/desk/fin-dept.js, fin-office.html  (build them first with build_desk_fin.py)
Writes  <hub>/Finance-Dept/desk/demo/fin-dept.js, fin-office.html
Usage: python build_desk_fin_demo.py --site alfaihaa [--hub <path>] [--anon <path to anon.py>]"""
import argparse, csv, glob, importlib.util, io, json, os, re, tarfile, tempfile

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--site', required=True); ap.add_argument('--hub'); ap.add_argument('--anon')
a = ap.parse_args()
site = json.load(open(os.path.join(KIT, 'config', f'site.{a.site}.json'), encoding='utf-8'))
hub = a.hub or site['folders']['hub_root']
src_dir = os.path.join(hub, 'Finance-Dept', 'desk'); out = os.path.join(src_dir, 'demo'); os.makedirs(out, exist_ok=True)

# anonymiser from the CFO-Cure demo kit (v180: insurers keep real names)
anon_path = a.anon
if not anon_path:
    tgz = os.path.join(hub, 'CFO-Cure-Kit', 'scripts', 'demo', 'demo_kit_v180.tgz')
    tmp = tempfile.mkdtemp()
    with tarfile.open(tgz) as t:
        m = [x for x in t.getmembers() if x.name.endswith('anon.py')][0]; m.name = 'anon.py'; t.extract(m, tmp)
    anon_path = os.path.join(tmp, 'anon.py')
spec = importlib.util.spec_from_file_location('anon', anon_path); anon = importlib.util.module_from_spec(spec); spec.loader.exec_module(anon)
A = anon.A

# supplier names → deterministic labels
names = {}
for f in glob.glob(os.path.join(hub, site['folders']['runs'], '*', 'ap-supplier-accountant', 'supplier_balances_*.csv')):
    with open(f, encoding='utf-8-sig') as fh:
        rd = csv.DictReader(fh)
        col = next((c for c in rd.fieldnames or [] if re.search(r'name|اسم', c, re.I)), None)
        if col:
            for r in rd:
                n = (r.get(col) or '').strip()
                if len(n) >= 3 and n not in names: names[n] = f'مورد {len(names)+1:03d}'
EXTRA = [('منازلنا', 'شركة عقارية شقيقة'), ('Manazelna', 'Sister Realty'), ('غداف', 'مورد رئيسي A'),
         ('ميغا كونستركشن', 'مقاول B'), ('ميجا كونستركشن', 'مقاول B'), ('صيدلية الشمال', 'صيدلية C'),
         ('سكوب ازرق', 'مكتب هندسي D'), ('محنشي', 'مقاول E'), ('رئيس مجلس الإدارة', 'الإدارة العليا')]
PAIRS = sorted(list(names.items()) + EXTRA, key=lambda kv: -len(kv[0]))
PERSON = re.compile(r"(?:محمد|احمد|أحمد|عبد ?ال)[؀-ۿ]*(?: [؀-ۿ]+){1,2}")

def T(s):
    if not isinstance(s, str) or not s: return s
    for k, v in PAIRS: s = s.replace(k, v)
    s = A.text(s, money=True)
    return PERSON.sub('موظف', s)

MONEY_KEY = re.compile(r'amount|balance|bal|net|gross|total|diff|vat|box|due|value|sum|debit|credit|payable|accrual|cost|price|revenue|salar|ded', re.I)
COUNT_KEY = re.compile(r'count|_n$|^n_|reviewed$|tested$|lines|items|services|suppliers_|staff|headcount|vouchers|docs|days', re.I)

def scrub(o, key=''):
    if isinstance(o, dict): return {k: (None if k == 'narration' else scrub(v, k)) for k, v in o.items()}
    if isinstance(o, list): return [scrub(v, key) for v in o]
    if isinstance(o, str): return o if key in ('id', 'severity', 'status', 'color', 'period', 'decision', 'model_used', 'model') else T(o)
    if isinstance(o, (int, float)) and not isinstance(o, bool):
        return A.S(o) if (key == 'amount' or (MONEY_KEY.search(key) and not COUNT_KEY.search(key))) else o
    return o

js = open(os.path.join(src_dir, 'fin-dept.js'), encoding='utf-8').read()
m = re.search(r'window\.FIN_DATA=(\{.*?\});\n', js, re.S)
data = json.loads(m.group(1))
demo = scrub(data); demo['site'] = 'مجموعة ديمو كير (عرض تجريبي)'
for p in demo['periods']:
    for r in p['roles']:
        r['totals'] = {k: (A.S(v) if isinstance(v, (int, float)) and MONEY_KEY.search(k) and not COUNT_KEY.search(k) else v)
                       for k, v in data['periods'][demo['periods'].index(p)]['roles'][p['roles'].index(r)]['totals'].items()}
js_demo = js[:m.start(1)] + json.dumps(demo, ensure_ascii=False, separators=(',', ':')) + js[m.end(1):]
open(os.path.join(out, 'fin-dept.js'), 'w', encoding='utf-8').write(js_demo)

# 3D office: only the replay texts (RUN = [...]) and visible company names change; scene code is untouched
h = open(os.path.join(src_dir, 'fin-office.html'), encoding='utf-8').read()
i = h.find('const RUN'); j = h.find('];', i)
if i >= 0 and j > i:
    seg = re.sub(r"'([^'\\]*)'", lambda mm: "'" + T(mm.group(1)).replace("'", "’") + "'", h[i:j])
    h = h[:i] + seg + h[j:]
h = h.replace('AI Reporting HUB · قسم', 'عرض تجريبي · قسم', 1)
open(os.path.join(out, 'fin-office.html'), 'w', encoding='utf-8').write(h)

# leak check: none of the real names may survive
left = [k for k, _ in PAIRS if k in js_demo or k in h] + [w for w in ('الفيحاء', 'Faihaa', 'بريدة', 'رفحاء') if w in js_demo or w in h]
print(f'demo written → {out} · supplier names mapped {len(names)} · leaks: {left or "none"}')
