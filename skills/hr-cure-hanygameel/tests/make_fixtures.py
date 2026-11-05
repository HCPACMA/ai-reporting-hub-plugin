#!/usr/bin/env python3
"""Regenerate raw/ replies in the Cure MCP table format from a verified extract file (round-trip test of ingest.py).
    python3 tests/make_fixtures.py data/extract.alfaihaa.2026-10-12.json tests/fixtures
Then:  python3 scripts/ingest.py --raw tests/fixtures ...   and compare with the source extract.
"""
import json, sys, os
ex = json.load(open(sys.argv[1], encoding='utf8')); out = sys.argv[2]; os.makedirs(out, exist_ok=True)
def table(cols, rows):
    w = [max(len(str(c)), *(len(str(r[i])) for r in rows)) if rows else len(str(c)) for i, c in enumerate(cols)]
    line = '+' + '+'.join('-' * (x + 2) for x in w) + '+'
    f = lambda r: '| ' + ' | '.join(str(v).ljust(w[i]) for i, v in enumerate(r)) + ' |'
    return '\n'.join([line, f(cols), line] + [f(r) for r in rows] + [line, f'  ({len(rows)} rows)'])
def put(name, cols, rows): open(os.path.join(out, name + '.txt'), 'w', encoding='utf8').write(table(cols, rows))
f = lambda v: f"{float(v)}"
ym = ex['ym']; draft = ex.get('draftMonth'); n = len(ym)
rows = []
for k in range(n):
    y, m = ym[k].split('-'); rows.append([f(y), f(m), f(ex['staffPaid'][k]), f(ex['basic'][k]), f(ex['gosiCo'][k]), f(ex['gosiSt'][k]), f(ex['absD'][k]), f(ex['ot'][k]), f(ex['unpostedByMonth'].get(ym[k], 0))])
if draft:
    y, m = draft.split('-'); rows.append([f(y), f(m), f(ex['HC']), f(1446843), f(0), f(0), f(0), f(0), f(ex['HC'])])
put('hr05a_payroll_header_monthly', ['y','m','stf','basic','gosi_co','gosi_st','abs_d','ot','notposted'], rows)
rows = []
for k in range(n):
    y, m = ym[k].split('-'); rows += [[f(y), f(m), '+', f(300), f(ex['plus'][k])], [f(y), f(m), '-', f(200), f(ex['minus'][k])]]
put('hr05b_payroll_items_monthly', ['y','m','sg','stf','amt'], rows)
put('hr07_hires_monthly', ['ym','hires'], [[ym[k], f(ex['hires'][k])] for k in range(n)])
put('hr08_leavers_last_pay', ['lm','n'], [[ym[k], f(ex['leavers'][k])] for k in range(n)])
put('hr01a_branch_summary', ['br','n','fem','saudi'], [[b['k'], f(b['h']), f(b['f']), f(b['s'])] for b in ex['branches']])
# salary rows: split each branch into S / N so the sums reproduce
sr = []
for b in ex['branches']:
    sr.append([b['k'], 'S', f(b['s']), f(0), f(0), f(0)]); sr.append([b['k'], 'N', f(b['h'] - b['s']), f(b['sal']), f(0), f(0)])
# adjust saudi / non-saudi salary totals (put the Saudi total on the first branch)
tot_s = ex['saudiSal']; first = ex['branches'][0]
sr[0][3] = f(tot_s); sr[1][3] = f(first['sal'] - tot_s)
rest_diff = ex['nonSaudiSal'] - sum(float(r[3]) for r in sr if r[1] == 'N')
sr[3][3] = f(float(sr[3][3]) + rest_diff) if rest_diff else sr[3][3]
sr[3][3] = f(float(sr[3][3]) - 0)
put('hr01b_branch_salary', ['br','sa','n','sal','mx','mn'], sr)
put('hr02_job_families', ['job','n','avg_sal'], [[j[0], f(j[1]), f(j[2])] for j in ex['jobs']])
ab = {'Under 20': 10, '20 to 29': 20, '30 to 39': 30, '40 to 49': 40, '50 to 59': 50, '60 and over': 60}
put('hr03_age_bands', ['age_b','n'], [[f(ab[a[0]]), f(a[1])] for a in ex['age'] if a[0] in ab])
tb = {'Under 1 year': 0, '1 to 2 years': 1, '2 to 3 years': 2, '3 to 5 years': 3, '5 to 8 years': 5, '8 to 10 years': 8, '10 to 15 years': 10, '15 years and over': 15}
put('hr04_tenure', ['ten_y','n'], [[f(tb[t[0]]), f(t[1])] for t in ex['tenure']])
put('hr06_items_last_month', ['si','en','sg','n','amt'], [[f(100+i), e[0], '+', f(10), f(e[1])] for i, e in enumerate(ex['earn'])] + [[f(-1 if d[0] in ('Loans','LOANS') else -10-j), d[0], '-', f(ex['loanDedStaff'] if d[0] in ('Loans','LOANS') else 5), f(d[1])] for j, d in enumerate(ex['ded'])])
import datetime
cm = []
y, m = int(ex['asof'][:4]), int(ex['asof'][5:7])
mm = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6}
yy = y + 1 if True else y
for lab, nn in zip(ex['expMonths'], ex['expN']):
    mon = lab.split()[0]; cm.append([f"{yy}-{mm[mon]:02d}", f(nn)])
put('hr09_contract_end_months', ['exp_y','n'], cm)
put('hr10_contract_status', ['st','cc','e','n','s'], [['A','Y','FUT',f(ex['HC']-ex['openEnded']-ex['expiredContracts']),f(1)],['A','Y','BLANK',f(ex['openEnded']),f(1)]] + ([['A','Y','PAST',f(ex['expiredContracts']),f(1)]] if ex['expiredContracts'] else []))
idm = {x[0]: x[1] for x in ex['idb']}
pp = ex.get('passport', dict(expired=0, soon=0, noexp=0, ok=0))
rows = [['RES', 'OK', f(idm.get('Valid beyond 6 months', 0))], ['RES', 'EXPIRED', f(idm['Expired'])], ['RES', 'D180', f(idm.get('Expires in 91 to 180 days', 0))], ['RES', 'D90', f(idm.get('Expires in 31 to 90 days', 0))], ['RES', 'NOEXP', f(idm['No expiry date'])],
        ['PASSPORT', 'OK', f(pp['ok'])], ['PASSPORT', 'EXPIRED', f(pp['expired'])], ['PASSPORT', 'D90', f(pp['soon'])], ['PASSPORT', 'NOEXP', f(pp['noexp'])]]
put('hr11_id_expiry', ['tp','b','n'], [r for r in rows if float(r[2]) or r[1] in ('EXPIRED','NOEXP')])
mc = ex['missCounts']
put('hr12_completeness', ['active','no_dss','no_dob','no_email','no_nat','no_lic','no_id','no_sal','no_gosi','no_prob'], [[f(ex['HC']), f(mc['dss']), f(mc['dob']), f(mc['email']), f(mc['nat']), f(mc['licence']), f(mc['idrec']), f(0), f(mc['gosi']), f(mc['probation'])]])
sm = {'Posted': 'P', 'Cancelled': 'C', 'Open': 'O'}
put('hr13_leave_summary', ['vt','pf','y','n','days'], [[r[1], sm[r[2]], r[0], f(r[3]), f(r[4])] for r in ex['leaveRows']])
put('hr14_open_leave_and_loan_holders', ['k','n','v'], [['open_leaves', f(ex['openLeaveRecords']), f(ex['openLeaveDays'])], ['loans_open_active_staff', f(ex['loanHoldersActive']), f(0)], ['loans_on_leavers', f(ex['leaverLoanStaff']), f(0)]])
cl = {'Paid (P)': 'P', 'Rescheduled (R)': 'R', 'Pending (N)': 'N'}
put('hr15_loan_installments', ['st','who','n','stf','amt','coll'], [[cl[r[1]], 'ACTIVE' if r[0] == 'Active staff' else 'LEAVER', f(r[2]), f(r[3]), f(r[4]), f(r[4] if r[1].startswith('Paid') else 0)] for r in ex['loanRows']])
put('hr16_gl_provisions', ['acc','n','net'], [['2111001', f(1), f(-ex['gl']['eosb'])], ['2111003', f(1), f(-ex['gl']['leave'])], ['2121001', f(1), f(-ex['gl']['pay'])]])
put('hr17_eosb_estimate', ['eosb_basic','eosb_totwage','tot_yrs','n'], [[f(ex['gl']['estB']), f(ex['gl']['estW']), f(1809.6), f(ex['HC'])]])
print('fixtures written to', out)
