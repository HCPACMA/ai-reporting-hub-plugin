"""
SKU-level demand forecasting for the top-50 Tier-A SKUs (Al Faihaa inventory
dashboard, item 2 of the AI roadmap). No statsmodels available in this sandbox
(no pypi network access) -> hand-rolled, numpy-only implementations of:
  - Holt-Winters triple exponential smoothing (additive trend + additive
    seasonal, period=12), parameters fit by minimizing in-sample SSE
    (scipy.optimize, L-BFGS-B, bounded [0.01,0.99]) -- used when a SKU has
    >=24 months of history (at least 2 full seasonal cycles).
  - Holt's linear (double exponential smoothing, no seasonal) -- used when
    12-23 months of history.
  - Naive (recent-average, flat forecast, wide band) -- used when <12 months.

This mirrors the spirit of the revenue SARIMA engine (trend + seasonality +
backtested accuracy + bias awareness) but is feasible to fit across 50 series
in one pass without the statsmodels/SARIMAX grid search that engine used.

Output: forecast/forecast_results_v27.json -- one record per SKU with the next-3-
month forecast, a prediction band, trend/seasonality diagnostics, and a
backtest-based accuracy score (holdout = last 6 months, if available).
"""
import json
import math
from datetime import date
import numpy as np
from scipy.optimize import minimize

from raw_series_v27 import RAW

SEASON = 12
HORIZON = 3
CURRENT_PARTIAL_MONTH = "2026-10"  # today is 2026-10-01: drop as incomplete


def parse_series(raw):
    pts = {}
    for tok in raw.split(","):
        ym, qty = tok.split(":")
        pts[ym] = float(qty)
    return pts


def month_range(start, end):
    y, m = int(start[:4]), int(start[5:7])
    ey, em = int(end[:4]), int(end[5:7])
    out = []
    while (y, m) <= (ey, em):
        out.append(f"{y:04d}-{m:02d}")
        m += 1
        if m == 13:
            m = 1
            y += 1
    return out


def densify(pts):
    months = sorted(pts.keys())
    months = [m for m in months if m != CURRENT_PARTIAL_MONTH]
    if not months:
        return [], np.array([])
    full = month_range(months[0], months[-1])
    y = np.array([pts.get(m, 0.0) for m in full], dtype=float)
    return full, y


def add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    m += k
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


# ---------------- Holt (double exponential smoothing, no seasonal) ----------
def holt_fit_forecast(y, horizon):
    n = len(y)

    def sse(params):
        alpha, beta = params
        level = y[0]
        trend = y[1] - y[0] if n > 1 else 0.0
        err = 0.0
        for t in range(1, n):
            f = level + trend
            e = y[t] - f
            err += e * e
            new_level = alpha * y[t] + (1 - alpha) * (level + trend)
            trend = beta * (new_level - level) + (1 - beta) * trend
            level = new_level
        return err

    res = minimize(sse, x0=[0.3, 0.1], bounds=[(0.01, 0.99), (0.01, 0.99)], method="L-BFGS-B")
    alpha, beta = res.x
    level = y[0]
    trend = y[1] - y[0] if n > 1 else 0.0
    resid = []
    for t in range(1, n):
        f = level + trend
        resid.append(y[t] - f)
        new_level = alpha * y[t] + (1 - alpha) * (level + trend)
        trend = beta * (new_level - level) + (1 - beta) * trend
        level = new_level
    resid = np.array(resid) if resid else np.array([0.0])
    sigma = float(np.std(resid))
    fcst = [max(0.0, level + (h + 1) * trend) for h in range(horizon)]
    return fcst, sigma, {"alpha": round(float(alpha), 3), "beta": round(float(beta), 3)}


# ---------------- Holt-Winters additive (trend + seasonal) ------------------
def hw_fit_forecast(y, horizon, season=SEASON):
    n = len(y)
    n_seasons = n // season
    # initial level/trend from first two full seasons
    s1 = y[:season]
    s2 = y[season:2 * season]
    level0 = float(np.mean(s1))
    trend0 = float((np.mean(s2) - np.mean(s1)) / season)
    seasonal0 = [float(y[i] - level0) for i in range(season)]
    # average seasonal indices across all available full seasons for stability
    seas_acc = np.zeros(season)
    seas_cnt = np.zeros(season)
    for i in range(n):
        seas_acc[i % season] += y[i] - (level0 + trend0 * (i - season / 2))
        seas_cnt[i % season] += 1
    seasonal0 = list(seas_acc / np.maximum(seas_cnt, 1))
    # center seasonal indices to sum to 0
    m = np.mean(seasonal0)
    seasonal0 = [s - m for s in seasonal0]

    def run(params, y_arr):
        alpha, beta, gamma = params
        level = level0
        trend = trend0
        seasonal = list(seasonal0)
        fitted = []
        for t in range(len(y_arr)):
            s_idx = t % season
            f = level + trend + seasonal[s_idx]
            fitted.append(f)
            yt = y_arr[t]
            new_level = alpha * (yt - seasonal[s_idx]) + (1 - alpha) * (level + trend)
            new_trend = beta * (new_level - level) + (1 - beta) * trend
            new_seasonal = gamma * (yt - new_level) + (1 - gamma) * seasonal[s_idx]
            seasonal[s_idx] = new_seasonal
            level, trend = new_level, new_trend
        return np.array(fitted), level, trend, seasonal

    def sse(params):
        fitted, _, _, _ = run(params, y)
        e = y - fitted
        return float(np.sum(e * e))

    res = minimize(sse, x0=[0.25, 0.05, 0.25], bounds=[(0.01, 0.9), (0.01, 0.5), (0.01, 0.9)], method="L-BFGS-B")
    alpha, beta, gamma = res.x
    fitted, level, trend, seasonal = run(res.x, y)
    resid = y - fitted
    sigma = float(np.std(resid[-max(12, n // 3):]))  # recent residual volatility
    fcst = []
    for h in range(horizon):
        s_idx = (n + h) % season
        val = level + (h + 1) * trend + seasonal[s_idx]
        fcst.append(max(0.0, float(val)))
    seasonal_strength = float(np.std(seasonal) / (np.std(y) + 1e-9))
    return fcst, sigma, {
        "alpha": round(float(alpha), 3), "beta": round(float(beta), 3), "gamma": round(float(gamma), 3),
        "seasonal_strength": round(seasonal_strength, 3),
    }


def backtest_mape(y, model_fn, holdout=6, season=SEASON):
    n = len(y)
    min_train = season * 2 if model_fn is hw_fit_forecast else 8
    if n < min_train + holdout:
        return None
    train = y[: n - holdout]
    actual = y[n - holdout: n - holdout + 3]  # score on first 3 of the holdout
    if len(actual) == 0 or np.sum(actual) == 0:
        return None
    try:
        fcst, _, _ = model_fn(train, len(actual))
    except Exception:
        return None
    errs = []
    for a, f in zip(actual, fcst):
        if a > 0:
            errs.append(abs(a - f) / a)
    if not errs:
        return None
    return round(float(np.mean(errs)) * 100, 1)


def trend_pct(y, window=12):
    if len(y) < window * 2:
        a, b = y[: len(y) // 2], y[len(y) // 2:]
    else:
        a, b = y[-2 * window:-window], y[-window:]
    ma, mb = np.mean(a), np.mean(b)
    if ma <= 0:
        return 0.0
    return round(float((mb - ma) / ma) * 100, 1)


results = {}
for code, raw in RAW.items():
    pts = parse_series(raw)
    months, y = densify(pts)
    n = len(y)
    last_month = months[-1] if months else None
    rec = {
        "code": code,
        "n_months": n,
        "first_month": months[0] if months else None,
        "last_month": last_month,
        "avg_last12": round(float(np.mean(y[-12:])), 1) if n >= 1 else 0.0,
        "avg_last3": round(float(np.mean(y[-3:])), 1) if n >= 1 else 0.0,
        "trend_pct_yoy_window": trend_pct(y) if n >= 4 else 0.0,
    }
    if n >= 24:
        fcst, sigma, params = hw_fit_forecast(y, HORIZON)
        model = "holt-winters"
        mape = backtest_mape(y, hw_fit_forecast)
    elif n >= 12:
        fcst, sigma, params = holt_fit_forecast(y, HORIZON)
        model = "holt-linear"
        mape = backtest_mape(y, holt_fit_forecast)
    else:
        recent = y[-min(3, n):]
        base = float(np.mean(recent)) if len(recent) else 0.0
        fcst = [base] * HORIZON
        sigma = float(np.std(y)) if n > 1 else base * 0.5
        params = {}
        model = "naive-avg"
        mape = None

    # Robustness guard: a seasonal-index fit can run away on a series with one
    # huge early outlier spike (seasonal component dominated by a one-off).
    # If the model's forecast is wildly inconsistent with recent actuals *and*
    # its own backtest MAPE confirms it's unreliable, blend toward a simple
    # trend-adjusted recent-average fallback instead of trusting it outright.
    avg3 = rec["avg_last12"] if rec["avg_last12"] > 0 else rec["avg_last3"]
    capped = False
    if avg3 > 0 and mape is not None and mape > 80:
        fcst_avg = float(np.mean(fcst))
        if fcst_avg < 0.4 * avg3 or fcst_avg > 2.5 * avg3:
            fallback = max(0.0, avg3 * (1 + rec["trend_pct_yoy_window"] / 100.0 * 0.5))
            fcst = [round(0.5 * f + 0.5 * fallback, 1) for f in fcst]
            sigma = max(sigma, 0.4 * avg3)
            capped = True

    fcst_months = [add_months(last_month, h + 1) for h in range(HORIZON)] if last_month else []
    ci_mult = 1.28  # ~80% band
    if mape is not None and mape < 30 and not capped:
        confidence = "high"
    elif n >= 12 and not capped:
        confidence = "medium"
    else:
        confidence = "low"
    rec.update({
        "model": model + ("+capped" if capped else ""),
        "params": params,
        "forecast_months": fcst_months,
        "forecast": [round(f, 1) for f in fcst],
        "forecast_total_3mo": round(float(sum(fcst)), 1),
        "sigma": round(float(sigma), 1),
        "ci_low_3mo": round(max(0.0, float(sum(fcst) - ci_mult * sigma * math.sqrt(HORIZON))), 1),
        "ci_high_3mo": round(float(sum(fcst) + ci_mult * sigma * math.sqrt(HORIZON)), 1),
        "backtest_mape_pct": mape,
        "confidence": confidence,
    })
    results[code] = rec

with open("forecast_results_v27.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)

# quick sanity summary
n_hw = sum(1 for r in results.values() if r["model"] == "holt-winters")
n_holt = sum(1 for r in results.values() if r["model"] == "holt-linear")
n_naive = sum(1 for r in results.values() if r["model"] == "naive-avg")
mapes = [r["backtest_mape_pct"] for r in results.values() if r["backtest_mape_pct"] is not None]
print(f"holt-winters={n_hw} holt-linear={n_holt} naive={n_naive}")
print(f"backtested SKUs: {len(mapes)}, median MAPE: {np.median(mapes):.1f}%" if mapes else "no backtests")
for code in list(results)[:3]:
    print(code, results[code]["model"], results[code]["forecast"], results[code]["backtest_mape_pct"])
