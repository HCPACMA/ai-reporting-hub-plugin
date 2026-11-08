# -*- coding: utf-8 -*-
"""Fast, incremental refresh of the Modeling Desk from the four EXSYS databases (Cure MCP only).

Why it is fast
  * Closed periods are cached. Every refresh re-reads only the open window:
      ledger jobs      -> 1 Jan of the open year (1 Jan of last year until 31 Mar, for late postings)
      invoice jobs     -> 1st of the previous month
  * Every light job is one GROUP BY per branch, so the four branch calls run in parallel.
  * Heavy line-level tests (window functions over years of lines) run weekly, one call at a time.
  * Results are parsed from the MCP result files, never re-typed, and every payload is rebuilt,
    validated and patched into the HTML by one command.

Usage (run from anywhere; ROOT defaults to /home/claude/work, override with CFO_ROOT)
  python3 refresh.py plan [--asof YYYY-MM-DD] [--weekly]
        -> runs/<id>/plan.md + one .sql per (job, branch). Run batch A in parallel (4 at a time),
           batch B one at a time. Copy each SQL verbatim into cure_run_query.
  python3 refresh.py ingest <job> <branch 01..04> (--file <mcp result file> | --marker '<text in the result>')
  python3 refresh.py build     -> merge staged results into the caches, rebuild payloads, validate, patch HTML
  python3 refresh.py status    -> what is staged / missing for the current run
  python3 refresh.py setup     -> lay out CFO_ROOT from the kit (scripts into gl/ drv/ anomdb/ expdb/ aud/ zak/ dmv/ norm/, kit symlink)
  python3 refresh.py pack      -> tar the caches + staged runs to /mnt/user-data/outputs/cfo_cache_<date>.tgz (then SendUserFile + device_commit_files to CFO-Cure-Kit\\cache\\)
  python3 refresh.py restore <tgz>  -> unpack a cache tgz into CFO_ROOT (run `setup` first)
  Session start: stage CFO-Cure-Kit\\cache\\cfo_cache_latest.tgz, `setup`, `restore`. Session end / after every build: `pack` and write it back. Caches live ONLY in the cloud container otherwise and are lost on reset.
"""
import json, os, sys, re, glob, datetime as dt, subprocess, collections, shutil

ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
KIT = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(ROOT, 'AlFaihaa_Modeling_Desk.html')
RUNS = os.path.join(KIT, 'runs')
BR = {'01': ('Riyadh', 'EXSYS.'), '02': ('BUR1', ''), '03': ('BUR2', ''), '04': ('Rafha', '')}
YFILE = {'01': 'y_riy.txt', '02': 'y_bur1.txt', '03': 'y_bur2.txt', '04': 'y_rafha.txt'}
EXPC = {'01': 'R', '02': 'B1', '03': 'B2', '04': 'B4'}
CCBR = {'01': 'RIY', '02': 'B1', '03': 'B2', '04': 'RF'}
sys.path.insert(0, os.path.join(ROOT, 'gl'))

# ----------------------------------------------------------------------------- windows
def windows(asof):
    ly = asof.year - 1 if asof.month <= 3 else asof.year          # ledger: keep last year open until Q1 ends
    pm = (asof.replace(day=1) - dt.timedelta(days=1)).replace(day=1)  # invoices: from 1st of previous month
    bl, bi = os.environ.get('BOOT_LEDGER'), os.environ.get('BOOT_INV')     # bootstrap: widen the windows to rebuild lost caches
    return {'ledger': dt.date.fromisoformat(bl) if bl else dt.date(ly, 1, 1), 'invoice': dt.date.fromisoformat(bi) if bi else pm,
            'end': dt.date(asof.year + 1, 1, 1), 'asof': asof}

# ----------------------------------------------------------------------------- SQL generators
def rd(p): return open(os.path.join(ROOT, p), encoding='utf-8').read()
def sql_file(p):   # strip comment lines, join
    return ' '.join(l for l in rd(p).split('\n') if not l.strip().startswith('--')).strip().rstrip(';')

def g_gl_annual(P, W):
    s = sql_file('kit/sql/gl_annual_accounts.sql').replace('{P}', P).replace('{B}', '70')
    return s.replace("WHERE t.STATUS<>'C'", f"WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{W['ledger']}'", 1)
def g_gl_cc(P, W):
    return rd('gl/cc.sql').replace('{P}', P).replace('{B}', '60').replace("DATE '2025-01-01'", f"DATE '{W['ledger']}'").strip()
def g_gl_drcr(P, W):
    s = rd('gl/drcr.sql').replace('{P}', P).strip()
    return s.replace("WHERE t.STATUS<>'C'", f"WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{W['ledger']}'", 1)
def g_inv(kind):
    def f(P, W):
        return subprocess.check_output(['python3', os.path.join(ROOT, 'anomdb/gen.py'), P, str(W['invoice']), str(W['end']), kind, '60'], text=True).strip()
    return f
def g_exp_monthly(P, W):
    s = sql_file('kit/sql/expense_monthly.sql')
    return s.replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
def g_aud_ctrl(P, W):
    s = rd('aud/ctrl.sql').replace('{P}', P).replace('{B}', '60').strip()
    return s.replace("WHERE t.STATUS<>'C'", f"WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{W['ledger']}'", 1)
def g_aud_vatgl(P, W):
    return rd('aud/vat_gl.sql').replace('{P}', P).replace("DATE '2023-01-01'", f"DATE '{W['ledger']}'").strip()
def g_aud_invm(P, W):
    s = ' '.join(rd('aud/inv_month.sql').split())
    return s.replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
def g_aud_uj(P, W):
    return rd('aud/uj.sql').replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end'])).strip()
def g_aud_vchk(P, W):
    return rd('aud/vchk.sql').replace('{P}', P).replace("DATE '2023-01-01'", f"DATE '{W['ledger']}'").strip()
def g_gl_open(P, W):   # vouchers of the open year still in status O: count per branch + movement on 12x accounts
    y0 = f"DATE '{dt.date(W['end'].year - 1, 1, 1)}'"
    return (f"SELECT 'N' a, COUNT(DISTINCT t.VOUCHER_NO) n, 0 v FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS='O' AND t.VM_DATE>={y0} "
            f"UNION ALL SELECT t.ACCOUNT_NO, COUNT(DISTINCT t.VOUCHER_NO), ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2) FROM {P}GL_TRANSACTIONS_DETAILS t "
            f"WHERE t.STATUS='O' AND t.VM_DATE>={y0} AND t.ACCOUNT_NO LIKE '12%' GROUP BY t.ACCOUNT_NO")
def g_bd_open(P, W):   # open (STATUS='O') vouchers on profit-and-loss accounts by month and branch/head-office cost centre — memo for Branches & Departments
    return (f"SELECT TO_CHAR(t.VM_DATE,'YYMM') ym, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) cc, COUNT(DISTINCT t.VOUCHER_NO) n, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '4%' THEN t.CR_AMOUNT-t.DR_AMOUNT ELSE 0 END),2) rev, "
            f"ROUND(SUM(CASE WHEN t.ACCOUNT_NO LIKE '3%' THEN t.DR_AMOUNT-t.CR_AMOUNT ELSE 0 END),2) exp "
            f"FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS='O' AND t.VM_DATE>=DATE '2023-01-01' AND t.VOUCHER_NO<>'JV1-24/04043' "
            f"AND (t.ACCOUNT_NO LIKE '3%' OR t.ACCOUNT_NO LIKE '4%') AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) "
            f"GROUP BY TO_CHAR(t.VM_DATE,'YYMM'), SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) ORDER BY 1, 2")
def g_vat_tb(P, W):
    return sql_file('kit/sql/tb_movements_monthly.sql').replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
def g_vat_ret(P, W):   # the VAT return itself (EXSYS VAT_FORM) from the MV, same window as the ledger
    return sql_file('kit/sql/vat_return_monthly.sql').replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
def _vpin(name):
    return lambda P, W: ' '.join(l for l in sql_file('kit/sql/' + name + '.sql').split('\n') if not l.strip().startswith('--')).replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
g_vat_pin_mv, g_vat_pin_gl, g_vat_pin_nm = _vpin('vat_pin_mv'), _vpin('vat_pin_gl'), _vpin('vat_pin_nm')
def g_is_mon(P, W):   # monthly income statement by nature, 2019 -> end (Statements tab same-months comparison)
    return ' '.join(sql_file('kit/sql/is_monthly_by_nature.sql').split()).replace('{P}', P).replace('{B}', '20').replace('{D0}', '2019-01-01').replace('{D1}', str(W['end']))
def g_yec(P, W):   # year-end provisions (EOSB / insurer discount / zakat) booked on 31-Dec -> DATA.yec for the estimate checkbox
    return ' '.join(sql_file('kit/sql/year_end_provisions.sql').split()).replace('{P}', P).replace('{D0}', '2019-01-01').replace('{D1}', str(W['end']))
def g_cn(P, W):   # customer credit notes (all statuses) -> DATA.cn
    return ' '.join(sql_file('kit/sql/cn_notes.sql').split()).replace('{P}', P).replace('{D0}', '2022-01-01').replace('{D1}', str(W['end']))
def g_cn_nm(P, W):
    return ' '.join(sql_file('kit/sql/cn_names.sql').split()).replace('{P}', P)
def g_lease_chk(P, W):   # live re-check of the Lease Audit findings (see kit/sql/lease_recheck.sql)
    vl = json.load(open(os.path.join(ROOT, 'kit', 'sql', 'lease_vlist.json'), encoding='utf-8'))
    q = lambda L: ','.join("'" + v + "'" for v in L)
    gv = [v for v in vl if v in ('JV1-26/02052', 'JV1-26/02053', 'JV1-26/02413', 'JV1-26/02569', 'JV1-26/02570', 'JV1-26/02747')]
    return ' '.join(sql_file('kit/sql/lease_recheck.sql').split()).replace('{P}', P).replace('{D1}', str(W['end'])).replace('{Y0}', str(int(str(W['end'])[:4])) + '-01-01').replace('{GV}', q(gv)).replace('{VL}', q(vl))
g_vat_cls = _vpin('vat_cls')   # patient (999999) share of return sales boxes 1-5, for the VAT tab's statement by VAT treatment
def g_vat_adj(P, W):
    a1, a2 = [' '.join(l for l in x.split('\n') if not l.strip().startswith('--')).strip().rstrip(';')
              for x in rd('kit/sql/vat_recon_adjustments.sql').split(';\n')[:2]]
    a1, a2 = [re.sub(r'\s+ORDER BY 1\s*$', '', x) for x in (a1, a2)]
    a2 = a2.replace("||';'||ROUND(SUM(T.CR_AMOUNT),2) R", "||';INV;0;'||ROUND(SUM(T.CR_AMOUNT),2) R")
    return (a1 + ' UNION ALL ' + a2).replace('{P}', P).replace('{D0}', str(W['ledger'])).replace('{D1}', str(W['end']))
# Deep Analysis drivers + monthly bucket series (DATA.m, DATA.drv): posted + open, account x cc-prefix x function x month
def _drvgen(kind, P, d0, d1):
    return subprocess.check_output(['python3', os.path.join(ROOT, 'drv/gen.py'), kind, P, str(d0), str(d1)], text=True).strip()
def g_gl_mon(P, W): return _drvgen('gl', P, W['ledger'], W['end'])
def g_cc_mon(P, W): return _drvgen('cc', P, W['ledger'], W['end'])
# Branches & Departments: ledger-held balances per database (year-ends of the 4 previous years + the last closed day)
def g_bd_cc3(P, W):   # P&L lines posted on the 3-character branch cost centres 001-004 (prefix '00' hides them in the 2-character convention): account|cc|yymm|DR-CR
    return ("SELECT bkt, LISTAGG(r,'~') WITHIN GROUP (ORDER BY r) r FROM (SELECT FLOOR((ROW_NUMBER() OVER (ORDER BY a,cc,ym)-1)/60) bkt, a||'|'||cc||'|'||ym||'|'||amt r FROM ("
            "SELECT t.ACCOUNT_NO a, t.COST_CENTER_NO cc, TO_CHAR(t.VM_DATE,'YYMM') ym, TO_CHAR(ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2)) amt "
            f"FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '2023-01-01' AND t.VM_DATE<DATE '{W['end']}' "
            "AND (t.ACCOUNT_NO LIKE '3%' OR t.ACCOUNT_NO LIKE '4%') AND LENGTH(t.COST_CENTER_NO)=3 AND t.COST_CENTER_NO IN ('001','002','003','004') AND t.VOUCHER_NO<>'JV1-24/04043' "
            f"AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) "
            "GROUP BY t.ACCOUNT_NO, t.COST_CENTER_NO, TO_CHAR(t.VM_DATE,'YYMM'))) GROUP BY bkt ORDER BY bkt")
def g_bd_bal(P, W):
    y0 = W['asof'].year; ds = [f'{y}-12-31' for y in range(y0 - 4, y0)] + [str(W['asof'] - dt.timedelta(days=1))]
    s = sql_file('kit/sql/branch_balances.sql').replace('{P}', P)
    for k, d in enumerate(ds, 1): s = s.replace('{D%d}' % k, d)
    return s
# Zakat: zakat expense/provision lines and every expense line whose description names a violation or fine
def g_zak_lines(P, W):
    return (f"SELECT TO_CHAR(t.VM_DATE,'YYYY-MM-DD') d, t.VOUCHER_NO v, t.ACCOUNT_NO a, t.STATUS s, ROUND(t.DR_AMOUNT-t.CR_AMOUNT,2) amt, "
            f"REPLACE(SUBSTR(t.DESCRIPTION,1,120),'|','/') ds FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.STATUS<>'C' AND t.VM_DATE>=DATE '{W['ledger']}' "
            f"AND t.VOUCHER_NO<>'JV1-24/04043' AND (t.ACCOUNT_NO IN ('3280005','2123003','2111004') OR (t.ACCOUNT_NO LIKE '3%' AND "
            f"(t.DESCRIPTION LIKE '%مخالف%' OR t.DESCRIPTION LIKE '%غرام%'))) AND NOT EXISTS (SELECT 1 FROM {P}FINANCIAL_YEARS fy "
            f"WHERE fy.GL_VOUCHER_NO=t.VOUCHER_NO) ORDER BY t.VM_DATE")
# heavy, weekly: full re-read of top-N lists
def g_inv2(kind, n, d0='2024-01-01'):
    def f(P, W):
        return subprocess.check_output(['python3', os.path.join(ROOT, 'anomdb/gen2.py'), P, d0, str(W['end']), kind, str(n)], text=True).strip()
    return f
def g_exp_flags(part):
    def f(P, W):
        s = open(os.path.join(ROOT, 'expdb/flags_R.sql')).read()
        s = s.replace('EXSYS.', P)
        i = s.index(" UNION ALL SELECT 'L'")
        return s[:i] if part == 'S' else s[i + len(' UNION ALL '):]
    return f

def g_norm(P, W):   # lines of the vouchers listed in Normalization.xlsx (norm/vouchers.json) on profit-and-loss accounts, by month, full cost centre and function
    vs = json.load(open(os.path.join(ROOT, 'norm', 'vouchers.json')))
    inl = ','.join("'" + re.sub(r"[^A-Za-z0-9/_-]", '', x['v']) + "'" for x in vs) or "'-'"
    fn = ("CASE WHEN SUBSTR(t.ACCOUNT_NO,1,1)<>'3' THEN '-' WHEN SUBSTR(t.COST_CENTER_NO,1,4) IN ('0102','0202','0302','0402') THEN 'COR' "
          "WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN 'GA' WHEN t.COST_CENTER_NO IN ('010100','020102','030100','040100') THEN 'INS' "
          "WHEN t.COST_CENTER_NO IN ('01011301','01011302','01011303','02011301','03011301','04011301') THEN 'COR' "
          "WHEN SUBSTR(t.COST_CENTER_NO,1,2)='00' THEN 'HO' ELSE 'X' END")
    return (f"SELECT t.VOUCHER_NO v, TO_CHAR(MIN(t.VM_DATE),'YYYY-MM-DD') d, TO_CHAR(t.VM_DATE,'YYMM') ym, SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) cc, {fn} f, t.ACCOUNT_NO a, "
            f"ROUND(SUM(t.DR_AMOUNT-t.CR_AMOUNT),2) amt, COUNT(*) n, CASE WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN '0'||SUBSTR(t.COST_CENTER_NO,3,1) ELSE SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) END bc FROM {P}GL_TRANSACTIONS_DETAILS t WHERE t.VOUCHER_NO IN ({inl}) AND t.STATUS<>'C' "
            f"AND (t.ACCOUNT_NO LIKE '3%' OR t.ACCOUNT_NO LIKE '4%') GROUP BY t.VOUCHER_NO, TO_CHAR(t.VM_DATE,'YYMM'), SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2), {fn}, t.ACCOUNT_NO, CASE WHEN t.COST_CENTER_NO IN ('001','002','003','004') THEN '0'||SUBSTR(t.COST_CENTER_NO,3,1) ELSE SUBSTR(NVL(t.COST_CENTER_NO,'00'),1,2) END ORDER BY 1, 3, 6")

JOBS = {   # name: (batch, generator, parser)
    'gl_annual':   ('A', g_gl_annual, 'packed'),
    'gl_cc':       ('A', g_gl_cc, 'packed_nc'),
    'gl_drcr':     ('A', g_gl_drcr, 'cols'),
    'gl_open':     ('A', g_gl_open, 'cols'),
    'vat_tb':      ('A', g_vat_tb, 'text1'),
    'vat_adj':     ('A', g_vat_adj, 'text1'),
    'vat_ret':     ('A', g_vat_ret, 'text1'),
    'vat_pin_mv':  ('A', g_vat_pin_mv, 'packed_nc'),
    'vat_pin_gl':  ('A', g_vat_pin_gl, 'packed_nc'),
    'vat_pin_nm':  ('A', g_vat_pin_nm, 'packed_nc'),
    'is_mon':      ('A', g_is_mon, 'packed_nc'),
    'vat_cls':     ('A', g_vat_cls, 'text1'),
    'yec':         ('A', g_yec, 'text1'),
    'lease_chk':   ('A', g_lease_chk, 'text1'),
    'cn':          ('A', g_cn, 'packed_nc'),
    'cn_nm':       ('A', g_cn_nm, 'text1'),
    'exp_monthly': ('A', g_exp_monthly, 'text1'),
    'aud_ctrl':    ('A', g_aud_ctrl, 'packed'),
    'aud_vatgl':   ('A', g_aud_vatgl, 'onerow'),
    'aud_invm':    ('A', g_aud_invm, 'cols'),
    'aud_uj':      ('A', g_aud_uj, 'packed'),
    'aud_vchk':    ('A', g_aud_vchk, 'packed'),
    'inv_daily':   ('A', g_inv('daily'), 'packed'),
    'inv_doc':     ('A', g_inv('doc'), 'packed'),
    'inv_cash':    ('A', g_inv('cash'), 'packed'),
    'inv_vis':     ('A', g_inv('vis'), 'packed'),
    'gl_mon':      ('A', g_gl_mon, 'packed'),
    'cc_mon':      ('A', g_cc_mon, 'packed'),
    'zak_lines':   ('A', g_zak_lines, 'cols'),
    'bd_bal':      ('A', g_bd_bal, 'cols'),
    'bd_open':     ('A', g_bd_open, 'cols'),
    'bd_cc3':      ('A', g_bd_cc3, 'packed_nc'),
    'norm':        ('A', g_norm, 'cols'),
    # weekly (plan --weekly): heavy, one call at a time, never in parallel
    'inv_exc':     ('B', g_inv2('exc', 400), 'packed'),
    'inv_price':   ('B', g_inv2('price', 200, '2025-01-01'), 'packed'),
    'inv_dup':     ('B', g_inv2('dup', 150), 'packed'),
    'inv_disc':    ('B', g_inv2('disc', 150), 'packed'),
    'exp_flagsS':  ('B', g_exp_flags('S'), 'text1'),
    'exp_flagsL':  ('B', g_exp_flags('L'), 'text1'),
}

# ----------------------------------------------------------------------------- result parsing
def transcript_find(marker):
    best = None
    for J in sorted(glob.glob(os.path.expanduser('~/.claude/projects/**/*.jsonl'), recursive=True), key=os.path.getmtime):
        for line in open(J, encoding='utf-8'):
            if marker not in line: continue
            try: o = json.loads(line)
            except Exception: continue
            c = (o.get('message') or {}).get('content')
            if not isinstance(c, list): continue
            for it in c:
                if isinstance(it, dict) and it.get('type') == 'tool_result':
                    cc = it.get('content')
                    t = cc if isinstance(cc, str) else ''.join(x.get('text', '') for x in cc if isinstance(x, dict)) if isinstance(cc, list) else ''
                    if marker in t and t.lstrip().startswith('{"result"'): best = t
    if best is None: raise SystemExit('marker not found in any transcript: ' + marker)
    return best

def result_text(args):
    if args.get('file'):
        t = open(args['file'], encoding='utf-8').read()
    else:
        t = transcript_find(args['marker'])
    return json.loads(t)['result']

def parse_text(t):   # packed rows: | bkt | n | r | _branch |  (r = rows joined by ~, fields by |)
    out = []
    for l in [l for l in t.split('\n') if re.match(r'\|\s*\d+(\.0)?\s*\|', l)]:
        m = re.match(r'\|\s*(\d+)(?:\.0)?\s*\|\s*(\d+)(?:\.0)?\s*\|(.*)\|[^|]*\|\s*$', l)
        if not m: raise ValueError('bad line ' + l[:80])
        n = int(m.group(2)); parts = m.group(3).strip().split('~')
        if len(parts) != n: raise ValueError(f'bucket {m.group(1)}: {len(parts)} vs {n}')
        out += [p.split('|') for p in parts]
    return out

def parse(kind, s):
    if kind == 'packed':
        return parse_text(s)
    lines = [l for l in s.split('\n') if l.startswith('| ') and not re.match(r'^\|\s*(r|R|bkt|YM|g)\s*\|', l)]
    bl = [i for i, l in enumerate(s.split('\n')) if l.startswith('+-')]
    if len(bl) >= 2:       # rows between the 2nd and 3rd border only: drops the header row whatever its column names are
        L = s.split('\n'); lines = [l for l in L[bl[1] + 1:(bl[2] if len(bl) > 2 else len(L))] if l.startswith('| ')]
    if kind == 'text1':      # single text column (may itself contain '|') + _branch column
        return [l.strip().strip('|').rsplit('|', 1)[0].strip() for l in lines]
    if kind == 'cols':       # plain columns, last one is _branch
        return [[c.strip() for c in l.strip().strip('|').split('|')][:-1] for l in lines]
    if kind == 'onerow':     # LISTAGG(...,'~') r, COUNT n, _branch
        out = []
        for l in lines:
            body = l.strip().strip('|').rsplit('|', 2)[0].strip()
            for p in body.split('~'): out.append([x.strip() for x in p.split('|')])
        return out
    if kind == 'packed_nc':  # bkt, LISTAGG r, _branch (no count column)
        out = []
        for l in lines:
            body = l.strip().strip('|').split('|', 1)[1].rsplit('|', 1)[0].strip()
            for p in body.split('~'): out.append([x.strip() for x in p.split('|')])
        return out
    raise ValueError(kind)

# ----------------------------------------------------------------------------- run bookkeeping
def cur_run():
    rs = sorted(glob.glob(os.path.join(RUNS, '*')))
    if not rs: raise SystemExit('no run planned — run: refresh.py plan')
    return rs[-1]

def plan(asof, weekly, only=None):
    W = windows(asof)
    rid = os.path.join(RUNS, asof.strftime('%Y%m%d') + ('w' if weekly else '') + (os.environ.get('RUN_TAG') or ''))
    os.makedirs(os.path.join(rid, 'sql'), exist_ok=True); os.makedirs(os.path.join(rid, 'staged'), exist_ok=True)
    jobs = [j for j, v in JOBS.items() if (v[0] == 'A' or weekly) and (not only or j in only)]
    md = [f'# Refresh run {os.path.basename(rid)}  (as of {asof})', '',
          f'Ledger window from {W["ledger"]}, invoice window from {W["invoice"]}.', '',
          '## Batch A — light, run the four branches of a job in parallel', '']
    items = []
    for j in jobs:
        for br, (name, P) in BR.items():
            s = JOBS[j][1](P, W)
            if not s.upper().startswith('SELECT'): raise SystemExit(f'{j}: SQL must start with SELECT')
            f = os.path.join(rid, 'sql', f'{j}_{br}.sql'); open(f, 'w').write(s)
            items.append({'job': j, 'br': br, 'branch': name, 'sql': f, 'batch': JOBS[j][0]})
    for b in ('A', 'B'):
        if b == 'B' and weekly: md += ['', '## Batch B — heavy, ONE call at a time; after a timeout wait 3 minutes', '']
        for it in items:
            if it['batch'] == b: md.append(f"- [ ] `{it['job']}` · {it['branch']} ({it['br']}) · sql/{os.path.basename(it['sql'])}")
    md += ['', 'After each call: `python3 refresh.py ingest <job> <br> --file <saved result>` (or `--marker "<text from the result>"`).',
           'Then: `python3 refresh.py build`.']
    json.dump({'asof': str(asof), 'win': {k: str(v) for k, v in W.items()}, 'items': items}, open(os.path.join(rid, 'plan.json'), 'w'), indent=1)
    open(os.path.join(rid, 'plan.md'), 'w').write('\n'.join(md) + '\n')
    print(os.path.join(rid, 'plan.md')); print(f'{len(items)} calls ({sum(1 for i in items if i["batch"]=="A")} light)')

def ingest(job, br, args):
    rid = cur_run(); rows = parse(JOBS[job][2], result_text(args))
    f = os.path.join(rid, 'staged', f'{job}_{br}.json')
    if args.get('append') and os.path.exists(f): rows = json.load(open(f)) + rows      # chunked pulls (date ranges) are added together
    json.dump(rows, open(f, 'w'), ensure_ascii=False)
    print(job, br, len(rows), 'rows staged' + (' (appended)' if args.get('append') else ''))

def status():
    rid = cur_run(); P = json.load(open(os.path.join(rid, 'plan.json')))
    miss = [f"{i['job']}_{i['br']}" for i in P['items'] if not os.path.exists(os.path.join(rid, 'staged', f"{i['job']}_{i['br']}.json"))]
    print(os.path.basename(rid), 'staged', len(P['items']) - len(miss), 'of', len(P['items']))
    for m in miss: print(' missing', m)
    return miss

# ----------------------------------------------------------------------------- merge into caches
def J(p): return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
def JW(p, o): json.dump(o, open(os.path.join(ROOT, p), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

def merge_all(rid):
    P = json.load(open(os.path.join(rid, 'plan.json'))); W = {k: dt.date.fromisoformat(v) for k, v in P['win'].items()}
    st = {}
    for f in glob.glob(os.path.join(rid, 'staged', '*.json')):
        k = os.path.basename(f)[:-5]; job, br = k.rsplit('_', 1); st.setdefault(job, {})[br] = json.load(open(f))
    Y0, M0 = W['ledger'].year, int(W['invoice'].strftime('%Y%m'))
    YM0 = int(W['ledger'].strftime('%Y%m'))
    log = []
    def need_all(job):
        if job in st and len(st[job]) != 4: raise SystemExit(f'{job}: staged for {sorted(st[job])} only — all four branches are required')
        return job in st
    if need_all('gl_annual'):
        for br, rows in st['gl_annual'].items():
            p = os.path.join(ROOT, 'gl', YFILE[br])
            keep = [l for l in open(p) if l.strip() and int(l.split('|')[0]) < Y0]
            open(p, 'w').write(''.join(keep) + ''.join('|'.join(r) + '\n' for r in rows))
        log.append(f'gl_annual: years >= {Y0} replaced')
    if need_all('gl_cc'):
        c = [r for r in J('gl/cc_rows.json') if r[1] < Y0]
        for br, rows in st['gl_cc'].items():
            c += [[CCBR[br], int(y), cc] + [float(x) for x in v] for y, cc, *v in rows]
        JW('gl/cc_rows.json', c); log.append('gl_cc merged')
    if need_all('gl_drcr'):
        d = {k: v for k, v in J('gl/drcr.json').items() if int(k.split('|')[1]) < Y0}
        for br, rows in st['gl_drcr'].items():
            for g, y, dr, cr in rows:
                if g in ('', 'None', 'null'): continue
                v = d.setdefault(f'{g}|{int(float(y))}', [0.0, 0.0]); v[0] += float(dr or 0); v[1] += float(cr or 0)
        JW('gl/drcr.json', {k: [round(a, 2), round(b, 2)] for k, (a, b) in d.items()}); log.append('gl_drcr merged')
    if 'exp_monthly' in st:
        for br, rows in st['exp_monthly'].items():
            p = os.path.join(ROOT, 'expdb', EXPC[br] + '_exp.txt'); acc = collections.OrderedDict()
            for l in open(p):
                l = l.strip()
                if not l: continue
                a, nm, rest = l.split('|', 2); acc[a] = [nm, {it.split(':')[0]: it for it in rest.split(',') if int('20' + it.split(':')[0]) < YM0}]
            for l in rows:
                a, nm, rest = l.split('|', 2); e = acc.setdefault(a, [nm, {}])
                for it in rest.split(','): e[1][it.split(':')[0]] = it
            open(p, 'w').write(''.join(f'{a}|{nm}|' + ','.join(v[k] for k in sorted(v)) + '\n' for a, (nm, v) in sorted(acc.items()) if v))
        log.append('exp_monthly merged')
    for job, fn in (('inv_daily', 'daily_rows.json'), ('inv_doc', 'doc_rows.json'), ('inv_cash', 'cash_rows.json')):
        if job not in st: continue
        rows = J('anomdb/' + fn); pi = 3 if job == 'inv_daily' else 1
        for br, new in st[job].items():
            rows = [r for r in rows if not (r[0] == br and int(r[pi]) >= M0)]
            if job == 'inv_daily': rows += [[br, pt, sp, ym, dl] for pt, sp, ym, dl in new]
            elif job == 'inv_doc': rows += [[br, ym, pt, did, sp, n1, n2, nd] for ym, pt, did, sp, n1, n2, nd in new]
            else: rows += [[br] + r for r in new]
        JW('anomdb/' + fn, rows); log.append(f'{job}: months >= {M0} replaced for {sorted(st[job])}')
    # Deep Analysis: monthly ledger by account/cc/function (also the source of DATA.m) and department revenue/cost
    if need_all('gl_mon'):
        g = [r for r in J('drv/gl_all.json') if int(r[4]) < YM0]
        for br, rows in st['gl_mon'].items():
            g += [[br, a, cc, f, '20' + ym, float(v)] for a, cc, f, ym, v in rows]
        JW('drv/gl_all.json', g)
        agg = collections.defaultdict(float)
        for br, a, cc, f, ym, v in g: agg[(a, cc, ym)] += v
        open(os.path.join(ROOT, 'drv/m_po.txt'), 'w').write(''.join(f'{a}|{cc}|{ym}|{round(v, 2)}\n' for (a, cc, ym), v in sorted(agg.items()) if abs(v) >= 0.005))
        log.append(f'gl_mon: months >= {YM0} replaced (drv/gl_all.json, drv/m_po.txt)')
    if need_all('cc_mon'):
        c = J('drv/cc_all.json')
        for br, rows in st['cc_mon'].items():
            c[br] = [r for r in c.get(br, []) if int('20' + r[0]) < YM0] + rows
        JW('drv/cc_all.json', c); log.append(f'cc_mon: months >= {YM0} replaced')
    if 'inv_vis' in st:
        v = J('drv/vis_all.json')
        for br, rows in st['inv_vis'].items():
            v = [r for r in v if not (r[0] == br and int('20' + r[1]) >= M0)] + [[br] + r for r in rows]
        JW('drv/vis_all.json', v); log.append(f'inv_vis: months >= {M0} replaced for {sorted(st["inv_vis"])}')
    if need_all('zak_lines'):
        z = [r for r in J('zak/lines.json') if r[1] < str(W['ledger'])]
        for br, rows in st['zak_lines'].items():
            z += [[br, d, v, a, s_, float(amt), ds] for d, v, a, s_, amt, ds in rows]
        JW('zak/lines.json', sorted(z, key=lambda r: (r[1], r[2]))); log.append('zak_lines: lines from ' + str(W['ledger']) + ' replaced')
    # weekly top-N lists: full replacement per branch
    for job, fn in (('inv_price', 'price_rows.json'), ('inv_dup', 'dup_rows.json'), ('inv_disc', 'disc_rows.json')):
        if job in st:
            d = J('anomdb/' + fn); d.update(st[job]); JW('anomdb/' + fn, d); log.append(job + ' replaced')
    if 'inv_exc' in st:
        rows = [r for r in J('anomdb/exc_rows.json') if r[0] not in st['inv_exc']]
        for br, new in st['inv_exc'].items(): rows += [[br] + r for r in new]
        JW('anomdb/exc_rows.json', rows); log.append('inv_exc replaced')
    for job, suf in (('exp_flagsS', '_flag.txt'), ('exp_flagsL', '_lines.txt')):
        if job in st:
            for br, rows in st[job].items():
                open(os.path.join(ROOT, 'expdb', EXPC[br] + suf), 'w').write('\n'.join(r[1:] for r in rows) + '\n')
            log.append(job + ' replaced')
    # audit payload is its own cache
    A = J('aud/data_aud_db.json'); ch = False
    if need_all('aud_ctrl'):
        A['ctrl'] = [r for r in A['ctrl'] if r[2] < YM0]
        for br, rows in st['aud_ctrl'].items(): A['ctrl'] += [[br, a, int(ym), round(float(n), 2)] for a, ym, n in rows]
        ch = True
    if need_all('aud_vatgl') and need_all('aud_invm'):
        A['vat'] = [r for r in A['vat'] if r[1] < YM0]
        for br in BR:
            G = {ym: [float(hs), float(inn), float(ar)] for ym, hs, inn, ar in st['aud_vatgl'][br]}
            I = {ym: float(n) for ym, n in st['aud_invm'][br]}
            for ym in sorted(set(G) | set(I)):
                hs, inn, ar = G.get(ym, [0, 0, 0]); iv = I.get(ym, 0.0)
                A['vat'].append([br, int(ym), round(hs + inn, 2), round(iv + inn, 2), round(ar, 2)])
        A['vat'].sort(key=lambda r: (r[0], r[1])); ch = True
    if need_all('aud_uj'):
        A['uj'] = [r for r in A['uj'] if r[2] < str(W['ledger'])]
        for br, rows in st['aud_uj'].items(): A['uj'] += [[br, v, d, vt, ss, u, ds, round(float(a), 2), int(nl)] for v, d, vt, ss, u, ds, a, nl in rows]
        A['uj'].sort(key=lambda r: (r[2], r[1])); ch = True
    if need_all('aud_vchk'):
        A['vchk'] = [r for r in A['vchk'] if r[1] < str(W['ledger'])]
        for br, rows in st['aud_vchk'].items(): A['vchk'] += [[v, d, round(float(a), 2), round(float(b), 2), ds, s] for v, d, a, b, ds, s in rows]
        A['vchk'].sort(key=lambda r: r[1]); ch = True
    if ch:
        A['asOf'] = P['asof']; JW('aud/data_aud_db.json', A); log.append('audit payload merged')
    return P, st, log

# ----------------------------------------------------------------------------- build + validate + patch
def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=os.path.join(ROOT, cwd), shell=True, capture_output=True, text=True)
    if r.returncode: raise SystemExit(f'{cmd} failed:\n{r.stdout}\n{r.stderr}')
    return r.stdout.strip().split('\n')[-1]

def patch(h, key, obj):
    L = h.split('\n'); pre = 'DATA.' + key + ' = '
    for i, l in enumerate(L):
        if l.startswith(pre):
            L[i] = pre + (obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, separators=(',', ':'))) + ';'
            return '\n'.join(L)
    raise SystemExit('payload line not found: ' + pre)

def build():
    rid = cur_run(); P, st, log = merge_all(rid); asof = P['asof']
    YW0 = int(P['win']['ledger'][:7].replace('-', ''))
    out = [f'# Build {os.path.basename(rid)}', ''] + ['- ' + x for x in log]
    shutil.copy(HTML, os.path.join(rid, 'before.html'))
    out.append('- ext: ' + run('python3 build_ext_gl.py', 'gl'))
    out.append('- cfa: ' + run('python3 build_cfa_gl.py', 'gl'))
    out.append('- dept/cc: ' + run('python3 build_dept_cc.py', 'gl'))
    out.append('- anom: ' + run('python3 build_anom_db.py', 'anomdb'))
    out.append('- exp: ' + run('python3 build_exp_db.py', 'expdb'))
    ad = (dt.date.fromisoformat(asof) - dt.timedelta(days=1)).isoformat()   # figures are complete through the day before the run
    out.append('- drv: ' + run(f'DRV_ASOF={ad} python3 build_drv.py', 'drv'))
    rm = subprocess.run(f"python3 {os.path.join(KIT, '..', 'scripts', 'build_monthly_buckets.py')} m_po.txt --closed={P['win']['ledger'][:7]} --write",
                        cwd=os.path.join(ROOT, 'drv'), shell=True, capture_output=True, text=True)
    if rm.returncode: raise SystemExit('build_monthly_buckets failed:\n' + rm.stdout + rm.stderr)
    vline = [l for l in rm.stdout.split('\n') if l.startswith('VERDICT')]
    out.append('- m: ' + (vline[0] if vline else 'no verdict'))
    E = J('gl/data_ext_gl.json'); h = open(HTML, encoding='utf-8').read()
    full = all(j in st and len(st[j]) == 4 for j, v in JOBS.items() if v[0] == 'A')
    old_asof = json.loads(re.search(r'\nDATA\.ext = (.*);\n', h).group(1)).get('asOf')
    E['asOf'] = asof if full else old_asof
    if not full: out.append('- partial run: date stamps left at ' + str(old_asof))
    # validation gates
    bad = []
    for i, y in enumerate(E['years']):
        d = E['bs']['total_assets'][i] - E['bs']['total_liab_eq'][i]
        if abs(d) > 1: bad.append(f'balance sheet {y} does not balance by {d:,.2f}')
    old = json.loads(re.search(r'\nDATA\.ext = (.*);\n', h).group(1))
    for i, y in enumerate(E['years']):
        if y < dt.date.fromisoformat(P['win']['ledger']).year:
            for k in ('total_revenue', 'net_income'):
                a, b = old['is_'][k][i], E['is_'][k][i]
                if abs(a - b) > 1: bad.append(f'closed year {y} {k} moved {a:,.0f} -> {b:,.0f} (posting into a closed year?)')
    A = J('anomdb/data_anom_db.json')
    names = set(n for r in A['doc'] for n in [r[3]] if re.fullmatch(r'\d+', str(n)))
    if names: bad.append('doctor ids without a name (add to anomdb/doc_names_extra.json): ' + ', '.join(sorted(names)))
    if not vline or 'REPRODUCED' not in vline[0]: bad.append('DATA.m: closed months moved — ' + (vline[0] if vline else 'no verdict') + ' (see build_monthly_buckets output)')
    Dv = J('drv/data_drv.json'); dn = sorted(set(r[3] for r in Dv['vis'] if re.fullmatch(r'\d+', str(r[3]))))
    if dn: bad.append('drivers: doctor ids without a name: ' + ', '.join(dn[:20]))
    out += ['', '## Checks', ''] + (['- ' + b for b in bad] or ['- all gates passed'])
    out += ['- reminder: re-read the Anomalies & Risks flags (DATA.data_quality_flags) — they describe the previous read']
    # patch payloads
    E['bs'] = {k: v for k, v in E['bs'].items() if not k.startswith('_')}
    C = J('gl/data_cfa_gl.json')
    # direct method (voucher level) + indirect with non-cash entries removed (IAS 7.43): dmv/build_cfd.py
    if os.path.exists(os.path.join(ROOT, 'dmv', 'build_cfd.py')):
        try:
            out.append('- cfd: ' + run('python3 build_cfd.py', 'dmv').split('\n')[0])
            C = J('gl/data_cfa_fixed.json')
        except SystemExit as e:
            if full: raise
            out.append('- cfd: SKIPPED in a partial run (voucher-level cash feed not refreshed; direct-method cash flow stays at the previous read) — ' + str(e).strip().split('\n')[-1])
    if 'gl_open' in st and len(st['gl_open']) == 4:
        ACC = J('gl/accounts.json'); par = lambda a: ACC.get(a, ('-', '?'))[0]
        iscash = lambda a: par(a) == '1210000' or par(a).startswith('122') or par(a) == '1210004'
        by = {}
        for br, rows in st['gl_open'].items():
            n = next(int(float(r[1])) for r in rows if r[0] == 'N')
            by[{'01': 'Riyadh', '02': 'Buraydah 1', '03': 'Buraydah 2', '04': 'Rafha'}[br]] = [n, round(sum(float(r[2]) for r in rows if r[0] != 'N' and iscash(r[0])), 2)]
        C['open_vouchers'] = {'asOf': asof, 'by': by, 'n': sum(v[0] for v in by.values()), 'cash': round(sum(v[1] for v in by.values()), 2)}
    else:   # carry the last read forward
        oc = json.loads(re.search(r'\nDATA\.cfa = (.*);\n', h).group(1))
        if 'open_vouchers' in oc: C['open_vouchers'] = oc['open_vouchers']
    if 'vat_tb' in st and 'vat_adj' in st and len(st['vat_tb']) == 4 and len(st['vat_adj']) == 4:
        Vr = json.loads(re.search(r'\nDATA\.vatr = (.*);\n', h).group(1)); cut = str(YW0)
        for br in BR:
            T = Vr['tb'].setdefault(br, {})
            for a in T:
                for ym in [k for k in T[a] if k >= cut]: del T[a][ym]
            for l in st['vat_tb'][br]:
                a, rest = l.split('|', 1)
                for it in rest.split(','):
                    ym, dr, cr = it.split(':'); T.setdefault(a, {})['20' + ym] = [float(dr), float(cr)]
            A2 = Vr['adj'].setdefault(br, {})
            for ym in [k for k in A2 if k >= cut]: del A2[ym]
            for l in st['vat_adj'][br]:
                ym, k, dr, cr = l.split(';'); A2.setdefault('20' + ym, {})[k] = round(float(cr if k == 'INV' else dr), 2)
        if 'vat_ret' in st and len(st['vat_ret']) == 4:
            # return lines from the MV (box formulas as kit/scripts/build_vat.py). Sept-2026 sales boxes 1-5 are the summary-invoice composition: keep them, refresh only purchase boxes 6/9/10.
            for br in BR:
                Rt = Vr['ret'].setdefault(br, {}); fresh = {}
                for l in st['vat_ret'][br]:
                    ym, ln, tt, amt, vat, v15, cnt = l.split(';')
                    if not ln or ym < cut: continue
                    ln = int(ln); amt = float(amt); vat = float(vat); v15 = float(v15)
                    d = fresh.setdefault(ym, {}).setdefault(ln, [0.0, 0.0, 0.0])
                    if ln <= 5:
                        if tt == 'SI': d[0] += amt - vat
                        else:
                            d[0] -= amt + vat
                            if tt == 'CN': d[2] += amt + vat
                        d[1] += vat
                    elif ln == 6:
                        d[0] += (amt - vat) if tt == 'PI' else v15
                        d[1] += vat
                    else:
                        d[0] += amt if tt == 'PI' else -amt
                        d[1] += vat
                for ym in [k for k in Rt if k >= cut and k != '202609']: del Rt[ym]
                for ym, D in fresh.items():
                    if ym == '202609':
                        T9 = Rt.setdefault(ym, {})
                        for k in [k for k in T9 if int(k) >= 6]: del T9[k]
                        for ln, v in D.items():
                            if ln >= 6: T9[str(ln)] = [round(x, 2) for x in v]
                    else:
                        Rt[ym] = {str(ln): [round(x, 2) for x in v] for ln, v in D.items()}
            out.append('- vatr: return (MV) lines replaced from ' + cut + ' (Sept-26 sales boxes kept as summary-invoice composition)')
        h = patch(h, 'vatr', Vr); out.append('- vatr: trial balance and adjustments replaced from ' + cut)
        if 'vat_cls' in st and len(st['vat_cls']) == 4:
            for br in BR:
                fresh = {}
                for l in st['vat_cls'][br]:
                    ym, ln, tt, amt, vat = l.split(';'); amt = float(amt); vat = float(vat)
                    d = fresh.setdefault(ym, {}).setdefault(str(int(float(ln))), [0.0, 0.0])
                    d[0] += (amt - vat) if tt == 'SI' else -(amt + vat); d[1] += vat
                Vr.setdefault('cls', {})[br] = {ym: {k: [round(x, 2) for x in v] for k, v in D.items()} for ym, D in fresh.items()}
            out.append('- vatr.cls: patient share of return sales boxes replaced')
        if all(k in st and len(st[k]) == 4 for k in ('vat_pin_mv', 'vat_pin_gl', 'vat_pin_nm')) and re.search(r'^DATA\.vatpin = ', h, flags=re.M):
            # input-VAT detail for the PDF/Excel export on the VAT tab: return purchase lines vs entries on 1263000 (closing entries dropped)
            PN = {'nm': {}, 'mv': {}, 'gl': {}}
            for br in BR:
                for r in st['vat_pin_nm'][br]:
                    if len(r) >= 2: PN['nm'][r[0]] = '|'.join(r[1:])
                PN['mv'][br] = [[r[0], r[1], r[2], r[3], r[4], r[5], float(r[6]), float(r[7])] for r in st['vat_pin_mv'][br] if len(r) == 8]
                PN['gl'][br] = [[r[0], r[1], r[2], r[3], float(r[4]), float(r[5]), r[6]] for r in st['vat_pin_gl'][br]
                                if len(r) == 7 and 'اقفال ضريبة' not in r[6] and 'قفال الحسابات الختامية' not in r[6]]
            h = patch(h, 'vatpin', PN); out.append('- vatpin: input-VAT detail replaced (' + ', '.join(br + ' mv ' + str(len(PN['mv'][br])) + ' gl ' + str(len(PN['gl'][br])) for br in BR) + ')')
    if 'is_mon' in st and len(st['is_mon']) == 4 and re.search(r'^DATA\.ism = ', h, flags=re.M):
        ISM = {}
        for br in BR:
            for r in st['is_mon'][br]:
                if len(r) == 4:
                    d = ISM.setdefault(r[0], {k: [0.0] * 12 for k in ('cash', 'cred', 'oth', 'COR', 'GA', 'INS', 'HO', 'zak', 'dep')})
                    if r[2] in d: d[r[2]][int(r[1]) - 1] = round(d[r[2]][int(r[1]) - 1] + float(r[3]), 2)
        h = patch(h, 'ism', ISM); out.append('- ism: monthly income statement replaced (' + str(len(ISM)) + ' years)')
    if 'yec' in st and len(st['yec']) == 4 and re.search(r'^DATA\.yec = ', h, flags=re.M):
        YE = {}
        for l in st['yec']['01']:   # accrual vouchers exist in the Riyadh GL only
            r = l.split(';')
            if len(r) == 5: YE[(int(r[0]), r[1], r[2], r[3])] = round(YE.get((int(r[0]), r[1], r[2], r[3]), 0) + float(r[4]), 2)
        h = re.sub(r'^DATA\.yec = .*;$', lambda m_: 'DATA.yec = ' + json.dumps([[k[0], k[1], k[2], k[3], v] for k, v in sorted(YE.items())], separators=(',', ':')) + ';', h, count=1, flags=re.M)
        out.append('- yec: year-end provisions replaced (' + str(len(YE)) + ' rows)')
    if 'cn' in st and len(st['cn']) == 4 and 'cn_nm' in st and re.search(r'^DATA\.cn = ', h, flags=re.M):
        CN = {'rows': [], 'nm': {}, 'gp': {}}
        for i_, b_ in enumerate(('01', '02', '03', '04')):
            for r in st['cn'][b_]:
                if len(r) == 9: CN['rows'].append([i_, r[0], r[1], int(r[2]), r[3], float(r[4]), float(r[5]), r[6], r[7], '' if r[8] == '-' else r[8]])
            for l in st['cn_nm'].get(b_, []):
                k_, no_, name_ = l.split(';', 2); (CN['gp'] if k_ == 'G' else CN['nm']).setdefault(no_, name_.strip())
        h = patch(h, 'cn', CN); out.append('- cn: customer credit notes replaced (' + str(len(CN['rows'])) + ' notes)')
    if 'lease_chk' in st and len(st['lease_chk']) == 4 and re.search(r'^DATA\.lease = ', h, flags=re.M):
        LC = [l.split(';') for l in st['lease_chk']['01']]; LD = json.loads(re.search(r'^DATA\.lease = (.*);$', h, flags=re.M).group(1)); today = str(dt.date.today())
        g = lambda k: [r for r in LC if r[0] == k]
        def setrc(fid, s, en, ar):
            for f in LD['findings']:
                if f['id'] == fid:
                    _ov = (f.get('rc') or {}).get('s'); f['rc'] = {'s': s, 'en': en, 'ar': ar, 'd': today}
                    if fid == 'F12': f['status'] = 'resolved' if s == 'resolved' else 'open'
                    if _ov and _ov != s: out.append('- lease finding ' + fid + ': ' + _ov + ' -> ' + s)
        for f in LD['findings']:
            if f.get('rc') and f['rc']['s'] != 'resolved' and f['id'] not in ('F02', 'F12', 'F15', 'F22', 'F24', 'F29'):
                f['rc']['d'] = today; f['rc']['en'] = 'Not testable from data (register / historical / method) - carried forward. ' + f['rc']['en'].split(' - carried forward. ')[-1]
        if g('LEGOP'): v = float(g('LEGOP')[0][1]); setrc('F12', 'resolved' if abs(v) < 100000 else 'open', 'Opening 2123001 = %s' % format(v, ',.2f'), 'رصيد 2123001 الافتتاحي = %s' % format(v, ',.2f'))
        if g('CC'):
            bad = [r for r in g('CC') if r[2] == '4300003' and r[3] == '000/000']
            setrc('F02', 'open' if bad else 'resolved', '4300003 legs still on cost centre 000: ' + ', '.join(r[1] for r in bad) if bad else 'Reversal cost centres now match the invoices', 'طرف الإيراد على 000: ' + ', '.join(r[1] for r in bad) if bad else 'مراكز التكلفة متطابقة')
        if g('D09'):
            posted = [r for r in g('D09') if r[2] == 'P' and abs(float(r[3]) - 75000) < 1]
            anyr = [r for r in g('D09') if abs(float(r[3]) - 75000) < 1]
            setrc('F15', 'resolved' if posted else ('partial' if anyr else 'open'), ('Posted: ' + posted[0][1]) if posted else (('Recorded but not posted: ' + anyr[0][1] + ' (status ' + anyr[0][2] + ')') if anyr else 'Instalment 75,000 still unrecorded'), 'القسط 75,000: ' + ('مرحّل' if posted else ('مسجل ولم يُرحَّل' if anyr else 'غير مسجل')))
        mm = {r[1] for r in g('D11')}; need = [m for m in ('202607', '202608', '202609') if m not in mm]
        setrc('F24', 'resolved' if not need else 'open', 'Warehouse accrual missing for ' + ', '.join(need) if need else 'Warehouse accrual booked for Jul-Sep 2026', 'استحقاق المستودع ناقص لشهور: ' + ', '.join(need) if need else 'تم تسجيل الاستحقاق')
        if g('S0290'): v = float(g('S0290')[0][1]); setrc('F22', 'resolved' if abs(v) < 0.5 else 'open', 'S0290 balance = %s' % format(v, ',.2f'), 'رصيد S0290 = %s' % format(v, ',.2f'))
        if g('DOC'):
            n = int(float(g('DOC')[0][1])); tot = len(json.load(open(os.path.join(ROOT, 'kit', 'sql', 'lease_vlist.json'), encoding='utf-8')))
            setrc('F29', 'resolved' if n >= tot else 'partial', '%d of %d in-scope vouchers have attachments (%d missing)' % (n, tot, tot - n), '%d من %d قيداً بمرفقات' % (n, tot))
        if LD.get('je'):   # correcting entries J01-J12 / E1-E5 (basis 30/09/2026 in DATA.lease.je): record live ledger figures and which entries are already done
            Q = LD['je']; live = {'d': today}
            for k, key, sg in (('L1252', 'a1252000', 1), ('L4300003', 'a4300003', -1), ('L3230000', 'a3230000', 1), ('O2123', 'o2123', 1)):
                if g(k): live[key] = round(sg * float(g(k)[0][1]), 2)
            if g('LEG'): live['a2123001_P'] = round(float(g('LEG')[0][1]), 2)
            if g('S0290'): live['s0290'] = round(-float(g('S0290')[0][1]), 2)
            jv = {r[1]: r[2] for r in g('JVST')}; Q['live'] = live
            done = {}
            if jv.get('JV1-26/02853') == 'P': done['J10'] = done['E3'] = 'JV1-26/02853 posted'
            if jv.get('JV1-26/02909') == 'P': done['E2'] = 'JV1-26/02909 posted'
            if not need: done['J11'] = 'warehouse accrual booked Jul-Sep'
            if g('S0290') and abs(float(g('S0290')[0][1])) < 0.5: done['J12'] = 'S0290 nil'
            if g('CC') and not [r for r in g('CC') if r[2] == '4300003' and r[3] == '000/000']: done['E1'] = 'cost centres corrected'
            if g('LEGOP') and abs(float(g('LEGOP')[0][1])) < 0.5: done['J01'] = 'legacy balance cleared'
            for j in Q['je'] + Q['ev']:
                _ol = j.get('live'); j['live'] = done.get(j['id'])
                if j['live'] and not _ol: out.append('- lease entry ' + j['id'] + ' now done in Cure: ' + j['live'])
            try:   # roll the adjustments forward to the latest closed month-end from live ledger figures (kit/scripts/lease_roll.py)
                import sys as _s; _s.path.insert(0, os.path.join(ROOT, 'kit', 'scripts')); import lease_roll
                lv = dict(live); lv['d11'] = sorted(mm); lv['chair_posted'] = jv.get('JV1-26/02853') == 'P'
                if 'a2123001_P' in lv and 'a1252000' in lv:
                    RR = lease_roll.roll(LD, lv, dt.date.fromisoformat(asof).replace(day=1) - dt.timedelta(days=1))
                    out.append('- lease roll-forward to %s: 2123001 ledger %s vs expected %s, unexplained residual %s' % (RR['asof'], format(RR['ledger_2123001'], ',.2f'), format(RR['expected_liability'], ',.2f'), format(RR['residual'], ',.2f')))
            except Exception as _e: out.append('- lease roll-forward skipped: ' + str(_e))
            out.append('- lease entries: ' + str(len(done)) + ' of ' + str(len(Q['je']) + len(Q['ev'])) + ' already reflected in Cure (amounts remain on the 30/09/2026 basis; rerun kit/scripts/lease_je.py for a new basis)')
        LD['rechecked'] = today; LD['kpi']['n_find'] = sum(1 for f in LD['findings'] if f['status'] == 'open')
        h = patch(h, 'lease', LD); out.append('- lease: findings re-checked on live data (' + today + ')')
    h = patch(h, 'ext', E); h = patch(h, 'cfa', C)
    if os.path.exists(os.path.join(ROOT, 'dmv', 'data_cfd.json')):
        h = patch(h, 'cfd', open(os.path.join(ROOT, 'dmv', 'data_cfd.json'), encoding='utf-8').read())
    h = patch(h, 'dept', J('gl/data_dept.json')); h = patch(h, 'cc', J('gl/data_cc.json'))
    h = patch(h, 'aud', J('aud/data_aud_db.json')); h = patch(h, 'anom', A); h = patch(h, 'exp', J('expdb/data_exp.json'))
    h = patch(h, 'drv', J('drv/data_drv.json')); h = patch(h, 'm', J('drv/data_m_new.json'))
    # top-level trend / bs_trend / ratios from the ledger statements
    m = re.search(r'\nconst DATA = (.*);\n', h); D = json.loads(m.group(1)); Y = E['years']; I, B, R = E['is_'], E['bs'], E['ratios_full']
    D['trend'] = [{'year': y, 'revenue': round(I['total_revenue'][i]), 'expense': round(I['total_revenue'][i] - I['net_income'][i]),
                   'net': round(I['net_income'][i]), 'flagged': False} for i, y in enumerate(Y)]
    D['bs_trend'] = [{'year': y, 'cash': round(B['cash'][i]), 'ar': round(B['ar'][i]), 'inventory': round(B['inventory'][i]),
                      'current_assets': round(B['current_assets'][i]), 'fixed_assets': round(B['fixed_net'][i]),
                      'total_assets': round(B['total_assets'][i]), 'current_liab': round(B['current_liab'][i]),
                      'noncurrent_liab': round(B['noncurrent_liab'][i]), 'equity': round(B['equity'][i]),
                      'st_loan': round(B['st_loans'][i]), 'lt_loan': round(B['lt_loans'][i])} for i, y in enumerate(Y)]
    keys = ['current_ratio', 'quick_ratio', 'debt_to_equity', 'net_debt', 'asset_turnover', 'net_margin', 'ebitda_margin', 'roe', 'roa']
    D['ratios'] = {(f'{y} YTD (as of {E["asOf"]})' if i == len(Y) - 1 else f'FY{y}'): {k: R[k][i] for k in keys} for i, y in enumerate(Y) if y >= 2023}
    h = h[:m.start()] + '\nconst DATA = ' + json.dumps(D, ensure_ascii=False) + ';\n' + h[m.end():]
    # date stamps in notes (never inside payload lines)
    prev = old.get('asOf') or ''
    if full and prev and prev != asof:
        pd, nd = dt.date.fromisoformat(prev), dt.date.fromisoformat(asof)
        pairs = [(pd.strftime('%-d %b %Y'), nd.strftime('%-d %b %Y')), (pd.strftime('%b %-d, %Y'), nd.strftime('%b %-d, %Y'))]
        L = h.split('\n')
        for i, l in enumerate(L):
            if l.startswith('DATA.') or l.startswith('const DATA'): continue
            for a, b in pairs: l = l.replace(a, b)
            L[i] = l
        h = '\n'.join(L)
    open(HTML, 'w', encoding='utf-8').write(h)
    # IFRS 18 statement: account x cost centre x function series, posted + open, to the drivers' as-of month
    out.append('- ifrs: ' + run('python3 build_ifrs_fn.py', 'ifrs').strip()[:160])
    h = open(HTML, encoding='utf-8').read(); h = patch(h, 'ifrs', J('ifrs/data_ifrs.json'))
    open(HTML, 'w', encoding='utf-8').write(h)
    # Branches & Departments reads DATA.m / DATA.ifrs / DATA.ext just written, so it comes after them
    if 'bd_bal' in st and len(st['bd_bal']) != 4: raise SystemExit('bd_bal: all four branches are required')
    bdv = run(f'CFO_ROOT={ROOT} python3 {os.path.join(KIT, "..", "scripts", "bd", "build_bd.py")} {rid}', '.')
    out.append('- bd: ' + bdv)
    if 'FAILED' in bdv: bad.append('Branches & Departments: ' + bdv)
    h = open(HTML, encoding='utf-8').read(); h = patch(h, 'bd', open(os.path.join(rid, 'data_bd.json'), encoding='utf-8').read())
    open(HTML, 'w', encoding='utf-8').write(h)
    # Normalization: the vouchers listed in Normalization.xlsx (job norm) -> DATA.norm (the switch in the global bar subtracts them at load time)
    if 'norm' in st and len(st['norm']) == 4 and os.path.exists(os.path.join(ROOT, 'norm', 'vouchers.json')):
        nv = run(f'CFO_ROOT={ROOT} python3 {os.path.join(KIT, "..", "scripts", "norm", "build_norm.py")} {rid}', '.')
        out.append('- ' + nv)
        h = open(HTML, encoding='utf-8').read(); nl = 'DATA.norm = ' + open(os.path.join(rid, 'data_norm.json'), encoding='utf-8').read().strip() + ';'
        if '\nDATA.norm = ' in h: h = re.sub(r'\nDATA\.norm = .*;\n', lambda _: '\n' + nl + '\n', h, count=1)
        else:
            i = h.index('\nDATA.bd = '); j = h.index('\n', i + 1); h = h[:j + 1] + nl + '\n' + h[j + 1:]
        open(HTML, 'w', encoding='utf-8').write(h)
        if os.path.exists(os.path.join(ROOT, 'norm', 'apply_ui.py')): run(f'DESK={HTML} python3 {os.path.join(ROOT, "norm", "apply_ui.py")}', '.')
    else: out.append('- norm: not staged for all four branches — DATA.norm left as it was')
    # Zakat reads the statements and drivers just written, so it is built last
    out.append('- zak: ' + run('python3 build_zakat.py', 'zak').strip()[:160])
    h = open(HTML, encoding='utf-8').read(); h = patch(h, 'zak', J('zak/data_zak.json'))
    open(HTML, 'w', encoding='utf-8').write(h)
    open(os.path.join(rid, 'build.md'), 'w').write('\n'.join(out) + '\n'); print('\n'.join(out))
    if bad: print('\nREVIEW the checks above before publishing.')

CACHE_DIRS = ['gl', 'drv', 'anomdb', 'expdb', 'aud', 'zak', 'ifrs', 'dmv', 'norm', 'arx', 'nph']
SETUP = {   # kit file -> dir under ROOT (copied; existing cache files are never overwritten)
    'gl': ['scripts/pk.py', 'scripts/parse.py', 'scripts/unpack.py', 'scripts/lastres.py', 'scripts/build_ext_gl.py', 'scripts/build_cfa_gl.py', 'scripts/build_dept_cc.py'],
    'anomdb': ['scripts/build_anom_db.py', ('scripts/sql_invoice_aggregates.py', 'gen.py'), ('scripts/sql_invoice_exceptions.py', 'gen2.py')],
    'expdb': ['scripts/build_exp_db.py'],
    'ifrs': ['scripts/build_ifrs_fn.py'],
    'aud': ['scripts/build_aud_db.py'],
    'drv': ['scripts/drv/build_drv.py', 'scripts/drv/gen.py'],
    'zak': ['scripts/zak/build_zakat.py', 'scripts/zak/exp_class.json', 'scripts/zak/lines.json'],
    'dmv': ['scripts/dmv/build_cfd.py', 'scripts/dmv/build_dm.py', 'scripts/dmv/parse.py', 'scripts/dmv/noncash.py', 'scripts/dmv/bsline.py'],
    'norm': ['scripts/norm/build_norm.py', 'norm/apply_ui.py', 'norm/xlsx_to_json.py'],
    'bd': ['bd/patch.py'], 'hl': ['hl/apply_hl.py'], 'arx': ['scripts/arx/build_arx.py', 'scripts/arx/build_ar_xlsx.py', 'scripts/arx/patch.py'],
}
SQLMAP = {'gl/cc.sql': 'sql/gl_costcentre_annual.sql', 'gl/drcr.sql': 'sql/gl_drcr_groups.sql', 'aud/ctrl.sql': 'sql/ctrl.sql', 'aud/vat_gl.sql': 'sql/vat_gl.sql',
          'aud/inv_month.sql': 'sql/inv_month.sql', 'aud/uj.sql': 'sql/uj.sql', 'aud/vchk.sql': 'sql/vchk.sql', 'expdb/flags_R.sql': 'sql/expense_redflags_riyadh_expanded.sql'}
def setup():
    link = os.path.join(ROOT, 'kit')
    if not os.path.lexists(link): os.symlink(os.path.dirname(KIT), link)
    n = 0
    for d, files in SETUP.items():
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        for f in files:
            src, dst = (f, os.path.basename(f)) if isinstance(f, str) else f
            sp = os.path.join(os.path.dirname(KIT), src); dp = os.path.join(ROOT, d, dst)
            if os.path.exists(sp): shutil.copy(sp, dp); n += 1
            else: print('  kit file missing:', src)
    for d, sq in SQLMAP.items():
        sp = os.path.join(os.path.dirname(KIT), sq)
        if os.path.exists(sp): shutil.copy(sp, os.path.join(ROOT, d)); n += 1
        else: print('  kit sql missing:', sq)
    for d in CACHE_DIRS: os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    print(f'setup: {n} scripts placed under {ROOT}; kit symlink -> {os.path.dirname(KIT)}')

def pack():
    out = '/mnt/user-data/outputs'; os.makedirs(out, exist_ok=True)
    f = os.path.join(out, 'cfo_cache_' + dt.date.today().strftime('%Y%m%d') + '.tgz')
    items = [d for d in CACHE_DIRS if os.path.isdir(os.path.join(ROOT, d))]
    if os.path.isdir(os.path.join(ROOT, 'kit', 'refresh', 'runs')): items.append('kit/refresh/runs')     # staged results of the runs
    subprocess.check_call(['tar', 'czf', f, '-C', ROOT] + items)
    print(f, round(os.path.getsize(f) / 1e6, 1), 'MB;', 'dirs:', ' '.join(items))
    print('NEXT: SendUserFile this file, then device_commit_files it to CFO-Cure-Kit\\cache\\cfo_cache_latest.tgz (force)')

def restore(tgz):
    subprocess.check_call(['tar', 'xzf', tgz, '--keep-directory-symlink', '-C', ROOT]); print('restored', tgz, 'into', ROOT)

if __name__ == '__main__':
    a = sys.argv[1:]
    opt = lambda k: a[a.index(k) + 1] if k in a else None
    if not a: print(__doc__)
    elif a[0] == 'plan': plan(dt.date.fromisoformat(opt('--asof')) if opt('--asof') else dt.date.today(), '--weekly' in a, opt('--jobs').split(',') if opt('--jobs') else None)
    elif a[0] == 'ingest': ingest(a[1], a[2], {'file': opt('--file'), 'marker': opt('--marker'), 'append': '--append' in a})
    elif a[0] == 'status': status()
    elif a[0] == 'build': build()
    elif a[0] == 'setup': setup()
    elif a[0] == 'pack': pack()
    elif a[0] == 'restore': restore(a[1])
    else: print(__doc__)
