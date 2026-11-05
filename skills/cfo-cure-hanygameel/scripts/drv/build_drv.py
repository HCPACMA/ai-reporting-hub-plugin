# DATA.drv — Deep Analysis driver payload. Posted + open vouchers from all four EXSYS ledgers,
# invoice visits/revenue from the invoice tables. Months Jan 2024 – open month.
import json, re, collections, datetime as dt, sys
sys.path.insert(0, '../gl')
H = open('../AlFaihaa_Modeling_Desk.html', encoding='utf-8').read()
def grab(n): return json.loads(re.search(r'\nDATA\.' + n + r' = (.*);\n', H).group(1))
IF = grab('ifrs')
import os
# data are complete through ASOF (default: yesterday); the month of ASOF is the open month
ASOF = dt.date.fromisoformat(os.environ['DRV_ASOF']) if os.environ.get('DRV_ASOF') else dt.date.today() - dt.timedelta(days=1)
OPEN = '%d-%02d' % (ASOF.year, ASOF.month)
M = ['%d-%02d' % (y, m) for y in range(2024, ASOF.year + 1) for m in range(1, 13)]
M = [m for m in M if m <= OPEN]; MI = {m: i for i, m in enumerate(M)}; N = len(M)
yy = lambda ym: '20' + ym[:2] + '-' + ym[2:] if len(ym) == 4 else ym[:4] + '-' + ym[4:]
# ---------- ledger P&L by account x cost-centre prefix x function
S = collections.defaultdict(lambda: [0.0] * N)
for br, a, cc, f, ym, v in json.load(open('gl_all.json')):
    if a[0] not in '34': continue
    m = ym[:4] + '-' + ym[4:]
    if m in MI: S['%s|%s|%s' % (a, cc, f)][MI[m]] += v
ser = {k: [round(x) for x in v] for k, v in S.items() if any(abs(x) >= 1 for x in v)}
ACCN = json.load(open('../gl/acc_names.json'))
acc = {}
for k in ser:
    a = k.split('|')[0]
    if a not in acc:
        e = IF['acc'].get(a)
        acc[a] = [e[0], e[1]] if e else [ACCN.get(a, a), '']
nat = [[g[0], g[1], g[2], g[3]] for g in IF['nat']]
# ---------- departments by month (cost-centre ledger)
AR = json.load(open('../gl/org_names.json'))
EN = {'02101':'Outpatient reception','02102':"Children's clinics",'02103':'General practice','02104':'Dermatology',
 '02106':'Obstetrics & gynaecology','02107':'ENT','02109':'Dialysis','02110':'Home care','02111':'Physiotherapy',
 '02113':'Ophthalmology','02115':'Orthopaedics','02118':'Chest','02121':'Internal medicine','02122':'Dental',
 '02123':'Urology','02124':'Laser clinics','02125':'Surgery','02126':'Neurology','023':'Laboratory','024':'Radiology',
 '025':'Emergency & dressing','026':'Pharmacy','027':'Health certificates','028':'Branch activity costs','029':'Vaccinations'}
def dept_of(cc):
    if cc[:2] == '00': return '00ZZ'
    if len(cc) >= 5 and cc[2:4] == '02':
        x = cc[:7]
        return x if len(x) == 7 and x[4] == '1' else x[:5]
    return cc[:2] + 'ZZ'                                   # non-clinical cost centres of the branch
D = collections.defaultdict(lambda: [[0.0] * N, [0.0] * N, [0.0] * N])
for br, rows in json.load(open('cc_all.json')).items():
    for ym, cc, ca, cr, dr, ccr in rows:
        m = yy(ym)
        if m not in MI: continue
        d = D[dept_of(cc)]; i = MI[m]
        d[0][i] += float(ca); d[1][i] += float(cr); d[2][i] += float(dr) - float(ccr)
dept = {}; dser = {}
for k, v in D.items():
    if not any(abs(x) >= 1 for s in v for x in s): continue
    nm_en = ('All head-office cost centres' if k == '00ZZ' else 'Non-clinical & shared') if k.endswith('ZZ') else EN.get(k[2:], AR.get(k, k))
    dept[k] = [k[:2], nm_en, '' if k.endswith('ZZ') else AR.get(k, '')]
    dser[k] = [[round(x) for x in s] for s in v]
# ---------- visits and invoice revenue by branch x payment type x specialty x doctor
names = json.load(open('../anomdb/doc_names.json')); names.update(json.load(open('../anomdb/doc_names_extra.json')))
V = collections.defaultdict(lambda: [[0] * N, [0] * N, [0] * N])
for br, ym, pt, did, sp, eps, n1, n2 in json.load(open('vis_all.json')):
    m = yy(ym)
    if m not in MI: continue
    v = V[(br, pt, sp.strip() or '-', names.get(did, did))]; i = MI[m]
    v[0][i] += int(float(eps)); v[1][i] += round(float(n1)); v[2][i] += round(float(n2))
vis = [[b, p, s, d] + v for (b, p, s, d), v in V.items() if any(v[1]) or any(v[0])]
unnamed = sorted(set(r[3] for r in vis if re.fullmatch(r'\d+', str(r[3]))))
DRV = {'m': M, 'open': MI.get(OPEN), 'openDay': ASOF.day, 'asOf': ASOF.isoformat(),
       'br': {'00': 'Head office', '01': 'Riyadh', '02': 'Buraydah 1', '03': 'Buraydah 2', '04': 'Rafha'},
       'ser': ser, 'acc': acc, 'nat': nat, 'dept': dept, 'dser': dser, 'vis': vis,
       'src': 'EXSYS ledgers (GL_TRANSACTIONS_DETAILS, posted and open vouchers; cancelled, year-end closing and JV1-24/04043 excluded) and invoice tables (RC_PATIENT_INVOICES / CHARGES less refunds), all four databases'}
json.dump(DRV, open('data_drv.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print('months', M[0], M[-1], 'open', DRV['open'], 'ser', len(ser), 'acc', len(acc), 'dept', len(dept), 'vis', len(vis), 'unnamed', unnamed[:20])
import os; print('bytes', os.path.getsize('data_drv.json'))
# ---------- ties: NI and revenue per month vs ledger rebuild
ni = [0.0] * N; rev = [0.0] * N
for k, v in ser.items():
    a = k.split('|')[0]
    for i, x in enumerate(v):
        ni[i] -= x
        if a[:2] in ('41', '42') and a != '4200027': rev[i] -= x
yr = collections.Counter(); yn = collections.Counter()
for i, m in enumerate(M): yr[m[:4]] += rev[i]; yn[m[:4]] += ni[i]
print({k: round(v) for k, v in yr.items()}, {k: round(v) for k, v in yn.items()})
