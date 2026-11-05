
  /* ------------------------------ small chart helpers (inline SVG, theme tokens) ------------------------------ */
  const svgN = (w,h,inner) => `<svg viewBox="0 0 ${w} ${h}" width="100%" role="img" style="display:block;max-width:${w}px;overflow:visible" xmlns="http://www.w3.org/2000/svg">${inner}</svg>`;
  const tx = (x,y,s,o={}) => `<text x="${x}" y="${y}" fill="${o.fill||'var(--ink-muted)'}" font-size="${o.size||11}" text-anchor="${o.anchor||'start'}" ${o.w?`font-weight="${o.w}"`:''} font-family="IBM Plex Sans,sans-serif">${s}</text>`;
  function legend(items){ return `<div class="bd-leg">${items.map(i=>`<span><i style="background:${i[1]}"></i>${i[0]}</span>`).join('')}</div>`; }
  /* diverging / plain horizontal bars: items [{label, v, color, text}] */
  function hbars(items, o={}){
    const W = 640, lw = o.lw||150, rw = 86, rowH = 26, h = items.length*rowH + 6;
    const mx = Math.max(...items.map(i=>Math.abs(i.v)), 1e-9), neg = items.some(i=>i.v<0);
    const nm = neg ? 78 : 0, x0 = neg ? lw + nm + (W-lw-rw-nm)/2 : lw, scale = neg ? (W-lw-rw-nm)/2/mx : (W-lw-rw)/mx;
    let g = '';
    if(neg) g += `<line x1="${x0}" x2="${x0}" y1="0" y2="${h}" stroke="var(--border)"/>`;
    items.forEach((it,k) => {
      const y = k*rowH + 4, bw = Math.abs(it.v)*scale, x = it.v<0 ? x0-bw : x0;
      g += tx(lw-8, y+14, it.label, {anchor:'end', fill:'var(--ink)'});
      g += `<rect x="${x}" y="${y+3}" width="${Math.max(bw,1)}" height="14" rx="3" fill="${it.color||'var(--accent)'}"/>`;
      g += tx(it.v<0 ? x-5 : x+bw+5, y+14, it.text, {anchor: it.v<0?'end':'start', fill:'var(--ink)'});
    });
    return svgN(W,h,g);
  }
  /* 100% stacked horizontal bars: rows [{label, parts:[{v,color}] }] */
  function stack100(rows){
    const W = 640, lw = 150, rowH = 30, h = rows.length*rowH+6; let g = '';
    rows.forEach((r,k) => {
      const tot = r.parts.reduce((s,p)=>s+p.v,0)||1; let x = lw; const y = k*rowH+4;
      g += tx(lw-8,y+15,r.label,{anchor:'end',fill:'var(--ink)'});
      r.parts.forEach(p => { const w = (W-lw-10)*p.v/tot; g += `<rect x="${x}" y="${y+2}" width="${Math.max(w-2,0)}" height="18" rx="3" fill="${p.color}"/>`;
        if(w>46) g += tx(x+w/2-1,y+15,fp(p.v/tot,0),{anchor:'middle',fill:'#fff',size:10.5,w:600}); x += w; });
    });
    return svgN(W,h,g);
  }
  /* multi-line chart: series [{name,color,vals[]}], labels[] */
  function lines(series, labels, o={}){
    const W = 640, H = 220, L = 46, R = 12, Tp = 10, B = 28;
    const all = series.flatMap(s=>s.vals).filter(v=>v!==null&&isFinite(v)); if(!all.length) return '';
    let lo = Math.min(...all, 0), hi = Math.max(...all); if(hi===lo){hi=lo+1;}
    const pad = (hi-lo)*.08; hi += pad; if(lo<0) lo -= pad;
    const X = i => L + (W-L-R)*(labels.length<2?0:i/(labels.length-1)), Y = v => Tp + (H-Tp-B)*(1-(v-lo)/(hi-lo));
    let g = '';
    for(let k=0;k<=4;k++){ const v = lo+(hi-lo)*k/4, y = Y(v); g += `<line x1="${L}" x2="${W-R}" y1="${y}" y2="${y}" stroke="var(--border)" stroke-dasharray="2 4"/>` + tx(L-6,y+4,(o.pct?fp(v,0):fM(v)),{anchor:'end',size:10}); }
    const step = Math.ceil(labels.length/8); labels.forEach((l,i) => { if(i%step===0 || i===labels.length-1) g += tx(X(i),H-8,l,{anchor:'middle',size:10}); });
    series.forEach(s => { let d=''; s.vals.forEach((v,i)=>{ if(v===null||!isFinite(v)) return; d += (d?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1); });
      g += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.w||2}" stroke-linejoin="round" stroke-linecap="round" ${s.dash?'stroke-dasharray="5 4"':''}/>`;
      const li = s.vals.length-1; if(s.vals[li]!==null) g += `<circle cx="${X(li)}" cy="${Y(s.vals[li])}" r="3.5" fill="${s.color}" stroke="var(--surface)" stroke-width="2"/>`; });
    return svgN(W,H,g);
  }
  /* waterfall: items [{label,v,total:bool}] */
  function waterfall(items){
    const W = 640, H = 250, L = 8, B = 46, Tp = 22, bw = Math.min(64, (W-L*2)/items.length-16);
    let run = 0; const bars = items.map(it => { const s = it.total ? 0 : run; const e = it.total ? it.v : run+it.v; if(!it.total) run = e; else run = it.v; return {...it,s,e}; });
    const vals = bars.flatMap(b=>[b.s,b.e,0]); const lo = Math.min(...vals), hi = Math.max(...vals), rg = (hi-lo)||1;
    const Y = v => Tp + (H-Tp-B)*(1-(v-lo)/rg); let g = `<line x1="${L}" x2="${W-L}" y1="${Y(0)}" y2="${Y(0)}" stroke="var(--border)"/>`;
    bars.forEach((b,i) => { const cx = L + (W-2*L)*(i+.5)/bars.length, y1 = Y(Math.max(b.s,b.e)), y2 = Y(Math.min(b.s,b.e));
      const col = b.total ? 'var(--ink-muted)' : (b.v>=0 ? 'var(--good)' : 'var(--critical)');
      g += `<rect x="${cx-bw/2}" y="${y1}" width="${bw}" height="${Math.max(y2-y1,1.5)}" rx="3" fill="${col}"/>`;
      g += tx(cx,(b.v>=0||b.total)?y1-5:y2+13,(b.total?'':(b.v>=0?'+':''))+fM(b.v),{anchor:'middle',fill:'var(--ink)',size:10.5,w:600});
      g += tx(cx,H-24,b.label,{anchor:'middle',size:10.5}) + (b.label2? tx(cx,H-11,b.label2,{anchor:'middle',size:10}) : ''); });
    return svgN(W,H,g);
  }
  const heat = (v,mx,good=true) => { if(v===null||!isFinite(v)||!mx) return ''; const a = Math.min(Math.abs(v)/mx,1)*.32; const c = (v>=0)===good ? '30,138,95' : '179,38,30'; return `style="background:rgba(${c},${a.toFixed(3)})"`; };

  /* ------------------------------ frame: head, toolbar, tabs, body ------------------------------ */
  const root = el('div','bd'); sec.insertBefore(root, document.getElementById('bd-pane-dept'));
  const head = el('div','section-head'); root.appendChild(head);
  const bar = el('div','ti-bar bd-bar'); root.appendChild(bar);
  const tabs = el('div','bd-tabs'); root.appendChild(tabs);
  const body = el('div','bd-body'); root.appendChild(body);
  const dpane = document.getElementById('bd-pane-dept'); root.appendChild(dpane); dpane.style.display = 'none';
  const TABS = [['is','Income Statement','قائمة الدخل'],['impact','Impact on the Group','التأثير على المجموعة'],['score','Branch Scorecard','تقييم الفروع'],
                ['cc','Cash vs Credit','النقدي والآجل'],['drv','Cash & Profit Drivers','محركات الكاش والربحية'],['wi','What-If','ماذا لو'],['dept','Departments','الأقسام']];

  function drawHead(){
    head.innerHTML = `<div class="eyebrow">${ti('Departments','الأقسام')}</div>
      <h2>${t('Branches & Departments','الفروع والأقسام')}</h2>
      <p>${ST.lang==='ar' ? 'قائمة الدخل لكل فرع من دفتر الأستاذ (مراكز التكلفة في قواعد EXSYS الأربع)، مع تحليل رأسي وأفقي، وتأثير كل بند على أداء المجموعة، وتقييم الفروع، والنقدي مقابل الآجل، ومحركات الكاش والربحية.'
        : 'Branch income statements from the ledger (cost centres in the four EXSYS databases), with vertical and horizontal analysis, each line’s impact on the Group, branch scoring, cash vs credit revenue, and the drivers of cash and profit.'}${ST.lang==='both'?`<span class="bd-ar" dir="rtl">قائمة الدخل لكل فرع من دفتر الأستاذ (مراكز التكلفة في قواعد EXSYS الأربع)، مع تحليل رأسي وأفقي، وتأثير كل بند على أداء المجموعة، وتقييم الفروع، والنقدي مقابل الآجل، ومحركات الكاش والربحية.</span>`:''}</p>`;
    head.querySelector('p').style.maxWidth = '860px';
  }
  function drawTabs(){
    tabs.innerHTML = TABS.map(x => `<button data-t="${x[0]}" class="${ST.tab===x[0]?'on':''}">${ti(x[1],x[2])}</button>`).join('');
    tabs.querySelectorAll('button').forEach(b => b.onclick = () => { ST.tab = b.dataset.t; drawTabs(); render(); });
  }
  function drawBar(){
    bar.innerHTML = `
      <div class="ti-grp"><span class="ti-lab">${ti('Language','اللغة')}</span>
        <div class="ti-seg" id="bd-lang"><button data-l="en" class="${ST.lang==='en'?'on':''}">EN</button><button data-l="both" class="${ST.lang==='both'?'on':''}">EN · عربي</button><button data-l="ar" class="${ST.lang==='ar'?'on':''}">عربي</button></div></div>
      <label class="ti-chk"><input type="checkbox" id="bd-alloc" ${ST.alloc?'checked':''}> ${ti('Allocate head-office costs to branches (by revenue share)','توزيع تكاليف الإدارة العامة على الفروع (بنسبة الإيراد)')}</label>
      <div class="ti-read" id="bd-read"></div>`;
    bar.querySelector('#bd-lang').querySelectorAll('button').forEach(b => b.onclick = () => { ST.lang = b.dataset.l; drawAll(); });
    bar.querySelector('#bd-alloc').onchange = e => { ST.alloc = e.target.checked; render(); };
  }
  function readout(){
    const w = W(), lab = winLabel(w.a,w.b), pw = ST.cmp ? winPrev(w) : null;
    bar.querySelector('#bd-read').innerHTML = `${ti('Filters above (Grain · Period · Branch) drive every tab','المرشحات أعلاه (الدورية · الفترة · الفرع) تتحكم في كل التبويبات')}<br>` +
      `${ST.lang==='ar'?lab[1]:lab[0]} · ${months(w)} ${ST.lang==='ar'?'شهر':'mo'}` + (pw ? ` ${ti('vs','مقابل')} ${ST.lang==='ar'?winLabel(pw.a,pw.b)[1]:winLabel(pw.a,pw.b)[0]}` : ` · <span class="bd-fl">${ti('no comparison period','لا توجد فترة مقارنة')}</span>`) + (w.b > LASTC ? ` · <span class="bd-fl">${ti('open month included','يشمل الشهر المفتوح')}</span>` : '');
  }
  function syncTI(){ ST.grain = TI.grain; ST.a = TI.a; ST.b = TI.b; ST.cc = TI.cc; ST.cmp = TI.cmp; }
  function drawAll(){
    root.dir = ST.lang==='ar' ? 'rtl' : 'ltr'; root.classList.toggle('bd-rtl', ST.lang==='ar');
    drawHead(); drawBar(); drawTabs(); render();
  }
