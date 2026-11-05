# Idempotent patch of the Zakat module into the Modeling Desk page.
import re, os
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
p = os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html'); h = open(p, encoding='utf-8').read()
D = open(os.path.join(ROOT, 'zak/data_zak.json'), encoding='utf-8').read()
m = re.search(r'\nDATA\.zak = .*;\n', h)
if m: h = h[:m.start()] + '\nDATA.zak = ' + D + ';\n' + h[m.end():]
else:
    m = re.search(r'\nDATA\.drv = .*;\n', h); h = h[:m.end()] + 'DATA.zak = ' + D + ';\n' + h[m.end():]
css = open(os.path.join(ROOT, 'zak/zak.css'), encoding='utf-8').read()
c1 = h.index('/* ===== Accounting Audit section ===== */')
if '/* ===== Zakat section ===== */' in h:
    c0 = h.index('/* ===== Zakat section ===== */'); h = h[:c0] + css + '\n' + h[c1:]
else:
    h = h[:c1] + css + '\n' + h[c1:]
js = open(os.path.join(ROOT, 'zak/zak.js'), encoding='utf-8').read()
t = "renderStrips();\nactivate('cfo-exec');"; j1 = h.index(t)
mk = '/* ======================================================================\n   Zakat · الزكاة'
if mk in h:
    j0 = h.index(mk); h = h[:j0] + js + '\n' + h[j1:]
else:
    h = h[:j1] + js + '\n' + h[j1:]
if "{id:'zakat'" not in h:
    a = "  {id:'cst-loss', label:'Loss Makers & Discount Ceiling', icon:'⊗', group:'Costing'},\n"
    assert a in h
    h = h.replace(a, a + "  {id:'zakat', label:'الزكاة · Zakat', icon:'ز', group:'Zakat'},\n")
open(p, 'w', encoding='utf-8').write(h); print('patched')
