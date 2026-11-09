# -*- coding: utf-8 -*-
"""Diagnosis-appropriateness rule-books for the medication-necessity tabs.

Two rule-books:
  * CURATED  — balanced. Broader accepted ICD-10 families per therapeutic class.
               A medication is flagged only if its class is known AND the episode
               carries diagnoses but none in the accepted set. Supplements/vitamins
               are NOT assessed (soft necessity) -> never counted as violations.
  * STRICT   — tighter accepted ICD-10 families, and it DOES assess supplements
               (a supplement with no matching deficiency dx is flagged). Higher
               catch rate, more to triage.

Drug -> therapeutic class is resolved by a hybrid classifier:
  1. ATC code (deterministic, from PH_SFDA_PRODUCTS via SFDA registration no.)
  2. else a brand / scientific-name keyword dictionary (site-specific top drugs)
Unclassifiable drugs -> class None -> "not assessed" (excluded from violations).
"""
import re

# ---- Therapeutic classes -------------------------------------------------
# key: (label, curated_icd_prefixes, strict_icd_prefixes, assess_in_curated)
# ICD prefixes are matched with ^(...) against the episode's ICD-10 codes.
CLASSES = {
 'abx':      ("Antibacterials / antibiotics",
              ["A0","A1","A2","A3","A4","A5","A6","A7","A8","A9","B",
               "J0","J1","J2","J3","J4","H6","H70",
               "K04","K05","K12","K35","K37","K52","K57","K61","K63","K65","K80","K81","K83",
               "N10","N11","N12","N15","N20","N23","N30","N34","N39","N41","N45",
               "N70","N71","N72","N73","N74","N75","N76","N77",
               "L0","M00","M01","M86","O23","O85","O86","O91","R50","Z"],
              ["A0","A1","A3","A4","A5","A6","A7","A8","A9","B",
               "J00","J01","J02","J03","J04","J05","J06","J09","J10","J11","J12","J13","J14","J15","J16","J17","J18","J20","J21","J22","J31","J32",
               "H60","H65","H66","H70","K04","K05","K35","K61","K65","K81",
               "N10","N11","N12","N15","N30","N34","N39","N41","N45","N70","N71","N72","N73","N74","N75","N76","N77",
               "L00","L01","L02","L03","L04","L05","L08","M00","M01","O23","O85","O86","R50"],
              True),
 'antifungal_sys': ("Systemic antifungal",
              ["B35","B36","B37","B38","B39","B44","B48","L01","N76","N77","J","K"],
              ["B35","B36","B37","B44","N76","N77"], True),
 'ppi':      ("Proton-pump inhibitor / acid suppression",
              ["K20","K21","K22","K25","K26","K27","K28","K29","K30","K31","K44","R12","R10"],
              ["K20","K21","K22","K25","K26","K27","K28","K29","K31","R12"], True),
 'antacid':  ("Antacid / reflux",
              ["K20","K21","K22","K25","K26","K27","K28","K29","K30","K31","R12","R10","R11","K59"],
              ["K20","K21","K29","K30","K31","R12"], True),
 'antispasm':("GI / biliary antispasmodic",
              ["K58","K59","K80","K81","K82","R10","N23","N94","K57","R11"],
              ["K58","K59","R10"], True),
 'antiemetic':("Antiemetic / prokinetic",
              ["R11","K52","K59","A0","A09","O2","O21","H81","H82","R42","R10","T","K30","R14","E86","R50","G43"],
              ["R11","A09","O21"], True),
 'nsaid':    ("NSAID / anti-inflammatory analgesic",
              ["M","R52","R51","N94","K08","S","T","G54","H57"],
              ["M","R52","N94"], True),
 'analgesic':("Simple analgesic / antipyretic",
              ["R50","R51","R52","R05","R07","J","K","M","N","H","S","T","G","B","A0","A3","A4","A9","L0","O2","U07","R10","R11","I"],
              ["R50","R51","R52","J00","J01","J02","J03","J04","J05","J06","J10","J11","K08","U07","B34"], True),
 'coldflu':  ("Cold & flu combination",
              ["J00","J01","J02","J03","J04","J06","J10","J11","J30","J31","J32","R05","R07","R50","R51"],
              ["J00","J01","J06","J10","J11","J30","J31","R05","R50"], True),
 'mucolytic':("Mucolytic / cough / expectorant",
              ["J00","J01","J02","J03","J04","J05","J06","J10","J11","J15","J16","J17","J18","J20","J21","J22","J40","J41","J42","J43","J44","J45","J47","J98","R05","R07","A37","B34"],
              ["J20","J21","J40","J41","J42","J44","J45","R05"], True),
 'antihist': ("Antihistamine / antiallergic",
              ["J00","J01","J02","J03","J04","J05","J06","J30","J31","J32","J39","L20","L23","L24","L25","L27","L28","L29","L50","H10","H11","T78","T88","R21","R05","R06","J45","B","L30"],
              ["J30","J31","L20","L23","L50","T78","H10"], True),
 'nasal':    ("Nasal decongestant / topical",
              ["J00","J01","J30","J31","J32","J33","J34","R09","H65","H66"],
              ["J01","J30","J31","J32"], True),
 'bronchod': ("Bronchodilator / inhaled airway",
              ["J20","J21","J40","J41","J42","J43","J44","J45","J46","J47","J98","R06","R05"],
              ["J44","J45","J46"], True),
 'antidiab': ("Antidiabetic",
              ["E10","E11","E12","E13","E14","R73","O24","E66","E28","P70"],
              ["E10","E11","E12","E13","E14","R73","O24"], True),
 'htn_cv':   ("Antihypertensive / cardiovascular",
              ["I10","I11","I12","I13","I15","I20","I21","I22","I23","I24","I25","I48","I49","I50","N18","O10","O11","O13","O14","O16","E27"],
              ["I10","I11","I12","I13","I15","I20","I21","I25","I48","I50","O10","O11","O13","O14","O16"], True),
 'lipid':    ("Lipid-lowering / statin",
              ["E78","I25","I63","I65","I70","G45","E11","I21"],
              ["E78"], True),
 'antithromb':("Antithrombotic / antiplatelet",
              ["I20","I21","I22","I23","I24","I25","I26","I48","I63","I65","I67","I74","I80","I82","G45","Z95","O14","O16"],
              ["I20","I21","I22","I23","I24","I25","I26","I48","I63","I80","I82","G45"], True),
 'thyroid':  ("Thyroid therapy",
              ["E00","E01","E02","E03","E04","E05","E06","E07","O99","C73","E89"],
              ["E01","E02","E03","E05","E06"], True),
 'iron_ana': ("Iron / anti-anaemic",
              ["D50","D51","D52","D53","D62","D63","D64","O99","E53","E56","Z34","Z33","N92","K92"],
              ["D50","D51","D52","D53","D62","D64","O99"], True),
 'folate':   ("Folate / prenatal haematinic",
              ["D52","O","Z34","Z33","Z31","D53","E53"],
              ["D52","O09","O26","Z34","Z33"], True),
 'vitamin':  ("Vitamin / supplement",   # NOT assessed in curated; assessed in strict
              [],
              ["E55","E56","E58","E50","E51","E52","E53","E54","M81","M83","D52","D51","E63","R53","Z34","O26","E64"],
              False),
 'progest':  ("Progestogen / gynae hormone",
              ["N91","N92","N93","N94","N95","N85","N89","E28","O20","O26","Z31","Z30","D25"],
              ["N91","N92","N93","N94","N95","E28","O20","Z31"], True),
 'fertility':("Ovulation / prolactin agent",
              ["N97","E28","E22","N91","N92","N93","E23"],
              ["N97","E28","E22"], True),
 'contra_hrt':("Contraceptive / HRT",
              ["Z30","N95","N91","N92","E28","L70","L68","N94"],
              ["Z30","N95","E28"], True),
 'vag_af':   ("Vaginal antifungal / anti-infective",
              ["N76","N77","N89","B37","A59","N70","N72","N73"],
              ["N76","N77","B37","A59"], True),
 'derm':     ("Dermatological topical",
              ["L","B35","B36","B37","T20","T21","T22","T23","T24","T25","S","H01"],
              ["L01","L02","L03","L08","L20","L21","L23","L24","L25","L28","L30","L70","L71","B35","B36"], True),
 'urinary':  ("Urinary alkaliniser / stone",
              ["N20","N21","N22","N23","R30","R31","R35","R39","N30","N39","E79","M10","M1A"],
              ["N20","N21","N22","N23","E79","M10"], True),
 'simeth':   ("Antiflatulent / simeticone",
              ["R14","R10","K30","K58","K59","P92","R11"],
              ["R14","K30","K58","K59"], True),
 'musc_relax':("Muscle relaxant",
              ["M","R52","G54","S13","S23","S33","T"],
              ["M54","M62","M79","M25","R52"], True),
 'ors':      ("Oral rehydration / electrolytes",
              ["A09","A00","A01","A02","A03","A04","A05","A06","A08","E86","E87","K52","R11","K59"],
              ["A09","E86","E87","K52"], True),
 'eyeent':   ("Eye / ENT topical",
              ["H0","H1","H6","H92","H93","J34","J00","J01"],
              ["H0","H1","H60","H65","H66"], True),
 'venotonic':("Venotonic / haemorrhoid",
              ["I83","I84","I87","K64","O22","O87","I80","R60"],
              ["I83","I84","I87","K64","O22"], True),
 'antidiarr':("Antidiarrhoeal",
              ["A09","A0","K52","K58","K59","R19"],
              ["A09","K52","K58","K59"], True),
 'laxative': ("Laxative",
              ["K59","K56","R19","K58","F98","O99"],
              ["K59","K56"], True),
 'vertigo':  ("Anti-vertigo",
              ["H81","H82","H83","R42","R55","I67"],
              ["H81","H82","R42"], True),
 'bph':      ("BPH / urinary retention",
              ["N40","R33","N32","N31","R39","N13"],
              ["N40","R33","N32"], True),
 'gout':     ("Gout / urate-lowering",
              ["M10","M1A","E79","N20","M11"],
              ["M10","M1A","E79"], True),
 'leukotriene':("Leukotriene antagonist",
              ["J45","J44","J30","J31","J46","J82"],
              ["J45","J30","J44"], True),
}

# ---- ATC prefix -> class (longest prefix wins) ---------------------------
ATC_MAP = [
 ("J01","abx"),("P01AB","abx"),("J04","abx"),("A07AA","abx"),
 ("J02","antifungal_sys"),("D01BA","antifungal_sys"),
 ("A02BC","ppi"),("A02BD","ppi"),
 ("A02A","antacid"),("A02BX","antacid"),
 ("A03B","antispasm"),("A03A","antispasm"),("A03D","antispasm"),
 ("A03F","antiemetic"),("A04","antiemetic"),
 ("M01A","nsaid"),("M02A","nsaid"),("M01C","nsaid"),
 ("N02BE","analgesic"),("N02BA","analgesic"),("N02B","analgesic"),("N02A","analgesic"),
 ("R05","mucolytic"),
 ("R06","antihist"),
 ("R01A","nasal"),("R01","nasal"),
 ("R03","bronchod"),
 ("A10","antidiab"),
 ("C02","htn_cv"),("C03","htn_cv"),("C07","htn_cv"),("C08","htn_cv"),("C09","htn_cv"),("C01D","htn_cv"),
 ("C10","lipid"),
 ("B01","antithromb"),
 ("H03","thyroid"),
 ("B03A","iron_ana"),("B03AA","iron_ana"),("B03AB","iron_ana"),("B03AE","iron_ana"),
 ("B03BB","folate"),("B03BA","folate"),
 ("A11","vitamin"),("A12","vitamin"),("A13","vitamin"),("V06","vitamin"),("B03BA01","folate"),
 ("G03D","progest"),("G03DA","progest"),("G03DB","progest"),
 ("G03GB","fertility"),("L02BG","fertility"),("G02CB","fertility"),
 ("G03A","contra_hrt"),("G03F","contra_hrt"),("G03C","contra_hrt"),("G03H","contra_hrt"),
 ("G01AF","vag_af"),("D01AC","vag_af"),("G01","vag_af"),
 ("D0","derm"),("D1","derm"),("D2","derm"),("D6","derm"),("D7","derm"),("D01AC","derm"),
 ("S01","eyeent"),("S02","eyeent"),("S03","eyeent"),
 ("A06","ors"),("B05BB","ors"),
 ("M03","musc_relax"),
]
ATC_MAP.sort(key=lambda kv: -len(kv[0]))  # longest prefix first

# ---- Brand / scientific keyword -> class ---------------------------------
# keyword matched case-insensitively as a word/substring on the description.
# Order matters: earlier = higher priority.
BRAND_MAP = [
 # antibiotics / antifungals (systemic)
 (["curam","klavox","gloclav","clavodar","clavo","megamox","clavimox","augmentin","amoxil","amoxi","hibiotic","julphamox"],"abx"),
 (["flagyl","anazol","metronidazol","amrizole","dumozol"],"abx"),
 (["ciproxen","ciprogen","ciflox","ciprocin","ciproflacin","ciprofloxacin","ciprodar","ciprobay"],"abx"),
 (["azimac","azi-once","azithromic","azithromycin","zithromax","xithrone"],"abx"),
 (["cefim","cefix","suprax","magnacef","cefixime","zinnat","zinoximor","cefuroxim","cephalexin","keflex","ceclor","cefdinir","cefaclor","cefpodox","velosef","ospexin","ceftin"],"abx"),
 (["apo-doxy","doxycyclin","vibramycin","tabocine"],"abx"),
 (["uvamin","nitrofurant","macrobid"],"abx"),
 (["levoflox","levofloxacin","tavanic"],"abx"),
 (["klacid","clarithromy","erythro","rovamycine","dalacin","clindamyc","fucidin"],"abx"),   # fucidin systemic rare; topical handled below first
 (["diflucan","fluconazol","itraconazol","terbinafin","lamifen","griseofulvin","nystatin"],"antifungal_sys"),
 # acid / GI
 (["hyposec","nexium","peptazol","gasec","esoxo","pantozol","toprazole","omepr","losec","risek","controloc","pariet","zurcazole","esomeprazol","pantoprazol","lansoprazol","rabeprazol","omez","gastrozol"],"ppi"),
 (["epimag","gaviscon","maalox","antacid","mucogel","gastro-","rennie","magaldrate"],"antacid"),
 (["scopinal","buscopan","hyoscine","spasmo","verine","meva","duspatalin","mebeverine","relaxon","drotaverine","no-spa","visceralgine","colofac"],"antispasm"),
 (["dompy","premosan","motilium","domperidone","metoclopram","primperan","vominore","dimenhydrinate","navidoxine","emistop","zoron","zetron","ondansetron","zofran","emetstop","dramamine","postafen"],"antiemetic"),
 # analgesics
 (["xefo","rofenac","cataflam","catafast","voltaren","votrex","diclomax","diclofenac","sapofen","brufen","nurofen","ibuprofen","mobic","meloxicam","fenam","mefenamic","ponstan","naproxen","proxen","napren","celebrex","celecoxib","arcoxia","etoricoxib","ketolgan","ketorolac","feldene","piroxicam","indomethacin","nabuco","dolo-","fastum","olfen"],"nsaid"),
 (["fevadol cold","panadol cold","panadol sinus","fevadol cold & flu","comtrex","panadol night","flu ","coldflu","panadol c","rhinofed"],"coldflu"),
 (["fevadol","panadol","adol","paracetamol","acetaminophen","tylenol","pyral","cetal","revanin","abimol","perfalgan","tempra","calpol","paramol","panadrex"],"analgesic"),
 (["mucosolvan","mucolyte","muxava","solvex","mentex","neorin","respred","kafosed","ambroxol","bromhexine","mucolase","fluimucil","acetylcystein","carbocistein","mucophylline","toplexil","prospan","cough","bisolvon","exocough","rhinathiol","zecuf"],"mucolytic"),
 (["lorine","clara","clarityne","loratadin","levozal","levocetiriz","zyrtec","cetirizin","artiz","xyzal","tilax","aerius","desloratadin","telfast","fexofenadin","allerfin","histazine","claritine","fenistil","avil","polaramine"],"antihist"),
 (["otrivin","tabunex","xylometazol","oxymetazol","afrin","apisal","rhinase","sinomarin","otrix","nasivin"],"nasal"),
 (["ticanase","flusort","flixonase","avamys","nasonex","beconase","budecort nasal","rhinocort","fluticason nasal"],"nasal"),
 (["ventolin","salbutamol","pulmicort","budesonide","seretide","symbicort","foradil","atrovent","berodual","bricanyl","salbovent","farcolin","asthalin","spiriva","flixotide"],"bronchod"),
 (["gliptamet","claz-mr","gliclazid","metformin","glucophage","januvia","sitaglipt","galvus","vildaglipt","amaryl","glimepirid","diamicron","forxiga","jardiance","dapagliflozin","glucovance","cidophage","glibenclam","insulin","lantus","novomix","novorapid","actrapid","mixtard","tresiba","trajenta","onglyza","glucobay"],"antidiab"),
 (["amlocard","amlodipin","diovan","valsartan","exforge","aldomet","methyldopa","concor","bisoprolol","tritace","ramipril","co-diovan","micardis","telmisartan","norvasc","tenormin","atenolol","inderal","propranolol","capoten","captopril","zestril","lisinopril","coversyl","perindopril","cardura","tensomin","hyperium","natrilix","indapamid","adalat","nifedipin","carvedilol","dilatrend","olmesartan","losartan","cozaar","aprovel","irbesartan","betaloc","metoprolol","nebilet","nebivolol","hydralazine"],"htn_cv"),
 (["atorlip","atorvastatin","lipanthyl","fenofibrat","crestor","rosuvastatin","lipitor","simvastatin","zocor","ezetimibe","ezetrol","pravastatin","lescol","fluvastatin","lopid","gemfibrozil","omacor"],"lipid"),
 (["jusprin","aspirin","aspocid","asa ","plavix","clopidogrel","clexane","enoxaparin","xarelto","rivaroxaban","eliquis","apixaban","pradaxa","warfarin","marevan","ticagrelor","brilinta","dipyridamole"],"antithromb"),
 (["eltroxin","euthyrox","levothyrox","thyronorm","thyrox","neomercazole","carbimazole","tapazole","thiamazol","liothyron"],"thyroid"),
 (["ferose","hemadid","ferro-fol","ferrofol","ferrous","haemoton","ferro","haemofer","feroglobin","haemo","iron","cobal","cobalamin","b12","hydroxocobalamin","totema","sangobion"],"iron_ana"),
 (["befolvit","folic","folicare","folvit","folate"],"folate"),
 (["biodal","vit d","vitd","vitamin d","cholecalciferol","d3","davixime","ossofortin","calcinate","calcium","cal-","osteocare","bonvit","centrum","elevit","pronatal","neurobion","vitamin b","b-complex","becozym","supradyn","omegana","omega","omipure","fish oil","surbex","vidaylin","materna","obimin","pharmaton","ginseng","zinc","selenium","magnesium","mag "],"vitamin"),
 (["duphaston","dydrogesteron","primolut","norethister","cyclogest","progesteron","utrogestan","susten","proluton","gestone"],"progest"),
 (["clomid","clomiphene","clomifene","femara","letrozole","dostinex","cabergoline","puregon","gonal","menogon","tamoxifen"],"fertility"),
 (["marvelon","climen","diane","yasmin","yaz","cerazette","microgynon","gynera","cilest","mercilon","logynon","femodene","evra","nuvaring","angeliq","kliogest","livial","tibolone","estrofem","progynova"],"contra_hrt"),
 (["gyno-","mikozal","daktarin","candizol","albothyl","avocin","clotrimazole","canesten","miconazole vag","gynozol","fluomizin","betadine vag"],"vag_af"),
 (["elica","fucicort","fucidin","lamifen","pilocin","fucidin-h","betnovate","dermovate","elocon","mometasone","fusidic","locoid","advantan","travocort","kenacomb","quadriderm","dermofix","fucidine","panthenol","bepanthen","zovirax cream","acyclovir cream","gentamicin cream","tobradex","aczone","differin","adapalene","benzoyl","retin","garamycin","polyfax","dermatop","lacticare","calamine"],"derm"),
 (["alka-ur","uralyte","coli-urinal","uralyt","potassium citrate","polycitra","sodium citrate","cystone","rowatinex","uriflow"],"urinary"),
 (["deflat","disflatyl","simethicone","simeticone","antiflat","infacol","gasrelief","dentinox"],"simeth"),
 (["ors ","babylyte","rehydra","hydran","pedialyte","oral rehydr","glucolyte"],"ors"),
 (["earcalm","otal","otosporin","earex","waxsol"],"eyeent"),
 (["tobrex","tobramycin","optidex","optipred","maxitrol","tobradex","oflox","vigamox","cravit eye","cravit oph","zymar","besivance"],"eyeent"),
 # additions to lift coverage on the volume tail
 (["daflon","procto-glyvenol","proctoglyvenol","diosmin","daffy","venoruton","venotone","doxium","calcium dobesilate"],"venotonic"),
 (["imodium","loperamide","antinal","nifuroxazide","enterogermina","smecta","racecadotril","hidrasec"],"antidiarr"),
 (["agiolax","dulcolax","bisacodyl","movicol","lactulose","duphalac","laxative","forlax","microlax","senna","sennalax","normalax"],"laxative"),
 (["betaserc","betahistine","serc","vertin"],"vertigo"),
 (["omnic","tamsulosin","xatral","alfuzosin","harnal","hytrin","terazosin","flomax","duodart","avodart","dutasteride"],"bph"),
 (["no-uric","allopurinol","zyloric","febuxostat","adenuric","ipuric"],"gout"),
 (["antikast","montelukast","singulair","montiget","montair","lukast"],"leukotriene"),
 # extra brand spellings for existing classes
 (["azitromicina","omacillin","sefarix","hibiotic","unictam","unasyn","zocef","fortum","rocephin","ceftriaxon","cefotax","tazocin","meropenem","tienam"],"abx"),
 (["carboset","flumed","exeltis cough","notussil","sedelut","broncophane"],"mucolytic"),
 (["voltic","emidol","dolamin","pandol","adwiflam","dolphin","dolo","rapidol","panadeine"],"nsaid"),
 (["dapazin","dapxiga","dezeroga","sensityn","dapa ","empa","forxiga","glucodex","gliben","tenaxum"],"antidiab"),
 (["amlor","lofral","lotevan","exforge","tareg","valzaar","concor cor","bystolic","olmetec","benicar","twynsta","sevikar"],"htn_cv"),
 (["fusiderm","fusibact","daivonex","calcipotriol","protopic","tacrolimus oint","elidel","locobase","dermovate"],"derm"),
 (["prolutex","luteran","progest","gestofit"],"progest"),
 (["neuro-b","neurorubine","milgamma","tri-b","vit b12","methylcobal"],"vitamin"),
]

_word = re.compile(r"[a-z0-9\-']+")

def classify(atc, pdesc, sci=None):
    """Return class_key or None. ATC first (deterministic), then brand keyword."""
    a = (atc or "").strip().upper()
    if a:
        for pfx, cls in ATC_MAP:
            if a.startswith(pfx):
                return cls
    text = (" " + (pdesc or "") + " " + (sci or "") + " ").lower()
    for kws, cls in BRAND_MAP:
        for kw in kws:
            if kw in text:
                return cls
    return None

def class_label(cls):
    return CLASSES[cls][0] if cls in CLASSES else "Not assessed"

def icd_prefixes(cls, book):
    """book in {'curated','strict'}."""
    if cls not in CLASSES: return None
    _, cur, strict, assess_cur = CLASSES[cls]
    if book == 'curated':
        return cur if assess_cur else None   # None => not assessed in curated
    return strict

def dx_matches(dx_codes, prefixes):
    if not prefixes: return False
    for d in dx_codes:
        d = (d or "").strip().upper()
        for p in prefixes:
            if d.startswith(p):
                return True
    return False
