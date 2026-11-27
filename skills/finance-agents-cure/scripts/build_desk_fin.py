#!/usr/bin/env python3
"""Build the Modeling Desk tab «الإدارة المالية» from the department's run folders.

Reads   <hub_root>/<runs>/<YYYY-MM>/  (handoffs, review*.md, audit.md, summary.md, run_log.md)
Writes  <hub_root>/Finance-Dept/desk/fin-dept.js      window.FIN_DATA + the tab module (templates/desk/fin-dept.src.js)
        <hub_root>/Finance-Dept/desk/fin-office.html  copy of templates/finance-office-3d.html
The two files are published BESIDE the Desk's index.html (publish_files, patch mode). The Desk loads fin-dept.js
from one include between <!--FIN-DEPT:start --> and <!--FIN-DEPT:end -->, so a new run never touches index.html.
Usage: python build_desk_fin.py --site alfaihaa [--hub <path>] [--periods 2026-10,2026-11]"""
import argparse, glob, html, json, os, re, shutil, datetime

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--site', required=True); ap.add_argument('--hub'); ap.add_argument('--periods')
a = ap.parse_args()
site = json.load(open(os.path.join(KIT, 'config', f'site.{a.site}.json'), encoding='utf-8'))
roles = json.load(open(os.path.join(KIT, 'config', 'roles.json'), encoding='utf-8'))['roles']
policy = json.load(open(os.path.join(KIT, 'config', 'model_policy.json'), encoding='utf-8'))['roles']
hub = a.hub or site['folders']['hub_root']
runs = os.path.join(hub, site['folders']['runs'])
out = os.path.join(hub, 'Finance-Dept', 'desk'); os.makedirs(out, exist_ok=True)

def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
    return t

def md(src):
    """Small Markdown → HTML: headings, tables, lists, quotes, paragraphs, bold, code."""
    lines, o, i = src.splitlines(), [], 0
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        m = re.match(r'^(#{1,4})\s+(.*)', l)
        if m: o.append(f'<h{len(m.group(1))+1}>{inline(m.group(2))}</h{len(m.group(1))+1}>'); i += 1; continue
        if l.lstrip().startswith('|'):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c or '--') for c in r)]
            if rows:
                h = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
                b = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
                o.append(f'<div class="fd-tw"><table class="fd-t"><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table></div>')
            continue
        if re.match(r'^\s*([-*]|\d+[.)])\s+', l):
            tag = 'ol' if re.match(r'^\s*\d', l) else 'ul'; items = []
            while i < len(lines) and re.match(r'^\s*([-*]|\d+[.)])\s+', lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+[.)])\s+', '', lines[i])); i += 1
            o.append(f'<{tag}>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + f'</{tag}>'); continue
        if l.startswith('>'):
            q = []
            while i < len(lines) and lines[i].startswith('>'): q.append(lines[i].lstrip('> ')); i += 1
            o.append(f'<blockquote>{inline(" ".join(q))}</blockquote>'); continue
        p = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||\s*([-*]|\d+[.)])\s|>)', lines[i]):
            p.append(lines[i]); i += 1
        o.append(f'<p>{inline(" ".join(p))}</p>')
    return '\n'.join(o)

def section_table(src, key):
    """Rows of the first table under a heading that contains `key`."""
    parts = re.split(r'\n(?=#{1,4} )', src)
    for p in parts:
        if key in p.split('\n', 1)[0]:
            rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in p.splitlines() if l.lstrip().startswith('|')]
            rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c or '--') for c in r)]
            return rows
    return []

def read(p):
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''

periods = sorted(d for d in os.listdir(runs) if re.fullmatch(r'\d{4}-\d{2}', d)) if os.path.isdir(runs) else []
if a.periods: periods = [p for p in periods if p in a.periods.split(',')]
DATA = {'site': site.get('company_name_ar', a.site), 'built': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'roles_def': [{k: r[k] for k in ('id', 'name_ar', 'reports_to', 'kind', 'color')} | {'model': policy.get(r['id'], {}).get('default')} for r in roles],
        'periods': []}
for per in periods:
    base = os.path.join(runs, per)
    summary = read(os.path.join(base, 'finance-manager', 'summary.md'))
    audit = read(os.path.join(base, 'internal-auditor', 'audit.md'))
    rating = next((w for w in ['استثناءات جوهرية', 'استثناءات طفيفة', 'نظيف'] if w in audit), '')
    P = {'period': per, 'summary_html': md(summary), 'audit_html': md(audit), 'audit_rating': rating,
         'log_html': md(read(os.path.join(base, 'run_log.md'))),
         'blockers': section_table(summary, 'موانع الإقفال'), 'role_table': section_table(summary, 'حالة الأدوار'),
         'headline': '', 'roles': []}
    m = re.search(r'#{1,4}[^\n]*العنوان[^\n]*\n+(.+?)(?:\n\n|\n#)', summary, re.S)
    if m: P['headline'] = inline(m.group(1).strip())
    reviews = {os.path.basename(f): read(f) for f in glob.glob(os.path.join(base, 'chief-accountant', 'review*.md'))}
    for r in roles:
        f = os.path.join(base, r['id'], 'handoff.json')
        if not os.path.exists(f): continue
        h = json.load(open(f, encoding='utf-8'))
        rv, r1 = h.get('review') or {}, h.get('review_round1') or {}
        P['roles'].append({'id': r['id'], 'name_ar': r['name_ar'], 'color': r['color'],
            'decision': rv.get('decision'), 'returned_before': r1.get('decision') == 'returned',
            'model_used': h.get('model_used'), 'summary_ar': h.get('summary_ar', ''), 'totals': h.get('totals', {}),
            'scope_notes_ar': h.get('scope_notes_ar', []), 'branches_missing': h.get('branches_missing', []),
            'referrals': h.get('referrals', []), 'review_notes': rv.get('notes_ar', []),
            'findings': [{k: x.get(k) for k in ('id', 'severity', 'title_ar', 'detail_ar', 'amount', 'status', 'rule', 'blocks_close', 'evidence')}
                         for x in h.get('findings', [])]})
    DATA['periods'].append(P)

src = read(os.path.join(KIT, 'templates', 'desk', 'fin-dept.src.js'))
open(os.path.join(out, 'fin-dept.js'), 'w', encoding='utf-8').write(
    '/* «الإدارة المالية» tab — data built by Finance-Agents-Kit/scripts/build_desk_fin.py */\nwindow.FIN_DATA=' +
    json.dumps(DATA, ensure_ascii=False, separators=(',', ':')) + ';\n' + src)
shutil.copy(os.path.join(KIT, 'templates', 'finance-office-3d.html'), os.path.join(out, 'fin-office.html'))
n = sum(len(r['findings']) for p in DATA['periods'] for r in p['roles'])
print(f"periods {[p['period'] for p in DATA['periods']]} · roles {sum(len(p['roles']) for p in DATA['periods'])} · findings {n} → {out}")
