# Idempotent patch of the AR Audit (insurance payments) module into the Modeling Desk page.
import re, os
ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
p = os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html'); h = open(p, encoding='utf-8').read()
D = open(os.path.join(ROOT, 'arx/data_arx.json'), encoding='utf-8').read()
m = re.search(r'\nDATA\.arx = .*;\n', h)
if m: h = h[:m.start()] + '\nDATA.arx = ' + D + ';\n' + h[m.end():]
else:
    m = re.search(r'\nDATA\.zak = .*;\n', h); h = h[:m.end()] + 'DATA.arx = ' + D + ';\n' + h[m.end():]
css = open(os.path.join(ROOT, 'arx/arx.css'), encoding='utf-8').read()
z = '/* ===== Zakat section ===== */'; c1 = h.index(z)
if '/* ===== AR Audit section ===== */' in h:
    c0 = h.index('/* ===== AR Audit section ===== */'); h = h[:c0] + css + '\n' + h[c1:]
else: h = h[:c1] + css + '\n' + h[c1:]
js = open(os.path.join(ROOT, 'arx/arx.js'), encoding='utf-8').read()
zj = '/* ======================================================================\n   Zakat · الزكاة'; j1 = h.index(zj)
mk = '/* ======================================================================\n   AR Audit · insurance payments'
if mk in h:
    j0 = h.index(mk); h = h[:j0] + js + '\n' + h[j1:]
else: h = h[:j1] + js + '\n' + h[j1:]
if "{id:'aud-arx'" not in h:
    a = "  {id:'aud-vat', label:'VAT Audit', icon:'٪', group:'Accounting Audit'},\n"
    assert a in h
    h = h.replace(a, a + "  {id:'aud-arx', label:'AR Audit · Insurance Payments', icon:'⇄', group:'AR · Accounts Receivable'},\n")
open(p, 'w', encoding='utf-8').write(h); print('patched', len(h))
# the AR workbook is rebuilt every time either AR payload is patched
import subprocess
subprocess.run(['python3', os.path.join(ROOT, 'arx/build_ar_xlsx.py')], check=True)
