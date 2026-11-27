#!/usr/bin/env python3
"""
2026-09-22 addition: the three best-practice tabs proposed (but not built) during the
Fraud Detection round, now built on real data:
  1. ABC / Pareto value-concentration analysis (from balances -- same source as valuation_by_store)
  2. Cycle-count variance tracking (from EXSYS IM_STOCK_ADJUSTMENTS_M/D, ADJS_TYPE G/L --
     the actual physical stock-count reconciliation log; fetched live via Cure MCP since this
     table isn't part of the Transactions-2026 extract)
  3. Vendor concentration / dependency analysis (from pi_rows -- same source as purchases_by_supplier)

Consumes _state.pkl (phase-1 output) + the current alfaihaa_inventory_audit.json (for
purchases_by_supplier / product_supplier_price_matrix, already computed) + a raw CSV pulled
live from EXSYS (cycle_count_adjustments_raw.csv). Writes the three new keys back into
alfaihaa_inventory_audit.json in place -- does not touch any of the existing keys.
"""
from __future__ import annotations
import json, pickle, csv
from pathlib import Path
from datetime import datetime
from collections import defaultdict

HERE = Path(__file__).parent
JSON_PATH = HERE / "alfaihaa_inventory_audit.json"
CSV_PATH = Path("/home/claude/inventory_build/cycle_count_adjustments_raw.csv")
BRANCH_NAMES = {"01": "Riyadh", "02": "Buraydah 1", "03": "Buraydah 2", "04": "Rafha"}

with open(HERE / "_state.pkl", "rb") as f:
    st = pickle.load(f)

balances = st["balances"]
products = st["products"]
last_cost = st["last_cost"]  # (org,store,product) -> (date, cost)
pi_rows = st["pi_rows"]
as_of = st["as_of"]

data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
product_supplier_price_matrix = data["product_supplier_price_matrix"]

# =============================================================================
# 1. ABC / PARETO VALUE-CONCENTRATION ANALYSIS
# =============================================================================
def classify_tiers(items_sorted_desc, total_value):
    """items_sorted_desc: list of dicts with 'value' key, already sorted desc by value.
    Returns the same list with cum_value/cum_pct/tier added, plus a tier summary."""
    cum = 0.0
    for it in items_sorted_desc:
        cum += it["value"]
        it["cum_value"] = round(cum, 2)
        it["cum_pct"] = round(100.0 * cum / total_value, 2) if total_value else 0.0
        if it["cum_pct"] <= 80.0:
            it["tier"] = "A"
        elif it["cum_pct"] <= 95.0:
            it["tier"] = "B"
        else:
            it["tier"] = "C"
    # a boundary item that crosses 80/95 is kept in the tier that contains most of its
    # cumulative range -- simplest, standard convention: whichever tier its cum_pct lands in.
    tiers = []
    for tier in ("A", "B", "C"):
        grp = [it for it in items_sorted_desc if it["tier"] == tier]
        tval = sum(it["value"] for it in grp)
        tiers.append({
            "tier": tier,
            "sku_count": len(grp),
            "sku_pct": round(100.0 * len(grp) / len(items_sorted_desc), 2) if items_sorted_desc else 0.0,
            "value": round(tval, 2),
            "value_pct": round(100.0 * tval / total_value, 2) if total_value else 0.0,
        })
    return tiers

# company-wide: aggregate by product code across all org/store
prod_agg = defaultdict(lambda: {"qty": 0.0, "value": 0.0, "branches": set(), "stores": set(), "unpriced": 0})
for b in balances:
    a = prod_agg[b["product"]]
    a["qty"] += b["on_hand"]
    a["branches"].add(BRANCH_NAMES.get(b["org"], b["org"]))
    a["stores"].add(b["store_name"])
    if b["on_hand_cost"] is not None:
        a["value"] += b["on_hand_cost"]
    else:
        a["unpriced"] += 1

company_items = []
for pcode, a in prod_agg.items():
    if a["value"] <= 0:
        continue  # zero/unpriced-value items excluded from the Pareto ranking itself
    pname = products.get(pcode, {}).get("name", "")
    company_items.append({
        "product": pcode, "product_name": pname,
        "branches": sorted(a["branches"]), "store_count": len(a["stores"]),
        "qty": round(a["qty"], 2), "value": round(a["value"], 2),
    })
zero_value_skus = sum(1 for a in prod_agg.values() if a["value"] <= 0)
company_items.sort(key=lambda r: -r["value"])
company_total_value = round(sum(r["value"] for r in company_items), 2)
company_tiers = classify_tiers(company_items, company_total_value)

# by-branch: separate Pareto scoped to each branch's own value
by_branch_prod = defaultdict(lambda: defaultdict(lambda: {"qty": 0.0, "value": 0.0}))
for b in balances:
    org = b["org"]
    a = by_branch_prod[org][b["product"]]
    a["qty"] += b["on_hand"]
    if b["on_hand_cost"] is not None:
        a["value"] += b["on_hand_cost"]

abc_by_branch = []
for org in sorted(by_branch_prod.keys()):
    items = []
    for pcode, a in by_branch_prod[org].items():
        if a["value"] <= 0:
            continue
        items.append({"product": pcode, "product_name": products.get(pcode, {}).get("name", ""),
                       "qty": round(a["qty"], 2), "value": round(a["value"], 2)})
    items.sort(key=lambda r: -r["value"])
    tval = round(sum(r["value"] for r in items), 2)
    tiers = classify_tiers(items, tval)
    abc_by_branch.append({
        "org": org, "branch": BRANCH_NAMES.get(org, org),
        "total_value": tval, "sku_count": len(items),
        "tiers": tiers,
        "top_items": items[:15],
    })

abc_analysis = {
    "methodology": ("Classic ABC / Pareto inventory classification on on-hand SAR value. Products are "
                     "ranked by value (highest first) and bucketed by cumulative share of total value: "
                     "Tier A = items making up the first 80% of value, Tier B = the next 15% (80-95%), "
                     "Tier C = the remaining 5% (95-100%). Company-wide ranking aggregates each product "
                     "across every branch/store that holds it; the by-branch view re-runs the same "
                     "classification scoped to each branch's own value only, since a product that's "
                     "'C-tier' company-wide can still be a branch's top item."),
    "as_of": as_of.isoformat(),
    "company_wide": {
        "total_value": company_total_value,
        "total_skus_ranked": len(company_items),
        "zero_or_unpriced_value_skus_excluded": zero_value_skus,
        "tiers": company_tiers,
        "items": company_items,
    },
    "by_branch": abc_by_branch,
}

# =============================================================================
# 2. CYCLE-COUNT VARIANCE TRACKING (from IM_STOCK_ADJUSTMENTS_M/D, ADJS_TYPE G/L)
# =============================================================================
def cost_lookup(org, store, product):
    v = last_cost.get((org, store, product))
    if v is not None:
        return v[1]
    # fall back to any store within the same org, then any store company-wide
    best = None
    for (o, s, p), (dt, c) in last_cost.items():
        if p == product and (o == org or best is None):
            if o == org:
                return c
            best = c
    return best

cc_rows = []
if CSV_PATH.exists():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            org8 = r["organization_no"]
            org = org8[:2]
            store = str(int(float(r["store_id"])))
            product = r["product_code"]
            qty = float(r["adjs_qty"])
            adjs_type = r["adjs_type"]
            dt = r["adjs_date"]
            cost = cost_lookup(org, store, product)
            value = round(qty * cost, 2) if cost is not None else None
            store_name = None
            for b in balances:
                if b["org"] == org and b["store"] == store:
                    store_name = b["store_name"]
                    break
            cc_rows.append({
                "org": org, "branch": BRANCH_NAMES.get(org, org), "store": store,
                "store_name": store_name or f"Store {store}",
                "adjs_no": r["adjs_no"], "adjs_date": dt[:10],
                "type": "Gain" if adjs_type == "G" else "Loss",
                "product": product, "product_name": products.get(product, {}).get("name", ""),
                "qty": round(qty, 2), "unit_cost": round(cost, 4) if cost is not None else None,
                "value": value, "batch_no": r["batch_no"], "posted_by": r["posted_by_user"],
            })

total_events = len(cc_rows)
gain_rows = [r for r in cc_rows if r["type"] == "Gain"]
loss_rows = [r for r in cc_rows if r["type"] == "Loss"]
gain_value = round(sum(r["value"] for r in gain_rows if r["value"] is not None), 2)
loss_value = round(sum(r["value"] for r in loss_rows if r["value"] is not None), 2)
unvalued_events = sum(1 for r in cc_rows if r["value"] is None)
dates = [r["adjs_date"] for r in cc_rows if r["adjs_date"]]
last_event_date = max(dates) if dates else None
events_in_2026 = sum(1 for d in dates if d >= "2026-01-01")
count_linked_events = 1  # per live-DB check: only 1 of 465 rows carries a COUNT_ID FK back to a stock-count session

by_branch_cc = defaultdict(lambda: {"events": 0, "gain_value": 0.0, "loss_value": 0.0, "gain_events": 0, "loss_events": 0, "dates": []})
for r in cc_rows:
    a = by_branch_cc[r["branch"]]
    a["events"] += 1
    a["dates"].append(r["adjs_date"])
    if r["type"] == "Gain":
        a["gain_events"] += 1
        a["gain_value"] += r["value"] or 0.0
    else:
        a["loss_events"] += 1
        a["loss_value"] += r["value"] or 0.0
cc_by_branch = []
for branch, a in by_branch_cc.items():
    cc_by_branch.append({
        "branch": branch, "events": a["events"],
        "gain_events": a["gain_events"], "loss_events": a["loss_events"],
        "gain_value": round(a["gain_value"], 2), "loss_value": round(a["loss_value"], 2),
        "net_value": round(a["gain_value"] - a["loss_value"], 2),
        "last_event_date": max(a["dates"]) if a["dates"] else None,
    })
cc_by_branch.sort(key=lambda r: -abs(r["net_value"]))

by_product_cc = defaultdict(lambda: {"events": 0, "gain_qty": 0.0, "gain_value": 0.0, "loss_qty": 0.0,
                                       "loss_value": 0.0, "branches": set(), "dates": [], "product_name": ""})
for r in cc_rows:
    a = by_product_cc[r["product"]]
    a["events"] += 1
    a["branches"].add(r["branch"])
    a["dates"].append(r["adjs_date"])
    a["product_name"] = r["product_name"]
    if r["type"] == "Gain":
        a["gain_qty"] += r["qty"]; a["gain_value"] += r["value"] or 0.0
    else:
        a["loss_qty"] += r["qty"]; a["loss_value"] += r["value"] or 0.0
cc_by_product = []
for pcode, a in by_product_cc.items():
    cc_by_product.append({
        "product": pcode, "product_name": a["product_name"], "branches": sorted(a["branches"]),
        "event_count": a["events"], "recurring": a["events"] >= 2,
        "gain_qty": round(a["gain_qty"], 2), "gain_value": round(a["gain_value"], 2),
        "loss_qty": round(a["loss_qty"], 2), "loss_value": round(a["loss_value"], 2),
        "net_value": round(a["gain_value"] - a["loss_value"], 2),
        "last_event_date": max(a["dates"]) if a["dates"] else None,
    })
cc_by_product.sort(key=lambda r: -abs(r["net_value"]))
recurring_products = sum(1 for r in cc_by_product if r["recurring"])

by_user_cc = defaultdict(lambda: {"events": 0, "gain_value": 0.0, "loss_value": 0.0})
for r in cc_rows:
    a = by_user_cc[r["posted_by"]]
    a["events"] += 1
    if r["type"] == "Gain":
        a["gain_value"] += r["value"] or 0.0
    else:
        a["loss_value"] += r["value"] or 0.0
cc_by_user = [{"user": u, "events": a["events"], "gain_value": round(a["gain_value"], 2),
               "loss_value": round(a["loss_value"], 2), "net_value": round(a["gain_value"] - a["loss_value"], 2)}
              for u, a in by_user_cc.items()]
cc_by_user.sort(key=lambda r: -r["loss_value"])

cc_rows.sort(key=lambda r: r["adjs_date"], reverse=True)

cycle_count_variance = {
    "methodology": ("Sourced directly from EXSYS's own stock-reconciliation adjustment log "
                     "(IM_STOCK_ADJUSTMENTS_M/D, ADJS_TYPE = 'G' for a physical-count overage/gain and "
                     "'L' for a shortage/loss) -- this is the ERP's real record of what a stocktake found "
                     "versus what the system expected, pulled live via Cure MCP since it sits outside the "
                     "Transactions-2026 extract used for the rest of this audit. Value = adjustment quantity "
                     "x each product's most recent known unit cost (the same moving-average-proxy cost used "
                     "throughout this workbook, since ADJS_VALUE itself is null for every row in this "
                     "tenant -- the same ~100%-NULL costing gap noted elsewhere in this audit)."),
    "data_quality_note": ("Of 465 posted count-reconciliation adjustments (2019-2025), only 1 carries a "
                           "formal link (COUNT_ID) back to a specific IM_STOCK_COUNT session -- so Cure "
                           "cannot currently tie a given adjustment back to the stocktake that produced it, "
                           "breaking the audit trail from 'we counted on this date' to 'and adjusted by "
                           "this much.' Free-text notes on many of these entries do reference 'Annual Check "
                           "of Inventory' / 'جرد' (stocktake), which is how this dataset was identified as "
                           "count-driven rather than treated as an ordinary stock adjustment."),
    "kpi": {
        "total_events": total_events, "gain_events": len(gain_rows), "loss_events": len(loss_rows),
        "gain_value": gain_value, "loss_value": loss_value, "net_value": round(gain_value - loss_value, 2),
        "unvalued_events": unvalued_events,
        "distinct_skus_with_variance": len(cc_by_product), "recurring_variance_skus": recurring_products,
        "count_id_linked_events": count_linked_events,
        "date_range": f"{min(dates)} to {max(dates)}" if dates else None,
        "last_event_date": last_event_date, "events_logged_in_2026": events_in_2026,
    },
    "by_branch": cc_by_branch,
    "by_product": cc_by_product,
    "by_user": cc_by_user,
    "events": cc_rows,
}

# =============================================================================
# 3. VENDOR CONCENTRATION / DEPENDENCY ANALYSIS
# =============================================================================
supplier_agg = defaultdict(lambda: {"spend": 0.0, "qty": 0.0, "lines": 0, "products": set(), "branches": set()})
for p in pi_rows:
    if p["unit_cost"] is None or p["primary_qty"] is None:
        continue
    k = (p["supplier_no"], p["supplier_name"])
    a = supplier_agg[k]
    a["spend"] += p["unit_cost"] * p["primary_qty"]
    a["qty"] += p["primary_qty"]
    a["lines"] += 1
    a["products"].add(p["product"])
    a["branches"].add(BRANCH_NAMES.get(p["org"], p["org"]))

total_spend = sum(a["spend"] for a in supplier_agg.values())
supplier_list = []
for (sno, sname), a in supplier_agg.items():
    supplier_list.append({
        "supplier_no": sno, "supplier_name": sname, "spend": round(a["spend"], 2),
        "share_pct": round(100.0 * a["spend"] / total_spend, 2) if total_spend else 0.0,
        "line_count": a["lines"], "product_count": len(a["products"]),
        "branches": sorted(a["branches"]),
    })
supplier_list.sort(key=lambda r: -r["spend"])
cum = 0.0
for r in supplier_list:
    cum += r["spend"]
    r["cum_pct"] = round(100.0 * cum / total_spend, 2) if total_spend else 0.0

hhi = round(sum((r["share_pct"]) ** 2 for r in supplier_list), 1)
if hhi < 1500:
    concentration_level = "Low"
elif hhi < 2500:
    concentration_level = "Moderate"
else:
    concentration_level = "High"

top5_share = round(sum(r["spend"] for r in supplier_list[:5]) / total_spend * 100, 2) if total_spend else 0.0
top10_share = round(sum(r["spend"] for r in supplier_list[:10]) / total_spend * 100, 2) if total_spend else 0.0

# single-source dependency: products bought from exactly 1 supplier in the price matrix
prod_supplier_count = defaultdict(list)
for row in product_supplier_price_matrix:
    prod_supplier_count[row["product"]].append(row)
single_source = []
for pcode, rows in prod_supplier_count.items():
    if len(rows) == 1:
        r = rows[0]
        spend_est = round((r.get("avg_price") or 0) * (r.get("tot_qty") or 0), 2)
        single_source.append({
            "product": pcode, "product_name": r.get("product_name", ""),
            "supplier_no": r["supplier_no"], "supplier_name": r["supplier_name"],
            "spend_est": spend_est, "qty": r.get("tot_qty"), "line_count": r.get("line_cnt"),
            "last_date": r.get("last_date"),
        })
single_source.sort(key=lambda r: -r["spend_est"])
single_source_spend = round(sum(r["spend_est"] for r in single_source), 2)
single_source_share = round(100.0 * single_source_spend / total_spend, 2) if total_spend else 0.0

# per-branch concentration
branch_supplier_spend = defaultdict(lambda: defaultdict(float))
for p in pi_rows:
    if p["unit_cost"] is None or p["primary_qty"] is None:
        continue
    br = BRANCH_NAMES.get(p["org"], p["org"])
    branch_supplier_spend[br][(p["supplier_no"], p["supplier_name"])] += p["unit_cost"] * p["primary_qty"]
vendor_by_branch = []
for br, supmap in branch_supplier_spend.items():
    btotal = sum(supmap.values())
    ranked = sorted(supmap.items(), key=lambda kv: -kv[1])
    bhhi = round(sum((100.0 * v / btotal) ** 2 for k, v in supmap.items()), 1) if btotal else 0.0
    top_sup = ranked[0] if ranked else None
    vendor_by_branch.append({
        "branch": br, "total_spend": round(btotal, 2), "supplier_count": len(supmap), "hhi": bhhi,
        "top_supplier_name": top_sup[0][1] if top_sup else None,
        "top_supplier_share_pct": round(100.0 * top_sup[1] / btotal, 2) if top_sup and btotal else None,
    })
vendor_by_branch.sort(key=lambda r: -r["total_spend"])

purchasing_model_note = (
    "All 2917 purchase-invoice lines in this extract are posted under Riyadh (org 01) -- "
    "Buraydah 1, Buraydah 2 and Rafha post zero purchase invoices of their own. This matches "
    "this audit's own earlier finding that Riyadh Main Store is the group's central buying "
    "office: it purchases on behalf of every branch, then moves stock out to the other three "
    "via Stock Transfer (see the Overstock methodology note elsewhere in this workbook). "
    "Practically, this means vendor/supplier concentration is a company-wide question, not a "
    "branch-by-branch one -- the 'by branch' table below is included for completeness but will "
    "always show a single Riyadh row until purchasing is decentralized or logged differently."
)

vendor_concentration = {
    "purchasing_model_note": purchasing_model_note,
    "methodology": ("Supplier spend is computed the same way as the existing Purchases & Pricing tab "
                     "(purchase-invoice-line unit_cost x quantity, 2026 data). Concentration is measured "
                     "with the Herfindahl-Hirschman Index (HHI = sum of each supplier's market-share-squared, "
                     "0-10,000 scale) -- the standard antitrust/procurement-risk measure: <1,500 = low "
                     "concentration (a healthy, diversified supplier base), 1,500-2,500 = moderate, "
                     ">2,500 = high (heavy reliance on a small number of vendors). Single-source dependency "
                     "flags every product bought from exactly one supplier in 2026, ranked by estimated spend "
                     "-- these are the specific items most exposed if that one vendor has a supply, pricing, "
                     "or relationship disruption."),
    "kpi": {
        "total_spend_2026": round(total_spend, 2), "supplier_count": len(supplier_list),
        "hhi": hhi, "concentration_level": concentration_level,
        "top5_share_pct": top5_share, "top10_share_pct": top10_share,
        "single_source_product_count": len(single_source),
        "single_source_spend_est": single_source_spend, "single_source_share_pct": single_source_share,
    },
    "top_suppliers": supplier_list,
    "by_branch": vendor_by_branch,
    "single_source_products": single_source,
}

# =============================================================================
# WRITE BACK
# =============================================================================
data["abc_analysis"] = abc_analysis
data["cycle_count_variance"] = cycle_count_variance
data["vendor_concentration"] = vendor_concentration

JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print("Wrote", JSON_PATH, "size:", JSON_PATH.stat().st_size)
print()
print("ABC company tiers:", abc_analysis["company_wide"]["tiers"])
print()
print("Cycle count KPI:", cycle_count_variance["kpi"])
print()
print("Vendor KPI:", vendor_concentration["kpi"])
