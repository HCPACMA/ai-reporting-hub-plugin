import json,re
def packed2(f, keypat):
    s=json.load(open(f))['result']; L=[]
    for l in s.split('\n'):
        if re.match(r'^\|\s*'+keypat, l): L.append(l)
        elif l.startswith('| ') or l.startswith('+'): L.append(None)
        elif l.strip() and L and L[-1] and not l.strip().startswith('('): L[-1]+=' '+l.strip()
    out=[]
    for l in L:
        if not l: continue
        m=re.match(r'^\|\s*('+keypat+r')\s*\|\s*(.*)\|\s*([^|]*)\|\s*$', l)
        br=m.group(3).strip()
        for x in m.group(2).strip().split('~'): out.append((br, x.split('|')))
    return out
