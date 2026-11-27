#!/usr/bin/env python3
"""
2026-09-22: adds the 3 best-practice tabs proposed (but not built) alongside Fraud Detection --
ABC/Pareto value concentration, Cycle-Count Variance, and Vendor Concentration/Dependency --
under the existing left-sidebar "Operational" group, right after Purchases & Pricing.
1) Re-embeds the current alfaihaa_inventory_audit.json (now including the 3 new keys).
2) Inserts 3 new panel sections (abc, cyclecount, vendor) after panel-purchases.
3) Updates the TABS array to add the 3 new entries.
4) Appends the 3 new rendering IIFEs.
"""
import json
from pathlib import Path

DASH = Path("/home/claude/inventory_build/dashboard.html")
JSON_SRC = Path("/home/claude/inventory_build/pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json")

html = DASH.read_text(encoding="utf-8")
data = json.loads(JSON_SRC.read_text(encoding="utf-8"))
for k in ("abc_analysis", "cycle_count_variance", "vendor_concentration"):
    assert k in data, f"{k} missing from source JSON"


def replace_once(haystack, old, new, label):
    n = haystack.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected exactly 1 occurrence, found {n}")
    return haystack.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) Insert the 3 new panels right after panel-purchases, before panel-board
# ---------------------------------------------------------------------------
anchor = '''        <div class="tablewrap"><div class="scrollbody"><table id="tbl-matrix"></table></div></div>
      </section>

      <section class="panel" id="panel-board" dir="rtl" lang="ar">'''

new_panels = '''        <div class="tablewrap"><div class="scrollbody"><table id="tbl-matrix"></table></div></div>
      </section>

      <section class="panel" id="panel-abc">
        <div class="section-head"><h2>ABC / Pareto Value Concentration</h2><span class="section-note" id="abc-note"></span></div>
        <section class="kpirow" id="abc-kpi-row"></section>
        <div class="section-head" style="margin-top:18px;"><h2 style="font-size:14px;">Tier summary</h2><span class="section-note">A = first 80% of value · B = next 15% (80-95%) · C = last 5% (95-100%).</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-abc-tiers"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Ranked items — company-wide</h2><span class="section-note">Every SKU ranked by on-hand SAR value, aggregated across every branch/store that holds it.</span></div>
        <div class="filterbar" id="filter-abc"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-abc-items"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Tier breakdown by branch</h2><span class="section-note">A branch's own Pareto — a product can be Tier A at one branch and Tier C company-wide.</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-abc-branch"></table></div></div>
      </section>

      <section class="panel" id="panel-cyclecount">
        <div class="section-head"><h2>Cycle-Count Variance Tracking</h2><span class="section-note" id="cc-note"></span></div>
        <div class="callout amber" id="cc-dq-callout"></div>
        <section class="kpirow" id="cc-kpi-row"></section>
        <div class="section-head" style="margin-top:18px;"><h2 style="font-size:14px;">By branch</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-branch"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">By SKU</h2><span class="section-note">Recurring = 2 or more separate count-adjustment events on the same product across 2019-2025 — a signal worth a closer look at counting procedure, bin discipline, or shrinkage for that item.</span></div>
        <div class="filterbar" id="filter-cc-product"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-product"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">By posting user</h2><span class="section-note">Which staff account posted the most count-adjustment value — a concentration here is worth pairing with the Fraud Detection tab's segregation-of-duties check.</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-user"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">All events</h2></div>
        <div class="filterbar" id="filter-cc-events"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-events"></table></div></div>
      </section>

      <section class="panel" id="panel-vendor">
        <div class="section-head"><h2>Vendor Concentration &amp; Dependency</h2><span class="section-note" id="vendor-note"></span></div>
        <section class="kpirow" id="vendor-kpi-row"></section>
        <div class="section-head" style="margin-top:18px;"><h2 style="font-size:14px;">Top suppliers by 2026 spend</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-vendor-top"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Concentration by branch</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-vendor-branch"></table></div></div>
        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Single-source dependency risk</h2><span class="section-note">Products bought from exactly one supplier in 2026 — the specific items most exposed to a single vendor's pricing, supply, or relationship disruption. Ranked by estimated spend.</span></div>
        <div class="filterbar" id="filter-vendor-ss"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-vendor-ss"></table></div></div>
      </section>

      <section class="panel" id="panel-board" dir="rtl" lang="ar">'''

html = replace_once(html, anchor, new_panels, "new-panels-insert")

# ---------------------------------------------------------------------------
# 2) TABS array: insert abc/cyclecount/vendor after 'purchases', before the Governance divider
# ---------------------------------------------------------------------------
old_tabs_line = "  {id:'purchases', label:'Purchases & Pricing'},\n  {id:'fraud', label:'Fraud Detection', n: AUDIT.fraud_detection.kpi.total_flags, risk:true, divider:'Governance & Reporting'},"
new_tabs_line = ("  {id:'purchases', label:'Purchases & Pricing'},\n"
                  "  {id:'abc', label:'ABC / Pareto', n: AUDIT.abc_analysis.company_wide.total_skus_ranked},\n"
                  "  {id:'cyclecount', label:'Cycle-Count Variance', n: AUDIT.cycle_count_variance.kpi.total_events},\n"
                  "  {id:'vendor', label:'Vendor Concentration', n: AUDIT.vendor_concentration.kpi.supplier_count},\n"
                  "  {id:'fraud', label:'Fraud Detection', n: AUDIT.fraud_detection.kpi.total_flags, risk:true, divider:'Governance & Reporting'},")
html = replace_once(html, old_tabs_line, new_tabs_line, "tabs-array")

# ---------------------------------------------------------------------------
# 3) Append the 3 rendering IIFEs, right after the fraud-detection IIFE (end of file, before final </script>)
# ---------------------------------------------------------------------------
new_js = r'''

/* ---------------- ABC / Pareto Value Concentration ---------------- */
(function(){
  const A = AUDIT.abc_analysis;
  const cw = A.company_wide;

  document.getElementById('abc-note').textContent = A.methodology;

  const tierCls = {A:'crit', B:'warn', C:''};
  const kpiDefs = [
    {label:'Total ranked value', value: fmtSAR(cw.total_value), foot: fmt0(cw.total_skus_ranked)+' SKUs ranked ('+fmt0(cw.zero_or_unpriced_value_skus_excluded)+' zero/unpriced excluded)'},
    ...cw.tiers.map(t=>({label:'Tier '+t.tier, value: fmtPct(t.value_pct), foot: fmt0(t.sku_count)+' SKUs ('+fmtPct(t.sku_pct)+' of items) · '+fmtSAR(t.value), cls: tierCls[t.tier]})),
  ];
  document.getElementById('abc-kpi-row').innerHTML = kpiDefs.map(d=>`
    <div class="kpi ${d.cls||''}"><span class="label">${d.label}</span><span class="value">${d.value}</span><span class="foot">${d.foot}</span></div>
  `).join('');

  const tierCols = [
    {key:'tier', label:'Tier', render:r=>`<span class="badge ${tierCls[r.tier]==='crit'?'red':tierCls[r.tier]==='warn'?'amber':''}">${r.tier}</span>`},
    {key:'sku_count', label:'SKUs', num:true, render:r=>fmt0(r.sku_count)},
    {key:'sku_pct', label:'% of SKUs', num:true, render:r=>fmtPct(r.sku_pct)},
    {key:'value', label:'Value (SAR)', num:true, render:r=>fmt0(r.value)},
    {key:'value_pct', label:'% of value', num:true, render:r=>fmtPct(r.value_pct)},
  ];
  buildTable(document.getElementById('tbl-abc-tiers'), tierCols, cw.tiers, {defaultSort:'tier', defaultDir:1});

  const itemCols = [
    {key:'tier', label:'Tier', render:r=>`<span class="badge ${tierCls[r.tier]==='crit'?'red':tierCls[r.tier]==='warn'?'amber':''}">${r.tier}</span>`},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'branches', label:'Branches', render:r=>r.branches.join(', ')},
    {key:'qty', label:'Qty on hand', num:true, render:r=>fmt0(r.qty)},
    {key:'value', label:'Value (SAR)', num:true, render:r=>fmt0(r.value)},
    {key:'cum_pct', label:'Cumulative %', num:true, render:r=>fmtPct(r.cum_pct)},
  ];
  const abcBranches = [...new Set(cw.items.flatMap(r=>r.branches))].sort();
  const abcTbl = buildTable(document.getElementById('tbl-abc-items'), itemCols, cw.items, {defaultSort:'value', defaultDir:-1});
  const abcFb = makeFilterBar(document.getElementById('filter-abc'), {placeholder:'Search product / code…', branches: abcBranches, onChange:(q,b)=>{
    abcTbl.setFilter(r => (!b||r.branches.includes(b)) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q)));
    abcFb.setCount(document.querySelectorAll('#tbl-abc-items tbody tr').length, cw.items.length);
  }});
  abcFb.setCount(cw.items.length, cw.items.length);

  const branchRows = A.by_branch.map(b=>({
    branch: b.branch, total_value: b.total_value, sku_count: b.sku_count,
    tier_a: b.tiers.find(t=>t.tier==='A'), tier_b: b.tiers.find(t=>t.tier==='B'), tier_c: b.tiers.find(t=>t.tier==='C'),
  }));
  const branchCols = [
    {key:'branch', label:'Branch'},
    {key:'sku_count', label:'SKUs', num:true, render:r=>fmt0(r.sku_count)},
    {key:'total_value', label:'Total value (SAR)', num:true, render:r=>fmt0(r.total_value)},
    {key:'tier_a', label:'Tier A SKUs', num:true, render:r=>fmt0(r.tier_a.sku_count)+' ('+fmtPct(r.tier_a.value_pct)+')'},
    {key:'tier_b', label:'Tier B SKUs', num:true, render:r=>fmt0(r.tier_b.sku_count)+' ('+fmtPct(r.tier_b.value_pct)+')'},
    {key:'tier_c', label:'Tier C SKUs', num:true, render:r=>fmt0(r.tier_c.sku_count)+' ('+fmtPct(r.tier_c.value_pct)+')'},
  ];
  buildTable(document.getElementById('tbl-abc-branch'), branchCols, branchRows, {defaultSort:'total_value', defaultDir:-1});
})();

/* ---------------- Cycle-Count Variance Tracking ---------------- */
(function(){
  const C = AUDIT.cycle_count_variance;
  const k = C.kpi;

  document.getElementById('cc-note').textContent = C.methodology;
  document.getElementById('cc-dq-callout').innerHTML = '<b>Audit-trail gap:</b> ' + C.data_quality_note;

  const kpiDefs = [
    {label:'Count-adjustment events', value: fmt0(k.total_events), foot: k.date_range+' · '+fmt0(k.gain_events)+' gain / '+fmt0(k.loss_events)+' loss'},
    {label:'Net value', value: fmtSAR(k.net_value), foot: 'Gain '+fmtSAR(k.gain_value)+' − Loss '+fmtSAR(k.loss_value), cls: k.net_value<0?'crit':''},
    {label:'Recurring-variance SKUs', value: fmt0(k.recurring_variance_skus), foot: 'of '+fmt0(k.distinct_skus_with_variance)+' distinct SKUs with any variance (2+ events)', cls:'warn'},
    {label:'Events logged in 2026', value: fmt0(k.events_logged_in_2026), foot: 'last posted event: '+(k.last_event_date||'—'), cls: k.events_logged_in_2026===0?'crit':''},
    {label:'Unvalued events', value: fmt0(k.unvalued_events), foot: 'no current cost basis available for this product — same gap as elsewhere in this audit'},
  ];
  document.getElementById('cc-kpi-row').innerHTML = kpiDefs.map(d=>`
    <div class="kpi ${d.cls||''}"><span class="label">${d.label}</span><span class="value">${d.value}</span><span class="foot">${d.foot}</span></div>
  `).join('');

  const branchCols = [
    {key:'branch', label:'Branch'},
    {key:'events', label:'Events', num:true, render:r=>fmt0(r.events)},
    {key:'gain_events', label:'Gain events', num:true, render:r=>fmt0(r.gain_events)},
    {key:'loss_events', label:'Loss events', num:true, render:r=>fmt0(r.loss_events)},
    {key:'gain_value', label:'Gain value (SAR)', num:true, render:r=>fmt0(r.gain_value)},
    {key:'loss_value', label:'Loss value (SAR)', num:true, render:r=>fmt0(r.loss_value)},
    {key:'net_value', label:'Net value (SAR)', num:true, render:r=>fmt0(r.net_value)},
    {key:'last_event_date', label:'Last event'},
  ];
  buildTable(document.getElementById('tbl-cc-branch'), branchCols, C.by_branch, {defaultSort:'net_value', defaultDir:1});

  const prodCols = [
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'branches', label:'Branch(es)', render:r=>r.branches.join(', ')},
    {key:'event_count', label:'Events', num:true, render:r=>r.recurring?`<span class="badge amber">${fmt0(r.event_count)}</span>`:fmt0(r.event_count)},
    {key:'gain_value', label:'Gain value (SAR)', num:true, render:r=>fmt0(r.gain_value)},
    {key:'loss_value', label:'Loss value (SAR)', num:true, render:r=>fmt0(r.loss_value)},
    {key:'net_value', label:'Net value (SAR)', num:true, render:r=>fmt0(r.net_value)},
    {key:'last_event_date', label:'Last event'},
  ];
  const ccProdBranches = [...new Set(C.by_product.flatMap(r=>r.branches))].sort();
  const ccProdTbl = buildTable(document.getElementById('tbl-cc-product'), prodCols, C.by_product, {defaultSort:'net_value', defaultDir:1});
  const ccProdFb = makeFilterBar(document.getElementById('filter-cc-product'), {placeholder:'Search product / code…', branches: ccProdBranches, onChange:(q,b)=>{
    ccProdTbl.setFilter(r => (!b||r.branches.includes(b)) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q)));
    ccProdFb.setCount(document.querySelectorAll('#tbl-cc-product tbody tr').length, C.by_product.length);
  }});
  ccProdFb.setCount(C.by_product.length, C.by_product.length);

  const userCols = [
    {key:'user', label:'User'},
    {key:'events', label:'Events', num:true, render:r=>fmt0(r.events)},
    {key:'gain_value', label:'Gain value (SAR)', num:true, render:r=>fmt0(r.gain_value)},
    {key:'loss_value', label:'Loss value (SAR)', num:true, render:r=>fmt0(r.loss_value)},
    {key:'net_value', label:'Net value (SAR)', num:true, render:r=>fmt0(r.net_value)},
  ];
  buildTable(document.getElementById('tbl-cc-user'), userCols, C.by_user, {defaultSort:'loss_value', defaultDir:-1});

  const evCols = [
    {key:'adjs_date', label:'Date'},
    {key:'type', label:'Type', render:r=>`<span class="badge ${r.type==='Loss'?'red':''}">${r.type}</span>`},
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'qty', label:'Qty', num:true, render:r=>fmt0(r.qty)},
    {key:'value', label:'Value (SAR)', num:true, render:r=>r.value==null?'—':fmt0(r.value)},
    {key:'adjs_no', label:'Adjustment #'},
    {key:'posted_by', label:'Posted by'},
  ];
  const evBranches = [...new Set(C.events.map(r=>r.branch))].sort();
  const evTbl = buildTable(document.getElementById('tbl-cc-events'), evCols, C.events, {defaultSort:'adjs_date', defaultDir:-1});
  const evFb = makeFilterBar(document.getElementById('filter-cc-events'), {placeholder:'Search product / code / adjustment #…', branches: evBranches, onChange:(q,b)=>{
    evTbl.setFilter(r => (!b||r.branch===b) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q) || (r.adjs_no||'').toLowerCase().includes(q)));
    evFb.setCount(document.querySelectorAll('#tbl-cc-events tbody tr').length, C.events.length);
  }});
  evFb.setCount(C.events.length, C.events.length);
})();

/* ---------------- Vendor Concentration & Dependency ---------------- */
(function(){
  const V = AUDIT.vendor_concentration;
  const k = V.kpi;

  document.getElementById('vendor-note').textContent = V.methodology;

  const kpiDefs = [
    {label:'Total 2026 spend', value: fmtSAR(k.total_spend_2026), foot: fmt0(k.supplier_count)+' active suppliers'},
    {label:'HHI (concentration)', value: fmt0(k.hhi), foot: k.concentration_level+' concentration company-wide', cls: k.concentration_level==='High'?'crit':(k.concentration_level==='Moderate'?'warn':'')},
    {label:'Top-5 supplier share', value: fmtPct(k.top5_share_pct), foot: 'Top-10 share: '+fmtPct(k.top10_share_pct)},
    {label:'Single-source products', value: fmt0(k.single_source_product_count), foot: fmtSAR(k.single_source_spend_est)+' est. spend ('+fmtPct(k.single_source_share_pct)+' of total)', cls:'warn'},
  ];
  document.getElementById('vendor-kpi-row').innerHTML = kpiDefs.map(d=>`
    <div class="kpi ${d.cls||''}"><span class="label">${d.label}</span><span class="value">${d.value}</span><span class="foot">${d.foot}</span></div>
  `).join('');

  const topCols = [
    {key:'supplier_name', label:'Supplier'},
    {key:'spend', label:'Spend (SAR)', num:true, render:r=>fmt0(r.spend)},
    {key:'share_pct', label:'Share', num:true, render:r=>fmtPct(r.share_pct)},
    {key:'cum_pct', label:'Cumulative %', num:true, render:r=>fmtPct(r.cum_pct)},
    {key:'product_count', label:'Products', num:true, render:r=>fmt0(r.product_count)},
    {key:'line_count', label:'PI lines', num:true, render:r=>fmt0(r.line_count)},
    {key:'branches', label:'Branches', render:r=>r.branches.join(', ')},
  ];
  buildTable(document.getElementById('tbl-vendor-top'), topCols, V.top_suppliers, {defaultSort:'spend', defaultDir:-1});

  const vbCols = [
    {key:'branch', label:'Branch'},
    {key:'total_spend', label:'Total spend (SAR)', num:true, render:r=>fmt0(r.total_spend)},
    {key:'supplier_count', label:'Suppliers', num:true, render:r=>fmt0(r.supplier_count)},
    {key:'hhi', label:'HHI', num:true, render:r=>fmt0(r.hhi)},
    {key:'top_supplier_name', label:'Top supplier'},
    {key:'top_supplier_share_pct', label:'Top supplier share', num:true, render:r=>r.top_supplier_share_pct==null?'—':fmtPct(r.top_supplier_share_pct)},
  ];
  buildTable(document.getElementById('tbl-vendor-branch'), vbCols, V.by_branch, {defaultSort:'total_spend', defaultDir:-1});

  const ssCols = [
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'supplier_name', label:'Supplier'},
    {key:'spend_est', label:'Est. spend (SAR)', num:true, render:r=>fmt0(r.spend_est)},
    {key:'qty', label:'Qty', num:true, render:r=>fmt0(r.qty)},
    {key:'last_date', label:'Last purchase'},
  ];
  const ssTbl = buildTable(document.getElementById('tbl-vendor-ss'), ssCols, V.single_source_products, {defaultSort:'spend_est', defaultDir:-1});
  const ssFb = makeFilterBar(document.getElementById('filter-vendor-ss'), {placeholder:'Search product / code / supplier…', onChange:(q)=>{
    ssTbl.setFilter(r => (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q) || (r.supplier_name||'').toLowerCase().includes(q)));
    ssFb.setCount(document.querySelectorAll('#tbl-vendor-ss tbody tr').length, V.single_source_products.length);
  }});
  ssFb.setCount(V.single_source_products.length, V.single_source_products.length);
})();
'''

marker = "  buildTable(document.getElementById('tbl-fraud-cancelled'), cancCols, FD.movement.cancelled_rows, {defaultSort:'transaction_date', defaultDir:-1});\n})();"
if html.count(marker) != 1:
    raise SystemExit(f"[new-js-anchor] expected exactly 1 occurrence, found {html.count(marker)}")
html = html.replace(marker, marker + new_js, 1)

# ---------------------------------------------------------------------------
# 4) Re-embed the audit-data JSON
# ---------------------------------------------------------------------------
start_tag = '<script id="audit-data" type="application/json">'
end_tag = '</script>\n<script>'
start_i = html.index(start_tag) + len(start_tag)
end_i = html.index(end_tag, start_i)
new_json_text = json.dumps(data, ensure_ascii=False, indent=2)
html = html[:start_i] + new_json_text + html[end_i:]

DASH.write_text(html, encoding="utf-8")
print("Applied. New size:", DASH.stat().st_size)
