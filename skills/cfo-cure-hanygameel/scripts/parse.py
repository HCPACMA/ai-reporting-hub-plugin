import json,sys,re
def parse(f):
    s=json.load(open(f))['result']
    out=[]
    for l in s.split('\n'):
        if not l.startswith('| '): continue
        body=l[2:]
        body=re.sub(r'\|\s*[^|]*\|\s*$','',body).rstrip()
        if body in ('r','R') or not body: continue
        out.append(body)
    return out
if __name__=='__main__':
    rows=parse(sys.argv[1]); open(sys.argv[2],'w').write('\n'.join(rows)); print(len(rows), rows[0][:150])
