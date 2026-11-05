#!/usr/bin/env python3
"""Pre-payroll payment check on the draft payroll of the next month.

A draft row (status O) is safe to pay only if the employee
  1. has no posted leave (PS_STAFF_VACATIONS POST_FLAG P) whose return was never recorded (ACTUAL_RETURN_DATE empty, screen HRVCRTRN),
  2. is not outside the Kingdom (travel report),
  3. is registered in GOSI.
(An unposted leave, POST_FLAG O, is a warning.)

  python3 scripts/prepay_check.py --draft raw/hr21_oct_draft.txt --leaves raw/hr22_open_leaves.txt --gosi data/gosi_check.json --names data/names.json \
      --extra data/prepay_extra.json --cc raw/hr23_cost_centres_0002.txt --month 2026-10 --out data/prepay.json
draft line:  staff|basic|plus|minus|social salary|social deduction      leave line: staff|flag|type|from|to|return
"""
import argparse, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--draft', required=True); ap.add_argument('--leaves', required=True); ap.add_argument('--gosi', required=True)
    ap.add_argument('--names'); ap.add_argument('--extra'); ap.add_argument('--exceptions', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'prepay_exceptions.json'))
    ap.add_argument('--cc', nargs='*', default=[], help='cost-centre files org|staff'); ap.add_argument('--month', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    g = json.load(open(a.gosi, encoding='utf8')); names = json.load(open(a.names, encoding='utf8')) if a.names else {}
    extra = json.load(open(a.extra, encoding='utf8')) if a.extra and os.path.exists(a.extra) else {}
    exc = {k: v for k, v in json.load(open(a.exceptions, encoding='utf8')).items() if not k.startswith('_')} if os.path.exists(a.exceptions) else {}
    rows = {r['code']: r for r in g['rows']}
    ccof = {}
    for f in a.cc:
        for l in open(f, encoding='utf8'):
            if '|' in l: o, c = l.strip().split('|')[:2]; ccof[c] = o
    ccx = json.load(open(a.exceptions, encoding='utf8')).get('_cost_centre_exempt', {}) if os.path.exists(a.exceptions) else {}
    out = {t['code']: t for t in g['travel'] if t['out'] and t['code']}
    draft = {}
    for l in open(a.draft, encoding='utf8'):
        p = l.strip().split('|')
        if len(p) >= 6:
            draft[p[0]] = dict(b=float(p[1]), p=float(p[2]), m=float(p[3]), soc=float(p[4]), si=float(p[5]))
    leaves = {}
    for l in open(a.leaves, encoding='utf8'):
        p = l.strip().split('|')
        if len(p) >= 6:
            leaves.setdefault(p[0], []).append(dict(flag=p[1], typ=p[2], f=p[3], t=p[4], r=p[5]))
    ym = a.month
    res, held, ok = [], [], 0
    for c in sorted(draft):
        d = draft[c]; gross = d['b'] + d['p']; lv = leaves.get(c, [])
        nm = names.get(c) or (extra.get(c) or {}).get('name', '')
        pend = [x for x in lv if x['flag'] == 'P' and x['f'] <= ym + '-31']  # leaves starting after the pay month belong to a later run
        unp = [x for x in lv if x['flag'] == 'O' and x['f'] >= ym[:4] + '-01-01']
        if gross <= 0:
            if pend or unp:
                held.append(dict(c=c, n=nm, lv=[[x['flag'], x['f'], x['t'], x['r']] for x in pend + unp]))
            continue
        iss = []
        if pend:
            span = '; '.join('%s → %s' % (x['f'], x['t']) for x in pend)
            iss.append(dict(k='lv', sev='H', en='Posted leave without a recorded return (%s). Record the return from leave (HRVCRTRN) first, or hold the salary' % span,
                            ar='لديه إجازة مرحّلة بدون تسجيل عودة (%s): تُسجَّل العودة من الإجازة (HRVCRTRN) أولاً أو يُوقَف الراتب' % span))
        t = out.get(c)
        if t:
            iss.append(dict(k='out', sev='H', en='Outside the Kingdom per the travel report: hold the salary until he is back', ar='خارج المملكة حسب تقرير السفر: يُوقَف الراتب حتى عودته'))
        exempt = [k for k, v in ccx.items() if any(ccof.get(c, '').startswith(pf) for pf in v['prefixes'])]
        ing = bool((rows.get(c) or {}).get('gosi')) if c in rows else bool((extra.get(c) or {}).get('in_gosi'))
        if not ing and 'gosi' not in exempt:
            iss.append(dict(k='gosi', sev='M', en='Not registered in GOSI: register him or confirm he is not subject', ar='غير مسجل في التأمينات: يُسجَّل أو يُؤكَّد أنه غير خاضع'))
        if unp:
            span = '; '.join('%s → %s' % (x['f'], x['t']) for x in unp)
            iss.append(dict(k='lvo', sev='M', en='Leave not yet posted (%s): post it so the pay and the return follow the leave' % span, ar='إجازة غير مرحّلة بعد (%s): تُرحَّل ليتبعها الراتب والعودة' % span))
        e = exc.get(c)
        if e:
            iss = [i for i in iss if i['k'] not in e['checks']]
        if not iss:
            ok += 1; continue
        res.append(dict(c=c, n=nm, b=(rows.get(c) or {}).get('gosi', {}) and rows[c]['gosi'].get('br', ''), gross=gross, ded=d['m'], net=gross - d['m'], iss=iss,
                        h=1 if any(i['sev'] == 'H' for i in iss) else 0))
    res.sort(key=lambda r: (-r['h'], r['c']))
    S = dict(month=ym, draft=len(draft), paid=sum(1 for c in draft if draft[c]['b'] + draft[c]['p'] > 0), ok=ok, flagged=len(res), blocked=sum(r['h'] for r in res),
             amount_blocked=sum(r['gross'] for r in res if r['h']), lv=sum(1 for r in res if any(i['k'] == 'lv' for i in r['iss'])), out=sum(1 for r in res if any(i['k'] == 'out' for i in r['iss'])),
             gosi=sum(1 for r in res if any(i['k'] == 'gosi' for i in r['iss'])), lvo=sum(1 for r in res if any(i['k'] == 'lvo' for i in r['iss'])), held=len(held))
    json.dump(dict(summary=S, rows=res, held=held), open(a.out, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print(json.dumps(S, ensure_ascii=False))


if __name__ == '__main__':
    main()
