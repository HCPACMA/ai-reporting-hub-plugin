import re
GEN = re.compile(r'^\s*(?:\(?\s*(?:[A-Z]{1,3}\s?\d{0,2}|\d{1,4}|NEW|New|new|VIP|Gold|Silver|Bronze|Plus|Standard|Class\s*\w+|R|B|C\d?|A\d?|D\d?|E\d?)\s*\)?\s*(?:NEW|New|new)?\s*(?:\(\s*[\w ]{0,8}\))?\s*)?$')
KEEP0 = re.compile(r'^(Cash|Normal|Credit|Staff|Employee|Internal|Private|Individual|INDVIDUL)', re.I)
FICT = re.compile(r'\b(Alpha|Beta|Gamma|Delta|Epsilon|Zeta|Eta|Theta|Iota|Kappa|Lambda|Mu|Nu|Xi|Omicron|Pi|Rho|Sigma|Tau|Upsilon|Phi|Chi|Psi|Omega|Kilo|Lima|Oscar|Quebec|Romeo|Sierra|Victor|Whiskey|Yankee|Zulu|OrbitTPA|VertexTPA|PrismTPA|SummitTPA|HelixTPA|Bank \\w+|Demo Care)\b', re.I)
_cl = {}
def client(seg):
    k = seg.strip().upper()
    if k not in _cl: _cl[k] = 'Client %03d' % (len(_cl) + 1)
    return _cl[k]
def contract(s, A):
    if not isinstance(s, str) or '-' not in s: return A.names(s) if isinstance(s, str) else s
    segs = re.sub(r'Co-operative', 'Cooperative', A.names(s), flags=re.I).split('-')
    out = [segs[0]]
    for seg in segs[1:]:
        if FICT.search(seg) or GEN.match(seg) or re.fullmatch(r'\s*\(.*\)\s*', seg) or KEEP0.match(seg.strip()):
            out.append(A.names(seg))
        elif re.search(r'[A-Za-zء-ي]{3,}', seg):
            out.append(client(seg))
        else:
            out.append(seg)
    return '-'.join(out)
