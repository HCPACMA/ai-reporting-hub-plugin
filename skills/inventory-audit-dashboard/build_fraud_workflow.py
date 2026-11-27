#!/usr/bin/env python3
"""
build_fraud_workflow.py -- workflow-aware correction layer for the Fraud Detection tab (2026-10-01).

WHY: the store-transfer process is a designed 3-step posting chain (confirmed by Hany, 2026-10-01 and
verified in the ERP tables IM_STOCK_SND_TRANSFER_M / IM_STOCK_RCV_TRANSFER_M):
  1. the sending storekeeper posts the Send Transfer (t_type TS) so the receiver can see it;
  2. the receiving storekeeper creates AND posts the Receive Transfer (t_type TR) -- that post IS the
     receipt and makes them responsible for the stock;
  3. the store accountant reviews the documents and, once receipt is confirmed, does the consolidated
     (monthly) GL posting of the sends (posted_by on the TS rows; one JV1-26/xxxxx per batch).
So "created_by == posted_by" on a TR row is step 2 working as designed, and a TS row's post_date is the
accountant's consolidated posting date, not a late individual posting.

This script re-reads the same raw extract as build_alfaihaa_fraud_detection.py and writes
fraud_workflow.json beside it (additive; does not touch alfaihaa_inventory_audit.json).
Run it after build_alfaihaa_fraud_detection.py.
"""
import json, statistics
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
import openpyxl

SRC = Path(__file__).resolve().parents[2] / "Riyadh_Inventory_Data_2026.xlsx"
OUT = Path(__file__).parent / "fraud_workflow.json"
BRANCH_NAMES = {"01": "Riyadh", "02": "Buraydah 1", "03": "Buraydah 2", "04": "Rafha"}
VALID = {"DS", "TS", "TR", "PI", "CRC", "PR"}

def to_f(v):
    if v is None: return None
    if isinstance(v, (int, float)): return float(v)
    s = str(v).strip()
    try: return float(s) if s and s.lower() not in ("none", "null") else None
    except ValueError: return None
def to_dt(v):
    if isinstance(v, datetime): return v
    s = str(v).strip() if v is not None else ""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s[:19], fmt)
        except ValueError: pass
    return None
def norm_store(v):
    f = to_f(v)
    return str(int(f)) if f is not None else (str(v).strip() if v is not None else None)

wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
names = {}
pw = wb["Products+Costing"]; it = pw.iter_rows(values_only=True)
ph = list(next(it)); pi = {h: i for i, h in enumerate(ph)}
for r in it:
    names[r[pi["product_code"]]] = r[pi["description_p"]] or r[pi["description_s"]] or r[pi["product_code"]]

ws = wb["Transactions 2026"]; it = ws.iter_rows(values_only=True)
hdr = list(next(it)); ix = {h: i for i, h in enumerate(hdr)}

posted_total = 0; tr_posted = 0
su_type = Counter(); user_posted = Counter(); user_tr_posted = Counter()
user_su = defaultdict(Counter)
rows_excl_tr = []
lag = defaultdict(list)
for row in it:
    tt = row[ix["t_type"]]
    if tt not in VALID: continue
    org = row[ix["organization_no"]]; store = norm_store(row[ix["store_id"]])
    if org is None or store is None: continue
    cb = row[ix["created_by"]]; pb = row[ix["posted_by"]]
    dt = to_dt(row[ix["transaction_date"]]); pdt = to_dt(row[ix["post_date"]])
    if pb:
        posted_total += 1; user_posted[pb] += 1
        if tt == "TR": tr_posted += 1; user_tr_posted[pb] += 1
        if cb and cb == pb:
            su_type[tt] += 1; user_su[pb][tt] += 1
            if tt != "TR":
                qty = (to_f(row[ix["line_qty"]]) or 0.0) * (to_f(row[ix["uom_factor"]]) or 1.0)
                cost = to_f(row[ix["primary_unit_cost"]])
                val = abs(qty * cost) if cost is not None else None
                pc = row[ix["product_code"]]
                rows_excl_tr.append({
                    "org": org, "branch": BRANCH_NAMES.get(str(org)[:2], org), "store": store,
                    "store_name": row[ix["store_name"]], "product": pc, "product_name": names.get(pc, pc),
                    "t_type": tt, "transaction_type": row[ix["transaction_type"]],
                    "transaction_no": row[ix["transaction_no"]],
                    "transaction_date": dt.isoformat() if dt else None,
                    "created_by": cb, "posted_by": pb, "value": round(val, 2) if val is not None else None,
                })
    if tt == "TS" and dt and pdt:
        lag[str(org)[:2]].append((pdt - dt).total_seconds() / 86400)

user_rows = []
for u, c in user_su.items():
    p_ex = user_posted[u] - user_tr_posted[u]
    s_ex = sum(v for k, v in c.items() if k != "TR")
    user_rows.append({"user": u, "posted_total": user_posted[u], "posted_excl_tr": p_ex,
                      "tr_same_user": c.get("TR", 0), "same_user_excl_tr": s_ex,
                      "same_user_excl_tr_pct": round(100 * s_ex / p_ex, 1) if p_ex else None,
                      "by_type": dict(c)})
user_rows.sort(key=lambda r: r["same_user_excl_tr"], reverse=True)

ts_lag = {}
for o, l in sorted(lag.items()):
    l.sort(); n = len(l)
    ts_lag[o] = {"branch": BRANCH_NAMES.get(o, o), "n_lines": n, "median_days": round(statistics.median(l), 1),
                 "p90_days": round(l[int(n * 0.9)], 1), "max_days": round(l[-1], 1),
                 "gt30": sum(1 for x in l if x > 30), "gt40": sum(1 for x in l if x > 40)}

total_su = sum(su_type.values())
out = {
    "source": "Riyadh_Inventory_Data_2026.xlsx / Transactions 2026",
    "posted_total": posted_total, "tr_posted": tr_posted, "posted_excl_tr": posted_total - tr_posted,
    "same_user_total": total_su, "same_user_by_type": dict(su_type),
    "same_user_excl_tr": total_su - su_type.get("TR", 0),
    "same_user_excl_tr_pct": round(100 * (total_su - su_type.get("TR", 0)) / (posted_total - tr_posted), 2),
    "user_summary_excl_tr": user_rows,
    "sod_rows_excl_tr": rows_excl_tr,
    "ts_consolidation_lag": ts_lag,
}
OUT.write_text(json.dumps(out, ensure_ascii=False))
print("done", {k: out[k] for k in ("posted_total", "tr_posted", "same_user_total", "same_user_excl_tr", "same_user_excl_tr_pct")},
      "rows", len(rows_excl_tr))
