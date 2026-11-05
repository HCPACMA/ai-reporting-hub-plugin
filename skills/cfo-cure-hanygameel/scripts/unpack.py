import json,sys,re
def unpack(path, sep='~'):
    s=json.load(open(path))['result']
    out=[]
    for l in s.split('\n'):
        if not l.startswith('| '): continue
        body=l[2:]
        body=re.sub(r'\|\s*[^|]*\|\s*$','',body).rstrip()   # drop trailing _branch cell
        if '|' not in body: continue
        head,rest=body.split('|',1)
        if head.strip() in ('bkt',): continue
        out.extend(x for x in rest.strip().split(sep) if x)
    return out
if __name__=='__main__':
    r=unpack(sys.argv[1]); open(sys.argv[2],'w').write('\n'.join(r)); print(len(r), r[0], r[-1])
