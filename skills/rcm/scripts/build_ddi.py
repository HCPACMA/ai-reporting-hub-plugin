# -*- coding: utf-8 -*-
"""Drug–drug interaction builder for the RCM interaction tab.

Reuses the SAME data already pulled for the appropriateness tabs:
  raw/dxappr_ep_*.md  — one row per episode with its drug product-code set (drugset),
                        population (open / inv90), payment type and patient context.
  raw/drug_catalog.csv — drug -> ATC / brand / scientific name.

For every episode carrying >=2 medications, each drug is reduced to interaction tags
(ddi_rules.ddi_tags), all drug pairs are screened against the curated DrugBank-modelled
rule table, and the resulting interactions (severity, mechanism, corrective action) are
aggregated. Emits ddi.json for the dashboard tab + workbook sheet.

Provenance: DrugBank's licensed DDI dataset is not reachable from this sandbox, so the
rules are a curated best-practice set modelled on DrugBank's structure; see ddi_rules.py.
A flag is a corrective-action prompt for pharmacist/clinician review, not evidence of harm.
"""
import csv, glob, json
import ddi_rules as D
import dxappr_rules as R

DETAIL_CAP = 2500
POPS = ['open', 'inv90']


def load_catalog():
    cat = {}
    for r in csv.DictReader(open('raw/drug_catalog.csv', encoding='utf-8')):
        code = (r['code'] or '').strip()
        if not code:
            continue
        cls = R.classify(r['atc1'], r['pdesc'], r['sci'])
        cat[code] = {'name': (r['pdesc'] or '').strip() or code,
                     'tags': D.ddi_tags(r['atc1'], r['pdesc'], r['sci'], cls)}
    return cat


def parse_pipe(path):
    raw = open(path, encoding='utf-8').read()
    s = raw.lstrip()
    txt = raw
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
    eps = []
    for f in sorted(glob.glob('raw/dxappr_ep_*.md')):
        eps.extend(parse_pipe(f))
    print('episode rows:', len(eps))

    # per (pop) severity tallies + episode counts; per-pair-class tallies; detail rows
    sev_counts = {p: {'Contraindicated': 0, 'Major': 0, 'Moderate': 0, 'Minor': 0} for p in POPS}
    ep_flagged = {p: set() for p in POPS}
    ep_total = {p: 0 for p in POPS}
    paircls = {p: {} for p in POPS}
    detail = []

    for r in eps:
        pop = (r.get('POP') or '').strip()
        if pop not in POPS:
            continue
        ep_total[pop] += 1
        codes = []
        seen = set()
        for c in (r.get('DRUGSET') or '').split():
            if c in seen:
                continue
            seen.add(c)
            info = cat.get(c)
            if info and info['tags']:
                codes.append({'code': c, 'name': info['name'], 'tags': info['tags']})
        if len(codes) < 2:
            continue
        inter = D.interactions_for(codes)
        if not inter:
            continue
        epkey = (r.get('ORG'), r.get('PATIENT_FILE'), r.get('EPISODE_NO'))
        ep_flagged[pop].add(epkey)
        # episode's worst severity for the detail ordering
        for it in inter:
            sev_counts[pop][it['sev']] += 1
            paircls[pop][it['pair_class']] = paircls[pop].get(it['pair_class'], 0) + 1
            detail.append({
                'pop': pop, 'org': r.get('ORG'), 'patient_file': r.get('PATIENT_FILE'),
                'episode_no': r.get('EPISODE_NO'), 'patient_name': r.get('PATIENT_NAME'),
                'date': r.get('ORDER_DATE'), 'pt': r.get('PT'),
                'severity': it['sev'], 'pair_class': it['pair_class'],
                'drug_a': it['drug_a'], 'drug_b': it['drug_b'],
                'mechanism': it['mech'], 'action': it['action'],
            })

    # order detail: severity desc, then most-recent
    detail.sort(key=lambda d: (-D.SEV_RANK.get(d['severity'], 0), d['date'] or ''), reverse=False)
    detail.sort(key=lambda d: (D.SEV_RANK.get(d['severity'], 0), d['date'] or ''), reverse=True)
    total_detail = len(detail)
    rows = detail[:DETAIL_CAP]

    books = {}
    for p in POPS:
        pairs = sorted(paircls[p].items(), key=lambda kv: -kv[1])
        books[p] = {
            'kpi': {
                'episodes_screened': ep_total[p],
                'episodes_flagged': len(ep_flagged[p]),
                'interactions': sum(sev_counts[p].values()),
                'contraindicated': sev_counts[p]['Contraindicated'],
                'major': sev_counts[p]['Major'],
                'moderate': sev_counts[p]['Moderate'],
                'minor': sev_counts[p]['Minor'],
            },
            'pairs': [{'label': k, 'count': v} for k, v in pairs],
        }

    out = {
        'books': books,
        'rows': rows,
        'meta': {
            'source': 'RC_PATIENT_MEDICATION_ORDER_MV drug pairs per episode (open + invoiced 90d) x curated DrugBank-modelled DDI rule set',
            'populations': {'open': "Open episodes (STATUS='O')", 'inv90': 'Invoiced, last 90 days'},
            'severity_order': ['Contraindicated', 'Major', 'Moderate', 'Minor'],
            'note': 'Each episode with >=2 medications is screened for drug-drug interactions. A flag is a corrective-action prompt for pharmacist & clinician review — not evidence that harm occurred. Route-aware: purely topical/local forms are not screened for systemic interactions.',
            'provenance': "DrugBank's licensed DDI dataset is not reachable from this environment (no account / network allowlist), so interactions use a curated rule set modelled on DrugBank's structure (severity tiers, mechanism, corrective action) in ddi_rules.py — high-yield, well-established interactions for this outpatient formulary. On a networked machine with DrugBank credentials the same tab can be repopulated from the full DrugBank DDI table.",
            'total_interactions': total_detail, 'detail_capped_at': DETAIL_CAP,
        },
    }
    json.dump(out, open('ddi.json', 'w', encoding='utf-8'), ensure_ascii=False)
    for p in POPS:
        k = books[p]['kpi']
        print('%-6s screened=%d flagged_ep=%d interactions=%d (C%d/Maj%d/Mod%d/Min%d)' % (
            p, k['episodes_screened'], k['episodes_flagged'], k['interactions'],
            k['contraindicated'], k['major'], k['moderate'], k['minor']))
    print('detail rows: %d (capped %d)' % (total_detail, DETAIL_CAP))
    print('top pairs (open):', [(x['label'], x['count']) for x in books['open']['pairs'][:8]])


if __name__ == '__main__':
    build()
