import json,sys
BR=['الرياض','بريدة 1','بريدة 2','رفحاء']
def rows_of(f):
    s=json.load(open(f))['result']; out=[]
    L=[]
    for l in s.split('\n'):
        if l.startswith('| '): L.append(l)
        elif l.strip() and L and not l.startswith('+') and not l.strip().startswith('('): L[-1]=L[-1].rstrip()+' '+l.strip()
    out=[[x.strip() for x in l.strip().strip('|').split('|')] for l in L]
    return out[1:]   # drop header
def build(name,header,files,keep,pk=None):
    allr=[]
    for br,f in zip(BR,files):
        for r in rows_of(f):
            if pk is not None:
                r=[c for c in r[:-1] if not (c and set(c)=={'x'})]
                r=r[:pk]+['|'.join(r[pk:])]
            allr.append([r[i] for i in keep]+[br])
    w=[max(len(str(x)) for x in col) for col in zip(header,*allr)]
    fmt=lambda r:'| '+' | '.join(str(x).ljust(w[i]) for i,x in enumerate(r))+' |'
    sep='+'+'+'.join('-'*(x+2) for x in w)+'+'
    open('delta/'+name+'.txt','w').write('\n'.join([sep,fmt(header),sep]+[fmt(r) for r in allr]+[sep])+'\n')
    print(name,len(allr))
if __name__=='__main__':
    name=sys.argv[1]; header=sys.argv[2].split(','); keep=[int(x) for x in sys.argv[3].split(',')]; files=open(sys.argv[4]).read().split()
    build(name,header+['_branch'],files,keep,int(sys.argv[5]) if len(sys.argv)>5 else None)
