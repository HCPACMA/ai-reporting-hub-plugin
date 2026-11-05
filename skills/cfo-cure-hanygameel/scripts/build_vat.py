import json,collections
BR=[('R','01'),('B1','02'),('B2','03'),('B4','04')]
def ret_lines(code):
    out={}  # ym -> line -> [net,vat]
    for yr in ('2025','2026'):
        for l in open(f'raw/{code}_{yr}.txt'):
            l=l.strip()
            if not l: continue
            ym,ln,tt,amt,vat,v15,cnt=l.split(';')
            if not ln: continue
            ln=int(ln); amt=float(amt); vat=float(vat); v15=float(v15)
            d=out.setdefault(ym,{}).setdefault(ln,[0.0,0.0,0.0])  # net, vat, cn(net incl vat) for sales
            if ln<=5:
                if tt=='SI': d[0]+=amt-vat
                else:
                    d[0]-=amt+vat
                    if tt=='CN': d[2]+=amt+vat
                d[1]+=vat
            elif ln==6:
                if tt=='PI': d[0]+=amt-vat
                else: d[0]+=v15
                d[1]+=vat
            else:
                d[0]+= amt if tt=='PI' else -amt
                d[1]+=vat
    return out
def tb(code):
    d={}
    for l in open(f'tb/{code}_tb_raw.txt'):
        l=l.strip()
        if not l: continue
        a,rest=l.split('|')
        for it in rest.split(','):
            ym,dr,cr=it.split(':'); d.setdefault(a,{})['20'+ym]=[float(dr),float(cr)]
    if code=='R':
        for l in open('tb/R_tb_2512.txt'):
            a,rest=l.strip().split('|'); ym,dr,cr=rest.split(':')
        # replace 2512 with YE-excluded values
        for a in d: d[a].pop('202512',None)
        for l in open('tb/R_tb_2512.txt'):
            a,rest=l.strip().split('|'); ym,dr,cr=rest.split(':')
            d.setdefault(a,{})['202512']=[float(dr),float(cr)]
    return d
def adj(code):
    d={}
    for l in open(f'tb/{code}_adj.txt'):
        ym,k,v=l.strip().split(';'); d.setdefault('20'+ym,{})[k]=float(v)
    return d
res={}
for code,cc in BR:
    res[cc]={'ret':ret_lines(code),'tb':tb(code),'adj':adj(code)}
json.dump(res,open('vat_all.json','w'))
# July 2026 check
ym='202607'
def r2(x): return round(x,2)
tot_rev=0; tot_43=collections.Counter(); ov=0; iv=0; pay=0; rs=0;rv=0;riv=0; cnr=0; med=0; inv=0
for cc,v in res.items():
    t=v['tb']
    for a,m in t.items():
        if ym not in m: continue
        dr,cr=m[ym]
        if a[0]=='4':
            tot_rev+=cr-dr
            if a.startswith('43'): tot_43[a]+=cr-dr
        if a=='21230071': ov+=cr-dr
        if a=='1263000': iv+=dr-cr
        if a=='21230072': pay+=dr-cr
    R=v['ret'].get(ym,{})
    rs+=sum(R[l][0] for l in R if l<=5); rv+=sum(R[l][1] for l in R if l<=5); riv+=R.get(6,[0,0])[1]
    cn_ret=sum(R[l][2] for l in R if l<=5)
    A=v['adj'].get(ym,{})
    cnr+=A.get('CN',0)+A.get('VCN',0)-cn_ret; med+=A.get('MED',0); inv+=A.get('INV',0)
print('TB rev',r2(tot_rev),'43x',{k:r2(x) for k,x in tot_43.items()})
print('ret sales',r2(rs),'ret vat',r2(rv),'ret input',r2(riv))
print('TB outVAT',r2(ov),'diff',r2(ov-rv))
print('TB inVAT',r2(iv),'pay',r2(pay),'in+pay-riv',r2(iv+pay-riv-pay))
print('MED',med,'INV',inv,'CNR',r2(cnr))
recon=tot_rev-sum(tot_43.values())+med+inv+cnr
print('recon',r2(recon),'vs ret',r2(rs),'resid',r2(recon-rs))
