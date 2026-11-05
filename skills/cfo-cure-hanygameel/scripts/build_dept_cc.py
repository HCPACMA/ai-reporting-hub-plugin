# -*- coding: utf-8 -*-
"""DATA.dept and DATA.cc from the ledger: GL_TRANSACTIONS_DETAILS by COST_CENTER_NO, all four
databases, FY2025 and FY2026 YTD. Revenue: cash 41x, credit 42x excl. 4200027 (insurance drug
sales, shown as other revenue in the statements). Cost: 3x excl. zakat, debit and credit.
Names: ORGANIZATIONS (Arabic description, as held in the ERP)."""
import json, collections
rows=json.load(open('cc_rows.json')); AR=json.load(open('org_names.json'))
BR={'01':'Riyadh','02':'Buraydah 1','03':'Buraydah 2','04':'Rafha'}
EN={'02101':'Outpatient reception','02102':'Children\'s clinics','02103':'General practice','02104':'Dermatology',
 '02106':'Obstetrics & gynaecology','02107':'ENT','02109':'Dialysis','02110':'Home care','02111':'Physiotherapy',
 '02113':'Ophthalmology','02115':'Orthopaedics','02118':'Chest','02121':'Internal medicine','02122':'Dental',
 '02123':'Urology','02124':'Laser clinics','02125':'Surgery','02126':'Neurology','023':'Laboratory','024':'Radiology',
 '025':'Emergency & dressing','026':'Pharmacy','027':'Health certificates','028':'Branch activity costs','029':'Vaccinations'}
def dept_of(cc):
    x=cc[:7]
    return x if x[4]=='1' else x[:5]
def en(d): return EN.get(d[2:], AR.get(d,d))
D=collections.defaultdict(lambda:[0.0]*4)     # (year, dept) -> cash, credit, cdr, ccr
C=collections.defaultdict(lambda:[0.0]*4)     # (year, cc)
for br,y,cc,ca,cr,dr,ccr in rows:
    for tgt,k in ((D,(y,dept_of(cc))),(C,(y,cc))):
        v=tgt[k]; v[0]+=ca; v[1]+=cr; v[2]+=dr; v[3]+=ccr
def drows(y):
    out=[]
    for (yy,d),v in D.items():
        if yy!=y: continue
        out.append({'branch':d[:2],'dept_no':d,'key':d[2:],'name':en(d),'name_ar':AR.get(d,''),
                    'cash':round(v[0],2),'credit':round(v[1],2),'revenue':round(v[0]+v[1],2),
                    'cost_dr':round(v[2],2),'cost_cr':round(v[3],2)})
    return sorted(out,key=lambda r:(r['branch'],-r['revenue']))
all25,all26=drows(2025),drows(2026)
ccs=collections.defaultdict(dict)
for (y,cc),v in C.items():
    if len(cc)!=9 and dept_of(cc)==cc[:7]: continue   # dept-level postings stay at department level
    r=ccs[cc]; r.update(org_no=cc, branch=cc[:2], name=AR.get(cc,cc), dept=en(dept_of(cc)), dept_no=dept_of(cc))
    s=str(y)
    r['cash_'+s]=round(v[0],2); r['credit_'+s]=round(v[1],2); r['cost_'+s]=round(v[2]-v[3],2)
cc_list=[]
for r in ccs.values():
    for s in ('2025','2026'):
        for k in ('cash_','credit_','cost_'): r.setdefault(k+s,0.0)
    if r['cash_2025']+r['credit_2025']+r['cash_2026']+r['credit_2026']>1 or r['cost_2025']+r['cost_2026']>1:
        cc_list.append(r)
cc_list.sort(key=lambda r:-(r['cash_2026']+r['credit_2026']))
dept_level=sum(v[0]+v[1] for (y,cc),v in C.items() if y==2026 and not (len(cc)!=9 and dept_of(cc)==cc[:7]))
note=("Read from the EXSYS ledger on 24 Sep 2026: GL_TRANSACTIONS_DETAILS by cost centre (COST_CENTER_NO), all four databases, "
 "posted and open vouchers, cancelled and year-end closing vouchers excluded. Revenue is cash (41x) plus credit (42x) "
 "excluding 4200027 insurance drug sales, which the statements show as other revenue. Department and branch revenue ties "
 "to the income statement exactly for Riyadh, Buraydah 1 and Buraydah 2; in Rafha SAR 115,806 of FY2025 and SAR 66,000 of "
 "FY2026 cash revenue is booked to a cost centre outside the clinics and is not in this view. Cost is every expense "
 "account (3x, excluding zakat) tagged to the department or clinic — mostly salaries, dispensed consumables and commissions, "
 "much of it booked in the Riyadh database on behalf of the branches. It is a contribution before unallocated overhead, "
 "insurance rejections and head-office cost. Names are as held in the ERP's ORGANIZATIONS table.")
DEPT={'asOf':'2026-09-24','ytd_days':267,'branches':BR,'note':note,
      'departments_2025':[r for r in all25 if r['branch']=='01'],'departments_2026ytd':[r for r in all26 if r['branch']=='01'],
      'all_2025':all25,'all_2026ytd':all26}
CC={'asOf':'2026-09-24','ytd_days':267,'branches':BR,
    'note':("Every doctor and clinic cost centre in the four ledgers (organisation codes xx02xxxxx), FY2025 and FY2026 YTD, "
            "from GL_TRANSACTIONS_DETAILS.COST_CENTER_NO — cash and credit revenue and direct cost are tagged per clinic in both years. "
            "Postings made at department level (laboratory, radiology, emergency) appear on the Department page, not here. Clinic names are as held in ORGANIZATIONS."),
    'cost_centers':cc_list}
json.dump(DEPT,open('data_dept.json','w'),ensure_ascii=False,separators=(',',':'))
json.dump(CC,open('data_cc.json','w'),ensure_ascii=False,separators=(',',':'))
print('depts 2025',len(all25),'2026',len(all26),'cc',len(cc_list))
for y,a in ((2025,all25),(2026,all26)):
    t=collections.defaultdict(float)
    for r in a: t[r['branch']]+=r['revenue']
    print(y,{BR[k]:round(v) for k,v in t.items()}, 'total',round(sum(t.values())))
print([ (r['name'],r['cash'],r['credit']) for r in all26 if r['branch']=='01'][:5])
