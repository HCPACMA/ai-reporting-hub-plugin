#!/usr/bin/env python3
"""Phase 2: consumes _state.pkl from build_alfaihaa_inventory.py, adds Batches (expiry)
and computes the 7 standing checks + supplier price matrix. Writes alfaihaa_inventory_audit.json."""
from __future__ import annotations
import json, pickle, statistics
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import openpyxl

HERE = Path(__file__).parent
SRC = HERE.resolve().parents[1] / "Riyadh_Inventory_Data_2026.xlsx"
OUT = HERE / "alfaihaa_inventory_audit.json"
BRANCH_NAMES = {"01": "Riyadh", "02": "Buraydah 1", "03": "Buraydah 2", "04": "Rafha"}

def to_f(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    s=str(v).strip()
    if s=="" or s.lower() in ("none","null"): return None
    try: return float(s)
    except ValueError: return None

def to_dt(v):
    if v is None: return None
    if isinstance(v, datetime): return v
    s=str(v).strip()
    if s=="" or s.lower()=="none": return None
    for fmt in ("%Y-%m-%d %H:%M:%S","%Y-%m-%d"):
        try: return datetime.strptime(s[:19], fmt)
        except ValueError: continue
    return None

def norm_store(v):
    f = to_f(v)
    if f is None: return str(v).strip() if v is not None else None
    return str(int(f))

def branch_org_of(org_raw):
    if org_raw is None: return None
    s = str(org_raw).strip()
    if len(s) > 2:
        return s[:2]
    return s

with open(HERE / "_state.pkl", "rb") as f:
    st = pickle.load(f)

as_of = st["as_of"]
extract_min_date = st.get("extract_min_date")
balances = st["balances"]
products = st["products"]
last_ds_date = st["last_ds_date"]
last_ts_date = st.get("last_ts_date", {})
last_cost = st.get("last_cost", {})
last_receipt_date = st.get("last_receipt_date", {})
last_receipt_type = st.get("last_receipt_type", {})
ds_qty_6mo = st["ds_qty_6mo"]
ts_qty_6mo = st.get("ts_qty_6mo", {})
ds_monthly_cc = st["ds_monthly_cc"]
receipt_qty_by_product = st["receipt_qty_by_product"]
receiving_lines = st["receiving_lines"]
pi_rows = st["pi_rows"]
branch_activity = st["branch_activity"]
store_activity = st["store_activity"]
malformed_count = st["malformed_count"]
total_rows = st["total_rows"]
reconstructed_count = st.get("reconstructed_count", 0)

print(f"as_of = {as_of.isoformat()}  balances={len(balances)}")

# ---------------------------------------------------------------------------
# 1. VALUATION & POSITION (by branch + store)
# ---------------------------------------------------------------------------
val_by_store = defaultdict(lambda: {"sku_count":0,"total_qty":0.0,"total_value":0.0,"unknown_cost_skus":0})
for b in balances:
    k = (b["org"], b["org_name"], b["store"], b["store_name"])
    v = val_by_store[k]
    v["sku_count"] += 1
    v["total_qty"] += b["on_hand"]
    if b["on_hand_cost"] is not None:
        v["total_value"] += b["on_hand_cost"]
    else:
        v["unknown_cost_skus"] += 1
valuation_by_store = [
    {"org":k[0],"branch":BRANCH_NAMES.get(k[0],k[0]),"org_name":k[1],"store":k[2],"store_name":k[3],
     "sku_count":v["sku_count"],"total_qty":round(v["total_qty"],2),"total_value":round(v["total_value"],2),
     "unknown_cost_skus":v["unknown_cost_skus"]}
    for k,v in val_by_store.items()
]
valuation_by_store.sort(key=lambda r: -r["total_value"])
total_value_all = round(sum(r["total_value"] for r in valuation_by_store), 2)
total_sku_all = sum(r["sku_count"] for r in valuation_by_store)

# ---------------------------------------------------------------------------
# 2. OVERSTOCK -- real days-of-cover, 6-month trailing consumption
# ---------------------------------------------------------------------------
overstock = []
overstock_window_start = as_of - timedelta(days=180)
for b in balances:
    key = (b["org"], b["store"], b["product"])
    # Outbound movement = dispense (DS) + send-transfer (TS). Riyadh Main Store is the central
    # purchasing/storage hub for all 4 branches -- stock physically there leaves both via DS
    # (dispensed to Riyadh's own patients/departments) and via TS (transferred out to the other
    # 3 branches). Counting DS alone understates real turnover there and falsely inflates
    # Riyadh's days-of-cover / overstock reading. This DS+TS rule is applied uniformly to every
    # branch (not special-cased to Riyadh) -- it is a no-op elsewhere since TS volume is
    # concentrated at Riyadh Main Store (~88% of all TS lines company-wide; verified against the
    # extract before implementing), but it is the methodologically correct definition everywhere.
    ds_out = ds_qty_6mo.get(key, 0.0)
    ts_out = ts_qty_6mo.get(key, 0.0)
    qty_out_6mo = ds_out + ts_out
    last_recv = last_receipt_date.get(key)
    recently_restocked = last_recv is not None and last_recv >= overstock_window_start
    if qty_out_6mo == 0:
        doc = None  # infinite / no consumption
        # a zero-consumption flag is meaningless if this stock only arrived within the 6-month
        # window itself -- there hasn't been time to prove it's not moving (see Slow-Moving note)
        flag = not recently_restocked
    else:
        daily = qty_out_6mo / 180.0
        doc = b["on_hand"] / daily if daily > 0 else None
        flag = (doc is not None and doc > 365)
    if flag:
        overstock.append({**b, "qty_out_6mo": round(qty_out_6mo,2),
                           "dispensed_qty_6mo": round(ds_out,2), "transferred_out_qty_6mo": round(ts_out,2),
                           "days_of_cover": round(doc,1) if doc else None,
                           "last_received": last_recv.date().isoformat() if last_recv else None,
                           "branch": BRANCH_NAMES.get(b["org"], b["org"])})
overstock.sort(key=lambda r: -(r["on_hand_cost"] or 0))
overstock_value = round(sum((r["on_hand_cost"] or 0) for r in overstock), 2)

# MIN/MAX config-artifact check (for the caveat note)
minmax_combos = Counter((b["min_qty"], b["reorder_qty"], b["max_qty"]) for b in balances)
minmax_top = minmax_combos.most_common(1)[0] if minmax_combos else (None,0)
minmax_is_uniform_default = (len(minmax_combos) == 1)
raw_erp_overstock = [b for b in balances if b["max_qty"] is not None and b["on_hand"] > b["max_qty"]]
raw_erp_overstock_value = round(sum((b["on_hand_cost"] or 0) for b in raw_erp_overstock), 2)

# ---------------------------------------------------------------------------
# 3. SLOW-MOVING / DEAD STOCK -- no dispense in 90+ days
# ---------------------------------------------------------------------------
slow_moving = []
cutoff = as_of - timedelta(days=90)
for b in balances:
    key = (b["org"], b["store"], b["product"])
    # Same DS+TS outbound definition as Overstock above: a branch that transferred stock out to
    # another branch has moved it, even if it was never locally dispensed -- most relevant at
    # Riyadh Main Store.
    last_ds = last_ds_date.get(key)
    last_ts = last_ts_date.get(key)
    if last_ds and last_ts:
        last_out, last_out_type = (last_ds, "dispense") if last_ds >= last_ts else (last_ts, "transfer-out")
    elif last_ds:
        last_out, last_out_type = last_ds, "dispense"
    elif last_ts:
        last_out, last_out_type = last_ts, "transfer-out"
    else:
        last_out, last_out_type = None, None
    last_recv = last_receipt_date.get(key)
    recently_restocked = last_recv is not None and last_recv >= cutoff
    if (last_out is None or last_out < cutoff) and not recently_restocked:
        slow_moving.append({**b, "last_out_date": last_out.date().isoformat() if last_out else None,
                             "last_out_type": last_out_type,
                             "last_received": last_recv.date().isoformat() if last_recv else None,
                             "branch": BRANCH_NAMES.get(b["org"], b["org"])})
slow_moving.sort(key=lambda r: (r["last_out_date"] or ""))
slow_moving_value = round(sum((r["on_hand_cost"] or 0) for r in slow_moving), 2)

# ---------------------------------------------------------------------------
# 4. EXPIRY RISK -- real batch-level data (Batches sheet)
# ---------------------------------------------------------------------------
print("loading Batches sheet ...")
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
wsb = wb["Batches"]
h = [c.value for c in next(wsb.iter_rows(min_row=1,max_row=1))]
bidx = {x:i for i,x in enumerate(h)}
expiry_risk = []
past_expiry = []
batch_rows_total = 0
unknown_cost_batches = 0
for row in wsb.iter_rows(min_row=2, values_only=True):
    batch_rows_total += 1
    qty = to_f(row[bidx["qty_on_hand"]]) or 0.0
    if qty <= 0: continue
    exp = to_dt(row[bidx["expiry_date"]])
    if exp is None: continue
    org_raw = row[bidx["organization_no"]]
    branch_org = branch_org_of(org_raw)
    store_n = norm_store(row[bidx["store_id"]])
    pcode = row[bidx["product_code"]]
    ned = to_f(row[bidx["near_expiry_days"]]) or 90.0
    # Value join: Batches uses the same granular store-level organization_no as Balance+Config,
    # so it needs the same branch_org_of/norm_store normalization to hit the (branch,store,
    # product) cost lookup built from transaction history. Same any-store-for-product fallback
    # used for on-hand valuation when the specific store has no cost history; never assumed zero.
    key = (branch_org, store_n, pcode)
    cost = last_cost.get(key, (None, None))[1]
    if cost is None:
        alt = [v[1] for k, v in last_cost.items() if k[2] == pcode]
        cost = alt[-1] if alt else None
    if cost is None:
        unknown_cost_batches += 1
    value = round(qty * cost, 2) if cost is not None else None
    rec = {
        "org": branch_org, "org_raw": org_raw, "branch": BRANCH_NAMES.get(branch_org, branch_org),
        "store": store_n,
        "product": pcode, "product_name": row[bidx["product_description"]],
        "batch_no": row[bidx["batch_no"]], "qty_on_hand": qty,
        "unit_cost": cost, "value": value, "cost_is_estimated": cost is None,
        "expiry_date": exp.date().isoformat(), "near_expiry_days": ned,
    }
    days_to_expiry = (exp - as_of).days
    if exp < as_of:
        past_expiry.append(rec)
    elif days_to_expiry <= ned:
        expiry_risk.append(rec)
wb.close()
expiry_risk.sort(key=lambda r: r["expiry_date"])
past_expiry.sort(key=lambda r: r["expiry_date"])

# Per-branch + grand-total SAR value rollups, for both Near-Expiry and Past-Expiry.
def rollup_expiry_value(rows_):
    agg = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0, "unknown_cost_count": 0})
    for r in rows_:
        a = agg[r["org"]]
        a["count"] += 1
        a["qty"] += r["qty_on_hand"]
        if r["value"] is not None:
            a["value"] += r["value"]
        else:
            a["unknown_cost_count"] += 1
    out = [
        {"org": org, "branch": BRANCH_NAMES.get(org, org),
         "count": v["count"], "qty": round(v["qty"], 2), "value": round(v["value"], 2),
         "unknown_cost_count": v["unknown_cost_count"]}
        for org, v in agg.items()
    ]
    out.sort(key=lambda r: -r["value"])
    return out

near_expiry_by_branch = rollup_expiry_value(expiry_risk)
past_expiry_by_branch = rollup_expiry_value(past_expiry)
near_expiry_value_total = round(sum(r["value"] for r in near_expiry_by_branch), 2)
past_expiry_value_total = round(sum(r["value"] for r in past_expiry_by_branch), 2)

# ---------------------------------------------------------------------------
# 5. RECEIVING-ERROR / DATA-QUALITY FLAGS
# ---------------------------------------------------------------------------
receiving_flags = []
med_by_product = {}
for pcode, qtys in receipt_qty_by_product.items():
    if len(qtys) >= 3:
        med_by_product[pcode] = statistics.median(qtys)
for line in receiving_lines:
    med = med_by_product.get(line["product"])
    if med and med > 0 and (line["qty"] > 20*med or (line["qty"] < med/20 and line["qty"]>0)):
        receiving_flags.append({**line, "product_median_receipt_qty": round(med,2),
                                 "branch": BRANCH_NAMES.get(line["org"], line["org"])})
receiving_flags.sort(key=lambda r: -abs(r["qty"]))

# ---------------------------------------------------------------------------
# 6. CROSS-BRANCH / CROSS-STORE PEER AUDIT
# ---------------------------------------------------------------------------
cross_org_peer_audit = []
for r in valuation_by_store:
    cross_org_peer_audit.append(r)
# simple peer stats: value per branch total, and store share within branch
branch_totals = defaultdict(float)
for r in valuation_by_store:
    branch_totals[r["org"]] += r["total_value"]

# ---------------------------------------------------------------------------
# 7. DISPENSE BY COST CENTER, MONTH OVER MONTH
# ---------------------------------------------------------------------------
dispense_by_cc = []
for (org, cc_no, cc_name, ym), v in ds_monthly_cc.items():
    dispense_by_cc.append({
        "org": org, "branch": BRANCH_NAMES.get(org, org),
        "cost_center_no": cc_no, "cost_center_name": cc_name or "(unassigned)",
        "month": ym, "qty": round(v["qty"],2), "cost": round(v["cost"],2),
    })
dispense_by_cc.sort(key=lambda r: (r["org"], r["cost_center_no"] or "", r["month"]))

# ---------------------------------------------------------------------------
# 8. PURCHASES BY SUPPLIER + PRODUCT x SUPPLIER PRICE MATRIX
# ---------------------------------------------------------------------------
purch_by_supplier_month = defaultdict(lambda: {"qty":0.0,"cost":0.0,"lines":0})
for p in pi_rows:
    if p["date"] is None: continue
    ym = p["date"].strftime("%Y-%m")
    k = (p["supplier_no"], p["supplier_name"], ym)
    v = purch_by_supplier_month[k]
    v["qty"] += p["primary_qty"]
    v["cost"] += (p["unit_cost"] or 0.0) * p["primary_qty"]
    v["lines"] += 1
purchases_by_supplier = [
    {"supplier_no":k[0],"supplier_name":k[1],"month":k[2],"qty":round(v["qty"],2),"total_cost":round(v["cost"],2),"line_count":v["lines"]}
    for k,v in purch_by_supplier_month.items()
]
purchases_by_supplier.sort(key=lambda r: (r["month"], -r["total_cost"]))

any_discount = any((p["item_discount"] or 0) != 0 or (p["invoice_discount"] or 0) != 0 for p in pi_rows)

price_rows = defaultdict(list)  # (product, supplier) -> list of unit costs
for p in pi_rows:
    if p["unit_cost"] is None or p["primary_qty"] in (None, 0): continue
    price_rows[(p["product"], p["supplier_no"], p["supplier_name"])].append((p["unit_cost"], p["primary_qty"], p["date"]))

product_median = {}
by_product_costs = defaultdict(list)
for (pcode, sup_no, sup_name), lst in price_rows.items():
    for c, q, d in lst:
        by_product_costs[pcode].append(c)
for pcode, costs in by_product_costs.items():
    if len(costs) >= 2:
        product_median[pcode] = statistics.median(costs)

matrix = []
for (pcode, sup_no, sup_name), lst in price_rows.items():
    med = product_median.get(pcode)
    outlier_lines = sum(1 for c,_,_ in lst if med and med>0 and (c>3*med or c<med/3))
    tot_qty = sum(q for _,q,_ in lst)
    tot_val = sum(c*q for c,q,_ in lst)
    matrix.append({
        "product": pcode, "product_name": products.get(pcode,{}).get("name", pcode),
        "supplier_no": sup_no, "supplier_name": sup_name,
        "min_price": round(min(c for c,_,_ in lst),4), "max_price": round(max(c for c,_,_ in lst),4),
        "avg_price": round(tot_val/tot_qty, 4) if tot_qty else None,
        "tot_qty": round(tot_qty,2), "line_cnt": len(lst),
        "last_date": max(d for _,_,d in lst if d).date().isoformat() if any(d for _,_,d in lst) else None,
        "outlier_lines": outlier_lines,
    })

# savings opportunities: for products with 2+ suppliers (clean, outlier-excluded)
by_product_matrix = defaultdict(list)
for m in matrix:
    by_product_matrix[m["product"]].append(m)
savings_opportunities = []
for pcode, rows_ in by_product_matrix.items():
    clean = [r for r in rows_ if r["outlier_lines"] == 0 and r["avg_price"] is not None]
    if len(clean) < 2: continue
    cheapest = min(clean, key=lambda r: r["avg_price"])
    priciest = max(clean, key=lambda r: r["avg_price"])
    if priciest["avg_price"] <= cheapest["avg_price"]: continue
    gap_pct = round(100*(priciest["avg_price"]-cheapest["avg_price"])/priciest["avg_price"], 1)
    savings_opportunities.append({
        "product": pcode, "product_name": products.get(pcode,{}).get("name", pcode),
        "cheapest_supplier": cheapest["supplier_name"], "cheapest_price": cheapest["avg_price"],
        "priciest_supplier": priciest["supplier_name"], "priciest_price": priciest["avg_price"],
        "gap_pct": gap_pct,
    })
savings_opportunities.sort(key=lambda r: -(r["gap_pct"] or 0))
outlier_matrix_rows = [m for m in matrix if m["outlier_lines"] > 0]

# ---------------------------------------------------------------------------
# 9. NEVER DISPENSED / AGING BUCKET
# Items sitting on hand that have never once been dispensed (DS) from the
# exact (branch, store) they currently sit in -- including stock that has
# circulated between branches purely via transfer (TS/TR) without ever
# reaching a clinic/patient anywhere. Two filter scopes, both derived from
# the same row set:
#   - "by branch": never dispensed from THIS store (may have been dispensed
#     at a different branch's store for the same product -- still worth a
#     look, e.g. a candidate for inter-branch reallocation instead of a
#     fresh purchase).
#   - "through all branches": never_dispensed_anywhere -- this product code
#     has ZERO dispense activity at ANY store, ANY branch, company-wide.
#     This is the more severe case the user flagged: stock moving between
#     warehouses (TS/TR) but never actually consumed anywhere.
# Aging is measured from last_receipt_date (most recent PI/TR = purchase or
# transfer-in) to as_of -- "how long has this sat here without being used". A
# key with on-hand stock but ZERO PI/TR rows anywhere in the extract must
# have held that stock since before the extract's own window started
# (extract_min_date) -- an implicit opening balance. That gives a calculable
# lower-bound entry date/age instead of leaving those rows "unknown"
# (user-clarified 2026-09-21).
#
# Addition (user-requested 2026-09-21, "Original Batch date"): the entry-date
# basis above answers "how long has this stock sat in its CURRENT warehouse"
# -- but a transfer-in resets that clock even though the batch itself may be
# far older (e.g. purchased in 2019, transferred between stores since). A
# second, independent date basis -- original_batch_date -- answers "how old
# is this batch really", using each (org,store,product) key's EARLIEST-EVER
# transaction date company-side, live-queried from the ERP directly (Cure
# MCP, IM_PRODUCTS_TRANSACTIONS) since this extract's own "Transactions 2026"
# sheet only covers 2026 and can't see back that far. Both bases are kept
# side by side (original_batch_date_live.json never overwrites the entry-date
# fields) so either can drive filtering/bucketing -- see original_batch_*
# fields below and the dashboard's date-basis toggle.
# ---------------------------------------------------------------------------
BUCKET_ORDER = ["0-30", "31-60", "61-90", "91-120", "121-180", "181-365", "365+", "Unknown"]
ENTRY_TYPE_LABEL = {"PI": "Purchase", "TR": "Transfer"}
ORIGINAL_BATCH_TYPE_LABEL = {
    "PI": "Purchase", "TR": "Transfer", "OB": "Opening balance", "CNT": "Stock count",
    "DS": "Dispense (earliest record on file)", "TS": "Send transfer", "CRC": "Credit/return", "PR": "Price revision",
}

def aging_bucket_of(days):
    if days is None: return "Unknown"
    if days <= 30: return "0-30"
    if days <= 60: return "31-60"
    if days <= 90: return "61-90"
    if days <= 120: return "91-120"
    if days <= 180: return "121-180"
    if days <= 365: return "181-365"
    return "365+"

dispensed_products_anywhere = set(k[2] for k in last_ds_date.keys())

# original_batch_date_live.json: one row per (org,product) never-dispensed key,
# {org, product, date, t_type, transaction_type, store_id, store_name, batch_no} -- the
# earliest-ever transaction for that product ANYWHERE in the branch (org), live-queried
# directly against EXSYS.IM_PRODUCTS_TRANSACTIONS. Deliberately partitioned by org+product,
# NOT by the never-dispensed row's own (org,store,product) key: verified against the user's
# own ERP screenshot for 0050418 that a batch's true Opening Balance can sit under a
# DIFFERENT store code within the same branch (e.g. Riyadh's Dental Store, org_raw
# '...1303') from where it's transferred to and sitting today (Main Store, '...1301') --
# scoping the earliest-transaction lookup to the current store alone silently misses that
# earlier opening balance and only finds the transfer-in date, which the entry-date basis
# below already reports. When the original batch's store differs from the row's current
# store, original_batch_store_name records where it was first seen.
original_batch_path = Path(__file__).parent / "original_batch_date_live.json"
original_batch_map = {}
if original_batch_path.exists():
    import json as _json2
    for rec in _json2.loads(original_batch_path.read_text(encoding="utf-8")):
        original_batch_map[(rec["org"], rec["product"])] = rec

never_dispensed = []
for b in balances:
    key = (b["org"], b["store"], b["product"])
    if key in last_ds_date:
        continue  # this exact store has dispensed it at some point -- not "never dispensed here"
    last_recv = last_receipt_date.get(key)
    if last_recv is not None:
        entry_type = ENTRY_TYPE_LABEL.get(last_receipt_type.get(key))
        effective_date = last_recv
    elif extract_min_date is not None:
        # opening balance: on hand, but no PI/TR row anywhere in this extract -- it was already
        # sitting here before the extract's own window began. extract_min_date is a hard lower
        # bound on age, not the true entry date (which could be older still).
        entry_type = "Opening balance (pre-extract)"
        effective_date = extract_min_date
    else:
        entry_type = None
        effective_date = None
    days_in_stock = (as_of - effective_date).days if effective_date else None

    ob_rec = original_batch_map.get((b["org"], b["product"]))
    ob_date = to_dt(ob_rec["date"]) if ob_rec else None
    ob_days = (as_of - ob_date).days if ob_date else None
    ob_store_differs = bool(ob_rec and ob_rec.get("store_id") != b["store"])

    never_dispensed.append({
        **b, "branch": BRANCH_NAMES.get(b["org"], b["org"]),
        "last_receipt_date": last_recv.date().isoformat() if last_recv else None,
        "entry_type": entry_type,
        "entry_date_estimated": last_recv is None and effective_date is not None,
        "entry_date_display": (effective_date.date().isoformat() if last_recv
                                else f"before {effective_date.date().isoformat()}") if effective_date else None,
        "days_in_stock": days_in_stock,
        "aging_bucket": aging_bucket_of(days_in_stock),
        "never_dispensed_anywhere": b["product"] not in dispensed_products_anywhere,
        "original_batch_date": ob_date.date().isoformat() if ob_date else None,
        "original_batch_type": ORIGINAL_BATCH_TYPE_LABEL.get(ob_rec["t_type"]) if ob_rec else None,
        "original_batch_days_in_stock": ob_days,
        "original_batch_aging_bucket": aging_bucket_of(ob_days),
        "original_batch_store_name": ob_rec.get("store_name") if (ob_rec and ob_store_differs) else None,
    })
never_dispensed.sort(key=lambda r: -(r["days_in_stock"] if r["days_in_stock"] is not None else 10**9))

never_dispensed_all_branches = [r for r in never_dispensed if r["never_dispensed_anywhere"]]

def nd_bucket_summary(rows_, bucket_field="aging_bucket"):
    agg = {bk: {"count": 0, "qty": 0.0, "value": 0.0} for bk in BUCKET_ORDER}
    for r in rows_:
        a = agg[r[bucket_field]]
        a["count"] += 1
        a["qty"] += r["on_hand"]
        a["value"] += (r["on_hand_cost"] or 0)
    return [{"bucket": bk, "count": agg[bk]["count"], "qty": round(agg[bk]["qty"], 2), "value": round(agg[bk]["value"], 2)}
            for bk in BUCKET_ORDER]

def nd_rollup_by_branch(rows_):
    agg = defaultdict(lambda: {"count": 0, "qty": 0.0, "value": 0.0})
    for r in rows_:
        a = agg[r["org"]]
        a["count"] += 1
        a["qty"] += r["on_hand"]
        a["value"] += (r["on_hand_cost"] or 0)
    out = [{"org": org, "branch": BRANCH_NAMES.get(org, org), "count": v["count"],
            "qty": round(v["qty"], 2), "value": round(v["value"], 2)} for org, v in agg.items()]
    out.sort(key=lambda r: -r["value"])
    return out

never_dispensed_value_total = round(sum((r["on_hand_cost"] or 0) for r in never_dispensed), 2)
never_dispensed_all_branches_value_total = round(sum((r["on_hand_cost"] or 0) for r in never_dispensed_all_branches), 2)
never_dispensed_all_branches_sku_count = len(set(r["product"] for r in never_dispensed_all_branches))
original_batch_coverage = sum(1 for r in never_dispensed if r["original_batch_date"])

never_dispensed_block = {
    "rows": never_dispensed,
    "bucket_order": BUCKET_ORDER,
    "extract_window_start": extract_min_date.date().isoformat() if extract_min_date else None,
    "original_batch_coverage": original_batch_coverage,
    "original_batch_coverage_total": len(never_dispensed),
    "bucket_summary_by_branch_scope": nd_bucket_summary(never_dispensed),
    "bucket_summary_all_branches_scope": nd_bucket_summary(never_dispensed_all_branches),
    "bucket_summary_original_batch_by_branch_scope": nd_bucket_summary(never_dispensed, "original_batch_aging_bucket"),
    "bucket_summary_original_batch_all_branches_scope": nd_bucket_summary(never_dispensed_all_branches, "original_batch_aging_bucket"),
    "value_by_branch_scope": nd_rollup_by_branch(never_dispensed),
    "value_by_branch_all_branches_scope": nd_rollup_by_branch(never_dispensed_all_branches),
}

# ---------------------------------------------------------------------------
# Assemble
# ---------------------------------------------------------------------------
audit = {
    "meta": {
        "generated_at": datetime.utcnow().isoformat()+"Z",
        "entity": "Al Faihaa Group",
        "source": "Cure+ (read-only) -- EXSYS Inventory Module, live-pulled 2026-10-06",
        "as_of": as_of.isoformat(),
        "branches_covered": sorted(set(b["org"] for b in balances)),
        "branch_names": BRANCH_NAMES,
        "methodology_doc": "Inventory_Analysis_Audit_Direct.md (Safan/AlFaiha demo original) + this rebuild's own findings below",
        "total_transaction_rows": total_rows,
        "malformed_rows_dropped": malformed_count,
        "batch_rows_total": batch_rows_total,
        "purchase_invoice_lines": len(pi_rows),
        "any_purchase_discount_found": any_discount,
        "minmax_is_uniform_default": minmax_is_uniform_default,
        "minmax_default_value": minmax_top[0] if minmax_is_uniform_default else None,
        "cost_source_note": "IM_PRODUCT_MASTER.PRODUCT_AVERAGE_COST/EXTERNAL_COST_PRICE are ~100% NULL for this tenant; on-hand valuation uses each product's most recent transaction unit cost (moving-average proxy) instead.",
        "findings": [
            "Scope: all 4 Al Faihaa branches (Riyadh, Buraydah 1, Buraydah 2, Rafha) show live inventory activity in this extract -- the prior README note that the inventory module was 'Riyadh-only' does not hold for this Cure MCP pull; re-verify operationally, but build accordingly as company-wide.",
            "Costing: IM_PRODUCT_MASTER.PRODUCT_AVERAGE_COST / EXTERNAL_COST_PRICE are essentially 100% NULL (15,006 of 15,007 products) -- valuation instead uses each (branch, store, product)'s most recent transaction PRIMARY_UNIT_COST as a moving-average proxy; a small number of SKUs with on-hand stock but no transaction cost history are flagged unknown_cost_skus per store and excluded from the value sum, not assumed zero.",
            "Overstock: IM_STORE_PRODUCTS-equivalent MIN/REORDER/MAX (1/2/3) is identical across all 1,328+ balance rows -- a config default, not calibrated per product; the ERP's own 'on_hand > max_qty' rule would flag ~75% of inventory value as overstock. The real method used here is 6-month trailing days-of-cover (>365 days or zero consumption), both numbers are reported so the gap is visible in-tab.",
            f"Data-quality: {malformed_count} of {total_rows} transaction rows were dropped as column-shift parser artifacts (a known Cure MCP ASCII-table quirk when a text field contains an embedded newline) -- negligible (<0.03%) but noted for transparency.",
            f"Correction (user-reported 2026-09-19, 'how it's come with no cost and no last movement'): {reconstructed_count} transaction rows for 2 SKUs (100571 CANNULA FILLER 25G 50 MM, 104532 SDR 15 DOSES -- both Riyadh Main Store) were a more severe case of the same export column-shift bug -- the row's tail (org, store, date, cost, qty onward) spilled onto the NEXT physical row re-anchored at column A instead of continuing at column 9. The truncated head row still had a valid transaction type, so it slipped past the malformed-row filter with every downstream field blank, while its shifted tail correctly failed the filter (invalid type) and was dropped -- silently discarding the real cost/date for that SKU and showing as 'no cost' / 'never moved' on Overstock and Slow-Moving even though the ERP's own Product Transactions screen shows full history. Fixed by detecting a valid-type row with organization_no AND stock_account both blank and splicing it back together with the next row's data (verified field-by-field against the ERP screen before applying). Both SKUs now carry their real last transaction cost and movement date; total inventory value moved by a negligible amount (~SAR 2,016 combined for both items).",
            "Batch/expiry tracking IS populated for this tenant (unlike the original demo-entity build) -- expiry risk below is computed from real IM_STORE_PRODUCT_BATCHS-equivalent batch balances, not a receipt-date proxy.",
            "Purchasing: 1,558 of 2,917 purchase lines (53%) carry a non-zero item_discount amount. The primary_unit_cost field used throughout this analysis is sourced from the transaction-posting cost column (matching IM_ALL_TRANSACTIONS.PRIMARY_UNIT_COST in the schema map), which the source methodology confirms posts NET of line discount -- so no further discount correction was applied here. This inference should be spot-checked against a raw purchase invoice screen before quoting supplier savings figures externally.",
            "UOM: purchase-line unit costs in this extract are already expressed per the product's primary/stocking unit (a uom_factor column is carried separately for reference) -- spot-checked against products purchased under 2+ different purchase UOMs, prices land in the same range once qty is treated as uom_factor-scaled. No further UOM normalization correction was needed (unlike the original demo-entity finding).",
            "Coverage: 881 Balance+Config rows carry organization_no='01' / store_id='1' / store_name='main store' (lowercase, distinct from the operational 'Main Store' at store_id=2) -- every one of these rows has zero on-hand quantity and no matching transaction history; treated as a stale/legacy store-config entry, excluded from valuation, not reported as a finding requiring action beyond this note. The Dental Store (store_id=6, Riyadh) similarly shows zero on-hand in this pull.",
            "Correction (caught by user spot-check against the ERP's own Product Transactions screen): the original Slow-Moving / dead-stock check flagged items purely on 'no dispense in 90+ days', which wrongly caught stock that was simply too new to have moved yet -- e.g. HEXAXIM VACCINE (0360033, Riyadh Main Store) was purchased 2026-09-01 (16 days before this as-of date) and had never been dispensed from that purchase, but showed as 'never dispensed / slow-moving' because its 2025 dispense history predates this extract's 2026-01-01 window. Both Slow-Moving and the zero-consumption branch of Overstock now also require the item's most recent receipt (purchase or transfer-in) to be at least 90 days old before flagging -- a 'last_received' column is shown on both tabs so a recent restock is visible rather than hidden.",
            "Correction (user-identified): Overstock and Slow-Moving originally counted only DS (dispense) as outbound movement. Riyadh Main Store is the central purchasing/storage warehouse for all 4 branches, so stock held there also leaves via TS (send-transfer) to the other 3 branches -- counting DS alone understated its real turnover and overstated its overstock/dead-stock reading. Both checks now treat DS+TS together as outbound movement, company-wide (not a Riyadh-only special case, though Riyadh Main Store accounts for ~88% of all TS volume so that is where the effect concentrates). Overstock rows now show 'dispensed_qty_6mo' and 'transferred_out_qty_6mo' separately; Slow-Moving rows show a 'last_out_type' (dispense vs transfer-out) alongside 'last_out_date'.",
            "Addition (user-requested 2026-09-21): Never-Dispensed / Aging Bucket check -- items on hand at a store that have NEVER once been dispensed (DS) from that exact store, aged from their last receipt (purchase PI or transfer-in TR) to as_of, bucketed 0-30/31-60/61-90/91-120/121-180/180+ days. A stricter 'never_dispensed_anywhere' flag additionally requires zero dispense activity for that product code at ANY store across all 4 branches -- this is the case the user specifically flagged: stock that circulates between warehouses via transfer without ever reaching a clinic/patient anywhere, which is pure dead capital regardless of which branch happens to be holding it today.",
            f"Refinement (user-clarified 2026-09-21, 'some items no receipt on file ... may come from opening balance that has date you can calculate'): a never-dispensed key with no PI/TR row anywhere in the extract is not truly unaged -- this extract's own transaction window runs {extract_min_date.date().isoformat() if extract_min_date else '?'} to {as_of.date().isoformat()}, so on-hand stock at such a key must have already been there before {extract_min_date.date().isoformat()} (an implicit opening balance never re-purchased or re-transferred since). Aging Bucket now treats {extract_min_date.date().isoformat() if extract_min_date else '?'} as a calculable lower-bound entry date for these rows (entry_type 'Opening balance (pre-extract)', entry_date_estimated=true, shown as 'before {extract_min_date.date().isoformat() if extract_min_date else '?'}') instead of leaving them bucketed Unknown -- since that lower bound is already >180 days before as_of, every such row now falls in the 180+ bucket, which is the correct (if conservative) read: these are the oldest, least-visible dead stock in the file, not merely undated.",
            "Correction (found 2026-09-21 while investigating the Original Batch Date request): 100571 CANNULA FILLER 25G 50 MM at Riyadh Main Store was wrongly listed as never-dispensed. Its export rows have a THIRD, more severe form of the same row-loss issue -- not the column-shift case already fixed above, and not the 'no 2026 rows at all' case also already fixed above, but a partial one: some of a SKU's 2026 transactions are present (a purchase and a send-transfer reconstructed fine) while others are simply absent from the file outright, including the one dispense that mattered here (DSP01-26-001026, 2026-05-02, confirmed against the live ERP). All 198 never-dispensed rows were re-checked against the live system for any in-window dispense of this kind -- 100571 was the only one affected. Backfilled the same way as the existing cost_backfill_live.json gap-fills (applied only because this exact key had no DS row of its own, never overriding real data); it now correctly drops off the never-dispensed list. Total never-dispensed value -SAR 269.97 (was 62,599.69, now 62,329.72); row count 198 -> 197.",
            f"Addition (user-requested 2026-09-21, 'Original Batch date'): each of the {original_batch_coverage} of {len(never_dispensed)} never-dispensed rows now also carries original_batch_date/_type/_days_in_stock/_aging_bucket -- the (org,product)'s EARLIEST-EVER transaction anywhere in that branch, live-queried directly from the ERP. Deliberately scoped by org+product, not by the row's own (org,store,product) key: verified against the user's own ERP screenshot for 0050418 that a batch's true Opening Balance can sit under a DIFFERENT store within the same branch (Dental Store, 2019-01-01) from where it was later transferred to and sits today (Main Store, 2020-11-10, which is exactly what the existing entry-date basis already reports) -- scoping to the current store alone would silently miss that earlier opening balance. original_batch_store_name is set whenever the original store differs from the row's current one, so that's visible rather than hidden. This sits ALONGSIDE the existing entry-date basis, never replacing it -- entry-date answers 'how long since this stock last moved into its current store', original-batch-date answers 'how old is this batch, full stop', and the two can differ by years. The dashboard and Excel both expose a toggle/columns for either basis. The bucket set is also extended everywhere (both bases) with a 365-day split -- 121-180 / 181-365 / 365+ in place of the old flat 180+ -- per the user's request.",
            f"Expiry Risk now carries a SAR value per batch (qty_on_hand x the same moving-average unit-cost proxy used for on-hand valuation, with the same any-store-for-product fallback -- {unknown_cost_batches} of {len(expiry_risk)+len(past_expiry)} at-risk/past-expiry batches have no cost history anywhere and are excluded from the value sum, not assumed zero), plus a per-branch and company-wide value rollup for both Near-Expiry and Past-Expiry so risk can be sized in SAR, not just batch counts.",
            "Correction (user-reported 2026-09-19, further SKUs still showing 'no cost'/'no value' after the column-shift fix above): 58 (org,store,product) balance keys -- 48 distinct SKUs, e.g. ECG AT-101 (3100062, 102 on hand, Riyadh Main Store) -- had genuinely zero rows anywhere in this extract, not corrupted ones. Root cause: this file only covers 'Transactions 2026', and these SKUs' last real movement was in 2025 or earlier per the ERP, so there was nothing 2026-dated to parse a cost or date from, however carefully. Fixed by querying the live ERP directly (Cure MCP, IM_PRODUCTS_TRANSACTIONS) for each affected key's single most recent cost-bearing transaction of any date, and seeding it into the cost/movement lookup ONLY where this extract had no row at all for that exact key -- see cost_backfill_live.json alongside this script; it never overrides a real 2026 value. One further gap (0390294 at Rafha, surfaced only in a past-expiry batch) was found and backfilled the same way. 'No cost'/'no value' is now fully cleared across every tab -- 0 of 1,328 balance rows remain unpriced (was 58).",
        ],
    },
    "kpi": {
        "total_inventory_value": total_value_all,
        "sku_count": total_sku_all,
        "overstock_value": overstock_value,
        "overstock_sku_count": len(overstock),
        "overstock_pct_of_value": round(100*overstock_value/total_value_all,1) if total_value_all else None,
        "raw_erp_overstock_value_config_artifact": raw_erp_overstock_value,
        "raw_erp_overstock_sku_count_config_artifact": len(raw_erp_overstock),
        "slow_moving_value": slow_moving_value,
        "slow_moving_sku_count": len(slow_moving),
        "expiry_risk_sku_count": len(expiry_risk),
        "expiry_risk_value": near_expiry_value_total,
        "past_expiry_on_hand_count": len(past_expiry),
        "past_expiry_value": past_expiry_value_total,
        "receiving_flag_count": len(receiving_flags),
        "price_gap_savings_identified": round(sum((r["priciest_price"]-r["cheapest_price"]) for r in savings_opportunities if r["priciest_price"] and r["cheapest_price"]),2),
        "never_dispensed_by_branch_row_count": len(never_dispensed),
        "never_dispensed_by_branch_value": never_dispensed_value_total,
        "never_dispensed_all_branches_sku_count": never_dispensed_all_branches_sku_count,
        "never_dispensed_all_branches_row_count": len(never_dispensed_all_branches),
        "never_dispensed_all_branches_value": never_dispensed_all_branches_value_total,
    },
    "valuation_by_store": valuation_by_store,
    "overstock": overstock,
    "slow_moving": slow_moving,
    "expiry_risk": expiry_risk,
    "past_expiry_on_hand": past_expiry,
    "expiry_value_by_branch": {"near_expiry": near_expiry_by_branch, "past_expiry": past_expiry_by_branch},
    "receiving_flags": receiving_flags[:200],
    "cross_org_peer_audit": cross_org_peer_audit,
    "dispense_by_cost_center": dispense_by_cc,
    "purchases_by_supplier": purchases_by_supplier,
    "product_supplier_price_matrix": matrix,
    "supplier_savings_opportunities": savings_opportunities[:200],
    "price_outliers_flagged": outlier_matrix_rows[:200],
    "never_dispensed": never_dispensed_block,
}

OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(f"wrote {OUT} -- total_value={total_value_all} sku={total_sku_all} overstock={len(overstock)} "
      f"slow_moving={len(slow_moving)} expiry_risk={len(expiry_risk)} receiving_flags={len(receiving_flags)} "
      f"savings_opps={len(savings_opportunities)}")
