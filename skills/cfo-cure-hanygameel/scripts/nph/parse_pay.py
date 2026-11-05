import json,sys,re
def parse(path):
    s=json.load(open(path))['result']
    out=[]; buf=None
    for l in s.split('\n'):
        if l.startswith('| NPB'): buf=l
        elif buf is not None: buf+=l
        else: continue
        if buf.rstrip().endswith('|') and buf.count('|')>=4:
            parts=buf.strip().strip('|').rsplit('|',1)[0]  # drop branch
            # first cell is bucket, then X
            b,x=parts.split('|',1)
            x=x.strip()
            # x ends with ' ' then '|'? already stripped
            out+= [p for p in x.rstrip(' |').split('~')]
            buf=None
    return out
if __name__=='__main__':
    r=parse(sys.argv[1]); print(len(r)); print(r[0]); print(r[-1])
    json.dump(r,open(sys.argv[2],'w'))
