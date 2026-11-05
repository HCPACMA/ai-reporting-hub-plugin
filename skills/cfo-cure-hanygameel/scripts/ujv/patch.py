import re, os
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
p = os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html'); h = open(p, encoding='utf-8').read()
D = open(os.path.join(ROOT, 'uj2/data_uj2.json'), encoding='utf-8').read()
m = re.search(r'\nDATA\.ujv = .*;\n', h)
if m: h = h[:m.start()] + '\nDATA.ujv = ' + D + ';\n' + h[m.end():]
else:
    m = re.search(r'\nDATA\.nphi = .*;\n', h); h = h[:m.end()] + 'DATA.ujv = ' + D + ';\n' + h[m.end():]
css = open(os.path.join(ROOT, 'uj2/ujv.css'), encoding='utf-8').read()
mk = '/* ===== Unlinked JV (tax vouchers) section ===== */'
if mk in h:
    c0 = h.index(mk); c2 = h.index('/* =====', c0 + len(mk)); h = h[:c0] + css + '\n' + h[c2:]
else:
    c1 = h.index('/* ===== AR Audit section ===== */'); h = h[:c1] + css + '\n' + h[c1:]
js = open(os.path.join(ROOT, 'uj2/ujv.js'), encoding='utf-8').read()
jm = '/* ======================================================================\n   Unlinked JV · tax vouchers'
if jm in h:
    j0 = h.index(jm); j2 = h.index('/* ======================================================================', j0 + 10); h = h[:j0] + js + '\n' + h[j2:]
else:
    j1 = h.index('/* ======================================================================\n   AR Audit · insurance payments'); h = h[:j1] + js + '\n' + h[j1:]
nav = "  {id:'aud-ujv', label:'Unlinked JV · Tax Vouchers', icon:'⛓', group:'Accounting Audit'},\n"
if "{id:'aud-ujv'" not in h:
    a = "  {id:'aud-uj', label:'Unattached Entries', icon:'⎘', group:'Accounting Audit'},\n"; assert a in h; h = h.replace(a, a + nav)
open(p, 'w', encoding='utf-8').write(h); print('patched', len(h))
