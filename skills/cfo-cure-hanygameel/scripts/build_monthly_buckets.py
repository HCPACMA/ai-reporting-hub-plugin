# -*- coding: utf-8 -*-
"""Rebuild DATA.m (the desk's monthly GL bucket series) from a fresh account-level
pull, using a classifier reverse-engineered from the published series and verified
against it month by month."""
import json, collections, numpy as np, sys
S=open('/home/claude/work/AlFaihaa_Modeling_Desk.html',encoding='utf-8').read()
def grab(n):
    i=S.index(n+' ='); j=S.index('\n',i)
    return json.loads(S[i+len(n)+2:j].rstrip().rstrip(';'))
M=grab('DATA.m')
# --closed=YYYY-MM : first month of the re-read window; every month before it must reproduce exactly
import datetime
CL=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--closed=')), '2026-05')
_t=datetime.date.today(); _last='%d-%02d'%(_t.year,_t.month); MO=list(M['months'])
while MO[-1]<_last:   # a new month has opened since the last build: extend every series
    y,mm=map(int,MO[-1].split('-')); y,mm=(y+1,1) if mm==12 else (y,mm+1); MO.append('%d-%02d'%(y,mm))
_pad=len(MO)-len(M['months']); M['series']={k:v+[0]*_pad for k,v in M['series'].items()}; M['months']=MO
MI={m:i for i,m in enumerate(MO)}; CCS=M['ccs']; NM=len(MO)
CCI={c:i for i,c in enumerate(CCS)}

EXACT={'1262000':'B12','2124000':'B36','2220001':'B32','2231000':'B35','2240001':'B01',
       '3200000':'B05','3280001':'B13','3370000':'B09','4200027':'B11',
       '3280003':'B30','3280004':'B30','3280005':'B30',
       '3290001':'B04','3290002':'B04'}
PREF=[('1110','B17'),('1111','B17'),('1112','B17'),('1120','B17'),('1121','B17'),
      ('113','B29'),('121','B07'),('122','B07'),('123','B21'),
      ('12460001','B38'),('12460002','B38'),('124','B02'),
      ('125','B28'),('126','B24'),('13','B34'),('14','B34'),
      ('2111','B15'),('2112','B22'),('2113','B22'),
      ('2121','B03'),('2122','B25'),('2123','B25'),
      ('2126','B31'),('2128','B14'),('2210','B06'),
      ('312','B23'),('314','B18'),('318','B37'),('319','B33'),
      ('332','B19'),('333','B16'),
      ('41','B08'),('42','B10'),('43','B27'),
      ('3','B26')]
def cls(a):
    if a in EXACT: return EXACT[a]
    for p,b in PREF:
        if a.startswith(p): return b
    return 'B99'

acc=collections.defaultdict(lambda: np.zeros((len(CCS),NM)))
for f in [x for x in sys.argv[1:] if not x.startswith("--")] or ['m_riy_a.txt','m_riy_b.txt','m_bur1.txt','m_bur2.txt','m_rafha.txt']:
    for l in open(f):
        l=l.strip()
        if not l: continue
        a,cc,ym,amt=l.split('|'); m=ym[:4]+'-'+ym[4:]
        if m in MI and cc in CCS: acc[a][CCI[cc],MI[m]]+=round(float(amt)*100)   # whole halalas: sums are exact, so row order never moves a rounding
new=collections.defaultdict(lambda: np.zeros((len(CCS),NM)))
unmapped=[]
for a,v in acc.items():
    b=cls(a)
    if b=='B99': unmapped.append(a)
    new[b]+=v/100.0
if unmapped: print('UNMAPPED ACCOUNTS:', sorted(unmapped))

# -------- verification: closed months only, where both bases must agree ---------
VER=[i for i,m in enumerate(MO) if m<CL]
print('\nverification on %s – %s (%d months)'%(MO[VER[0]],MO[VER[-1]],len(VER)))
print('%-4s %-40s %14s %14s %9s'%('bkt','label','published','rebuilt','max cell'))
bad=[]
for b in sorted(set(M['labels']) | set(new)):
    y=np.zeros((len(CCS),NM))
    for c in CCS:
        s=M['series'].get(b+'|'+c)
        if s: y[CCI[c]]=s
    x=new.get(b, np.zeros((len(CCS),NM)))
    if np.abs(y[:,VER]).sum()<0.01 and np.abs(x[:,VER]).sum()<0.01: continue
    mx=float(np.abs(y[:,VER]-x[:,VER]).max())
    if mx>=2.0: bad.append(b)
    print('%-4s %-40s %14.0f %14.0f %9.2f%s'%(b, M['labels'].get(b,['?'])[0],
          y[:,VER].sum(), x[:,VER].sum(), mx, '   <-- CHECK' if mx>=2 else ''))
print('\n%s'%('ALL BUCKETS REPRODUCED' if not bad else 'mismatched: '+','.join(bad)))

# -------- what the refresh changed, by month ------------------------------------
print('\nwhat moved since the last build (net across cost centres):')
for i,m in enumerate(MO):
    tot=0.0
    for b in set(M['labels']) | set(new):
        y=sum(M['series'].get(b+'|'+c,[0]*NM)[i] for c in CCS)
        x=float(new.get(b, np.zeros((len(CCS),NM)))[:,i].sum())
        tot+=abs(x-y)
    if tot>50: print('  %s  total absolute change %14.0f'%(m, tot))
if '--write' in sys.argv:
    out=dict(M); ser={}
    for b in sorted(set(M['labels']) | set(new)):
        x=new.get(b)
        if x is None: continue
        for ci,c in enumerate(CCS):
            v=[round(float(z)) for z in x[ci]]
            if any(v): ser[b+'|'+c]=v
    out['series']=ser
    import datetime, subprocess
    out['asOf']=datetime.date.today().isoformat()
    out['source']=M['source']
    json.dump(out, open('data_m_new.json','w'), ensure_ascii=False, separators=(',',':'))
    print('\nwrote data_m_new.json  buckets %d  series %d'%(len(set(k.split("|")[0] for k in ser)), len(ser)))
print('VERDICT', 'ALL BUCKETS REPRODUCED' if not bad else 'mismatched: '+','.join(bad))
