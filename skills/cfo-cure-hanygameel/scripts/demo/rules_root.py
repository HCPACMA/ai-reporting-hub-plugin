"""root (const DATA): consolidated trend, balance-sheet trend, FY2025 branch split, ratios, data-quality flags."""
import re

_RANGE = re.compile(r'(\d+(?:\.\d+)?)[–-](\d+(?:\.\d+)?)M\b')   # "12–16M" : both ends are money
_BIGK = re.compile(r'\b(\d{4,}(?:\.\d+)?)K\b')                  # "1588K" after scaling -> "1.59M"


def _txt(s, A):
    if not isinstance(s, str):
        return s
    keep = []

    def rng(m):
        a, b = float(m.group(1)), float(m.group(2))
        keep.append('%s–%sM' % (('%g' % A.S(a)), ('%g' % A.S(b))))
        return '\x00%d\x00' % (len(keep) - 1)
    s = _RANGE.sub(rng, s)
    s = A.text(s, money=True)
    s = _BIGK.sub(lambda m: '%.2fM' % (float(m.group(1)) / 1000), s)
    return re.sub('\x00(\\d+)\x00', lambda m: keep[int(m.group(1))], s)


def transform(d, A):
    S = A.S
    for t in d['trend']:
        for k in ('revenue', 'expense', 'net'):
            t[k] = S(t[k])
    for b in d['bs_trend']:
        for k in list(b):
            if k != 'year':
                b[k] = S(b[k])
    for br in d['branch_fy2025'].values():
        for k in list(br):
            br[k] = S(br[k])
    for r in d['ratios'].values():          # ratios stay; net_debt is money
        r['net_debt'] = S(r['net_debt'])
    for f in d['data_quality_flags']:
        for k in ('scope', 'finding', 'action'):
            f[k] = _txt(f[k], A)
    return d
