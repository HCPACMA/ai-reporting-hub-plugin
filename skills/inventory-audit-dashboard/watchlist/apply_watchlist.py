import json, shutil, sys
from datetime import datetime

SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
WD = f"{SCR}/watch"

html = open(WORK, "r", encoding="utf-8").read()
orig_len = len(html)
shutil.copyfile(WORK, f"{SCR}/dashboard_askai.pre_watchlist.html")


def rep(old, new, label, count=1):
    global html
    assert html.count(old) == count, f"{label}: anchor count={html.count(old)}"
    html = html.replace(old, new)


# ------------------------------------------------------------------ 1. data
start_tag = '<script id="audit-data" type="application/json">'
si = html.index(start_tag) + len(start_tag)
ei = html.index("</script>", si)
A = json.loads(html[si:ei])
R = json.load(open(f"{WD}/live_result.json", encoding="utf-8"))
B, WL = R["blocks"], R["watchlist"]

before = {
    "lines": A["meta"]["purchase_invoice_lines"],
    "spend": A["vendor_concentration"]["kpi"]["total_spend_2026"],
    "suppliers": A["vendor_concentration"]["kpi"]["supplier_count"],
    "single_source": A["vendor_concentration"]["kpi"]["single_source_product_count"],
}
A["purchases_by_supplier"] = B["purchases_by_supplier"]
A["product_supplier_price_matrix"] = B["product_supplier_price_matrix"]
A["supplier_savings_opportunities"] = B["supplier_savings_opportunities"]
A["price_outliers_flagged"] = B["price_outliers_flagged"]
A["kpi"]["price_gap_savings_identified"] = B["price_gap_savings_identified"]
V = A["vendor_concentration"]
V["kpi"] = B["vendor"]["kpi"]
V["top_suppliers"] = B["vendor"]["top_suppliers"]
V["by_branch"] = B["vendor"]["by_branch"]
V["single_source_products"] = B["vendor"]["single_source_products"]
n_lines = len([1 for _ in json.load(open(f"{WD}/pi_live_raw.json"))])
V["purchasing_model_note"] = V["purchasing_model_note"].replace(
    "All 2917 purchase-invoice lines in this extract",
    f"All {n_lines:,} posted purchase-invoice lines (January to 29 September 2026, re-pulled live from the ERP) ")
assert "2917" not in V["purchasing_model_note"]
A["meta"]["purchase_invoice_lines"] = n_lines
A["meta"]["findings"][6] += (
    " UPDATE 2026-10-02: the purchase-invoice lines were re-pulled live from the ERP (posted lines only, 3,099 lines to 29 Sep). "
    "Net-of-discount is now verified rather than inferred: on all 200 posted 2026 lines that carry both an item discount and VAT, "
    "VAT equals 15% of quantity x unit cost (net), and on none of them 15% of the gross amount; on a 50-line check of lines with an "
    "invoice-level discount, 48 also tie to the net amount. Invoice-level discounts (22% of lines) are not verified exhaustively.")
A["meta"]["purchasing_refresh"] = {
    "refreshed_on": "2026-10-02", "source": "IM_PRODUCTS_TRANSACTIONS, T_TYPE = PI, STATUS = P, 2026-01-01 to 2026-09-30",
    "lines": n_lines, "previous_snapshot_lines": before["lines"], "previous_snapshot_spend": before["spend"],
    "note": ("The earlier snapshot (to 8 Sep) was missing every purchase line dated 8 March 2026 (46 lines, SAR 47,176) and had one "
             "cancelled line and one 1 Feb line out of step with the ERP; the live pull fixes all three and adds 9-29 Sep."),
}
A["watchlist"] = WL

js = json.dumps(A, ensure_ascii=False, separators=(",", ":"))
assert "</" not in js
html = html[:si] + js + html[ei:]

# ------------------------------------------------------------------ 2. CSS
css = """
/* ---------- Price & vendor watch-list ---------- */
#panel-watch .wlcell{display:inline-flex; align-items:center; gap:4px; white-space:nowrap;}
#panel-watch .wlsel{font:inherit; font-size:12px; padding:3px 5px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--ink); max-width:150px;}
#panel-watch .wlsel[data-v="ack"]{background:var(--blue-soft); color:var(--blue); border-color:var(--blue-soft);}
#panel-watch .wlsel[data-v="negotiating"]{background:var(--amber-soft); color:var(--amber); border-color:var(--amber-soft);}
#panel-watch .wlsel[data-v="resolved"]{background:var(--accent-soft); color:var(--accent); border-color:var(--accent-soft);}
#panel-watch .wlsel[data-v="accepted"]{background:var(--surface-2); color:var(--ink-2);}
#panel-watch .wlnote{appearance:none; border:0; background:none; color:var(--ink-mute); cursor:pointer; font-size:14px; padding:2px 3px; opacity:.55;}
#panel-watch .wlnote.has{opacity:1; color:var(--accent);}
#panel-watch .wlsel:disabled,#panel-watch .wlnote:disabled{opacity:.5; cursor:not-allowed;}
#panel-watch .wl-what{display:block; white-space:normal; line-height:1.4; font-size:12px; color:var(--ink-2); margin-top:2px;}
#panel-watch .wl-prod{display:inline-flex; flex-direction:column; align-items:flex-start; gap:2px; white-space:normal; min-width:300px; max-width:380px;}
#panel-watch .wl-tag{display:inline-flex; gap:8px; align-items:center;}
#panel-watch .wl-sup{display:inline-block; white-space:normal; min-width:120px; max-width:170px;}
#panel-watch .wlsel{max-width:112px;}
#panel-watch .wl-prod b{color:var(--ink); font-weight:600;}
#panel-watch .wl-code,#panel-watch .wl-prev{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-mute);}
#panel-watch .wl-fine{font-size:12px; color:var(--ink-mute); margin-top:8px; line-height:1.5;}
#panel-watch .filterbar button, #wl-note-pop button{appearance:none; font:inherit; font-size:12.5px; padding:7px 12px; border-radius:7px; border:1px solid var(--border); background:var(--surface-2); color:var(--ink-2); cursor:pointer;}
#wl-note-pop{position:fixed; z-index:60; display:none; width:min(300px, calc(100vw - 16px)); background:var(--surface); border:1px solid var(--border); border-radius:10px; box-shadow:var(--shadow); padding:10px;}
#wl-note-pop textarea{width:100%; min-height:70px; font:inherit; font-size:13px; padding:7px 9px; border-radius:7px; border:1px solid var(--border); background:var(--surface); color:var(--ink); resize:vertical;}
#wl-note-pop .row{display:flex; gap:8px; justify-content:flex-end; margin-top:8px;}
#wl-note-pop .wl-pop-save{background:var(--accent); color:var(--accent-ink); border-color:var(--accent);}
"""
rep("</style>\n\n<div class=\"app\">", css + "</style>\n\n<div class=\"app\">", "css")

# ------------------------------------------------------------------ 3. panel
panel = """<section class="panel" id="panel-watch">
        <div class="section-head"><h2>Price &amp; Vendor Watch-list</h2><span class="section-note" id="wl-note-text"></span></div>
        <div class="callout">The one-off price-gap and single-source findings, turned into a list to work down. Every alert is a real purchase-invoice pattern ranked by how many riyals it cost over the last 90 days. Set a status on each one (saved for everyone who opens this dashboard); the next refresh then shows what is new, what got worse, what cleared, and flags anything marked resolved that is still happening.</div>
        <section class="kpirow" id="wl-kpi-row"></section>
        <div class="chartcard"><h3>Open SAR impact, re-computed at each weekly cut</h3><div id="wl-trend"></div><p class="wl-fine">Each point re-runs the same rules on the purchases known at that date, so the line shows whether the problem is growing. The earliest points have less history behind them and read lower for that reason.</p></div>
        <div class="section-head" style="margin-top:20px;"><h2 style="font-size:14px;">Alerts, largest first</h2><span class="section-note" id="wl-status"></span></div>
        <div class="filterbar">
          <input type="search" id="wl-search" placeholder="Search product / code / supplier…" aria-label="Search alerts">
          <select id="wl-type" aria-label="Alert type"><option value="">All types</option><option value="price_up">Price increase</option><option value="supplier_gap">Cheaper supplier</option><option value="entry_outlier">Price entry check</option></select>
          <select id="wl-chg" aria-label="Change since last cut"><option value="">Any change</option><option value="new">New</option><option value="worse">Worse</option><option value="same">Unchanged</option><option value="better">Improving</option></select>
          <select id="wl-state" aria-label="Status filter"><option value="open">Open (not resolved or accepted)</option><option value="unreviewed">Not reviewed yet</option><option value="closed">Resolved or accepted</option><option value="all">All</option></select>
          <span class="count" id="wl-count"></span>
          <button type="button" id="wl-export">Download (CSV)</button>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-wl-alerts"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Suppliers — where spend is moving</h2><span class="section-note">Last 90 days against the 90 days before. A supplier whose share jumps, or that appears for the first time, is worth a look even when none of its prices has tripped an alert.</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-wl-suppliers"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Sole-source items bought in the last 90 days</h2><span class="section-note">Products with a single supplier on record for 2026, ranked by recent spend, with the price trend. With no second supplier there is no price to compare against, so a rise here is the one you cannot spot from the cheaper-supplier alerts.</span></div>
        <div class="filterbar" id="filter-wl-sole"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-wl-sole"></table></div></div>
        <div class="callout amber"><b>How the numbers are built, and what they cannot tell you.</b> Source: posted purchase-invoice lines from the ERP (all booked at Riyadh, the only branch that buys). Unit costs are net of line discounts — checked against VAT on 200 discounted lines. <b>Price increase:</b> same product and supplier, volume-weighted price in the last 90 days at least 10% above its average earlier in 2026; SAR = price rise × units bought in the last 90 days. <b>Cheaper supplier:</b> price paid at one supplier at least 10% above the lowest volume-weighted price among suppliers used in the last 180 days; SAR = the difference × units; it assumes the cheaper supplier has the same item and can supply the volume, and the row says when it was last used. <b>Price entry check:</b> a line priced above 3× or below ⅓ of the product's median — above, the figure is the amount paid over the median; below, it is the recorded line value (usually a unit-of-measure slip). Alerts under SAR 300 are not shown, and lines with zero cost or quantity are left out. SAR is not additive across types (a rise and a cheaper-supplier gap can describe the same purchases), so the headline counts each product-supplier pair once at its larger figure. There is no contract or tender price list in the data, so a rise that was agreed shows up as an alert — mark it Accepted. Freight, payment terms, rebates and invoice-level discounts are not modelled.</div>
        <div id="wl-note-pop" role="dialog" aria-label="Status note"><textarea maxlength="280" placeholder="Why? (optional, 280 characters)"></textarea><div class="row"><button type="button" class="wl-pop-cancel">Cancel</button><button type="button" class="wl-pop-save">Save note</button></div></div>
      </section>

      <section class="panel" id="panel-askai">"""
rep('<section class="panel" id="panel-askai">', panel, "panel")

# ------------------------------------------------------------------ 4. tab + JS block + digest
rep("  {id:'vendor', label:'Vendor Concentration', n: AUDIT.vendor_concentration.kpi.supplier_count},\n",
    "  {id:'vendor', label:'Vendor Concentration', n: AUDIT.vendor_concentration.kpi.supplier_count},\n"
    "  {id:'watch', label:'🎯 Price & Vendor Watch', n: AUDIT.watchlist.kpi.alerts},\n", "tab")
anchor = "/* ---------------- Vendor Concentration & Dependency ---------------- */"
rep(anchor, open(f"{WD}/wl_block.js", encoding="utf-8").read() + "\n" + anchor, "js block")
rep("      fraud_review: FB.summary(),\n", "      fraud_review: FB.summary(),\n      price_vendor_watchlist: WL.summary(),\n", "digest")

# the legacy 'price gap' figure was a sum of per-unit differences, not SAR: show the volume-weighted number everywhere it is labelled as savings
rep("const kpi = AUDIT.kpi;\nconst kpiDefs = [",
    "const kpi = AUDIT.kpi;\n"
    "/* the pipeline's price_gap_savings_identified is a sum of per-unit price differences (not SAR); the watch-list's volume-weighted\n"
    "   overpayment vs the cheapest recent supplier is what the summary cards and board report now show */\n"
    "kpi.price_gap_unit_price_sum = kpi.price_gap_savings_identified;\n"
    "kpi.price_gap_savings_identified = (AUDIT.watchlist && AUDIT.watchlist.kpi.by_type.supplier_gap) ? Math.round(AUDIT.watchlist.kpi.by_type.supplier_gap.sar) : kpi.price_gap_savings_identified;\n"
    "const kpiDefs = [", "kpi override")
rep("foot:'identified across best-price analysis'}", "foot:'paid above the cheapest recent supplier, last 90 days, weighted by quantity'}", "kpi foot")
rep("foot:'من تحليل فجوات أسعار الموردين'}", "foot:'ما دُفع فوق أرخص مورد حديث — آخر 90 يومًا، موزون بالكميات'}", "board foot")
rep("مقابل فرص توفير محتملة تقدَّر بـ <span class=\"ltr-num\">${fmtSAR(kpi.price_gap_savings_identified)}</span> ناتجة عن فروقات أسعار نفس الصنف بين الموردين.",
    "مقابل فرص توفير محتملة تقدَّر بـ <span class=\"ltr-num\">${fmtSAR(kpi.price_gap_savings_identified)}</span> (موزونة بالكميات المشتراة خلال آخر 90 يومًا) ناتجة عن فروقات أسعار نفس الصنف بين الموردين.", "exec text")
rep("بإجمالي فرصة توفير مقدّرة <span class=\"ltr-num\">${fmtSAR(kpi.price_gap_savings_identified)}</span>، قابلة للارتفاع",
    "بإجمالي فرصة توفير مقدّرة <span class=\"ltr-num\">${fmtSAR(kpi.price_gap_savings_identified)}</span> خلال آخر 90 يومًا، قابلة للارتفاع", "rec text")

# ------------------------------------------------------------------ 5. Buraydah single-storekeeper arrangement = expected (confirmed by Hany 2026-10-02)
rep("      {label:'Sender = receiver', value: fmt0(K.same_person_docs)+' docs', foot: fmt0(K.same_person_bur_docs)+' Buraydah 1 ↔ 2 + '+fmt0(K.same_person_docs-K.same_person_bur_docs)+' Riyadh ↔ org 01011302 — no independent receipt', cls:'crit'},",
    "      {label:'Sender = receiver', value: fmt0(K.same_person_docs-K.same_person_bur_docs)+' docs', foot: fmt0(K.same_person_bur_docs)+' Buraydah 1 ↔ 2 transfers are an accepted arrangement (one storekeeper covers both stores, confirmed 2 Oct 2026) · these '+fmt0(K.same_person_docs-K.same_person_bur_docs)+' Riyadh ↔ org 01011302 transfers still have no independent receipt', cls:'warn'},",
    "wf kpi")
rep("see the route table. Staff numbers are EXSYS user numbers.';",
    "see the route table. Staff numbers are EXSYS user numbers; roles confirmed on 2 Oct 2026: 6381 is the Riyadh storekeeper, 6362 Rafha, 6265 both Buraydah stores (a single storekeeper — an accepted arrangement, so the '+fmt0(K.same_person_bur_docs)+' Buraydah 1 ↔ 2 transfers sent and received by the same person are treated as expected), and 2022 / 2024 / 2001 are the store accountants who post step 3.';",
    "wf callout")
rep("    const routeCols = [\n",
    "    const ACC = r => (r.from_org==='02011301' && r.to_org==='03011301') || (r.from_org==='03011301' && r.to_org==='02011301');\n    const routeCols = [\n", "ACC")
rep("render:r=>r.same_person>0 ? '<span class=\"badge red\">'+fmt0(r.same_person)+' of '+fmt0(r.docs)+'</span>' : '0'},",
    "render:r=>r.same_person>0 ? '<span class=\"badge '+(ACC(r)?'blue':'red')+'\">'+fmt0(r.same_person)+' of '+fmt0(r.docs)+(ACC(r)?' · accepted':'')+'</span>' : '0'},", "wf route badge")
rep("same_person_sent_and_received:r.same_person, avg_days_to_receipt:r.avg_days}))",
    "same_person_sent_and_received:r.same_person, same_person_is_accepted_arrangement:((r.from_org==='02011301'&&r.to_org==='03011301')||(r.from_org==='03011301'&&r.to_org==='02011301')), avg_days_to_receipt:r.avg_days}))", "digest routes")

open(WORK, "w", encoding="utf-8").write(html)
print(f"orig_len={orig_len} new_len={len(html)} delta={len(html)-orig_len}")
print("before:", before)
print("after:", {"lines": n_lines, "spend": V["kpi"]["total_spend_2026"], "suppliers": V["kpi"]["supplier_count"], "single_source": V["kpi"]["single_source_product_count"]})
