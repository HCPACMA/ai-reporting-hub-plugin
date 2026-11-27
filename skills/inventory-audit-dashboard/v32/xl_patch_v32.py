import sys,json,re,copy
from openpyxl import load_workbook
from openpyxl.workbook.properties import CalcProperties
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
SRC,CHK,OUT=sys.argv[1],sys.argv[2],sys.argv[3]
C=json.load(open(CHK,encoding='utf-8')); wb=load_workbook(SRC)
src=open('/home/claude/w/v27/build_xlsx_refresh.py',encoding='utf-8').read()
a=src.index('FONT = "Arial"'); b=src.index('W = A["watchlist"]')
from openpyxl.styles import PatternFill, Border, Side
ns=dict(wb=wb,Font=Font,PatternFill=PatternFill,Alignment=Alignment,Border=Border,Side=Side,get_column_letter=get_column_letter)
exec(src[a:b],ns)
fresh,table,kv,section=ns['fresh'],ns['table'],ns['kv'],ns['section']
AMBER,RED,GREEN,M0,M2,M4,Q1=ns['AMBER'],ns['RED'],ns['GREEN'],ns['M0'],ns['M2'],ns['M4'],ns['Q1']
def addcols(ws,hdr_row,heads,widths):
    last=ws.max_column
    for j,(h,w) in enumerate(zip(heads,widths),1):
        c=ws.cell(hdr_row,last+j,h); s=ws.cell(hdr_row,last); c.font=copy.copy(s.font); c.fill=copy.copy(s.fill); c.alignment=copy.copy(s.alignment); c.border=copy.copy(s.border)
        ws.column_dimensions[get_column_letter(last+j)].width=w
    return last
def style_like(ws,r,col,ref_col):
    c=ws.cell(r,col); s=ws.cell(r,ref_col); c.font=copy.copy(s.font); c.border=copy.copy(s.border); c.alignment=copy.copy(s.alignment)
# ---- savings status columns
ws=wb['Savings Opportunities']; st={r['product']:r for r in C['savings']['rows']}
last=addcols(ws,5,['Latest purchase from','Latest purchase date','Status'],[34,14,12])
for r in range(6,ws.max_row+1):
    p=ws.cell(r,1).value
    if p in st:
        s=st[p]
        for j,v in enumerate([s['last_supplier'],s['last_date'],s['status']],1):
            ws.cell(r,last+j,v); style_like(ws,r,last+j,last)
        if s['status']=='realized':
            for j in range(1,last+4): ws.cell(r,j).fill=GREEN
ws.auto_filter.ref=f"A5:{get_column_letter(ws.max_column)}{ws.max_row}"
k=C['savings']['kpi']
ws['A2']=ws['A2'].value+f" STATUS (24 Oct 2026): {k['realized']} of {k['total']} opportunities are already realized (green) - the latest purchase of the product was from the cheapest supplier; {k['open']} are still open."
# ---- count-created % on overstock / slow-moving
ctm={(r['product'],r['branch']):r for r in C['ct']['rows']}
for name in ('Overstock','Slow-Moving'):
    ws=wb[name]; last=addcols(ws,5,['Count-created qty','Count-created %'],[14,14])
    for r in range(6,ws.max_row+1):
        c=ctm.get((str(ws.cell(r,3).value),ws.cell(r,1).value))
        v1,v2=(c['ct_qty'],c['ct_pct']/100) if c else (0,0)
        ws.cell(r,last+1,v1).number_format=M0; ws.cell(r,last+2,v2).number_format='0%'
        for j in (1,2): style_like(ws,r,last+j,5)
        ws.cell(r,last+1).number_format=M0; ws.cell(r,last+2).number_format='0%'
        if v2>=0.5: ws.cell(r,last+2).fill=AMBER
    ws.auto_filter.ref=f"A5:{get_column_letter(ws.max_column)}{ws.max_row}"
# ---- Count-created sheet
K=C['ct']['kpi']; idx=wb.sheetnames.index('Valuation Errors')+1
ws=fresh('Count-Created Stock','Stock created by counts and still on hand',
  'Batches created by a stock count (batch no. starting CT) that still have quantity on hand. These units were never purchased: they come from a count that found more than the system showed, booked at the current cost. Where they are most of the balance, or the line is also Overstock / Slow-moving, re-check physically before treating it as over-buying. Based on batch-tracked items in the 20 Oct 2026 extract.',index=idx,tab='B9852F')
r=kv(ws,4,[('Count-created stock value (SAR)',K['value']),('Share of total stock value',K['pct_of_stock']/100),('Units',K['units']),('Product-store lines',K['skus']),('Lines where >=50% of the balance is count-created',K['mostly_ct']),('Lines also in Overstock',K['in_overstock']),('  value (SAR)',K['in_overstock_value']),('Lines also in Slow-moving',K['in_slow']),('  value (SAR)',K['in_slow_value'])],
  {'Count-created stock value (SAR)':M0,'Share of total stock value':'0.00%','  value (SAR)':M0})
table(ws,r,['Branch','Code','Product','On hand','Count-created qty','Share','Unit cost','Count-created value (SAR)','On-hand value (SAR)','CT batches','Earliest expiry','In Overstock','In Slow-moving'],
  [[x['branch'],x['product'],x['product_name'],x['on_hand'],x['ct_qty'],x['ct_pct']/100,x['unit_cost'],x['ct_value'],x['on_hand_value'],x['batches'],x['earliest_expiry'],'yes' if x['in_overstock'] else '','yes' if x['in_slow'] else ''] for x in C['ct']['rows']],
  {4:M0,5:M0,6:'0%',7:M4,8:M0,9:M0,10:M0},[12,10,38,10,14,8,11,16,16,10,13,11,12],filt=True,fills=lambda x: AMBER if x[5]>=0.5 else None)
ws.freeze_panes='A4'
# ---- UOM sheet
U=C['uom']; UK=U['kpi']
ws=fresh('UOM Pack Mismatch','Pack / UOM mismatches - the same code bought in different packs',
  f"The ERP stores cost per primary unit, so one code bought as PC and as a box should give the same cost per unit. Signals: 'high' = the higher cost equals the lower cost x the pack size (a box price booked per piece, e.g. 102922: 185.225 = 26.46 x 7); 'medium' = cost differs 3x or more between packs with no pack-size explanation; 'low' = several packs, costs consistent. Purchases from {UK['since']}; invoices later returned are not removed here.",index=idx+1,tab='B9852F')
r=kv(ws,4,[('Products bought in 2+ pack sizes',UK['skus']),('High - cost equals a pack multiple',UK['high']),('  on-hand value (SAR)',UK['value_high']),('Medium - large cost gap',UK['medium']),('Low - pack mix only',UK['low']),('On-hand value of all products (SAR)',UK['value_all'])],
  {'  on-hand value (SAR)':M0,'On-hand value of all products (SAR)':M0})
rows=[]
for x in U['rows']:
    for v in x['variants']:
        rows.append([x['product'],x['product_name'],x['severity'],v['uom'],v['factor'],v['lines'],v['qty'],v['min_cost'],v['max_cost'],v['last'],x['ratio'],x['reason'],x['on_hand'],x['on_hand_value']])
table(ws,r,['Code','Product','Signal','Pack (UOM)','Pack size','Lines','Qty (packs)','Lowest cost / unit','Highest cost / unit','Last purchase','Gap across packs (x)','Why flagged','On hand','On-hand value (SAR)'],rows,
  {5:M0,6:M0,7:M0,8:M4,9:M4,11:Q1,13:M0,14:M0},[10,36,9,11,9,7,11,14,14,13,12,44,10,15],filt=True,fills=lambda x: RED if x[2]=='high' else (AMBER if x[2]=='medium' else None))
ws.freeze_panes='A4'
# ---- Data Status + Summary
D=wb['Data Status']
D.cell(D.max_row+2,1,'Rules added 24 Oct 2026').font=Font(name='Arial',size=11,bold=True,color='0F6E5C')
rows=[('Savings opportunities - realized','An opportunity is realized when the latest purchase of the product was from the cheapest supplier (status column on Savings Opportunities)'),
      ('Count-created stock','Batches starting CT with quantity on hand = units created by a stock count, not bought; shown on Count-Created Stock and as a column on Overstock / Slow-Moving'),
      ('UOM / pack mismatch','Same code bought in 2+ pack sizes since 1 Jan 2025; flagged when cost per primary unit differs by a pack multiple or by 3x or more (UOM Pack Mismatch sheet)')]
base=D.max_row+1
for i,(x,y) in enumerate(rows):
    D.cell(base+i,1,x).font=Font(name='Arial',size=10); c=D.cell(base+i,2,y); c.font=Font(name='Arial',size=10); c.alignment=Alignment(wrap_text=True,vertical='top')
S=wb['Summary']
for row in S.iter_rows(min_row=1,max_row=6):
    for c in row:
        if isinstance(c.value,str) and 'dashboard Version' in c.value: c.value=re.sub(r'dashboard Version \d+','dashboard Version 32',c.value)
wb.calculation=CalcProperties(fullCalcOnLoad=True)
wb.save(OUT); print(wb.sheetnames[-6:])
