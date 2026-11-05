# DATA.aud rebuilt from the EXSYS database (no Power BI). See aud/*.sql for the queries.
import json,sys,re,collections
sys.path.insert(0,'.')
from pk import items, items_file
from onerow import onerow
from getres import find
TR='/root/.claude/projects/-home-claude/bee4938b-749b-5170-9e80-fa9fe506607a/tool-results/mcp-remote-devices-Cure_MCP__cure_run_query-'
def gl(mk): return {p.split('|')[0]:[float(x) for x in p.split('|')[1:]] for p in onerow(mk)}
def inv(mk): return {p.split('|')[0]:float(p.split('|')[1]) for p in onerow(mk)}
G={'01':gl('202301|2444441.56|0|0~202302|2396829.66|0|-31353.48~202303|2243716.36|0|-12708.85~202304|2008452.28|0|-530342.26~202305|2464430.39|0|-106281.87~202306|2117122.74|0|-69145.15~202307|2262121.24|0|-44713.05~202308|2381889.21|0|-43606.6~202309|2541454.14|1140|-139244.7~202310|2875237.72|6755|-88078.22~202311|2569607.84|6614|-411608.32~202312|2802651.32'),
   '02':gl('202312|995816.61|0|-100808.06'),'03':gl('202312|1679715.82|0|-443986'),'04':gl('202312|985582.9|0|-59240.02')}
G['01']['202412'][0]+=15387527.14   # JV1-24/04043 reversal voucher, excluded everywhere else in the desk
I={'01':{**inv('202301|2444441.56~202302|2396829.66~202303'),**inv('202407|2727903.7~202408|2431872.61')},
   '02':inv('202301|1207127.73~'),'03':inv('202301|1595160.58~202302|1561126.45'),'04':inv('202301|915178.18~202302|787826.82~202303')}
vat=[]
for br in G:
    for ym in sorted(set(G[br])|set(I[br])):
        hs,inn,ar=G[br].get(ym,[0,0,0]); iv=I[br].get(ym,0.0)
        vat.append([br,int(ym),round(hs+inn,2),round(iv+inn,2),round(ar,2)])
vchk=[]
for mk in ['JV1-23/02254|2023-08-10|399','CP2-26/00124|2026-06-01|25.36|0|','CP4-24/00089|2024-04-25']:
    for v,dt,dr,cr,d,st in items(mk): vchk.append([v,dt,round(float(dr),2),round(float(cr),2),d,st])
vchk.sort(key=lambda r:r[1])
files={'01':['1790286941272','1790286953715','1790286957657','1790286961800','1790286966169','1790286969732'],'02':['1790286978798'],'03':['1790286984032'],'04':['1790286987211']}
uj=[]
for br,fs in files.items():
    for f in fs:
        for v,dt,vt,ss,u,d,amt,nl in items_file(TR+f+'.txt'): uj.append([br,v,dt,vt,ss,u,d,round(float(amt),2),int(nl)])
uj.sort(key=lambda r:(r[2],r[1]))
users={}
for mk in ['2001|Hany Gameel ( 2001 )~2004','2001|Hani Gameel ( 2001 )~2004|Ali Adam ( 2004 )~2005|Marwan Mohammed ( 2005 )~2009|Mohamed Gamal','2001|Hani Gameel ( 2001 )~2004|Ali Adam ( 2004 )~2005|Marwan Mohammed ( 2005 )~2009|Mohamed Elboraei','1009|Yasser ( 1009 )~2001']:
    for p in onerow(mk):
        u,n=p.split('|',1); users.setdefault(u,' '.join(n.split()))
ctrl=json.load(open('../aud/ctrl.json')); T=json.load(open('../aud/term.json'))
acc=json.load(open('acc_names.json'))
cacc={a:acc.get(a,a) for a in sorted({r[1] for r in ctrl})}
A={'vat':vat,'vchk':vchk,'ctrl':ctrl,'cacc':cacc,'term':T['term'],'tacc':T['tacc'],'uj':uj,'users':users,'asOf':'2026-09-24',
   'src':'EXSYS database via Cure, read 24 Sep 2026: GL_TRANSACTIONS_DETAILS, RC_PATIENT_INVOICES / CHARGES and refunds, PS_STAFF_CONTRACT, ACCOUNTS'}
json.dump(A,open('../aud/data_aud_db.json','w'),ensure_ascii=False,separators=(',',':'))
print('vat',len(vat),'vchk',len(vchk),'uj',len(uj),'users',len(users),'term',len(T['term']),'ctrl',len(ctrl))
print(collections.Counter((r[0],r[2][:4]) for r in uj))
print([r for r in vat if r[1] in (202608,202609)])
