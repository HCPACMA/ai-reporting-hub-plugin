# -*- coding: utf-8 -*-
"""Diagnosis-appropriateness (medication necessity) builder.

Data pull (paged, canonical query = EPISODE_SQL): one row per violation-eligible
episode (has >=1 medication order AND >=1 diagnosis) across two populations:
  * open   — open episodes (RC_PATIENT_EPISODES.STATUS='O')
  * inv90  — episodes invoiced in the last 90 days
Each row carries the episode's distinct ICD-10 codes (dxset), distinct drug
product codes (drugset), payment type and patient context. Pages of 1000 via
:off. Pages are saved to raw/dxappr_ep_<NNNN>.md.

build(): classifies every drug (dxappr_rules: ATC then brand keyword, from
raw/drug_catalog.csv), and for each (episode, drug) tests whether the episode
carries an accepted diagnosis for the drug's therapeutic class under each
rule-book (curated / strict). Emits dxappr.json (KPIs, class breakdowns, capped
violation detail) for the two dashboard tabs + workbook sheets.

A flag = a medication whose therapeutic indication is not among the episode's
diagnoses. It is a documentation / medical-necessity screening signal for coder
& clinician review, NOT a determination the drug was clinically wrong. Episodes
with no diagnosis at all are the separate "Medication without diagnosis" check.
"""
import csv, glob, json, os, sys
import dxappr_rules as R

EPISODE_SQL = """WITH ep AS (
  SELECT 'open' pop, e.ORGANIZATION_NO o, e.PATIENT_FILE_NO p, e.EPISODE_NO e,
         CASE WHEN cg.DESCRIPTION_P='Cash Customer' THEN 'Cash' ELSE 'Credit' END pt
  FROM RC_PATIENT_EPISODES e
  LEFT JOIN RC_CONTRACTS c ON c.CONTRACT_NO=e.CONTRACT_NO
  LEFT JOIN CUSTOMER_GROUPS cg ON cg.CUSTOMER_GROUP_NO=c.CUSTOMER_GROUP_NO
  WHERE e.STATUS='O'
  UNION ALL
  SELECT 'inv90', e.ORGANIZATION_NO, e.PATIENT_FILE_NO, e.EPISODE_NO,
         CASE WHEN cg.DESCRIPTION_P='Cash Customer' THEN 'Cash' ELSE 'Credit' END pt
  FROM RC_PATIENT_EPISODES e
  JOIN (SELECT DISTINCT ORGANIZATION_NO o,PATIENT_FILE_NO p,EPISODE_NO e FROM RC_EPISODE_INVOICES WHERE INVOICE_DATE>=SYSDATE-90) iv
    ON iv.o=e.ORGANIZATION_NO AND iv.p=e.PATIENT_FILE_NO AND iv.e=e.EPISODE_NO
  LEFT JOIN RC_CONTRACTS c ON c.CONTRACT_NO=e.CONTRACT_NO
  LEFT JOIN CUSTOMER_GROUPS cg ON cg.CUSTOMER_GROUP_NO=c.CUSTOMER_GROUP_NO
),
epm AS (
  SELECT ep.pop, ep.o, ep.p, ep.e, ep.pt,
    (SELECT MIN(mm.REQUEST_DATE) FROM RC_PATIENT_MEDICATION_ORDER_MV mm WHERE mm.ORGANIZATION_NO=ep.o AND mm.PATIENT_FILE_NO=ep.p AND mm.EPISODE_NO=ep.e) req,
    (SELECT MAX(REPLACE(REPLACE(mm.PATIENT_NAME_P,'|','/'),CHR(10),' ')) FROM RC_PATIENT_MEDICATION_ORDER_MV mm WHERE mm.ORGANIZATION_NO=ep.o AND mm.PATIENT_FILE_NO=ep.p AND mm.EPISODE_NO=ep.e) pname,
    (SELECT MAX(mm.AGE) FROM RC_PATIENT_MEDICATION_ORDER_MV mm WHERE mm.ORGANIZATION_NO=ep.o AND mm.PATIENT_FILE_NO=ep.p AND mm.EPISODE_NO=ep.e) age,
    (SELECT MAX(mm.GENDER) FROM RC_PATIENT_MEDICATION_ORDER_MV mm WHERE mm.ORGANIZATION_NO=ep.o AND mm.PATIENT_FILE_NO=ep.p AND mm.EPISODE_NO=ep.e) gender
  FROM ep
  WHERE EXISTS (SELECT 1 FROM RC_PATIENT_MEDICATION_ORDER_MV mm WHERE mm.ORGANIZATION_NO=ep.o AND mm.PATIENT_FILE_NO=ep.p AND mm.EPISODE_NO=ep.e)
    AND EXISTS (SELECT 1 FROM RC_PATIENT_DIAGNOSIS_MV dd WHERE dd.ORGANIZATION_NO=ep.o AND dd.PATIENT_FILE_NO=ep.p AND dd.EPISODE_NO=ep.e)
)
SELECT pop, o AS org, p AS patient_file, e AS episode_no, pt,
  TO_CHAR(req,'YYYY-MM-DD') AS order_date, pname AS patient_name, age, gender,
  (SELECT LISTAGG(c,' ') WITHIN GROUP (ORDER BY c) FROM (SELECT DISTINCT SUBSTR(REPLACE(d.DIAGNOSIS_CODE,'.',''),1,5) c FROM RC_PATIENT_DIAGNOSIS_MV d WHERE d.ORGANIZATION_NO=epm.o AND d.PATIENT_FILE_NO=epm.p AND d.EPISODE_NO=epm.e)) AS dxset,
  (SELECT LISTAGG(dc,', ') WITHIN GROUP (ORDER BY dc) FROM (SELECT DISTINCT d.DIAGNOSIS_CODE dc FROM RC_PATIENT_DIAGNOSIS_MV d WHERE d.ORGANIZATION_NO=epm.o AND d.PATIENT_FILE_NO=epm.p AND d.EPISODE_NO=epm.e AND ROWNUM<=8)) AS dxcodes,
  (SELECT LISTAGG(dn,' / ') WITHIN GROUP (ORDER BY dn) FROM (SELECT DISTINCT REPLACE(REPLACE(REPLACE(d.DIAGNOSIS_NAME,'|','/'),CHR(10),' '),CHR(13),' ') dn FROM RC_PATIENT_DIAGNOSIS_MV d WHERE d.ORGANIZATION_NO=epm.o AND d.PATIENT_FILE_NO=epm.p AND d.EPISODE_NO=epm.e AND ROWNUM<=6)) AS dxnames,
  (SELECT LISTAGG(pc,' ') WITHIN GROUP (ORDER BY pc) FROM (SELECT DISTINCT m.PRODUCT_CODE pc FROM RC_PATIENT_MEDICATION_ORDER_MV m WHERE m.ORGANIZATION_NO=epm.o AND m.PATIENT_FILE_NO=epm.p AND m.EPISODE_NO=epm.e)) AS drugset
FROM epm
ORDER BY pop, org, patient_file, episode_no
OFFSET :off ROWS FETCH NEXT 1000 ROWS ONLY"""

DETAIL_CAP = 2500


def load_catalog():
    cat = {}
    for r in csv.DictReader(open('raw/drug_catalog.csv', encoding='utf-8')):
        code = (r['code'] or '').strip()
        if not code:
            continue
        cat[code] = {'cls': R.classify(r['atc1'], r['pdesc'], r['sci']),
                     'name': (r['pdesc'] or '').strip()}
    return cat


def parse_pipe(path):
    raw = open(path, encoding='utf-8').read()
    txt = raw
    s = raw.lstrip()
    if s.startswith('{'):
        try:
            txt = json.loads(raw).get('result', raw)
        except Exception:
            txt = raw
    lines = [l for l in txt.splitlines() if l.strip().startswith('|')]
    if not lines:
        return []
    hdr = [h.strip() for h in lines[0].strip().strip('|').split('|')]
    out = []
    for l in lines[2:]:
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if len(c) < len(hdr):
            continue
        if len(c) > len(hdr):
            c = c[:len(hdr) - 1] + [' | '.join(c[len(hdr) - 1:])]
        out.append(dict(zip(hdr, c)))
    return out


def build():
    cat = load_catalog()
    files = sorted(glob.glob('raw/dxappr_ep_*.md'))
    eps = []
    for f in files:
        eps.extend(parse_pipe(f))
    print('episode rows loaded:', len(eps), 'from', len(files), 'pages')

    POPS = ['open', 'inv90']
    # accumulators: agg[book][pop][cls] = {orders,with_dx,supported,violations}
    agg = {b: {p: {} for p in POPS} for b in ('curated', 'strict')}
    viol_rows = []   # candidate detail rows (violations under either book)

    for r in eps:
        pop = (r.get('POP') or '').strip()
        if pop not in POPS:
            continue
        dxset = set((r.get('DXSET') or '').split())
        drugcodes = (r.get('DRUGSET') or '').split()
        pt = r.get('PT'); org = r.get('ORG'); pf = r.get('PATIENT_FILE'); epn = r.get('EPISODE_NO')
        seen = set()
        for code in drugcodes:
            if code in seen:
                continue
            seen.add(code)
            info = cat.get(code)
            cls = info['cls'] if info else None
            if not cls:
                continue  # not assessed
            drug_name = info['name'] if info else code
            row_flags = {}
            for book in ('curated', 'strict'):
                pref = R.icd_prefixes(cls, book)
                if pref is None:
                    row_flags[book] = None  # not assessed under this book
                    continue
                ok = R.dx_matches(dxset, pref)
                d = agg[book][pop].setdefault(cls, {'orders': 0, 'supported': 0, 'violations': 0})
                d['orders'] += 1
                if ok:
                    d['supported'] += 1
                    row_flags[book] = 'ok'
                else:
                    d['violations'] += 1
                    row_flags[book] = 'viol'
            if row_flags.get('curated') == 'viol' or row_flags.get('strict') == 'viol':
                viol_rows.append({
                    'pop': pop, 'org': org, 'patient_file': pf, 'episode_no': epn,
                    'code': code, 'cls': cls, 'class_label': R.class_label(cls),
                    'drug': drug_name, 'patient_name': r.get('PATIENT_NAME'),
                    'age': r.get('AGE'), 'gender': r.get('GENDER'), 'date': r.get('ORDER_DATE'),
                    'pt': pt, 'dx_codes': r.get('DXCODES'), 'dx_names': r.get('DXNAMES'),
                    'cur_violation': row_flags.get('curated') == 'viol',
                    'strict_violation': row_flags.get('strict') == 'viol',
                })

    # build per-book/per-pop KPI + class breakdown
    books = {}
    for book in ('curated', 'strict'):
        books[book] = {}
        for pop in POPS:
            classes = []
            tot_o = tot_ok = tot_v = 0
            for cls, d in agg[book][pop].items():
                classes.append({'cls': cls, 'label': R.class_label(cls),
                                'orders': d['orders'], 'supported': d['supported'],
                                'violations': d['violations']})
                tot_o += d['orders']; tot_ok += d['supported']; tot_v += d['violations']
            classes.sort(key=lambda x: -x['violations'])
            rate = round(100.0 * tot_ok / tot_o, 1) if tot_o else 0.0
            books[book][pop] = {'kpi': {'assessed_orders': tot_o, 'supported': tot_ok,
                                        'violations': tot_v, 'appropriateness_rate': rate},
                                'classes': classes}

    # order detail rows: most recent first, cap
    viol_rows.sort(key=lambda x: (x['date'] or ''), reverse=True)
    total_viol_rows = len(viol_rows)
    rows = viol_rows[:DETAIL_CAP]

    out = {
        'books': books,
        'rows': rows,
        'meta': {
            'source': 'RC_PATIENT_MEDICATION_ORDER_MV (drug orders) x RC_PATIENT_DIAGNOSIS_MV (episode ICD-10)',
            'populations': {'open': "Open episodes (STATUS='O')", 'inv90': 'Invoiced, last 90 days'},
            'rulebooks': {
                'curated': 'Balanced ATC/brand therapeutic map — broader accepted ICD-10 families per drug class. Vitamins/supplements are not assessed. A drug is flagged only if its class is known and the episode carries diagnoses but none is an accepted indication.',
                'strict': 'Tighter accepted ICD-10 families, and vitamins/supplements ARE assessed (a supplement with no matching deficiency diagnosis is flagged). Higher catch rate, more to triage.'},
            'classifier': 'Drug -> therapeutic class by ATC code (PH_SFDA_PRODUCTS via SFDA registration no.) else brand/scientific keyword. ~98% of order volume classified; the remainder is shown as "not assessed" and never flagged.',
            'note': 'A flag is a documentation / medical-necessity screening signal for coder & clinician review — NOT a determination that a medication was clinically wrong. Episodes with no diagnosis at all are covered by the separate "Medication without diagnosis" check, not here.',
            'total_violation_rows': total_viol_rows, 'detail_capped_at': DETAIL_CAP,
            'rulebook_note': 'Both rule-books are maintained in dxappr_rules.py (transparent, editable). No NPHIES/CHI ICD-drug crossmatch table is populated at this site, so appropriateness uses these explicit rule-books.',
        },
    }
    json.dump(out, open('dxappr.json', 'w', encoding='utf-8'), ensure_ascii=False)
    for book in ('curated', 'strict'):
        for pop in POPS:
            k = books[book][pop]['kpi']
            print('%-8s %-6s orders=%d supported=%d violations=%d rate=%.1f%%' % (
                book, pop, k['assessed_orders'], k['supported'], k['violations'], k['appropriateness_rate']))
    print('violation detail rows: %d (capped at %d)' % (total_viol_rows, DETAIL_CAP))


if __name__ == '__main__':
    build()
