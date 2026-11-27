#!/usr/bin/env python3
"""
build_alfaihaa_inventory.py -- Al Faihaa Group Inventory Analysis & Audit
Rebuilds the Inventory Analysis/Audit module (see ../README.md, ../Inventory_Analysis_Audit_Direct.md,
../EXSYS_Inventory_refresh.sql) for Al Faihaa Group, sourced from data already pulled live via Cure MCP
on 2026-09-09 (../../Riyadh_Inventory_Data_2026.xlsx -- despite the filename this covers all 4 branches,
see Finding A below) plus this script's own computations (no direct DB access here -- pure Python/openpyxl).

Writes alfaihaa_inventory_audit.json next to this script.
"""
from __future__ import annotations
import json, re, statistics
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import openpyxl

SRC = Path(__file__).resolve().parents[2] / "Riyadh_Inventory_Data_2026.xlsx"
OUT = Path(__file__).parent / "alfaihaa_inventory_audit.json"

BRANCH_NAMES = {"01": "Riyadh", "02": "Buraydah 1", "03": "Buraydah 2", "04": "Rafha"}

def to_f(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    if s == "" or s.lower() in ("none", "null", "n/a"): return None
    try: return float(s)
    except ValueError: return None

def to_dt(v):
    if v is None: return None
    if isinstance(v, datetime): return v
    s = str(v).strip()
    if s == "" or s.lower() in ("none", "null"): return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
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

def rows(ws):
    header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
    idx = {h: i for i, h in enumerate(header)}
    n = len(header)
    for r in ws.iter_rows(min_row=2, values_only=True):
        if len(r) < n: r = tuple(r) + (None,) * (n - len(r))   # read-only mode trims trailing empty cells
        yield r, idx

print("[1/6] loading workbook ...")
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)

# ---------------------------------------------------------------------------
# Products+Costing
# ---------------------------------------------------------------------------
print("[2/6] Products+Costing ...")
products = {}
zero_cost = 0
for r, idx in rows(wb["Products+Costing"]):
    code = r[idx["product_code"]]
    ac = to_f(r[idx["product_average_cost"]])
    ec = to_f(r[idx["external_cost_price"]])
    if ac is None and ec is None: zero_cost += 1
    products[code] = {
        "name": r[idx["description_p"]] or r[idx["description_s"]] or code,
        "inv_group": r[idx["inv_group_description"]] if "inv_group_description" in idx else r[idx["inv_group"]],
        "category": r[idx["product_category"]],
        "primary_uom": r[idx["primary_uom"]],
        "active": r[idx["active_flag"]],
        "near_expiry_days": to_f(r[idx["near_expiry_days"]]),
        "control_drug": r[idx["control_drug_flag"]],
        "master_avg_cost": ac,
        "master_ext_cost": ec,
    }
print(f"    {len(products)} products loaded; {zero_cost} with NO cost in IM_PRODUCT_MASTER (Finding: PRODUCT_AVERAGE_COST/EXTERNAL_COST_PRICE ~empty)")

# ---------------------------------------------------------------------------
# Transactions 2026 -- single pass, build all aggregates we need
# ---------------------------------------------------------------------------
print("[3/6] Transactions 2026 (single pass aggregation) ...")
ws = wb["Transactions 2026"]
header = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
idx = {h: i for i, h in enumerate(header)}
NCOLS = len(header)

VALID_TTYPES = {"DS", "TS", "TR", "PI", "CRC", "PR"}
malformed_count = 0
reconstructed_count = 0
total_rows = 0
as_of = datetime(2000,1,1)
extract_min_date = None  # earliest transaction_date found anywhere in the sheet -- the
                          # extract's effective "window start". A balance-row key with on-hand
                          # stock but ZERO PI/TR rows anywhere in the file must have held that
                          # stock since before this date (an implicit opening balance) -- used
                          # by the Aging Bucket / Never-Dispensed check as a calculable lower-
                          # bound entry date instead of leaving those rows "unknown".

last_cost = {}          # (org,store,product) -> (date, unit_cost)
last_ds_date = {}       # (org,store,product) -> date (DS = dispense, outbound to patient/dept)
last_ts_date = {}       # (org,store,product) -> date (TS = send-transfer, outbound to another branch/store)
last_receipt_date = {}  # (org,store,product) -> most recent PI/TR date (was this stock just restocked?)
last_receipt_type = {}  # (org,store,product) -> "PI" or "TR" for whichever transaction set last_receipt_date
ds_qty_6mo = defaultdict(float)   # (org,store,product) -> qty (primary)
ds_monthly_cc = defaultdict(lambda: {"qty": 0.0, "cost": 0.0})  # (org, cc_no, cc_name, yyyymm) -> {}
receipt_qty_by_product = defaultdict(list)  # product -> list of primary qty (PI/TR) for outlier baseline
receiving_lines = []     # candidate outlier raw lines (PI/TR) collected, filtered later
pi_rows = []             # kept for supplier matrix pass
branch_activity = Counter()   # org -> txn count
store_activity = Counter()    # (org,store) -> txn count

# ---------------------------------------------------------------------------
# Known export defect (found while investigating a user-reported "no cost /
# never moved" item, 2026-09-19): a handful of rows in this sheet arrive
# column-shifted -- the source export occasionally splits one logical
# transaction record across two physical spreadsheet rows. The first
# physical row keeps only columns 0-7 (t_type..product_category_description);
# columns 8 (stock_account) onward spill onto the NEXT physical row,
# re-anchored at column A instead of continuing at column 9. That head row
# still has a syntactically valid t_type, so it used to slip past the
# malformed-row filter with organization_no/store/cost/date all None (->
# "no cost"/"never moved" for that SKU downstream), while its tail row has
# an invalid t_type (a raw stock_account code, e.g. '1230001') and was
# correctly dropped as malformed -- silently discarding the real data.
# Verified against the ERP screen for product 100571: reconstructing splices
# the head row's cols 0-7 with the tail row's cols 0-38 (remapped to logical
# cols 8-46) and every field lines up (org/store/date/cost/qty all sane).
# ---------------------------------------------------------------------------
def reconstruct_shifted_row(head, tail):
    full = list(head[:8]) + [None] * (NCOLS - 8)
    n = min(len(tail), NCOLS - 8)
    for j in range(n):
        full[8 + j] = tail[j]
    return tuple(full)

raw_rows = [r for r in ws.iter_rows(min_row=2, values_only=True)]
clean_rows = []
i = 0
n_raw = len(raw_rows)
while i < n_raw:
    r = raw_rows[i]
    total_rows += 1
    tt = r[idx["t_type"]]
    if (tt in VALID_TTYPES and r[idx["organization_no"]] is None
            and r[idx["stock_account"]] is None and i + 1 < n_raw):
        r = reconstruct_shifted_row(r, raw_rows[i + 1])
        reconstructed_count += 1
        clean_rows.append(r)
        i += 2
        continue
    if tt not in VALID_TTYPES:
        malformed_count += 1
        i += 1
        continue
    clean_rows.append(r)
    i += 1

for r in clean_rows:
    tt = r[idx["t_type"]]
    org = r[idx["organization_no"]]
    store = norm_store(r[idx["store_id"]])
    pcode = r[idx["product_code"]]
    dt = to_dt(r[idx["transaction_date"]])
    if dt and dt > as_of: as_of = dt
    if dt and (extract_min_date is None or dt < extract_min_date): extract_min_date = dt
    qty = to_f(r[idx["line_qty"]]) or 0.0
    uf = to_f(r[idx["uom_factor"]]) or 1.0
    cost = to_f(r[idx["primary_unit_cost"]])
    primary_qty = qty * uf
    branch_activity[org] += 1
    store_activity[(org, store)] += 1
    key = (org, store, pcode)

    if cost is not None and dt is not None:
        prev = last_cost.get(key)
        if prev is None or dt > prev[0]:
            last_cost[key] = (dt, cost)

    if tt == "DS":
        if dt is not None:
            prev = last_ds_date.get(key)
            if prev is None or dt > prev:
                last_ds_date[key] = dt
        cc_no = r[idx["cost_centet_no"]]
        cc_name = r[idx["cost_center_name"]]
        if dt is not None:
            ym = dt.strftime("%Y-%m")
            k2 = (org, cc_no, cc_name, ym)
            ds_monthly_cc[k2]["qty"] += primary_qty
            ds_monthly_cc[k2]["cost"] += (cost or 0.0) * primary_qty

    if tt == "TS":
        # Send-transfer to another branch/store -- also a real outbound movement of on-hand
        # stock, not just DS. This matters most at Riyadh Main Store, which acts as the
        # central purchasing warehouse for all 4 branches (see Finding on Overstock methodology).
        if dt is not None:
            prevt = last_ts_date.get(key)
            if prevt is None or dt > prevt:
                last_ts_date[key] = dt

    if tt in ("PI", "TR"):
        receipt_qty_by_product[pcode].append(primary_qty)
        if dt is not None:
            prevr = last_receipt_date.get(key)
            if prevr is None or dt > prevr:
                last_receipt_date[key] = dt
                last_receipt_type[key] = tt
        receiving_lines.append({
            "t_type": tt, "org": org, "store": store, "product": pcode,
            "date": dt.isoformat() if dt else None, "qty": primary_qty, "cost": cost,
        })

    if tt == "PI":
        pi_rows.append({
            "org": org, "store": store, "product": pcode,
            "supplier_no": r[idx["supplier_no"]], "supplier_name": r[idx["supplier_description_p"]],
            "date": dt, "primary_qty": primary_qty, "unit_cost": cost,
            "item_discount": to_f(r[idx["item_discount"]]), "invoice_discount": to_f(r[idx["invoice_discount"]]),
        })

print(f"    {total_rows} rows, {malformed_count} malformed/dropped, {reconstructed_count} column-shift rows reconstructed, as_of={as_of.isoformat()}")

# ---------------------------------------------------------------------------
# Live-Cure-MCP cost/movement backfill (added 2026-09-19, user-reported "no cost"
# on more SKUs beyond the 2 column-shift cases above). This extract is scoped to
# "Transactions 2026" -- SKUs with no 2026 activity at all (last real movement in
# 2025 or earlier per the ERP) simply have zero rows here, so last_cost/last_*_date
# can never be populated for them from this file, however carefully it's parsed.
# Confirmed against the live ERP (Cure MCP cure_run_query) for 58 such (org,store,
# product) keys plus 1 more surfaced via past-expiry batches -- see
# cost_backfill_live.json, one row per key: that key's single most recent
# cost-bearing transaction of any date, from IM_PRODUCTS_TRANSACTIONS directly.
# Applied ONLY where this extract has nothing at all for that exact key, so it
# can never override real 2026 data -- a pure gap-fill, not a correction.
# ---------------------------------------------------------------------------
backfill_path = Path(__file__).parent / "cost_backfill_live.json"
backfill_applied = 0
if backfill_path.exists():
    import json as _json
    for rec in _json.loads(backfill_path.read_text(encoding="utf-8")):
        bkey = (rec["org"], rec["store"], rec["product"])
        bdt = to_dt(rec["date"])
        if bkey not in last_cost:
            last_cost[bkey] = (bdt, rec["cost"])
            backfill_applied += 1
        if rec["t_type"] == "DS" and bkey not in last_ds_date:
            last_ds_date[bkey] = bdt
        elif rec["t_type"] == "TS" and bkey not in last_ts_date:
            last_ts_date[bkey] = bdt
        elif rec["t_type"] in ("PI", "TR") and bkey not in last_receipt_date:
            last_receipt_date[bkey] = bdt
            last_receipt_type[bkey] = rec["t_type"]
    print(f"    live-backfill: {backfill_applied} (org,store,product) keys with zero 2026 rows seeded from {backfill_path.name}")

# Pass 2: recompute ds_qty_6mo correctly now that as_of is final (need a real second pass -- cheap, same in-memory rows)
print("[4/6] second pass for 6-month consumption window ...")
ds_qty_6mo = defaultdict(float)
ts_qty_6mo = defaultdict(float)
window_start = as_of - timedelta(days=180)
for r in clean_rows:
    tt2 = r[idx["t_type"]]
    if tt2 not in ("DS", "TS"): continue
    dt = to_dt(r[idx["transaction_date"]])
    if dt is None or dt < window_start: continue
    qty = to_f(r[idx["line_qty"]]) or 0.0
    uf = to_f(r[idx["uom_factor"]]) or 1.0
    primary_qty = qty * uf
    if primary_qty >= 1000: continue  # outlier guard
    key = (r[idx["organization_no"]], norm_store(r[idx["store_id"]]), r[idx["product_code"]])
    if tt2 == "DS":
        ds_qty_6mo[key] += primary_qty
    else:
        ts_qty_6mo[key] += primary_qty

last_out_90_cutoff = as_of - timedelta(days=90)

# ---------------------------------------------------------------------------
# Balance+Config -- current on-hand position
# ---------------------------------------------------------------------------
print("[5/6] Balance+Config ...")
balances = []
for r, bidx in rows(wb["Balance+Config"]):
    onhand = to_f(r[bidx["onhand_qty"]]) or 0.0
    if onhand <= 0: continue
    org_raw = r[bidx["organization_no"]]
    store_raw = r[bidx["store_id"]]
    branch_org = branch_org_of(org_raw)
    store_n = norm_store(store_raw)
    pcode = r[bidx["product_code"]]
    key = (branch_org, store_n, pcode)
    cost = last_cost.get(key, (None, None))[1]
    if cost is None:
        # fallback: latest cost for this product at ANY store/branch
        alt = [v[1] for k, v in last_cost.items() if k[2] == pcode]
        cost = alt[-1] if alt else None
    balances.append({
        "org": branch_org, "org_raw": org_raw, "org_name": r[bidx["organization_name"]],
        "store": store_n, "store_raw": store_raw, "store_name": r[bidx["store_name"]],
        "product": pcode, "product_name": r[bidx["product_name"]],
        "uom": r[bidx["uom_code"]],
        "on_hand": onhand,
        "min_qty": to_f(r[bidx["min_qty"]]), "reorder_qty": to_f(r[bidx["reorder_qty"]]), "max_qty": to_f(r[bidx["max_qty"]]),
        "unit_cost": cost,
        "on_hand_cost": round(onhand * cost, 2) if cost is not None else None,
        "cost_is_estimated": cost is None,
    })
print(f"    {len(balances)} balance rows with on_hand>0")

wb.close()
print(f"[6/6] writing partial state for further analysis in a second script ...")

import pickle
with open(Path(__file__).parent / "_state.pkl", "wb") as f:
    pickle.dump({
        "as_of": as_of, "extract_min_date": extract_min_date, "balances": balances, "products": products,
        "last_cost": last_cost,
        "last_ds_date": last_ds_date, "last_ts_date": last_ts_date,
        "last_receipt_date": last_receipt_date, "last_receipt_type": last_receipt_type,
        "ds_qty_6mo": dict(ds_qty_6mo), "ts_qty_6mo": dict(ts_qty_6mo),
        "ds_monthly_cc": {k: v for k, v in ds_monthly_cc.items()},
        "receipt_qty_by_product": dict(receipt_qty_by_product),
        "receiving_lines": receiving_lines, "pi_rows": pi_rows,
        "branch_activity": branch_activity, "store_activity": store_activity,
        "malformed_count": malformed_count, "total_rows": total_rows, "reconstructed_count": reconstructed_count,
    }, f)
print("done -- state saved to _state.pkl")
