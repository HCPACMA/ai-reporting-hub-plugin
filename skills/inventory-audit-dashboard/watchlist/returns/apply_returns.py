import json, shutil
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
RD = f"{SCR}/returns"
html = open(WORK, "r", encoding="utf-8").read()
orig_len = len(html)
shutil.copyfile(WORK, f"{SCR}/dashboard_askai.pre_returns.html")

def rep(old, new, label, count=1):
    global html
    assert html.count(old) == count, f"{label}: anchor count={html.count(old)}"
    html = html.replace(old, new)

tag = '<script id="audit-data" type="application/json">'
si = html.index(tag) + len(tag); ei = html.index("</script>", si)
A = json.loads(html[si:ei])
LR = json.load(open(f"{SCR}/watch/live_result.json", encoding="utf-8"))
B, WL, BR = LR["blocks"], LR["watchlist"], LR["returns"]
PCD = json.load(open(f"{SCR}/pc/price_changes.json", encoding="utf-8"))
RET = json.load(open(f"{RD}/returns.json", encoding="utf-8"))
before = {"lines": A["meta"]["purchase_invoice_lines"], "spend": A["vendor_concentration"]["kpi"]["total_spend_2026"]}

# --- purchasing blocks now built on lines net of purchase returns
A["purchases_by_supplier"] = B["purchases_by_supplier"]
A["product_supplier_price_matrix"] = B["product_supplier_price_matrix"]
A["supplier_savings_opportunities"] = B["supplier_savings_opportunities"]
A["price_outliers_flagged"] = B["price_outliers_flagged"]
A["kpi"]["price_gap_savings_identified"] = B["price_gap_savings_identified"]
V = A["vendor_concentration"]
V["kpi"] = B["vendor"]["kpi"]; V["top_suppliers"] = B["vendor"]["top_suppliers"]
V["by_branch"] = B["vendor"]["by_branch"]; V["single_source_products"] = B["vendor"]["single_source_products"]
V["purchasing_model_note"] += (" Figures on this tab are net of purchase returns: SAR %s of purchases (%d returned lines on %d return documents) are taken out, "
    "so spend is SAR %s against SAR %s gross." % (f"{BR['returns_value']:,.0f}", BR["returns_lines"], BR["returns_docs"], f"{BR['spend_net']:,.0f}", f"{BR['spend_gross']:,.0f}"))
A["meta"]["findings"][6] += (" UPDATE 2026-10-03: purchase returns are now netted out. A return is matched to its purchase invoice by the invoice number on the return document "
    "(all 22 returns of 2026 are linked); the returned quantity is removed from that invoice line before any price test, so a wrong-price line that was sent back no longer shows as a price rise, "
    "a price drop, a cheaper-supplier gap or an entry outlier. Gross purchases SAR %s, returns SAR %s, net SAR %s." % (f"{BR['spend_gross']:,.0f}", f"{BR['returns_value']:,.0f}", f"{BR['spend_net']:,.0f}"))
A["meta"]["purchasing_refresh"].update({"refreshed_on": "2026-10-03", "returns_netted": True, "gross_lines": BR["lines_gross"], "returns_lines": BR["returns_lines"],
    "returns_value": BR["returns_value"], "net_spend": BR["spend_net"], "gross_spend": BR["spend_gross"]})

# --- watch-list, price changes, returns review
A["watchlist"] = WL
ev_ret = PCD.pop("events_returned")
A["price_changes"] = PCD
RE = WL["returns_effect"]
A["returns_review"] = {
    "as_of": "2026-10-03", "bridge": BR,
    "kpi": {k: PCD["kpi"][k] for k in ("events_returned_total", "events_returned_window", "events_returned_sar_window", "invoice_lines_returned_full", "invoice_lines_returned_partial")},
    "lines": RET, "events_returned": ev_ret,
    "watch": {"cleared": len(RE["cleared_by_return"]), "cleared_sar": RE["cleared_sar"], "unique_sar_gross": RE["unique_sar_gross"], "unique_sar_net": RE["unique_sar_net"],
              "cleared_list": [f"{a['product_name']} at {a['supplier_name']} (SAR {a['impact']:,.0f})" for a in RE["cleared_by_return"]]},
}
js = json.dumps(A, ensure_ascii=False, separators=(",", ":"))
assert "</" not in js
html = html[:si] + js + html[ei:]

css = """
/* ---------- purchase returns and item-identity review ---------- */
#panel-watch .rvsel{font:inherit; font-size:12px; padding:3px 5px; border-radius:6px; border:1px solid var(--border); background:var(--surface); color:var(--ink); max-width:170px;}
#panel-watch .rvsel[data-v="investigate"]{background:var(--amber-soft); color:var(--amber); border-color:var(--amber-soft);}
#panel-watch .rvsel[data-v="genuine"], #panel-watch .rvsel[data-v="cleared"]{background:var(--accent-soft); color:var(--accent); border-color:var(--accent-soft);}
#panel-watch .rvsel[data-v="mismatch"]{background:var(--red-soft); color:var(--red); border-color:var(--red-soft);}
"""
rep("</style>\n\n<div class=\"app\">", css + "</style>\n\n<div class=\"app\">", "css")

anchor = "Scans exist only from 31 March 2026, so older invoices show “no scan attached”.</p>\n"
sect = anchor + """        <div class="section-head" style="margin-top:26px;"><h2 style="font-size:14px;">Purchase returns and item-identity review</h2><span class="section-note" id="rv-note-text"></span></div>
        <div class="callout"><b>Returns.</b> When a supplier invoices the wrong item or price and the purchase is sent back, the returned quantity is taken out of every price test above — it is not a price rise, a price drop or a cheaper-supplier gap. The changes this removes are listed at the bottom so nothing disappears silently.<br><b>Item identity.</b> A line can also be received into the ERP under another item's code because the right item was not set up yet, then returned and re-bought. The ERP keeps no supplier item description, so the name on the supplier's invoice can only be compared on the scan; the list below ranks every returned line by how much it looks like that case (price far from the product's usual, returned in full, stock already moved before the return) so the scans worth opening first are at the top.</div>
        <section class="kpirow" id="rv-kpi"></section>
        <div class="filterbar">
          <input type="search" id="rv-search" placeholder="Search product / code / supplier / invoice or return no…" aria-label="Search returned lines">
          <select id="rv-level" aria-label="Review level"><option value="">All levels</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
          <select id="rv-state" aria-label="Review status"><option value="">Any status</option><option value="open">Open (not reviewed)</option><option value="reviewed">Reviewed</option><option value="investigate">Under investigation</option><option value="genuine">Genuine supplier error</option><option value="mismatch">Name mismatch confirmed</option><option value="cleared">Cleared</option></select>
          <span class="count" id="rv-count"></span>
          <button type="button" id="rv-export">Download (CSV)</button>
          <span class="section-note" id="rv-status"></span>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-rv"></table></div></div>
        <p class="wl-fine">A return is matched to its purchase invoice through the invoice number on the return document (all 22 returns of 2026 are linked). Each flag scores a point (price far from the usual scores two, and a line of SAR 5,000 or more scores one more); High = four points or more, Medium = two or three. “Price vs usual” compares the price paid with the median of the product's other 2026 invoices, or with the cost the ERP used on later stock movements when there are fewer than two. “Moved before return” counts dispense and transfer-out quantity between the receipt and the return, product-wide, so it can include other stores. None of the 34 returned lines carries a reason on the return document — making the reason a required field would let this list separate supplier errors from item-code mix-ups without opening a scan.</p>
        <div class="section-head" style="margin-top:18px;"><h2 style="font-size:14px;">Price changes left out because the quantity was returned</h2><span class="section-note">Not counted in any figure above</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-rv-ex"></table></div></div>
"""
rep(anchor, sect, "section")

rep("PC.build(); PC.init();\n", "PC.build(); PC.init();\n" + open(f"{RD}/rv_block.js", encoding="utf-8").read() + "\n", "js block")
rep("      price_changes_between_invoices: PC.summary(),\n", "      price_changes_between_invoices: PC.summary(),\n      purchase_returns_review: RV.summary(),\n", "digest")
rep("product-supplier pairs have two or more invoices in 2026';", "product-supplier pairs have two or more invoices in 2026 · net of purchase returns (see below)';", "pc note")
open(WORK, "w", encoding="utf-8").write(html)
print(orig_len, len(html), len(html) - orig_len)
print("before", before, "after", BR)
