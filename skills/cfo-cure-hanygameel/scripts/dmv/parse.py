import json
def rows(f):
    s=json.load(open(f))['result']
    L=[]
    for l in s.split('\n'):
        if l.startswith('| ') or l.startswith('+'): L.append(l)
        elif l.strip() and L and L[-1].startswith('| ') and not l.strip().startswith('('): L[-1]=L[-1]+' '+l.strip()
    out=[]
    for l in L:
        if not l.startswith('| '): continue
        out.append([x.strip() for x in l.strip().strip('|').split('|')])
    return out[1:]
