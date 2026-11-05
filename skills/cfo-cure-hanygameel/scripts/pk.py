import json,re
from getres import find
def items(marker, nfields=None):
    """Return packed rows (split on ~ then |) from the last tool result containing marker.
    Checks the per-bucket count column n when present."""
    t=json.loads(find(marker))['result']
    out=[]; lines=[l for l in t.split('\n') if re.match(r'\|\s*\d+(\.0)?\s*\|',l)]
    for l in lines:
        m=re.match(r'\|\s*(\d+)(?:\.0)?\s*\|\s*(\d+)(?:\.0)?\s*\|(.*)\|[^|]*\|\s*$',l)
        if not m: raise ValueError('bad line '+l[:80])
        n=int(m.group(2)); body=m.group(3).strip()
        parts=body.split('~')
        if len(parts)!=n: raise ValueError(f'bucket {m.group(1)}: {len(parts)} parsed vs {n} counted')
        out+= [p.split('|') for p in parts]
    return out
def parse_text(t):
    out=[]; lines=[l for l in t.split('\n') if re.match(r'\|\s*\d+(\.0)?\s*\|',l)]
    for l in lines:
        m=re.match(r'\|\s*(\d+)(?:\.0)?\s*\|\s*(\d+)(?:\.0)?\s*\|(.*)\|[^|]*\|\s*$',l)
        if not m: raise ValueError('bad line '+l[:80])
        n=int(m.group(2)); parts=m.group(3).strip().split('~')
        if len(parts)!=n: raise ValueError(f'bucket {m.group(1)}: {len(parts)} vs {n}')
        out+=[p.split('|') for p in parts]
    return out
def items_file(path): return parse_text(json.load(open(path))['result'])
