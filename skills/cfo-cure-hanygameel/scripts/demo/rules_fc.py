"""DATA.fc — SARIMA(X) invoice revenue forecast + forecast ledger + variance justifications.

Rendering (AlFaihaa_Modeling_Desk.html ~L3501-3629):
  act[key][ym]  = [revenue SAR, visits, refunds SAR (neg), credit-only SAR amount (additive across branches)]
  led[key][]    = [vintage ym, target ym, forecast SAR, lo80, hi80, lo95, hi95, forecast visits,
                   'live'|'backtest', bias correction (ratio), model string]
  just[key]     = {a: actual SAR, var: SAR, pct: ratio, parts: [[label, SAR effect, text]], notes: [text]}
  reg           = model orders / MAPE / bias / recent errors (ratios) / AICc candidates -> untouched
  cal           = [Ramadan days, Eid days, Fridays] -> untouched
"""
import re

_NUM = r'-?\d[\d,]*(?:\.\d+)?'
_RPV = re.compile(r'^(' + _NUM + r') vs (' + _NUM + r') expected')      # "165 vs 147 expected (+12.1%)"
_REF = re.compile(r'^refunds (' + _NUM + r') vs (' + _NUM + r') normal')  # "refunds 15,606 vs 7,496 normal"


def _fmt(orig, v):
    # integers in the source text; keep integer display with thousands separators
    dec = len(orig.split('.')[1]) if '.' in orig else 0
    return f"{v:,.{dec}f}"


def _scale_nums(m, A, s):
    k = A.S(1.0)
    def rep(g):
        o = m.group(g)
        return _fmt(o, float(o.replace(',', '')) * k)
    return s[:m.start(1)] + rep(1) + s[m.end(1):m.start(2)] + rep(2) + s[m.end(2):]


def _part_text(label, s, A):
    if not isinstance(s, str):
        return s
    if label == 'Revenue per visit':
        m = _RPV.match(s)
        if m:
            return _scale_nums(m, A, s)
        return A.text(s, money=True)
    # 'Visits' and anything else: counts only
    return A.text(s, money=False)


def _note(s, A):
    if not isinstance(s, str):
        return s
    m = _REF.match(s)
    if m:
        return _scale_nums(m, A, s)
    return A.text(s, money=False)   # Fridays / Ramadan / Eid day counts


def transform(d, A):
    S = A.S
    # actuals: [rev, visits, refunds, credit amount]
    for key, series in d.get('act', {}).items():
        for ym, v in series.items():
            series[ym] = [S(v[0]), v[1], S(v[2]), S(v[3])] + v[4:]
    # ledger
    for key, rows in d.get('led', {}).items():
        for r in rows:
            for i in (2, 3, 4, 5, 6):
                r[i] = S(r[i])
            # r[7] forecast visits, r[9] bias ratio, r[10] model -> keep
    # justifications
    for key, j in d.get('just', {}).items():
        j['a'] = S(j['a'])
        j['var'] = S(j['var'])
        for p in j.get('parts', []):
            p[1] = S(p[1])
            p[2] = _part_text(p[0], p[2], A)
        j['notes'] = [_note(n, A) for n in j.get('notes', [])]
    # branch labels
    for k, v in d.get('brn', {}).items():
        d['brn'][k] = A.names(v)
    return d
