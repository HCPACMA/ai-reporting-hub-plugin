import json
ACC=json.load(open('/home/claude/work/gl/accounts.json'))
par=lambda a: ACC.get(a,('-','?'))[0]
def bs_line(a):
    p=par(a)
    if p=='1210000' or p.startswith('122') or p=='1210004': return 'cash'
    if a=='1263000': return 'other_creditors'
    if p in ('1240004','1240000'): return 'ar'
    if p=='12460000': return 'related_party'
    if p=='1250000': return 'prepaid'
    if a=='1262000': return 'lt_loans'
    if p.startswith('126'): return 'other_debtors'
    if p.startswith('13'): return 'unearned'            # sales control accounts
    if p.startswith('3') or p.startswith('4'): return 'pl'
    if a=='2111003': return 'vacation'
    if p=='2111000': return 'empben'
    if p=='2112000': return 'lt_loans'
    if p=='2210000': return 'capital'
    if a=='2123003': return 'zakat_provision'
    if p=='2220000' or p=='2200000': return 're'
    if p=='2230000': return 'statutory_reserve'
    if p=='2240000': return 'aoci'
    if a=='2123001': return 'other_debtors_l'          # liability shown on the debtor line
    if p=='2122000': return 'trade_payables'
    if p in ('2121000','2123000','2123007') or a=='2124000': return 'other_creditors'
    if p=='2126000': return 'due_related_party'
    if p=='2128000': return 'dividends_payable'
    if p in ('1110000','1120000','1111000','1121000'): return 'fixed_net'
    if p.startswith('113'): return 'wip'
    if p=='1230000': return 'inventory'
    return 'other'

