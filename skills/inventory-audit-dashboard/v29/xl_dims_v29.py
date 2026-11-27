from copy import copy
import json,sys
from openpyxl import load_workbook
from openpyxl.styles import Font,PatternFill,Alignment
from openpyxl.utils import get_column_letter as L
src,out=sys.argv[1],sys.argv[2]
d=json.load(open('dims_v29.json'))
IG,PC,ST=d['ig'],d['pc'],d['st']
prod={k.lstrip('0'):v for k,v in d['prod'].items()}
pt={k.lstrip('0'):v for k,v in d['pt'].items()}
supN=d['sup']; supNo={v['no']:(n,v) for n,v in supN.items()}
def sfind(x):
    x=str(x or '').strip()
    if x in supN: return supN[x]
    if x in supNo: return supNo[x][1]
def top(m,names,n=3):
    return '; '.join(names.get(k,k) for k,_ in sorted(m.items(),key=lambda a:-a[1])[:n])
CODE={'Code','Product code','Item code'}; SUP={'Supplier no.','Supplier','Supplier no'}
wb=load_workbook(src)
hf=wb['Overstock'].cell(5,1).font if 'Overstock' in wb.sheetnames else Font(bold=True)
hfill=wb['Overstock'].cell(5,1).fill
stats={}
for ws in wb:
    if ws.title in('Summary','Methodology','Data Status','تقرير مجلس الإدارة'): continue
    r=1; n=0
    while r<=ws.max_row:
        hdr={}
        for c in range(1,ws.max_column+1):
            v=ws.cell(r,c).value
            if isinstance(v,str) and v.strip() in CODE|SUP and v.strip() not in hdr: hdr[v.strip()]=c
        cc=next((hdr[k] for k in hdr if k in CODE),None)
        sc=hdr.get('Supplier no.') or hdr.get('Supplier no') or hdr.get('Supplier')
        if not(cc or sc): r+=1; continue
        last=max(c for c in range(1,ws.max_column+1) if ws.cell(r,c).value is not None)
        e=r+1
        while e<=ws.max_row and any(ws.cell(e,c).value not in(None,'') for c in range(1,last+1)): e+=1
        rows=range(r+1,e)
        if cc:
            hit=sum(1 for i in list(rows)[:8] if str(ws.cell(i,cc).value or '').strip().lstrip('0') in prod)
            if hit<1: cc=None
        if sc:
            hs=sum(1 for i in list(rows)[:8] if sfind(ws.cell(i,sc).value))
            if hs<1 and not cc: sc=None
        if not(cc or sc): r=e; continue
        cols=[]
        if cc: cols+= [('Inventory group',lambda c:IG.get(prod.get(c,['',''])[0],'') if c in prod else ''),('Product category',lambda c:PC.get(prod[c][1],'') if c in prod else '')]
        newc=[]
        col=last+1
        def put(title,fn):
            global col
            ws.cell(r,col,title).font=copy(hf); ws.cell(r,col).fill=copy(hfill)
            ws.cell(r,col).alignment=Alignment(wrap_text=True,vertical='center')
            for i in rows: ws.cell(i,col,fn(i))
            ws.column_dimensions[L(col)].width=22; col+=1
        if cc:
            put('Inventory group',lambda i:(IG.get(prod[k][0],'') if (k:=str(ws.cell(i,cc).value or '').strip().lstrip('0')) in prod else ''))
            put('Product category',lambda i:(PC.get(prod[k][1],'') if (k:=str(ws.cell(i,cc).value or '').strip().lstrip('0')) in prod else ''))
        if sc:
            put('Supplier type',lambda i:(ST.get(s['t'],s['t']) if (s:=sfind(ws.cell(i,sc).value)) else ''))
            if not cc:
                put('Groups supplied (top by spend)',lambda i:(top(s['ig'],IG) if (s:=sfind(ws.cell(i,sc).value)) else ''))
                put('Categories supplied (top by spend)',lambda i:(top(s['pc'],PC) if (s:=sfind(ws.cell(i,sc).value)) else ''))
        elif cc and 'Supplier' not in hdr:
            put('Supplier types (item)',lambda i:', '.join(ST.get(t,t) for t in pt.get(str(ws.cell(i,cc).value or '').strip().lstrip('0'),[])))
        af=ws.auto_filter.ref
        if af:
            import re
            m=re.match(r'([A-Z]+)(\d+):([A-Z]+)(\d+)',af)
            if m and int(m.group(2))==r: ws.auto_filter.ref=f"{m.group(1)}{r}:{L(col-1)}{m.group(4)}"
        n+=1; r=e
    if n: stats[ws.title]=n
# lookup sheet
ds=wb.create_sheet('Dimensions')
ds['A1']='Dimensions lookup - Inventory group / Product category / Supplier type (source: Cure item master, SUPPLIERS+CODES; supplier columns from 2026 purchase lines)'
ds['A1'].font=Font(bold=True,size=12)
h=['Kind','Code / No.','Name','Inventory group','Product category','Supplier type(s)','Groups supplied','Categories supplied','2026 spend (SAR)']
for i,t in enumerate(h,1):
    c=ds.cell(3,i,t); c.font=copy(hf); c.fill=copy(hfill)
r=4
for k,v in sorted(d['prod'].items()):
    ds.append([]) if False else None
    for i,x in enumerate(['Item',k,'',IG.get(v[0],v[0]),PC.get(v[1],v[1]),', '.join(ST.get(t,t) for t in pt.get(k,[]))],1): ds.cell(r,i,x)
    r+=1
for n,s in sorted(supN.items()):
    for i,x in enumerate(['Supplier',s['no'],n,'','',ST.get(s['t'],s['t']),top(s['ig'],IG,6),top(s['pc'],PC,6),sum(s['ig'].values())],1): ds.cell(r,i,x)
    r+=1
ds.auto_filter.ref=f"A3:I{r-1}"; ds.freeze_panes='A4'
for i,w in enumerate([10,14,40,28,28,26,40,40,16],1): ds.column_dimensions[L(i)].width=w
wb.save(out); print(stats)
