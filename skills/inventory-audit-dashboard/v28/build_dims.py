import json,pickle,collections
S='/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad'
A=json.load(open(f'{S}/refresh/audit_v27.json'))
ext=pickle.load(open(f'{S}/inv/new_extract.pkl','rb'))
h,rows=ext['Products+Costing']; ix={k:i for i,k in enumerate(h)}
P={r[ix['product_code']]:(r[ix['inv_group']],r[ix['product_category']]) for r in rows}

EXTRA={'0050127':(5,6),'0050580':(5,6),'0050728':(5,6),'0050797':(5,6),'0100271':(10,31),'0170122':(17,1),'0200012':(20,70),'0250005':(25,80),'0330034':(33,16),'0330037':(33,16),'0330073':(33,16),'0330094':(33,16),'0330268':(33,16),'0360003':(36,68),'0360007':(36,68),'0360030':(36,68),'0390030':(39,10),'0390060':(39,10),'0390080':(39,10),'0390294':(39,10),'0390299':(39,10),'0390300':(39,10),'0390359':(39,10),'0390438':(39,10),'0390442':(39,10),'0390538':(39,10),'0502384':(5,10),'102485':(33,72),'102543':(39,72),'3100067':(31,80)}
for k,v in EXTRA.items(): P.setdefault(k,(str(v[0]),str(v[1])))
def n(x):
    if x in (None,''): return ''
    try: return str(int(float(x)))
    except: return str(x)
# codes used anywhere in the dashboard data
codes=set()
def walk(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in('product','product_code','code','sku') and isinstance(v,str): codes.add(v)
            else: walk(v)
    elif isinstance(o,list):
        for v in o: walk(v)
walk(A)
IG={'1':'Pediatrics','2':'Internal Medicine','3':'Obstetrics & Gynecology','4':'General Surgery','5':'Dental','6':'E.N.T','7':'Chest','8':'Urology','9':'Orthopaedics','10':'Dermatology','11':'Opthalmology','12':'General practitioner','13':'Plastic Surgery','14':'Consultation','15':'Emergency','16':'Physiotherapy','17':'Laboratory','18':'X-Ray Department','19':'Pharmacy','20':'Renal Dialysis','21':'Stock Items','22':'Office Supplies','23':'prints','24':'Medical trash','25':'Cleaning tools','26':'Laboratory supplies (kits)','27':'Worker Examination','28':'Comprehensive examination','29':'Medical certificates','30':'Sterilization materials','31':'Medical Supplies','32':'Medical tools','33':'medicine','34':'Teeth implant','35':'Radiology Supplies','36':'Vaccinations','37':'Home visit','38':'Home Care','39':'Disposable items','40':'Rent','41':'Cupping Clinic'}
PC={'1':'LA-Laboratory','2':'XR-Radiology','4':'PS-Plastic Surgery','6':'Dental','7':'General Surgery','9':'CN-Consultation','10':'Medical Consumables','12':'Home visit','13':'DP-Dental Prostheis','14':'Obstetrics & Gynecology','16':'ER-Medicine','18':'UR-Urology','20':'Opthalmology','24':'E.N.T','26':'Rounding','27':'Pediatrics','30':'Internal Medicine','31':'Dermatology','33':'Physeotherapy','35':'Chest','37':'ST-Orthopedics','58':'Worker Examination','59':'Cardiology','60':'Comprehensive examination','61':'General Practitioner','62':'Neuro Surgeries Services','63':'Pharmacy','64':'Rent','65':'(blank)','66':'Devices Stock','67':'Cosmetics','68':'Vaccinations','69':'Maintenance Consumable','70':'Renal Dialysis','71':'Computer Consumable','72':'Stock Items','73':'Medical certificates','74':'Lab Consumable','75':'Office Supplies','76':'Home Care','77':'radilogy supplies','79':'prints','80':'cleaning tools','81':'Sterilization materials','82':'Medical tools','83':'Cupping Clinic'}
ST={'F':'Fixed Assets','P':'Pharmacuticals','C':'Consumbles','D':'Dental suppliers','R':'Suppliers Rentals','S':'Suppliers clinics','W':'Suppliers warehouse','10':'Lab Consumabels','11':'Dental Consumabels','12':'Dermal Consumabels','13':'PRINTING MARKETING','O':'Others'}
# supplier types of the 64 suppliers (from SUPPLIERS.PREFIX_CATEGORY)
stype=dict(l.split() for l in """M0002 W
M0005 W
S0003 W
S0009 W
S0012 W
S0017 W
S0027 W
S0045 W
S0051 W
S0053 W
S0086 W
S0087 W
S0117 W
S0132 W
S0144 W
S0168 W
S0183 W
S0267 S
S0304 W
S0355 W
S0372 W
S0383 W
S0417 S
S0436 W
S0440 W
S0473 W
S0478 W
S0483 W
S0485 W
S0489 S
S0508 S
S0517 W
S0521 W
S0536 10
S0538 W
S0547 W
S0548 10
S0551 W
S0554 W
S0560 10
S0561 S
S0563 W
S0565 10
S0568 10
S0571 10
S0575 10
S0576 10
S0579 W
S0580 10
S0581 F
S0585 F
S0586 W
S0587 F
S0588 F
S0589 F
S0591 W
S0593 W
S0597 W
S0599 W
S0601 S
S0604 W
S0607 W
S0608 W
S0610 W""".split('\n'))
assert len(stype)==64
names=json.load(open(f'{S}/watch/supplier_names.json'))
pi=json.load(open(f'{S}/watch/pi_live_raw.json'))  # product, supplier, date, qty, cost
prod={};missing=0
for c in codes:
    if c in P: prod[c]=[n(P[c][0]),n(P[c][1])]
    else: missing+=1
# add every product that appears in purchase lines
for r in pi:
    if r[0] in P: prod.setdefault(r[0],[n(P[r[0]][0]),n(P[r[0]][1])])
sup={}; pt=collections.defaultdict(set)
for no,nm in names.items(): sup[nm]={'no':no,'t':stype[no],'ig':{},'pc':{}}
for p,s,d,q,c in pi:
    if s not in names or p not in P: continue
    nm=names[s]; ig,pc=n(P[p][0]),n(P[p][1]); amt=round(q*c,2)
    sup[nm]['ig'][ig]=round(sup[nm]['ig'].get(ig,0)+amt); sup[nm]['pc'][pc]=round(sup[nm]['pc'].get(pc,0)+amt)
    pt[p].add(stype[s])
used_ig={v[0] for v in prod.values()}|{k for s in sup.values() for k in s['ig']}
used_pc={v[1] for v in prod.values()}|{k for s in sup.values() for k in s['pc']}
D={'ig':{k:IG.get(k,'Group '+k) for k in used_ig if k},'pc':{k:PC.get(k,'Category '+k) for k in used_pc if k},
   'st':{k:ST[k] for k in set(stype.values())},'prod':prod,'pt':{k:sorted(v) for k,v in pt.items()},'sup':sup}
json.dump(D,open(f'{S}/v28/dims.json','w'),ensure_ascii=False,separators=(',',':'))
print('codes',len(codes),'with dims',len(prod),'missing',missing,'ig',len(D['ig']),'pc',len(D['pc']),'st',D['st'])
import os;print(os.path.getsize(f'{S}/v28/dims.json'))
print([c for c in codes if c not in P][:10])
print({k:v for k,v in list(sup.items())[:1]})
