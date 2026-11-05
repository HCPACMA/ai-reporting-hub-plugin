from gen import walk
def transform(d, A):
    def keep(p):
        if p[0] in ('years', 'layout'): return True
        if p[0] == 'open_vouchers' and (p[-1] == 'n' or (len(p) == 4 and p[1] == 'by' and p[3] == 0)): return True
        return False
    return walk(d, A, keep, lambda s, p: A.text(s, money=False))
