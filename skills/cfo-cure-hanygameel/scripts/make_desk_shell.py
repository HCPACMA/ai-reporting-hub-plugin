import re,json,sys
s=open('ModelingDesk_current.html',encoding='utf-8').read()
dec=json.JSONDecoder()
KEY=re.compile(r'^([A-Za-z_][A-Za-z0-9_]{0,29}|[A-Za-z]{0,3}[ _-]?(?:19|20)\d\d(?:[ _-]?(?:YTD|Q[1-4]|H[12]|\d{1,2}))*)$')
import random
_R=random.Random(7)
def fake(v):
    if isinstance(v,float) and abs(v)<=1: return round(_R.uniform(0.05,0.6),3)
    return _R.randint(1000,99000)
def pipekey(k):
    return '|' in k and all(re.fullmatch(r'[A-Za-z0-9]{1,4}|\d{1,8}|(19|20)\d\d(0[1-9]|1[0-2])|(?i:cash|credit|total|all|insurance|patient)',p) for p in k.split('|'))
def periodkey(k):
    if not re.search(r'(19|20)\d\d',k) or len(k)>40: return False
    r=re.sub(r'(19|20)\d\d(-\d\d){0,2}|\b(YTD|as|of|FY|Q[1-4]|H[12]|TTM|LTM)\b|[\s()_,:/-]','',k)
    return r==''
def sk(v,d=0):
    if isinstance(v,dict):
        return {k:sk(x,d+1) for k,x in v.items() if KEY.match(k) or periodkey(k) or pipekey(k) or re.fullmatch(r'\d{1,8}|(19|20)\d\d(0[1-9]|1[0-2])',k)}
    if isinstance(v,list):
        return [sk(x,d+1) for x in v[:60]]
    if isinstance(v,bool): return v
    if isinstance(v,(int,float)): return v if isinstance(v,int) and (-1<=v<=12 or 1990<=v<=2035 or 199001<=v<=203512) else fake(v)
    if isinstance(v,str): return v if pipekey(v) or re.fullmatch(r"[A-Za-z0-9]{1,4}|\d{1,8}|[a-z][a-z0-9_]{0,15}|(19|20)\d\d-?(0[1-9]|1[0-2])(-\d\d)?",v) or re.fullmatch(r"(19|20)\d\d(-\d\d)?( YTD)?",v) else ""
    return None
out=[];pos=0
for m in re.finditer(r'(?:const|let|var)\s+[A-Za-z_]\w*\s*=\s*|DATA(?:\.\w+|\[[\'"]\w+[\'"]\])\s*=\s*',s):
    if m.start()<pos: continue
    j=m.end()
    if j>=len(s) or s[j] not in '{["': continue
    try: v,e=dec.raw_decode(s,j)
    except Exception: continue
    if e-j<300: continue
    out.append(s[pos:j]); out.append(json.dumps(sk(v))); pos=e
out.append(s[pos:]); t=''.join(out)
t=t.replace('56000001453104','[bank-account]')
t=re.sub(r'((?:fmtSAR|pkSAR|nfmt|n2|f2|fmt)\()\d{5,}(?:\.\d+)?',r'\g<1>0',t)
hdr='<!-- CFO Modeling Desk - DATA-FREE SHELL. Every DATA.* payload is reduced to its schema (structure kept; every amount replaced by RANDOM DUMMY numbers, all names and labels blanked); bank account and hard-coded amounts masked. Layout/code reference only: fill DATA from the Cure MCP with the kit scripts. -->\n'
open('ModelingDesk_shell.html','w',encoding='utf-8').write(hdr+t)
print(len(t), 'emails',len(re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[a-z]{2,}',t)),'ids',len(re.findall(r'(?<![\d.])[12]\d{9}(?![\d.])',t)))
