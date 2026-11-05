# Lease Audit roll-forward: re-measures the 2123001 / 1252000 / accrual adjustments (J01-J12) at ANY month-end from live ledger figures.
# Called by refresh.py after the 'lease_chk' job. Input: DATA.lease (LD) + live dict from lease_recheck.sql. Output: LD['je']['roll'].
import datetime as dt
r2 = lambda v: round(v + 0.0, 2)
def month_end(d): return (d.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
def months_between(a, b): return (b.year - a.year) * 12 + b.month - a.month          # a,b month-ends
def roll(LD, live, asof):
    Q = LD['je']; T = month_end(asof); ym = '%d-%02d' % (T.year, T.month)
    # ---- expected (contract-supported) unearned revenue at T, credit +
    q_end = month_end(dt.date(T.year, 3 * ((T.month - 1) // 3 + 1), 1)); rem_q = months_between(T, q_end)      # months of the current quarter still ahead
    ghadaf = 54166.67 * rem_q + 100000.0 * rem_q                      # quarterly invoices are issued in advance (F03) and released monthly
    villa_end, mini_end = dt.date(2026, 12, 31), dt.date(2027, 2, 28)
    villa = 5000.0 * max(0, months_between(T, villa_end)); mini = 3260.87 * max(0, months_between(T, mini_end))
    expected = r2(ghadaf + villa + mini)
    ledger = r2(live['a2123001_P'] + live.get('o2123', 0.0))
    n_mini = max(0, months_between(dt.date(2026, 2, 28), T))          # released on the gross (3,750 vs 3,260.87) since March 2026 - F11
    comp = [('J01 legacy balance', -26782.31), ('J02 straight-line asset (Buraydah 2)', 149999.99), ('J03 rounding', 0.07),
            ('J05 apartments receivable', 17999.85), ('J06 villa over-accrual', 4032.26), ('J07 VAT on first instalment', -2934.78),
            ('J08 mini-market gross release (%d months)' % n_mini, r2(489.13 * n_mini))]
    resid = r2(expected - ledger - sum(v for _, v in comp))
    # ---- debit leases: required prepaid at T from the straight-line grid, booked prepaid live
    req = r2(sum(({g['m']: g for g in x['grid']}.get(ym) or {}).get('pre_exp', 0.0) for x in LD['debit']))
    adj09 = r2(req - live['a1252000'])
    wh = [m for m in ('2026%02d' % i for i in range(7, T.month + 1)) if m not in live.get('d11', [])] if T.year == 2026 else []
    ch = 0.0 if live.get('chair_posted') else r2(54342.11 + 12500.0 * max(0, months_between(dt.date(2026, 9, 30), min(T, dt.date(2026, 11, 30)))))
    R = dict(asof=str(T), ledger_2123001=ledger, expected_liability=expected, adjustments=comp, residual=resid,
             required_1252000=req, booked_1252000=live['a1252000'], j09=adj09, j09_2026=r2(adj09 - 29722.08), j09_re=29722.08,
             j10_chairman=ch, j11_warehouse=r2(6197.95 * len(wh)), j11_months=wh, j12=1000.0 if abs(live.get('s0290', 0)) > 0.5 else 0.0)
    Q['roll'] = R
    return R
