#!/usr/bin/env python3
"""Year-to-date overtime feasibility. Merges months into data/overtime_feas.ytd.json (same schema as the Oct file, entries/days tagged with m).
Doctor 3013 (dialysis) is excluded everywhere. Oct is reused from data/overtime_feas.2026-10.json."""
import json, os
EX = {'3013', '3106'}  # 3013 dialysis; 3106 administrative
MONTHS = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09']
AR = {'الرياض': 'Riyadh', 'بريدة 1': 'BUR1', 'بريدة 2': 'BUR2', 'رفحاء': 'Rafha'}
rates = json.load(open('raw/otf_rates.json'))
oct_rates = {r['st']: r.get('rate') or 0 for r in json.load(open('data/overtime.2026-10.json'))['rows']}
rates['2026-10'] = oct_rates
order = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10']
org = {}; sal = {}
for ln in open('raw/hr24_doc_nurse.txt', encoding='utf8'):
    q = ln.strip().split('|')
    if len(q) >= 5:
        org[q[2]] = q[0]
        try: sal[q[2]] = float(q[4])
        except ValueError: pass
def rate_of(st, m):
    r = rates.get(m, {}).get(st)
    if r: return r, 'month'
    for mm in sorted(order, key=lambda x: abs(order.index(x) - order.index(m))):
        r = rates.get(mm, {}).get(st)
        if r: return r, 'near ' + mm
    if st in sal: return round(sal[st] / 180.0, 4), 'salary/180'
    return 0, 'none'
def ovl(w1, w2): return sum(max(0, min(a[1], b[1]) - max(a[0], b[0])) for a in w1 for b in w2)
docs = {}; nurses = []; stats = []
def getdoc(br, st, name):
    return docs.setdefault((br, st), {'br': br, 'st': st, 'name': name, 'rate': 0, 'entries': []})
for m in MONTHS:
    ent = json.load(open('raw/otf_entries.%s.json' % m))['entries']
    groups = json.load(open('raw/otf2_groups.%s.json' % m))
    gmap = {(g['st'], g['s'], g['e']): g for g in groups}
    rev = {}   # (g, day) -> dict
    for ln in open('raw/otf2_rev_%s.txt' % m, encoding='utf8'):
        ln = ln.strip()
        if not ln: continue
        br, g, v = ln.split('|'); br = AR.get(br, br); g = int(g)
        if groups[g]['br'] != br: continue
        for part in v.split(';'):
            d, c, cn, r, rn = part.split(':')
            o = rev.setdefault((g, int(d)), {'C': 0, 'Ce': 0, 'R': 0, 'Re': 0})
            o['C'] += float(c); o['Ce'] += int(cn); o['R'] += float(r); o['Re'] += int(rn)
    nurE = []
    for i, e in enumerate(ent):
        if e['kind'] == 'nurse':
            rt = rate_of(e['st'], m)[0]
            nurE.append({'i': i, 'm': m, 'st': e['st'], 'name': e['name'], 'br': e['br'], 'rate': rt, 'hrs': e['hrs'], 'each': e['each'], 'dd': e['dd'], 'reason': e['reason'], 'win': e['win'], 'org': org.get(e['st'], ''), 'charged': 0.0})
    share = {}
    def okdoc(e): return e['kind'] == 'doctor' and e['st'] not in EX
    for i, e in enumerate(ent):
        if okdoc(e) and org.get(e['st']) and e['win']:
            for d in e['dd']:
                for n in nurE:
                    if n['org'] == org[e['st']] and d in n['dd'] and ovl(e['win'], n['win']) > 0:
                        share.setdefault((n['i'], d), set()).add(e['st'])
    nd = 0
    for i, e in enumerate(ent):
        if not okdoc(e): continue
        D = getdoc(e['br'], e['st'], e['name']); rt, src = rate_of(e['st'], m)
        if rt: D['rate'] = rt
        w = [x for x in e['win'] if x[1] - x[0] <= 16]
        cb = 'cbahi' in e['reason'].lower()
        flag = 'CBAHI' if cb else ('nowin' if not w or not e['dd'] else '')
        days = []
        if not flag:
            for d in e['dd']:
                C = R = Ce = Re = 0
                for x in w:
                    g = gmap.get((e['st'], x[0], x[1]))
                    if g is None: continue
                    o = rev.get((g['g'], d))
                    if o: C += o['C']; R += o['R']; Ce += o['Ce']; Re += o['Re']
                nc = 0.0; nn = []
                for n in nurE:
                    if n['org'] and n['org'] == org.get(e['st']) and d in n['dd']:
                        oo = ovl(w, n['win'])
                        if oo > 0:
                            hh = min(oo, n['each']) / max(1, len(share.get((n['i'], d), {e['st']})))
                            nc += hh * n['rate']; n['charged'] += hh; nn.append('%s %s %.1fh' % (n['st'], n['name'], hh))
                days.append({'m': m, 'd': d, 'hrs': e['each'], 'cash': round(C, 2), 'cashN': Ce, 'cred': round(R, 2), 'credN': Re, 'nur': round(nc, 2), 'nn': '; '.join(nn)})
        D['entries'].append({'m': m, 'i': i, 'spec': '', 'reason': e['reason'], 'win': w, 'hrs': e['hrs'], 'each': e['each'], 'flag': flag, 'rt': rt, 'rtsrc': src,
                             'wlen': round(sum(b - a for a, b in w), 2), 'days': days, 'costOnlyHrs': e['hrs'] if flag else 0, 'svc': []})
        nd += 1
    for n in nurE: n['chargedCost'] = round(n['charged'] * n['rate'], 2)
    nurses += nurE
    stats.append((m, nd))
# October (already built, link logic included)
o = json.load(open('data/overtime_feas.2026-10.json'))
for D0 in o['doctors']:
    if D0['st'] in EX: continue
    D = getdoc(D0['br'], D0['st'], D0['name']); D['rate'] = D0['rate'] or D['rate']
    for E in D0['entries']:
        E['m'] = '2026-10'; E['rt'] = D0['rate']; E['rtsrc'] = 'month'
        for x in E['days']: x['m'] = '2026-10'
        D['entries'].append(E)
for n in o['nurses']: n['m'] = '2026-10'; nurses.append(n)
for D in docs.values():
    for E in D['entries']:
        if not E['rt']: E['rt'] = D['rate']
out = {'month': 'YTD', 'months': order, 'discount': 35, 'doctors': sorted(docs.values(), key=lambda d: (d['br'], d['st'])), 'nurses': nurses,
       'missing': [],
       'note_en': 'Revenue = net of VAT, pharmacy excluded; cash = invoice types C+D, credit = R. Window = the time written in the overtime statement (overnight windows run past midnight). Doctor 3013 (dialysis: sessions run in working time and are not invoiced by the hour) and doctor 3106 (administrative role) are excluded. April to July were read from the scanned voucher attachments (doctor rows only); nurse overtime cost is not linked for those four months because the scans give no nurse windows.',
       'note_ar': 'الإيراد = الصافي بدون الضريبة وبدون الصيدلية؛ النقدي = فواتير C+D والآجل = R. النافذة = الوقت المكتوب في كشف الإضافي (النوافذ الليلية تمتد بعد منتصف الليل). تم استثناء الطبيبة 3013 (غسيل كلوي: يتم في وقت العمل ولا يُفوتَر بالساعة) والطبيب 3106 (عمل إداري). شهور أبريل إلى يوليو قُرئت من مرفقات القيود الممسوحة (صفوف الأطباء فقط)، وتكلفة تمريض الإضافي غير مربوطة فيها لأن المسح لا يحدد نوافذ التمريض.'}
json.dump(out, open('data/overtime_feas.ytd.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
print(stats, len(docs), 'doctors', sum(len(D['entries']) for D in docs.values()), 'entries')
zero = [(D['st'], E['m']) for D in docs.values() for E in D['entries'] if not E['rt']]
print('zero rate entries', len(zero), zero[:15])
for m in order:
    c = sum(x['cash'] for D in docs.values() for E in D['entries'] if E['m'] == m for x in E['days'])
    r = sum(x['cred'] for D in docs.values() for E in D['entries'] if E['m'] == m for x in E['days'])
    k = sum(E['hrs'] * E['rt'] for D in docs.values() for E in D['entries'] if E['m'] == m)
    print(m, 'cash', round(c), 'cred', round(r), 'doc cost', round(k))
