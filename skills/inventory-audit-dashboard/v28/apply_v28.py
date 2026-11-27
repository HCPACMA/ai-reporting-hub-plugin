import json,shutil
SCR='/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad'
W=f'{SCR}/dashboard_askai.html'
shutil.copyfile(W,f'{SCR}/dashboard_askai.pre_v28.html')
h=open(W,encoding='utf-8').read()
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
# 1) embed dims into the audit JSON
tag='<script id="audit-data" type="application/json">'
si=h.index(tag)+len(tag); ei=h.index('</script>',si)
A=json.loads(h[si:ei]); A['dims']=json.load(open(f'{SCR}/v28/dims.json',encoding='utf-8'))
js=json.dumps(A,ensure_ascii=False,separators=(',',':')); assert '</' not in js
h=h[:si]+js+h[ei:]
# 2) CSS
css="""
.gfbar{position:sticky; top:calc(env(safe-area-inset-top,0px) + 70px); z-index:18; display:flex; flex-wrap:wrap; gap:10px 14px; align-items:center; padding:9px 12px; margin-block:10px 0; background:var(--surface); border:1px solid var(--border); border-radius:10px;}
.gfbar .gf-t{font-size:12.5px; font-weight:700; color:var(--ink-2);}
.gfbar label{display:flex; flex-direction:column; gap:2px; font-size:11px; color:var(--ink-mute);}
.gfbar select{font:inherit; font-size:13px; min-width:190px; max-width:260px; padding:6px 8px; border-radius:7px; border:1px solid var(--border); background:var(--bg); color:var(--ink);}
.gfbar button{appearance:none; font:inherit; font-size:12.5px; padding:7px 12px; border-radius:7px; border:1px solid var(--border); background:var(--surface-2); color:var(--ink-2); cursor:pointer;}
@media (max-width:900px){.gfbar{position:static;}}
.gfbar .gf-note{font-size:11.5px; color:var(--ink-mute); flex:1 1 260px;}
.gfbar.on{border-color:#0f6e5c; box-shadow:0 0 0 1px #0f6e5c inset;}
"""
rep('</style>',css+'</style>','css',h.count('</style>')) if h.count('</style>')==1 else None
if css not in h:
    i=h.index('</style>'); h=h[:i]+css+h[i:]
# 3) HTML bar
rep('''    <div class="content-col">
    <main>''','''    <div class="content-col">
    <div class="gfbar" id="gfbar" role="search" aria-label="Global filters"></div>
    <main>''','bar')# 4) JS: filter engine + buildTable hooks
engine=r"""
/* ---------------- Global item / supplier filters (Version 28) ---------------- */
const DIM = AUDIT.dims;
const GF = {st:'', ig:'', pc:'', reg:new Map()};
const DIM_SUPNO = {}; Object.keys(DIM.sup).forEach(n=>{ DIM_SUPNO[DIM.sup[n].no] = DIM.sup[n]; });
const gfProd = r => r.product!=null ? String(r.product) : (r.p!=null ? String(r.p) : null);
const gfSup = r => r.supplier_name!=null ? DIM.sup[r.supplier_name] : (r.sn!=null ? (DIM.sup[r.sn]||DIM_SUPNO[r.s]) : (r.s!=null ? DIM_SUPNO[r.s] : null));
const gfHasSup = r => r.supplier_name!=null || r.sn!=null || r.s!=null;
function gfPass(r){
  if(!GF.st && !GF.ig && !GF.pc) return true;
  const code = gfProd(r), sp = gfSup(r);
  if(code!=null){
    const pd = DIM.prod[code];
    if(GF.ig || GF.pc){ if(!pd) return false; if(GF.ig && pd[0]!==GF.ig) return false; if(GF.pc && pd[1]!==GF.pc) return false; }
    if(GF.st){ if(sp){ if(sp.t!==GF.st) return false; } else { const t=DIM.pt[code]; if(!t || t.indexOf(GF.st)<0) return false; } }
    return true;
  }
  if(gfHasSup(r)){
    if(!sp) return false;
    if(GF.st && sp.t!==GF.st) return false;
    if(Array.isArray(r.L) && (GF.ig || GF.pc)){   // invoice rows: keep when any invoice line is in the group / category
      return r.L.some(l=>{ const pd = DIM.prod[String(l[0])]; return pd && (!GF.ig || pd[0]===GF.ig) && (!GF.pc || pd[1]===GF.pc); });
    }
    if(GF.ig && !(GF.ig in sp.ig)) return false;
    if(GF.pc && !(GF.pc in sp.pc)) return false;
  }
  return true;
}
function gfTop(m, names, n){ return Object.entries(m||{}).sort((a,b)=>b[1]-a[1]).slice(0,n).map(e=>names[e[0]]||e[0]).join(' · '); }
function gfAugment(tableEl, columns, data){
  if(!DIM || (tableEl.id||'').indexOf('tbl-board')===0 || !data.length) return columns;
  const hasProd = data.some(r=>gfProd(r)!=null), hasSup = data.some(r=>gfHasSup(r));
  if(!hasProd && !hasSup) return columns;
  const hasInvLines = data.some(r=>Array.isArray(r.L));
  data.forEach(r=>{
    const code = gfProd(r), sp = gfSup(r);
    if(code!=null){
      const pd = DIM.prod[code];
      r._gig = pd && pd[0] ? (DIM.ig[pd[0]]||pd[0]) : '—'; r._gpc = pd && pd[1] ? (DIM.pc[pd[1]]||pd[1]) : '—';
      if(sp) r._gst = DIM.st[sp.t]; else { const t = DIM.pt[code]; r._gst = t ? t.map(x=>DIM.st[x]).join(' · ') : '—'; }
    } else {
      r._gst = sp ? DIM.st[sp.t] : '—';
      if(Array.isArray(r.L)){
        const ig={}, pc={}; r.L.forEach(l=>{ const pd=DIM.prod[String(l[0])]; if(pd){ const v=(l[2]||1)*(l[3]||1); ig[pd[0]]=(ig[pd[0]]||0)+v; pc[pd[1]]=(pc[pd[1]]||0)+v; } });
        r._gig = gfTop(ig, DIM.ig, 3)||'—'; r._gpc = gfTop(pc, DIM.pc, 3)||'—';
      } else { r._gig = sp ? gfTop(sp.ig, DIM.ig, 3) : '—'; r._gpc = sp ? gfTop(sp.pc, DIM.pc, 3) : '—'; }
    }
  });
  const sup = !hasProd;
  return columns.concat([
    {key:'_gst', label: hasSup?'Supplier type':'Supplier type (2026 buys)', searchable:false},
    {key:'_gig', label: sup?'Inventory groups supplied':'Inventory group', searchable:false},
    {key:'_gpc', label: sup?'Product categories supplied':'Product category', searchable:false}
  ]);
}
function gfRerender(){ GF.reg.forEach(fn=>{ try{ fn(); }catch(e){} }); }
(function gfInit(){
  const bar = document.getElementById('gfbar'); if(!bar || !DIM) return;
  const opts = (m)=>Object.entries(m).sort((a,b)=>String(a[1]).localeCompare(String(b[1]))).map(([k,v])=>`<option value="${esc(k)}">${esc(v)}</option>`).join('');
  bar.innerHTML = `<span class="gf-t">Filters</span>
    <label>Supplier type<select id="gf-st"><option value="">All supplier types</option>${opts(DIM.st)}</select></label>
    <label>Inventory group<select id="gf-ig"><option value="">All inventory groups</option>${opts(DIM.ig)}</select></label>
    <label>Product category<select id="gf-pc"><option value="">All product categories</option>${opts(DIM.pc)}</select></label>
    <button type="button" id="gf-reset">Reset</button>
    <span class="gf-note" id="gf-note"></span>`;
  const note = ()=>{ const n=[GF.st,GF.ig,GF.pc].filter(Boolean).length; bar.classList.toggle('on', n>0);
    document.getElementById('gf-note').textContent = n ? 'Filtering the tables on every tab (rows tied to an item or a supplier). KPI cards and charts stay company-wide.' : 'Applies to the tables on every tab: item rows by inventory group and category, supplier rows by type and what they supply (2026 purchases).'; };
  const upd = ()=>{ GF.st=document.getElementById('gf-st').value; GF.ig=document.getElementById('gf-ig').value; GF.pc=document.getElementById('gf-pc').value; note(); gfRerender(); };
  ['gf-st','gf-ig','gf-pc'].forEach(id=>document.getElementById(id).addEventListener('change', upd));
  document.getElementById('gf-reset').addEventListener('click', ()=>{ ['gf-st','gf-ig','gf-pc'].forEach(id=>document.getElementById(id).value=''); upd(); });
  note();
})();
"""
rep("function buildTable(tableEl, columns, data, opts={}){\n","function buildTable(tableEl, columns, data, opts={}){\n  const skipGF = (tableEl.id||'').indexOf('tbl-board')===0;\n  columns = gfAugment(tableEl, columns, data);\n",'bt1')
rep("let rows = data.filter(filterFn);","let rows = data.filter(filterFn).filter(r=>skipGF||gfPass(r));",'bt2')
rep("  render();\n  return {\n    setFilter(fn){ filterFn=fn; render(); }","  GF.reg.set(tableEl, render);\n  render();\n  return {\n    setFilter(fn){ filterFn=fn; render(); }",'bt3')
rep("/* ---------------- generic sortable/filterable table ---------------- */",engine+"\n/* ---------------- generic sortable/filterable table ---------------- */",'engine')
open(W,'w',encoding='utf-8').write(h); print(len(h))
