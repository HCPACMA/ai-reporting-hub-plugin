import json, math, shutil, os

XYZ = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad/xyz"
UP = XYZ

abc_items = json.load(open(f"{UP}/abc_items_v27.json", encoding="utf-8"))
flags = json.load(open(f"{UP}/flag_sets_v27.json", encoding="utf-8"))
ov_set, sm_set = flags["overstock"], flags["slow_moving"]

stats = {k: tuple(v) for k, v in json.load(open(f"{XYZ}/stats_v27.json")).items()}

# --- parameters (all surfaced on the dashboard; H and service levels are user-adjustable there) ---
MIN_HISTORY = 12          # months of eligible history needed to classify variability
X_MAX, Y_MAX = 0.5, 1.0   # CV cut-offs: X <= 0.5 < Y <= 1.0 < Z
DEFAULT_H = 3.0           # protection interval (replenishment lead time + review), months -- ASSUMPTION, user-adjustable
SERVICE_Z = {             # target service level -> z, by ABC x XYZ cell
    "AX": 2.05, "AY": 1.88, "AZ": 1.65,
    "BX": 1.88, "BY": 1.65, "BZ": 1.28,
    "CX": 1.65, "CY": 1.28, "CZ": 0.84,
}
SERVICE_PCT = {"AX": 98, "AY": 97, "AZ": 95, "BX": 97, "BY": 95, "BZ": 90, "CX": 95, "CY": 90, "CZ": 80}

items = []
for it in abc_items:
    pc = it["product"]
    n_eff, n_nz, mean, sd = stats[pc]
    qty, value = it["qty"], it["value"]
    unit_cost = (value / qty) if qty else 0.0
    if n_eff < MIN_HISTORY:
        xyz, cv = "N", None            # too new to classify
    elif mean <= 0:
        xyz, cv = "D", None            # no demand in the window
    else:
        cv = sd / mean
        xyz = "X" if cv <= X_MAX else ("Y" if cv <= Y_MAX else "Z")
    items.append({
        "product": pc, "product_name": it["product_name"], "tier": it["tier"], "xyz": xyz,
        "cell": it["tier"] + xyz,
        "qty": qty, "value": round(value, 2), "unit_cost": round(unit_cost, 4),
        "mean_m": mean, "sd_m": sd, "cv": None if cv is None else round(cv, 3),
        "n_months": n_eff, "nz_months": n_nz,
        "intermittent": bool(n_eff and (n_nz / n_eff) < 0.5 and xyz in ("X", "Y", "Z")),
        "overstock_flag": pc in ov_set, "slow_flag": pc in sm_set,
        "branches": it["branches"],
    })

def policy(it, H):
    """Order-up-to level = mean*H + z*sd*sqrt(H); only for classifiable demand."""
    if it["xyz"] not in ("X", "Y", "Z"):
        return None
    z = SERVICE_Z[it["cell"]]
    return it["mean_m"] * H + z * it["sd_m"] * math.sqrt(H)

for it in items:
    tgt = policy(it, DEFAULT_H)
    it["target_qty"] = None if tgt is None else round(tgt, 1)
    if tgt is None:
        it["excess_qty"] = None; it["excess_value"] = None; it["at_risk"] = False
    else:
        ex = max(0.0, it["qty"] - tgt)
        it["excess_qty"] = round(ex, 1)
        it["excess_value"] = round(ex * it["unit_cost"], 2)
        it["at_risk"] = bool(it["qty"] < it["mean_m"] * DEFAULT_H)

# --- matrix ---
cells = {}
for t in "ABC":
    for x in "XYZ":
        cells[t + x] = {"cell": t + x, "tier": t, "xyz": x, "skus": 0, "value": 0.0, "excess_value": 0.0, "at_risk": 0}
extra = {}
for t in "ABC":
    for x in "ND":
        extra[t + x] = {"cell": t + x, "tier": t, "xyz": x, "skus": 0, "value": 0.0}
for it in items:
    c = cells.get(it["cell"])
    if c is not None:
        c["skus"] += 1; c["value"] += it["value"]
        c["excess_value"] += it["excess_value"] or 0.0
        c["at_risk"] += 1 if it["at_risk"] else 0
    else:
        e = extra[it["cell"]]; e["skus"] += 1; e["value"] += it["value"]
for c in list(cells.values()) + list(extra.values()):
    c["value"] = round(c["value"], 2)
    if "excess_value" in c:
        c["excess_value"] = round(c["excess_value"], 2)
    c["service_pct"] = SERVICE_PCT.get(c["cell"])

total_value = sum(i["value"] for i in items)
classified = [i for i in items if i["xyz"] in ("X", "Y", "Z")]
kpi = {
    "skus_ranked": len(items),
    "skus_classified": len(classified),
    "skus_no_demand": sum(1 for i in items if i["xyz"] == "D"),
    "skus_new": sum(1 for i in items if i["xyz"] == "N"),
    "value_no_demand": round(sum(i["value"] for i in items if i["xyz"] == "D"), 2),
    "value_new": round(sum(i["value"] for i in items if i["xyz"] == "N"), 2),
    "total_value": round(total_value, 2),
    "excess_value_default": round(sum(i["excess_value"] or 0 for i in items), 2),
    "excess_skus_default": sum(1 for i in items if (i["excess_value"] or 0) > 0),
    "at_risk_skus_default": sum(1 for i in items if i["at_risk"]),
    "az_skus": cells["AZ"]["skus"], "az_value": cells["AZ"]["value"],
    "default_H": DEFAULT_H, "min_history_months": MIN_HISTORY, "window": "2024-10 to 2026-09 (24 months)",
    "cv_cutoffs": {"X": X_MAX, "Y": Y_MAX},
}
sensitivity = []
for H in (1.0, 2.0, 3.0, 4.0, 6.0):
    ex_tot, ex_n, risk_n = 0.0, 0, 0
    for it in classified:
        tgt = it["mean_m"] * H + SERVICE_Z[it["cell"]] * it["sd_m"] * math.sqrt(H)
        ex = max(0.0, it["qty"] - tgt) * it["unit_cost"]
        ex_tot += ex; ex_n += 1 if ex > 0 else 0
        risk_n += 1 if it["qty"] < it["mean_m"] * H else 0
    sensitivity.append({"H": H, "excess_value": round(ex_tot, 2), "excess_skus": ex_n, "at_risk_skus": risk_n})
kpi["sensitivity"] = sensitivity
out = {"kpi": kpi, "cells": list(cells.values()) + list(extra.values()), "service_z": SERVICE_Z,
       "service_pct": SERVICE_PCT, "items": items}
json.dump(out, open(f"{XYZ}/abc_xyz.json", "w", encoding="utf-8"), ensure_ascii=False)

print(json.dumps(kpi, indent=1))
print("\nMATRIX (skus / value):")
for t in "ABC":
    print(t, "  ".join(f"{x}: {cells[t+x]['skus']:3d} / {cells[t+x]['value']:>10,.0f}" for x in "XYZ"),
          "| N:", extra[t+'N']['skus'], "D:", extra[t+'D']['skus'], f"({extra[t+'D']['value']:,.0f})")
print("\nTop excess SKUs under default policy:")
for i in sorted(items, key=lambda r: -(r["excess_value"] or 0))[:10]:
    print(f"  {i['cell']} {i['product']} {i['product_name'][:32]:32s} qty={i['qty']:>8.0f} tgt={i['target_qty']} excess_SAR={i['excess_value']:>10,.0f} cv={i['cv']} ov={i['overstock_flag']}")
print("\nAt-risk A-tier:")
for i in [r for r in items if r["at_risk"] and r["tier"] == "A"][:10]:
    print(f"  {i['cell']} {i['product']} {i['product_name'][:32]:32s} qty={i['qty']:.0f} mean={i['mean_m']} cv={i['cv']}")
