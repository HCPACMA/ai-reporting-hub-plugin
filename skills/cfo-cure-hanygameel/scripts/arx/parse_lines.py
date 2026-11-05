import json,sys,collections
def parse(path, n):
    s=json.load(open(path))['result']
    buf=''; recs=[]
    for l in s.split('\n'):
        if l.startswith('| ARX~') or l.startswith('| ATT~'): buf=l
        elif buf: buf+=' '+l
        else: continue
        if buf.rstrip().endswith('|'):
            x=buf.strip().strip('|'); x,br=x.rsplit('|',1)
            f=[t.strip() for t in x.strip().split('~')[1:]]
            assert len(f)==n,(len(f),buf[:200])
            recs.append(f+[br.strip()]); buf=''
    return recs
if __name__=='__main__':
    r=parse(sys.argv[1],int(sys.argv[2])); json.dump(r,open(sys.argv[3],'w'),ensure_ascii=False); print(len(r))
