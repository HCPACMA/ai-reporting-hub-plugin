#!/usr/bin/env python3
"""Generic month: groups doctor overtime entries by (doctor, window) and emits compact SQL chunks (<=7500 chars) for branch ALL.
usage: python3 scripts/ot_feas_sql2.py 2026-01  -> raw/otf2_groups.<m>.json, raw/otf2_rev_<m>_<k>.sql, raw/otf2_svc_<m>_<k>.sql"""
import json, sys, calendar
m = sys.argv[1]; Y, M = int(m[:4]), int(m[5:])
ent = json.load(open('raw/otf_entries.%s.json' % m))['entries']
nxt = (Y + (M == 12), M % 12 + 1)
lo = "DATE '%04d-%02d-01'" % (Y, M); hi = "DATE '%04d-%02d-01'" % nxt
G = {}
for i, e in enumerate(ent):
    if e['kind'] != 'doctor' or e['st'] == '3013' or not e['win'] or not e['dd'] or 'cbahi' in e['reason'].lower(): continue
    for w in e['win']:
        if w[1] - w[0] > 16: continue
        k = (e['st'], w[0], w[1]); g = G.setdefault(k, {'st': e['st'], 'br': e['br'], 's': w[0], 'e': w[1], 'days': set()})
        g['days'].update(e['dd'])
gl = []
for n, (k, g) in enumerate(sorted(G.items())):
    g['g'] = n; g['days'] = sorted(g['days']); gl.append(g)
json.dump(gl, open('raw/otf2_groups.%s.json' % m, 'w'))
def sname(x): return 'S%d' % int(round(x * 2))
def cond(g):
    sh = sname(g['s']); yy = '%02d%02d' % (Y % 100, M)
    return ("WHEN D='%s' AND INSTR('%s',','||TO_CHAR(%s,'FMDD')||',')>0 AND TO_CHAR(%s,'YYMM')='%s' AND (%s-TRUNC(%s))*24<%s THEN '%d_'||TO_CHAR(%s,'FMDD')"
            % (g['st'], ',' + ','.join(map(str, g['days'])) + ',', sh, sh, yy, sh, sh, round(g['e'] - g['s'], 2), g['g'], sh))
chunks = []; cur = []; size = 0
for g in gl:
    c = cond(g)
    if cur and size + len(c) > 6000: chunks.append(cur); cur = []; size = 0
    cur.append(g); size += len(c)
if cur: chunks.append(cur)
for k, ch in enumerate(chunks):
    cases = ' '.join(cond(g) for g in ch); docs = ','.join(sorted({"'%s'" % g['st'] for g in ch}))
    cols = ','.join("PATIENT_INVOICE_DATE-%s/24 %s" % (x, sname(x)) for x in sorted({g['s'] for g in ch}))
    base = "FROM (SELECT DOCTOR_ID D, PATIENT_INVOICE_TYPE PT, INV_NET-NVL(VAT_AMT,0) NV, PATIENT_FILE_NO||'-'||EPISODE_NO FE, PRODUCT_CODE PC, " + cols + " FROM EXSYS.RC_NET_PATIENT_INVOICES_ITEMS WHERE SPECIALTY_NO<>30 AND PATIENT_INVOICE_DATE>=%s-1 AND PATIENT_INVOICE_DATE<%s+1 AND DOCTOR_ID IN (%s))" % (lo, hi, docs)
    rev = ("SELECT SUBSTR(K,1,INSTR(K,'_')-1) G, LISTAGG(SUBSTR(K,INSTR(K,'_')+1)||':'||C||':'||CN||':'||R||':'||RN,';') WITHIN GROUP (ORDER BY K) V FROM (SELECT K, ROUND(SUM(CASE WHEN T='C' THEN NV ELSE 0 END),2) C, COUNT(DISTINCT CASE WHEN T='C' THEN FE END) CN, ROUND(SUM(CASE WHEN T='R' THEN NV ELSE 0 END),2) R, COUNT(DISTINCT CASE WHEN T='R' THEN FE END) RN FROM (SELECT CASE " + cases +
           " END K, CASE WHEN PT='R' THEN 'R' WHEN PT IN ('C','D') THEN 'C' ELSE 'X' END T, NV, FE " + base + ") WHERE K IS NOT NULL GROUP BY K) GROUP BY SUBSTR(K,1,INSTR(K,'_')-1) ORDER BY 1")
    svc = ("SELECT G, LISTAGG(N||'~'||REV||'~'||C,'|') WITHIN GROUP (ORDER BY RN) V FROM (SELECT G,N,REV,C,ROW_NUMBER() OVER (PARTITION BY G ORDER BY REV DESC) RN FROM (SELECT SUBSTR(K,1,INSTR(K,'_')-1) G, NVL(MAX(p.DESCRIPTION_P),PC) N, ROUND(SUM(NV),0) REV, COUNT(*) C FROM (SELECT CASE " + cases +
           " END K, PC, NV " + base + ") x LEFT JOIN EXSYS.IM_PRODUCT_MASTER p ON p.PRODUCT_CODE=x.PC WHERE K IS NOT NULL GROUP BY SUBSTR(K,1,INSTR(K,'_')-1), PC)) WHERE RN<=5 GROUP BY G ORDER BY 1")
    open('raw/otf2_rev_%s_%d.sql' % (m, k), 'w').write(rev); open('raw/otf2_svc_%s_%d.sql' % (m, k), 'w').write(svc)
    print(m, 'chunk', k, 'groups', len(ch), 'len', len(rev), len(svc))
