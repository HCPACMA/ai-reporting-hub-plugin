import json, os
from collections import Counter

def parse_pipe(path):
    lines=[l for l in open(path,encoding='utf-8').read().splitlines() if l.strip().startswith('|')]
    if not lines: return []
    hdr=[h.strip() for h in lines[0].strip().strip('|').split('|')]
    out=[]
    for l in lines[2:]:
        c=[x.strip() for x in l.strip().strip('|').split('|')]
        if len(c)>len(hdr): c=c[:len(hdr)-1]+[' | '.join(c[len(hdr)-1:])]
        if len(c)!=len(hdr): continue
        out.append({hdr[i]:(c[i] if c[i] not in ('','-') else None) for i in range(len(hdr))})
    return out

rows=[]
if os.path.exists('raw/pbm.md'):
    for r in parse_pipe('raw/pbm.md'):
        rows.append({
          'date':r.get('PBM_DATE'),'pf':r.get('PF'),'name':r.get('PNAME'),'ep':r.get('EP'),
          'product':r.get('PRODUCT'),'qty':r.get('QTY'),'req_dur':r.get('REQ_DUR'),'appr_dur':r.get('APPR_DUR'),
          'dosage':r.get('DOSAGE'),'route':r.get('ROUTE'),'reply':r.get('REPLY'),
          'outcome':(r.get('OUTCOME') or '').strip() or None,'status':r.get('STATUS'),
          'reject':r.get('REJECT_NOTES'),
          'pt':'Credit'})  # PBM pre-authorisation is an insurance (Credit) workflow

def norm(o):
    o=(o or '').lower()
    if 'approv' in o: return 'Approved'
    if 'error' in o: return 'Error'
    if 'reject' in o or 'denied' in o: return 'Rejected'
    if 'pend' in o or o=='' : return 'Pending'
    return o.title() or 'Pending'

oc=Counter(norm(r['outcome']) for r in rows)
# distinct requests = distinct (pf, ep, date)
reqs=len({(r['pf'],r['ep'],r['date']) for r in rows})
pbm={'rows':rows,
 'kpi':{'requests':reqs,'lines':len(rows),'approved':oc.get('Approved',0),
        'errored':oc.get('Error',0),'rejected':oc.get('Rejected',0),'pending':oc.get('Pending',0),
        'outcomes':dict(oc)},
 'meta':{'source':'HS_NPHIES_PBM_REQUEST (+ _DTL) — NPHIES pharmacy benefit pre-authorisation',
         'note':'PBM (drug pre-authorisation) is barely used at this site; every recorded request currently ends in error — the pre-auth channel is not operational.'}}
json.dump(pbm,open('pbm.json','w',encoding='utf-8'),ensure_ascii=False)
print('PBM lines:',len(rows),'| requests:',reqs,'| outcomes:',dict(oc))
