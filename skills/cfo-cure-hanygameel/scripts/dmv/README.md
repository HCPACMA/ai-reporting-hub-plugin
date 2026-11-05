# dmv — cash flow · direct method at voucher level (29 Sep 2026)

Pipeline (Cure MCP only, branch='ALL', cut-off {D1}):
1. Run the SQL in `kit/sql/cashflow_direct_voucher_level.sql`; save results as r_alloc2.json, r_cash.json, r_ins.json;
   non-cash lines -> ncv.json (list of [v,dt,a,net]); voucher drill -> vch.json; descriptions -> desc.json; mixed -> mixed.json.
2. The indirect statement comes from the normal refresh (gl_annual / gl_drcr with the same cut-off) -> gl/data_cfa_gl.json.
3. `python3 build_cfd.py` -> gl/data_cfa_fixed.json (indirect, non-cash removed, NC line added) + dmv/data_cfd.json.
   refresh.py build runs it automatically and patches DATA.cfa (fixed) and DATA.cfd.
4. Gates (build_cfd asserts): fixed indirect CFO = direct CFO every year; closing = balance-sheet cash; monthly Σalloc = Δcash.
Front end: kit/templates/cfa.js (indirect + shared non-cash card), cfd.js (direct tab), cfd.css.
