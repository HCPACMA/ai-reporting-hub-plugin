import json,re,sys
sys.path.insert(0,'.')
from dummy_rules2 import *
d=json.load(open('audit_v28.json'))
def sc(v,f):
    r=v*f
    return round(r,6) if abs(r)<100 else round(r,2)
def qsc(v):
    r=v*Q; return int(r) if isinstance(v,int) else round(r,4)
def norm(p): return '/'.join(q for q in p if not q.isdigit())
NUM=re.compile(r'(?<![\w/.\-])(\d{1,3}(?:,\d{3})+(?:\.\d{1,4})?|\d+\.\d{2,4})(?![\w%])')
SARN=re.compile(r'(SAR\s?)(\d[\d,]*(?:\.\d+)?)(\s?[KkMm]\b)?')
PAIR=re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)(\s*(?:boxes|box|packs|carton|dozen|amps?|pcs)?\s*[x×]\s*)(\d+(?:,\d{3})*(?:\.\d+)?)(?![\w%])')
def fmt_like(orig,val):
    dec=len(orig.split('.')[1]) if '.' in orig else 0
    return f'{val:,.{dec}f}' if ',' in orig else f'{val:.{dec}f}'
def scale_ai(s):
    def pr(m):
        q=float(m.group(1)); p=m.group(3)
        qn=q*Q; qs=str(int(qn)) if qn==int(qn) else f'{qn:.2f}'
        pv=float(p.replace(',',''))*U
        return qs+m.group(2)+fmt_like(p,pv)
    s=PAIR.sub(pr,s)
    # remaining money-looking tokens are totals/amounts; skip tokens already inside converted pairs (cannot tell) -> mark by protecting
    return s
def scale_ai_full(s):
    marks=[]
    def prot(m):
        marks.append(m.group(0)); return f'\x00{len(marks)-1}\x00'
    def pr(m):
        q=float(m.group(1)); p=m.group(3)
        qn=q*Q; qs=str(int(qn)) if qn==int(qn) else f'{qn:.2f}'
        pv=float(p.replace(',',''))*U
        marks.append(qs+m.group(2)+fmt_like(p,pv)); return f'\x00{len(marks)-1}\x00'
    s=PAIR.sub(pr,s)
    def tok(m):
        raw=m.group(1); v=float(raw.replace(',',''))
        after=s_[m.end():m.end()+8]
        f=U if (after.startswith('/unit') or (',' not in raw and v<1000 and not after.startswith(' total'))) else G
        return fmt_like(raw,v*f)
    s_=s
    s=NUM.sub(tok,s)
    return re.sub(r'\x00(\d+)\x00',lambda m:marks[int(m.group(1))],s)
def scale_sar(s):
    return SARN.sub(lambda m:m.group(1)+fmt_like(m.group(2),float(m.group(2).replace(',',''))*G)+(m.group(3) or ''),s)
def walk(x,top,path):
    if isinstance(x,dict):
        for k,v in list(x.items()):
            if isinstance(v,bool): continue
            if isinstance(v,(int,float)):
                kd=kind(top,norm(path),k)
                if kd=='G': x[k]=sc(v,G)
                elif kd=='U': x[k]=sc(v,U)
                elif kd=='Q': x[k]=qsc(v)
            elif isinstance(v,str):
                p=norm(path)
                if top=='scan_review' and 'ai' in p.split('/') and k in('note','qp'): nv=scale_ai_full(v)
                elif k in('methodology','generated_note','definition','basis_note','note_basis') or (top=='meta' and k in('methodology_doc','source','generated_at','as_of','entity')): nv=v
                else: nv=scale_sar(v)
                x[k]=nv
            elif isinstance(v,list) and k=='forecast' and v and isinstance(v[0],(int,float)):
                x[k]=[qsc(a) for a in v]
            else: walk(v,top,path+[k])
    elif isinstance(x,list):
        for i,e in enumerate(x):
            if isinstance(e,(dict,list)): walk(e,top,path+['[]'])
            elif isinstance(e,str) and top=='meta': x[i]=scale_sar(e)
for t,v in d.items():
    if t=='dims': continue
    walk(v,t,[])
for r in d['scan_review']['top_suppliers_not_linked']: r[2]=sc(r[2],G)
for inv in d['scan_review']['invoices']:
    for L in inv.get('L',[]): L[2]=qsc(L[2]); L[3]=sc(L[3],U)
for s in d['dims']['sup'].values():
    for g in('ig','pc'):
        for k in s[g]: s[g][k]=sc(s[g][k],G)
json.dump(d,open('audit_dummy.json','w'),ensure_ascii=False,separators=(',',':'))
print('ok')
