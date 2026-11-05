# -*- coding: utf-8 -*-
"""Payment Via NPHIES (Rafha). Builds DATA.nph from the Cure MCP pulls:
   other.json / taw.json  packed per-payment rows (pay.sql): header, detail sum, linked claims, claimed, months, booking accounts
   disp.json              payment DISPOSITION text (period wording from the payer)
   ref.json               Rafha sub-accounts (1240007) and CUSTOMER_GROUPS (NPHIES_ID)
   glr.json               Rafha receipts credited to 1240007 (BR / JV, posted + open) since 2025-01
Only real cash payments (PAYMENT_AMOUNT > 0)."""
import json, collections, datetime as dt, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
P = json.load(open('other.json')) + json.load(open('taw.json'))
DISP = json.load(open('disp.json')); REF = json.load(open('ref.json')); GLR = json.load(open('glr.json'))
SUBS, GRPS = REF['subs'], REF['grps']
BY_NPH = {g['nph']: (k, g) for k, g in GRPS.items() if g['nph']}
# payer identity found in each insurer's own NPHIES message (paymentIssuer / Organization name) — read, not guessed
MSG = {'7001626717': ('GlobeMed Saudi', 'tpa'), '7001523724': ('GlobeMed Saudi', 'tpa'), '7041839510': ('GlobeMed Saudi', 'tpa'),
       '7001527667': ('GlobeMed Saudi', 'tpa'), '7001537161': ('GlobeMed Saudi', 'tpa'),
       '7001535694': ('Allied Cooperative Insurance Group (ACIG)', 'ins'), '7001641419': ('Gulf General Company for Cooperative Insurance', 'ins')}
ISSUER = {'7001526578': 'GlobeMed Saudi', '7001703672': 'GlobeMed Saudi', '7001571327': 'Bupa', '7000911508': 'Tawuniya',
          '7001593321': 'Al Rajhi Takaful', '7001607683': 'GIG', '7001549059': 'Al Etihad', '7001532279': 'Gulf Union', '7001539720': 'SAICO'}

rows = []
for s in P:
    f = s.split('|') + [''] * 13
    pk, pd, ins, amt, fee, dsum, dcnt, lnk, clm, tax, snd, accs, mons = f[:13]
    fl = lambda x: float(x) if x not in ('', None) else None
    dsum, dfee = (dsum.split('/') + [''])[:2]
    hd, dd = (pd.split('/') + [''])[:2]
    pd = hd
    amt, fee, dsum, dfee, clm, tax = fl(amt), fl(fee) or 0.0, fl(dsum), fl(dfee) or 0.0, fl(clm), fl(tax)
    dcnt, lnk = int(float(dcnt or 0)), int(float(lnk or 0))
    M = []
    for m in (mons or '').split(';'):
        if m.count(':') == 2:
            ym, c, a = m.split(':'); M.append([ym, int(float(c)), round(float(a), 2)])
    snd = snd if snd and snd != '/' else ''
    rows.append(dict(pk=int(pk), d=pd, hd=hd, dd=dd, ins=ins, amt=round(amt, 2), fee=round(fee, 2), dsum=dsum, dfee=round(dfee, 2), dcnt=dcnt, lnk=lnk,
                     clm=clm, tax=tax, snd=snd, accs=[a for a in (accs or '').split(',') if a], m=M, disp=DISP.get(pk, '')))

# header PAYMENT_DATE that carries hundreds of notices for one insurer is a bulk-load date, not a payment date:
# use the detail PAYMENT_DATE for those
bulk = collections.Counter((r['ins'], r['hd']) for r in rows)
for r in rows:
    r['bulk'] = bulk[(r['ins'], r['hd'])] > 200
    if r['bulk'] and r.get('dd'): r['d'] = r['dd']
# ---- insurer identity
INS = {}
for r in rows:
    i = r['ins']
    if i in INS: continue
    if i in BY_NPH:
        k, g = BY_NPH[i]; INS[i] = dict(id=i, status='named', grp=k, en=g['en'], ar=g['ar'], via=ISSUER.get(i, ''))
    else:
        nm, kind = MSG.get(i, (None, None))
        INS[i] = dict(id=i, status='tpa' if kind == 'tpa' else 'unnamed', grp=None, en=nm or '', ar='', via=nm if kind == 'tpa' else '')
# booking accounts per insurer (where its claims actually post)
bk = collections.defaultdict(collections.Counter)
for r in rows:
    for a in r['accs']: bk[r['ins']][a] += r['lnk'] or 1
for i, c in bk.items():
    INS[i]['book'] = [[a, SUBS.get(a, {}).get('name', ''), n] for a, n in c.most_common()]
for i, v in INS.items():
    b = v.get('book') or []
    # the carrier behind an unnamed NPHIES id = the account its claims actually book to (read from EXSYS, not guessed)
    v['carrier'] = b[0][1] if b else ''

# ---- two-sided reconciliation: NPHIES notice <-> Rafha ledger receipt on 1240007
GLD = json.load(open('gldesc.json'))
D = dt.date.fromisoformat
ASOF = max(r['d'] for r in rows)
AR_M = {'يناير':1,'فبراير':2,'مارس':3,'ابريل':4,'أبريل':4,'إبريل':4,'مايو':5,'يونيو':6,'يونيه':6,'يوليو':7,'يوليه':7,'اغسطس':8,'أغسطس':8,
        'سبتمبر':9,'اكتوبر':10,'أكتوبر':10,'نوفمبر':11,'ديسمبر':12}
import re
def narr_months(t):
    out = []
    for m in re.finditer(r'(يناير|فبراير|مارس|ابريل|أبريل|إبريل|مايو|يونيو|يونيه|يوليو|يوليه|اغسطس|أغسطس|سبتمبر|اكتوبر|أكتوبر|نوفمبر|ديسمبر)\s*(\d{4})?', t or ''):
        y = m.group(2)
        out.append((y + '-' if y else '') + '%02d' % AR_M[m.group(1)])
    for m in re.finditer(r'(20\d\d)[/-](\d{1,2})(?!\d)', t or ''): out.append('%s-%02d' % (m.group(1), int(m.group(2))))
    return sorted(set(out))
# which ledger sub-accounts belong to which NPHIES payer (booking accounts + the payer's own customer group)
SUB_INS = collections.defaultdict(set)
for r in rows:
    for a in r['accs']: SUB_INS[a].add(r['ins'])
for i, v in INS.items():
    if v['status'] == 'named':
        for k, sv in SUBS.items():
            if sv.get('cg') == v['grp']: SUB_INS[k].add(i)
cover = {}
for r in rows:
    c = cover.setdefault(r['ins'], [r['d'], r['d']]); c[0] = min(c[0], r['d']); c[1] = max(c[1], r['d'])
def co_ok(g, n):   # receipt booked under the right company for this notice?
    return g['sub'] in n['accs'] or n['ins'] in SUB_INS.get(g['sub'], ())
byins = collections.defaultdict(list)
for r in rows: byins[r['ins']].append(r)
for r in rows:
    r['gl'] = None
    # claim-level notices: one notice per claim, the bank transfer covers many of them (reconciled by month, not by amount)
    r['cl'] = r['ins'] in ('7000911508', '7001532279') or (r['ins'] == '7001571327' and r['lnk'] > 0)
seen = {}
for r in sorted(rows, key=lambda x: x['pk']):
    r['dup'] = None
    if r['cl']: continue
    k = (r['ins'], r['d'], r['amt'], r['disp'])
    if k in seen and r['disp']: r['dup'] = seen[k]
    else: seen[k] = r['pk']
G = sorted(GLR, key=lambda g: (g['d'], g['v']))
for g in G:
    k = g['v'] + '|' + g['sub']; x = GLD.get(k, {}); g['desc'] = x.get('desc', ''); g['user'] = x.get('user', '')
    g['nm'] = narr_months(g['desc']); g['m'] = None; g['st'] = None
def win(g, n): return -15 <= (D(g['d']) - D(n['d'])).days <= 100
def take(g, ns, kind, ok):
    for n in ns: n['gl'] = [g['v'], g['d'], g['sub'], kind, 1 if ok else 0]
    sm = sorted({m[0] for n in ns for m in n['m']})
    nm = g['nm']
    mok = None if not (sm and nm) else (1 if any(x[-2:] == y[-2:] and (len(x) < 7 or x[:4] == y[:4]) for x in nm for y in sm) else 0)
    g['m'] = dict(pks=[n['pk'] for n in ns], kind=kind, ok=1 if ok else 0, ins=ns[0]['ins'],
                  tot=round(sum(n['amt'] for n in ns), 2), sm=sm, mok=mok)
# pass 1: same company — single notice, then same-day total, then same-day total on this booking account
for g in G:
    ins = SUB_INS.get(g['sub'])
    if not ins: continue
    cands = [n for i in ins for n in byins[i] if n['gl'] is None and not n['cl'] and not n['dup'] and win(g, n)]
    a = round(g['amt'], 2)
    one = sorted([n for n in cands if abs(n['amt'] - a) < 0.011], key=lambda n: abs((D(g['d']) - D(n['d'])).days))
    if one: take(g, [one[0]], 'single notice', True); continue
    for key in (lambda n: (n['ins'], n['d']), lambda n: (n['ins'], n['d'], g['sub'] in n['accs'])):
        grp = collections.defaultdict(list)
        for n in cands: grp[key(n)].append(n)
        hit = [v for v in grp.values() if len(v) > 1 and abs(sum(n['amt'] for n in v) - a) < 0.02]
        if hit: take(g, hit[0], f'{len(hit[0])} notices same day', True); break
# pass 1c: same company, amount differs by at most 2 SAR (bank charge / rounding) — single notice or same-day total
for g in G:
    if g['m']: continue
    ins = SUB_INS.get(g['sub'])
    if not ins: continue
    cands = [n for i in ins for n in byins[i] if n['gl'] is None and not n['cl'] and not n['dup'] and win(g, n)]
    a = round(g['amt'], 2)
    one = sorted([n for n in cands if abs(n['amt'] - a) <= 2], key=lambda n: (abs(n['amt'] - a), abs((D(g['d']) - D(n['d'])).days)))
    if one: take(g, [one[0]], f'single notice, Δ {a - one[0]["amt"]:+.2f}', True); continue
    grp = collections.defaultdict(list)
    for n in cands: grp[(n['ins'], n['d'])].append(n)
    hit = sorted([v for v in grp.values() if len(v) > 1 and abs(sum(n['amt'] for n in v) - a) <= 2], key=lambda v: abs(sum(n['amt'] for n in v) - a))
    if hit: take(g, hit[0], f'{len(hit[0])} notices same day, Δ {a - sum(n["amt"] for n in hit[0]):+.2f}', True)
# pass 2: exact amount but booked under another company (only for amounts >= 100, to avoid chance matches)
for g in G:
    if g['m'] or g['amt'] < 100: continue
    cands = sorted([n for n in rows if n['gl'] is None and not n['cl'] and abs(n['amt'] - g['amt']) < 0.011 and win(g, n)],
                   key=lambda n: abs((D(g['d']) - D(n['d'])).days))
    if cands: take(g, [cands[0]], 'single notice', co_ok(g, cands[0]))
# receipt status
for g in G:
    ins = SUB_INS.get(g['sub'])
    if g['m']: g['st'] = 'matched' if g['m']['ok'] else 'other_co'
    elif not ins: g['st'] = 'non_nphies'
    elif all(i in ('7000911508', '7001532279') for i in ins): g['st'] = 'claim_level'
    else:
        c0 = min(cover[i][0] for i in ins); c1 = max(cover[i][1] for i in ins)
        g['st'] = 'before' if g['d'] < c0 else ('after' if D(g['d']) > D(c1) + dt.timedelta(days=45) else 'no_notice')
# notice status
for r in rows:
    if r['gl']: r['bs'] = 'booked' if r['gl'][4] else 'booked_other'
    elif r['cl']: r['bs'] = 'claim_level'
    elif r['dup']: r['bs'] = 'duplicate'
    else: r['bs'] = 'pending' if (D(ASOF) - D(r['d'])).days <= 60 else 'unbooked'
GL_OUT = [[g['v'], g['d'], g['sub'], round(g['amt'], 2), g['st'], g['desc'], ','.join(g['nm']), g['m'], g.get('user', ''),
           (lambda s: s)(g.get('st'))] for g in G]
GL_OUT = [x[:9] for x in GL_OUT]
# ---- flags
out = []
for r in rows:
    dA = round(r['amt'] - (r['dsum'] or 0) - r['dfee'], 2) if r['dsum'] is not None else None
    dC = round(r['amt'] - r['clm'], 2) if (r['clm'] is not None and r['lnk'] == r['dcnt'] and r['lnk'] > 0) else None
    fa = 'match' if dA is not None and abs(dA) < 1 else ('nodtl' if r['dsum'] is None else 'var')
    fc = None if dC is None else ('match' if abs(dC) < 1 else ('short' if dC < 0 else 'over'))
    ms = sorted({m[0] for m in r['m']})
    fm = 'none' if not ms else ('single' if len(ms) == 1 else 'mixed')
    I = INS[r['ins']]
    out.append([r['pk'], r['d'], r['ins'], r['amt'], r['dfee'], r['dsum'], r['dcnt'], r['lnk'], r['clm'], dA, dC, fa, fc, fm,
                r['m'], ','.join(r['accs']), r['snd'], r['disp'][:60], r.get('gl'), r['hd'] if r['bulk'] else '', r['bs'], r['dup'], r['tax']])
out.sort(key=lambda x: (x[1], x[0]), reverse=True)
F = ['pk', 'd', 'ins', 'amt', 'fee', 'dsum', 'dcnt', 'lnk', 'clm', 'dA', 'dC', 'fa', 'fc', 'fm', 'm', 'accs', 'snd', 'disp', 'gl', 'hd', 'bs', 'dupOf', 'tax']
res = dict(asOf=dt.date.today().isoformat(), branch='Rafha', fields=F, rows=out, ins=INS,
           subs={k: v['name'] for k, v in SUBS.items()}, glN=len(GLR), gl=GL_OUT,
           glF=['v','d','sub','amt','st','desc','nm','m','user'], cover=cover, subIns={k: sorted(v) for k, v in SUB_INS.items()},
           range=[min(r['d'] for r in rows), max(r['d'] for r in rows)])
json.dump(res, open('data_nph.json', 'w'), ensure_ascii=False, separators=(',', ':'))
c = collections.Counter
print('payments', len(out), 'SAR', round(sum(r[3] for r in out), 2), 'range', res['range'], 'bytes', os.path.getsize('data_nph.json'))
print('amount hdr-vs-detail', c(r[11] for r in out)); print('paid-vs-claimed', c(r[12] for r in out)); print('month', c(r[13] for r in out))
print('notice status', c(r[20] for r in out)); print('receipt status', c(g[4] for g in GL_OUT))
for i, v in INS.items(): print(i, v['status'], v['en'], v.get('via'), v.get('book', [])[:3])
