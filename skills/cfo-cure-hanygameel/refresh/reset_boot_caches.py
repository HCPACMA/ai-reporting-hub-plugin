import json
W='/home/claude/work/'
for f in ('y_riy','y_bur1','y_bur2','y_rafha'):
    L=[l for l in open(W+'gl/%s.txt'%f) if l.startswith('2018|')]; open(W+'gl/%s.txt'%f,'w').write(''.join(L))
json.dump([],open(W+'gl/cc_rows.json','w')); json.dump(json.load(open(W+'kit/refresh/boot_drcr_2018.json')),open(W+'gl/drcr.json','w'))
g=json.load(open(W+'drv/gl_all.json')); json.dump([x for x in g if x[4]!='202301'],open(W+'drv/gl_all.json','w'))
c=json.load(open(W+'drv/cc_all.json')); json.dump({b:[x for x in v if x[0]!='2301'] for b,v in c.items()},open(W+'drv/cc_all.json','w'))
z=json.load(open(W+'zak/lines.json')); json.dump([x for x in z if not ('2023-01-01'<=x[1]<'2023-02-01')],open(W+'zak/lines.json','w'))
