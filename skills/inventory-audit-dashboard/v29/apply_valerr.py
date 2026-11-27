import json,sys
W='/home/claude/w'
SRC=sys.argv[1] if len(sys.argv)>1 else f'{W}/dashboard_v29.html'; OUT=sys.argv[2] if len(sys.argv)>2 else f'{W}/dashboard_v30.html'
h=open(SRC,encoding='utf-8').read()
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
# 1. data key
tag='<script id="audit-data" type="application/json">'
si=h.index(tag)+len(tag); ei=h.index('</script>',si)
A=json.loads(h[si:ei])
if 'valuation_errors' not in A:
    A['valuation_errors']=json.load(open(f'{W}/valerr/valuation_errors.json',encoding='utf-8'))
    js=json.dumps(A,ensure_ascii=False,separators=(',',':')); assert '</' not in js
    h=h[:si]+js+h[ei:]
# 2. panel
PANEL='''      <section class="panel" id="panel-valerr">
        <div class="section-head"><h2>Valuation Errors — cost mismatches that inflate or deflate stock value</h2><span class="section-note" id="ve-note"></span></div>
        <div class="callout amber" id="ve-callout"></div>
        <section class="kpirow" id="ve-kpi"></section>
        <div class="filterbar">
          <input type="search" id="ve-search" placeholder="Search product / code…" aria-label="Search products">
          <select id="ve-pat" aria-label="Pattern"><option value="">All patterns</option><option value="TR">Transfer received at a different cost</option><option value="PI">Purchase price jump</option><option value="VAL">Stock cost far from latest purchase</option></select>
          <select id="ve-dir" aria-label="Effect on stock value"><option value="">Inflated or deflated</option><option value="inflated">Stock value inflated</option><option value="deflated">Stock value deflated</option></select>
          <select id="ve-sev" aria-label="Severity"><option value="">All severities</option><option value="high">High</option><option value="medium">Medium</option><option value="low">Low</option></select>
          <span class="count" id="ve-count"></span>
          <button type="button" id="ve-export">Download (CSV)</button>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-ve-sku"></table></div></div>
        <p class="wl-fine" id="ve-fine"></p>
        <div class="section-head" style="margin-top:26px;"><h2 style="font-size:14px;">The movements behind the flags</h2><span class="section-note" id="ve-ev-note"></span></div>
        <div class="filterbar">
          <input type="search" id="ve-ev-search" placeholder="Search product / code / document…" aria-label="Search movements">
          <select id="ve-ev-kind" aria-label="Movement type"><option value="">Transfers and purchases</option><option value="TR">Transfer receipts only</option><option value="PI">Purchases only</option></select>
          <span class="count" id="ve-ev-count"></span>
          <button type="button" id="ve-ev-export">Download (CSV)</button>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-ve-ev"></table></div></div>
      </section>

'''
rep('      <section class="panel" id="panel-askai">',PANEL+'      <section class="panel" id="panel-askai">','panel')
# 3. tab
rep("  {id:'askai', label:'🤖 Ask AI', divider:'Governance & Reporting'},",
    "  {id:'valerr', label:'⚖️ Valuation Errors', n: AUDIT.valuation_errors.kpi.skus_flagged},\n  {id:'askai', label:'🤖 Ask AI', divider:'Governance & Reporting'},",'tab')
# 4. JS after overstock IIFE
JS=r'''
/* ---------------- Valuation errors (21 Oct 2026) ---------------- */
(function(){
  const VE = AUDIT.valuation_errors, K = VE.kpi;
  const PAT = {TR:'Transfer cost', PI:'Purchase jump', VAL:'Stock vs last purchase'};
  const sevBadge = s => `<span class="badge ${s==='high'?'red':(s==='medium'?'amber':'')}">${s}</span>`;
  const sgn = n => n==null?'—':(n>0?'+':n<0?'−':'')+fmt0(Math.abs(n));
  const px = n => n==null?'—':(n>=100?fmt2(n):(+n.toFixed(4)).toString());
  document.getElementById('ve-note').textContent = 'Posted ERP movements to '+K.as_of+' · transfers since 2024 · purchases since Oct 2025 · '+fmt0(K.skus_flagged)+' products flagged';
  document.getElementById('ve-callout').innerHTML = '<b>Why this matters.</b> Stock is valued at the last posted unit cost, so one wrong cost carries into every unit on hand. The ERP is meant to restart the average when a balance reaches zero, but when a branch receives a transfer it can blend in its own old average instead of keeping the cost the sender used — e.g. 103463 Numbering machine was bought at 1.67 and sent at 1.67, yet received at 109.50. Three patterns are checked: <b>(1)</b> a transfer received at a cost at least 2× away from the cost it was sent at, <b>(2)</b> a purchase priced 3× or more away from the previous purchase of the same product, <b>(3)</b> the cost the stock is valued at being 2× or more away from the latest purchase cost. Purchase invoices that have a return are not used.';
  const card = (label,val,foot,cls) => `<div class="kpi ${cls||''}"><div class="label">${label}</div><div class="value">${val}</div><div class="foot">${foot}</div></div>`;
  document.getElementById('ve-kpi').innerHTML =
    card('Products flagged', fmt0(K.skus_flagged), fmt0(K.skus_with_impact)+' with stock on hand at a doubtful cost')
   +card('Stock value inflated', 'SAR '+fmt0(K.inflated_value), 'valued above the latest purchase cost','warn')
   +card('Stock value deflated', 'SAR '+fmt0(Math.abs(K.deflated_value)), 'valued below the latest purchase cost','warn')
   +card('Net effect on stock value', 'SAR '+sgn(K.net_impact), fmt2(K.pct_of_stock_value)+'% of total stock value')
   +card('Transfers at a different cost', fmt0(K.events_tr), 'received ≥2× away from the send cost')
   +card('Purchase price jumps', fmt0(K.events_pi), '≥3× vs previous purchase · '+fmt0(K.pi_events_dropped_returned)+' left out (invoice returned)');
  const skuCols = [
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'patterns', label:'Patterns', render:r=>r.patterns.map(p=>`<span class="badge blue" title="${esc(PAT[p])}">${p}</span>`).join(' '), searchable:false},
    {key:'n_events', label:'Movements', num:true, render:r=>fmt0(r.n_events)},
    {key:'max_ratio', label:'Largest gap', num:true, render:r=>r.max_ratio>=999?'∞':'×'+(+r.max_ratio.toFixed(1))},
    {key:'on_hand', label:'On hand', num:true, render:r=>fmt0(r.on_hand)},
    {key:'valuation_unit_cost', label:'Valued at', num:true, render:r=>r.on_hand?px(r.valuation_unit_cost||0):'—'},
    {key:'reference_cost', label:'Latest purchase / send cost', num:true, render:r=>px(r.reference_cost)},
    {key:'impact', label:'Effect on value (SAR)', num:true, render:r=>r.impact===0?'—':`<b style="color:var(--${r.impact>0?'red':'amber'})">${sgn(r.impact)}</b>`},
    {key:'direction', label:'Direction', render:r=>r.direction==='inflated'?'<span class="badge red">inflated</span>':(r.direction==='deflated'?'<span class="badge amber">deflated</span>':'—')},
    {key:'severity', label:'Severity', render:r=>sevBadge(r.severity)},
  ];
  const skuTbl = buildTable(document.getElementById('tbl-ve-sku'), skuCols, VE.skus, {defaultSort:'impact', defaultDir:-1});
  const evCols = [
    {key:'date', label:'Date'},
    {key:'kind', label:'Type', render:r=>r.kind==='TR'?'<span class="badge blue">Transfer in</span>':'<span class="badge accent">Purchase</span>'},
    {key:'product', label:'Code'},
    {key:'product_name', label:'Product', name:true},
    {key:'doc', label:'Document', render:r=>`<span style="font-family:'IBM Plex Mono',monospace;font-size:12px;">${esc(r.doc)}</span><br><span class="wl-prev">vs ${esc(r.ref_doc)}</span>`},
    {key:'qty', label:'Qty', num:true, render:r=>fmt0(r.qty)},
    {key:'cost_from', label:'Earlier cost', num:true, render:r=>px(r.cost_from)},
    {key:'cost_to', label:'Cost booked', num:true, render:r=>px(r.cost_to)},
    {key:'ratio', label:'Gap', num:true, render:r=>r.ratio>=999?'∞':'×'+r.ratio},
    {key:'effect', label:'Effect (SAR)', num:true, render:r=>sgn(r.effect)},
    {key:'on_hand_now', label:'On hand now', num:true, render:r=>fmt0(r.on_hand_now)},
    {key:'severity', label:'Severity', render:r=>sevBadge(r.severity)},
  ];
  const evTbl = buildTable(document.getElementById('tbl-ve-ev'), evCols, VE.events, {defaultSort:'effect', defaultDir:-1});
  const g = id => document.getElementById(id);
  function skuRefilter(){
    const q=g('ve-search').value.trim().toLowerCase(), p=g('ve-pat').value, d=g('ve-dir').value, s=g('ve-sev').value;
    skuTbl.setFilter(r=>(!q||(r.product_name||'').toLowerCase().includes(q)||r.product.toLowerCase().includes(q))&&(!p||r.patterns.includes(p))&&(!d||r.direction===d)&&(!s||r.severity===s));
    g('ve-count').textContent = document.querySelectorAll('#tbl-ve-sku tbody tr').length+' of '+VE.skus.length+' products';
  }
  function evRefilter(){
    const q=g('ve-ev-search').value.trim().toLowerCase(), k=g('ve-ev-kind').value;
    evTbl.setFilter(r=>(!q||(r.product_name||'').toLowerCase().includes(q)||r.product.toLowerCase().includes(q)||r.doc.toLowerCase().includes(q)||(r.ref_doc||'').toLowerCase().includes(q))&&(!k||r.kind===k));
    g('ve-ev-count').textContent = document.querySelectorAll('#tbl-ve-ev tbody tr').length+' of '+VE.events.length+' movements';
  }
  ['ve-search'].forEach(i=>g(i).addEventListener('input',skuRefilter)); ['ve-pat','ve-dir','ve-sev'].forEach(i=>g(i).addEventListener('change',skuRefilter));
  g('ve-ev-search').addEventListener('input',evRefilter); g('ve-ev-kind').addEventListener('change',evRefilter);
  skuRefilter(); evRefilter();
  g('ve-ev-note').textContent = fmt0(VE.events.length)+' movements · effect = quantity × (cost booked − earlier cost)';
  g('ve-fine').textContent = 'Effect on value = units on hand × (the cost the stock is valued at − the latest purchase cost, or the sending cost when the product was only transferred). It is counted only where the two costs differ by 2× or more; positive means stock is overstated, negative understated. The check is read-only: the fix is a cost correction or an adjustment posted in the ERP.';
  function csv(rows, cols, name){
    const q = v => '"'+String(v==null?'':v).replace(/"/g,'""')+'"';
    const txt = [cols.map(c=>q(c[1])).join(',')].concat(rows.map(r=>cols.map(c=>q(Array.isArray(r[c[0]])?r[c[0]].join(' '):r[c[0]])).join(','))).join('\n');
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿'+txt],{type:'text/csv'})); a.download = name; document.body.appendChild(a); a.click(); a.remove();
  }
  g('ve-export').addEventListener('click',()=>csv(VE.skus,[['product','Code'],['product_name','Product'],['patterns','Patterns'],['n_events','Movements'],['max_ratio','Largest gap'],['on_hand','On hand'],['valuation_unit_cost','Valued at'],['reference_cost','Reference cost'],['on_hand_value','On-hand value'],['value_at_reference','Value at reference cost'],['impact','Effect on value'],['direction','Direction'],['severity','Severity']],'valuation_errors_products.csv'));
  g('ve-ev-export').addEventListener('click',()=>csv(VE.events,[['date','Date'],['kind','Type'],['product','Code'],['product_name','Product'],['doc','Document'],['ref_doc','Compared with'],['qty','Qty'],['cost_from','Earlier cost'],['cost_to','Cost booked'],['ratio','Gap'],['effect','Effect'],['on_hand_now','On hand now'],['severity','Severity']],'valuation_errors_movements.csv'));
  window.VE_SUMMARY = function(){
    return {what:'Cost mismatches that inflate or deflate stock value (transfers received at a cost far from the send cost; purchase price jumps of 3x or more; stock valued far from the latest purchase cost). Purchase invoices with a return are excluded.',
      kpi:K, top_products:VE.skus.slice(0,15).map(r=>({code:r.product,product:r.product_name,patterns:r.patterns,on_hand:r.on_hand,valued_at:r.valuation_unit_cost,reference_cost:r.reference_cost,effect_on_value_sar:r.impact,direction:r.direction}))};
  };
})();
'''
anchor="  fb.setCount(AUDIT.overstock.length, AUDIT.overstock.length);\n})();\n"
rep(anchor,anchor+JS,'js')
# 5. ask-ai digest
rep("      price_vendor_watchlist: WL.summary(),","      price_vendor_watchlist: WL.summary(),\n      valuation_errors: (window.VE_SUMMARY?window.VE_SUMMARY():null),",'digest')
open(OUT,'w',encoding='utf-8').write(h); print(len(h))
