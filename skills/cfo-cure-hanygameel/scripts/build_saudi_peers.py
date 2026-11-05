# -*- coding: utf-8 -*-
"""Saudi-listed healthcare peer set — Tadawul main market (TASI) and Nomu.
Figures collected 24 Sep 2026.  Market caps, EV, net debt, TTM EBITDA and P/E
from StockAnalysis.com (per-company as-of date recorded below); revenue, operating
profit and net income are audited FY2025 (all peers have 31 Dec year-ends).
"""
import json, statistics as st

# mkt, ticker, name, asof, mcap, revFY25, ebitdaTTM, opFY25, niFY25, netdebt, ev,
# ev_rev, ev_ebitda, pe, computed?, note
P = [
 ('TASI','4013','Dr. Sulaiman Al Habib Medical Services (HMG)','2026-09-20',
  79.80e9, 13707e6, 3.40e9, 2619e6, 2401e6, 7.35e9, 87.73e9, 6.01, 24.89, 32.98, False,
  'Largest private operator — hospitals, medical complexes, day surgery, retail pharmacy, home care; ~10,475 staff'),
 ('TASI','4002','Mouwasat Medical Services','2026-08-19',
  12.78e9, 3223e6, 1.15e9, 878.8e6, 822.0e6, 1.02e9, 13.95e9, 4.14, 12.08, 15.03, False,
  '7 hospitals, ~1,600 beds, ~600 clinics — Eastern Province weighted'),
 ('TASI','4004','Dallah Healthcare','2026-08-26',
  10.22e9, 4067e6, 721.1e6, 594.4e6, 538.3e6, 4.14e9, 14.39e9, 3.35, 17.55, 23.34, False,
  '4 hospitals, ~1,154 beds, plus Dallah Clinics and home care'),
 ('TASI','4005','National Medical Care (Care)','2026-09-08',
  5.36e9, 1600e6, 423.2e6, 354.5e6, 318.5e6, 555.6e6, 5.92e9, 3.56, 12.96, 17.90, False,
  'Riyadh hospitals and medical centres, home health, stake in a pharma distributor'),
 ('TASI','4007','Al Hammadi Holding','2026-09-08',
  3.92e9, 1235e6, 303.6e6, 257.9e6, 241.9e6, 231.2e6, 4.16e9, 3.26, 11.67, 16.77, False,
  '2 Riyadh hospitals, 600 rooms / ~180 outpatient clinics; Al Olaya opening 2026'),
 ('TASI','4009','Middle East Healthcare (Saudi German Health)','2026-09-01',
  3.04e9, 3103e6, 583.8e6, 387.3e6, 301.9e6, 2.40e9, 5.50e9, 1.77, 9.42, 20.02, True,
  '6 Saudi German tertiary hospitals; shares down ~47% over the year'),
 ('TASI','4017','Dr. Soliman Fakeeh Hospital (Fakeeh Care)','2026-08-14',
  7.87e9, 3090e6, 380.3e6, 308.0e6, 290.2e6, 856.1e6, 9.14e9, 2.95, 20.63, 33.94, False,
  '4 hospitals incl. Dubai, ~5 medical centres; manages NEOM Hospital and KAUST Health'),
 ('TASI','4018','Almoosa Health','2026-09-03',
  5.33e9, 1416e6, 295.8e6, 219.6e6, 236.5e6, 1.38e9, 6.70e9, 4.47, 21.72, 32.59, False,
  '2 hospitals in Al Ahsa, ~730 beds; 2 more under construction'),
 ('Nomu','9546','Naba Alsaha Medical Services','2026-07-22',
  441.0e6, 201.8e6, 42.1e6, 32.4e6, 27.5e6, 103.8e6, 544.8e6, 2.70, 12.63, 16.02, False,
  'Operates and manages private and government hospitals; Al Zahraa Hospital plus a pharmacy'),
 ('Nomu','9594','Al-Modawat Specialized Medical','2026-09-24',
  339.9e6, 121.8e6, 26.0e6, 24.0e6, 19.0e6, 16.6e6, 356.5e6, 2.57, 11.80, 23.16, False,
  'One general hospital in Muhayil, Asir; inpatient capacity up ~60%, 42 clinics added'),
 ('Nomu','9626','Basma Adeem Medical (Smile Care)','2026-09-24',
  108.4e6, 45.5e6, 11.2e6, 8.1e6, 7.3e6, -18.7e6, 89.7e6, 1.63, 6.71, 11.37, False,
  'Dental, orthodontics, implants, dermatology — 2 Riyadh clinics; listed Feb 2026'),
 ('Nomu','9620','Balsm Alofoq Medical','2026-09-15',
  58.75e6, 20.4e6, 3.4e6, 2.5e6, 2.0e6, -9.3e6, 49.4e6, 2.43, 13.41, 29.86, False,
  'Medical complexes, clinics, day surgery and labs, plus medical-supplies wholesale'),
]
EXCL = [
 ('TASI','4014','Scientific and Medical Equipment House','Equipment supply, maintenance, manpower and facilities — runs no hospitals of its own'),
 ('Nomu','9530','Arabian International Healthcare Holding (Tibbiyah)','Distributor and maintainer of medical devices and imaging — not a provider'),
 ('Nomu','9572','Al-Razi Medical','Mostly retail and wholesale of medical devices; some complexes and day surgery'),
 ('Nomu','9544','Future Care Trading','Asset-light home medical visits, nursing, mobile clinics — not facility-based'),
 ('Nomu','9587','Lana Medical','Medical-waste management, equipment sales and construction — a vendor to the sector'),
]
K=['mkt','ticker','name','asof','mcap','rev','ebitda','op','ni','netdebt','ev','ev_rev','ev_ebitda','pe','computed','note']
peers=[dict(zip(K,p)) for p in P]
for p in peers:
    p['ebitda_margin']=p['ebitda']/p['rev']
    p['net_margin']=p['ni']/p['rev']
med=lambda xs: st.median(xs)
tasi=[p for p in peers if p['mkt']=='TASI']; nomu=[p for p in peers if p['mkt']=='Nomu']
out={'peers':peers,
     'excluded':[dict(zip(['mkt','ticker','name','why'],e)) for e in EXCL],
     'med':{'TASI':{'ev_rev':med([p['ev_rev'] for p in tasi]),'ev_ebitda':med([p['ev_ebitda'] for p in tasi]),
                    'ebitda_margin':med([p['ebitda_margin'] for p in tasi]),'n':len(tasi)},
            'Nomu':{'ev_rev':med([p['ev_rev'] for p in nomu]),'ev_ebitda':med([p['ev_ebitda'] for p in nomu]),
                    'ebitda_margin':med([p['ebitda_margin'] for p in nomu]),'n':len(nomu)}},
     'asof':'2026-09-24',
     'source':'StockAnalysis.com (market cap, EV, net debt, TTM EBITDA, P/E; per-company as-of date shown), audited FY2025 statements for revenue and earnings, Argaam and Saudi Exchange for listings and profiles',
     'discount':0.75}
json.dump(out, open('data_peers.json','w'), ensure_ascii=False, separators=(',',':'))
print('TASI median EV/Rev %.2f  EV/EBITDA %.2f  EBITDA margin %.1f%%'%(out['med']['TASI']['ev_rev'],out['med']['TASI']['ev_ebitda'],out['med']['TASI']['ebitda_margin']*100))
print('Nomu median EV/Rev %.2f  EV/EBITDA %.2f  EBITDA margin %.1f%%'%(out['med']['Nomu']['ev_rev'],out['med']['Nomu']['ev_ebitda'],out['med']['Nomu']['ebitda_margin']*100))
rev=56966114.4333474; ebitda=3823927.88388121
d=out['discount']
print('\nAl Faihaa FY2025 revenue %.0f  EBITDA %.0f  margin %.1f%%'%(rev,ebitda,ebitda/rev*100))
for m in ('Nomu','TASI'):
    print('  via %s median: EV/Rev %.2fx -> %.0f   EV/EBITDA %.2fx -> %.0f'%(
        m, out['med'][m]['ev_rev']*d, rev*out['med'][m]['ev_rev']*d,
        out['med'][m]['ev_ebitda']*d, ebitda*out['med'][m]['ev_ebitda']*d))
print('bytes', len(open('data_peers.json').read()))
