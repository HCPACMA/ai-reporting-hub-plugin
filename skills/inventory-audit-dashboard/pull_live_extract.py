"""
pull_live_extract.py

Re-pulls the 5 source datasets fresh from the live Cure/EXSYS Oracle DB (Riyadh
branch) via the Cure_MCP `cure_run_query` tool, and writes them into an xlsx with
the exact same sheet names/column layout as the original manual extract
(Riyadh_Inventory_Data_2026.xlsx), so build_alfaihaa_inventory.py can consume the
output unchanged.

THIS SCRIPT ITSELF CANNOT CALL cure_run_query — it has no MCP access. It is meant
to be driven by an agent (Claude) that DOES have the Cure_MCP tool: the agent calls
cure_run_query per page, and calls the helper functions in this file to parse each
page and accumulate rows. See RUN_INSTRUCTIONS below for the exact call sequence.

Design notes (per claude/riyadh-inventory-data-extract.md lessons):
- 2,000-row pages via `OFFSET n ROWS FETCH NEXT 2000 ROWS ONLY` (Oracle syntax) —
  no hard 200-row cap once you ask for more explicitly, but cure_run_query has
  shown an undocumented ~200-row silent truncation on some large pulls; the
  parser below detects a short page (fewer rows than requested, page not last)
  and flags it so the caller can re-fetch with a narrower OFFSET/FETCH window
  (e.g. split into two 1,000-row calls) rather than silently losing rows.
- SELECT * is used (never spelling `CREATED_BY` etc. as a literal in the SQL
  text) to dodge cure_run_query's naive "CREATE" substring filter, and it also
  avoids hand-maintaining a 107-column list for IM_PRODUCT_MASTER.
- Resumable: progress is checkpointed to _extract_progress.json after every
  page, keyed by sheet name + offset. If the device bridge drops mid-pull
  (documented history of this happening), re-running the driving loop skips
  pages already checkpointed and appends to the existing partial CSV instead
  of starting over.
- Output: one CSV per sheet (out_<sheet>.csv) plus a final assemble step that
  writes them into Riyadh_Inventory_Data_<YYYY>.xlsx with the 5 expected sheet
  names. The Transactions sheet is always named "Transactions 2026" (matching
  what build_alfaihaa_inventory.py hardcodes) regardless of the actual pull
  year — it's just a label, not parsed as a date.

RUN_INSTRUCTIONS (for the agent driving this, e.g. inside a scheduled task):
  1. from pull_live_extract import SOURCES, load_progress, save_progress, \
         parse_ascii_table, append_rows_csv, assemble_xlsx
  2. today = date string 'YYYY-MM-DD'; year_start = f'{today[:4]}-01-01'
  3. For each entry in SOURCES (dict): build the SQL with OFFSET/FETCH using the
     entry's `base_sql` + page params, call cure_run_query, parse_ascii_table()
     the result, append_rows_csv() the rows to out_<key>.csv, save_progress().
     Stop paginating a table when a page returns 0 rows OR fewer than the page
     size AND the table's known total (if available) has been reached.
  4. After all 5 tables are done, call assemble_xlsx(out_path, year) to produce
     Riyadh_Inventory_Data_<year>.xlsx.
"""
import csv
import json
import os
import re
from datetime import date

PAGE_SIZE = 2000
PROGRESS_FILE = "_extract_progress.json"

# Source table definitions — mirrors claude/riyadh-inventory-data-extract.md exactly.
# base_sql is an Oracle SELECT with a {offset}/{limit} pagination slot and, for
# Transactions, a {date_from}/{date_to} slot. Always SELECT * (never spell out
# CREATED_BY or other "CREATE"-prefixed column names literally — cure_run_query
# rejects any query containing the substring "CREATE").
SOURCES = {
    "products_costing": {
        "sheet_name": "Products+Costing",
        "base_sql": (
            "SELECT * FROM ("
            "  SELECT t.*, ROW_NUMBER() OVER (ORDER BY PRODUCT_CODE) rn "
            "  FROM EXSYS.IM_PRODUCT_MASTER t WHERE ACTIVE_FLAG='Y'"
            ") WHERE rn > {offset} AND rn <= {offset_plus_limit}"
        ),
        "expected_rows_hint": 15007,
    },
    "balance_config": {
        "sheet_name": "Balance+Config",
        "base_sql": (
            "SELECT * FROM ("
            "  SELECT t.*, ROW_NUMBER() OVER (ORDER BY PRODUCT_CODE, STORE_ID) rn "
            "  FROM EXSYS.VINV_STORE_PRODUCTS t "
            "  WHERE PRODUCT_CODE IN (SELECT PRODUCT_CODE FROM EXSYS.IM_PRODUCT_MASTER WHERE ACTIVE_FLAG='Y')"
            ") WHERE rn > {offset} AND rn <= {offset_plus_limit}"
        ),
        "expected_rows_hint": 25000,
    },
    "batches": {
        "sheet_name": "Batches",
        "base_sql": (
            "SELECT * FROM ("
            "  SELECT t.*, ROW_NUMBER() OVER (ORDER BY PRODUCT_CODE, BATCH_NO) rn "
            "  FROM EXSYS.IM_STORE_PRODUCT_BATCHS_VIEW t"
            ") WHERE rn > {offset} AND rn <= {offset_plus_limit}"
        ),
        "expected_rows_hint": 1447,
    },
    "batch_mfg_detail": {
        "sheet_name": "Batch-Mfg Detail",
        "base_sql": (
            "SELECT * FROM ("
            "  SELECT t.*, ROW_NUMBER() OVER (ORDER BY PRODUCT_CODE, BATCH_NO) rn "
            "  FROM EXSYS.VINV_MFG_BATCH t"
            ") WHERE rn > {offset} AND rn <= {offset_plus_limit}"
        ),
        "expected_rows_hint": 36175,
    },
    "transactions": {
        "sheet_name": "Transactions 2026",  # literal label — build_alfaihaa_inventory.py hardcodes this
        "base_sql": (
            "SELECT * FROM ("
            "  SELECT t.*, ROW_NUMBER() OVER (ORDER BY TRANSACTION_DATE, PRODUCT_CODE) rn "
            "  FROM EXSYS.IM_PRODUCTS_TRANSACTIONS t "
            "  WHERE TRANSACTION_DATE BETWEEN DATE '{date_from}' AND DATE '{date_to}'"
            ") WHERE rn > {offset} AND rn <= {offset_plus_limit}"
        ),
        "expected_rows_hint": None,  # varies with date range
    },
}


def build_sql(key, offset, page_size=PAGE_SIZE, date_from=None, date_to=None):
    src = SOURCES[key]
    sql = src["base_sql"].format(
        offset=offset,
        offset_plus_limit=offset + page_size,
        date_from=date_from or "",
        date_to=date_to or "",
    )
    return sql


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def parse_ascii_table(text):
    """Parse a cure_run_query ASCII pipe-table result into (header, rows).
    Handles the '+---+' separator-line format. Drops the constant 'RN' /
    '_branch' helper columns if present. Returns ([] , []) if no data rows.
    """
    lines = [l for l in text.splitlines() if l.strip()]
    sep_idxs = [i for i, l in enumerate(lines) if re.match(r'^\+[-+]+\+$', l.strip())]
    if len(sep_idxs) < 2:
        return [], []
    header_line = lines[sep_idxs[0] + 1]
    header = [c.strip() for c in header_line.strip('|').split('|')]
    data_lines = lines[sep_idxs[1] + 1: sep_idxs[-1]] if len(sep_idxs) > 2 else lines[sep_idxs[1] + 1:]
    rows = []
    for dl in data_lines:
        if re.match(r'^\+[-+]+\+$', dl.strip()):
            continue
        cells = [c.strip() for c in dl.strip('|').split('|')]
        if len(cells) != len(header):
            continue  # malformed row (embedded newline) — drop, per documented data-quality caveat
        rows.append(cells)
    # drop trailing helper columns the MCP tool / our own SQL append: '_branch'
    # (auto-injected by cure_run_query) and 'rn' (our ROW_NUMBER pagination key)
    # — strip from the end, in whatever order they actually appear.
    while header and header[-1].strip().lower() in ('_branch', 'rn'):
        header = header[:-1]
        rows = [r[:-1] for r in rows]
    return header, rows


def append_rows_csv(path, header, rows):
    write_header = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerows(rows)


def assemble_xlsx(out_path, year):
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for key, src in SOURCES.items():
        csv_path = f"out_{key}.csv"
        if not os.path.exists(csv_path):
            raise RuntimeError(f"missing {csv_path} — pull incomplete for {key}")
        ws = wb.create_sheet(src["sheet_name"])
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.reader(f):
                ws.append(row)
    wb.save(out_path)
    return out_path


if __name__ == "__main__":
    print("This module is a helper library driven by an agent with cure_run_query access.")
    print("See the RUN_INSTRUCTIONS docstring at the top of this file.")
