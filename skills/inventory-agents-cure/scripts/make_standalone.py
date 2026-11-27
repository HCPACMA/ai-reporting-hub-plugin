#!/usr/bin/env python3
"""Make a Desk page self-contained so it works when copied alone to another computer.
Inlines every <script src="X.js"> whose file sits beside the page (fin-dept.js, ar-*.js …) and embeds inv-office.html
for the 3D office (window.INV_OFFICE_HTML → iframe srcdoc). Scripts whose file is missing are listed and left as they are.
Usage: python make_standalone.py <page.html> [--out <file>]   (default: overwrite the page; a .bak is kept)"""
import argparse, json, os, re, shutil
ap = argparse.ArgumentParser(); ap.add_argument('page'); ap.add_argument('--out'); a = ap.parse_args()
d = os.path.dirname(os.path.abspath(a.page)); s = open(a.page, encoding='utf-8').read()
inlined, missing = [], []
def sub(m):
    name = m.group(1)
    if re.match(r'^(https?:|//|data:|blob:)', name): return m.group(0)
    f = os.path.join(d, name)
    if not os.path.exists(f): missing.append(name); return m.group(0)
    js = open(f, encoding='utf-8').read().replace('</script', '<\\/script')
    inlined.append(name); return f'<script data-inlined="{name}">\n{js}\n</script>'
s = re.sub(r'<script[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>', sub, s)
office = os.path.join(d, 'inv-office.html')
if os.path.exists(office) and 'window.INV_OFFICE_HTML=' not in s:
    blob = json.dumps(open(office, encoding='utf-8').read(), ensure_ascii=False).replace('</', '<\\/')
    tag = f'<script>window.INV_OFFICE_HTML={blob};</script>'
    i = s.find('<script data-inlined="inv-dept.js">')
    s = s[:i] + tag + '\n' + s[i:] if i >= 0 else s + '\n' + tag
    inlined.append('inv-office.html')
out = a.out or a.page
if out == a.page: shutil.copy(a.page, a.page + '.bak')
open(out, 'w', encoding='utf-8').write(s)
print('inlined:', inlined); print('missing (not beside the page):', missing or 'none')
