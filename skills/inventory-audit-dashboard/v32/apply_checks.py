import json,sys,re
W='/home/claude/w'
SRC=sys.argv[1]; OUT=sys.argv[2]; CHK=sys.argv[3] if len(sys.argv)>3 else f'{W}/checks/checks.json'
h=open(SRC,encoding='utf-8').read()
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
C=json.load(open(CHK,encoding='utf-8'))
tag='<script id="audit-data" type="application/json">'
si=h.index(tag)+len(tag); ei=h.index('</script>',si)
A=json.loads(h[si:ei])
# ---- data merge
A['supplier_savings_opportunities']=C['savings']['rows']
ctmap={(r['product'],r['store']):r for r in C['ct']['rows']}
for k in ('overstock','slow_moving'):
    for r in A[k]:
        c=ctmap.get((r['product'],str(r['store'])))
        r['ct_pct']=c['ct_pct'] if c else 0; r['ct_qty']=c['ct_qty'] if c else 0
A['checks']=dict(savings_kpi=C['savings']['kpi'],ct=C['ct'],uom=C['uom'])
js=json.dumps(A,ensure_ascii=False,separators=(',',':')); assert '</' not in js
h=h[:si]+js+h[ei:]
# ---- 1. savings panel html
rep('''        <div class="tablewrap"><div class="scrollbody"><table id="tbl-savings"></table></div></div>''',
'''        <div class="callout amber" id="sav-callout"></div>
        <section class="kpirow" id="sav-kpi"></section>
        <div class="filterbar"><select id="sav-status" aria-label="Status"><option value="">All opportunities</option><option value="open">Still open</option><option value="realized">Already realized</option></select><span class="count" id="sav-count"></span><button type="button" id="sav-export">Download (CSV)</button></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-savings"></table></div></div>''','sav html')
rep('''    {key:'gap_pct', label:'Gap %', num:true, render:r=>fmtPct(r.gap_pct)},
  ];
  buildTable(document.getElementById('tbl-savings'), savCols, AUDIT.supplier_savings_opportunities, {defaultSort:'gap_pct', defaultDir:-1});''',
'''    {key:'gap_pct', label:'Gap %', num:true, render:r=>fmtPct(r.gap_pct)},
    {key:'last_supplier', label:'Latest purchase from', name:true, render:r=>r.last_supplier?esc(r.last_supplier)+'<br><span class="wl-prev">'+esc(r.last_date||'')+'</span>':'—'},
    {key:'status', label:'Status', render:r=>r.status==='realized'?'<span class="badge accent">realized</span>':'<span class="badge amber">open</span>'},
  ];
  const savTbl = buildTable(document.getElementById('tbl-savings'), savCols, AUDIT.supplier_savings_opportunities, {defaultSort:'gap_pct', defaultDir:-1});
  (function(){
    const K=AUDIT.checks.savings_kpi, g=id=>document.getElementById(id);
    g('sav-callout').innerHTML='<b>Realized vs open.</b> The comparison above spans the whole year, so a gap can reflect purchases that were already moved to the cheaper supplier. An opportunity is marked <b>realized</b> when the <i>latest</i> purchase of the product was from the cheapest supplier; only <b>open</b> ones are still to be acted on.';
    const open=AUDIT.supplier_savings_opportunities.filter(r=>r.status==='open'), avgOpen=open.length?open.reduce((a,r)=>a+r.gap_pct,0)/open.length:0;
    g('sav-kpi').innerHTML=[['Opportunities listed',fmt0(K.total),'products bought from 2+ suppliers',''],['Already realized',fmt0(K.realized),Math.round(100*K.realized/K.total)+'% — latest purchase was from the cheapest supplier',''],['Still open',fmt0(K.open),'average gap '+fmtPct(avgOpen),'warn']].map(d=>`<div class="kpi ${d[3]}"><span class="label">${d[0]}</span><span class="value">${d[1]}</span><span class="foot">${d[2]}</span></div>`).join('');
    function ref(){const s=g('sav-status').value; savTbl.setFilter(r=>!s||r.status===s); g('sav-count').textContent=document.querySelectorAll('#tbl-savings tbody tr').length+' of '+AUDIT.supplier_savings_opportunities.length;}
    g('sav-status').addEventListener('change',ref); ref();
    g('sav-export').addEventListener('click',()=>window.__csv(AUDIT.supplier_savings_opportunities,[['product','Code'],['product_name','Product'],['cheapest_supplier','Cheapest supplier'],['cheapest_price','Cheapest price'],['priciest_supplier','Priciest supplier'],['priciest_price','Priciest price'],['gap_pct','Gap %'],['last_supplier','Latest purchase from'],['last_date','Latest purchase date'],['status','Status']],'savings_opportunities_status.csv'));
  })();''','sav js')
# ---- 2. count-created column in overstock + slow
CTCOL='''    {key:'ct_pct', label:'Count-created', num:true, render:r=>r.ct_pct>0?(r.ct_pct>=50?'<span class="badge amber" title="Units created by a stock count, not bought">'+fmt0(r.ct_pct)+'%</span>':fmt0(r.ct_pct)+'%'):'—'},
'''
rep("    {key:'qty_out_6mo', label:'Outbound /6mo'",CTCOL+"    {key:'qty_out_6mo', label:'Outbound /6mo'",'ov col')
rep("    {key:'last_out_date', label:'Last movement'",CTCOL+"    {key:'last_out_date', label:'Last movement'",'sm col')
# ---- 3. CT section in cycle-count panel
rep('''        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">All events</h2></div>
        <div class="filterbar" id="filter-cc-events"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-events"></table></div></div>
      </section>''','''        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">All events</h2></div>
        <div class="filterbar" id="filter-cc-events"></div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-cc-events"></table></div></div>
        <div class="section-head" style="margin-top:30px;"><h2>Stock created by counts and still on hand</h2><span class="section-note" id="ct-note"></span></div>
        <div class="callout amber" id="ct-callout"></div>
        <section class="kpirow" id="ct-kpi"></section>
        <div class="chartcard"><h3>Largest count-created stock by value — top 10 (amber = also overstock · red = also slow-moving)</h3><div id="chart-ct"></div></div>
        <div class="filterbar">
          <input type="search" id="ct-search" placeholder="Search product / code…" aria-label="Search products">
          <select id="ct-branch" aria-label="Branch"><option value="">All branches</option></select>
          <select id="ct-flag" aria-label="Flag"><option value="">All</option><option value="ov">Also in Overstock</option><option value="sm">Also in Slow-moving</option><option value="most">Mostly count-created (≥50%)</option></select>
          <span class="count" id="ct-count"></span><button type="button" id="ct-export">Download (CSV)</button>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-ct"></table></div></div>
      </section>''','ct html')
# ---- 4. UOM section in valerr panel
rep('''        <div class="tablewrap"><div class="scrollbody"><table id="tbl-ve-ev"></table></div></div>
      </section>''','''        <div class="tablewrap"><div class="scrollbody"><table id="tbl-ve-ev"></table></div></div>
        <div class="section-head" style="margin-top:30px;"><h2>Pack / UOM mismatches — the same code bought in different packs</h2><span class="section-note" id="um-note"></span></div>
        <div class="callout amber" id="um-callout"></div>
        <section class="kpirow" id="um-kpi"></section>
        <div class="filterbar">
          <input type="search" id="um-search" placeholder="Search product / code…" aria-label="Search products">
          <select id="um-sev" aria-label="Signal"><option value="">All signals</option><option value="high">Cost = pack multiple (likely wrong pack)</option><option value="medium">Large cost gap between packs</option><option value="low">Pack mix only</option></select>
          <span class="count" id="um-count"></span><button type="button" id="um-export">Download (CSV)</button>
        </div>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-um"></table></div></div>
      </section>''','um html')
JS=r'''
/* ---------------- Unit checks (24 Oct 2026): count-created stock + pack/UOM mismatch ---------------- */
window.__csv = window.__csv || function(rows, cols, name){
  const q = v => '"'+String(v==null?'':v).replace(/"/g,'""')+'"';
  const txt = [cols.map(c=>q(c[1])).join(',')].concat(rows.map(r=>cols.map(c=>q(r[c[0]])).join(','))).join('\n');
  const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(['﻿'+txt],{type:'text/csv'})); a.download = name; document.body.appendChild(a); a.click(); a.remove();
};
function __bars(el, items, fmtv){
  const w=760, rowH=26, pad={l:230,r:90,t:6,b:6}, h=pad.t+pad.b+items.length*rowH, max=Math.max(...items.map(i=>i.value),1);
  let s=`<svg viewBox="0 0 ${w} ${h}" width="100%" height="${h}" role="img">`;
  items.forEach((it,i)=>{const y=pad.t+i*rowH+3, bw=(w-pad.l-pad.r)*it.value/max;
    s+=`<text x="${pad.l-10}" y="${y+14}" font-size="11" text-anchor="end">${esc(it.label.length>34?it.label.slice(0,32)+'…':it.label)}</text><rect x="${pad.l}" y="${y}" width="${Math.max(bw,1)}" height="${rowH-9}" rx="3" fill="var(--${it.color||'blue'})" opacity="0.85"/><text class="bar-label" x="${pad.l+bw+8}" y="${y+14}" font-size="11">${fmtv(it.value)}</text>`;});
  el.innerHTML=s+'</svg>';
}
(function(){
  const CK=AUDIT.checks.ct, K=CK.kpi, R=CK.rows, g=id=>document.getElementById(id);
  g('ct-note').textContent = fmt0(K.skus)+' product-store lines · batches created by a stock count (batch no. starting CT) with quantity still on hand';
  g('ct-callout').innerHTML='<b>Why this matters.</b> A count that finds more units than the system shows creates a new batch (CT…) at the current cost. Those units were never purchased, so they should not be read as over-buying; and if the count was wrong or the item is a different pack, the stock value is overstated. Lines where count-created units are most of the balance, or that also appear as Overstock or Slow-moving, need a physical re-check first. Based on batch-tracked items in the latest extract.';
  g('ct-kpi').innerHTML=[['Count-created stock','SAR '+fmt0(K.value),fmt2(K.pct_of_stock)+'% of total stock value · '+fmt0(K.units)+' units',''],['Product-store lines',fmt0(K.skus),fmt0(K.mostly_ct)+' where ≥50% of the balance is count-created','warn'],['Also in Overstock',fmt0(K.in_overstock),'SAR '+fmt0(K.in_overstock_value)+' of the overstock list was created by counts','warn'],['Also in Slow-moving',fmt0(K.in_slow),'SAR '+fmt0(K.in_slow_value)+' of the slow-moving list was created by counts','']].map(d=>`<div class="kpi ${d[3]}"><span class="label">${d[0]}</span><span class="value">${d[1]}</span><span class="foot">${d[2]}</span></div>`).join('');
  __bars(g('chart-ct'), R.slice(0,10).map(r=>({label:r.product+' · '+r.product_name+' ('+r.branch+')',value:r.ct_value,color:r.in_overstock?'amber':(r.in_slow?'red':'blue')})), v=>fmt0(v));
  const cols=[{key:'branch',label:'Branch'},{key:'product',label:'Code'},{key:'product_name',label:'Product',name:true},
    {key:'on_hand',label:'On hand',num:true,render:r=>fmt0(r.on_hand)},{key:'ct_qty',label:'Count-created',num:true,render:r=>fmt0(r.ct_qty)},
    {key:'ct_pct',label:'Share',num:true,render:r=>r.ct_pct>=50?'<b>'+fmt0(r.ct_pct)+'%</b>':fmt0(r.ct_pct)+'%'},
    {key:'ct_value',label:'Value (SAR)',num:true,render:r=>fmt0(r.ct_value)},{key:'batches',label:'CT batches',num:true},
    {key:'earliest_expiry',label:'Earliest expiry',render:r=>r.earliest_expiry||'—'},
    {key:'in_overstock',label:'Flags',render:r=>(r.in_overstock?'<span class="badge amber">overstock</span> ':'')+(r.in_slow?'<span class="badge red">slow-moving</span>':'')||'—',searchable:false}];
  const tbl=buildTable(g('tbl-ct'),cols,R,{defaultSort:'ct_value',defaultDir:-1});
  [...new Set(R.map(r=>r.branch))].sort().forEach(b=>{const o=document.createElement('option');o.value=b;o.textContent=b;g('ct-branch').appendChild(o);});
  function ref(){const q=g('ct-search').value.trim().toLowerCase(),b=g('ct-branch').value,f=g('ct-flag').value;
    tbl.setFilter(r=>(!q||(r.product_name||'').toLowerCase().includes(q)||r.product.toLowerCase().includes(q))&&(!b||r.branch===b)&&(!f||(f==='ov'&&r.in_overstock)||(f==='sm'&&r.in_slow)||(f==='most'&&r.ct_pct>=50)));
    g('ct-count').textContent=document.querySelectorAll('#tbl-ct tbody tr').length+' of '+R.length+' lines';}
  g('ct-search').addEventListener('input',ref); ['ct-branch','ct-flag'].forEach(i=>g(i).addEventListener('change',ref)); ref();
  g('ct-export').addEventListener('click',()=>window.__csv(R,[['branch','Branch'],['product','Code'],['product_name','Product'],['on_hand','On hand'],['ct_qty','Count-created qty'],['ct_pct','Share %'],['unit_cost','Unit cost'],['ct_value','Value SAR'],['batches','CT batches'],['earliest_expiry','Earliest expiry'],['in_overstock','In overstock'],['in_slow','In slow-moving']],'count_created_stock.csv'));
})();
(function(){
  const UK=AUDIT.checks.uom, K=UK.kpi, R=UK.rows, g=id=>document.getElementById(id);
  const SEV={high:'<span class="badge red">pack multiple</span>',medium:'<span class="badge amber">cost gap</span>',low:'<span class="badge">pack mix</span>'};
  g('um-note').textContent=fmt0(K.skus)+' products bought in 2+ pack sizes since '+K.since+' · unit cost shown per primary unit';
  g('um-callout').innerHTML='<b>Why this matters.</b> The ERP stores cost per primary unit, so the same code bought as PC and as a box should give the same cost per unit. When it does not, the pack or UOM on a line was probably entered wrongly and the price is not like-for-like. <b>Pack multiple</b>: the higher cost equals the lower cost × the pack size (e.g. 102922: 185.225 = 26.46 × 7, so a box price was booked per piece). <b>Cost gap</b>: ≥3× difference between packs with no pack-size explanation. <b>Pack mix</b>: several packs, costs consistent — informational. Purchases from 1 Jan 2025; invoices that were later returned are not removed here.';
  g('um-kpi').innerHTML=[['Products with mixed packs',fmt0(K.skus),'SAR '+fmt0(K.value_all)+' on hand',''],['Pack multiple',fmt0(K.high),'SAR '+fmt0(K.value_high)+' on hand at risk of a wrong cost','crit'],['Large cost gap',fmt0(K.medium),'to confirm with purchasing','warn'],['Pack mix only',fmt0(K.low),'costs consistent','']].map(d=>`<div class="kpi ${d[3]}"><span class="label">${d[0]}</span><span class="value">${d[1]}</span><span class="foot">${d[2]}</span></div>`).join('');
  const cols=[{key:'product',label:'Code'},{key:'product_name',label:'Product',name:true},
    {key:'severity',label:'Signal',render:r=>SEV[r.severity]},
    {key:'packs',label:'Packs bought',searchable:false},
    {key:'variants',label:'Cost per unit by pack',searchable:false,render:r=>r.variants.map(v=>`${esc(v.uom)}: ${v.min_cost===v.max_cost?v.min_cost:v.min_cost+'–'+v.max_cost} <span class="wl-prev">(${v.lines} lines)</span>`).join('<br>')},
    {key:'ratio',label:'Gap',num:true,render:r=>'×'+r.ratio},
    {key:'reason',label:'Why flagged',render:r=>esc(r.reason||'—')},
    {key:'on_hand',label:'On hand',num:true,render:r=>fmt0(r.on_hand)},
    {key:'on_hand_value',label:'Value (SAR)',num:true,render:r=>fmt0(r.on_hand_value)},
    {key:'last_purchase',label:'Last purchase'}];
  const tbl=buildTable(g('tbl-um'),cols,R,{defaultSort:'on_hand_value',defaultDir:-1});
  function ref(){const q=g('um-search').value.trim().toLowerCase(),s=g('um-sev').value;
    tbl.setFilter(r=>(!q||(r.product_name||'').toLowerCase().includes(q)||r.product.toLowerCase().includes(q))&&(!s||r.severity===s));
    g('um-count').textContent=document.querySelectorAll('#tbl-um tbody tr').length+' of '+R.length+' products';}
  g('um-search').addEventListener('input',ref); g('um-sev').addEventListener('change',ref); ref();
  g('um-export').addEventListener('click',()=>window.__csv(R,[['product','Code'],['product_name','Product'],['severity','Signal'],['packs','Packs'],['min_cost','Lowest cost/unit'],['max_cost','Highest cost/unit'],['ratio','Gap x'],['reason','Why flagged'],['on_hand','On hand'],['on_hand_value','Value SAR'],['last_purchase','Last purchase']],'uom_pack_mismatch.csv'));
  window.CHK_SUMMARY=function(){const sv=AUDIT.checks.savings_kpi;return {savings_status:sv,count_created:{kpi:AUDIT.checks.ct.kpi,top:AUDIT.checks.ct.rows.slice(0,10).map(r=>({code:r.product,product:r.product_name,branch:r.branch,share_pct:r.ct_pct,value_sar:r.ct_value,overstock:r.in_overstock,slow:r.in_slow}))},uom_mismatch:{kpi:K,top:R.filter(r=>r.severity!=='low').slice(0,12).map(r=>({code:r.product,product:r.product_name,signal:r.severity,why:r.reason,on_hand_value_sar:r.on_hand_value}))}};};
})();
'''
anchor="/* ---------------- Slow-moving ---------------- */"
rep(anchor,JS+"\n"+anchor,'js')
rep("      valuation_errors: (window.VE_SUMMARY?window.VE_SUMMARY():null),","      valuation_errors: (window.VE_SUMMARY?window.VE_SUMMARY():null),\n      unit_checks: (window.CHK_SUMMARY?window.CHK_SUMMARY():null),",'digest')
open(OUT,'w',encoding='utf-8').write(h); print(len(h))
