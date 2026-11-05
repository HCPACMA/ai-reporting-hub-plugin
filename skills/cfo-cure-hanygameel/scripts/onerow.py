import json,re
from getres import find
def onerow(mk):
    t=json.loads(find(mk))['result']
    for l in t.split('\n'):
        if mk[:12] in l:
            cells=[c for c in re.split(r'\s+\|\s+|^\|\s*|\s*\|$',l) if c!='']
            r,n=cells[0],int(float(cells[1])); parts=r.split('~'); assert len(parts)==n,(len(parts),n); return parts
    raise ValueError('not found')
