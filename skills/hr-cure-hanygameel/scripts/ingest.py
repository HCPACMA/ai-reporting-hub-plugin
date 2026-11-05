#!/usr/bin/env python3
"""Turn the saved Cure MCP replies (raw/<job>.txt) into the extract file that build_hr.py reads.

    python3 ingest.py --raw raw/ --config config/company.<co>.json --asof 2026-10-12 --out data/extract.<co>.<date>.json

A raw file is the text the cure_run_query tool returned (an ASCII table), or the JSON wrapper {"result": "..."}.
Jobs and their columns are documented at the top of each sql/hrNN_*.sql file.
"""
import argparse, json, os, re, datetime as dt

def parse_table(text):
    text = text.strip()
    if text.startswith('{'):
        try: text = json.loads(text)['result']
        except Exception: pass
    rows, header = [], None
    for ln in text.splitlines():
        if not ln.startswith('|'): continue
        cells = [c.strip() for c in ln.strip().strip('|').split('|')]
        if header is None: header = [c.lower() for c in cells]; continue
        d = {}
        for h, c in zip(header, cells):
            d[h] = None if c == '' else c   # keep text as text: codes such as '00' and '09' must not become numbers
        rows.append(d)
    return rows

def load(raw, name, required=True):
    p = os.path.join(raw, name + '.txt')
    if not os.path.exists(p):
        if required: raise SystemExit(f"missing raw/{name}.txt - run sql/{name}*.sql")
        return None
    return parse_table(open(p, encoding='utf8').read())

def ym_of(y, m): return f"{int(float(y))}-{int(float(m)):02d}"
def add_months(y, m, k):
    t = y*12 + (m-1) + k; return t // 12, t % 12 + 1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True); ap.add_argument('--config', required=True); ap.add_argument('--asof', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--months', type=int, default=24)
    a = ap.parse_args()
    cfg = json.load(open(a.config, encoding='utf8')); asof = dt.date.fromisoformat(a.asof)
    R = lambda n, req=True: load(a.raw, n, req)
    i = lambda v: int(round(float(v or 0)))

    # ---- payroll header: window of closed months, draft month detection ----
    ph = R('hr05a_payroll_header_monthly')
    ph = [r for r in ph]
    draft = None
    rows = {}
    for r in ph:
        ym = ym_of(r['y'], r['m']); rows[ym] = r
    last = max(rows)
    if float(rows[last]['notposted'] or 0) and float(rows[last]['notposted']) >= float(rows[last]['stf']):
        draft = last
    closed = sorted(k for k in rows if k != draft)[-a.months:]
    ym = closed
    pick = lambda col: [i(rows[k][col]) for k in ym]
    D = {}
    for r in R('hr05b_payroll_items_monthly'):
        D[(ym_of(r['y'], r['m']), r['sg'])] = i(r['amt'])
    plus = [D.get((k, '+'), 0) for k in ym]; minus = [D.get((k, '-'), 0) for k in ym]
    unposted = {k: i(rows[k]['notposted']) for k in ym if i(rows[k]['notposted'])}

    hires_map = {r['ym']: i(r['hires']) for r in R('hr07_hires_monthly')}
    lv_map = {r['lm']: i(r['n']) for r in R('hr08_leavers_last_pay')}

    # ---- branches ----
    names = {b['k']: b['name'] for b in cfg['branches']}
    b1 = {r['br']: r for r in R('hr01a_branch_summary')}
    sal = {}
    for r in R('hr01b_branch_salary'):
        sal.setdefault(r['br'], 0); sal[r['br']] += i(r['sal'])
    saudi_sal = sum(i(r['sal']) for r in R('hr01b_branch_salary') if r['sa'] == 'S')
    non_sal = sum(i(r['sal']) for r in R('hr01b_branch_salary') if r['sa'] == 'N')
    branches = [dict(k=k, n=names.get(k, k), h=i(r['n']), f=i(r['fem']), s=i(r['saudi']), sal=sal.get(k, 0)) for k, r in sorted(b1.items())]
    HC = sum(b['h'] for b in branches)

    jobs = [[r['job'] or 'Unclassified', i(r['n']), i(r['avg_sal'])] for r in R('hr02_job_families')]

    ages = {}
    for r in R('hr03_age_bands'):
        b = int(float(r['age_b'])); lab = 'Under 20' if b < 20 else '60 and over' if b >= 60 else f"{b} to {b+9}"
        ages[lab] = ages.get(lab, 0) + i(r['n'])
    order = ['Under 20', '20 to 29', '30 to 39', '40 to 49', '50 to 59', '60 and over']
    age = [[k, ages[k]] for k in order if k in ages]
    if HC - sum(v for _, v in age) > 0: age.append(['Birth date missing', HC - sum(v for _, v in age)])

    def tb(y):
        y = int(float(y))
        return 'Under 1 year' if y < 1 else '1 to 2 years' if y < 2 else '2 to 3 years' if y < 3 else '3 to 5 years' if y < 5 else '5 to 8 years' if y < 8 else '8 to 10 years' if y < 10 else '10 to 15 years' if y < 15 else '15 years and over'
    ten = {}
    for r in R('hr04_tenure'): ten[tb(r['ten_y'])] = ten.get(tb(r['ten_y']), 0) + i(r['n'])
    tord = ['Under 1 year', '1 to 2 years', '2 to 3 years', '3 to 5 years', '5 to 8 years', '8 to 10 years', '10 to 15 years', '15 years and over']
    tenure = [[k, ten.get(k, 0)] for k in tord]

    items = R('hr06_items_last_month')
    earn = [[r['en'] or f"Item {i(r['si'])}", i(r['amt'])] for r in items if r['sg'] == '+']
    ded = [[r['en'] or f"Item {i(r['si'])}", i(r['amt'])] for r in items if r['sg'] == '-']
    loan_ded = sum(i(r['n']) for r in items if i(r['si']) == -1)

    # ---- contracts ----
    cm = sorted((r['exp_y'], i(r['n'])) for r in R('hr09_contract_end_months'))
    cur = f"{asof.year}-{asof.month:02d}"
    fut = [x for x in cm if x[0] > cur][:6]
    def short(ymm): y, m = ymm.split('-'); return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][int(m)-1] + (f" {y[2:]}" if int(m) == 1 or ymm == fut[0][0] else '')
    exp_months = [short(x[0]) for x in fut]; exp_n = [x[1] for x in fut]
    cs = R('hr10_contract_status')
    cnt = lambda e: sum(i(r['n']) for r in cs if r['st'] == 'A' and r['cc'] == 'Y' and r['e'] == e)
    expired_contracts, open_ended = cnt('PAST'), cnt('BLANK')

    # ---- ids ----
    idrows = R('hr11_id_expiry')
    idm = {r['b']: i(r['n']) for r in idrows if r['tp'] == 'RES'}
    pm = {r['b']: i(r['n']) for r in idrows if r['tp'] == 'PASSPORT'}
    idb = [['Valid beyond 6 months', idm.get('OK', 0), 'good'], ['Expired', idm.get('EXPIRED', 0), 'bad'], ['Expires in 91 to 180 days', idm.get('D180', 0), 'warn'],
           ['Expires in 31 to 90 days', idm.get('D90', 0), 'warn'], ['Expires within 30 days', idm.get('D30', 0), 'warn'], ['No expiry date', idm.get('NOEXP', 0), 'b']]
    idb = [x for x in idb if x[1] or x[0] in ('Expired', 'No expiry date')]
    passport = dict(expired=pm.get('EXPIRED', 0), soon=pm.get('D30', 0) + pm.get('D90', 0) + pm.get('D180', 0), noexp=pm.get('NOEXP', 0), ok=pm.get('OK', 0))

    c = R('hr12_completeness')[0]
    mc = dict(licence=i(c['no_lic']), probation=i(c['no_prob']), dss=i(c['no_dss']), gosi=i(c['no_gosi']), email=i(c['no_email']), dob=i(c['no_dob']), nat=i(c['no_nat']), idrec=i(c['no_id']))
    miss = [['Professional licence ID', mc['licence']], ['Probation days', mc['probation']], ['Service start date (master)', mc['dss']], ['GOSI date', mc['gosi']],
            ['Email', mc['email']], ['Birth date', mc['dob']], ['ID record', mc['idrec']], ['Nationality', mc['nat']], ['Salary record', i(c['no_sal'])]]

    # ---- leave ----
    lrows = R('hr13_leave_summary')
    st = {'P': 'Posted', 'C': 'Cancelled', 'O': 'Open'}
    leave_rows = [[str(int(float(r['y']))), str(r['vt']), st.get(r['pf'], r['pf']), i(r['n']), i(r['days'])] for r in lrows]
    lt, sh = cfg['leave_types']['long'], cfg['leave_types']['short']
    ch = {}
    for r in lrows:
        if r['pf'] != 'P': continue
        y = str(int(float(r['y']))); ch.setdefault(y, [0, 0, 0])
        k = 0 if str(r['vt']) == lt else 1 if str(r['vt']) == sh else 2
        ch[y][k] += i(r['days'])
    leave_chart = [[y] + v for y, v in sorted(ch.items()) if int(y) <= asof.year]
    ol = {r['k']: r for r in R('hr14_open_leave_and_loan_holders')}

    # ---- loans ----
    lab = {'P': 'Paid (P)', 'R': 'Rescheduled (R)', 'N': 'Pending (N)'}
    loan_rows = []
    for who, wl in [('ACTIVE', 'Active staff'), ('LEAVER', 'Leavers')]:
        for s in ['P', 'R', 'N']:
            for r in R('hr15_loan_installments'):
                if r['who'] == who and r['st'] == s: loan_rows.append([wl, lab[s], i(r['n']), i(r['stf']), i(r['amt'])])

    gl = {r['acc']: -i(r['net']) for r in R('hr16_gl_provisions')}
    e = R('hr17_eosb_estimate')[0]
    acc = cfg['accounts']
    glx = dict(eosb=gl.get(acc['eosb'], 0), leave=gl.get(acc['leave'], 0), pay=gl.get(acc['payables'], 0), estB=i(e['eosb_basic']), estW=i(e['eosb_totwage']))

    out = dict(
        asof=a.asof, ym=ym, draftMonth=draft, leaverMethod='lastpay',
        staffPaid=pick('stf'), basic=pick('basic'), plus=plus, minus=minus, gosiCo=pick('gosi_co'), gosiSt=pick('gosi_st'), absD=pick('abs_d'), ot=pick('ot'),
        hires=[hires_map.get(k, 0) for k in ym], leavers=[lv_map.get(k, 0) for k in ym],
        branches=branches, jobs=jobs, age=age, tenure=tenure, earn=earn, ded=ded, expMonths=exp_months, expN=exp_n,
        leaveRows=leave_rows, leaveChart=leave_chart, loanRows=loan_rows, miss=miss, idb=idb, gl=glx,
        HC=HC, saudi=sum(b['s'] for b in branches), female=sum(b['f'] for b in branches), salRoll=sum(b['sal'] for b in branches),
        saudiSal=saudi_sal, nonSaudiSal=non_sal,
        expiredContracts=expired_contracts, openEnded=open_ended, expiredIds=idm.get('EXPIRED', 0), idSoon=idm.get('D30', 0) + idm.get('D90', 0) + idm.get('D180', 0), idNoExpiry=idm.get('NOEXP', 0), idValid=idm.get('OK', 0), passport=passport,
        unpostedByMonth=unposted, loanDedStaff=loan_ded, loanHoldersActive=i(ol['loans_open_active_staff']['n']), leaverLoanStaff=i(ol['loans_on_leavers']['n']),
        openLeaveRecords=i(ol['open_leaves']['n']), openLeaveDays=i(ol['open_leaves']['v']), missCounts=mc)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('wrote', a.out, '| months', ym[0], 'to', ym[-1], '| draft', draft, '| HC', HC)

if __name__ == '__main__':
    main()
