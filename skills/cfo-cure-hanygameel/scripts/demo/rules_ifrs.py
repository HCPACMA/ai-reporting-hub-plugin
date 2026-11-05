"""DATA.ifrs — IFRS 18 statement: ser / fser are monthly GL amounts (money); acc / nat / fn are labels + codes."""


def transform(d, A):
    d['ser'] = {k: [A.S(x) for x in v] for k, v in d['ser'].items()}
    d['fser'] = {k: [A.S(x) for x in v] for k, v in d['fser'].items()}
    d['acc'] = {k: [A.names(x) for x in v] for k, v in d['acc'].items()}
    return d
