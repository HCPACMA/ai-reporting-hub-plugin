#!/usr/bin/env python3
"""
build_alfaihaa_fraud_detection.py -- Al Faihaa Group Inventory Fraud/Control Detection

Adds a "fraud_detection" section to the existing alfaihaa_inventory_audit.json, covering the
4 categories the user picked (2026-09-21): timing & posting-control anomalies, user &
segregation-of-duties anomalies, pricing & cost anomalies, and movement-pattern anomalies.

This is a SEPARATE, additive pass over the raw extract (Transactions 2026) rather than an
extension of build_alfaihaa_inventory.py/_2.py -- it needs row-level fields those scripts never
captured (created_by, posted_by, post_date, status, receive_store_id, supplier_no on every PI
line), so it re-reads the sheet on its own rather than reusing _state.pkl, and only WRITES a new
top-level key into the existing JSON (never touches any of the other keys). Safe to re-run any
time after build_alfaihaa_inventory.py + _2.py have produced/refreshed the base JSON.

Every check here is grounded in a field-level profiling pass of the actual extract (see the
project doc for the numbers) -- nothing here is a generic template check bolted on without
checking the data supports it. Two things worth noting up front because they shape what's
NOT here: control_drug_flag is populated on essentially 0 of 15,007 products (so no
controlled-substance-specific check was built -- it would show empty), and there is no
"Stock Count" transaction type in this 2026-scoped extract at all (the closest analogue,
"Correction" / t_type CRC, 145 rows, is what the movement-pattern check uses instead).
"""
from __future__ import annotations
import json, statistics
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import openpyxl

SRC = Path(__file__).resolve().parents[2] / "Riyadh_Inventory_Data_2026.xlsx"
OUT = Path(__file__).parent / "alfaihaa_inventory_audit.json"

BRANCH_NAMES = {"01": "Riyadh", "02": "Buraydah 1", "03": "Buraydah 2", "04": "Rafha"}
STORE_TO_ORG = {"2": "01", "3": "02", "4": "03", "5": "04", "7": "01"}
STORE_NAMES = {"2": "Main Store", "3": "Buridah-1 Store", "4": "Buridah-2 Store", "5": "Rafha Store", "7": "Dialysis Store"}

LATE_POSTING_THRESHOLD_DAYS = 30
OFF_HOURS = {0, 1, 2}  # midnight-2:59am -- the sparse tail in the hour histogram (213 of 55,190 txns)
PRICE_DEVIATION_THRESHOLD = 0.25  # 25% away from a product+supplier's own median PI cost
PRICE_MIN_GROUP_SIZE = 3          # need at least 3 PI lines for a product+supplier to have a meaningful median
ROUND_TRIP_WINDOW_DAYS = 60
ROUND_TRIP_QTY_TOLERANCE = 0.15   # out-leg and back-leg qty must be within 15% of each other --
                                   # without this, "same product moves both directions between the
                                   # same two stores within 60 days" mostly just describes normal
                                   # hub-and-spoke rebalancing traffic, not a wash pattern. Requiring
                                   # near-equal quantity is what turns it into a real signal (the
                                   # same physical stock apparently shuttled back rather than used).
CORRECTION_MIN_COUNT = 2          # (org,store,product) keys with >=2 "Correction" (CRC) entries in 2026


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


def branch_of(org):
    return BRANCH_NAMES.get(str(org).strip()[:2], org)


print("[1/6] loading workbook + product names ...")
wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)

product_names = {}
pw = wb["Products+Costing"]
phdr = [c.value for c in next(pw.iter_rows(min_row=1, max_row=1))]
pidx = {h: i for i, h in enumerate(phdr)}
for r in pw.iter_rows(min_row=2, values_only=True):
    code = r[pidx["product_code"]]
    product_names[code] = r[pidx["description_p"]] or r[pidx["description_s"]] or code

ws = wb["Transactions 2026"]
hdr = [c.value for c in next(ws.iter_rows(min_row=1, max_row=1))]
idx = {h: i for i, h in enumerate(hdr)}
VALID_TTYPES = {"DS", "TS", "TR", "PI", "CRC", "PR"}

print("[2/6] single pass over Transactions 2026 ...")
late_posting_rows = []
off_hours_rows = []
user_stats = defaultdict(lambda: {"created": 0, "posted": 0, "same_user": 0, "value": 0.0})
same_user_rows = []
nonstandard_created_rows = []
pi_by_group = defaultdict(list)       # (product, supplier_no) -> list of PI line dicts
ts_by_product = defaultdict(list)     # product -> list of TS line dicts (for round-trip matching)
crc_by_key = defaultdict(list)        # (org,store,product) -> list of CRC line dicts
cancelled_rows = []
pr_rows = []
total_rows = 0
skipped_malformed = 0

for row in ws.iter_rows(min_row=2, values_only=True):
    total_rows += 1
    tt = row[idx["t_type"]]
    if tt not in VALID_TTYPES:
        skipped_malformed += 1
        continue
    org = row[idx["organization_no"]]
    store = norm_store(row[idx["store_id"]])
    pcode = row[idx["product_code"]]
    if org is None or store is None:
        # column-shift-corrupted head row (see build_alfaihaa_inventory.py) -- no reconstruction
        # needed here since this pass only needs the transaction's own fields, not cost/date
        # continuity, but a row missing org/store can't be branch/store-attributed, so skip it.
        continue
    dt = to_dt(row[idx["transaction_date"]])
    pdt = to_dt(row[idx["post_date"]])
    qty = to_f(row[idx["line_qty"]]) or 0.0
    uf = to_f(row[idx["uom_factor"]]) or 1.0
    primary_qty = qty * uf
    cost = to_f(row[idx["primary_unit_cost"]])
    value = abs(primary_qty * cost) if cost is not None else None
    created_by = row[idx["created_by"]]
    posted_by = row[idx["posted_by"]]
    status = row[idx["status"]]
    txn_no = row[idx["transaction_no"]]
    pname = product_names.get(pcode, pcode)
    branch = branch_of(org)

    base = {
        "org": org, "branch": branch, "store": store, "store_name": row[idx["store_name"]],
        "product": pcode, "product_name": pname, "t_type": tt, "transaction_type": row[idx["transaction_type"]],
        "transaction_no": txn_no, "transaction_date": dt.isoformat() if dt else None,
        "created_by": created_by, "posted_by": posted_by, "value": round(value, 2) if value is not None else None,
    }

    # ---- A. Timing & posting-control -------------------------------------------------
    if dt and pdt:
        gap_days = (pdt - dt).total_seconds() / 86400
        if gap_days > LATE_POSTING_THRESHOLD_DAYS:
            r2 = dict(base)
            r2["post_date"] = pdt.isoformat()
            r2["gap_days"] = round(gap_days, 1)
            late_posting_rows.append(r2)
    if dt and dt.hour in OFF_HOURS:
        r2 = dict(base)
        r2["hour"] = dt.hour
        off_hours_rows.append(r2)

    # ---- B. User & segregation-of-duties -----------------------------------------------
    if created_by:
        user_stats[created_by]["created"] += 1
        user_stats[created_by]["value"] += value or 0.0
        if not str(created_by).startswith("EXSYS"):
            nonstandard_created_rows.append(dict(base))
    if posted_by:
        user_stats[posted_by]["posted"] += 1
        if created_by and created_by == posted_by:
            user_stats[created_by]["same_user"] += 1
            if len(same_user_rows) < 500:  # cap the raw sample; full counts are in user_stats
                same_user_rows.append(dict(base))

    # ---- C. Pricing & cost (Purchase lines only) -----------------------------------------
    if tt == "PI" and cost is not None and cost > 0:
        pi_by_group[(pcode, row[idx["supplier_no"]])].append({
            **base,
            "supplier_no": row[idx["supplier_no"]],
            "supplier_name": row[idx["supplier_description_p"]],
            "unit_cost": cost, "qty": primary_qty,
        })

    # ---- D. Movement-pattern -------------------------------------------------------------
    if tt == "TS" and dt:
        ts_by_product[pcode].append({
            **base, "date": dt, "recv_store": norm_store(row[idx["receive_store_id"]]),
            "recv_store_name": row[idx["receive_store_name"]], "qty": primary_qty,
        })
    if tt == "CRC":
        crc_by_key[(org, store, pcode)].append(dict(base))
    if status == "C":
        cancelled_rows.append(dict(base))
    if tt == "PR":
        pr_rows.append(dict(base))

wb.close()
print(f"    {total_rows} rows scanned, {skipped_malformed} malformed/dropped (same defect as the main pipeline)")

# ---------------------------------------------------------------------------------------
print("[3/6] timing & posting-control rollups ...")
late_posting_rows.sort(key=lambda r: r["gap_days"], reverse=True)
late_posting_value = sum(r["value"] or 0 for r in late_posting_rows)
late_posting_by_branch = Counter(r["branch"] for r in late_posting_rows)
off_hours_by_branch = Counter(r["branch"] for r in off_hours_rows)

# ---------------------------------------------------------------------------------------
print("[4/6] user / segregation-of-duties rollups ...")
user_summary = []
for user, s in user_stats.items():
    user_summary.append({
        "user": user, "created_count": s["created"], "posted_count": s["posted"],
        "same_user_count": s["same_user"], "created_value": round(s["value"], 2),
        "same_user_pct": round(100 * s["same_user"] / s["posted"], 1) if s["posted"] else None,
    })
user_summary.sort(key=lambda r: r["same_user_count"], reverse=True)
total_same_user = sum(s["same_user"] for s in user_stats.values())
total_posted = sum(s["posted"] for s in user_stats.values())

# ---------------------------------------------------------------------------------------
print("[5/6] pricing anomalies + movement-pattern (frequent corrections, round-trips, cancellations) ...")
price_anomaly_rows = []
for (pcode, supplier), lines in pi_by_group.items():
    if len(lines) < PRICE_MIN_GROUP_SIZE:
        continue
    costs = [l["unit_cost"] for l in lines]
    med = statistics.median(costs)
    if med <= 0:
        continue
    for l in lines:
        dev = (l["unit_cost"] - med) / med
        if abs(dev) >= PRICE_DEVIATION_THRESHOLD:
            r2 = dict(l)
            r2["group_median_cost"] = round(med, 4)
            r2["deviation_pct"] = round(dev * 100, 1)
            r2["deviation_value"] = round(abs(l["unit_cost"] - med) * l["qty"], 2)
            price_anomaly_rows.append(r2)
price_anomaly_rows.sort(key=lambda r: abs(r["deviation_pct"]), reverse=True)
price_anomaly_value = sum(r["deviation_value"] for r in price_anomaly_rows)

frequent_corrections = []
for (org, store, pcode), lines in crc_by_key.items():
    if len(lines) < CORRECTION_MIN_COUNT:
        continue
    total_val = sum(l["value"] or 0 for l in lines)
    frequent_corrections.append({
        "org": org, "branch": branch_of(org), "store": store,
        "store_name": STORE_NAMES.get(store, lines[0]["store_name"]),
        "product": pcode, "product_name": lines[0]["product_name"],
        "correction_count": len(lines), "total_value": round(total_val, 2),
        "dates": sorted(l["transaction_date"] for l in lines if l["transaction_date"]),
    })
frequent_corrections.sort(key=lambda r: r["correction_count"], reverse=True)

round_trip_pairs = []
for pcode, lines in ts_by_product.items():
    lines.sort(key=lambda l: l["date"])
    for i, a in enumerate(lines):
        if a["recv_store"] is None:
            continue
        for b in lines[i + 1:]:
            if (b["date"] - a["date"]).days > ROUND_TRIP_WINDOW_DAYS:
                break
            if b["store"] == a["recv_store"] and b["recv_store"] == a["store"]:
                bigger = max(a["qty"], b["qty"]) or 1.0
                if abs(a["qty"] - b["qty"]) / bigger > ROUND_TRIP_QTY_TOLERANCE:
                    continue  # different-enough quantity -- ordinary two-way traffic, not a wash pair
                round_trip_pairs.append({
                    "product": pcode, "product_name": a["product_name"],
                    "out_branch": a["branch"], "out_store": a["store"], "out_store_name": a["store_name"],
                    "out_date": a["transaction_date"], "out_qty": a["qty"], "out_txn": a["transaction_no"],
                    "back_branch": b["branch"], "back_store": b["store"], "back_store_name": b["store_name"],
                    "back_date": b["transaction_date"], "back_qty": b["qty"], "back_txn": b["transaction_no"],
                    "days_between": (b["date"] - a["date"]).days,
                })
                break  # one match per outbound leg is enough to flag it

cancelled_by_branch = Counter(r["branch"] for r in cancelled_rows)
cancelled_by_user = Counter(r["created_by"] for r in cancelled_rows if r["created_by"])
pr_value = sum(r["value"] or 0 for r in pr_rows)
pr_by_supplier = Counter()  # PR rows don't carry supplier_no in this pass; kept as a flat list instead

print("[6/6] writing fraud_detection into alfaihaa_inventory_audit.json ...")
data = json.loads(OUT.read_text(encoding="utf-8"))

data["fraud_detection"] = {
    "generated_note": (
        "4 categories, all grounded in fields actually present in the extract (created_by, "
        "posted_by, post_date vs transaction_date, status, supplier_no). No controlled-substance "
        "check: control_drug_flag is unpopulated for 15,006 of 15,007 products. No stock-count-"
        "frequency check: this 2026-scoped extract has zero 'Stock Count' transactions -- "
        "'Correction' (CRC, t_type) is the nearest available analogue and is what's used below."
    ),
    "kpi": {
        "late_posting_count": len(late_posting_rows), "late_posting_value": round(late_posting_value, 2),
        "off_hours_count": len(off_hours_rows),
        "same_user_create_post_count": total_same_user, "same_user_create_post_pct": round(100 * total_same_user / total_posted, 1) if total_posted else None,
        "nonstandard_user_count": len(nonstandard_created_rows),
        "price_anomaly_count": len(price_anomaly_rows), "price_anomaly_value": round(price_anomaly_value, 2),
        "frequent_correction_keys": len(frequent_corrections),
        "round_trip_count": len(round_trip_pairs),
        "cancelled_count": len(cancelled_rows), "purchase_return_count": len(pr_rows), "purchase_return_value": round(pr_value, 2),
        # Sidebar-badge total: the discrete, individually-reviewable categories only.
        # late_posting_count (6,475) is deliberately excluded here -- it's a bulk process-
        # timeliness metric best read as a count+% in its own KPI card, not as 6,475 "flags"
        # dominating a badge meant to signal "how many items are worth a look".
        "total_flags": len(off_hours_rows) + len(price_anomaly_rows) + len(frequent_corrections) + len(round_trip_pairs) + len(cancelled_rows),
    },
    "timing": {
        "late_posting_threshold_days": LATE_POSTING_THRESHOLD_DAYS,
        "late_posting_rows": late_posting_rows[:300],
        "late_posting_total_count": len(late_posting_rows),
        "late_posting_by_branch": dict(late_posting_by_branch),
        "off_hours_window": "00:00-02:59",
        "off_hours_rows": off_hours_rows,
        "off_hours_by_branch": dict(off_hours_by_branch),
    },
    "sod": {
        "user_summary": user_summary,
        "same_user_rows": same_user_rows,
        "same_user_total_count": total_same_user,
        "nonstandard_created_by_rows": nonstandard_created_rows,
    },
    "pricing": {
        "method": f"PI lines grouped by (product, supplier); flagged when unit cost deviates >={int(PRICE_DEVIATION_THRESHOLD*100)}% from that group's own median (group needs >={PRICE_MIN_GROUP_SIZE}+ PI lines to have a meaningful median).",
        "anomaly_rows": price_anomaly_rows[:300],
        "anomaly_total_count": len(price_anomaly_rows),
    },
    "movement": {
        "frequent_corrections": frequent_corrections,
        "round_trip_transfers": round_trip_pairs,
        "round_trip_window_days": ROUND_TRIP_WINDOW_DAYS,
        "cancelled_rows": cancelled_rows,
        "cancelled_by_branch": dict(cancelled_by_branch),
        "cancelled_by_user": dict(cancelled_by_user),
        "purchase_return_rows": pr_rows,
    },
}

OUT.write_text(json.dumps(data, ensure_ascii=False, indent=None), encoding="utf-8")
print(f"done -- late_posting={len(late_posting_rows)} off_hours={len(off_hours_rows)} same_user={total_same_user} "
      f"nonstandard_user={len(nonstandard_created_rows)} price_anomalies={len(price_anomaly_rows)} "
      f"frequent_corrections={len(frequent_corrections)} round_trips={len(round_trip_pairs)} "
      f"cancelled={len(cancelled_rows)} purchase_returns={len(pr_rows)}")
