"""Generic walker: scale all numbers unless keep(path) is True; strings via strfn."""
def walk(x, A, keep=lambda p: False, strfn=None, path=()):
    if isinstance(x, dict):
        return {k: walk(v, A, keep, strfn, path + (k,)) for k, v in x.items()}
    if isinstance(x, list):
        return [walk(v, A, keep, strfn, path + (i,)) for i, v in enumerate(x)]
    if isinstance(x, bool) or x is None:
        return x
    if isinstance(x, (int, float)):
        return x if keep(path) else A.S(x)
    if isinstance(x, str):
        return strfn(x, path) if strfn else A.names(x)
    return x
