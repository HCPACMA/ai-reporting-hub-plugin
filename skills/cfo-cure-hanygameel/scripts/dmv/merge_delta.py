import json, collections
CUT_YM='202610'; CUT_DT='2026-10-01'
def lines(txt):
    L=[]
    for l in txt.split('\n'):
        if l.startswith('| ') or l.startswith('+'): L.append(l)
        elif l.strip() and L and L[-1].startswith('| ') and not l.strip().startswith('('): L[-1]+=' '+l.strip()
    return [l for l in L if l.startswith('| ')][1:]
def packed(f,hasn):
    out=[]
    for l in lines(open('delta/'+f+'.txt').read()):
        body=l.strip().strip('|'); first,rest=body.split('|',1); mid,br=rest.rsplit('|',1)
        if hasn: _,mid=mid.split('|',1)
        out.append(mid.strip())
    return out
def cells(l): return [x.strip() for x in l.strip().strip('|').split('|')]
def newrows(f): return [cells(l) for l in lines(open('delta/'+f+'.txt').read())]
def oldrows(f):
    s=json.load(open(f))['result']; return [cells(l) for l in lines(s)]
def emit(f, header, rows):
    t=['| '+' | '.join(header)+' |']+['| '+' | '.join(str(x) for x in r)+' |' for r in rows]
    json.dump({'result':'\n'.join(t)},open(f,'w'),ensure_ascii=False)
items=lambda r:[i for i in r.split(';') if i]
srt=lambda its:sorted(set(its),key=lambda x:x[:6])
# alloc
D=collections.OrderedDict()
for a,n,r,br in oldrows('r_alloc2.pre3nov.json'): D[(a,br)]=[i for i in items(r) if i[:6]<CUT_YM]
for c in newrows('alloc'):
    a,n,r,br=c; D.setdefault((a,br),[]); D[(a,br)]+=items(r)
rows=[[a,len(set(i)),';'.join(srt(i)),br] for (a,br),i in D.items() if i]
emit('r_alloc2.json',['a','n','r','_branch'],rows); print('alloc',len(rows))
# cash
D=collections.OrderedDict()
for a,r,br in oldrows('r_cash.pre3nov.json'): D[(a,br)]=[i for i in items(r) if i[:6]<CUT_YM]
for a,r,br in newrows('cash'): D.setdefault((a,br),[]); D[(a,br)]+=items(r)
rows=[[a,';'.join(srt(i)),br] for (a,br),i in D.items() if i]
emit('r_cash.json',['a','r','_branch'],rows); print('cash',len(rows))
# ins
D=collections.OrderedDict()
for a,sub,snm,r,br in oldrows('r_ins.pre3nov.json'): D[(a,sub,br)]=[snm,[i for i in items(r) if i[:6]<CUT_YM]]
for a,sub,snm,r,br in newrows('ins'):
    D.setdefault((a,sub,br),[snm,[]]); D[(a,sub,br)][1]+=items(r)
    if snm: D[(a,sub,br)][0]=snm
rows=[[a,sub,snm,';'.join(srt(i)),br] for (a,sub,br),(snm,i) in D.items() if i]
emit('r_ins.json',['a','sub','snm','r','_branch'],rows); print('ins',len(rows))
# vch / ncv / desc
vch=[x for x in json.load(open('vch.pre3nov.json')) if x[1]<CUT_DT]
for m in packed('vch',True):
    for rec in m.split('~'):
        v,dt,a,amt=rec.split('|'); vch.append([v,dt,a,float(amt)])
json.dump(vch,open('vch.json','w'),ensure_ascii=False); print('vch',len(vch))
ncv=[x for x in json.load(open('ncv.pre3nov.json')) if x[1]<CUT_DT]   # no new non-cash vouchers since 1 Oct
json.dump(ncv,open('ncv.json','w'),ensure_ascii=False); print('ncv',len(ncv))
desc=json.load(open('desc.pre3nov.json'))
for m in packed('desc',False):
    for rec in m.split('~'):
        if '|' not in rec: continue
        v,ds=rec.split('|',1); desc[v.strip()]=ds.strip()
json.dump(desc,open('desc.json','w'),ensure_ascii=False); print('desc',len(desc))
