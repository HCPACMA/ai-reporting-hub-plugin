/* Cure skin v1 — AI Reporting HUB (inv) */
(function(){if(document.getElementById('cure-skin'))return;var s=document.createElement('style');s.id='cure-skin';s.textContent="/* ===== Cure skin \u2014 makes the page look like part of the Cure (EXSYS) system ===== */\n@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700;900&family=Cairo:wght@400;600;700&display=swap');\n:root{--cu-hd:58px;--cu-ft:30px}\nhtml:root:not([data-theme=\"dark\"]){\n  --cu-bg:#F2F5F9;--cu-surf:#FFFFFF;--cu-surf2:#EFF2F6;--cu-surf3:#E5EBF2;--cu-line:#DCE3EC;\n  --cu-ink:#1B2B4B;--cu-mute:#55657D;--cu-faint:#8794A8;\n  --cu-blue:#0B6FBF;--cu-blue2:#3AA0F0;--cu-soft:#E7F1FC;--cu-th:#0B6FBF;\n  --cu-orange:#F5A623;--cu-red:#D7261E;--cu-green:#1E9E5A;\n  --cu-shadow:0 1px 2px rgba(16,42,84,.05),0 4px 14px rgba(16,42,84,.07);color-scheme:light}\n@media (prefers-color-scheme:dark){html:root:not([data-theme=\"light\"]){\n  --cu-bg:#0E1626;--cu-surf:#152036;--cu-surf2:#1B2942;--cu-surf3:#22324F;--cu-line:#2A3B59;\n  --cu-ink:#E6EDF7;--cu-mute:#A3B2C9;--cu-faint:#7889A3;\n  --cu-blue:#3D8BFF;--cu-blue2:#62A8FF;--cu-soft:rgba(61,139,255,.16);--cu-th:#1D5FAF;\n  --cu-orange:#F5B24A;--cu-red:#FF6B61;--cu-green:#3ECF8E;\n  --cu-shadow:0 1px 2px rgba(0,0,0,.25),0 8px 24px rgba(0,0,0,.3);color-scheme:dark}}\nhtml:root[data-theme=\"dark\"]{\n  --cu-bg:#0E1626;--cu-surf:#152036;--cu-surf2:#1B2942;--cu-surf3:#22324F;--cu-line:#2A3B59;\n  --cu-ink:#E6EDF7;--cu-mute:#A3B2C9;--cu-faint:#7889A3;\n  --cu-blue:#3D8BFF;--cu-blue2:#62A8FF;--cu-soft:rgba(61,139,255,.16);--cu-th:#1D5FAF;\n  --cu-orange:#F5B24A;--cu-red:#FF6B61;--cu-green:#3ECF8E;\n  --cu-shadow:0 1px 2px rgba(0,0,0,.25),0 8px 24px rgba(0,0,0,.3);color-scheme:dark}\n\n/* type */\nhtml body{font-family:'Roboto','Cairo',system-ui,-apple-system,'Segoe UI',sans-serif!important;padding-top:var(--cu-hd)!important;padding-bottom:var(--cu-ft)!important;background:var(--cu-bg)}\nhtml body h1,html body h2,html body h3,html body .display{font-family:'Roboto','Cairo',system-ui,sans-serif!important;letter-spacing:-.005em}\n[dir=rtl],[lang=ar]{font-family:'Cairo','Roboto',system-ui,sans-serif}\n\n/* tables: Cure blue header bar, white bold titles */\nhtml body thead th{background:var(--cu-th)!important;color:#fff!important;font-weight:600!important;text-transform:none!important;letter-spacing:.01em!important;border-bottom:0!important;border-inline-end:1px solid rgba(255,255,255,.16);padding-inline:10px!important}\nhtml body thead th :not(input):not(select):not(option):not(textarea){color:inherit!important}\nhtml body thead th svg{stroke:#fff}\nhtml body thead tr:first-child th:first-child{border-start-start-radius:6px}\nhtml body thead tr:first-child th:last-child{border-start-end-radius:6px;border-inline-end:0}\nhtml body tbody tr:hover>td{background-color:var(--cu-soft)}\n\n/* controls */\nhtml body input[type=search],html body input[type=text],html body input[type=number],html body input[type=date],html body input[type=month],html body select{border-radius:6px}\nhtml body input:focus-visible,html body select:focus-visible{outline:2px solid var(--cu-blue2)!important;outline-offset:1px}\nhtml body .btn.pri,html body .btn-primary,html body button.primary{background:linear-gradient(90deg,var(--cu-blue),var(--cu-blue2))!important;border-color:transparent!important;color:#fff!important}\ninput[type=range],input[type=checkbox],input[type=radio]{accent-color:var(--cu-blue)}\n\n/* ===== Cure header ===== */\n#cure-hd{position:fixed;top:0;left:0;right:0;height:var(--cu-hd);z-index:60;display:flex;align-items:center;gap:18px;padding:0 22px;\n  background:var(--cu-surf);border-bottom:1px solid var(--cu-line);box-shadow:0 1px 6px rgba(16,42,84,.05);direction:ltr;\n  font:400 13.5px 'Roboto','Cairo',system-ui,sans-serif;color:var(--cu-ink)}\n#cure-hd .cu-logo{display:flex;align-items:center;gap:9px;flex:none;cursor:pointer;text-decoration:none}\n#cure-hd .cu-mark{position:relative;width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,var(--cu-blue),var(--cu-blue2));flex:none}\n#cure-hd .cu-mark::before,#cure-hd .cu-mark::after{content:\"\";position:absolute;background:#fff;border-radius:2px;left:50%;top:50%;transform:translate(-50%,-50%)}\n#cure-hd .cu-mark::before{width:16px;height:5px}#cure-hd .cu-mark::after{width:5px;height:16px}\n#cure-hd .cu-mark i{position:absolute;right:-3px;top:-3px;width:10px;height:10px;border-radius:50%;background:var(--cu-orange);border:2px solid var(--cu-surf)}\n#cure-hd .cu-name b{display:block;font:900 20px/1 'Roboto',sans-serif;color:var(--cu-blue);letter-spacing:-.03em}\n#cure-hd .cu-name small{display:block;font-size:10.5px;color:var(--cu-mute);margin-top:2px;letter-spacing:.02em}\n#cure-hd .cu-bc{flex-direction:row;margin:0;flex:1;min-width:0;display:flex;align-items:center;gap:8px;white-space:nowrap;overflow:hidden;padding-inline-start:16px;border-inline-start:1px solid var(--cu-line)}\n#cure-hd .cu-bc svg{width:17px;height:17px;flex:none;stroke:var(--cu-blue);fill:none;stroke-width:2}\n#cure-hd .cu-bc .s{color:var(--cu-faint)}\n#cure-hd .cu-bc .r{font-weight:700;color:var(--cu-ink)}\n#cure-hd .cu-bc .l{color:var(--cu-blue);overflow:hidden;text-overflow:ellipsis}\n#cure-hd .cu-bc .l[dir=rtl]{font-family:'Cairo','Roboto',sans-serif}\n#cure-hd .cu-search{position:relative;width:clamp(180px,24vw,400px);flex:none}\n#cure-hd .cu-search input{width:100%;height:36px;border:1px solid var(--cu-line);border-radius:20px;background:var(--cu-surf);color:var(--cu-ink);padding:0 38px 0 16px;font:inherit;box-shadow:0 2px 8px rgba(16,42,84,.05);outline:none}\n#cure-hd .cu-search input:focus{border-color:var(--cu-blue2);box-shadow:0 0 0 3px var(--cu-soft)}\n#cure-hd .cu-search svg{position:absolute;right:13px;top:50%;transform:translateY(-50%);width:16px;height:16px;stroke:var(--cu-blue);fill:none;stroke-width:2.2;pointer-events:none}\n#cure-hd .cu-res{display:none;position:absolute;top:42px;left:0;right:0;background:var(--cu-surf);border:1px solid var(--cu-line);border-radius:10px;box-shadow:var(--cu-shadow);max-height:60vh;overflow:auto;padding:6px}\n#cure-hd .cu-res.on{display:block}\n#cure-hd .cu-res button{display:flex;flex-direction:column;align-items:flex-start;width:100%;border:0;background:none;text-align:start;padding:7px 10px;border-radius:7px;cursor:pointer;color:var(--cu-ink);font:500 13px 'Roboto','Cairo',sans-serif}\n#cure-hd .cu-res button small{color:var(--cu-faint);font-size:11px;font-weight:400}\n#cure-hd .cu-res button:hover,#cure-hd .cu-res button.k{background:var(--cu-soft);color:var(--cu-blue)}\n#cure-hd .cu-res .nil{padding:10px;color:var(--cu-faint);font-size:12.5px}\n#cure-hd .cu-tools{display:flex;align-items:center;gap:12px;flex:none}\n#cure-hd .cu-ico{width:34px;height:34px;display:grid;place-items:center;border-radius:50%;border:0;background:none;cursor:pointer;color:var(--cu-blue)}\n#cure-hd .cu-ico:hover{background:var(--cu-soft)}\n#cure-hd .cu-ico svg{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}\n#cure-hd .cu-pill{display:flex;align-items:center;gap:8px;border:1px solid var(--cu-line);border-radius:20px;padding:3px 12px 3px 4px;font-size:12.5px;color:var(--cu-mute)}\n#cure-hd .cu-av{width:28px;height:28px;border-radius:50%;background:var(--cu-soft);color:var(--cu-blue);display:grid;place-items:center;font:700 11.5px 'Roboto',sans-serif}\n#cure-hd .cu-pill b{color:var(--cu-ink);font-weight:500;font-family:'Cairo','Roboto',sans-serif}\n\n/* ===== Cure footer ===== */\n#cure-ft{position:fixed;left:0;right:0;bottom:0;height:var(--cu-ft);z-index:60;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:0 22px;\n  background:var(--cu-surf);border-top:1px solid var(--cu-line);direction:ltr;font:400 12px 'Roboto','Cairo',sans-serif;color:var(--cu-mute)}\n#cure-ft .cu-org{color:var(--cu-blue);font-family:'Cairo','Roboto',sans-serif;font-weight:600;direction:rtl;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}\n#cure-ft .cu-mod b{color:var(--cu-ink);font-weight:500}\n#cure-ft .cu-tag{color:var(--cu-red);font-weight:700}\n\n@media (max-width:900px){\n  #cure-hd{gap:10px;padding:0 12px}\n  #cure-hd .cu-bc,#cure-hd .cu-pill b,#cure-hd .cu-name small{display:none}\n  #cure-hd .cu-search{flex:1;width:auto}\n  #cure-ft .cu-mod{display:none}\n}\n@media print{#cure-hd,#cure-ft{display:none!important}html body{padding:0!important}}\n\n/* --- Inventory Audit mapping --- */\nhtml:root[data-theme],html:root:not([data-theme]){\n  --bg:var(--cu-bg);--surface:var(--cu-surf);--surface-2:var(--cu-surf2);--border:var(--cu-line);\n  --ink:var(--cu-ink);--ink-2:var(--cu-mute);--ink-mute:var(--cu-faint);\n  --accent:var(--cu-blue);--accent-ink:#fff;--accent-soft:var(--cu-soft);--red:var(--cu-red);--shadow:var(--cu-shadow)}\n.topbar{top:var(--cu-hd)!important}\n.gfbar{top:calc(var(--cu-hd) + 70px)!important}\n.topbar .brand .name{color:var(--cu-blue)}\n.sidebar{top:calc(var(--cu-hd) + 78px)!important;max-height:calc(100vh - 96px - var(--cu-hd) - var(--cu-ft))!important}\n.sidebar-label{color:var(--cu-blue)!important}\n.tab-btn{border:1px solid var(--cu-line)!important;background:var(--cu-surf)!important;border-radius:10px!important;color:var(--cu-ink)!important;font-weight:500!important;box-shadow:0 1px 2px rgba(16,42,84,.04)}\n.tab-btn:hover{border-color:var(--cu-blue2)!important;background:var(--cu-soft)!important}\n.tab-btn[aria-selected=\"true\"]{background:var(--cu-blue)!important;border-color:var(--cu-blue)!important;color:#fff!important;font-weight:600!important;box-shadow:0 3px 10px rgba(11,111,191,.25)}\n.tab-btn[aria-selected=\"true\"] .n{color:#fff!important;opacity:.85}\n.tab-btn.risk{color:var(--cu-red)!important}\n.tab-btn.risk[aria-selected=\"true\"]{background:var(--cu-red)!important;border-color:var(--cu-red)!important;color:#fff!important}\n.kpi{border-radius:10px!important}\n@media (max-width:900px){.sidebar{top:calc(var(--cu-hd) + 66px)!important;max-height:none!important}}\n";document.body.appendChild(s);})();
window.CURE_CFG={module:"Inventory Analysis & Audit",tag:"Inventory",items:".tab-btn",active:".tab-btn[aria-selected=\"true\"]",scroller:"",group:function(el){if(!el)return '';return (function(el,cls){for(var p=el;p;p=p.previousElementSibling){if(p!==el&&p.classList&&p.classList.contains(cls))return (p.textContent||'').replace(/\s+/g,' ').trim()}if(el.parentElement&&el.parentElement.id!=='nav'&&el.parentElement.previousElementSibling){var q=el.parentElement.previousElementSibling;if(q.classList.contains(cls))return (q.textContent||'').replace(/\s+/g,' ').trim()}return ''})(el,'sidebar-label')}};
(function(){
  if(window.__cureSkin) return; window.__cureSkin=1;
  var C=window.CURE_CFG||{};
  var $=function(s,r){return (r||document).querySelector(s)}, $$=function(s,r){return Array.prototype.slice.call((r||document).querySelectorAll(s))};
  function label(el){
    if(!el) return '';
    var c=el.cloneNode(true);
    $$('.n,.nv-badge,svg,.cv,.ic',c).forEach(function(x){x.remove()});
    var b=c.querySelector('.bi>span, .lb .bi>span, .lb');
    var t=(b?b.textContent:c.textContent)||'';
    return t.replace(/\s+/g,' ').trim();
  }
  function group(el){ try{ return C.group?C.group(el):''; }catch(e){ return ''; } }
  function esc(s){return String(s).replace(/[&<>"]/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]})}
  var isAr=function(s){return /[؀-ۿ]/.test(s)};
  var ic={
    home:'<svg viewBox="0 0 24 24"><path d="M3 11l9-7 9 7"/><path d="M5 10v10h5v-6h4v6h5V10"/></svg>',
    search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
    bell:'<svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 1112 0c0 7 3 8 3 8H3s3-1 3-8"/><path d="M10 20a2 2 0 004 0"/></svg>',
    print:'<svg viewBox="0 0 24 24"><path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/></svg>',
    top:'<svg viewBox="0 0 24 24"><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></svg>'
  };
  var d=new Date(), ds=('0'+d.getDate()).slice(-2)+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+d.getFullYear();
  var hd=document.createElement('header'); hd.id='cure-hd';
  hd.innerHTML='<a class="cu-logo" title="Home"><span class="cu-mark"><i></i></span><span class="cu-name"><b>Al Faihaa</b><small>Medical Center</small></span></a>'+
    '<div class="cu-bc" role="navigation" aria-label="Breadcrumb">'+ic.home+'<span class="r">Administrative</span><span class="s">&rsaquo;</span><span class="l">'+esc(C.module||'')+'</span>'+
    '<span class="s g">&rsaquo;</span><span class="l g" id="cu-grp"></span><span class="s c">&rsaquo;</span><span class="l c" id="cu-cur"></span></div>'+
    '<div class="cu-search"><input type="search" placeholder="Search here" aria-label="Search screens" autocomplete="off">'+ic.search+'<div class="cu-res" role="listbox"></div></div>'+
    '<div class="cu-tools"><button class="cu-ico" data-a="top" title="Back to top">'+ic.top+'</button><button class="cu-ico" data-a="print" title="Print">'+ic.print+'</button>'+
    '<span class="cu-pill"><span class="cu-av">HG</span><b>هاني جميل</b><span>'+ds+'</span></span></div>';
  var ft=document.createElement('footer'); ft.id='cure-ft';
  ft.innerHTML='<span class="cu-org">مجمع الفيحاء الطبي - الرياض (مجموعة الفيحاء للخدمات الطبية) هاني جميل</span>'+
    '<span class="cu-mod">AI Reporting HUB &middot; <b>'+esc(C.module||'')+'</b></span><span class="cu-tag">'+esc(C.tag||'Cure Integrated')+'</span>';
  document.body.insertBefore(hd,document.body.firstChild); document.body.appendChild(ft);

  function setL(id,t){var e=document.getElementById(id); e.textContent=t; e.dir=isAr(t)?'rtl':'ltr'; $$(id==='cu-grp'?'.cu-bc .g':'.cu-bc .c',hd).forEach(function(x){x.style.display=t?'':'none'});}
  function sync(){
    var a=$(C.active||'.x-none'); var g=group(a), t=label(a);
    if(g===t) g='';
    setL('cu-grp',g); setL('cu-cur',t);
  }
  document.addEventListener('click',function(){setTimeout(sync,80)},true);
  setTimeout(sync,300); setTimeout(sync,1500); setInterval(sync,4000);

  /* search screens */
  var inp=$('.cu-search input',hd), res=$('.cu-res',hd), hits=[], k=0;
  function draw(){
    res.innerHTML = hits.length ? hits.map(function(h,i){return '<button type="button" data-i="'+i+'" class="'+(i===k?'k':'')+'">'+esc(h.t)+(h.g?'<small>'+esc(h.g)+'</small>':'')+'</button>'}).join('') : '<div class="nil">No match</div>';
  }
  function find(){
    var q=inp.value.trim().toLowerCase(); if(!q){res.classList.remove('on');return}
    var seen={}; hits=[];
    $$(C.items||'.x-none').forEach(function(el){
      var full=(el.textContent||'').replace(/\s+/g,' ').toLowerCase(), t=label(el);
      if(t && full.indexOf(q)>-1 && !seen[t+group(el)]){seen[t+group(el)]=1;hits.push({el:el,t:t,g:group(el)})}
    });
    hits=hits.slice(0,12); k=0; draw(); res.classList.add('on');
  }
  function go(h){ if(!h) return; var gEl=h.el.closest&&h.el.closest('.nv-g'); if(gEl&&!gEl.classList.contains('open')){var gh=gEl.querySelector('.nv-h'); if(gh&&!gEl.classList.contains('flat')) gh.click();}
    h.el.click(); inp.value=''; res.classList.remove('on'); setTimeout(sync,80); }
  inp.addEventListener('input',find);
  inp.addEventListener('keydown',function(e){
    if(e.key==='ArrowDown'){k=Math.min(k+1,hits.length-1);draw();e.preventDefault()}
    else if(e.key==='ArrowUp'){k=Math.max(k-1,0);draw();e.preventDefault()}
    else if(e.key==='Enter'){go(hits[k]);e.preventDefault()}
    else if(e.key==='Escape'){res.classList.remove('on');inp.blur()}
  });
  res.addEventListener('mousedown',function(e){var b=e.target.closest('button'); if(b){e.preventDefault(); go(hits[+b.dataset.i]);}});
  inp.addEventListener('blur',function(){setTimeout(function(){res.classList.remove('on')},150)});
  document.addEventListener('keydown',function(e){ if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();inp.focus();} });

  $('.cu-logo',hd).addEventListener('click',function(){var f=$(C.items||'.x-none'); if(f) f.click(); setTimeout(sync,80);});
  hd.addEventListener('click',function(e){var b=e.target.closest('.cu-ico'); if(!b) return;
    if(b.dataset.a==='print') window.print();
    if(b.dataset.a==='top'){ var s=C.scroller&&$(C.scroller); (s||window).scrollTo({top:0,behavior:'smooth'}); }
  });

  /* recolour chart marks drawn with the old teal accent */
  var MAP={'#146356':'#0B6FBF','#0f766e':'#0B6FBF','#0f6e5c':'#0B6FBF','#4fd1b3':'#3D8BFF','#2dd4bf':'#3D8BFF','#39b596':'#3D8BFF'};
  var keys=Object.keys(MAP), sel=[];
  keys.forEach(function(h){[h,h.toUpperCase()].forEach(function(v){sel.push('[fill="'+v+'"]','[stroke="'+v+'"]','[stop-color="'+v+'"]')})});
  sel=sel.join(',');
  function recolor(){ $$(sel).forEach(function(el){['fill','stroke','stop-color'].forEach(function(a){var v=el.getAttribute(a); if(v&&MAP[v.toLowerCase()]) el.setAttribute(a,MAP[v.toLowerCase()]);});}); }
  var tm=0; new MutationObserver(function(){clearTimeout(tm);tm=setTimeout(recolor,250)}).observe(document.body,{childList:true,subtree:true});
  recolor();
})();

