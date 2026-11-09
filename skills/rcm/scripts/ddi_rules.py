# -*- coding: utf-8 -*-
"""Drug–drug interaction (DDI) knowledge base for the RCM interaction tab.

DrugBank's licensed dataset is not reachable from this sandbox (no account / not on
the network allowlist), so this is a CURATED, clinically-grounded rule set modelled on
DrugBank's DDI structure: each drug is reduced to a set of pharmacologic interaction
TAGS (ingredient / class, derived from ATC code, else brand/scientific keyword), and a
symmetric RULE table maps tag-pairs to a severity tier (Contraindicated / Major /
Moderate / Minor), the interaction mechanism, and a concrete CORRECTIVE ACTION.

Scope = the high-yield, well-established interactions relevant to this outpatient
formulary. Route-aware: purely topical/local forms (gel, cream, vaginal, eye/ear,
nasal) are not given systemic tags, so e.g. a diclofenac GEL is not flagged as a
systemic NSAID interaction.

A flagged interaction is a screening / corrective-action prompt for pharmacist &
clinician review — not a statement that harm occurred.
"""
import re
import dxappr_rules as R

SEV_RANK = {'Contraindicated': 4, 'Major': 3, 'Moderate': 2, 'Minor': 1}

_TOPICAL = re.compile(r'\b(gel|cream|ointment|emulgel|topical|derm|lotion|ovule|ovules|pessar|vag|vaginal|suppositor|eye|ophth|opht|optha|ear|otic|n/?spray|nasal|nose|drops|dps|inhaler|evohaler|respule|nebul)\b', re.I)


def _atc_tags(a):
    """Precise tags from ATC code prefix."""
    t = set()
    if not a:
        return t
    a = a.upper()
    P = lambda *pfx: any(a.startswith(x) for x in pfx)
    if P('M01A'): t |= {'nsaid'}
    if P('N02BA'): t |= {'nsaid', 'aspirin_analgesic'}          # acetylsalicylic acid (analgesic dose)
    if P('B01AC06'): t |= {'antiplatelet', 'aspirin'}           # low-dose ASA
    if P('B01AC04'): t |= {'antiplatelet', 'clopidogrel'}
    if P('B01AC'): t |= {'antiplatelet'}
    if P('B01AA'): t |= {'anticoagulant', 'warfarin'}
    if P('B01AF', 'B01AE'): t |= {'anticoagulant'}              # DOACs
    if P('B01AB'): t |= {'anticoagulant'}                       # heparins
    if P('C09'): t |= {'ace_arb', 'raas'}
    if P('C03DA'): t |= {'k_sparing', 'diuretic'}
    if P('C03'): t |= {'diuretic'}
    if P('A12BA'): t |= {'potassium'}
    if P('N06AB'): t |= {'ssri', 'serotonergic'}
    if P('N06AX'): t |= {'serotonergic'}                        # SNRIs / others
    if P('N06AF', 'N06AG'): t |= {'maoi', 'serotonergic'}
    if P('N02AX02'): t |= {'tramadol', 'opioid', 'serotonergic'}
    if P('N02A'): t |= {'opioid', 'cns_depressant'}
    if P('N05BA', 'N05CD', 'N05CF'): t |= {'benzodiazepine', 'cns_depressant'}
    if P('N03AX12', 'N02BF'): t |= {'cns_depressant'}           # gabapentin/pregabalin
    if P('N02CC'): t |= {'triptan', 'serotonergic'}
    if P('J01FA'): t |= {'macrolide', 'cyp3a4_inhibitor', 'qt_prolong'}
    if P('J01MA'): t |= {'fluoroquinolone', 'qt_prolong', 'polyvalent_sensitive'}
    if P('J02AC', 'J02AB'): t |= {'azole_antifungal', 'cyp3a4_inhibitor', 'qt_prolong'}
    if P('P01AB', 'J01XD'): t |= {'metronidazole', 'disulfiram_like'}
    if P('J01EE', 'J01EA'): t |= {'trimethoprim'}
    if P('C10AA'): t |= {'statin'}
    if P('A10BB', 'A10BJ'): t |= {'sulfonylurea', 'hypoglycemic'}
    if P('A10A'): t |= {'insulin', 'hypoglycemic'}
    if P('A10BA'): t |= {'metformin'}
    if P('A02BC'): t |= {'ppi'}
    if P('H02AB'): t |= {'corticosteroid'}
    if P('A03FA01'): t |= {'metoclopramide', 'qt_prolong', 'serotonergic'}
    if P('A03FA03', 'A03FA'): t |= {'domperidone', 'qt_prolong'}
    if P('A04AA'): t |= {'setron', 'qt_prolong'}                # ondansetron etc.
    if P('R03DA'): t |= {'theophylline'}
    if P('L01BA01', 'L04AX03'): t |= {'methotrexate'}
    if P('C01AA'): t |= {'digoxin'}
    if P('H03AA'): t |= {'levothyroxine'}
    if P('B03A'): t |= {'polyvalent_cation', 'iron'}
    if P('A12AA'): t |= {'polyvalent_cation', 'calcium'}
    if P('A02A'): t |= {'polyvalent_cation', 'antacid'}
    if P('R06AD', 'R06AB', 'R06AA'): t |= {'sedating_antihistamine', 'cns_depressant'}
    return t


# brand / scientific keyword -> tags, for drugs that don't resolve to an ATC
_BRAND = [
 (['warfarin', 'marevan', 'marfarin', 'orfarin'], {'anticoagulant', 'warfarin'}),
 (['xarelto', 'rivaroxaban', 'eliquis', 'apixaban', 'pradaxa', 'dabigatran', 'lixiana', 'edoxaban'], {'anticoagulant'}),
 (['clexane', 'enoxaparin', 'heparin', 'fraxiparine', 'innohep', 'fondaparin'], {'anticoagulant'}),
 (['plavix', 'clopidogrel', 'clopid', 'brilinta', 'ticagrelor', 'effient', 'prasugrel'], {'antiplatelet', 'clopidogrel'}),
 (['jusprin', 'aspocid', 'aspirin', 'asa ', 'ecosprin', 'cardioaspirin', 'baby aspirin'], {'antiplatelet', 'aspirin'}),
 (['xefo', 'lornoxicam', 'rofenac', 'cataflam', 'catafast', 'voltaren', 'votrex', 'diclomax', 'diclofenac', 'sapofen',
   'brufen', 'nurofen', 'ibuprofen', 'mobic', 'meloxicam', 'fenam', 'mefenamic', 'ponstan', 'naproxen', 'proxen',
   'napren', 'celebrex', 'celecoxib', 'arcoxia', 'etoricoxib', 'ketolgan', 'ketorolac', 'feldene', 'piroxicam',
   'indomethacin', 'nabuco', 'voltic', 'olfen', 'adwiflam', 'fastum', 'dolfen'], {'nsaid'}),
 (['tramadol', 'tramal', 'tramax', 'ultracet', 'tramundin'], {'tramadol', 'opioid', 'serotonergic'}),
 (['codeine', 'morphine', 'oxycod', 'oxycontin', 'fentanyl', 'pethidine', 'tapentadol', 'nalufin', 'nalbuphine'], {'opioid', 'cns_depressant'}),
 (['xanax', 'alprazolam', 'valium', 'diazepam', 'ativan', 'lorazepam', 'rivotril', 'clonazepam', 'lexotanil', 'bromazepam',
   'dormicum', 'midazolam', 'librax'], {'benzodiazepine', 'cns_depressant'}),
 (['lyrica', 'pregabalin', 'gabapentin', 'neurontin', 'gabica'], {'cns_depressant'}),
 (['prozac', 'fluoxetine', 'seroxat', 'paroxetine', 'cipralex', 'escitalopram', 'cipram', 'citalopram', 'zoloft',
   'sertraline', 'faverin', 'fluvoxamine', 'lustral'], {'ssri', 'serotonergic'}),
 (['effexor', 'venlafaxine', 'cymbalta', 'duloxetine'], {'serotonergic'}),
 (['imigran', 'sumatriptan', 'zomig', 'rizatriptan', 'maxalt'], {'triptan', 'serotonergic'}),
 (['azimac', 'azithromic', 'azithromycin', 'zithromax', 'xithrone', 'azi-once', 'azitromicina', 'klacid', 'clarithromy',
   'klaricid', 'erythro', 'erythrocin', 'rovamycine', 'spiramycin'], {'macrolide', 'cyp3a4_inhibitor', 'qt_prolong'}),
 (['ciproxen', 'ciprogen', 'ciflox', 'ciprocin', 'ciproflacin', 'ciprofloxacin', 'ciprodar', 'ciprobay', 'levoflox',
   'levofloxacin', 'tavanic', 'avalox', 'moxifloxacin', 'ofloxacin', 'norfloxacin'], {'fluoroquinolone', 'qt_prolong', 'polyvalent_sensitive'}),
 (['diflucan', 'fluconazol', 'itraconazol', 'itracon', 'ketoconazol', 'voriconazol', 'sporanox'], {'azole_antifungal', 'cyp3a4_inhibitor', 'qt_prolong'}),
 (['flagyl', 'anazol', 'metronidazol', 'amrizole', 'dumozol', 'tinidazol', 'fasigyn'], {'metronidazole', 'disulfiram_like'}),
 (['septrin', 'co-trimoxazole', 'cotrimoxazole', 'sulfamethoxazole', 'trimethoprim', 'bactrim', 'septra'], {'trimethoprim'}),
 (['atorlip', 'atorvastatin', 'lipitor', 'crestor', 'rosuvastatin', 'zocor', 'simvastatin', 'pravastatin', 'lescol',
   'fluvastatin', 'lovastatin', 'ezetrol'], {'statin'}),
 (['amaryl', 'glimepirid', 'diamicron', 'gliclazid', 'claz-mr', 'glibenclam', 'daonil', 'gliben', 'glipizide', 'minidiab'], {'sulfonylurea', 'hypoglycemic'}),
 (['insulin', 'lantus', 'novomix', 'novorapid', 'actrapid', 'mixtard', 'tresiba', 'humalog', 'levemir', 'toujeo'], {'insulin', 'hypoglycemic'}),
 (['metformin', 'glucophage', 'cidophage', 'gliptamet', 'glucovance', 'diaformin'], {'metformin'}),
 (['hyposec', 'nexium', 'peptazol', 'gasec', 'esoxo', 'pantozol', 'pantoloc', 'pantomax', 'toprazole', 'omepr', 'losec',
   'risek', 'controloc', 'pariet', 'esomeprazol', 'pantoprazol', 'lansoprazol', 'rabeprazol', 'omez', 'gastrozol'], {'ppi'}),
 (['hydrocortison', 'prednisolon', 'prednison', 'solupred', 'deltacortril', 'methylprednisolon', 'depo-medrol', 'medrol',
   'dexamethason', 'betamethason', 'diprofos', 'kenacort', 'triamcinolon'], {'corticosteroid'}),
 (['dompy', 'premosan', 'motilium', 'domperidone'], {'domperidone', 'qt_prolong'}),
 (['primperan', 'metoclopram', 'metoclopramide'], {'metoclopramide', 'qt_prolong', 'serotonergic'}),
 (['zoron', 'zetron', 'ondansetron', 'zofran', 'danset'], {'setron', 'qt_prolong'}),
 (['eltroxin', 'euthyrox', 'levothyrox', 'thyronorm', 'thyrox', 'levothyroxine'], {'levothyroxine'}),
 (['ferose', 'hemadid', 'ferro-fol', 'ferrofol', 'ferrous', 'haemoton', 'ferro', 'haemofer', 'feroglobin', 'iron', 'totema', 'sangobion'], {'polyvalent_cation', 'iron'}),
 (['calcinate', 'calcium', 'cal-', 'osteocare', 'ossofortin', 'caltrate'], {'polyvalent_cation', 'calcium'}),
 (['epimag', 'gaviscon', 'maalox', 'antacid', 'mucogel', 'rennie', 'magaldrate'], {'polyvalent_cation', 'antacid'}),
 (['aldomet', 'methyldopa'], {'ace_arb'}),           # not RAAS but treat CV additive; approximate
 (['amlocard', 'amlodipin', 'amlor', 'norvasc', 'diovan', 'valsartan', 'exforge', 'concor', 'bisoprolol', 'tritace',
   'ramipril', 'co-diovan', 'micardis', 'telmisartan', 'capoten', 'captopril', 'zestril', 'lisinopril', 'coversyl',
   'perindopril', 'losartan', 'cozaar', 'aprovel', 'irbesartan', 'olmesartan'], {'antihypertensive'}),
 (['lasix', 'furosemide', 'frusemide', 'natrilix', 'indapamid', 'hydrochlorothiazide', 'hydrochlorothiazid', 'moduretic'], {'diuretic'}),
 (['spironolacton', 'aldactone', 'eplerenon'], {'k_sparing', 'diuretic'}),
 (['digoxin', 'lanoxin'], {'digoxin'}),
 (['methotrexate', 'trexall', 'rheumatrex'], {'methotrexate'}),
 (['minipress', 'sildenafil', 'viagra', 'tadalafil', 'cialis'], {'pde5'}),
 (['clara', 'lorine', 'zyrtec', 'cetirizin', 'loratadin', 'levozal', 'levocetiriz', 'avil', 'fenistil', 'polaramine', 'atarax', 'hydroxyzine'], set()),  # non-sedating/most antihistamines: no major systemic DDI here
]


def _has(text, kw):
    """Match kw at a WORD START (kw may be a prefix of a longer word), so 'proxen'
    matches brand 'Proxen' but NOT 'Ciproxen'/'Naproxen'."""
    return re.search(r'(?<![a-z0-9])' + re.escape(kw), text) is not None


def ddi_tags(atc, pdesc, sci, cls=None):
    text = (' ' + (pdesc or '') + ' ' + (sci or '') + ' ').lower()
    topical = bool(_TOPICAL.search(text))
    tags = set()
    tags |= _atc_tags(atc)
    for kws, tg in _BRAND:
        if any(_has(text, k) for k in kws):
            tags |= tg
    # a few class-level fallbacks from the appropriateness classifier
    if cls == 'nsaid':
        tags.add('nsaid')
    if cls == 'ppi':
        tags.add('ppi')
    if cls in ('macrolide',):
        tags.add('macrolide')
    if topical:
        # keep only tags that make sense locally; drop systemic-interaction tags
        tags -= {'nsaid', 'anticoagulant', 'antiplatelet', 'corticosteroid', 'ace_arb', 'ssri', 'serotonergic',
                 'opioid', 'benzodiazepine', 'statin', 'metronidazole', 'macrolide', 'fluoroquinolone', 'sulfonylurea',
                 'insulin', 'metformin', 'cns_depressant', 'qt_prolong'}
    return tags


# ---- interaction rules: (tagA, tagB, severity, mechanism, corrective action) ----
# tagA==tagB means "two DIFFERENT drugs both carrying that tag".
RULES = [
 ('nsaid', 'nsaid', 'Major', 'Two systemic NSAIDs — additive GI ulceration/bleeding and renal risk with no added benefit.',
  'Keep a single NSAID; stop the duplicate. Add a PPI if an NSAID must continue.'),
 ('anticoagulant', 'nsaid', 'Major', 'Additive bleeding risk; NSAIDs also impair platelets and can raise anticoagulant effect.',
  'Avoid NSAID; use paracetamol. If unavoidable, shortest course + PPI and monitor INR/for bleeding.'),
 ('anticoagulant', 'antiplatelet', 'Major', 'Additive bleeding from combined anticoagulant + antiplatelet.',
  'Only combine with a documented indication (e.g. recent stent + AF); add PPI and set a stop date; monitor bleeding.'),
 ('antiplatelet', 'nsaid', 'Major', 'Antiplatelet + NSAID markedly raises GI bleeding risk.',
  'Avoid chronic NSAID; prefer paracetamol. If needed, co-prescribe a PPI.'),
 ('warfarin', 'metronidazole', 'Major', 'Metronidazole inhibits warfarin metabolism → INR rises, bleeding.',
  'Monitor INR within 3–5 days; pre-emptively reduce warfarin dose.'),
 ('warfarin', 'macrolide', 'Major', 'Macrolide CYP inhibition raises warfarin effect (INR↑).',
  'Monitor INR closely; consider an alternative antibiotic.'),
 ('warfarin', 'fluoroquinolone', 'Major', 'Fluoroquinolones potentiate warfarin (INR↑).',
  'Monitor INR closely during and after the course.'),
 ('warfarin', 'azole_antifungal', 'Major', 'Azole CYP2C9 inhibition sharply raises warfarin effect.',
  'Avoid if possible; if used, reduce warfarin dose and monitor INR.'),
 ('warfarin', 'nsaid', 'Major', 'Additive bleeding + protein-binding displacement.',
  'Avoid NSAID; use paracetamol. If essential, PPI + close INR/bleeding monitoring.'),
 ('clopidogrel', 'ppi', 'Moderate', 'Omeprazole/esomeprazole inhibit CYP2C19 → reduced clopidogrel activation.',
  'Prefer pantoprazole or an H2-blocker; avoid omeprazole/esomeprazole with clopidogrel.'),
 ('serotonergic', 'serotonergic', 'Major', 'Two serotonergic agents — risk of serotonin syndrome.',
  'Avoid combining; if unavoidable, use lowest doses and counsel on serotonin-toxicity symptoms.'),
 ('opioid', 'benzodiazepine', 'Major', 'Additive CNS/respiratory depression.',
  'Avoid co-prescription; if essential use lowest doses, counsel, and consider take-home naloxone.'),
 ('cns_depressant', 'cns_depressant', 'Moderate', 'Additive sedation / CNS depression.',
  'Review need for both; warn about sedation, driving and falls.'),
 ('ace_arb', 'ace_arb', 'Major', 'Dual RAAS blockade → hyperkalaemia and acute kidney injury.',
  'Do not combine an ACE inhibitor with an ARB; keep one agent.'),
 ('ace_arb', 'potassium', 'Major', 'Additive hyperkalaemia.',
  'Avoid routine potassium; monitor serum potassium.'),
 ('ace_arb', 'k_sparing', 'Major', 'ACE/ARB + potassium-sparing diuretic → hyperkalaemia.',
  'Monitor potassium and renal function; avoid unless closely supervised.'),
 ('ace_arb', 'nsaid', 'Moderate', 'NSAID blunts antihypertensive effect and adds renal risk ("triple whammy" with a diuretic).',
  'Limit NSAID duration; monitor BP, renal function and potassium — especially in the elderly/CKD.'),
 ('diuretic', 'nsaid', 'Moderate', 'NSAID reduces diuretic/antihypertensive effect and adds renal risk.',
  'Monitor renal function and fluid status; keep NSAID short.'),
 ('statin', 'macrolide', 'Major', 'Clarithromycin/erythromycin inhibit CYP3A4 → statin levels rise, myopathy/rhabdomyolysis.',
  'Hold the statin during the macrolide course, or use azithromycin; warn re muscle pain.'),
 ('statin', 'azole_antifungal', 'Major', 'Azole CYP3A4 inhibition raises statin exposure → myopathy.',
  'Suspend statin during the azole course; counsel on muscle symptoms.'),
 ('methotrexate', 'nsaid', 'Major', 'NSAID reduces methotrexate clearance → marrow/renal toxicity.',
  'Avoid NSAID with methotrexate; if unavoidable monitor CBC and renal function.'),
 ('methotrexate', 'trimethoprim', 'Contraindicated', 'Additive antifolate effect → severe myelosuppression.',
  'Do not co-prescribe; choose a non-trimethoprim antibiotic.'),
 ('qt_prolong', 'qt_prolong', 'Major', 'Two QT-prolonging drugs — additive risk of QT prolongation / torsades.',
  'Avoid combining QT-prolonging drugs; if unavoidable, ECG and electrolyte check.'),
 ('theophylline', 'fluoroquinolone', 'Major', 'Ciprofloxacin inhibits CYP1A2 → theophylline toxicity.',
  'Avoid ciprofloxacin; monitor theophylline level and for toxicity.'),
 ('theophylline', 'macrolide', 'Moderate', 'Macrolide raises theophylline levels.',
  'Monitor theophylline level; watch for nausea, tremor, arrhythmia.'),
 ('digoxin', 'macrolide', 'Moderate', 'Macrolides raise digoxin levels.',
  'Monitor digoxin level and for toxicity.'),
 ('digoxin', 'diuretic', 'Moderate', 'Diuretic-induced hypokalaemia potentiates digoxin toxicity.',
  'Monitor potassium and digoxin level.'),
 ('corticosteroid', 'nsaid', 'Moderate', 'Additive GI ulceration/bleeding.',
  'Add gastroprotection (PPI); review need for both.'),
 ('hypoglycemic', 'fluoroquinolone', 'Moderate', 'Fluoroquinolones can cause hypo- or hyperglycaemia.',
  'Monitor blood glucose during the course.'),
 ('levothyroxine', 'polyvalent_cation', 'Moderate', 'Iron/calcium/antacid chelate levothyroxine → reduced absorption.',
  'Separate doses by at least 4 hours.'),
 ('polyvalent_sensitive', 'polyvalent_cation', 'Moderate', 'Iron/calcium/antacid chelate fluoroquinolones → treatment failure.',
  'Separate the antibiotic and the cation by 2–4 hours.'),
 ('levothyroxine', 'ppi', 'Minor', 'Reduced gastric acid lowers levothyroxine absorption.',
  'Monitor TSH; separate dosing.'),
 ('ppi', 'iron', 'Minor', 'Reduced acid lowers oral iron absorption.',
  'Take iron with vitamin C or review PPI need if anaemia persists.'),
 ('ssri', 'nsaid', 'Moderate', 'SSRI antiplatelet effect + NSAID → GI bleeding.',
  'Add a PPI; prefer paracetamol.'),
 ('ssri', 'anticoagulant', 'Moderate', 'SSRI adds bleeding risk to anticoagulation.',
  'Monitor for bleeding; consider gastroprotection.'),
 ('metronidazole', 'disulfiram_like', 'Moderate', 'Two disulfiram-like agents — flushing/vomiting with any alcohol.',
  'Counsel: strictly no alcohol during and 48 h after.'),
]


def interactions_for(drugs):
    """drugs = list of {code,name,tags}. Return list of interaction dicts (deduped per drug-pair+rule)."""
    out = []
    seen = set()
    n = len(drugs)
    for i in range(n):
        for j in range(i + 1, n):
            a, b = drugs[i], drugs[j]
            if a['code'] == b['code']:
                continue
            ta, tb = a['tags'], b['tags']
            for (x, y, sev, mech, act) in RULES:
                hit = False
                if x == y:
                    if x in ta and y in tb:
                        hit = True
                else:
                    if (x in ta and y in tb) or (x in tb and y in ta):
                        hit = True
                if not hit:
                    continue
                pairkey = tuple(sorted([a['code'], b['code']])) + (x, y)
                if pairkey in seen:
                    continue
                seen.add(pairkey)
                d1, d2 = sorted([a, b], key=lambda d: d['name'])
                out.append({'sev': sev, 'mech': mech, 'action': act,
                            'drug_a': d1['name'], 'drug_b': d2['name'],
                            'pair_class': _pair_label(x, y)})
    return out


def _pair_label(x, y):
    nice = {
     'nsaid': 'NSAID', 'anticoagulant': 'Anticoagulant', 'antiplatelet': 'Antiplatelet', 'warfarin': 'Warfarin',
     'clopidogrel': 'Clopidogrel', 'ppi': 'PPI', 'serotonergic': 'Serotonergic', 'opioid': 'Opioid',
     'benzodiazepine': 'Benzodiazepine', 'cns_depressant': 'CNS depressant', 'ace_arb': 'ACE/ARB',
     'potassium': 'Potassium', 'k_sparing': 'K-sparing diuretic', 'diuretic': 'Diuretic', 'statin': 'Statin',
     'macrolide': 'Macrolide', 'azole_antifungal': 'Azole antifungal', 'fluoroquinolone': 'Fluoroquinolone',
     'methotrexate': 'Methotrexate', 'trimethoprim': 'Trimethoprim', 'qt_prolong': 'QT-prolonging',
     'theophylline': 'Theophylline', 'digoxin': 'Digoxin', 'corticosteroid': 'Corticosteroid',
     'hypoglycemic': 'Antidiabetic', 'levothyroxine': 'Levothyroxine', 'polyvalent_cation': 'Iron/Ca/antacid',
     'polyvalent_sensitive': 'Fluoroquinolone', 'iron': 'Iron', 'metronidazole': 'Metronidazole',
     'disulfiram_like': 'Disulfiram-like',
    }
    if x == y:
        return nice.get(x, x) + ' × ' + nice.get(x, x)
    return nice.get(x, x) + ' × ' + nice.get(y, y)
