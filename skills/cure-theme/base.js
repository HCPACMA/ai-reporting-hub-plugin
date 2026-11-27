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
