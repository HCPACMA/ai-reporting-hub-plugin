#!/usr/bin/env python3
"""Create the run folders for one period: <hub_root>/<runs>/<period>/<role>/ + run_log.md.
Usage: python new_period.py --site alfaihaa --period 2026-10 [--hub <path>]"""
import argparse, json, os, datetime
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser(); ap.add_argument('--site', required=True); ap.add_argument('--period', required=True); ap.add_argument('--hub')
a = ap.parse_args()
site = json.load(open(os.path.join(KIT, 'config', f'site.{a.site}.json'), encoding='utf-8'))
roles = json.load(open(os.path.join(KIT, 'config', 'roles.json'), encoding='utf-8'))['roles']
hub = a.hub or site['folders']['hub_root']
base = os.path.join(hub, site['folders']['runs'], a.period)
for r in roles: os.makedirs(os.path.join(base, r['id']), exist_ok=True)
log = os.path.join(base, 'run_log.md')
if not os.path.exists(log):
    with open(log, 'w', encoding='utf-8') as f:
        f.write(f"# سجل تشغيل الإدارة المالية — {site['company_name_ar']} — {a.period}\n\n| الوقت | الدور | الحالة | ملاحظة |\n|---|---|---|---|\n")
with open(log, 'a', encoding='utf-8') as f:
    f.write(f"| {datetime.datetime.now():%Y-%m-%d %H:%M} | finance-manager | started | فتح الفترة |\n")
print(base)
