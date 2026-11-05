import re
p='/home/claude/work/AlFaihaa_Modeling_Desk.html'; h=open(p).read()
D=open('data_drv.json').read()
m=re.search(r'\nDATA\.drv = .*;\n',h); h=h[:m.start()]+'\nDATA.drv = '+D+';\n'+h[m.end():]
c0=h.index('/* ===== Deep Analysis · Drivers ===== */'); c1=h.index('/* ===== Accounting Audit section ===== */')
h=h[:c0]+open('drv.css').read()+'\n'+h[c1:]
j0=h.index('/* ======================================================================\n   Deep Analysis · Drivers'); t="renderStrips();\nactivate('cfo-exec');"; j1=h.index(t)
h=h[:j0]+open('drv.js').read()+'\n'+h[j1:]
open(p,'w').write(h); print('patched')
