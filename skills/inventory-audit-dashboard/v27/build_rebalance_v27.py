import json

RB = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad/rebalance"
FORECAST_DIR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad/forecast"

rows = json.load(open(f"{RB}/branch_balances_top50_v27.json", encoding="utf-8"))
forecast_items = json.load(open(f"{FORECAST_DIR}/demand_forecast_items_v27.json", encoding="utf-8"))["items"]
fc_by_code = {it["product"]: it for it in forecast_items}

RESERVE_MONTHS = 4.0       # Riyadh keeps this many months of its OWN dispense-only rate before anything is "surplus"
DEFICIT_HORIZON_MONTHS = 3.0  # receiving branch flagged if it would run out within the forecast's own 3-month window
MIN_TRANSFER_QTY = 1
MIN_TRANSFER_SAR = 50.0

# ---- 1. roll up branch_balances (handles Riyadh's 2 stores: Main + Dialysis) ----
by_sku_branch = {}  # product -> branch -> agg dict
for r in rows:
    p, b = r["product"], r["branch"]
    agg = by_sku_branch.setdefault(p, {}).setdefault(b, {
        "branch": b, "on_hand_qty": 0.0, "on_hand_value": 0.0,
        "dispensed_qty_6mo": 0.0, "transferred_out_qty_6mo": 0.0, "qty_out_6mo": 0.0,
        "unit_cost_sum": 0.0, "unit_cost_n": 0,
    })
    agg["on_hand_qty"] += r["on_hand_qty"]
    agg["on_hand_value"] += r["on_hand_value"]
    agg["dispensed_qty_6mo"] += r["dispensed_qty_6mo"]
    agg["transferred_out_qty_6mo"] += r["transferred_out_qty_6mo"]
    agg["qty_out_6mo"] += r["qty_out_6mo"]
    agg["unit_cost_sum"] += r["unit_cost"]
    agg["unit_cost_n"] += 1

recommendations = []
skus_no_riyadh_stock = []
skus_no_deficit = []

for product, branches in by_sku_branch.items():
    fc = fc_by_code.get(product)
    if fc is None:
        continue
    product_name = fc["product_name"]
    forecast_3mo_company = fc["forecast_total_3mo"]
    confidence = fc["confidence"]
    model = fc["model"]

    riyadh = branches.get("Riyadh")
    if riyadh is None or riyadh["on_hand_qty"] <= 0:
        skus_no_riyadh_stock.append(product)
        continue

    riyadh_unit_cost = riyadh["unit_cost_sum"] / max(riyadh["unit_cost_n"], 1)
    riyadh_ds_monthly = riyadh["dispensed_qty_6mo"] / 6.0
    riyadh_reserve_qty = riyadh_ds_monthly * RESERVE_MONTHS
    riyadh_surplus_qty = max(0.0, riyadh["on_hand_qty"] - riyadh_reserve_qty)

    total_out_6mo = sum(b["qty_out_6mo"] for b in branches.values())

    deficits = []
    for bname, b in branches.items():
        if bname == "Riyadh":
            continue
        share = (b["qty_out_6mo"] / total_out_6mo) if total_out_6mo > 0 else 0.0
        forecast_3mo_b = forecast_3mo_company * share
        deficit_qty = max(0.0, forecast_3mo_b - b["on_hand_qty"])
        deficits.append({
            "branch": bname, "share": share, "forecast_3mo": round(forecast_3mo_b, 1),
            "on_hand_qty": b["on_hand_qty"], "on_hand_value": round(b["on_hand_value"], 2),
            "deficit_qty": deficit_qty,
        })

    deficits.sort(key=lambda x: -x["deficit_qty"])
    remaining_surplus = riyadh_surplus_qty
    any_deficit = False
    for d in deficits:
        if d["deficit_qty"] <= 0 or remaining_surplus <= 0:
            continue
        any_deficit = True
        transfer_qty = min(remaining_surplus, d["deficit_qty"])
        transfer_qty_int = int(transfer_qty)  # whole units only
        if transfer_qty_int < MIN_TRANSFER_QTY:
            continue
        transfer_value = round(transfer_qty_int * riyadh_unit_cost, 2)
        if transfer_value < MIN_TRANSFER_SAR:
            continue
        remaining_surplus -= transfer_qty_int
        recommendations.append({
            "product": product, "product_name": product_name,
            "from_branch": "Riyadh", "to_branch": d["branch"],
            "transfer_qty": transfer_qty_int, "transfer_value": transfer_value,
            "riyadh_on_hand_qty": riyadh["on_hand_qty"], "riyadh_on_hand_value": round(riyadh["on_hand_value"], 2),
            "riyadh_surplus_qty": round(riyadh_surplus_qty, 1),
            "riyadh_reserve_months": RESERVE_MONTHS,
            "to_branch_on_hand_qty": d["on_hand_qty"], "to_branch_on_hand_value": d["on_hand_value"],
            "to_branch_forecast_3mo": d["forecast_3mo"], "to_branch_deficit_qty": round(d["deficit_qty"], 1),
            "to_branch_share_of_demand": round(d["share"], 3),
            "forecast_model": model, "confidence": confidence,
            "company_forecast_3mo": round(forecast_3mo_company, 1),
        })
    if not any_deficit:
        skus_no_deficit.append(product)

recommendations.sort(key=lambda r: -r["transfer_value"])

kpi = {
    "sku_count_evaluated": len(by_sku_branch),
    "recommendation_count": len(recommendations),
    "distinct_skus_recommended": len({r["product"] for r in recommendations}),
    "total_transfer_qty": round(sum(r["transfer_qty"] for r in recommendations), 0),
    "total_transfer_value": round(sum(r["transfer_value"] for r in recommendations), 2),
    "branches_receiving": sorted({r["to_branch"] for r in recommendations}),
    "skus_no_riyadh_stock": len(skus_no_riyadh_stock),
    "skus_no_deficit_found": len(skus_no_deficit),
}

out = {"kpi": kpi, "recommendations": recommendations}
json.dump(out, open(f"{RB}/rebalancing_recommendations_v27.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print("KPI:", json.dumps(kpi, indent=1))
print("\nTop 10 recommendations by value:")
for r in recommendations[:10]:
    print(f"  {r['product']} {r['product_name'][:35]:35s} Riyadh -> {r['to_branch']:12s} qty={r['transfer_qty']:5d} SAR={r['transfer_value']:9.2f} conf={r['confidence']}")
