# -*- coding: utf-8 -*-
"""AR Audit · insurance payments (account 1240007). Builds DATA.arx from
   lines.json   GL lines of every voucher that touches 1240007 (posted + open), from Cure MCP
   created.json voucher creation / posting dates (GL_TRANSACTIONS_VIEW)
   att.json     EX_ATTACHMENTS rows of those vouchers
   manifest.json + extract/<BR>.json   what each attached document actually says (read page by page)
Scope: vouchers registered (created) in the review month; credit notes / provision entries excluded."""
import json, re, collections, datetime as dt, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
L = json.load(open('lines.json')); C = json.load(open('created.json')); A = json.load(open('att.json'))
M = json.load(open('manifest.json'))
EX = []
for b in ['RUH', 'BUR1', 'BUR2', 'RAF']: EX += json.load(open(f'extract/{b}.json'))
BR = {'الرياض': 'RUH', 'بريدة 1': 'BUR1', 'بريدة 2': 'BUR2', 'رفحاء': 'RAF'}
EXCL = {'JV1-26/02300': 'provision close', 'JV1-26/02306': 'credit note', 'JV3-26/00045': 'credit note'}
MISSING = {'CM_(BR2-26_00171)_07092026152207_917..pdf', 'CM_(BR2-26_00171)_07092026152432_917..pdf',
           'CM_(BR2-26_00171)_07092026152603_918..pdf', 'CM_(BR2-26_00172)_07092026154451_920..pdf',
           'CM_(BR2-26_00174)_08092026120301_926.pdf'}
REVIEW = '2026-09'

# ---- vouchers
V = collections.OrderedDict()
for vno, d, st, ss, acc, sub, subnm, dr, cr, ds, eu, en, br in L:
    if vno in EXCL: continue
    v = V.setdefault(vno, dict(v=vno, br=BR[br], dt=d, st=st, user=en, ar=[], bank=0.0, other=[]))
    dr = float(dr or 0); cr = float(cr or 0)
    if acc == '1240007':
        v['ar'].append(dict(sub=sub, cust=subnm.replace('\n', ' ').strip(), amt=round(cr - dr, 2), desc=ds.strip()))
    elif acc.startswith('122'): v['bank'] = round(v['bank'] + dr - cr, 2)
    else: v['other'].append(dict(acc=acc, amt=round(dr - cr, 2), desc=ds.strip()))
for k, v in V.items():
    c = C.get(k, {}); v['cd'] = c.get('cd'); v['pd'] = c.get('pd') or None
    v['kind'] = 'refund' if k[:2] == 'BP' else ('allocation' if k[:2] == 'JV' else 'receipt')
    v['amt'] = round(sum(a['amt'] for a in v['ar']), 2)
    subs = sorted({(a['sub'], a['cust']) for a in v['ar']}); v['sub'], v['cust'] = subs[0]
    v['desc'] = v['ar'][0]['desc']
    v['att'] = [dict(file=f.split('\\')[-1], label=ds, date=dd) for vv, t, f, ds, dd, img, b in A if vv == k]

# ---- documents
man = {m['dst']: m for m in M}
docs = collections.defaultdict(list); verdict = {}
for e in EX:
    if e.get('kind') == 'voucher_verdict': verdict[e['voucher']] = e; continue
    docs[e['voucher']].append(e)
for m in M:  # attachments whose file is not on the server
    if m['src'].split('\\')[-1] in MISSING and m['voucher'] in V:
        if not any(d.get('file') == m['dst'] for d in docs[m['voucher']]):
            docs[m['voucher']].append(dict(voucher=m['voucher'], file=m['dst'], kind='missing', label=m['desc']))

def mon(s):
    return s[:7] if s else None

# duplicate transfers: same bank reference + same amount booked by two receipts in the same ledger
tref = collections.defaultdict(list)
for k, ds in docs.items():
    for d in ds:
        if d.get('kind') == 'transfer' and d.get('transfer_ref') and d.get('direction') != 'outgoing':
            tref[(V[k]['br'], d['transfer_ref'].strip(), round(d.get('amount') or 0, 2))].append(k)
DUP = {}
for key, ks in tref.items():
    ks = sorted(set(k for k in ks if V[k]['kind'] == 'receipt'))
    if len(ks) > 1:
        for k in ks: DUP[k] = [x for x in ks if x != k]

ISS = [  # (code, severity, regex on the reviewer's issue text)
    ('dup', 3, r'DUPLICATE'),
    ('subacct', 3, r'WRONG SUB-ACCOUNT'),
    ('broken', 3, r'missing on disk'),
    ('noproof', 3, r'No outgoing transfer / refund proof'),
    ('untraced', 3, r'exceeds the attached|cannot be traced'),
    ('pct', 2, r'75%'),
    ('nosupport', 2, r'No (claim|clinic claim|reconciliation|settlement)|no remittance|not attached|No reconciliation'),
    ('partdoc', 2, r'only page|Only page|page \d+ of \d+ only|last page|totals page|page 2/2|page 1 missing|incomplete'),
    ('rebate', 1, r'rebate'),
    ('ref', 1, r'transfer no|transfer ref|IBAN|truncated|not unique|building number|account no\.|remitter address'),
    ('narr', 1, r'[Nn]arrative says'),
    ('twice', 1, r'attached twice|same page|same file\)|Two claim attachments are the same'),
    ('extra', 1, r'also contains refunds'),
    ('fees', 1, r'Bank charges'),
]
LBL = {
    'dup': ['حوالة واحدة مسجلة مرتين', 'Same bank transfer booked twice'],
    'subacct': ['قيد على حساب فرعي خاطئ', 'Credited to the wrong customer sub-account'],
    'broken': ['مرفق مسجل في النظام وملفه غير موجود', 'Attachment row points to a file that does not exist'],
    'noproof': ['مرفق سند الصرف ليس إثبات التحويل الصادر', 'Refund voucher attaches the incoming transfer, not the refund'],
    'untraced': ['المبلغ غير مؤيد بالمطالبة المرفقة', 'Amount not supported by the attached claim'],
    'pct': ['نسبة السداد في البيان لا تطابق الفعلي', 'Narrative percentage differs from the amount paid'],
    'nosupport': ['لا توجد مطالبة / كشف تسوية مرفق', 'No claim / settlement statement attached'],
    'partdoc': ['المطالبة المرفقة ناقصة الصفحات', 'Claim attached is incomplete (last page only)'],
    'rebate': ['خصم حجم عمل كبير من المبلغ', 'Volume rebate deducted from the payment'],
    'ref': ['رقم الحوالة في البيان ليس مرجع البنك', 'Transfer no. in narrative is not the bank reference'],
    'narr': ['البيان يذكر العناية الشاملة والسداد مباشر من الشركة', 'Narrative names the TPA; paid by insurer directly'],
    'twice': ['نفس الملف مرفق مرتين', 'Same file attached twice'],
    'extra': ['المرفق يشمل مبالغ لفروع أخرى', 'Attachment also covers other branches'],
    'fees': ['رسوم التحويل غير مقيدة', 'Transfer fees not booked'],
    'late': ['الحوالة في شهر والقيد في شهر لاحق', 'Transfer received in an earlier month than the voucher date'],
}

out = []
for k, v in V.items():
    if not v['cd'] or v['cd'][:7] != REVIEW and v['dt'][:7] != REVIEW: continue
    ds = docs.get(k, []); vr = verdict.get(k, {})
    tr = [d for d in ds if d.get('kind') in ('transfer', 'refund_proof')]
    cl = [d for d in ds if d.get('kind') in ('claim', 'remittance_advice', 'credit_note')]
    miss = [d for d in ds if d.get('kind') == 'missing']
    t0 = next((d for d in tr if d.get('kind') == 'transfer'), tr[0] if tr else {})
    issues = []
    for txt in (vr.get('issues') or []):
        hit = None
        for code, sev, rx in ISS:
            if re.search(rx, txt): hit = (code, sev); break
        issues.append(dict(code=hit[0] if hit else 'note', sev=hit[1] if hit else 1, en=txt))
    # value date vs voucher date
    vd = t0.get('value_date'); gap = None
    if vd:
        gap = (dt.date.fromisoformat(v['dt']) - dt.date.fromisoformat(vd)).days
        if v['kind'] != 'refund' and vd[:7] != v['dt'][:7] and not any(i['code'] == 'late' for i in issues):
            issues = [i for i in issues if not re.search(r'booked|recorded|dated \d|dated \d\d/', i['en']) or i['code'] not in ('note',)]
            issues.append(dict(code='late', sev=2, en=f'Bank value date {vd}, voucher dated {v["dt"]} ({gap} days later)'))
    if k in DUP and not any(i['code'] == 'dup' for i in issues):
        issues.append(dict(code='dup', sev=3, en='Same bank reference and amount also booked in ' + ', '.join(DUP[k])))
    if miss and not any(i['code'] == 'broken' for i in issues):
        issues.append(dict(code='broken', sev=3, en=f'{len(miss)} attachment(s) listed in EX_ATTACHMENTS are not on the file server'))
    # a subsequent timing note from the reviewer duplicates the computed one
    issues = [i for i in issues if not (i['code'] == 'note' and re.search(r'(booked|recorded|dated) .*\d{2}/\d{2}/\d{4}|posted ~|late\)|\(late\)', i['en']))]
    # checks
    pm = vr.get('payer_matches_customer', 'unknown')
    if any(i['code'] == 'subacct' for i in issues): pm = 'no'
    chk = {
        'att': 'bad' if miss else ('ok' if tr else 'bad'),
        'payer': {'yes': 'ok', 'partial': 'tpa', 'no': 'bad'}.get(pm, 'na'),
        'amount': {'yes': 'ok', 'part_of_transfer': 'split', 'no': 'bad'}.get(vr.get('amount_matches'), 'na'),
        'period': {'yes': 'ok', 'no': 'bad'}.get(vr.get('period_consistent'), 'na'),
        'claim': 'ok' if cl else ('na' if v['kind'] == 'refund' else 'miss'),
        'dup': 'bad' if (k in DUP or any(i['code'] == 'dup' for i in issues)) else 'ok',
        'file': {'yes': 'ok', 'no': 'bad'}.get(vr.get('right_file'), 'na'),
    }
    per_src = 'bank' if any(d.get('period_in_transfer') for d in tr) else ('hand' if any(d.get('handwritten_note') for d in tr) else 'none')
    sev = max([i['sev'] for i in issues] + [0])
    out.append(dict(
        v=k, br=v['br'], kind=v['kind'], dt=v['dt'], cd=v['cd'], pd=v['pd'], st=v['st'], user=v['user'],
        sub=v['sub'], cust=v['cust'], amt=v['amt'], bank=v['bank'], other=v['other'], desc=v['desc'],
        split=[dict(amt=a['amt'], desc=a['desc']) for a in v['ar']] if len(v['ar']) > 1 else [],
        tr=dict(date=vd, amt=t0.get('amount'), payer=t0.get('payer_name'), ref=t0.get('transfer_ref'),
                det=(t0.get('bank_details_text') or '')[:220], hand=t0.get('handwritten_note'),
                per=t0.get('period_in_transfer'), dir=t0.get('direction')) if t0 else None,
        pv=vr.get('period_voucher'), pt=vr.get('period_transfer'), pdoc=vr.get('period_docs'), psrc=per_src,
        docs=[dict(f=d.get('file'), k=d.get('kind'), ins=d.get('doc_insurer'), per=d.get('doc_period'),
                   brn=d.get('doc_branch'), paid=d.get('doc_amount_paid'), cl=d.get('doc_amount_claimed'),
                   amt=d.get('amount'), n=(d.get('notes') or '')[:400]) for d in ds],
        natt=len(v['att']), chk=chk, iss=issues, sev=sev, conf=vr.get('confidence')))

# refunds: link each BP to the duplicated receipts it follows; BP3's outgoing-transfer proof sits in BP1/BP2's attachment
for r in out:
    if r['kind'] == 'refund':
        r['iss'].append(dict(code='fees', sev=1, en='Outgoing transfer of 01/09/2026 carried bank charges 7.00 + VAT 1.05 (per the SNB advices) that are not in the voucher'))
        if r['v'] == 'BP3-26/00001':
            for i in r['iss']:
                if i['code'] == 'noproof': i['en'] += ' — the SNB outgoing-transfer advice for −35,556.67 (NCBK82426244BEBE, 01/09/2026) is on page 5 of the attachment to BP1-26/00003 / BP2-26/00001, so the refund did happen'
        r['sev'] = max(i['sev'] for i in r['iss'])
groups = []
seen = set()
for k in sorted(DUP):
    if k in seen: continue
    g = sorted([k] + DUP[k]); seen |= set(g)
    rr = [x for x in out if x['v'] in g]
    amt = rr[0]['amt']; brn = rr[0]['br']
    bp = [x['v'] for x in out if x['kind'] == 'refund' and x['br'] == brn and abs(-x['amt'] - amt) < 0.01]
    # receipts - refunds: a transfer the payer sent twice by mistake and the company returned (bank statement shows both credits) nets to nil;
    # only receipts that are NOT matched by a refund are an overstatement.
    extra = round(amt * max(0, len(g) - 1 - len(bp)), 2)
    groups.append(dict(vs=g, br=brn, amt=amt, extra=extra, settled=(extra == 0), refund=bp, ref=rr[0]['tr']['ref'] if rr[0]['tr'] else None,
                       cust=rr[0]['cust'], st=[x['st'] for x in rr]))
    if extra == 0:
        for x in rr:
            x['iss'] = [i for i in x['iss'] if i['code'] != 'dup']
            x['chk']['dup'] = 'ok'
            x['iss'].append(dict(code='note', sev=1, en=f"Paid twice at the bank on {rr[0]['dt']} (payer sent it in error); {len(g)} receipts − {len(bp)} refund ({', '.join(bp)}) = one receipt, so the books are correct. Attach the second transfer's own bank advice"))
            x['sev'] = max([i['sev'] for i in x['iss']] or [0])
out.sort(key=lambda r: (-r['sev'], r['br'], r['v']))
res = dict(asOf=dt.date.today().isoformat(), review=REVIEW, account='1240007', lbl=LBL,
           months=[REVIEW], rows=out, dups=groups,
           excluded=[dict(v=k, why=w) for k, w in EXCL.items()])
json.dump(res, open('data_arx.json', 'w'), ensure_ascii=False, separators=(',', ':'))
c = collections.Counter(r['sev'] for r in out)
print('vouchers', len(out), 'by severity', dict(c), 'bytes', os.path.getsize('data_arx.json'))
print('dup', sorted(DUP))
print(collections.Counter(i['code'] for r in out for i in r['iss']))
