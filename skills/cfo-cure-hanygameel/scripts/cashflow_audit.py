from fs import BS, Y
from cfdata import CFI, TOT, NAME
import json
def d(k,t): return BS[k][t]-BS[k][t-1]
def g(y,o): return CFI[y].get(o,0.0)
rows=[]
for t in range(2,len(Y)):           # 2020..2026
    y=Y[t]; R=[]
    A=lambda *o: sum(g(y,x) for x in o)
    R.append(('Accounts receivable (net of provision)', -d('ar',t), A(15,8,9)))
    R.append(('Related party — receivable',             -d('rp',t),  A(17)))
    R.append(('Due to related party',                     d('durp',t),A(16)))
    R.append(('Inventory',                              -d('inv',t), A(18)))
    R.append(('Prepaid expenses',                       -d('pre',t), A(19)))
    R.append(('Other debtors',                          -d('odeb',t),A(20)))
    R.append(('Other creditors',                          d('ocr',t),A(21)))
    R.append(('Creditors',                                d('cred',t),A(22)))
    R.append(('Severance pay (EOSB)',                     d('eosb',t),A(11,23,43)))
    R.append(('Vacation allowance',                       d('vac',t), A(12,24)))
    R.append(('Unearned revenue / sales control',         d('unearn',t),A(26)))
    R.append(('Zakat provision',                          d('zak',t), A(3,25)))
    R.append(('Property &amp; equipment',                -d('fa',t),  A(4,29,30,6,7,5)))
    R.append(('Assets in progress',                      -d('wip',t), A(31)))
    R.append(('Loans',                                    d('loans',t),A(36,34,10)))
    R.append(('AOCI — actuarial remeasurement',           d('aoci',t),-A(43)))
    R.append(('Capital',                                  d('cap',t), 0.0))
    paid = g(y,1) - d('re',t) - d('res',t) - d('divp',t)
    R.append(('Dividends and equity movements',          -paid,        A(35)))
    tot=sum(c-b for _,b,c in R)
    dc=d('cash',t)
    cfn=TOT[y][3]
    rows.append({'y':y,'lines':[[n,round(b,2),round(c,2),round(c-b,2)] for n,b,c in R],
                 'resid':round(tot,2),'dcash':round(dc,2),'cfnet':round(cfn,2),
                 'open':round(BS['cash'][t-1],2),'close':round(BS['cash'][t],2),
                 'divTrue':round(paid,2),'divModel':round(-g(y,35),2)})
print('%-6s %12s %12s %12s   %s'%('year','ΔBS cash','model CF net','break','worst line'))
for r in rows:
    bad=max(r['lines'], key=lambda x: abs(x[3]))
    print('%-6d %12.0f %12.0f %12.0f   %s %.0f'%(r['y'],r['dcash'],r['cfnet'],r['cfnet']-r['dcash'],bad[0],bad[3]))
json.dump(rows, open('audit.json','w'))
