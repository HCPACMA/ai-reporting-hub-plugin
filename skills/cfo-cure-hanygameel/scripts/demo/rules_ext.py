"""ext: extended financials (BS / IS arrays), ratios, DuPont, cash bridge, DCF, LBO, international trading comps."""
import re

# DCF keys that are money (scalars or year arrays); everything else in dcf is a rate/assumption/factor
_DCF_MONEY = {'revenue', 'ebitda', 'tax_zakat', 'capex', 'd_nwc', 'ufcf', 'pv_fcf', 'sum_pv_fcf',
              'terminal_value', 'pv_terminal_value', 'ev', 'comps_cross_check_ev', 'net_debt_fy2025',
              'equity_value'}
_LBO_MONEY = {'entry_ebitda', 'entry_ev', 'entry_debt', 'entry_equity', 'exit_ebitda', 'exit_ev',
              'exit_debt', 'exit_equity'}
_COMPS_MONEY = {'subject_revenue_fy2025', 'subject_ebitda_fy2025', 'implied_ev_via_rev', 'implied_ev_via_ebitda'}

# international comps: original name prefix -> neutral label (same labels anon.py uses where it has one)
_PEER = [
    ('Dr. Sulaiman Al Habib', 'Peer Alpha (Tadawul: P001)'),
    ('Apollo Hospitals', 'Intl Peer A'),
    ('Sigma Healthcare', 'Intl Peer B'),
    ('IHH Healthcare', 'Intl Peer C'),
    ('Fresenius', 'Intl Peer D'),
    ('Rede D', 'Intl Peer E'),
    ('Tenet Healthcare', 'Intl Peer F'),
    ('JD Health', 'Intl Peer G'),
]
_USD_B = re.compile(r'\$(\d+(?:\.\d+)?)B\b')


def _sv(v, A):
    if isinstance(v, list):
        return [_sv(x, A) for x in v]
    return A.S(v)


def transform(d, A):
    S = A.S
    for k in d['bs']:
        d['bs'][k] = _sv(d['bs'][k], A)
    for k in d['is_']:
        d['is_'][k] = _sv(d['is_'][k], A)
    d['ratios_full']['net_debt'] = _sv(d['ratios_full']['net_debt'], A)   # other ratios / dso stay
    # dupont: all ratios -> unchanged
    for k, v in d['cashflow'].items():
        if isinstance(v, list):
            d['cashflow'][k] = _sv(v, A)
    dcf = d['dcf']
    for k in _DCF_MONEY:
        dcf[k] = _sv(dcf[k], A)
    dcf['sensitivity']['grid'] = _sv(dcf['sensitivity']['grid'], A)      # EV grid; wacc_rows / g_cols stay
    lbo = d['lbo']
    for k in _LBO_MONEY:
        lbo[k] = S(lbo[k])
    # lbo multiples, leverage, hold, cagr, moic, irr and IRR grid stay
    c = d['comps']
    for k in _COMPS_MONEY:
        c[k] = S(c[k])
    for p in c['peers']:
        for pre, lab in _PEER:
            if p['name'].startswith(pre):
                p['name'] = lab
                break
        else:
            raise ValueError('unmapped comps peer: ' + p['name'])
        p['note'] = A.names(_USD_B.sub(lambda m: '$%gB' % S(float(m.group(1))), p['note']))
    c['source'] = A.names(c['source'])
    d['source'] = A.names(d['source'])
    return d
