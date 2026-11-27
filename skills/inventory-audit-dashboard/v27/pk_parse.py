import json,re,sys,os
# usage: pk_parse.py <tool-result-file> <name>  -> raw/<name>.json = {"g":{gnum:[rows]}}
src,name=sys.argv[1],sys.argv[2]
txt=json.load(open(src))['result']
R=re.compile(r'^\|\s*([\d.]+)\s*\|\s(.*?)\s*\|\s*[^|]+\|\s*$')
G={}
bad=0
for ln in txt.split('\n'):
    if not ln.startswith('|') or ln.startswith('| g ') or ln.startswith('| n'): continue
    m=R.match(ln)
    if not m: bad+=1; continue
    g=int(float(m.group(1)))
    G[g]=m.group(2).split('~')
json.dump({"g":G},open(f'raw/{name}.json','w'))
rows=sum(len(v) for v in G.values())
print(name,'groups',len(G),'min',min(G) if G else None,'max',max(G) if G else None,'rows',rows,'badlines',bad, 'tail:',txt[-80:].replace('\n',' '))
