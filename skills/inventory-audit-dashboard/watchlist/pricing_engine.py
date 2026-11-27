"""
pricing_engine.py  (Al Faihaa inventory dashboard, roadmap item 6)

Two jobs, both pure functions of the purchase-invoice (PI) lines:

1. build_blocks(pi_rows, names)  -> re-creates the point-in-time purchasing blocks of the
   dashboard exactly as build_alfaihaa_inventory_2.py (section 8) and
   build_alfaihaa_abc_vendor_cyclecount.py (section 3) compute them, so they can be refreshed
   from a fresh PI pull without re-running the whole (currently blocked) 5-table extract.
   Verified against the published Version-20 blocks (regression in verify_engine.py).

2. build_watchlist(pi_rows, names, as_of)  -> the standing, SAR-ranked watch-list.

pi_row dict keys: org, product, supplier_no, supplier_name, date(datetime), primary_qty,
unit_cost, item_discount, invoice_discount.
"""
import statistics
from collections import defaultdict
from datetime import datetime, timedelta

BRANCH_NAMES = {"01": "Riyadh"}

# ----------------------------------------------------------------------------------------
# 1. Point-in-time blocks (identical logic to the original pipeline)
# ----------------------------------------------------------------------------------------
def build_blocks(pi_rows, names):
    # --- purchases by supplier by month
    pbs = defaultdict(lambda: {"qty": 0.0, "cost": 0.0, "lines": 0})
    for p in pi_rows:
        if p["date"] is None:
            continue
        ym = p["date"].strftime("%Y-%m")
        v = pbs[(p["supplier_no"], p["supplier_name"], ym)]
        v["qty"] += p["primary_qty"]
        v["cost"] += (p["unit_cost"] or 0.0) * p["primary_qty"]
        v["lines"] += 1
    purchases_by_supplier = [
        {"supplier_no": k[0], "supplier_name": k[1], "month": k[2], "qty": round(v["qty"], 2),
         "total_cost": round(v["cost"], 2), "line_count": v["lines"]}
        for k, v in pbs.items()
    ]
    purchases_by_supplier.sort(key=lambda r: (r["month"], -r["total_cost"]))

    # --- product x supplier price matrix
    price_rows = defaultdict(list)
    for p in pi_rows:
        if p["unit_cost"] is None or p["primary_qty"] in (None, 0):
            continue
        price_rows[(p["product"], p["supplier_no"], p["supplier_name"])].append(
            (p["unit_cost"], p["primary_qty"], p["date"]))
    by_product_costs = defaultdict(list)
    for (pc, _, _), lst in price_rows.items():
        for c, q, d in lst:
            by_product_costs[pc].append(c)
    product_median = {pc: statistics.median(cs) for pc, cs in by_product_costs.items() if len(cs) >= 2}
    matrix = []
    for (pc, sno, sname), lst in price_rows.items():
        med = product_median.get(pc)
        outlier_lines = sum(1 for c, _, _ in lst if med and med > 0 and (c > 3 * med or c < med / 3))
        tq = sum(q for _, q, _ in lst)
        tv = sum(c * q for c, q, _ in lst)
        matrix.append({
            "product": pc, "product_name": names.get(pc, pc),
            "supplier_no": sno, "supplier_name": sname,
            "min_price": round(min(c for c, _, _ in lst), 4), "max_price": round(max(c for c, _, _ in lst), 4),
            "avg_price": round(tv / tq, 4) if tq else None,
            "tot_qty": round(tq, 2), "line_cnt": len(lst),
            "last_date": max(d for _, _, d in lst if d).date().isoformat() if any(d for _, _, d in lst) else None,
            "outlier_lines": outlier_lines,
        })
    by_prod = defaultdict(list)
    for m in matrix:
        by_prod[m["product"]].append(m)
    savings = []
    for pc, rows_ in by_prod.items():
        clean = [r for r in rows_ if r["outlier_lines"] == 0 and r["avg_price"] is not None]
        if len(clean) < 2:
            continue
        cheapest = min(clean, key=lambda r: r["avg_price"])
        priciest = max(clean, key=lambda r: r["avg_price"])
        if priciest["avg_price"] <= cheapest["avg_price"]:
            continue
        savings.append({
            "product": pc, "product_name": names.get(pc, pc),
            "cheapest_supplier": cheapest["supplier_name"], "cheapest_price": cheapest["avg_price"],
            "priciest_supplier": priciest["supplier_name"], "priciest_price": priciest["avg_price"],
            "gap_pct": round(100 * (priciest["avg_price"] - cheapest["avg_price"]) / priciest["avg_price"], 1),
        })
    savings.sort(key=lambda r: -(r["gap_pct"] or 0))
    outlier_rows = [m for m in matrix if m["outlier_lines"] > 0]
    price_gap_kpi = round(sum((r["priciest_price"] - r["cheapest_price"]) for r in savings
                              if r["priciest_price"] and r["cheapest_price"]), 2)

    # --- vendor concentration
    sup = defaultdict(lambda: {"spend": 0.0, "qty": 0.0, "lines": 0, "products": set(), "branches": set()})
    for p in pi_rows:
        if p["unit_cost"] is None or p["primary_qty"] is None:
            continue
        a = sup[(p["supplier_no"], p["supplier_name"])]
        a["spend"] += p["unit_cost"] * p["primary_qty"]
        a["qty"] += p["primary_qty"]
        a["lines"] += 1
        a["products"].add(p["product"])
        a["branches"].add(BRANCH_NAMES.get(p["org"], p["org"]))
    total_spend = sum(a["spend"] for a in sup.values())
    slist = []
    for (sno, sname), a in sup.items():
        slist.append({"supplier_no": sno, "supplier_name": sname, "spend": round(a["spend"], 2),
                      "share_pct": round(100.0 * a["spend"] / total_spend, 2) if total_spend else 0.0,
                      "line_count": a["lines"], "product_count": len(a["products"]),
                      "branches": sorted(a["branches"])})
    slist.sort(key=lambda r: -r["spend"])
    cum = 0.0
    for r in slist:
        cum += r["spend"]
        r["cum_pct"] = round(100.0 * cum / total_spend, 2) if total_spend else 0.0
    hhi = round(sum(r["share_pct"] ** 2 for r in slist), 1)
    level = "Low" if hhi < 1500 else ("Moderate" if hhi < 2500 else "High")
    top5 = round(sum(r["spend"] for r in slist[:5]) / total_spend * 100, 2) if total_spend else 0.0
    top10 = round(sum(r["spend"] for r in slist[:10]) / total_spend * 100, 2) if total_spend else 0.0
    psc = defaultdict(list)
    for row in matrix:
        psc[row["product"]].append(row)
    single = []
    for pc, rows_ in psc.items():
        if len(rows_) == 1:
            r = rows_[0]
            single.append({"product": pc, "product_name": r.get("product_name", ""),
                           "supplier_no": r["supplier_no"], "supplier_name": r["supplier_name"],
                           "spend_est": round((r.get("avg_price") or 0) * (r.get("tot_qty") or 0), 2),
                           "qty": r.get("tot_qty"), "line_count": r.get("line_cnt"), "last_date": r.get("last_date")})
    single.sort(key=lambda r: -r["spend_est"])
    single_spend = round(sum(r["spend_est"] for r in single), 2)
    single_share = round(100.0 * single_spend / total_spend, 2) if total_spend else 0.0
    bsp = defaultdict(lambda: defaultdict(float))
    for p in pi_rows:
        if p["unit_cost"] is None or p["primary_qty"] is None:
            continue
        bsp[BRANCH_NAMES.get(p["org"], p["org"])][(p["supplier_no"], p["supplier_name"])] += p["unit_cost"] * p["primary_qty"]
    by_branch = []
    for br, sm in bsp.items():
        bt = sum(sm.values())
        ranked = sorted(sm.items(), key=lambda kv: -kv[1])
        bh = round(sum((100.0 * v / bt) ** 2 for v in sm.values()), 1) if bt else 0.0
        top = ranked[0] if ranked else None
        by_branch.append({"branch": br, "total_spend": round(bt, 2), "supplier_count": len(sm), "hhi": bh,
                          "top_supplier_name": top[0][1] if top else None,
                          "top_supplier_share_pct": round(100.0 * top[1] / bt, 2) if top and bt else None})
    by_branch.sort(key=lambda r: -r["total_spend"])
    return {
        "purchases_by_supplier": purchases_by_supplier,
        "product_supplier_price_matrix": matrix,
        "supplier_savings_opportunities": savings[:200],
        "price_outliers_flagged": outlier_rows[:200],
        "price_gap_savings_identified": price_gap_kpi,
        "vendor": {
            "kpi": {"total_spend_2026": round(total_spend, 2), "supplier_count": len(slist), "hhi": hhi,
                    "concentration_level": level, "top5_share_pct": top5, "top10_share_pct": top10,
                    "single_source_product_count": len(single), "single_source_spend_est": single_spend,
                    "single_source_share_pct": single_share},
            "top_suppliers": slist, "by_branch": by_branch, "single_source_products": single,
        },
    }


# ----------------------------------------------------------------------------------------
# 2. Watch-list
# ----------------------------------------------------------------------------------------
W = 90            # recent window, days
LOOKBACK = 180    # window used to find the cheapest currently-available supplier
PCT_MIN = 0.10    # price-up / gap threshold
SAR_MIN = 300.0   # minimum SAR impact for an alert
ANNUAL = 365.0 / W


def _wavg(lines):
    q = sum(l[1] for l in lines)
    return (sum(l[0] * l[1] for l in lines) / q) if q else None, q


def _alerts_at(clean, cut, names, supname):
    """clean: list of (product, sno, date, qty, price). Returns dict id -> alert, using only lines <= cut."""
    cutd = cut.date() if isinstance(cut, datetime) else cut
    lines = [l for l in clean if l[2] <= cutd]
    win_start = cutd - timedelta(days=W - 1)
    lb_start = cutd - timedelta(days=LOOKBACK - 1)
    by_prod = defaultdict(list)
    for l in lines:
        by_prod[l[0]].append(l)
    out = {}
    sole = {}
    for pc, ls in by_prod.items():
        sup_set = {l[1] for l in ls}
        sole[pc] = (len(sup_set) == 1)
        prices = [l[4] for l in ls]
        med = statistics.median(prices) if len(prices) >= 3 else None
        def is_out(price):
            return bool(med and med > 0 and (price > 3 * med or price < med / 3))
        good = [l for l in ls if not is_out(l[4])]
        # --- C: entry outliers in the recent window
        by_s_out = defaultdict(list)
        for l in ls:
            if l[2] >= win_start and is_out(l[4]):
                by_s_out[l[1]].append(l)
        def dev(l):
            # price far ABOVE the product's median: the amount paid above median (possible overpayment / keying error).
            # price far BELOW the median: usually a unit-of-measure / quantity keying error; the cash at stake is only the
            # recorded line value, so that (not a median-based figure) is the exposure.
            return (l[4] - med) * l[3] if l[4] > med else l[4] * l[3]
        for sno, ols in by_s_out.items():
            exposure = sum(dev(l) for l in ols)
            if exposure >= SAR_MIN:
                worst = max(ols, key=dev)
                aid = f"outlier__{pc}__{sno}"
                out[aid] = {"id": aid, "type": "entry_outlier", "product": pc, "supplier_no": sno,
                            "impact": round(exposure, 2), "lines": len(ols),
                            "direction": "high" if worst[4] > med else "low",
                            "price": round(worst[4], 4), "ref_price": round(med, 4),
                            "date": worst[2].isoformat(), "qty": round(worst[3], 2),
                            "ratio": round(worst[4] / med, 2) if med else None}
        # --- A: same supplier price increase (recent vs earlier, outlier lines excluded)
        by_s = defaultdict(lambda: {"rec": [], "base": []})
        for l in good:
            (by_s[l[1]]["rec"] if l[2] >= win_start else by_s[l[1]]["base"]).append((l[4], l[3], l[2]))
        for sno, d in by_s.items():
            if d["rec"] and d["base"]:
                ba, bq = _wavg(d["base"])
                ra, rq = _wavg(d["rec"])
                if ba and ra and ra >= ba * (1 + PCT_MIN):
                    impact = (ra - ba) * rq
                    if impact >= SAR_MIN:
                        aid = f"priceup__{pc}__{sno}"
                        out[aid] = {"id": aid, "type": "price_up", "product": pc, "supplier_no": sno,
                                    "impact": round(impact, 2), "from": round(ba, 4), "to": round(ra, 4),
                                    "pct": round(100 * (ra / ba - 1), 1), "qty": round(rq, 2),
                                    "n_base": len(d["base"]), "n_rec": len(d["rec"]),
                                    "date": max(x[2] for x in d["rec"]).isoformat(),
                                    "base_date": max(x[2] for x in d["base"]).isoformat()}
        # --- B: cross-supplier gap (what we paid in the window vs the cheapest recently-used supplier)
        lbs = defaultdict(list)
        for l in good:
            if l[2] >= lb_start:
                lbs[l[1]].append((l[4], l[3], l[2]))
        if len(lbs) >= 2:
            avgs = {s: _wavg(v)[0] for s, v in lbs.items()}
            best = min(avgs, key=lambda s: avgs[s])
            best_avg = avgs[best]
            best_last = max(x[2] for x in lbs[best]).isoformat()
            for sno, d in by_s.items():
                if sno == best or not d["rec"]:
                    continue
                ra, rq = _wavg(d["rec"])
                if ra and best_avg and ra >= best_avg * (1 + PCT_MIN):
                    impact = (ra - best_avg) * rq
                    if impact >= SAR_MIN:
                        aid = f"gap__{pc}__{sno}"
                        out[aid] = {"id": aid, "type": "supplier_gap", "product": pc, "supplier_no": sno,
                                    "impact": round(impact, 2), "paid": round(ra, 4), "best": round(best_avg, 4),
                                    "best_supplier_no": best, "best_last_date": best_last,
                                    "pct": round(100 * (ra / best_avg - 1), 1), "qty": round(rq, 2),
                                    "date": max(x[2] for x in d["rec"]).isoformat()}
    for a in out.values():
        a["product_name"] = names.get(a["product"], a["product"])
        a["supplier_name"] = supname.get(a["supplier_no"], a["supplier_no"])
        if a.get("best_supplier_no"):
            a["best_supplier_name"] = supname.get(a["best_supplier_no"], a["best_supplier_no"])
        a["annualized"] = round(a["impact"] * ANNUAL, 2)
        a["sole_source"] = bool(sole.get(a["product"]))
    return out


def _unique_sar(alerts):
    best = {}
    for a in alerts.values():
        k = (a["product"], a["supplier_no"])
        best[k] = max(best.get(k, 0.0), a["impact"])
    return round(sum(best.values()), 2)


def build_watchlist(pi_rows, names, as_of, supname=None, prev_days=30):
    supname = supname or {}
    for p in pi_rows:
        supname.setdefault(p["supplier_no"], p["supplier_name"])
    clean = [(p["product"], p["supplier_no"], p["date"].date(), p["primary_qty"], p["unit_cost"])
             for p in pi_rows if p["date"] and p["unit_cost"] and p["unit_cost"] > 0
             and p["primary_qty"] and p["primary_qty"] > 0]
    zero_lines = sum(1 for p in pi_rows if (p["unit_cost"] or 0) <= 0 or not p["primary_qty"] or p["primary_qty"] <= 0)
    as_of_d = as_of.date() if isinstance(as_of, datetime) else as_of
    cur = _alerts_at(clean, as_of_d, names, supname)
    prev_cut = as_of_d - timedelta(days=prev_days)
    prev = _alerts_at(clean, prev_cut, names, supname)
    for aid, a in cur.items():
        p = prev.get(aid)
        if p is None:
            a["chg"] = "new"
            a["prev_impact"] = 0.0
        else:
            a["prev_impact"] = p["impact"]
            if a["impact"] >= p["impact"] * 1.25 and a["impact"] - p["impact"] >= 200:
                a["chg"] = "worse"
            elif a["impact"] <= p["impact"] * 0.75 and p["impact"] - a["impact"] >= 200:
                a["chg"] = "better"
            else:
                a["chg"] = "same"
    cleared = [aid for aid in prev if aid not in cur]
    alerts = sorted(cur.values(), key=lambda a: -a["impact"])

    # weekly trend of the unique SAR impact (same rules, rolling cut)
    trend = []
    first = min(l[2] for l in clean)
    cut = as_of_d
    cuts = []
    while cut >= first + timedelta(days=W + 30) and len(cuts) < 18:
        cuts.append(cut)
        cut -= timedelta(days=7)
    for c in reversed(cuts):
        al = _alerts_at(clean, c, names, supname)
        byt = defaultdict(float)
        for a in al.values():
            byt[a["type"]] += a["impact"]
        trend.append({"cut": c.isoformat(), "alerts": len(al), "unique_sar": _unique_sar(al),
                      "price_up": round(byt["price_up"], 2), "supplier_gap": round(byt["supplier_gap"], 2),
                      "entry_outlier": round(byt["entry_outlier"], 2)})

    # supplier table: recent window vs the previous window
    win_start = as_of_d - timedelta(days=W - 1)
    prev_start = win_start - timedelta(days=W)
    sp = defaultdict(lambda: {"rec": 0.0, "prev": 0.0, "lines": 0, "products": set()})
    tot_rec = tot_prev = 0.0
    for pc, sno, d, q, c in clean:
        if d >= win_start:
            sp[sno]["rec"] += q * c; sp[sno]["lines"] += 1; sp[sno]["products"].add(pc); tot_rec += q * c
        elif d >= prev_start:
            sp[sno]["prev"] += q * c; tot_prev += q * c
    first_seen = {}
    for pc, sno, d, q, c in clean:
        if sno not in first_seen or d < first_seen[sno]:
            first_seen[sno] = d
    agg = defaultdict(lambda: {"price_up": 0.0, "supplier_gap": 0.0, "entry_outlier": 0.0, "n": 0})
    for a in alerts:
        g = agg[a["supplier_no"]]
        g[a["type"]] += a["impact"]; g["n"] += 1
    suppliers = []
    for sno, s in sp.items():
        g = agg.get(sno, {"price_up": 0.0, "supplier_gap": 0.0, "entry_outlier": 0.0, "n": 0})
        suppliers.append({
            "supplier_no": sno, "supplier_name": supname.get(sno, sno),
            "spend_90d": round(s["rec"], 2), "spend_prev_90d": round(s["prev"], 2),
            "share_pct": round(100 * s["rec"] / tot_rec, 2) if tot_rec else 0.0,
            "share_prev_pct": round(100 * s["prev"] / tot_prev, 2) if tot_prev else 0.0,
            "lines": s["lines"], "products": len(s["products"]),
            "new_supplier": first_seen.get(sno, as_of_d) >= win_start,
            "alerts": g["n"], "price_up_sar": round(g["price_up"], 2),
            "gap_sar": round(g["supplier_gap"], 2), "outlier_sar": round(g["entry_outlier"], 2),
        })
    suppliers.sort(key=lambda r: -r["spend_90d"])

    # sole-source exposure (single supplier across all 2026 lines), with price trend
    all_sup = defaultdict(set)
    for pc, sno, d, q, c in clean:
        all_sup[pc].add(sno)
    sole_rows = []
    byp = defaultdict(list)
    for l in clean:
        byp[l[0]].append(l)
    alert_prod_sup = {(a["product"], a["supplier_no"]): a for a in alerts if a["type"] == "price_up"}
    for pc, sset in all_sup.items():
        if len(sset) != 1:
            continue
        ls = byp[pc]
        rec = [(l[4], l[3], l[2]) for l in ls if l[2] >= win_start]
        if not rec:
            continue
        base = [(l[4], l[3], l[2]) for l in ls if l[2] < win_start]
        ra, rq = _wavg(rec)
        ba = _wavg(base)[0] if base else None
        sno = next(iter(sset))
        sole_rows.append({"product": pc, "product_name": names.get(pc, pc), "supplier_no": sno,
                          "supplier_name": supname.get(sno, sno), "spend_90d": round(ra * rq, 2),
                          "price_now": round(ra, 4), "price_before": round(ba, 4) if ba else None,
                          "pct": round(100 * (ra / ba - 1), 1) if ba else None,
                          "last_date": max(x[2] for x in rec).isoformat(),
                          "days_since": (as_of_d - max(x[2] for x in rec)).days})
    sole_rows.sort(key=lambda r: -r["spend_90d"])
    sole_total_90d = round(sum(r["spend_90d"] for r in sole_rows), 2)

    by_type = defaultdict(lambda: {"n": 0, "sar": 0.0})
    for a in alerts:
        by_type[a["type"]]["n"] += 1
        by_type[a["type"]]["sar"] += a["impact"]
    kpi = {
        "as_of": as_of_d.isoformat(), "window_start": win_start.isoformat(), "window_days": W,
        "prev_as_of": prev_cut.isoformat(),
        "alerts": len(alerts), "unique_sar_90d": _unique_sar(cur),
        "unique_sar_annualized": round(_unique_sar(cur) * ANNUAL, 2),
        "new_alerts": sum(1 for a in alerts if a["chg"] == "new"),
        "worse_alerts": sum(1 for a in alerts if a["chg"] == "worse"),
        "cleared_alerts": len(cleared),
        "prev_unique_sar": _unique_sar(prev),
        "by_type": {k: {"n": v["n"], "sar": round(v["sar"], 2)} for k, v in by_type.items()},
        "spend_90d": round(tot_rec, 2), "spend_prev_90d": round(tot_prev, 2),
        "lines_90d": sum(s["lines"] for s in suppliers),
        "suppliers_90d": len(suppliers), "new_suppliers_90d": sum(1 for s in suppliers if s["new_supplier"]),
        "sole_source_products_90d": len(sole_rows), "sole_source_spend_90d": sole_total_90d,
        "sole_source_share_pct": round(100 * sole_total_90d / tot_rec, 2) if tot_rec else 0.0,
        "sole_source_alerts": sum(1 for a in alerts if a["sole_source"]),
        "zero_or_negative_lines_excluded": zero_lines, "total_lines": len(pi_rows),
    }
    return {"kpi": kpi, "alerts": alerts, "trend": trend, "suppliers": suppliers,
            "sole_source": sole_rows[:60], "cleared": cleared}
