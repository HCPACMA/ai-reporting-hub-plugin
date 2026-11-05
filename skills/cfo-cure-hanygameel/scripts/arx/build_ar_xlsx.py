# -*- coding: utf-8 -*-
"""AR workbook — every detail behind the two AR tabs of the Modeling Desk, generated from the same payloads
(arx/data_arx.json, nph/data_nph.json). Run after either build; patch scripts call it automatically.
Output: AR_Details.xlsx (next to the desk)."""
import json, os, datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule, FormulaRule

ROOT = os.environ.get('CFO_ROOT', '/home/claude/work')
X = json.load(open(os.path.join(ROOT, 'arx/data_arx.json'), encoding='utf-8'))
N = json.load(open(os.path.join(ROOT, 'nph/data_nph.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'AR_Details.xlsx')

F = 'Arial'
H = Font(name=F, bold=True, color='FFFFFF', size=10)
HF = PatternFill('solid', fgColor='146356')
B = Font(name=F, size=10); BB = Font(name=F, size=10, bold=True)
T = Font(name=F, size=14, bold=True, color='146356'); S = Font(name=F, size=10, italic=True, color='4B5F5A')
RED = PatternFill('solid', fgColor='FDECEA'); AMB = PatternFill('solid', fgColor='FFF4D6'); GRN = PatternFill('solid', fgColor='E3F2EA')
NUM = '#,##0.00;(#,##0.00);"-"'; INT = '#,##0;(#,##0);"-"'
BR = {'RUH': 'Riyadh', 'BUR1': 'Buraydah 1', 'BUR2': 'Buraydah 2', 'RAF': 'Rafha'}
SEV = {3: 'Exception', 2: 'Review', 1: 'Note', 0: 'Clean'}
NS = {'booked': 'Booked · right company', 'booked_other': 'Booked · other company', 'pending': 'Awaiting booking (≤60 days)',
      'unbooked': 'Not found in ledger', 'duplicate': 'Duplicate notice', 'claim_level': 'Per-claim notice (month view)'}
GS = {'matched': 'Matched to NPHIES', 'other_co': 'Matched · other company', 'no_notice': 'NPHIES payer · no notice',
      'after': "After payer's last notice", 'before': "Before payer's first notice", 'claim_level': 'Per-claim payer (month view)',
      'non_nphies': 'Payer not paying via NPHIES'}
wb = Workbook()
META = {}
def rg(sh, col):
    cols, n = META[sh]; L = get_column_letter(cols.index(col) + 1)
    return f"'{sh}'!${L}$2:${L}${max(n, 2)}"

def sheet(title, cols, rows, widths=None, money=(), ints=(), dates=(), wrap=(), rtl=(), name=None):
    ws = wb.create_sheet(title)
    ws.append([c for c in cols])
    for c in ws[1]: c.font = H; c.fill = HF; c.alignment = Alignment(vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = 30
    for r in rows: ws.append(r)
    n = len(rows) + 1
    for j, c in enumerate(cols, 1):
        L = get_column_letter(j)
        ws.column_dimensions[L].width = (widths or {}).get(c, 14)
        for i in range(2, n + 1):
            cell = ws[f'{L}{i}']; cell.font = B
            if c in money: cell.number_format = NUM
            elif c in ints: cell.number_format = INT
            elif c in dates: cell.number_format = 'dd/mm/yyyy'
            if c in wrap: cell.alignment = Alignment(wrap_text=True, vertical='top')
            elif c in rtl: cell.alignment = Alignment(horizontal='right', vertical='top', readingOrder=2)
            else: cell.alignment = Alignment(vertical='top')
    if rows:
        t = Table(displayName=name or ''.join(ch for ch in title if ch.isalnum()), ref=f'A1:{get_column_letter(len(cols))}{n}')
        t.tableStyleInfo = TableStyleInfo(name='TableStyleLight9', showRowStripes=True)
        ws.add_table(t)
    ws.freeze_panes = 'B2'
    META[title] = (cols, n)
    return ws, n

D = lambda s: dt.date.fromisoformat(s) if s else None
def fill_by(ws, col, n, mapping):
    L = col
    for i in range(2, n + 1):
        v = ws[f'{L}{i}'].value
        f = mapping.get(v)
        if f:
            for c in ws[i]: c.fill = f

# ------------------------------------------------------------------ AR Audit · Insurance Payments
rows = []
for r in X['rows']:
    t = r['tr'] or {}
    rows.append([r['v'], BR[r['br']], r['kind'], D(r['dt']), D(r['cd']), r['st'], r['sub'], r['cust'], r['amt'], r['bank'],
                 t.get('payer'), D(t.get('date')), t.get('amt'), t.get('ref'), t.get('hand'), r['pv'], r['pt'], r['pdoc'],
                 r['chk']['att'], r['chk']['payer'], r['chk']['amount'], r['chk']['period'], r['chk']['claim'], r['chk']['dup'],
                 SEV[r['sev']], len([i for i in r['iss'] if i['code'] != 'note']), r['desc'], r['user']])
cols = ['Voucher', 'Branch', 'Kind', 'Voucher date', 'Created', 'Status', 'Sub-account', 'Customer (credited)', 'Amount to 1240007',
        'Bank movement', 'Remitter on bank advice', 'Bank value date', 'Transfer amount', 'Bank reference', 'Handwritten note',
        'Month · voucher', 'Month · transfer', 'Month · claim papers', 'Chk attachment', 'Chk payer', 'Chk amount', 'Chk month',
        'Chk claim papers', 'Chk booked once', 'Result', 'Findings', 'Narrative', 'Entered by']
ws1, n1 = sheet('AR Vouchers', cols, rows, widths={'Customer (credited)': 34, 'Remitter on bank advice': 34, 'Narrative': 60, 'Bank reference': 22,
                'Handwritten note': 22, 'Month · transfer': 26, 'Month · claim papers': 20, 'Month · voucher': 16, 'Entered by': 22, 'Voucher': 15},
                money=('Amount to 1240007', 'Bank movement', 'Transfer amount'), ints=('Findings',),
                dates=('Voucher date', 'Created', 'Bank value date'), rtl=('Customer (credited)', 'Narrative'), name='ARVouchers')
fill_by(ws1, 'Y', n1, {'Exception': RED, 'Review': AMB})

rows = []
for r in X['rows']:
    for i in r['iss']:
        lb = X['lbl'].get(i['code'])
        rows.append([r['v'], BR[r['br']], r['cust'], r['amt'], {3: 'High', 2: 'Medium', 1: 'Low'}.get(i['sev'], 'Low'),
                     lb[1] if lb else 'Reviewer note', lb[0] if lb else '', i['en']])
rows.sort(key=lambda x: ({'High': 0, 'Medium': 1, 'Low': 2}[x[4]], x[0]))
ws2, n2 = sheet('AR Findings', ['Voucher', 'Branch', 'Customer', 'Amount', 'Severity', 'Finding', 'Finding (Arabic)', 'Detail'], rows,
                widths={'Customer': 34, 'Finding': 38, 'Finding (Arabic)': 34, 'Detail': 90, 'Voucher': 15}, money=('Amount',),
                wrap=('Detail',), rtl=('Customer', 'Finding (Arabic)'), name='ARFindings')
fill_by(ws2, 'E', n2, {'High': RED, 'Medium': AMB})

rows = []
for r in X['rows']:
    for d in r['docs']:
        rows.append([r['v'], BR[r['br']], d.get('f'), d.get('k'), d.get('ins'), d.get('per'), d.get('brn'), d.get('cl'), d.get('paid'), d.get('amt'), d.get('n')])
sheet('AR Documents read', ['Voucher', 'Branch', 'File', 'Kind', 'Insurer on document', 'Period on document', 'Branch on document',
      'Claimed', 'Paid', 'Amount', 'What the document says'], rows,
      widths={'File': 34, 'Insurer on document': 30, 'What the document says': 90, 'Voucher': 15}, money=('Claimed', 'Paid', 'Amount'),
      wrap=('What the document says',), name='ARDocuments')

rows = [[BR[g['br']], g['ref'], ' + '.join(g['vs']), ', '.join(g['refund']), g['cust'], g['amt'], g['extra']] for g in X['dups']]
sheet('AR Duplicate receipts', ['Branch', 'Bank reference', 'Receipted twice', 'Refunded by', 'Customer', 'Transfer amount', 'Overstated'], rows,
      widths={'Receipted twice': 30, 'Customer': 34, 'Bank reference': 22}, money=('Transfer amount', 'Overstated'), rtl=('Customer',), name='ARDuplicates')

# ------------------------------------------------------------------ Payment Via NPHIES · Rafha
I = N['ins']; SUBS = N['subs']
def insname(i):
    x = I.get(i, {})
    return x.get('en') if x.get('status') == 'named' else (x.get('carrier') or x.get('en') or i)
NR = [dict(zip(N['fields'], r)) for r in N['rows']]
GL = [dict(zip(N['glF'], g)) for g in N['gl']]

rows = []
for i, x in I.items():
    rs = [r for r in NR if r['ins'] == i]; tl = [r for r in rs if r['bs'] != 'claim_level']
    subs = [s for s, v in N['subIns'].items() if i in v]
    rows.append([i, insname(i), {'named': 'Named (customer group)', 'tpa': 'Via TPA · no group', 'unnamed': 'Name only in NPHIES message'}[x['status']],
                 x.get('via', ''), x.get('grp') or '', ' | '.join(f"{b[0]} {b[1]}" for b in (x.get('book') or [])[:3]), ', '.join(subs),
                 D((N['cover'].get(i) or [None])[0]), D((N['cover'].get(i) or [None, None])[1]), len(rs), round(sum(r['amt'] for r in rs), 2),
                 len(tl), sum(1 for r in tl if r['bs'] == 'booked'), sum(1 for r in tl if r['bs'] == 'unbooked'),
                 round(sum(r['amt'] for r in tl if r['bs'] == 'unbooked'), 2), sum(1 for r in tl if r['bs'] == 'pending'),
                 sum(1 for g in GL if g['sub'] in subs and g['st'] in ('no_notice', 'after'))])
rows.sort(key=lambda x: -x[10])
sheet('NPHIES Payers', ['NPHIES licence', 'Payer / carrier', 'Status', 'Notices issued by', 'Customer group', 'Books to (1240007)',
      'Ledger accounts compared', 'First notice', 'Last notice', 'Notices', 'Paid SAR', 'Transfer-level notices', 'Booked right co.',
      'Not found in ledger', 'Not found SAR', 'Awaiting', 'Receipts without notice'], rows,
      widths={'Payer / carrier': 38, 'Books to (1240007)': 50, 'Status': 24, 'Notices issued by': 18, 'Ledger accounts compared': 18},
      money=('Paid SAR', 'Not found SAR'), ints=('Notices', 'Transfer-level notices', 'Booked right co.', 'Not found in ledger', 'Awaiting', 'Receipts without notice'),
      dates=('First notice', 'Last notice'), rtl=('Books to (1240007)',), name='NPHPayers')

rows = []
for r in NR:
    gl = r['gl'] or [None] * 5
    rows.append([r['pk'], D(r['d']), r['ins'], insname(r['ins']), r['amt'], r['dsum'], r['fee'], r['dA'], r['clm'], r['tax'], r['dC'],
                 r['dcnt'], r['lnk'], ' + '.join(m[0] for m in r['m']), r['accs'], ' | '.join(SUBS.get(a, '') for a in (r['accs'] or '').split(',') if a),
                 NS[r['bs']], gl[0], D(gl[1]), gl[2], (SUBS.get(gl[2], '') if gl[2] else None), ('Yes' if gl[4] else 'No') if gl[0] else None,
                 gl[3], r['dupOf'], r['disp'], D(r['hd']) if r['hd'] else None])
sheet('NPHIES Notices', ['Notice no', 'Paid', 'NPHIES licence', 'Payer / carrier', 'Amount', 'Σ claim lines', 'Early-fee field', 'Δ vs lines',
      'Company net claimed', 'VAT claimed', 'Δ vs claimed', 'Claim lines', 'Linked claims', 'Service month(s)', 'Booking account(s)',
      'Booking account name', 'Ledger status', 'Ledger voucher', 'Voucher date', 'Voucher account', 'Voucher account name', 'Right company',
      'Match', 'Duplicate of', 'Payer wording', 'Header loaded'], rows,
      widths={'Payer / carrier': 34, 'Booking account name': 38, 'Ledger status': 28, 'Voucher account name': 34, 'Match': 26, 'Payer wording': 44, 'Service month(s)': 16},
      money=('Amount', 'Σ claim lines', 'Early-fee field', 'Δ vs lines', 'Company net claimed', 'VAT claimed', 'Δ vs claimed'),
      ints=('Claim lines', 'Linked claims'), dates=('Paid', 'Voucher date', 'Header loaded'), rtl=('Booking account name', 'Voucher account name'), name='NPHNotices')
ws = wb['NPHIES Notices']; fill_by(ws, 'Q', len(rows) + 1, {NS['unbooked']: RED, NS['booked_other']: RED, NS['pending']: AMB, NS['duplicate']: AMB})

rows = []
for g in GL:
    m = g['m'] or {}
    rows.append([g['v'], D(g['d']), g['sub'], SUBS.get(g['sub'], ''), g['amt'], GS[g['st']], g['nm'] or None,
                 ', '.join('#' + str(p) for p in m.get('pks', [])) or None, m.get('kind'), insname(m['ins']) if m.get('ins') else None,
                 ' + '.join(m.get('sm', [])) or None, {1: 'Same', 0: 'Different'}.get(m.get('mok')) if m else None, g['desc'], g['user']])
sheet('Ledger Receipts', ['Voucher', 'Dated', 'Account', 'Account name', 'Amount', 'Status', 'Month in narrative', 'NPHIES notice(s)',
      'Match', 'Payer', 'Service month', 'Narrative vs service month', 'Narrative', 'Entered by'], rows,
      widths={'Account name': 38, 'Status': 28, 'NPHIES notice(s)': 20, 'Match': 26, 'Payer': 30, 'Narrative': 60, 'Voucher': 15},
      money=('Amount',), dates=('Dated',), rtl=('Account name', 'Narrative'), name='LedgerReceipts')
ws = wb['Ledger Receipts']; fill_by(ws, 'F', len(rows) + 1, {GS['no_notice']: RED, GS['other_co']: RED, GS['after']: AMB})

# payer x month: NPHIES vs ledger
M = {}
for r in NR:
    k = (r['ins'], r['d'][:7]); o = M.setdefault(k, [0, 0, 0, 0]); o[1 if r['bs'] == 'claim_level' else 0] += r['amt']
for g in GL:
    for i in N['subIns'].get(g['sub'], []):
        o = M.setdefault((i, g['d'][:7]), [0, 0, 0, 0]); o[2] += g['amt']
        if g['m'] and g['m']['ins'] == i: o[3] += g['amt']
rows = [[i, insname(i), ym, round(o[0], 2), round(o[1], 2), round(o[2], 2), round(o[3], 2), None] for (i, ym), o in sorted(M.items(), key=lambda x: (insname(x[0][0]), x[0][1]))]
ws, n = sheet('NPHIES vs Ledger by month', ['NPHIES licence', 'Payer / carrier', 'Month', 'NPHIES transfer notices', 'NPHIES per-claim notices',
              'Ledger receipts', 'Ledger matched', 'Difference (NPHIES − ledger)'], rows,
              widths={'Payer / carrier': 34, 'Difference (NPHIES − ledger)': 20}, money=('NPHIES transfer notices', 'NPHIES per-claim notices',
              'Ledger receipts', 'Ledger matched', 'Difference (NPHIES − ledger)'), name='NPHMonth')
for i in range(2, n + 1): ws[f'H{i}'] = f'=D{i}+E{i}-F{i}'; ws[f'H{i}'].number_format = NUM; ws[f'H{i}'].font = B

# ------------------------------------------------------------------ Summary (first sheet), live formulas over the detail sheets
ws = wb.active; ws.title = 'Summary'
ws['A1'] = 'AR · Accounts Receivable — detail workbook'; ws['A1'].font = T
ws['A2'] = (f"Al Faihaa Group · generated {dt.date.today():%d/%m/%Y} from the Modeling Desk payloads (EXSYS via Cure MCP, read-only). "
            f"AR Audit covers vouchers on 1240007 registered in {X['review']}; Payment Via NPHIES covers Rafha notices "
            f"{N['range'][0]} → {N['range'][1]} and Rafha receipts on 1240007 since 2025-01.")
ws['A2'].font = S; ws['A2'].alignment = Alignment(wrap_text=True); ws.merge_cells('A2:D2'); ws.row_dimensions[2].height = 44
def block(r0, title, items):
    ws.cell(r0, 1, title).font = BB; ws.cell(r0, 1).fill = PatternFill('solid', fgColor='E3F2EA')
    ws.cell(r0, 2, 'Count').font = BB; ws.cell(r0, 3, 'SAR').font = BB
    for k, (lab, fc, fs) in enumerate(items, 1):
        ws.cell(r0 + k, 1, lab).font = B
        c = ws.cell(r0 + k, 2, fc); c.font = B; c.number_format = INT
        if fs: c = ws.cell(r0 + k, 3, fs); c.font = B; c.number_format = NUM
    return r0 + len(items) + 2
r = 4
r = block(r, 'AR Audit · Insurance Payments (1240007)', [
    ('Payment vouchers reviewed', '=COUNTA('+rg('AR Vouchers','Voucher')+')', '=SUM('+rg('AR Vouchers','Amount to 1240007')+')'),
    ('Exceptions', '=COUNTIF('+rg('AR Vouchers','Result')+',"Exception")', '=SUMIFS('+rg('AR Vouchers','Amount to 1240007')+','+rg('AR Vouchers','Result')+',"Exception")'),
    ('Need review', '=COUNTIF('+rg('AR Vouchers','Result')+',"Review")', '=SUMIFS('+rg('AR Vouchers','Amount to 1240007')+','+rg('AR Vouchers','Result')+',"Review")'),
    ('Remitter ≠ customer (Chk payer = bad)', '=COUNTIF('+rg('AR Vouchers','Chk payer')+',"bad")', None),
    ('Month differs (Chk month = bad)', '=COUNTIF('+rg('AR Vouchers','Chk month')+',"bad")', None),
    ('Transfer booked twice', '=COUNTA('+rg('AR Duplicate receipts','Branch')+')', '=SUM('+rg('AR Duplicate receipts','Overstated')+')'),
    ('High-severity findings', '=COUNTIF('+rg('AR Findings','Severity')+',"High")', None)])
r = block(r, 'Payment Via NPHIES · Rafha — notices → ledger', [
    ('NPHIES cash notices', '=COUNTA('+rg('NPHIES Notices','Notice no')+')', '=SUM('+rg('NPHIES Notices','Amount')+')')] + [
    (NS[k], '=COUNTIF('+rg('NPHIES Notices','Ledger status')+f',"{NS[k]}")', '=SUMIFS('+rg('NPHIES Notices','Amount')+','+rg('NPHIES Notices','Ledger status')+f',"{NS[k]}")') for k in NS])
r = block(r, 'Payment Via NPHIES · Rafha — ledger → notices', [
    ('Rafha receipts on 1240007', '=COUNTA('+rg('Ledger Receipts','Voucher')+')', '=SUM('+rg('Ledger Receipts','Amount')+')')] + [
    (GS[k], '=COUNTIF('+rg('Ledger Receipts','Status')+f',"{GS[k]}")', '=SUMIFS('+rg('Ledger Receipts','Amount')+','+rg('Ledger Receipts','Status')+f',"{GS[k]}")') for k in GS])
ws.cell(r, 1, 'Sheets').font = BB
for k, (nm, what) in enumerate([
    ('AR Vouchers', 'one row per payment voucher: bank advice read-out, the six checks, result'),
    ('AR Findings', 'every finding, with severity and the reviewer detail'),
    ('AR Documents read', 'what each attached document actually says'),
    ('AR Duplicate receipts', 'bank transfers receipted twice'),
    ('NPHIES Payers', 'one row per NPHIES licence: identity, booking accounts, booked / not booked'),
    ('NPHIES Notices', 'every NPHIES payment notice with claims, service month and its ledger voucher'),
    ('Ledger Receipts', 'every Rafha receipt on 1240007 and the NPHIES notice(s) behind it'),
    ('NPHIES vs Ledger by month', 'payer × month totals; difference is a live formula')], 1):
    ws.cell(r + k, 1, nm).font = B; ws.cell(r + k, 2, what).font = S
ws.column_dimensions['A'].width = 46; ws.column_dimensions['B'].width = 16; ws.column_dimensions['C'].width = 20; ws.column_dimensions['D'].width = 40
wb.calculation.fullCalcOnLoad = True
wb.save(OUT); print('saved', OUT, os.path.getsize(OUT))

# Artifacts can't serve .xlsx directly: publish a base64 copy the page decodes before downloads.save()
import base64
open(OUT + '.b64.txt', 'w').write(base64.b64encode(open(OUT, 'rb').read()).decode())
