import sys, re
from openpyxl import load_workbook
from openpyxl.workbook.properties import CalcProperties
from openpyxl.styles import Font, Alignment
p=sys.argv[1]; wb=load_workbook(p)
S=wb['Summary']
for row in S.iter_rows(min_row=1,max_row=6):
    for c in row:
        if isinstance(c.value,str) and 'dashboard Version' in c.value: c.value=re.sub(r'dashboard Version \d+','dashboard Version 31',c.value)
D=wb['Data Status']
D['A2']="Which figures are live. Everything rests on the full live re-extract of 20 Oct 2026 (the 5 October snapshot is kept only for comparison on the Live Check sheet). Refreshed 2026-10-21 from the Cure MCP (read-only)."
D['B5']="Live - 3,229 posted lines to 17 Oct 2026, net of 34 returned lines (SAR 68,866); price analyses leave out every invoice that has a return"
D['C5']="Watch-list, price changes, supplier gaps, savings and outliers skip any purchase invoice with a return (rule of 21 Oct 2026); spend totals stay net of returns (net SAR 4,386,100 against SAR 4,454,966 gross)"
D['B12']="Rebuilt 2026-10-21 on the full re-extract of 20 Oct"
D['B13']="Live pull 2026-09-22; re-checked 2026-10-20 (no event since 2025-12-31)"
D['A6'].value  # keep
r=D.max_row+1
# new rows appended before tie-outs would shift; add after the table at the bottom instead
D.cell(D.max_row+2,1,"Rules added 21 Oct 2026").font=Font(name='Arial',size=11,bold=True,color='0F6E5C')
rows=[("New items (Overstock / Slow-Moving)","An item needs about three months of consumption history; items first bought less than three months before the as-of date are left out (2 SKUs, SAR 20,117 on hand: 105262, 105282)"),
      ("Purchase returns (price analyses)","Any purchase invoice that has a return is left out of price changes, supplier gaps, savings and outliers"),
      ("Valuation Errors","Transfers received at a cost 2x or more away from the send cost (since 2024), purchases 3x or more away from the previous purchase (since Oct 2025), stock valued 2x or more away from the latest purchase cost")]
base=D.max_row+1
for i,(a,b) in enumerate(rows):
    D.cell(base+i,1,a).font=Font(name='Arial',size=10); c=D.cell(base+i,2,b); c.font=Font(name='Arial',size=10); c.alignment=Alignment(wrap_text=True,vertical='top')
for r in range(1,D.max_row+1):
    if D.cell(r,1).value=='Purchase lines (posted) 2026, gross': D.cell(r,2).value=3229
    if D.cell(r,1).value=='Last posted purchase date': D.cell(r,2).value='2026-10-17'
L=wb['Live Check']
for row in L.iter_rows():
    for c in row:
        if isinstance(c.value,str) and '8 Sep' in c.value: c.value=c.value.replace('8 September','5 October').replace('8 Sep','5 Oct')
wb.calculation=CalcProperties(fullCalcOnLoad=True)
wb.save(p); print('patched')
