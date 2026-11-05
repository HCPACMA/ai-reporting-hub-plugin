# DATA.exp from the EXSYS expense ledger lines (kit/sql/expense_monthly.sql + expense_redflags.sql), all four databases.
import json, datetime as dt
def f(x):
    try: return float(x)
    except: return 0.0
# ---- expenses
BR={'R':'01','B1':'02','B2':'03','B4':'04'}
names={}; mon={}; flg={}; xl=[]
for c,cc in BR.items():
    mon[cc]={}; flg[cc]={}
    for l in open(f'{c}_exp.txt'):
        l=l.strip()
        if not l: continue
        a,nm,rest=l.split('|',2); names[a]=nm
        mon[cc][a]={('20'+it.split(':')[0]):[round(f(x),2) for x in it.split(':')[1:]] for it in rest.split(',')}
    try:
        for l in open(f'{c}_flag.txt'):
            l=l.strip()
            if not l: continue
            a,rest=l.split('|',1)
            flg[cc][a]={('20'+it.split(':')[0]):[int(x) for x in it.split(':')[1:]] for it in rest.split(',')}
    except FileNotFoundError: pass
    try:
        for l in open(f'{c}_lines.txt'):
            p=l.rstrip('\n').split('~')
            if len(p)<13: continue
            xl.append([cc,p[0],p[1],p[2],round(f(p[3]),2),round(f(p[4]),2),p[5],p[6],p[7].strip(),p[8].strip(),p[9].strip(),p[10].strip(),p[11],int(f(p[12]))])
    except FileNotFoundError: pass
exp={'asOf':dt.date.today().isoformat(),'names':names,'mon':mon,'flg':flg,'lines':xl}
s2=json.dumps(exp,ensure_ascii=False,separators=(',',':'))
open('data_exp.json','w').write(s2); print('exp bytes',len(s2),'lines',len(xl))
