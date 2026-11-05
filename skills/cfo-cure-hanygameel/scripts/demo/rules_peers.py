"""peers: Saudi-listed healthcare peers (TASI / Nomu), excluded names, medians."""

_MONEY = ('mcap', 'rev', 'ebitda', 'op', 'ni', 'netdebt', 'ev')

# ticker -> (neutral name, masked ticker). Labels match anon.py where it already maps the company.
_MAP = {
    '4013': ('Peer Alpha', 'P001'),
    '4002': ('Peer Beta', 'P002'),
    '4004': ('Peer Gamma', 'P003'),
    '4005': ('Peer Epsilon', 'P004'),
    '4007': ('Peer Delta', 'P005'),
    '4009': ('Peer Zeta', 'P006'),
    '4017': ('Listed peer 7', 'P007'),
    '4018': ('Listed peer 8', 'P008'),
    '9546': ('Listed peer 9', 'P009'),
    '9594': ('Listed peer 10', 'P010'),
    '9626': ('Listed peer 11', 'P011'),
    '9620': ('Listed peer 12', 'P012'),
}
_EXCL = {
    '4014': ('Excluded Peer 1', 'X001'),
    '9530': ('Excluded Peer 2', 'X002'),
    '9572': ('Excluded Peer 3', 'X003'),
    '9544': ('Excluded Peer 4', 'X004'),
    '9587': ('Excluded Peer 5', 'X005'),
}
# notes that name places, hospitals or clients that would re-identify the company
_NOTE = {
    '4013': 'Largest private operator — hospitals, medical complexes, day surgery, retail pharmacy, home care',
    '4002': 'Multi-hospital operator with a large outpatient clinic network — regionally weighted',
    '4004': '4 hospitals plus a clinic chain and home care',
    '4005': 'Hospitals and medical centres, home health, stake in a pharma distributor',
    '4007': '2 hospitals with outpatient clinics; a third opening 2026',
    '4009': 'Tertiary hospital network; shares down ~47% over the year',
    '4017': 'Hospitals incl. one abroad, medical centres; manages third-party hospitals',
    '4018': '2 hospitals; 2 more under construction',
    '9546': 'Operates and manages private and government hospitals, plus a pharmacy',
    '9594': 'One general hospital; inpatient capacity up ~60%, 42 clinics added',
    '9626': 'Dental, orthodontics, implants, dermatology — 2 clinics; listed Feb 2026',
}


def transform(d, A):
    for p in d['peers']:
        t = p['ticker']
        if t not in _MAP:
            raise ValueError('unmapped peer ticker ' + t)
        p['name'], p['ticker'] = _MAP[t]
        for k in _MONEY:
            if k in p:
                p[k] = A.S(p[k])
        p['note'] = _NOTE.get(t, A.names(p.get('note')))
        # ev_rev, ev_ebitda, pe, margins, computed, asof, mkt stay
    for e in d['excluded']:
        t = e['ticker']
        if t not in _EXCL:
            raise ValueError('unmapped excluded ticker ' + t)
        e['name'], e['ticker'] = _EXCL[t]
        e['why'] = A.names(e['why'])
    # med (multiples, margins, n), discount, asof: unchanged
    d['source'] = A.names(d['source'])
    return d
