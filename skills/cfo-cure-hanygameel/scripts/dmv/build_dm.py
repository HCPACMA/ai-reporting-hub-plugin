import json, collections, sys, os
ALLOCF=os.environ.get('ALLOCF','r_alloc.json')
from parse import rows
from bsline import bs_line
NM=json.load(open('/home/claude/work/gl/acc_names.json'))
ALLOC=collections.defaultdict(float); NV=collections.defaultdict(int)
for a,n,r,br in rows(ALLOCF):
    for it in r.split(';'):
        ym,amt,nv=it.split(':'); ALLOC[(a,ym)]+=float(amt); NV[(a,ym)]+=int(nv)
CASH=collections.defaultdict(float); CASHM=collections.defaultdict(float)
for a,r,br in rows('r_cash.json'):
    for it in r.split(';'):
        ym,amt=it.split(':'); CASH[(a,ym)]+=float(amt); CASHM[ym]+=float(amt)
# ---- direct-method line for a counter account (mirrors the indirect statement's categories)
def dm(a):
    k=bs_line(a); p=a[:3]
    if k in ('fixed_net','wip') or a.startswith(('1110','1120','113','1111','1121')) or a in ('4300008','3380000','1410000','3280001','3280002'): return ('CFI','capex')
    if k=='lt_loans' or a.startswith(('2112','2113','2125')) or a in ('3290001','1262000'): return ('CFF','loans')
    if k=='dividends_payable' or a.startswith('2128'): return ('CFF','div')
    if a.startswith(('221','222','223')): return ('CFF','equity')
    if a=='1240007': return ('CFO','r_ins')
    if a.startswith('1240') and a!='1240008': return ('CFO','r_corp')
    if a.startswith('13') or a.startswith('14') or a.startswith('41') or a.startswith('42'): return ('CFO','r_pat')
    if a.startswith('43') or a=='2123001': return ('CFO','r_oth')
    if a.startswith('332'): return ('CFO','p_insfee')
    if a.startswith('2121') or a.startswith('319') or a in ('2111001','2111003','2123201','3140002','3220000','1253000') or a.startswith('1265') or a=='1390000': return ('CFO','p_staff')
    if a.startswith('2122') or a=='2124000' or a.startswith('123') or a.startswith('330') or a.startswith('333'): return ('CFO','p_sup')
    if a in ('1263000','21230071','21230072') : return ('CFO','p_vat')
    if a in ('2123003','3280005'): return ('CFO','p_zak')
    if a=='3140001' or a=='1251000' or a.startswith('3140'): return ('CFO','p_gov')
    if a.startswith('2126') or a.startswith('1246') or k in ('related_party','due_related_party'): return ('CFO','p_owner')
    if a in ('2123006','1266000'): return ('CFO','susp')
    return ('CFO','p_opex')
LINES=[('CFO','r_pat','Receipts from patients (cash, network, visa, transfer, Tabby)','مقبوضات من المرضى (نقدي/شبكة/فيزا/تحويل/تابي)'),
 ('CFO','r_ins','Receipts from insurance companies','مقبوضات من شركات التأمين'),
 ('CFO','r_corp','Receipts from corporate & instalment customers','مقبوضات من عملاء الشركات والتقسيط'),
 ('CFO','r_oth','Other operating receipts','مقبوضات تشغيلية أخرى'),
 ('CFO','p_staff','Paid to and for employees','مدفوعات للموظفين ونيابة عنهم'),
 ('CFO','p_sup','Paid to suppliers','مدفوعات للموردين'),
 ('CFO','p_gov','Government fees, iqamas & licences','رسوم حكومية وإقامات وتراخيص'),
 ('CFO','p_insfee','Insurance rejections, commissions & claim fees','مرفوضات وعمولات ورسوم مطالبات التأمين'),
 ('CFO','p_opex','Other operating expenses paid','مصروفات تشغيلية أخرى مدفوعة'),
 ('CFO','p_vat','VAT paid (net)','ضريبة القيمة المضافة المدفوعة (صافي)'),
 ('CFO','p_zak','Zakat paid','زكاة مدفوعة'),
 ('CFO','p_owner','Owner & related-party accounts','حسابات المالك والأطراف ذات العلاقة'),
 ('CFO','susp','Suspense & cheques under settlement','حسابات تحت التسوية وشيكات تحت التحصيل'),
 ('CFI','capex','Property, equipment & projects (net)','أصول ثابتة ومشروعات (صافي)'),
 ('CFF','loans','Loans drawn / repaid incl. interest','قروض مستلمة / مسددة شاملة الفوائد'),
 ('CFF','div','Dividends paid','توزيعات أرباح مدفوعة'),
 ('CFF','equity','Capital & equity accounts','رأس المال وحقوق الملكية')]
Y=lambda ym:int(ym[:4])
yr=collections.defaultdict(lambda: collections.defaultdict(float)); acc_y=collections.defaultdict(lambda: collections.defaultdict(float))
for (a,ym),v in ALLOC.items():
    c,l=dm(a); yr[Y(ym)][l]+=v; acc_y[(l,a)][Y(ym)]+=v
cash_y=collections.defaultdict(float)
for (a,ym),v in CASH.items(): cash_y[Y(ym)]+=v
cfa=json.load(open('/home/claude/work/gl/data_cfa_gl.json'))
print('check1 monthly: max |Σalloc − Δcash| =', max(abs(sum(v for (a,ym),v in ALLOC.items() if ym==m)-CASHM[m]) for m in CASHM))
run=0; open_={}
for y in sorted(cash_y):
    open_[y]=run; run+=cash_y[y]
print('\nyear  CFO_dir  CFI_dir  CFF_dir  NET  close_calc  close_BS  diff | CFO_ind  CFI_ind  CFF_ind  ΔCFO')
for y in cfa['years']:
    d=yr[y]; cat=lambda C: sum(v for l,v in d.items() if [x for x in LINES if x[1]==l][0][0]==C)
    CFO,CFI,CFF=cat('CFO'),cat('CFI'),cat('CFF'); close=open_[y]+cash_y[y]
    v=cfa['v'][str(y)]; bs=cfa['bs'][str(y)]['cash']
    print(y, *['%12.0f'%x for x in (CFO,CFI,CFF,CFO+CFI+CFF,close,bs,close-bs,v['CFO'],v['CFI'],v['CFF'],CFO-v['CFO'])])
json.dump({'yr':{y:dict(d) for y,d in yr.items()}},open('dm_year.json','w'))
print()
for l in LINES:
    print(l[1].ljust(9), ' '.join('%12.0f'%yr[y][l[1]] for y in cfa['years']))
