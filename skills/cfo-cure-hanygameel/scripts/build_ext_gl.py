# -*- coding: utf-8 -*-
"""DATA.ext rebuilt from the ledger only (no Power BI).
Inputs: y_*.txt — annual journal movements from GL_TRANSACTIONS_DETAILS for all four
databases (STATUS <> 'C'), by account, organisation function and voucher flag;
accounts.json — the ACCOUNTS master (parent and type).
Gate: every closed year (2019–2025) must reproduce the published statements."""
import json, collections, sys
ACC=json.load(open('accounts.json'))
par=lambda a: ACC.get(a,('-','?'))[0]
R=[]
for f in ['y_riy.txt','y_bur1.txt','y_bur2.txt','y_rafha.txt']:
    for l in open(f):
        l=l.strip()
        if l:
            y,a,fn,fl,v=l.split('|'); R.append((int(y),a,fn,fl,float(v)))
S=open('/home/claude/work/AlFaihaa_Modeling_Desk.html',encoding='utf-8').read()
i=S.index('DATA.ext ='); j=S.index('\n',i); E=json.loads(S[i+10:j].rstrip().rstrip(';'))
YRS=E['years']

def bs_line(a):
    p=par(a)
    if p=='1210000' or p.startswith('122') or p=='1210004': return 'cash'
    if a=='1263000': return 'other_creditors'
    if p in ('1240004','1240000'): return 'ar'
    if p=='12460000': return 'related_party'
    if p=='1250000': return 'prepaid'
    if a=='1262000': return 'lt_loans'
    if p.startswith('126'): return 'other_debtors'
    if p.startswith('13'): return 'unearned'            # sales control accounts
    if p.startswith('3') or p.startswith('4'): return 'pl'
    if a=='2111003': return 'vacation'
    if p=='2111000': return 'empben'
    if p=='2112000': return 'lt_loans'
    if p=='2210000': return 'capital'
    if a=='2123003': return 'zakat_provision'
    if p=='2220000' or p=='2200000': return 're'
    if p=='2230000': return 'statutory_reserve'
    if p=='2240000': return 'aoci'
    if a=='2123001': return 'other_debtors_l'          # liability shown on the debtor line
    if p=='2122000': return 'trade_payables'
    if p in ('2121000','2123000','2123007') or a=='2124000': return 'other_creditors'
    if p=='2126000': return 'due_related_party'
    if p=='2128000': return 'dividends_payable'
    if p in ('1110000','1120000','1111000','1121000'): return 'fixed_net'
    if p.startswith('113'): return 'wip'
    if p=='1230000': return 'inventory'
    return 'other'

def year(y):
    N=lambda pred, fn=None: sum(v for (yy,a,f,fl,v) in R if yy==y and fl=='N' and pred(a) and (fn is None or f==fn))
    cash=-N(lambda a:a.startswith('41'))
    cred=-N(lambda a:a.startswith('42') and a!='4200027')
    other=-N(lambda a:a.startswith('43') or a=='4200027')
    ex=lambda fn: -N(lambda a:a.startswith('3') and a!='3280005', fn)
    cor,ga,ins,ho=ex('COR'),ex('GA'),ex('INS'),ex('HO')
    zak=N(lambda a:a=='3280005'); dep=N(lambda a:a in ('3280001','3280002'))
    tot=cash+cred; gm=tot+cor; pfo=gm+ga+ins+ho; nibz=pfo+other; ni=nibz-zak
    is_=dict(cash_revenue=cash, credit_revenue=cred, total_revenue=tot, cost_of_revenue=cor, gross_margin=gm,
             ga_expenses=ga, insurance_expenses=ins, headoffice_expenses=ho, total_ga_rollup=ga+ins+ho,
             profit_from_operation=pfo, other_revenue=other, nibz=nibz, zakat_expenses=-zak, net_income=ni,
             depreciation=dep, ebitda=ni+dep)
    b=collections.defaultdict(float)
    for (yy,a,f,fl,v) in R:
        if yy<=y and fl=='N': b[bs_line(a)]+=v
    D=lambda k: b.get(k,0.0)          # debit-positive
    C=lambda k: -b.get(k,0.0)         # credit-positive
    # related-party balances are shown on whichever side their sign puts them
    rp_a=max(D('related_party'),0)+max(D('due_related_party'),0)
    rp_l=max(C('related_party'),0)+max(C('due_related_party'),0)
    bs=dict(cash=D('cash'), ar=D('ar'), related_party=rp_a, inventory=D('inventory'), prepaid=D('prepaid'),
            other_debtors=D('other_debtors')+D('other_debtors_l'), fixed_net=D('fixed_net'), wip=D('wip'))
    bs['noncurrent_assets']=bs['fixed_net']+bs['wip']
    bs['current_assets']=bs['cash']+bs['ar']+bs['related_party']+bs['inventory']+bs['prepaid']+bs['other_debtors']
    bs['total_assets']=bs['current_assets']+bs['noncurrent_assets']
    bs.update(empben=C('empben')+C('vacation'), lt_loans=C('lt_loans'), st_loans=0.0,
              other_creditors=C('other_creditors'), trade_payables=C('trade_payables'),
              due_related_party=rp_l, dividends_payable=C('dividends_payable'), zakat_provision=C('zakat_provision'))
    bs['noncurrent_liab']=bs['empben']+bs['lt_loans']
    bs['current_liab']=bs['other_creditors']+bs['trade_payables']+bs['due_related_party']+bs['dividends_payable']+bs['zakat_provision']+bs['st_loans']
    bs['unearned_revenue']=C('unearned')
    bs['total_liab']=bs['current_liab']+bs['noncurrent_liab']+bs['unearned_revenue']
    bs.update(capital=C('capital'), statutory_reserve=C('statutory_reserve'), aoci=C('aoci'),
              retained_earnings=C('re')+C('pl'))
    bs['equity']=bs['capital']+bs['statutory_reserve']+bs['aoci']+bs['retained_earnings']
    bs['total_liab_eq']=bs['total_liab']+bs['equity']
    bs['_other']=D('other')
    return is_,bs

new_is=collections.defaultdict(list); new_bs=collections.defaultdict(list)
for y in YRS:
    a,b=year(y)
    for k,v in a.items(): new_is[k].append(v)
    for k,v in b.items(): new_bs[k].append(v)

# ---------------- gate: closed years must reproduce the published statements ----------------
bad=[]
for grp,new,old in [('is_',new_is,E['is_']),('bs',new_bs,E['bs'])]:
    for k in old:
        if k not in new: continue
        for i,y in enumerate(YRS):
            if y>=2026: continue
            o=old[k][i] or 0.0; n=new[k][i] or 0.0
            if abs(n-o)>max(2.0,abs(o)*0.0002): bad.append((grp,k,y,o,n))
for b in bad: print('CLOSED-YEAR MISMATCH %s.%s %d published %.0f ledger %.0f'%b)
bal=[abs(new_bs['total_assets'][i]-new_bs['total_liab_eq'][i]) for i in range(len(YRS))]
print('balance check (assets - liabilities - equity):', ['%.0f'%x for x in bal])
print('unclassified balance:', ['%.0f'%x for x in new_bs['_other']])
if bad and '--force' not in sys.argv: sys.exit(1)

print('\n2026 YTD  ledger vs the FS snapshot the desk was showing:')
for grp,k in [('is_','cash_revenue'),('is_','credit_revenue'),('is_','total_revenue'),('is_','other_revenue'),
              ('is_','net_income'),('is_','ebitda'),('bs','cash'),('bs','ar'),('bs','total_assets'),('bs','equity')]:
    o=E[grp][k][-1]; n=(new_is if grp=='is_' else new_bs)[k][-1]
    print('  %-16s FS %14.0f   ledger %14.0f   diff %12.0f'%(k,o,n,n-o))

# ---------------- derived series ----------------------------------------------
n=len(YRS); z=lambda x: x if x else 0.0
rf={}
rf['current_ratio']=[z(new_bs['current_assets'][i])/z(new_bs['current_liab'][i]) if new_bs['current_liab'][i] else 0 for i in range(n)]
rf['quick_ratio']=[(z(new_bs['current_assets'][i])-z(new_bs['inventory'][i]))/z(new_bs['current_liab'][i]) if new_bs['current_liab'][i] else 0 for i in range(n)]
rf['debt_to_equity']=[(z(new_bs['lt_loans'][i])+z(new_bs['st_loans'][i]))/z(new_bs['equity'][i]) if new_bs['equity'][i] else 0 for i in range(n)]
rf['net_debt']=[z(new_bs['lt_loans'][i])+z(new_bs['st_loans'][i])-z(new_bs['cash'][i]) for i in range(n)]
rf['net_margin']=[z(new_is['net_income'][i])/z(new_is['total_revenue'][i]) if new_is['total_revenue'][i] else 0 for i in range(n)]
rf['ebitda_margin']=[z(new_is['ebitda'][i])/z(new_is['total_revenue'][i]) if new_is['total_revenue'][i] else 0 for i in range(n)]
rf['roe']=[z(new_is['net_income'][i])/z(new_bs['equity'][i]) if new_bs['equity'][i] else 0 for i in range(n)]
rf['roa']=[z(new_is['net_income'][i])/z(new_bs['total_assets'][i]) if new_bs['total_assets'][i] else 0 for i in range(n)]
rf['asset_turnover']=[z(new_is['total_revenue'][i])/z(new_bs['total_assets'][i]) if new_bs['total_assets'][i] else 0 for i in range(n)]
rf['dso']=[z(new_bs['ar'][i])/z(new_is['total_revenue'][i])*365 if new_is['total_revenue'][i] else 0 for i in range(n)]
du={'years':E['dupont']['years']}
du['years']=[int(y) for y in du['years']]
idx=[YRS.index(y) for y in du['years']]
du['net_margin']=[rf['net_margin'][i] for i in idx]
du['asset_turnover']=[rf['asset_turnover'][i] for i in idx]
du['equity_multiplier']=[z(new_bs['total_assets'][i])/z(new_bs['equity'][i]) if new_bs['equity'][i] else 0 for i in idx]
du['roe']=[rf['roe'][i] for i in idx]
# cash-flow bridge: FY2023->FY2025 and FY2025->2026 YTD
def bridge(a,b):
    d=lambda k: z(new_bs[k][YRS.index(b)])-z(new_bs[k][YRS.index(a)])
    ni=sum(z(new_is['net_income'][YRS.index(y)]) for y in YRS if a<y<=b)
    dep=sum(z(new_is['depreciation'][YRS.index(y)]) for y in YRS if a<y<=b)
    d_ar=-d('ar'); d_inv=-d('inventory')
    d_ap=d('trade_payables')+d('other_creditors')+d('empben')
    cfo=ni+dep+d_ar+d_inv+d_ap
    cfi=-(d('fixed_net')+d('wip')+dep)
    cff=d('lt_loans')+d('st_loans')
    sub=cfo+cfi+cff
    return ni,dep,d_ar,d_inv,d_ap,cfo,cfi,cff,sub,d('cash')
b1=bridge(2023,2025); b2=bridge(2025,2026)
cfw={'bridge1_label':E['cashflow']['bridge1_label'],'bridge2_label':E['cashflow']['bridge2_label']}
for k,i in [('net_income',0),('depreciation',1),('d_ar',2),('d_inv',3),('d_ap_accrued',4),
            ('cfo',5),('d_fixed_assets',6),('cfi',6),('d_loans',7),('cff',7),('subtotal',8),('actual_d_cash',9)]:
    cfw[k]=[b1[i],b2[i]]
cfw['plug']=[cfw['actual_d_cash'][0]-cfw['subtotal'][0], cfw['actual_d_cash'][1]-cfw['subtotal'][1]]

E['is_']=new_is; E['bs']=new_bs; E['ratios_full']=rf; E['dupont']=du; E['cashflow']=cfw
i25=YRS.index(2025)
E['dcf']['net_debt_fy2025']=rf['net_debt'][i25]
E['lbo']['entry_ebitda']=new_is['ebitda'][i25]
E['comps']['subject_revenue_fy2025']=new_is['total_revenue'][i25]
E['comps']['subject_ebitda_fy2025']=new_is['ebitda'][i25]
E['asOf']='2026-09-24'
E['source']='EXSYS ledger — GL_TRANSACTIONS_DETAILS, all four databases, STATUS <> C, year-end closing vouchers and JV1-24/04043 excluded; ACCOUNTS for classification'
new_bs={k:v for k,v in new_bs.items() if not k.startswith('_')}
json.dump(E, open('data_ext_gl.json','w'), ensure_ascii=False, separators=(',',':'))
print('\nwrote data_ext_gl.json')
print('2026: revenue %.0f  net income %.0f  cash %.0f  total assets %.0f'%(
    new_is['total_revenue'][-1], new_is['net_income'][-1], new_bs['cash'][-1], new_bs['total_assets'][-1]))
