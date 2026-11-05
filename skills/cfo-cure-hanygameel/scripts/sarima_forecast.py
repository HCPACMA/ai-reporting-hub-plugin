"""
CFO-Cure · Invoice revenue forecasting with seasonal ARIMA (SARIMA / SARIMAX)
---------------------------------------------------------------------------
Input : monthly_invoice_revenue.csv  (built from EXSYS / Cure invoice tables via Cure MCP)
Output: forecast_ledger.csv   – every forecast ever issued (vintage × series × target month), append-only
        model_registry.json   – model chosen per series at each run, with backtest error and bias factor
        fc_payload.json       – compact payload for the Modeling Desk "Forecasting" section

Method (auto-enhancing):
  1. Series = branch × {cash, credit} + group cash / credit / total, log-transformed.
  2. Exogenous calendar: Ramadan days, Eid holiday days, Fridays, COVID lockdown dummy (SARIMAX).
  3. Candidate orders (p,d,q)(P,D,Q)12 ranked by AICc on data up to T-12; the best 6 are
     re-scored by a rolling-origin backtest over the last 12 complete months (1-step and 3-step MAPE).
     The winner is the spec with the lowest blended MAPE.  Re-run every month → the model is
     re-selected on the newest errors (this is the "auto-enhance" loop).
  4. Bias correction: if the winner's last 6 one-step errors share a sign ≥5/6 times and the mean
     error is >2 %, forecasts are scaled by (1 − mean error).  Logged in the registry.
  5. Vintages: on first run the backtest origins are written to the ledger as reconstructed
     vintages ("backtest"); every later run appends a "live" vintage.  Rows already in the ledger
     are never overwritten, so forecast-vs-actual variance stays auditable.
  6. Visits (episodes) are forecast with the same spec so variance can be split into
     volume (visits) and rate (revenue per visit).

Usage:  python sarima_forecast.py <folder>        (folder holds monthly_invoice_revenue.csv)
"""
import sys, os, json, math, warnings, itertools, datetime as dt
import numpy as np, pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")

FOLDER = sys.argv[1] if len(sys.argv) > 1 else "."
TODAY = dt.date.today()
H = 16                      # forecast horizon (months)
BT = 12                     # backtest window (months)
BRN = {"01": "Riyadh", "02": "Bur-1", "03": "Bur-2", "04": "Rafha"}

# ---------------------------------------------------------------- calendar (Umm al-Qura, approximate)
RAMADAN = {2019: "2019-05-06", 2020: "2020-04-24", 2021: "2021-04-13", 2022: "2022-04-02", 2023: "2023-03-23",
           2024: "2024-03-11", 2025: "2025-03-01", 2026: "2026-02-18", 2027: "2027-02-08", 2028: "2028-01-28"}
FITR = {2019: "2019-06-04", 2020: "2020-05-24", 2021: "2021-05-13", 2022: "2022-05-02", 2023: "2023-04-21",
        2024: "2024-04-10", 2025: "2025-03-30", 2026: "2026-03-20", 2027: "2027-03-10", 2028: "2028-02-27"}
ADHA = {2019: "2019-08-11", 2020: "2020-07-31", 2021: "2021-07-20", 2022: "2022-07-09", 2023: "2023-06-28",
        2024: "2024-06-16", 2025: "2025-06-06", 2026: "2026-05-27", 2027: "2027-05-16", 2028: "2028-05-05"}

def day_flags():
    ram, eid = set(), set()
    for y, s in RAMADAN.items():
        d0 = dt.date.fromisoformat(s); d1 = dt.date.fromisoformat(FITR[y])
        d = d0
        while d < d1: ram.add(d); d += dt.timedelta(1)
    for dct, n in ((FITR, 4), (ADHA, 5)):
        for s in dct.values():
            d = dt.date.fromisoformat(s)
            for i in range(n): eid.add(d + dt.timedelta(i))
    return ram, eid
RAM, EID = day_flags()

def exog_for(periods):
    out = []
    for p in periods:
        y, m = p.year, p.month
        d = dt.date(y, m, 1); days = []
        while d.month == m: days.append(d); d += dt.timedelta(1)
        out.append([sum(x in RAM for x in days), sum(x in EID for x in days),
                    sum(x.weekday() == 4 for x in days), 1.0 if (y == 2020 and m in (4, 5)) else 0.0])
    return pd.DataFrame(out, index=periods, columns=["ramadan", "eid", "fridays", "covid"])

# ---------------------------------------------------------------- data
df = pd.read_csv(os.path.join(FOLDER, "monthly_invoice_revenue.csv"), dtype={"branch": str, "ym": str})
df["period"] = pd.PeriodIndex(df["ym"].str[:4] + "-" + df["ym"].str[4:], freq="M")
cur = pd.Period(TODAY, freq="M")
last_full = cur - 1
series = {}
for br, g in df.groupby("branch"):
    g = g.set_index("period").sort_index()
    for k in ("cash", "credit"):
        series[f"{br}|{k}"] = (g[k], g["eps_" + k])
tot = df.groupby("period")[["cash", "credit", "eps_cash", "eps_credit"]].sum().sort_index()
series["ALL|cash"] = (tot["cash"], tot["eps_cash"])
series["ALL|credit"] = (tot["credit"], tot["eps_credit"])
series["ALL|total"] = (tot["cash"] + tot["credit"], tot["eps_cash"] + tot["eps_credit"])

def clean(s):
    s = s.copy()
    s = s[s.index <= last_full]
    # trim leading months before the branch really opened (first month ≥ 20 % of median)
    med = s[s > 0].median()
    first = s[s >= 0.2 * med].index.min()
    s = s[s.index >= first]
    full = pd.period_range(s.index.min(), last_full, freq="M")
    s = s.reindex(full).interpolate().bfill().ffill()
    return s.clip(lower=1.0)

ORDERS = [(p, d, q) for p in (0, 1, 2) for d in (0, 1) for q in (0, 1, 2)]
SORDERS = [(P, D, Q, 12) for P in (0, 1) for D in (0, 1) for Q in (0, 1)]

def fit(y, x, order, sorder):
    m = SARIMAX(np.log(y), exog=x, order=order, seasonal_order=sorder, trend="c" if (order[1] + sorder[1]) == 0 else "n",
                enforce_stationarity=False, enforce_invertibility=False)
    return m.fit(disp=False, maxiter=200)

def aicc(r, n):
    k = len(r.params)
    return r.aic + (2 * k * (k + 1)) / max(1, n - k - 1)

def fc(res, xf, steps, bias=0.0):
    f = res.get_forecast(steps=steps, exog=xf)
    mu = f.predicted_mean; ci80 = f.conf_int(alpha=0.2); ci95 = f.conf_int(alpha=0.05)
    k = (1 - bias)
    return (np.exp(mu) * k, np.exp(ci80.iloc[:, 0]) * k, np.exp(ci80.iloc[:, 1]) * k,
            np.exp(ci95.iloc[:, 0]) * k, np.exp(ci95.iloc[:, 1]) * k)

def backtest(y, X, spec, origins, steps=3):
    e1, e3 = [], []
    for o in origins:
        tr = y[y.index < o]
        if len(tr) < 30: continue
        try:
            r = fit(tr, X.loc[tr.index], *spec)
            f = fc(r, X.loc[pd.period_range(o, periods=steps, freq="M")], steps)[0]
        except Exception:
            continue
        a = y.reindex(f.index)
        if not np.isnan(a.iloc[0]): e1.append((f.iloc[0] - a.iloc[0]) / a.iloc[0])
        if len(a.dropna()) == steps: e3.append(float(np.mean(np.abs((f.values - a.values) / a.values))))
    return e1, e3

def select(y, X):
    n = len(y); tr = y.iloc[:-BT] if n > 48 else y
    ranked = []
    for o, s in itertools.product(ORDERS, SORDERS):
        if s[1] == 1 and len(tr) < 40: continue
        try:
            r = fit(tr, X.loc[tr.index], o, s); ranked.append((aicc(r, len(tr)), o, s))
        except Exception:
            pass
    ranked.sort(key=lambda t: t[0])
    origins = list(y.index[-BT:])
    best = None
    for _, o, s in ranked[:6]:
        e1, e3 = backtest(y, X, (o, s), origins)
        if not e1: continue
        mape1 = float(np.mean(np.abs(e1))); mape3 = float(np.mean(e3)) if e3 else mape1
        score = 0.6 * mape1 + 0.4 * mape3
        if best is None or score < best["score"]:
            best = {"order": o, "sorder": s, "score": score, "mape1": mape1, "mape3": mape3, "e1": e1}
    return best, ranked[:6]

# ---------------------------------------------------------------- ledger
LEDGER = os.path.join(FOLDER, "forecast_ledger.csv")
cols = ["vintage", "kind", "series", "target", "forecast", "lo80", "hi80", "lo95", "hi95", "fc_eps", "model", "bias", "issued"]
ledger = pd.read_csv(LEDGER, dtype=str) if os.path.exists(LEDGER) else pd.DataFrame(columns=cols)
have = set(zip(ledger["vintage"], ledger["series"], ledger["target"])) if len(ledger) else set()
first_run = len(ledger) == 0
new_rows = []
registry = {"run": TODAY.isoformat(), "last_full": str(last_full), "series": {}}

horizon = pd.period_range(last_full + 1, periods=H, freq="M")
for key, (rev, eps) in series.items():
    y = clean(rev); e = clean(eps)
    allp = pd.period_range(y.index.min(), horizon[-1], freq="M")
    X = exog_for(allp)
    best, top = select(y, X)
    if best is None:
        continue
    spec = (best["order"], best["sorder"])
    e1 = best["e1"][-6:]
    mb = float(np.mean(e1)) if e1 else 0.0
    same = max(sum(x > 0 for x in e1), sum(x < 0 for x in e1)) if e1 else 0
    bias = mb if (abs(mb) > 0.02 and same >= 5) else 0.0
    mname = f"SARIMAX{best['order']}x{best['sorder'][:3]}12 + calendar"
    registry["series"][key] = {"model": mname, "order": best["order"], "sorder": best["sorder"],
                               "mape1": round(best["mape1"], 4), "mape3": round(best["mape3"], 4),
                               "bias": round(bias, 4), "recent_err": [round(x, 4) for x in e1],
                               "candidates": [[round(a, 1), o, s] for a, o, s in top]}
    # visits model: same spec on episodes
    try:
        re_ = fit(e, X.loc[e.index], *spec); ef = fc(re_, X.loc[horizon], H)[0]
    except Exception:
        ef = pd.Series([np.nan] * H, index=horizon)
    # live vintage
    r = fit(y, X.loc[y.index], *spec)
    f, l8, h8, l9, h9 = fc(r, X.loc[horizon], H, bias)
    vint = str(last_full + 1)
    for i, p in enumerate(horizon):
        if (vint, key, str(p)) in have: continue
        new_rows.append([vint, "live", key, str(p), f.iloc[i], l8.iloc[i], h8.iloc[i], l9.iloc[i], h9.iloc[i], ef.iloc[i], mname, bias, TODAY.isoformat()])
    # reconstructed vintages (first run only): origins over the last 20 months, 12 steps each
    if first_run:
        for o in pd.period_range(last_full - 19, last_full, freq="M"):
            tr = y[y.index < o]; tre = e[e.index < o]
            if len(tr) < 30: continue
            hz = pd.period_range(o, periods=12, freq="M")
            try:
                rr = fit(tr, X.loc[tr.index], *spec); ff, a8, b8, a9, b9 = fc(rr, X.loc[hz], 12)
                ree = fit(tre, X.loc[tre.index], *spec); eef = fc(ree, X.loc[hz], 12)[0]
            except Exception:
                continue
            for i, p in enumerate(hz):
                new_rows.append([str(o), "backtest", key, str(p), ff.iloc[i], a8.iloc[i], b8.iloc[i], a9.iloc[i], b9.iloc[i], eef.iloc[i], mname, 0.0, TODAY.isoformat()])
    print(key, mname, "MAPE1 %.1f%%" % (100 * best["mape1"]), "bias %.1f%%" % (100 * bias), flush=True)

if new_rows:
    add = pd.DataFrame(new_rows, columns=cols)
    for c in ("forecast", "lo80", "hi80", "lo95", "hi95", "fc_eps"):
        add[c] = add[c].astype(float).round(0)
    ledger = pd.concat([ledger, add.astype(str)], ignore_index=True)
ledger.to_csv(LEDGER, index=False)
json.dump(registry, open(os.path.join(FOLDER, "model_registry.json"), "w"), indent=1, default=str)
print("ledger rows", len(ledger), "new", len(new_rows))
