#!/usr/bin/env python3
"""Build the Inventory Audit dashboard tab «إدارة المخازن · AI Agents» (+ its demo copy).
Writes <hub>/Inventory-Dept/desk/{inv-dept.js, inv-office.html} and <hub>/Inventory-Dept/desk/demo/{…}.
Publish both files BESIDE the dashboard's index.html (patch); the page loads inv-dept.js from one include
<!--INV-DEPT:start --><script src="inv-dept.js"></script><!--INV-DEPT:end -->.
Usage: python build_inv_tab.py --site alfaihaa [--hub <path>]"""
import argparse, glob, html, json, os, re, shutil, datetime
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--site', required=True); ap.add_argument('--hub'); a = ap.parse_args()
site = json.load(open(os.path.join(KIT, 'config', f'site.{a.site}.json'), encoding='utf-8'))
roles = json.load(open(os.path.join(KIT, 'config', 'roles.json'), encoding='utf-8'))['roles']
pol = json.load(open(os.path.join(KIT, 'config', 'model_policy.json'), encoding='utf-8'))['roles']
hub = a.hub or site['folders']['hub_root']; runs = os.path.join(hub, site['folders']['runs'])
out = os.path.join(hub, 'Inventory-Dept', 'desk'); os.makedirs(os.path.join(out, 'demo'), exist_ok=True)
TAB = {'overview':'Overview','overstock':'Overstock','slowmoving':'Slow-Moving','expiry':'Expiry','receiving':'Receiving Flags','aging':'Aging Bucket',
       'crossorg':'Cross-Branch Audit','dispense':'Dispense by CC','purchases':'Purchases & Pricing','abc':'ABC / Pareto','forecast':'Demand Forecast',
       'rebalance':'Rebalancing','abcxyz':'ABC × XYZ','cyclecount':'Cycle-Count Variance','vendor':'Vendor Concentration','watch':'Price & Vendor Watch',
       'valerr':'Valuation Errors','fraud':'Fraud Detection','board':'تقرير المجلس'}
names = {r['id']: r['name_ar'] for r in roles}; names['finance-manager'] = 'المدير المالي (الإدارة المالية)'
def inline(t): return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html.escape(t, quote=False))
def md(src):
    o = []
    for blk in re.split(r'\n\s*\n', src.strip()):
        l = blk.strip()
        if not l: continue
        m = re.match(r'^(#{1,4})\s+(.*)', l)
        if m: o.append(f'<h{len(m.group(1))+1}>{inline(m.group(2))}</h{len(m.group(1))+1}>'); continue
        if l.startswith('|'):
            rows = [[c.strip() for c in x.strip().strip('|').split('|')] for x in l.splitlines() if x.strip().startswith('|')]
            rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c or '--') for c in r)]
            o.append('<div class="iv-tw"><table class="iv-t"><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in rows[0]) + '</tr></thead><tbody>' +
                     ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:]) + '</tbody></table></div>'); continue
        if re.match(r'^[-*]\s', l):
            items = [inline(re.sub(r'^[-*]\s+', '', x)) for x in l.splitlines()]
            o.append('<ul>' + ''.join('<li>' + it + '</li>' for it in items) + '</ul>'); continue
        o.append(f'<p>{inline(" ".join(l.splitlines()))}</p>')
    return '\n'.join(o)
D = {'site': site.get('company_name_ar', a.site), 'built': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'tab_labels': TAB,
     'roles': [dict(r, reports_to_ar=names.get(r['reports_to'], r['reports_to']), model=pol.get(r['id'], {}).get('default', 'sonnet')) for r in roles], 'periods': []}
for per in sorted(p for p in (os.listdir(runs) if os.path.isdir(runs) else []) if re.fullmatch(r'\d{4}-\d{2}', p)):
    base = os.path.join(runs, per); P = {'period': per, 'roles': [], 'summary_html': ''}
    s = os.path.join(base, 'inv-manager', 'summary.md')
    if os.path.exists(s): P['summary_html'] = md(open(s, encoding='utf-8').read())
    for r in roles:
        f = os.path.join(base, r['id'], 'handoff.json')
        if os.path.exists(f):
            h = json.load(open(f, encoding='utf-8'))
            P['roles'].append({'id': r['id'], 'decision': (h.get('review') or {}).get('decision'),
                               'findings': [{k: x.get(k) for k in ('id', 'severity', 'title_ar', 'detail_ar', 'amount', 'status')} for x in h.get('findings', [])]})
    D['periods'].append(P)
src = open(os.path.join(KIT, 'templates', 'tab', 'inv-dept.src.js'), encoding='utf-8').read()
def write(folder, data):
    open(os.path.join(folder, 'inv-dept.js'), 'w', encoding='utf-8').write(
        '/* «إدارة المخازن · AI Agents» tab — built by Inventory-Agents-Kit/scripts/build_inv_tab.py */\nwindow.INV_DATA=' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n' + src)
    shutil.copy(os.path.join(KIT, 'templates', 'warehouse-3d.html'), os.path.join(folder, 'inv-office.html'))
write(out, D)
# demo: no company name; findings amounts ×6.25 (same factor as the dashboard demo); no run text kept beyond titles
demo = json.loads(json.dumps(D)); demo['site'] = 'Demo Care (عرض تجريبي)'
for P in demo['periods']:
    P['summary_html'] = ''
    for r in P['roles']:
        for f in r['findings']:
            if isinstance(f.get('amount'), (int, float)): f['amount'] = round(f['amount'] * 6.25, 2)
            f['detail_ar'] = ''
txt = json.dumps(demo, ensure_ascii=False)
for real, fake in [('مجموعة الفيحاء', 'ديمو كير'), ('الفيحاء', 'ديمو كير'), ('Al Faihaa', 'Demo Care'), ('الرياض', 'المركزي'), ('بريدة', 'البوابة الشرقية'), ('رفحاء', 'الحقل الشمالي')]:
    txt = txt.replace(real, fake)
write(os.path.join(out, 'demo'), json.loads(txt))
left = [w for w in ('الفيحاء', 'Faihaa') if w in txt]
print(f'roles {len(roles)} · periods {[p["period"] for p in D["periods"]]} → {out} (+demo) · demo leaks: {left or "none"}')
