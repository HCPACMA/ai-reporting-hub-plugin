"""Unlinked JV audit: tax transactions (GL_VOUCHER_TAX_* / CM_VOUCHER_TAX_*) vs the vouchers they post (VOUCHER_MASTERS / CM_VOUCHER_MASTER)."""
import json, os, sys, collections
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H); sys.path.insert(0, '/home/claude/work/dmv')
from pk2 import packed2
from parse import rows
BR = {'الرياض':'Riyadh','بريدة 1':'BUR1','بريدة 2':'BUR2','رفحاء':'Rafha'}
f = lambda s: float(s) if s not in ('', None) else None
def trip(s):
    p = (s or '').split('/') + ['', '', '', '', '']
    return f(p[0]), f(p[1]), int(p[2] or 0), f(p[3]), p[4]
TX = []
def add(src, br, r):
    tno, v, st, d, tx, vst, vc, eu, ds = (r + [''] * 9)[:9]
    tdr, tvat, tn, ttot, tacc = trip(tx); vdr, vvat, vn, vtot, vacc = trip(vc)
    TX.append(dict(src=src, br=BR.get(br, br), tno=tno, v=v or None, st=st, d=d, tdr=tdr, tvat=tvat, tn=tn, ttot=ttot, vst=vst or None, vdr=vdr, vvat=vvat, vn=vn, vtot=vtot, eu=eu, ds=ds.strip()))
for fn, k in (('gl_riy_1.json', r'G\d{3}'), ('gl_riy_2.json', r'G\d{3}'), ('gl_oth.json', r'G\d+')):
    for br, r in packed2(os.path.join(H, fn), k): add('GL', br, r)
for br, r in packed2(os.path.join(H, 'cm_all.json'), r'C\d{3}'): add('CM', br, r)
refs = collections.Counter((t['src'], t['br'], t['v']) for t in TX if t['v'])
def cls(t):
    out = []
    if t['st'] == 'P':
        if not t['v']: out.append('posted_nojv')
        elif not t['vst']: out.append('jv_missing')
        elif t['vst'] == 'C': out.append('jv_cancelled')
        elif t['vst'] == 'O': out.append('jv_open')
        else:
            if t['tdr'] is not None and t['vdr'] is not None and abs(t['tdr'] - t['vdr']) > 0.05: out.append('amt_diff')
    elif t['st'] == 'O': out.append('open_pending')
    elif t['st'] == 'C' and t['v'] and t['vst'] and t['vst'] != 'C': out.append('cancelled_live_jv')
    if t['v'] and refs[(t['src'], t['br'], t['v'])] > 1: out.append('shared_jv')
    return out
for t in TX: t['fl'] = cls(t)
# live system JVs with no tax transaction behind them
GLS = []
for v, s, d, ss, ty, sq, sqo, dr, vat, eu, ds, br in rows(os.path.join(H, 'gls.json')):
    kind = 'closing' if 'إقفال الحسابات الختامية' in ds else ('purchase_2019' if ds.startswith('Purchase') else 'system')
    GLS.append(dict(br=BR.get(br, br), v=v, st=s, d=d, dr=f(dr), vat=f(vat), eu=eu, ds=ds, kind=kind))
# twins: same date + same debit total as a tax-linked voucher; duplicate only when the lines are identical
FP = {r[0]: r[1] for r in rows(os.path.join(H, 'fp.json'))}
DUP = []
for lv, tno, tw, ts, ty, d, dr, n, bn, bds, br in rows(os.path.join(H, 'twin.json')):
    same = FP.get(lv) and FP.get(lv) == FP.get(tw)
    if same: DUP.append(dict(br=BR.get(br, br), tno=tno, lv=lv, twin=tw, st=ts, ty=ty, d=d, dr=f(dr), n=int(float(n)), ds=bds))
for g in GLS:
    if any(x['twin'] == g['v'] for x in DUP): g['kind'] = 'duplicate'; g['tno'] = [x['tno'] for x in DUP if x['twin'] == g['v']][0]; g['lv'] = [x['lv'] for x in DUP if x['twin'] == g['v']][0]
    elif g['kind'] == 'system':
        m = [t for t in TX if t['src'] == 'GL' and t['br'] == g['br'] and t['st'] in ('C', 'O') and t['d'] == g['d'] and t['tdr'] and g['dr'] and abs(t['tdr'] - g['dr']) < 0.05]
        if m:
            g['kind'] = 'orphan'; g['tno'] = m[0]['tno']; g['tst'] = m[0]['st']
            rp = [t for t in TX if t['src'] == 'GL' and t['br'] == g['br'] and t['st'] == 'P' and t['tdr'] and abs(t['tdr'] - g['dr']) < 0.05 and t['d'] == g['d'] and t['ds'][:25] == m[0]['ds'][:25]]
            if rp: g['repost'] = [rp[0]['tno'], rp[0]['v'], rp[0]['d']]
# cash-management side: live cash voucher with the same date, cash account and amount as a cancelled cash tax transaction
for tno, ts, d, tamt, acc, v, vs, vamt, eu, ds, br in rows(os.path.join(H, 'cmorph.json')):
    GLS.append(dict(br=BR.get(br, br), v=v, st=vs, d=d, dr=f(vamt), vat=None, eu=eu, ds=ds, kind='orphan_cm', tno=tno, tst=ts))
# same supplier invoice in more than one posted tax transaction
DI = []
for src, inv, taxno, nt, txs, vat, br in rows(os.path.join(H, 'dupinv.json')):
    items = [x.split('>') for x in txs.split(',') if x]
    its = [dict(t=a[0], v=a[1], d=a[2], dr=f(a[3]), vat=f(a[4])) for a in items if len(a) >= 5]
    same = len({(i['dr'], i['vat']) for i in its}) == 1
    DI.append(dict(src=src, br=BR.get(br, br), inv=inv, taxno=taxno, n=len(its), its=its, vat=f(vat), same=same))
OUT = dict(asOf='2026-10-01', tx=[t for t in TX if t['fl']], n=collections.Counter(f"{t['src']}|{t['br']}|{t['st']}" for t in TX),
           ok=sum(1 for t in TX if t['st'] == 'P' and not t['fl']), total=len(TX), gls=GLS, dup=DUP, di=DI)
json.dump(OUT, open(os.path.join(H, 'data_uj2.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
print('tx', len(TX), 'ok posted', OUT['ok'], 'flagged', len(OUT['tx']))
print(collections.Counter(x for t in TX for x in t['fl']))
for t in OUT['tx']:
    if any(x not in ('open_pending',) for x in t['fl']): print(t['src'], t['br'], t['tno'], t['v'], t['st'], t['vst'], t['d'], t['tdr'], t['vdr'], t['tvat'], t['vvat'], t['fl'], t['ds'][:50])
print('GLS', collections.Counter(g['kind'] for g in GLS)); print('DUP', DUP)
print('DI', len(DI), sum(1 for d in DI if d['same']), round(sum(d['vat'] for d in DI if d['same']),2))
