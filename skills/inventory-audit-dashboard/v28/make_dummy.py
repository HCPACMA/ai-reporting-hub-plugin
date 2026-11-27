import json,re,sys,copy
sys.path.insert(0,'.')
from dummy_rules import *
d=json.load(open('audit_v28.json'))
def sc(v):
    r=v*G
    return round(r,6) if abs(r)<100 else round(r,2)
def norm(p): return '/'.join(q for q in p if not q.isdigit())
# strings: scale "SAR 1,234.56" / "17,386.14" style money in free-text fields
NUM=re.compile(r'(?<![\w/.\-])(\d{1,3}(?:,\d{3})+(?:\.\d{1,4})?|\d+\.\d{2,4})(?![\w%])')
SARN=re.compile(r'(SAR\s?)(\d[\d,]*(?:\.\d+)?)(\s?[KkMm]\b)?')
def fmt_like(orig,val):
    dec=len(orig.split('.')[1]) if '.' in orig else 0
    s=f'{val:,.{dec}f}' if ',' in orig else f'{val:.{dec}f}'
    return s
def scale_text(s,mode):
    if mode=='sar':
        def r(m):
            n=float(m.group(2).replace(',',''))
            return m.group(1)+fmt_like(m.group(2),n*G)+(m.group(3) or '')
        return SARN.sub(r,s)
    else: # ai text: decimals with >=2 digits and thousands-grouped numbers
        def r(m):
            n=float(m.group(1).replace(',','')); return fmt_like(m.group(1),n*G)
        return NUM.sub(r,s)
changed_strings=[]
def walk(x,top,path):
    if isinstance(x,dict):
        for k,v in list(x.items()):
            if isinstance(v,bool): continue
            if isinstance(v,(int,float)):
                if is_money(top,norm(path),k): x[k]=sc(v)
            elif isinstance(v,str):
                p=norm(path)
                if (top=='scan_review' and ('ai' in p.split('/'))) and k in('note','qp'):
                    nv=scale_text(v,'ai')
                elif k in('methodology','generated_note','definition','basis_note','note_basis') or (top=='meta' and k in('methodology_doc','source','generated_at','as_of','entity')):
                    nv=v
                else:
                    nv=scale_text(v,'sar')
                if nv!=v: changed_strings.append((top,p,k,v[:110],nv[:110])); x[k]=nv
            else: walk(v,top,path+[k])
    elif isinstance(x,list):
        for i,e in enumerate(x):
            if isinstance(e,(dict,list)): walk(e,top,path+['[]'])
            elif isinstance(e,str) and top=='meta':
                nv=scale_text(e,'sar')
                if nv!=e: changed_strings.append((top,'findings','[]',e[:110],nv[:110])); x[i]=nv
for t,v in d.items():
    if t=='dims': continue
    walk(v,t,[])
# meta findings list sits under meta (walk handles list of str)
# array rules
for r in d['scan_review']['top_suppliers_not_linked']: r[2]=sc(r[2])
for inv in d['scan_review']['invoices']:
    for L in inv.get('L',[]): L[3]=sc(L[3])
for s in d['dims']['sup'].values():
    for g in('ig','pc'):
        for k in s[g]: s[g][k]=sc(s[g][k])
# remove unscaled-sensitive: none
json.dump(d,open('audit_dummy.json','w'),ensure_ascii=False,separators=(',',':'))
print('strings changed',len(changed_strings))
import collections
c=collections.Counter((a,b,k) for a,b,k,_,_ in changed_strings); print(c.most_common(30))
for a,b,k,o,n in changed_strings[:12]: print(a,b,k,'\n  ',o,'\n  ',n)
