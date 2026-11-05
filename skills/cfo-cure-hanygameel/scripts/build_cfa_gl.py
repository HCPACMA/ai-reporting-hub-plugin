# -*- coding: utf-8 -*-
"""Indirect cash-flow statement rebuilt from the EXSYS ledger only (no Power BI).
Inputs: y_*.txt (annual net movement by account, flag N = ordinary vouchers),
drcr.json (annual debit/credit totals for fixed assets, WIP, loans, deferred interest,
dividends payable and the provision accounts), accounts.json.
Every balance-sheet line is paired with the cash-flow lines that represent it;
the statement must close to the balance-sheet cash with no plug."""
import json, collections, sys
sys.path.insert(0,'.')
from build_ext_gl import bs_line   # same classification as the desk's statements
ACC=json.load(open('accounts.json'))
X=json.load(open('drcr.json'))
dc=lambda g,y,i: X.get(f'{g}|{y}',[0.0,0.0])[i]
DR=lambda g,y: dc(g,y,0); CR=lambda g,y: dc(g,y,1)

mv=collections.defaultdict(float)        # (year, account) -> DR-CR, ordinary vouchers
for f in ['y_riy.txt','y_bur1.txt','y_bur2.txt','y_rafha.txt']:
    for l in open(f):
        l=l.strip()
        if not l: continue
        y,a,fn,fl,v=l.split('|')
        if fl=='N': mv[(int(y),a)]+=float(v)
YALL=sorted({y for y,a in mv})

def line(a):
    if a=='2111001': return 'eosb'
    if a=='2111003': return 'vac'
    k=bs_line(a)
    if k=='empben': return 'oprov'
    if k=='other_debtors_l': return 'other_debtors'
    if k in ('re','pl'): return 'reall'
    return k
bal={}
run=collections.defaultdict(float)
for y in YALL:
    for (yy,a),v in mv.items():
        if yy==y: run[line(a)]+=v
    bal[y]=dict(run)
B=lambda k,y: bal[y].get(k,0.0)                  # debit-positive balance at year end
P=lambda a,y: mv.get((y,a),0.0)                  # P&L account movement, debit-positive

YEARS=[y for y in YALL if y>=2019]
out={'years':YEARS,'layout':[],'audit':[],'v':{},'eq':{},'bs':{},'checks':{}}
for y in YEARS:
    p=y-1
    dD=lambda k: B(k,y)-B(k,p)          # change in debit balance
    dC=lambda k: -(B(k,y)-B(k,p))       # change in credit balance
    ni=-sum(v for (yy,a),v in mv.items() if yy==y and a[:1] in '34')
    G=-P('4300008',y); L=P('3380000',y)
    o={}
    o[1]=ni
    o[4]=P('3280001',y); o[5]=P('3280002',y); o[6]=-G; o[7]=L
    o[8]=CR('PROV',y); o[9]=-DR('PROV',y)
    o[10]=P('3290001',y)
    o[11]=P('3280003',y)+P('3390000',y)
    o[12]=CR('VAC',y)
    o[3]=P('3280005',y)
    o[15]=-dD('ar')-o[8]-o[9]
    o[16]=-dD('due_related_party'); o[17]=-dD('related_party')
    o[18]=-dD('inventory'); o[19]=-dD('prepaid'); o[20]=-dD('other_debtors')
    o[21]=dC('other_creditors'); o[22]=dC('trade_payables'); o[26]=dC('unearned'); o[27]=dC('oprov')
    act=dD('aoci')                                   # actuarial loss booked to OCI, credited to EOSB
    o[43]=act
    o[23]=dC('eosb')-o[11]-act
    o[24]=dC('vac')-o[12]
    o[25]=dC('zakat_provision')-o[3]
    o[29]=-(DR('FAC',y))
    o[30]=CR('FAC',y)-DR('ACD',y)+G-L
    o[31]=-dD('wip')
    o[36]=max(0.0, CR('LOAN',y)-DR('DINT',y))
    o[34]=dC('lt_loans')-o[10]-o[36]
    o[35]=-DR('DIV',y)
    eqchg=dC('capital')+dC('statutory_reserve')+dC('reall')+dC('dividends_payable')
    EQ=eqchg-ni-o[35]
    CFO=sum(o[k] for k in (1,4,5,6,7,8,9,10,11,12,3,15,16,17,18,19,20,21,22,26,27,23,24,25))
    CFI=o[29]+o[30]+o[31]
    CFF=o[36]+o[34]+o[35]+EQ
    NET=CFO+CFI+CFF
    v={'CFO':CFO,'CFI':CFI,'CFF':CFF,'NET':NET,'OPEN':B('cash',p),'CLOSE':B('cash',p)+NET,'EQ':EQ}
    for k,x in o.items(): v['o%d'%k]=x
    out['v'][y]={k:round(x,2) for k,x in v.items()}
    out['eq'][y]=round(EQ,2)
    out['bs'][y]={'cash':round(B('cash',y),2),'open':round(B('cash',p),2)}
    # audit pairs: balance movement vs the cash-flow lines that represent it
    pairs=[
     ('Accounts receivable (net of provision)','الذمم المدينة (بعد المخصص)', -dD('ar'), o[15]+o[8]+o[9]),
     ('Related party — receivable','أرصدة مدينة لأطراف ذات علاقة', -dD('related_party'), o[17]),
     ('Due to related party','مستحق لأطراف ذات علاقة', dC('due_related_party'), o[16]),
     ('Inventory','المخزون', -dD('inventory'), o[18]),
     ('Prepaid expenses','مصاريف مدفوعة مقدماً', -dD('prepaid'), o[19]),
     ('Other debtors (incl. revenue received in advance)','أرصدة مدينة أخرى', -dD('other_debtors'), o[20]),
     ('Other creditors (incl. VAT)','أرصدة دائنة أخرى', dC('other_creditors'), o[21]),
     ('Creditors','الدائنون', dC('trade_payables'), o[22]),
     ('Severance pay (EOSB)','مكافأة نهاية الخدمة', dC('eosb'), o[11]+o[23]+o[43]),
     ('Vacation allowance','بدل الإجازات', dC('vac'), o[12]+o[24]),
     ('Other provisions (housing, lawsuits)','مخصصات أخرى', dC('oprov'), o[27]),
     ('Unearned revenue / sales control','إيرادات غير مكتسبة', dC('unearned'), o[26]),
     ('Zakat provision','مخصص الزكاة', dC('zakat_provision'), o[3]+o[25]),
     ('Property, equipment &amp; intangibles','الأصول الثابتة', -dD('fixed_net'), o[4]+o[5]+o[6]+o[7]+o[29]+o[30]),
     ('Assets in progress','مشاريع تحت التنفيذ', -dD('wip'), o[31]),
     ('Loans (net of deferred interest)','القروض', dC('lt_loans'), o[36]+o[34]+o[10]),
     ('AOCI — actuarial remeasurement','إعادة قياس اكتوارية', dC('aoci'), -o[43]),
     ('Capital, reserve, retained earnings and dividends payable','رأس المال والاحتياطي والأرباح المبقاة والتوزيعات',
        eqchg-ni, o[35]+EQ),
    ]
    for i,(en,ar,bsv,cfv) in enumerate(pairs):
        if len(out['audit'])<=i: out['audit'].append({'en':en,'ar':ar,'y':{}})
        out['audit'][i]['y'][y]=[round(bsv,2),round(cfv,2),round(cfv-bsv,2)]
    unc=B('other',y)
    out['checks'][y]={'dep_vs_accum':round(o[4]+o[5]-CR('ACD',y),2),'unclassified':round(unc,2),
                      'close_minus_bs':round(v['CLOSE']-B('cash',y),2)}

LAYOUT=[
 ('h','Cash flows from operating activities','التدفقات النقدية من الأنشطة التشغيلية',None),
 ('l','Net income','صافي الربح',[1]),
 ('s','Adjustments for non-cash items','تسويات البنود غير النقدية',None),
 ('l','Depreciation','الإهلاك',[4]),
 ('l','Amortisation','الإطفاء',[5]),
 ('l','Gain on disposal of assets','أرباح بيع أصول',[6]),
 ('l','Loss on disposal of assets','خسائر بيع أصول',[7]),
 ('l','Doubtful-debt provision','مخصص الديون المشكوك فيها',[8]),
 ('l','Bad debts written off','ديون معدومة مشطوبة',[9]),
 ('l','Finance cost on loans','تكلفة تمويل القروض',[10]),
 ('l','Severance-pay provision','مخصص مكافأة نهاية الخدمة',[11]),
 ('l','Vacation-allowance provision','مخصص بدل الإجازات',[12]),
 ('l','Zakat provision','مخصص الزكاة',[3]),
 ('s','Changes in working capital','التغير في رأس المال العامل',None),
 ('l','Accounts receivable','الذمم المدينة',[15]),
 ('l','Due to related party','مستحق لأطراف ذات علاقة',[16]),
 ('l','Related party receivable','أرصدة مدينة لأطراف ذات علاقة',[17]),
 ('l','Inventory','المخزون',[18]),
 ('l','Prepaid expenses','مصاريف مدفوعة مقدماً',[19]),
 ('l','Other debtors','أرصدة مدينة أخرى',[20]),
 ('l','Other creditors','أرصدة دائنة أخرى',[21]),
 ('l','Creditors','الدائنون',[22]),
 ('l','Other provisions','مخصصات أخرى',[27]),
 ('l','Unearned revenue / sales control','إيرادات غير مكتسبة (حسابات مراقبة)',[26]),
 ('s','Cash paid out of provisions','المدفوع من المخصصات',None),
 ('l','Severance pay paid','مكافأة نهاية خدمة مدفوعة',[23]),
 ('l','Vacation allowance paid','بدل إجازات مدفوع',[24]),
 ('l','Zakat paid','زكاة مدفوعة',[25]),
 ('t','Net cash from operating activities','صافي التدفق النقدي من التشغيل','CFO'),
 ('h','Cash flows from investing activities','التدفقات النقدية من الأنشطة الاستثمارية',None),
 ('l','Purchase of property &amp; equipment','مدفوعات شراء أصول',[29]),
 ('l','Proceeds from disposals','متحصلات بيع أصول',[30]),
 ('l','Paid for assets in progress','مدفوعات مشاريع تحت التنفيذ',[31]),
 ('t','Net cash used in investing activities','صافي التدفق النقدي من الاستثمار','CFI'),
 ('h','Cash flows from financing activities','التدفقات النقدية من الأنشطة التمويلية',None),
 ('l','Proceeds from loans','متحصلات القروض',[36]),
 ('l','Loan repayments, including interest','سداد القروض شاملاً الفوائد',[34]),
 ('l','Dividends paid','توزيعات أرباح مدفوعة',[35]),
 ('l','Movements taken directly to equity','حركات مقيدة مباشرة في حقوق الملكية','EQ'),
 ('t','Net cash from financing activities','صافي التدفق النقدي من التمويل','CFF'),
 ('t','Net change in cash and cash equivalents','صافي التغير في النقد وما يعادله','NET'),
 ('l','Cash and cash equivalents at 1 January','النقد وما يعادله في 1 يناير','OPEN'),
 ('T','Cash and cash equivalents at period end','النقد وما يعادله في نهاية الفترة','CLOSE'),
]
out['layout']=[list(r) for r in LAYOUT]
out['asOf']='2026-09-24'
out['source']='EXSYS ledger: GL_TRANSACTIONS_DETAILS (all four databases, STATUS <> C, closing vouchers and JV1-24/04043 excluded) + ACCOUNTS'
json.dump(out,open('data_cfa_gl.json','w'),ensure_ascii=False,separators=(',',':'))
print('%-5s %13s %13s %13s %13s %13s %10s %10s'%('year','CFO','CFI','CFF','close','BS cash','diff','dep-acd'))
for y in YEARS:
    v=out['v'][y]; c=out['checks'][y]
    print('%-5d %13.0f %13.0f %13.0f %13.0f %13.0f %10.2f %10.2f'%(y,v['CFO'],v['CFI'],v['CFF'],v['CLOSE'],out['bs'][y]['cash'],c['close_minus_bs'],c['dep_vs_accum']))
print('residuals by pair:')
for r in out['audit']:
    bad={y:x[2] for y,x in r['y'].items() if abs(x[2])>0.5}
    if bad: print('  ',r['en'],bad)
print('EQ',out['eq'])
