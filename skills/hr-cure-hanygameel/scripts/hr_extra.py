#!/usr/bin/env python3
"""Nursing-per-doctor and leave-days aggregation.
Inputs: raw/hr24_doc_nurse.txt (org|job|staff|name|salary), raw/hr25_org_names.txt (org|name), raw/hr26_leave_days_2026.txt (staff|name|job|org|sick|emerg|unpaid|open)
Outputs: data/nursing.json, data/leave_days.json
"""
import json, os, sys, argparse
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(p):
    return [l.rstrip('\n').split('|') for l in open(p, encoding='utf8') if l.strip()]

def branch_of(org, cfg):
    if len(org) >= 6 and org[:2] in cfg['branches']: return org[:2]
    return cfg['admin_org_branch'].get(org[:3], '00')

def dept_of(org, cfg):
    """returns (key, en, ar)"""
    if len(org) >= 7 and org[:2] in cfg['branches']:
        suf = org[2:7]; nm = cfg['depts'].get(suf)
        return org[:7], (nm[0] if nm else org[:7]), (nm[1] if nm else org[:7])
    if len(org) == 6 and org[:2] in cfg['branches']:
        nm = cfg['special_depts'].get(org[2:6], cfg['special_depts']['admin']); return org, nm[0], nm[1]
    if org in ('000', '001', '002', '003', '004'):
        nm = cfg['special_depts']['admin']; return org, nm[0], nm[1]
    nm = cfg['special_depts']['hq']; return org, nm[0], nm[1]

def jobname(j, cfg):
    x = cfg['jobs'].get(j); return {'en': x[0], 'ar': x[1]} if x else {'en': 'Job ' + j, 'ar': 'وظيفة ' + j}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staff', default=os.path.join(KIT, 'raw/hr24_doc_nurse.txt'))
    ap.add_argument('--orgs', default=os.path.join(KIT, 'raw/hr25_org_names.txt'))
    ap.add_argument('--leaves', default=os.path.join(KIT, 'raw/hr26_leave_days_2026.txt'))
    ap.add_argument('--cfg', default=os.path.join(KIT, 'config/jobs_depts.json'))
    ap.add_argument('--year', default='2026')
    a = ap.parse_args()
    cfg = json.load(open(a.cfg, encoding='utf8'))
    orgn = {r[0]: r[1] for r in load(a.orgs)}
    DJ, NJ = set(cfg['doctor_jobs']), set(cfg['nurse_jobs'])
    staff = [dict(org=r[0], job=r[1], c=r[2], n=' '.join(r[3].split()), sal=float(r[4])) for r in load(a.staff)]
    docs = [s for s in staff if s['job'] in DJ]; nurses = [s for s in staff if s['job'] in NJ]
    other = [s for s in staff if s['job'] not in DJ and s['job'] not in NJ]
    if other: sys.exit('unexpected jobs in staff file: %s' % other[:3])
    # clinic = organization with at least one doctor
    byorg = {}
    for s in docs: byorg.setdefault(s['org'], []).append(s)
    nurse_by = {}
    for n in nurses: nurse_by.setdefault(n['org'], []).append(n)
    maxn = cfg['max_nurses_per_doctor']
    out_docs = []
    for d in docs:
        sharing = len(byorg[d['org']])
        ns = nurse_by.get(d['org'], [])
        okj = cfg['no_nurse_ok_jobs'].get(d['job'])
        dept_unit = len(d['org']) <= 7           # department (radiology, lab) rather than a doctor's own clinic
        if not ns:
            st = 'none_ok' if (okj or dept_unit) else 'none'
        elif len(ns) > maxn * sharing: st = 'extra'
        else: st = 'ok'
        info = None
        if st == 'none_ok': info = {'en': okj[0] if okj else 'Department level cost centre, nursing is not charged per doctor', 'ar': okj[1] if okj else 'مركز تكلفة على مستوى القسم، لا يُحمَّل التمريض على الطبيب'}
        out_docs.append(dict(c=d['c'], n=d['n'], job=d['job'], jn=jobname(d['job'], cfg), org=d['org'], on=orgn.get(d['org'], d['org']),
                             br=branch_of(d['org'], cfg), sh=sharing, st=st, info=info, k=len(ns), cost=sum(x['sal'] for x in ns), sal=d['sal'],
                             nurses=[dict(c=x['c'], n=x['n'], job=x['job'], sal=x['sal']) for x in sorted(ns, key=lambda z: z['c'])]))
    out_docs.sort(key=lambda r: (r['br'], r['org'], r['c']))
    # nurses not in a doctor's clinic
    orphans = []
    for n in nurses:
        if n['org'] in byorg: continue
        dn = dept_of(n['org'], cfg)
        if n['org'] in ('0102501', '0202501', '0302501', '0402501'): why = {'en': 'Works in the emergency department, not in a specific doctor clinic. Cost sits on the department.', 'ar': 'تعمل في قسم الطوارئ وليس في عيادة طبيب محدد. تكلفتها على القسم.'}; kind = 'dept'
        elif n['job'] == '223' or n['org'][-6:] == '211000': why = {'en': 'Home care nurse, charged to the home care department.', 'ar': 'ممرضة رعاية منزلية، تُحمَّل على قسم الرعاية المنزلية.'}; kind = 'dept'
        elif 3 < len(n['org']) <= 7: why = {'en': 'Works at department level (' + dn[1] + '), not in a specific doctor clinic. Cost sits on the department.', 'ar': 'تعمل على مستوى القسم (' + dn[2] + ') وليس في عيادة طبيب محدد. تكلفتها على القسم.'}; kind = 'dept'
        elif len(n['org']) <= 3: why = {'en': 'Charged to administration expenses, not to any clinic. Move her to a clinic or confirm the charge.', 'ar': 'تُحمَّل على المصاريف الإدارية وليس على عيادة. انقلها إلى عيادة أو أكّد التحميل.'}; kind = 'admin'
        else: why = {'en': 'No doctor of this clinic is on the active list. Cost has no doctor to carry it.', 'ar': 'لا يوجد طبيب نشط في هذه العيادة. التكلفة بلا طبيب يتحمّلها.'}; kind = 'nodoc'
        orphans.append(dict(c=n['c'], n=n['n'], job=n['job'], jn=jobname(n['job'], cfg), org=n['org'], on=orgn.get(n['org'], n['org']), br=branch_of(n['org'], cfg), sal=n['sal'], kind=kind, why=why))
    orphans.sort(key=lambda r: (r['kind'], r['br'], r['org'], r['c']))
    cnt = lambda s: sum(1 for r in out_docs if r['st'] == s)
    nursing = dict(doctors=out_docs, orphans=orphans, maxn=maxn,
        summary=dict(doctors=len(docs), nurses=len(nurses), none=cnt('none'), none_ok=cnt('none_ok'), extra=cnt('extra'), ok=cnt('ok'), orphan=len(orphans),
                     orphan_actionable=sum(1 for o in orphans if o['kind'] in ('admin', 'nodoc')), nurse_cost=sum(n['sal'] for n in nurses),
                     nurse_cost_orphan=sum(o['sal'] for o in orphans), branches={b: v[0] for b, v in cfg['branches'].items()}))
    json.dump(nursing, open(os.path.join(KIT, 'data/nursing.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    # leave days
    lv = {r[0]: r for r in load(a.leaves)}
    rows = {}
    for r in load(a.leaves):
        c, n, job, org, sk, em, un, op = r[0], ' '.join(r[1].split()), r[2], r[3], *map(int, r[4:8])
        dk = dept_of(org, cfg)
        rows[c] = dict(c=c, n=n, job=job, org=org, sick=sk, emg=em, unp=un, tot=sk + em + un, op=op)
    for s in staff:   # doctors and nurses without leave still appear with zero
        if s['c'] not in rows: rows[s['c']] = dict(c=s['c'], n=s['n'], job=s['job'], org=s['org'], sick=0, emg=0, unp=0, tot=0, op=0)
    out = []
    for c, r in rows.items():
        dk = dept_of(r['org'], cfg); r['br'] = branch_of(r['org'], cfg); r['dk'] = dk[0]; r['dn'] = {'en': dk[1], 'ar': dk[2]}
        r['jn'] = jobname(r['job'], cfg); r['grp'] = 'doc' if r['job'] in DJ else ('nurse' if r['job'] in NJ else 'other')
        out.append(r)
    out.sort(key=lambda r: (r['grp'] != 'doc', -r['tot'], r['c']))
    docs_l = [r for r in out if r['grp'] == 'doc']
    tt = lambda L, k: sum(r[k] for r in L)
    summ = dict(year=a.year, staff_with_leave=sum(1 for r in out if r['tot'] or r['op']), docs=len(docs_l), docs_with=sum(1 for r in docs_l if r['tot']),
                total=tt(out, 'tot'), sick=tt(out, 'sick'), emg=tt(out, 'emg'), unp=tt(out, 'unp'), open=tt(out, 'op'),
                doc_total=tt(docs_l, 'tot'), doc_sick=tt(docs_l, 'sick'), doc_emg=tt(docs_l, 'emg'), doc_unp=tt(docs_l, 'unp'),
                nurses=sum(1 for r in out if r['grp'] == 'nurse'), nurse_total=tt([r for r in out if r['grp'] == 'nurse'], 'tot'),
                branches={b: v[0] for b, v in cfg['branches'].items()})
    json.dump(dict(rows=out, summary=summ), open(os.path.join(KIT, 'data/leave_days.json'), 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps(nursing['summary'], ensure_ascii=False)); print(json.dumps(summ, ensure_ascii=False))
    for d in out_docs:
        if d['st'] in ('none', 'extra'): print(d['st'], d['c'], d['n'], d['org'], d['k'])
    for o in orphans: print('orph', o['kind'], o['c'], o['org'])
main()
