#!/usr/bin/env python3
"""
Applies the 2026-09-21 Fraud Detection + left-sidebar-nav redesign to dashboard.html.
1) Re-embeds the current alfaihaa_inventory_audit.json (now including fraud_detection).
2) Rewrites the CSS for .tabs/.tab-btn into a .shell/.sidebar/.tab-btn left-nav layout.
3) Restructures the HTML shell (wrap -> shell{sidebar, content-col}).
4) Inserts the new Fraud Detection panel markup.
5) Updates the TABS array (adds 'fraud', reorders 'board' under a Governance divider).
6) Appends the Fraud Detection rendering IIFE.
"""
import json
from pathlib import Path

DASH = Path("/home/claude/inventory_build/dashboard.html")
JSON_SRC = Path("/home/claude/inventory_build/pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json")

html = DASH.read_text(encoding="utf-8")
data = json.loads(JSON_SRC.read_text(encoding="utf-8"))
assert "fraud_detection" in data, "fraud_detection key missing from source JSON"


def replace_once(haystack, old, new, label):
    n = haystack.count(old)
    if n != 1:
        raise SystemExit(f"[{label}] expected exactly 1 occurrence, found {n}")
    return haystack.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1) CSS: .tabs / .tab-btn -> .shell / .sidebar / .tab-btn (left nav)
# ---------------------------------------------------------------------------
old_css = '''/* ---------- tabs ---------- */
.tabs{
  display:flex; gap:4px; overflow-x:auto; padding-block:2px 10px; border-bottom:1px solid var(--border);
  position:sticky; top:calc(env(safe-area-inset-top,0px) + 66px); background:var(--bg); z-index:19;
}
.tabs::-webkit-scrollbar{height:0;}
.tab-btn{
  appearance:none; border:1px solid transparent; background:transparent; color:var(--ink-2);
  font:inherit; font-size:13px; font-weight:600; padding:8px 13px; border-radius:8px 8px 0 0;
  cursor:pointer; white-space:nowrap;
}
.tab-btn:hover{background:var(--surface-2); color:var(--ink);}
.tab-btn[aria-selected="true"]{background:var(--surface); color:var(--accent); border-color:var(--border) var(--border) var(--surface);}
.tab-btn .n{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-mute); margin-left:5px;}

main{padding-block:18px 40px;}'''

new_css = '''/* ---------- shell layout: left sidebar + content (2026-09-21 redesign) ---------- */
.shell{max-width:1400px; margin:0 auto; padding-inline:20px; display:flex; align-items:flex-start; gap:22px;}
.content-col{flex:1; min-width:0;}
.sidebar{
  flex:0 0 210px; width:210px; display:flex; flex-direction:column; gap:3px;
  position:sticky; top:calc(env(safe-area-inset-top,0px) + 78px);
  max-height:calc(100vh - 96px); overflow-y:auto; padding-block:4px 14px;
}
.sidebar::-webkit-scrollbar{width:0;}
.sidebar-label{font-size:10px; text-transform:uppercase; letter-spacing:.07em; color:var(--ink-mute); font-weight:700; padding:14px 10px 4px;}
.sidebar-label:first-child{padding-top:2px;}
.tab-btn{
  appearance:none; border:1px solid transparent; background:transparent; color:var(--ink-2);
  font:inherit; font-size:13px; font-weight:600; padding:9px 12px; border-radius:8px;
  cursor:pointer; white-space:nowrap; text-align:left; display:flex; align-items:center; justify-content:space-between; gap:8px; width:100%;
}
.tab-btn:hover{background:var(--surface-2); color:var(--ink);}
.tab-btn[aria-selected="true"]{background:var(--accent-soft); color:var(--accent); border-color:var(--accent-soft);}
.tab-btn .n{font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-mute); margin-left:5px;}
.tab-btn.risk{color:var(--red);}
.tab-btn.risk .n{color:var(--red); opacity:.8;}
.tab-btn.risk[aria-selected="true"]{background:var(--red-soft); color:var(--red); border-color:var(--red-soft);}
.tab-btn.risk:hover{background:var(--red-soft);}

@media (max-width:900px){
  .shell{display:block; padding-inline:20px;}
  .sidebar{
    position:sticky; top:calc(env(safe-area-inset-top,0px) + 66px); width:auto; flex-direction:row;
    overflow-x:auto; overflow-y:visible; max-height:none; gap:4px; padding-block:2px 10px;
    border-bottom:1px solid var(--border); background:var(--bg); z-index:19; margin-bottom:4px;
  }
  .sidebar::-webkit-scrollbar{height:0;}
  .sidebar-label{display:none;}
  .tab-btn{border-radius:8px 8px 0 0; text-align:center; justify-content:center; width:auto;}
}

main{padding-block:18px 40px;}'''

html = replace_once(html, old_css, new_css, "css")

# ---------------------------------------------------------------------------
# 2) HTML shell: split the old .wrap(kpi+tabs+main) into .wrap(kpi) + .shell(sidebar, content-col{main})
# ---------------------------------------------------------------------------
old_open = '''  <div class="wrap">
    <section class="kpirow" id="kpi-row"></section>

    <nav class="tabs" id="tabs"></nav>

    <main>'''
new_open = '''  <div class="wrap">
    <section class="kpirow" id="kpi-row"></section>
  </div>

  <div class="shell">
    <nav class="sidebar" id="tabs"></nav>
    <div class="content-col">
    <main>'''
html = replace_once(html, old_open, new_open, "shell-open")

old_close = '''    </main>

    <details class="findings" id="findings-box" open>
      <summary>Methodology notes &amp; data-quality findings (<span id="findings-count">0</span>)</summary>
      <ul id="findings-list"></ul>
    </details>

    <footer class="page">Al Faihaa Group · AI Reporting HUB · Inventory Analysis &amp; Audit · source: Cure+ (read-only EXSYS connection) · not for external distribution without review</footer>
  </div>
</div>'''
new_close = '''    </main>

    <details class="findings" id="findings-box" open>
      <summary>Methodology notes &amp; data-quality findings (<span id="findings-count">0</span>)</summary>
      <ul id="findings-list"></ul>
    </details>

    <footer class="page">Al Faihaa Group · AI Reporting HUB · Inventory Analysis &amp; Audit · source: Cure+ (read-only EXSYS connection) · not for external distribution without review</footer>
    </div>
  </div>
</div>'''
html = replace_once(html, old_close, new_close, "shell-close")

# ---------------------------------------------------------------------------
# 3) Insert the Fraud Detection panel right after panel-board's closing </section>
# ---------------------------------------------------------------------------
anchor = '''        <div class="callout amber">
          <b>المقترحات والتوصيات</b>
          <ol class="board-reco" id="board-recommendations"></ol>
        </div>
      </section>
    </main>'''

fraud_panel = '''        <div class="callout amber">
          <b>المقترحات والتوصيات</b>
          <ol class="board-reco" id="board-recommendations"></ol>
        </div>
      </section>

      <section class="panel" id="panel-fraud">
        <div class="section-head"><h2>Fraud &amp; Control Detection</h2><span class="section-note">Exception-based review across 4 categories, each grounded in fields actually present in the raw extract (created_by / posted_by / post_date vs. transaction_date / status / supplier). A flag marks a pattern worth a second look — it is not on its own a finding of wrongdoing.</span></div>

        <section class="kpirow" id="fraud-kpi-row"></section>

        <div class="callout" id="fraud-scope-callout"></div>

        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Timing &amp; posting-control anomalies</h2><span class="section-note" id="fraud-timing-note"></span></div>
        <div class="filterbar" id="filter-fraud-timing"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-timing"></table></div></div>

        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">User &amp; segregation-of-duties</h2><span class="section-note">Per-user creation vs. posting activity for 2026. A user who both creates and posts 100% of their own transactions has no independent second check on their own entries.</span></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-sod-users"></table></div></div>
        <div class="section-head" style="margin-top:14px;"><h2 style="font-size:13px;">Sample same-user create+post transactions</h2></div>
        <div class="filterbar" id="filter-fraud-sod"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-sod"></table></div></div>

        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Pricing &amp; cost anomalies</h2><span class="section-note" id="fraud-pricing-note"></span></div>
        <div class="filterbar" id="filter-fraud-pricing"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-pricing"></table></div></div>

        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Movement-pattern anomalies</h2><span class="section-note">Frequent corrections on the same SKU/store, quantity-matched round-trip transfers between the same two stores, and cancelled-transaction clustering.</span></div>
        <div class="section-head" style="margin-top:8px;"><h2 style="font-size:13px;">Frequent corrections (2+ on the same SKU/store in 2026)</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-corrections"></table></div></div>
        <div class="section-head" style="margin-top:14px;"><h2 style="font-size:13px;">Round-trip transfers (quantity-matched, within 60 days)</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-roundtrip"></table></div></div>
        <div class="section-head" style="margin-top:14px;"><h2 style="font-size:13px;">Cancelled transactions</h2></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-fraud-cancelled"></table></div></div>
      </section>
    </main>'''

html = replace_once(html, anchor, fraud_panel, "fraud-panel-insert")

# ---------------------------------------------------------------------------
# 4) TABS array: add 'fraud' under a new "Governance & Reporting" divider, move 'board' under it too
# ---------------------------------------------------------------------------
old_tabs = '''const TABS = [
  {id:'overview', label:'Overview'},
  {id:'overstock', label:'Overstock', n: AUDIT.overstock.length},
  {id:'slowmoving', label:'Slow-Moving', n: AUDIT.slow_moving.length},
  {id:'expiry', label:'Expiry', n: AUDIT.expiry_risk.length},
  {id:'receiving', label:'Receiving Flags', n: AUDIT.receiving_flags.length},
  {id:'aging', label:'Aging Bucket', n: AUDIT.never_dispensed.rows.length},
  {id:'crossorg', label:'Cross-Branch Audit'},
  {id:'dispense', label:'Dispense by CC', n: AUDIT.dispense_by_cost_center.length},
  {id:'purchases', label:'Purchases & Pricing'},
  {id:'board', label:'تقرير المجلس'},
];
document.getElementById('tabs').innerHTML = TABS.map((t,i)=>`
  <button class="tab-btn" role="tab" aria-selected="${i===0}" data-tab="${t.id}">${t.label}${t.n!=null?`<span class="n">${t.n}</span>`:''}</button>
`).join('');'''

new_tabs = '''const TABS = [
  {id:'overview', label:'Overview', divider:'Operational'},
  {id:'overstock', label:'Overstock', n: AUDIT.overstock.length},
  {id:'slowmoving', label:'Slow-Moving', n: AUDIT.slow_moving.length},
  {id:'expiry', label:'Expiry', n: AUDIT.expiry_risk.length},
  {id:'receiving', label:'Receiving Flags', n: AUDIT.receiving_flags.length},
  {id:'aging', label:'Aging Bucket', n: AUDIT.never_dispensed.rows.length},
  {id:'crossorg', label:'Cross-Branch Audit'},
  {id:'dispense', label:'Dispense by CC', n: AUDIT.dispense_by_cost_center.length},
  {id:'purchases', label:'Purchases & Pricing'},
  {id:'fraud', label:'Fraud Detection', n: AUDIT.fraud_detection.kpi.total_flags, risk:true, divider:'Governance & Reporting'},
  {id:'board', label:'تقرير المجلس'},
];
document.getElementById('tabs').innerHTML = TABS.map((t,i)=>`
  ${t.divider?`<div class="sidebar-label">${t.divider}</div>`:''}<button class="tab-btn${t.risk?' risk':''}" role="tab" aria-selected="${i===0}" data-tab="${t.id}">${t.label}${t.n!=null?`<span class="n">${t.n}</span>`:''}</button>
`).join('');'''

html = replace_once(html, old_tabs, new_tabs, "tabs-array")

# ---------------------------------------------------------------------------
# 5) Append the Fraud Detection rendering IIFE, right before the final </script>
# ---------------------------------------------------------------------------
fraud_js = r'''

/* ---------------- Fraud & Control Detection ---------------- */
(function(){
  const FD = AUDIT.fraud_detection;
  const k = FD.kpi;

  const kpiDefs = [
    {label:'Late-posted transactions', value: fmt0(k.late_posting_count), foot: fmtSAR(k.late_posting_value)+' at risk · >'+FD.timing.late_posting_threshold_days+'d posting gap', cls:'warn'},
    {label:'After-hours activity', value: fmt0(k.off_hours_count), foot: 'transactions logged '+FD.timing.off_hours_window, cls:'warn'},
    {label:'Same-user create+post', value: fmtPct(k.same_user_create_post_pct), foot: fmt0(k.same_user_create_post_count)+' txns — no independent posting check', cls: k.same_user_create_post_pct>5 ? 'warn':''},
    {label:'Pricing anomalies', value: fmtSAR(k.price_anomaly_value), foot: fmt0(k.price_anomaly_count)+' PI lines ≥25% off their own product+supplier median', cls:'crit'},
    {label:'Movement-pattern flags', value: fmt0(k.frequent_correction_keys + k.round_trip_count + k.cancelled_count), foot: fmt0(k.frequent_correction_keys)+' frequent corrections · '+fmt0(k.round_trip_count)+' round-trips · '+fmt0(k.cancelled_count)+' cancelled'},
    {label:'Purchase returns', value: fmtSAR(k.purchase_return_value), foot: fmt0(k.purchase_return_count)+' PR lines in 2026'},
  ];
  document.getElementById('fraud-kpi-row').innerHTML = kpiDefs.map(d=>`
    <div class="kpi ${d.cls||''}"><span class="label">${d.label}</span><span class="value">${d.value}</span><span class="foot">${d.foot}</span></div>
  `).join('');

  document.getElementById('fraud-scope-callout').innerHTML = FD.generated_note;

  // ---- Timing: late-posting + off-hours, combined into one flagged-transaction table ----
  const timingRows = FD.timing.late_posting_rows.map(r=>({...r, flag_type:'Late posting', detail: r.gap_days+'d to post'}))
    .concat(FD.timing.off_hours_rows.map(r=>({...r, flag_type:'After-hours', detail: String(r.hour).padStart(2,'0')+':xx'})));
  const timingCols = [
    {key:'flag_type', label:'Flag'},
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'transaction_type', label:'Type'},
    {key:'transaction_date', label:'Transaction date'},
    {key:'detail', label:'Detail'},
    {key:'value', label:'Value (SAR)', num:true, render:r=>r.value==null?'—':fmt0(r.value)},
    {key:'created_by', label:'Created by'},
  ];
  const timingBranches = [...new Set(timingRows.map(r=>r.branch))].sort();
  const timingTbl = buildTable(document.getElementById('tbl-fraud-timing'), timingCols, timingRows, {defaultSort:'value', defaultDir:-1});
  const timingFb = makeFilterBar(document.getElementById('filter-fraud-timing'), {placeholder:'Search product / code / transaction no…', branches: timingBranches, onChange:(q,b)=>{
    timingTbl.setFilter(r => (!b||r.branch===b) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q) || (r.transaction_no||'').toLowerCase().includes(q)));
    timingFb.setCount(document.querySelectorAll('#tbl-fraud-timing tbody tr').length, timingRows.length);
  }});
  timingFb.setCount(timingRows.length, timingRows.length);
  document.getElementById('fraud-timing-note').textContent =
    `Showing top ${fmt0(FD.timing.late_posting_rows.length)} of ${fmt0(FD.timing.late_posting_total_count)} transactions posted more than ${FD.timing.late_posting_threshold_days} days after the fact, plus all ${fmt0(FD.timing.off_hours_rows.length)} transactions logged ${FD.timing.off_hours_window} — sortable/filterable together below.`;

  // ---- SoD: per-user summary ----
  const sodUserCols = [
    {key:'user', label:'User'},
    {key:'created_count', label:'Created', num:true, render:r=>fmt0(r.created_count)},
    {key:'posted_count', label:'Posted', num:true, render:r=>fmt0(r.posted_count)},
    {key:'same_user_count', label:'Same-user (created+posted)', num:true, render:r=>fmt0(r.same_user_count)},
    {key:'same_user_pct', label:'% of own postings', num:true, render:r=>r.same_user_pct==null?'—':(r.same_user_pct>=90?`<span class="badge red">${fmtPct(r.same_user_pct)}</span>`:fmtPct(r.same_user_pct))},
    {key:'created_value', label:'Value created (SAR)', num:true, render:r=>fmt0(r.created_value)},
  ];
  buildTable(document.getElementById('tbl-fraud-sod-users'), sodUserCols, FD.sod.user_summary, {defaultSort:'same_user_count', defaultDir:-1});

  // ---- SoD: sample same-user rows ----
  const sodCols = [
    {key:'transaction_no', label:'Transaction'},
    {key:'transaction_date', label:'Date'},
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'transaction_type', label:'Type'},
    {key:'created_by', label:'User (created & posted)'},
    {key:'value', label:'Value (SAR)', num:true, render:r=>r.value==null?'—':fmt0(r.value)},
  ];
  const sodBranches = [...new Set(FD.sod.same_user_rows.map(r=>r.branch))].sort();
  const sodTbl = buildTable(document.getElementById('tbl-fraud-sod'), sodCols, FD.sod.same_user_rows, {defaultSort:'value', defaultDir:-1});
  const sodFb = makeFilterBar(document.getElementById('filter-fraud-sod'), {placeholder:'Search product / code / transaction no…', branches: sodBranches, onChange:(q,b)=>{
    sodTbl.setFilter(r => (!b||r.branch===b) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q) || (r.transaction_no||'').toLowerCase().includes(q)));
    sodFb.setCount(document.querySelectorAll('#tbl-fraud-sod tbody tr').length, FD.sod.same_user_rows.length);
  }});
  sodFb.setCount(FD.sod.same_user_rows.length, FD.sod.same_user_rows.length);

  // ---- Pricing anomalies ----
  const pricingCols = [
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'supplier_name', label:'Supplier'},
    {key:'transaction_date', label:'Date'},
    {key:'unit_cost', label:'Unit cost', num:true, render:r=>fmt2(r.unit_cost)},
    {key:'group_median_cost', label:"Product+supplier median", num:true, render:r=>fmt2(r.group_median_cost)},
    {key:'deviation_pct', label:'Deviation', num:true, render:r=>`<span class="badge ${Math.abs(r.deviation_pct)>=100?'red':'amber'}">${r.deviation_pct>0?'+':''}${r.deviation_pct}%</span>`},
    {key:'deviation_value', label:'Value at risk (SAR)', num:true, render:r=>fmt0(r.deviation_value)},
  ];
  const pricingBranches = [...new Set(FD.pricing.anomaly_rows.map(r=>r.branch))].sort();
  const pricingTbl = buildTable(document.getElementById('tbl-fraud-pricing'), pricingCols, FD.pricing.anomaly_rows, {defaultSort:'deviation_value', defaultDir:-1});
  const pricingFb = makeFilterBar(document.getElementById('filter-fraud-pricing'), {placeholder:'Search product / code / supplier…', branches: pricingBranches, onChange:(q,b)=>{
    pricingTbl.setFilter(r => (!b||r.branch===b) && (!q || (r.product_name||'').toLowerCase().includes(q) || (r.product||'').toLowerCase().includes(q) || (r.supplier_name||'').toLowerCase().includes(q)));
    pricingFb.setCount(document.querySelectorAll('#tbl-fraud-pricing tbody tr').length, FD.pricing.anomaly_rows.length);
  }});
  pricingFb.setCount(FD.pricing.anomaly_rows.length, FD.pricing.anomaly_rows.length);
  document.getElementById('fraud-pricing-note').textContent = FD.pricing.method + ` Showing ${fmt0(FD.pricing.anomaly_rows.length)} of ${fmt0(FD.pricing.anomaly_total_count)} flagged lines.`;

  // ---- Movement: frequent corrections ----
  const corrCols = [
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'correction_count', label:'Corrections in 2026', num:true, render:r=>fmt0(r.correction_count)},
    {key:'total_value', label:'Value (SAR)', num:true, render:r=>fmt0(r.total_value)},
  ];
  buildTable(document.getElementById('tbl-fraud-corrections'), corrCols, FD.movement.frequent_corrections, {defaultSort:'correction_count', defaultDir:-1});

  // ---- Movement: round-trip transfers ----
  const rtCols = [
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'out_branch', label:'Out → branch'},
    {key:'out_store_name', label:'Out store'},
    {key:'out_date', label:'Out date'},
    {key:'out_qty', label:'Out qty', num:true, render:r=>fmt0(r.out_qty)},
    {key:'back_branch', label:'Back → branch'},
    {key:'back_date', label:'Back date'},
    {key:'back_qty', label:'Back qty', num:true, render:r=>fmt0(r.back_qty)},
    {key:'days_between', label:'Days between', num:true, render:r=>fmt0(r.days_between)},
  ];
  buildTable(document.getElementById('tbl-fraud-roundtrip'), rtCols, FD.movement.round_trip_transfers, {defaultSort:'days_between', defaultDir:1});

  // ---- Movement: cancelled transactions ----
  const cancCols = [
    {key:'branch', label:'Branch'},
    {key:'store_name', label:'Store'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'transaction_type', label:'Type'},
    {key:'transaction_no', label:'Transaction'},
    {key:'transaction_date', label:'Date'},
    {key:'created_by', label:'Created by'},
  ];
  buildTable(document.getElementById('tbl-fraud-cancelled'), cancCols, FD.movement.cancelled_rows, {defaultSort:'transaction_date', defaultDir:-1});
})();
'''

marker = "  stopBtn.addEventListener('click', stopSpeaking);\n})();"
if html.count(marker) != 1:
    raise SystemExit(f"[fraud-js-anchor] expected exactly 1 occurrence, found {html.count(marker)}")
html = html.replace(marker, marker + fraud_js, 1)

# ---------------------------------------------------------------------------
# 6) Re-embed the audit-data JSON (now including fraud_detection)
# ---------------------------------------------------------------------------
start_tag = '<script id="audit-data" type="application/json">'
end_tag = '</script>\n<script>'
start_i = html.index(start_tag) + len(start_tag)
end_i = html.index(end_tag, start_i)
new_json_text = json.dumps(data, ensure_ascii=False, indent=2)
html = html[:start_i] + new_json_text + html[end_i:]

DASH.write_text(html, encoding="utf-8")
print("done -- dashboard.html updated:", len(html), "chars")
