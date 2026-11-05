import json, re
H='/home/claude/work/AlFaihaa_Modeling_Desk.html'
h=open(H,encoding='utf-8').read()
cfa=open('/home/claude/work/gl/data_cfa_fixed.json',encoding='utf-8').read()
cfd=open('data_cfd.json',encoding='utf-8').read()
L=h.split('\n')
for i,l in enumerate(L):
    if l.startswith('DATA.cfa = '): L[i]='DATA.cfa = '+json.dumps(json.loads(cfa),ensure_ascii=False,separators=(',',':'))+';'; ci=i
L=[l for l in L if not l.startswith('DATA.cfd = ')]
ci=[i for i,l in enumerate(L) if l.startswith('DATA.cfa = ')][0]
L.insert(ci+1,'DATA.cfd = '+cfd+';')
h='\n'.join(L)
# css
css=open('cfd.css').read()
if '/* ===== Cash flow · direct method ===== */' in h:
    i=h.index('/* ===== Cash flow · direct method ===== */'); j=h.index('/* ===== Deep Analysis · Drivers ===== */')
    h=h[:i]+css+'\n'+h[j:]
else:
    h=h.replace('/* ===== Deep Analysis · Drivers ===== */', css+'\n/* ===== Deep Analysis · Drivers ===== */',1)
# js: replace cfa block (+ any existing cfd block)
i=h.index('/* ---- Cash Flow (audited) ---- */')
if '/* ---- Cash Flow · Direct (voucher level) ---- */' in h:
    k=h.index('/* ---- Cash Flow · Direct (voucher level) ---- */'); j=h.index('})();',k)+5
else:
    j=h.index('})();', h.index('(function(){', h.index("const sec = document.getElementById('sec-cashflow');")-200))+5
h=h[:i]+open('cfa_new.js',encoding='utf-8').read()+'\n'+open('cfd.js',encoding='utf-8').read()+h[j:]
# nav
h=h.replace("{id:'cashflow', label:'Cash Flow', icon:'△', group:'Statements'},","{id:'cashflow', label:'Cash Flow · Indirect', icon:'△', group:'Statements'},\n  {id:'cashflow-direct', label:'Cash Flow · Direct', icon:'▽', group:'Statements'},")
open(H,'w',encoding='utf-8').write(h)
print('patched', len(h), h.count("id:'cashflow-direct'"), h.count('DATA.cfd = '))
