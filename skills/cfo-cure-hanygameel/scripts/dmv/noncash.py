import json, collections
FIN_INV_PREFIX=('1110','1120','113','1111','1121','2112','2113','2125','2128','221','222','223')
FIN_INV_EXACT={'4300008','3380000','1410000','3280001','3280002','1262000','3290001'}
def side(a):
    if a.startswith(('1110','1120','113','1111','1121')) or a in ('4300008','3380000','1410000','3280001','3280002'): return 'INV'
    if a.startswith(('2112','2113','2125','2128','221','222','223')) or a in ('1262000','3290001'): return 'FIN'
    return 'OP'
def load(cut='2026-10-10'):
    rows=[r for r in json.load(open('ncv.json')) if r[1]<cut]
    V=collections.defaultdict(list)
    for v,dt,a,n in rows: V[v].append((dt,a,n))
    out=[]
    for v,ls in V.items():
        dt=ls[0][0]
        s={'OP':0.0,'INV':0.0,'FIN':0.0}
        for _,a,n in ls: s[side(a)]+=n
        out.append({'v':v,'d':dt,'y':int(dt[:4]),'op':-s['OP'],'inv':-s['INV'],'fin':-s['FIN'],'lines':[(a,n) for _,a,n in ls]})
    return out
if __name__=='__main__':
    X=load(); c=json.load(open('/home/claude/work/gl/data_cfa_gl.json')); d=json.load(open('dm_year.json'))['yr']
    CFO=['r_pat','r_ins','r_corp','r_oth','p_staff','p_sup','p_gov','p_insfee','p_opex','p_vat','p_zak','p_owner','susp']
    for y in c['years']:
        op=sum(x['op'] for x in X if x['y']==y); inv=sum(x['inv'] for x in X if x['y']==y); fin=sum(x['fin'] for x in X if x['y']==y)
        v=c['v'][str(y)]; x=d[str(y)]
        cfo_d=sum(x.get(k,0) for k in CFO); cfi_d=x.get('capex',0); cff_d=sum(x.get(k,0) for k in ('loans','div','equity'))
        print(y,'noncash op %.0f inv %.0f fin %.0f | CFI: ind-noncash %.0f vs dir %.0f  res %.0f | CFF res %.0f | CFO res %.0f'%(op,inv,fin, v['CFI']-inv, cfi_d, v['CFI']-inv-cfi_d, v['CFF']-fin-cff_d, v['CFO']-op-cfo_d))
