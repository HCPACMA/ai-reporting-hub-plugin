# -*- coding: utf-8 -*-
"""Merge the account-level expense series into DATA.ifrs and verify the
IFRS 18 statement ties to the audited FY2025 figures."""
import json, collections

BASE = json.load(open('data_ifrs.json'))
EXP  = json.load(open('exp_ser.json'))
MONTHS = BASE['months']; MI = {m: i for i, m in enumerate(MONTHS)}

NAMES = {
 '3110000':['قرطاسية وأدوات مكتبية','Stationery'],
 '3120001':['إصلاح وصيانة آلات ومعدات','Repairs — plant & equipment'],
 '3120002':['إصلاح وصيانة سيارات','Repairs — vehicles'],
 '3120003':['إصلاح وصيانة متنوع','Repairs — general'],
 '3120004':['تأثيث سكنات','Staff housing furnishing'],
 '3130001':['تذاكر سفر','Air tickets'],
 '3130002':['سفر وانتقال','Travel & transport'],
 '3140001':['رسوم حكومية وإقامات ورخص','Government fees, iqamas & licences'],
 '3140002':['تأمينات اجتماعية (GOSI)','Social insurance (GOSI)'],
 '3140003':['تصديق خطابات','Letter attestation'],
 '3140004':['مخالفات حكومية وتعويضات','Government fines & penalties'],
 '3140005':['أتعاب استقدام كوادر فنية','Recruitment fees'],
 '3140006':['أتعاب استشارات','Consultancy fees'],
 '3140007':['رسوم دورات تدريبية','Training course fees'],
 '3140009':['تأمين سيارات','Vehicle insurance'],
 '3150001':['نقل وشحن','Freight & carriage'],
 '3150002':['توصيل طلبيات','Order delivery'],
 '3160000':['محروقات وغيار زيت','Fuel & lubricants'],
 '3170001':['نظافة','Cleaning'],
 '3170002':['مغسلة','Laundry'],
 '3180001':['هاتف وإنترنت','Telephone & internet'],
 '3180002':['كهرباء','Electricity'],
 '3180003':['مياه','Water'],
 '3190001':['رواتب','Salaries'],
 '3190003':['مكافآت','Bonuses'],
 '3190004':['بدل إجازة','Leave allowance'],
 '3190005':['إضافي','Overtime'],
 '3190006':['نسب','Commissions'],
 '3190007':['تعويضات عاملين','Staff compensation'],
 '3200000':['مكافأة مجلس الإدارة','Board remuneration'],
 '3210000':['إكراميات','Gratuities'],
 '3220000':['علاج عاملين','Staff medical care'],
 '3230000':['إيجارات','Rent'],
 '3240000':['حراسة','Security'],
 '3250001':['ضيافة','Hospitality'],
 '3250002':['ضيافة (2)','Hospitality (2)'],
 '3260000':['إفطار رمضان','Ramadan iftar'],
 '3270000':['دعاية وإعلان وتسويق','Advertising & marketing'],
 '3280001':['مصروف الإهلاك','Depreciation'],
 '3280003':['تكلفة الخدمة الحالية — نهاية الخدمة','Current service cost — EOSB'],
 '3280004':['خصم إضافي عملاء شركات التأمين','Additional discount — insurance payers'],
 '3280005':['مخصص الزكاة الشرعية','Zakat provision'],
 '3300001':['أغراض منصرفة من المستودع','Stores issued'],
 '3300002':['أغراض ومهمات وزي للعمل','Supplies & uniforms'],
 '3300003':['تسويات جردية وبضاعة تالفة','Inventory adjustments & damaged goods'],
 '3310000':['نفايات طبية','Medical waste'],
 '3320001':['مصاريف شركات تأمين (1)','Insurer charges (1)'],
 '3320002':['مصاريف شركات تأمين (2)','Insurer charges (2)'],
 '3320004':['رسوم رفع مطالبات التأمين','Claim submission fees'],
 '3330001':['تحاليل وأشعة خارجية','External labs & radiology'],
 '3330002':['تركيبات أسنان','Dental prosthetics'],
 '3330003':['عدسات عيون','Optical lenses'],
 '3350000':['أتعاب مراجعة','Audit fees'],
 '3360000':['مصاريف أخرى','Other charges'],
 '3370000':['تكلفة مشتريات أدوية التأمين','Insurance drug purchases'],
 '3380000':['خسائر رأسمالية','Losses on disposal'],
 '3290003':['مصاريف بنكية أخرى','Other bank charges'],
 '3390000':['تكلفة العمولة على التزامات منافع الموظفين','Interest cost on employee benefit obligations'],
}

# nature group -> (ar, en, [accounts])
NAT = [
 ('emp',   'الرواتب ومزايا الموظفين','Employee benefits',
    ['3190001','3190003','3190004','3190005','3190006','3190007','3140002','3220000','3280003','3200000']),
 ('cons',  'المستلزمات الطبية والمستهلكات','Medical supplies & consumables',
    ['3300001','3300002','3310000']),
 ('extmed','خدمات طبية خارجية','External medical services',
    ['3330001','3330002','3330003','3370000']),
 ('insadm','مصاريف شركات التأمين','Insurance company charges',
    ['3320004','3320001','3320002']),
 ('ded',   'حسميات مطالبات التأمين (تسوية سنوية)','Insurance claim deductions (annual true-up)',
    ['3280004']),
 ('dep',   'الإهلاك','Depreciation',['3280001']),
 ('rent',  'الإيجارات','Rent',['3230000']),
 ('util',  'الكهرباء والمياه والاتصالات','Utilities',['3180001','3180002','3180003']),
 ('maint', 'الإصلاح والصيانة','Repairs & maintenance',['3120001','3120002','3120003','3120004']),
 ('govt',  'الرسوم الحكومية والتراخيص','Government fees & licences',['3140001','3140003','3140004','3140009']),
 ('prof',  'أتعاب مهنية واستقدام وتدريب','Professional, recruitment & training fees',
    ['3140005','3140006','3140007','3350000']),
 ('fac',   'النظافة والمغسلة والحراسة','Cleaning, laundry & security',['3170001','3170002','3240000']),
 ('trav',  'السفر والانتقال والنقل','Travel & transport',['3130001','3130002','3150001','3150002','3160000']),
 ('admin', 'مصاريف إدارية أخرى','Other administrative expenses',
    ['3110000','3210000','3250001','3250002','3260000','3270000','3360000']),
 ('wdown', 'تسويات جردية وبضاعة تالفة','Inventory adjustments & write-downs',['3300003']),
 ('disp',  'خسائر استبعاد أصول','Losses on disposal of assets',['3380000']),
 ('bankc', 'عمولات بنكية','Bank charges',['3290002']),
]
OUTSIDE = {'3290001':'financing','3390000':'financing','3280005':'zakat'}

covered = set(OUTSIDE)
for g in NAT: covered |= set(g[3])
have = {k.split('|')[0] for k in EXP} | {k.split('|')[0] for k in BASE['ser']}
miss = {a for a in have if a.startswith('3')} - covered
assert not miss, ('uncovered expense accounts', miss)

BASE['ser'].update(EXP)
BASE['acc'].update(NAMES)
BASE['nat'] = [[k, ar, en, accs] for k, ar, en, accs in NAT]
json.dump(BASE, open('data_ifrs.json','w'), ensure_ascii=False, separators=(',',':'))
print('accounts', len({k.split("|")[0] for k in BASE["ser"]}), 'series', len(BASE['ser']),
      'bytes', len(open('data_ifrs.json').read()))

# ---------------- verification: FY2025 -----------------------------------
CCS = ['00','01','02','03','04']
a, b = MI['2025-01'], MI['2025-12']
def acc(x):
    return sum(sum(BASE['ser'][x+'|'+c][a:b+1]) for c in CCS if x+'|'+c in BASE['ser'])
def grp(g):
    return sum(acc(x) for x in dict((k,accs) for k,_,_,accs in NAT)[g])
opex = sum(grp(g[0]) for g in NAT)
rev  = 57099067.0                     # cash + credit − contra, from DATA.m
othop = -sum(acc(x) for x in ['4300001','4300002','4300004','4300005','4300006']) - acc('4300008')
inv   = -acc('4300003') - acc('4300009')
fin   = acc('3290001') + acc('3390000')
zak   = acc('3280005')
op    = rev + othop - opex
print('\nFY2025 — corrected IFRS 18 statement')
for k, ar, en, accs in NAT: print('  %-7s %-42s %12s' % (k, en, format(round(sum(acc(x) for x in accs)), ',')))
print('  revenue                                          %12s' % format(round(rev),','))
print('  other operating income                           %12s' % format(round(othop),','))
print('  OPERATING PROFIT                                 %12s' % format(round(op),','))
print('  investing                                        %12s' % format(round(inv),','))
print('  PBFT                                             %12s' % format(round(op+inv),','))
print('  financing                                        %12s' % format(round(fin),','))
print('  PROFIT BEFORE ZAKAT                              %12s   (audited 1,922,881)' % format(round(op+inv-fin),','))
print('  zakat                                            %12s' % format(round(zak),','))
print('  PROFIT                                           %12s   (audited 1,775,238)' % format(round(op+inv-fin-zak),','))
