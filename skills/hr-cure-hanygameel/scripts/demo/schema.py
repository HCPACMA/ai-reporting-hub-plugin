import json,sys,collections
d=json.load(open('out/data.json'))
S=collections.OrderedDict()
def add(path,v):
    t=type(v).__name__
    e=S.setdefault(path,{'t':collections.Counter(),'ex':[], 'mn':None,'mx':None,'n':0})
    e['t'][t]+=1; e['n']+=1
    if isinstance(v,(int,float)) and not isinstance(v,bool):
        e['mn']=v if e['mn'] is None else min(e['mn'],v); e['mx']=v if e['mx'] is None else max(e['mx'],v)
    if isinstance(v,str) and len(e['ex'])<2 and v not in e['ex']: e['ex'].append(v[:40])
def walk(v,p):
    if isinstance(v,dict):
        keys=list(v)
        dyn = len(keys)>25 or (keys and all(k.replace('-','').replace('.','').isalnum() and (k.isdigit() or len(k)>12) for k in keys[:5]) and len(keys)>6)
        for k,x in v.items():
            walk(x,p+'.'+('{*}' if dyn else k))
    elif isinstance(v,list):
        for x in v:
            if isinstance(x,list) and len(x)<=40:
                for i,y in enumerate(x): walk(y,p+'[]#'+str(i))
            else: walk(x,p+'[]')
    else: add(p,v)
for k,v in d.items(): walk(v,k)
for p,e in S.items():
    print(p,dict(e['t']),e['n'],e['mn'],e['mx'],e['ex'])
