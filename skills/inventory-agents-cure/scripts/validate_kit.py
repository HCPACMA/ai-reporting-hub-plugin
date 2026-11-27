#!/usr/bin/env python3
"""Consistency + portability checks for the Inventory-Agents-Cure kit.
Usage: python validate_kit.py [--site <site>]   (exit code 1 on any error)"""
import argparse, json, os, re, sys
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--site'); a = ap.parse_args()
err, warn = [], []
roles = json.load(open(os.path.join(KIT, 'config', 'roles.json'), encoding='utf-8'))['roles']
ids = [r['id'] for r in roles]
if len(set(ids)) != len(ids): err.append('duplicate role ids')
for r in roles:
    if r['reports_to'] not in ids + ['board', 'finance-manager']: err.append(f"{r['id']}: reports_to {r['reports_to']} unknown")
agents_dir = os.path.join(KIT, 'agents')
files = {f[:-3] for f in os.listdir(agents_dir) if f.endswith('.md')}
for i in ids:
    if i not in files: err.append(f'agents/{i}.md missing')
for f in files - set(ids): err.append(f'agents/{f}.md has no role in roles.json')
# frontmatter + portability: agents must not hard-code site specifics
SITE_LITERALS = re.compile(r'الفيحاء|Al ?Faihaa|\bRiyadh\b|BUR1|BUR2|Rafha', re.I)
for i in [x for x in ids if x in files]:
    t = open(os.path.join(agents_dir, i + '.md'), encoding='utf-8').read()
    m = re.match(r'^---\nname: (.+)\ndescription: (.+)\n(?:model: (haiku|sonnet|opus|inherit)\n)?---\n', t)
    if not m: err.append(f'{i}: bad frontmatter'); continue
    if m.group(1).strip() != i: err.append(f'{i}: name field is {m.group(1)}')
    if len(m.group(2)) > 1024: err.append(f'{i}: description too long')
    hits = SITE_LITERALS.findall(t)
    if hits: err.append(f'{i}: site-specific literal(s) in agent file — move to site config: {hits[:3]}')
    pol = json.load(open(os.path.join(KIT, 'config', 'model_policy.json'), encoding='utf-8'))['roles']
    if m.group(3) and i in pol and m.group(3) != pol[i]['default']: err.append(f'{i}: model {m.group(3)} differs from model_policy default {pol[i]["default"]}')
    if 'Read-only' not in t: err.append(f'{i}: missing read-only hard limit')
# schema parses
json.load(open(os.path.join(KIT, 'specs', '001-ai-inventory-department', 'contracts', 'handoff.schema.json'), encoding='utf-8'))
# site checks
if a.site:
    p = os.path.join(KIT, 'config', f'site.{a.site}.json')
    s = json.load(open(p, encoding='utf-8'))
    if s.get('read_only_db_user_confirmed') is not True: err.append('site: read_only_db_user_confirmed is not true')
    if not s.get('inventory_database_branch'): err.append('site: inventory_database_branch missing')
    rd = os.path.join(KIT, s['rules_dir'])
    for need in ['inventory.md']:
        if not os.path.exists(os.path.join(rd, need)): err.append(f'site: {s["rules_dir"]}/{need} missing')

for w in warn: print('WARN ', w)
for e in err: print('ERROR', e)
print('OK' if not err else f'{len(err)} error(s)')
sys.exit(1 if err else 0)
