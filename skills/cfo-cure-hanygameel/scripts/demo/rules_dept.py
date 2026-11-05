"""DATA.dept — department revenue / cost, FY2025 and FY2026 YTD."""
MONEY = ('cash', 'credit', 'revenue', 'cost_dr', 'cost_cr')
LISTS = ('departments_2025', 'departments_2026ytd', 'all_2025', 'all_2026ytd')


def transform(d, A):
    d['note'] = A.text(d.get('note'), money=True)      # "SAR 115,806 ... SAR 66,000" scaled
    for lk in LISTS:
        for r in d.get(lk) or []:
            for k in MONEY:
                if k in r:
                    r[k] = A.S(r[k])
            r['name'] = A.names(r.get('name'))
            r['name_ar'] = A.names(r.get('name_ar'))
    return d
