
/* ======================================================================
   ANOMALY DETECTION  ·  invoices (daily revenue, doctors, cashiers,
   exception lines) and expenses (GL account by account red-flag tests)
   ====================================================================== */
const ANM = {
  BR: ['01','02','03','04'],
  brName: cc => ({'01':'Riyadh','02':'Bur-1','03':'Bur-2','04':'Rafha'})[cc] || cc,
  wd: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
  mean: a => a.length ? a.reduce((s,x)=>s+x,0)/a.length : 0,
  sdp: a => { if(a.length < 2) return 0; const m = ANM.mean(a); return Math.sqrt(a.reduce((s,x)=>s+(x-m)*(x-m),0)/a.length); },
  ccFromTI: () => (TI.cc && ['01','02','03','04'].includes(TI.cc)) ? TI.cc : 'ALL',
  bar(id, label, opts, val){ return `<div class="f"><label for="${id}">${label}</label><select id="${id}">${opts.map(([v,t])=>`<option value="${esc(v)}"${String(v)===String(val)?' selected':''}>${esc(t)}</option>`).join('')}</select></div>`; },
  chk(id, label, on){ return `<label class="chk" for="${id}"><input type="checkbox" id="${id}"${on?' checked':''}> ${label}</label>`; },
};

/* ---------------------------------------------------------------- A ---- */
/* Invoice anomalies                                                        */
(function(){
  const sec = document.getElementById('sec-aud-anom-inv'); if(!sec || !DATA.anom) return;
  const A = DATA.anom, D0 = new Date(A.d0 + 'T00:00:00Z'), ND = A.nd;
  const dayDate = i => new Date(D0.getTime() + i*86400000);
  const dayISO = i => dayDate(i).toISOString().slice(0,10);
  const dayYM = i => { const d = dayDate(i); return d.getUTCFullYear()*100 + d.getUTCMonth()+1; };
  const dayY = i => dayDate(i).getUTCFullYear();
  const dayW = i => dayDate(i).getUTCDay();
  const SPECS = [...new Set(Object.keys(A.daily).map(k => k.split('|')[2]))].sort();

  audHead(sec, 'Accounting Audit · Anomaly Detection', 'Invoice Anomalies', 'كشف الشذوذ في الفواتير',
    'Daily invoice revenue tested against its own year-to-date behaviour — a day outside the mean ± 2σ band is an anomaly, a standard year-to-date control-band test. Below it the same idea applied to doctors, cashiers and individual invoice lines: heavy cash discounts, returns, after-hours billing, prices far off the usual tariff and the same service billed twice to one patient on one day.');
  const st = {cc: ANM.ccFromTI(), pt: 'ALL', spec: 'ALL', noPh: true, noFri: true, k: 2, base: 'ytd', exc: 'HD', q: '', hidePh: true};
  const barBox = el('div','aud-bar'); sec.appendChild(barBox);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const cChart = el('div','card'); cChart.style.marginTop = '16px'; sec.appendChild(cChart);
  const row = el('div','grid grid-2'); row.style.marginTop = '16px'; row.style.alignItems = 'start'; sec.appendChild(row);
  const cDays = el('div','card'), cDoc = el('div','card'); row.appendChild(cDays); row.appendChild(cDoc);
  const cCash = el('div','card'); cCash.style.marginTop = '16px'; sec.appendChild(cCash);
  const cExc = el('div','card'); cExc.style.marginTop = '16px'; sec.appendChild(cExc);
  sec.appendChild(el('div','note', `<b>Source.</b> NextGen V1.1 model, <code>[Total Revenue]</code> = Σ NET_AMT over the 12 invoice tables, sliced by <code>Branches</code>, <code>P_TYPE</code> and <code>DOCTORS</code>, Jan 2024 – 21 Sep 2026. The NextGen Anomaly page excludes the Pharmacy service specialty and Fridays; both switches above reproduce that and are on by default. Band = average ± kσ of the daily totals from 1 January to that day (<code>DATESYTD</code>, population σ, blank days ignored), so the first days of each year have a narrow band. Exception lines come from the same tables at line level (tests described on each tab). Patient names are left out — use the file number in the HIS.`));

  function drawBar(){
    barBox.innerHTML = ANM.bar('ai-cc','Branch',[['ALL','All branches'],...ANM.BR.map(c=>[c,ANM.brName(c)])],st.cc)
      + ANM.bar('ai-pt','Payment type',[['ALL','Cash + Credit'],['Cash','Cash'],['Credit','Credit']],st.pt)
      + ANM.bar('ai-spec','Doctor speciality',[['ALL','All specialities'],...SPECS.map(s=>[s,s])],st.spec)
      + ANM.bar('ai-k','Sensitivity',[[2,'± 2σ (NextGen)'],[2.5,'± 2.5σ'],[3,'± 3σ']],st.k)
      + ANM.bar('ai-base','Baseline',[['ytd','Year to date (NextGen)'],['r90','Rolling 90 days']],st.base)
      + ANM.chk('ai-ph','Exclude pharmacy',st.noPh) + ANM.chk('ai-fri','Exclude Fridays',st.noFri);
    const on = (id, fn) => barBox.querySelector('#'+id).onchange = e => { fn(e.target); render(); };
    on('ai-cc', t => st.cc = t.value); on('ai-pt', t => st.pt = t.value); on('ai-spec', t => st.spec = t.value);
    on('ai-k', t => st.k = +t.value); on('ai-base', t => st.base = t.value);
    on('ai-ph', t => st.noPh = t.checked); on('ai-fri', t => st.noFri = t.checked);
  }
  function keyOK(k){ const [cc,pt,sp] = k.split('|'); return (st.cc==='ALL'||cc===st.cc) && (st.pt==='ALL'||pt===st.pt) && (st.spec==='ALL'||sp===st.spec); }
  function series(){
    const src = st.noPh && A.dailyNP ? A.dailyNP : A.daily, s = new Float64Array(ND);
    for(const k in src){ if(!keyOK(k)) continue; const v = src[k]; for(let i=0;i<ND;i++) s[i] += v[i]; }
    return s;
  }
  // flag each day with the NextGen rule (YTD expanding window) or a rolling 90-day window
  function flags(s){
    const out = []; let yr = -1, n = 0, sum = 0, sq = 0; const win = [];
    for(let i=0;i<ND;i++){
      const skip = st.noFri && dayW(i) === 5, v = s[i];
      if(st.base === 'ytd'){
        if(dayY(i) !== yr){ yr = dayY(i); n = 0; sum = 0; sq = 0; }
        if(!skip && v){ n++; sum += v; sq += v*v; }
        if(skip || !v){ out.push(null); continue; }
        const m = sum/n, sd = Math.sqrt(Math.max(0, sq/n - m*m));
        out.push({m, sd, z: sd ? (v-m)/sd : 0, hi: v > m + st.k*sd, lo: v < m - st.k*sd});
      } else {
        if(skip || !v){ out.push(null); continue; }
        win.push(v); if(win.length > 90) win.shift();
        const m = ANM.mean(win), sd = ANM.sdp(win);
        out.push({m, sd, z: sd ? (v-m)/sd : 0, hi: v > m + st.k*sd, lo: v < m - st.k*sd});
      }
    }
    return out;
  }
  function win(){ const w = audWindow(); const a = w.a, b = w.b; let i0 = ND, i1 = -1; for(let i=0;i<ND;i++){ const ym = dayYM(i); if(ym >= a && ym <= b){ if(i<i0) i0=i; i1=i; } } return {i0, i1, w}; }

  function chart(s, fl, i0, i1){
    const W = 1100, H = 300, L = 58, R = 14, T = 16, B = 34;
    const idx = []; for(let i=i0;i<=i1;i++) if(!(st.noFri && dayW(i)===5)) idx.push(i);
    if(!idx.length) return '<p class="card-sub">No days in this period.</p>';
    let mx = 0; for(const i of idx){ mx = Math.max(mx, s[i], fl[i] ? fl[i].m + st.k*fl[i].sd : 0); }
    mx = mx*1.08 || 1;
    const step = Math.pow(10, Math.floor(Math.log10(mx/4))); const tick = [1,2,2.5,5,10].map(x=>x*step).find(t => mx/t <= 5) || step*10;
    const X = j => L + (W-L-R) * (idx.length === 1 ? 0.5 : j/(idx.length-1)), Y = v => T + (H-T-B) * (1 - v/mx);
    let g = '';
    for(let t=0; t<=mx; t+=tick) g += `<line x1="${L}" x2="${W-R}" y1="${Y(t)}" y2="${Y(t)}" class="an-grid"/><text x="${L-6}" y="${Y(t)+4}" class="an-ax" text-anchor="end">${t>=1000? (t/1000).toLocaleString('en-US')+'k' : t}</text>`;
    // band
    let up = '', dn = '';
    idx.forEach((i,j) => { const f = fl[i]; if(!f) return; up += `${X(j)},${Y(f.m + st.k*f.sd)} `; dn = `${X(j)},${Y(Math.max(0,f.m - st.k*f.sd))} ` + dn; });
    const band = up ? `<polygon points="${up}${dn}" class="an-band"/>` : '';
    let mline = ''; idx.forEach((i,j) => { const f = fl[i]; if(f) mline += `${X(j)},${Y(f.m)} `; });
    let line = ''; idx.forEach((i,j) => { line += `${j?'L':'M'}${X(j).toFixed(1)},${Y(s[i]).toFixed(1)}`; });
    let pts = '';
    idx.forEach((i,j) => { const f = fl[i]; if(!f || !(f.hi || f.lo)) return; const x = X(j), y = Y(s[i]);
      pts += f.hi ? `<path d="M${x-5},${y-4}L${x+5},${y-4}L${x},${y-12}Z" class="an-hi"/>` : `<path d="M${x-5},${y+4}L${x+5},${y+4}L${x},${y+12}Z" class="an-lo"/>`; });
    // month labels
    let ml = '', last = -1; idx.forEach((i,j) => { const ym = dayYM(i); if(ym !== last){ last = ym; ml += `<text x="${X(j)}" y="${H-12}" class="an-ax">${EN_MON[ym%100-1]}${ym%100===1||j===0?' '+Math.floor(ym/100):''}</text>`; } });
    return `<div class="an-chart"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Daily revenue with anomaly band">${g}${band}<polyline points="${mline}" class="an-mean"/><path d="${line}" class="an-line"/>${pts}${ml}<rect x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent" class="an-hit"/></svg><div class="an-tip" hidden></div></div>
      <div class="an-legend"><span><i class="lg-line"></i>Daily revenue</span><span><i class="lg-mean"></i>YTD average</span><span><i class="lg-band"></i>Normal band (± ${st.k}σ)</span><span><i class="lg-hi">▲</i>Anomaly — high</span><span><i class="lg-lo">▼</i>Anomaly — low</span></div>`;
  }
  function wireTip(s, fl, i0, i1){
    const box = cChart.querySelector('.an-chart'); if(!box) return;
    const svg = box.querySelector('svg'), tip = box.querySelector('.an-tip');
    const idx = []; for(let i=i0;i<=i1;i++) if(!(st.noFri && dayW(i)===5)) idx.push(i);
    svg.addEventListener('mousemove', e => {
      const r = svg.getBoundingClientRect(), fx = (e.clientX - r.left)/r.width, L = 58/1100, R = 14/1100;
      const j = Math.max(0, Math.min(idx.length-1, Math.round((fx - L)/(1-L-R) * (idx.length-1)))), i = idx[j], f = fl[i];
      tip.hidden = false; tip.style.left = Math.min(r.width-190, Math.max(0, e.clientX - r.left + 12)) + 'px';
      tip.innerHTML = `<b>${ANM.wd[dayW(i)]} ${dayISO(i)}</b><br>Revenue ${nfmt(s[i])}${f?`<br>YTD average ${nfmt(f.m)}<br>z = ${f.z.toFixed(2)} ${f.hi?'<span class="pill bad">High</span>':f.lo?'<span class="pill warn">Low</span>':''}`:''}`;
    });
    svg.addEventListener('mouseleave', () => tip.hidden = true);
  }

  function docTable(i0ym, i1ym){
    const src = st.noPh && A.docNP ? A.docNP : A.doc;
    const by = {};
    for(const [ym,cc,pt,dn,sp,rev,days] of src){
      if((st.cc!=='ALL'&&cc!==st.cc)||(st.pt!=='ALL'&&pt!==st.pt)||(st.spec!=='ALL'&&sp!==st.spec)) continue;
      const k = dn+'|'+sp; const o = by[k] = by[k] || {dn, sp, m:{}}; o.m[ym] = (o.m[ym]||0) + rev;
    }
    const rows = [];
    for(const k in by){ const o = by[k]; const yms = Object.keys(o.m).map(Number).sort();
      for(const ym of yms){ if(ym < i0ym || ym > i1ym) continue;
        const hist = yms.filter(x => x < ym).map(x => o.m[x]); if(hist.length < 6) continue;
        const m = ANM.mean(hist), sd = ANM.sdp(hist); if(!sd) continue;
        const z = (o.m[ym]-m)/sd; if(Math.abs(z) >= st.k && Math.abs(o.m[ym]-m) >= 5000) rows.push({dn:o.dn, sp:o.sp, ym, v:o.m[ym], m, z});
      } }
    rows.sort((a,b)=>Math.abs(b.z)-Math.abs(a.z));
    let h = `<h3>Doctors outside their own pattern <span class="tag">${rows.length}</span></h3><p class="card-sub">الأطباء خارج نمطهم المعتاد · a month compared with the same doctor's earlier months (needs 6+ months of history, gap ≥ 5,000)</p><div class="aud-scroll" style="max-height:420px"><table class="aud-t"><thead><tr><th>Doctor</th><th>Month</th><th class="n">Revenue</th><th class="n">Usual</th><th class="n">z</th></tr></thead><tbody>`;
    h += rows.slice(0,150).map(r=>`<tr><td>${esc(r.dn)}<div class="an-sub">${esc(r.sp)}</div></td><td>${ymLab(r.ym)}</td><td class="n">${nfmt(r.v)}</td><td class="n">${nfmt(r.m)}</td><td class="n"><span class="pill ${r.z>0?'bad':'warn'}">${r.z>0?'+':''}${r.z.toFixed(1)}</span></td></tr>`).join('') || `<tr><td colspan="5" class="an-empty">No doctor moved outside ± ${st.k}σ of their own history in this period.</td></tr>`;
    return h + '</tbody></table></div>';
  }

  function cashTable(a, b){
    const by = {}, brAgg = {};
    for(const [org,ym,cid,cn,pt,lines,gross,disc,net,rn,ra,hn,ha,nn,na] of A.cash){
      if(ym < a || ym > b || (st.cc!=='ALL'&&org!==st.cc)) continue;
      const k = org+'|'+cid; const o = by[k] = by[k] || {org, cn, lines:0, cg:0, cd:0, net:0, rn:0, ra:0, hn:0, ha:0, nn:0, na:0};
      o.lines += lines; o.net += net; o.rn += rn; o.ra += ra; o.hn += hn; o.ha += ha; o.nn += nn; o.na += na;
      if(pt !== 'Credit'){ o.cg += gross; o.cd += disc; const g = brAgg[org] = brAgg[org] || {g:0,d:0,l:0,r:0}; g.g += gross; g.d += disc; }
      const g2 = brAgg[org] = brAgg[org] || {g:0,d:0,l:0,r:0}; g2.l += lines; g2.r += rn;
    }
    const rows = Object.values(by).filter(o => o.lines >= 50).map(o => {
      const g = brAgg[o.org], avgD = g.g ? g.d/g.g : 0, avgR = g.l ? g.r/g.l : 0;
      const dp = o.cg ? o.cd/o.cg : 0, rp = o.lines ? o.rn/o.lines : 0;
      const f = []; if(o.cg >= 5000 && dp > Math.max(2*avgD, avgD + 0.10)) f.push('Discount'); if(rp > Math.max(3*avgR, 0.05) && o.rn >= 20) f.push('Returns'); if(o.nn >= 20 && o.nn >= 0.05*o.lines) f.push('After hours'); if(o.hn >= 20) f.push('Heavy discounts');
      return {...o, dp, avgD, rp, avgR, f};
    }).sort((x,y)=> y.f.length - x.f.length || y.cd - x.cd);
    let h = `<h3>Cashier controls <span class="tag">${rows.filter(r=>r.f.length).length} flagged of ${rows.length}</span></h3><p class="card-sub">رقابة الكاشير · cash discount rate against the branch average, returns above 3× the branch rate, 20+ heavy (≥30%) cash discounts, and 20+ lines (≥5%) billed between midnight and 6 am · cashiers with 50+ lines in the period</p><div class="aud-scroll" style="max-height:460px"><table class="aud-t"><thead><tr><th>Cashier</th><th>Branch</th><th class="n">Lines</th><th class="n">Cash gross</th><th class="n">Cash discount</th><th class="n">Disc %</th><th class="n">Branch avg</th><th class="n">Returns</th><th class="n">Return amt</th><th class="n">Heavy disc.</th><th class="n">00–06 h</th><th>Flags</th></tr></thead><tbody>`;
    h += rows.slice(0,200).map(r=>`<tr><td>${esc(r.cn)}</td><td>${ANM.brName(r.org)}</td><td class="n">${nfmt(r.lines)}</td><td class="n">${nfmt(r.cg)}</td><td class="n">${nfmt(r.cd)}</td><td class="n ${r.f.includes('Discount')?'neg':''}">${(r.dp*100).toFixed(1)}%</td><td class="n">${(r.avgD*100).toFixed(1)}%</td><td class="n">${nfmt(r.rn)}</td><td class="n">${nfmt(r.ra)}</td><td class="n">${nfmt(r.hn)}</td><td class="n">${nfmt(r.nn)}</td><td>${r.f.map(x=>`<span class="pill ${x==='Discount'||x==='Heavy discounts'?'bad':'warn'}">${x}</span>`).join(' ') || '<span class="pill ok">OK</span>'}</td></tr>`).join('');
    return h + '</tbody></table></div>';
  }

  const EXC = [
    ['HD','Heavy cash discounts','خصومات نقدية كبيرة','Cash and discounted-cash lines where the discount is 30% or more of a gross of 200+. Insurance (credit) lines are excluded because their discounts come from the contract.'],
    ['RT','Largest returns','أكبر المرتجعات','Negative invoice lines — refunds and reversals — largest first.'],
    ['NT','After-hours billing','فوترة بعد منتصف الليل','Lines billed between 00:00 and 06:00, largest first. Legitimate for emergency and dialysis; unusual for clinics.'],
    ['PR','Price outliers','أسعار خارج المعتاد','Unit gross price above max(average + 4σ, 3 × average) for the same service, branch and payment type (services with 30+ lines).'],
    ['DU','Same service twice, same day','تكرار الخدمة لنفس المريض','One patient billed the same service in two or more separate episodes on the same day.'],
    ['DP','Repeated discount beneficiaries','مستفيدون متكررون من الخصم','Patient files with the most cash discount received, per cashier, since Jan 2024 (not filtered by period).']];
  function excTable(a, b){
    const inP = iso => { const ym = +iso.slice(0,7).replace('-',''); return ym >= a && ym <= b; };
    const brOK = org => st.cc==='ALL' || org===st.cc, q = st.q.trim().toLowerCase();
    const hit = arr => !q || arr.some(x => String(x).toLowerCase().includes(q));
    const def = EXC.find(e=>e[0]===st.exc);
    let head = '', body = '', n = 0;
    if(['HD','RT','NT'].includes(st.exc)){
      const rows = A.lines.filter(r => r[0]===st.exc && brOK(r[1]) && inP(r[2]) && hit([r[4],r[5],r[6],r[7],r[9]]));
      n = rows.length;
      head = '<th>Date</th><th>Hr</th><th>Branch</th><th>Cashier</th><th>File no</th><th>Doctor</th><th>Service</th><th>Type · contract</th><th class="n">Gross</th><th class="n">Discount</th><th class="n">Net</th>';
      body = rows.slice(0,300).map(r=>`<tr><td>${r[2]}</td><td>${esc(r[3])}</td><td>${ANM.brName(r[1])}</td><td>${esc(r[4])}</td><td>${esc(r[5])}</td><td>${esc(r[6])}</td><td>${esc(r[7])}</td><td>${esc(r[8])}<div class="an-sub">${esc(r[9])}</div></td><td class="n">${nfmt(r[11],2)}</td><td class="n ${r[12]>=0.5*r[11]&&r[11]>0?'neg':''}">${nfmt(r[12],2)}</td><td class="n">${nfmt(r[13],2)}</td></tr>`).join('');
    } else if(st.exc === 'PR'){
      const rows = A.price.filter(r => brOK(r[0]) && inP(r[3]) && !(st.hidePh && /pharm/i.test(r[4])) && hit([r[4],r[5],r[6],r[7],r[8]]));
      n = rows.length;
      head = '<th>Date</th><th>Branch</th><th>Cashier</th><th>File no</th><th>Doctor</th><th>Service</th><th>Type · contract</th><th class="n">Qty</th><th class="n">Unit gross</th><th class="n">Usual unit</th><th class="n">× usual</th>';
      body = rows.slice(0,300).map(r=>{ const u = r[9] ? r[10]/r[9] : r[10]; return `<tr><td>${r[3]}</td><td>${ANM.brName(r[0])}</td><td>${esc(r[4])}</td><td>${esc(r[5])}</td><td>${esc(r[6])}</td><td>${esc(r[7])}</td><td>${esc(r[2])}<div class="an-sub">${esc(r[8])}</div></td><td class="n">${nfmt(r[9])}</td><td class="n">${nfmt(u,2)}</td><td class="n">${nfmt(r[14],2)}</td><td class="n"><span class="pill bad">${(u/(r[14]||1)).toFixed(1)}×</span></td></tr>`; }).join('');
    } else if(st.exc === 'DU'){
      const rows = A.dup.filter(r => brOK(r[0]) && inP(r[1]) && hit([r[2],r[3],r[8]]));
      n = rows.length;
      head = '<th>Date</th><th>Branch</th><th>File no</th><th>Service</th><th>Type</th><th class="n">Episodes</th><th class="n">Net billed</th><th>Cashier</th>';
      body = rows.slice(0,300).map(r=>`<tr><td>${r[1]}</td><td>${ANM.brName(r[0])}</td><td>${esc(r[2])}</td><td>${esc(r[3])}</td><td>${esc(r[4])}</td><td class="n">${r[6]}</td><td class="n">${nfmt(r[7],2)}</td><td>${esc(r[8])}</td></tr>`).join('');
    } else {
      const rows = A.discpat.filter(r => brOK(r[0]) && hit([r[1],r[2]]));
      n = rows.length;
      head = '<th>Branch</th><th>File no</th><th>Cashier</th><th class="n">Lines</th><th class="n">Gross</th><th class="n">Discount</th><th class="n">Disc %</th><th>First</th><th>Last</th>';
      body = rows.slice(0,300).map(r=>`<tr><td>${ANM.brName(r[0])}</td><td>${esc(r[1])}</td><td>${esc(r[2])}</td><td class="n">${nfmt(r[3])}</td><td class="n">${nfmt(r[4])}</td><td class="n">${nfmt(r[5])}</td><td class="n">${r[4]?(r[5]/r[4]*100).toFixed(0)+'%':'—'}</td><td>${r[6]}</td><td>${r[7]}</td></tr>`).join('');
    }
    const tabs = EXC.map(e=>`<button class="an-tab${e[0]===st.exc?' on':''}" data-k="${e[0]}">${e[1]}</button>`).join('');
    return `<h3>Invoice exception lines</h3><p class="card-sub">بنود فواتير تحتاج مراجعة · ${esc(def[3])}</p>
      <div class="an-tabs" role="tablist">${tabs}</div>
      <div class="aud-bar" style="margin:10px 0"><div class="f"><label for="ai-q">Search</label><input type="search" id="ai-q" placeholder="cashier, file no, doctor, service" value="${esc(st.q)}"></div>${st.exc==='PR'?ANM.chk('ai-hph','Hide pharmacy items',st.hidePh):''}<span class="an-count">${nfmt(n)} line${n===1?'':'s'}${n>300?' · first 300 shown':''}</span></div>
      <div class="aud-scroll"><table class="aud-t"><thead><tr>${head}</tr></thead><tbody>${body || `<tr><td colspan="11" class="an-empty">Nothing in this period for the selected branch.</td></tr>`}</tbody></table></div>`;
  }

  function render(){
    drawBar();
    const s = series(), fl = flags(s), {i0, i1, w} = win();
    let rev = 0, hiN = 0, loN = 0, anomV = 0, big = null;
    const days = [];
    for(let i=i0;i<=i1;i++){ if(st.noFri && dayW(i)===5) continue; rev += s[i]; const f = fl[i]; if(!f) continue;
      if(f.hi || f.lo){ f.hi ? hiN++ : loN++; anomV += s[i]; days.push(i); if(!big || Math.abs(f.z) > Math.abs(fl[big].z)) big = i; } }
    let lyRev = null; if(w.c){ lyRev = 0; for(let i=0;i<ND;i++){ const ym = dayYM(i); if(ym>=w.c.a && ym<=w.c.b && !(st.noFri && dayW(i)===5)) lyRev += s[i]; } }
    kp.innerHTML = kpiTile('Invoice revenue', nfmt(rev), lyRev!==null ? dPct(rev, lyRev) : periodLabel('en'))
      + kpiTile('Anomaly days', `${hiN + loN}`, `${hiN} high · ${loN} low`, hiN+loN > 0)
      + kpiTile('Anomaly revenue value', nfmt(anomV), rev ? `${(anomV/rev*100).toFixed(1)}% of revenue on flagged days` : '')
      + kpiTile('Strongest deviation', big!==null ? nfmt(s[big]) : '—', big!==null ? `${dayISO(big)} · z ${fl[big].z.toFixed(1)}` : 'none in period', big!==null);
    cChart.innerHTML = `<h3>Total revenue, anomaly value and flag by date</h3><p class="card-sub">الإيراد اليومي ونطاق الشذوذ · ${esc(periodLabel('en'))} · ${st.cc==='ALL'?'all branches':ANM.brName(st.cc)} · ${st.pt==='ALL'?'cash + credit':st.pt}${st.spec!=='ALL'?' · '+esc(st.spec):''}</p>` + chart(s, fl, i0, i1);
    wireTip(s, fl, i0, i1);
    days.sort((x,y)=>Math.abs(fl[y].z)-Math.abs(fl[x].z));
    cDays.innerHTML = `<h3>Anomaly days <span class="tag">${days.length}</span></h3><p class="card-sub">الأيام الشاذة · largest deviation first — a high day can be a bulk posting or back-dated invoices, a low day a system outage, a closure or unbilled services</p><div class="aud-scroll" style="max-height:420px"><table class="aud-t"><thead><tr><th>Date</th><th>Day</th><th class="n">Revenue</th><th class="n">YTD average</th><th class="n">Gap</th><th class="n">z</th></tr></thead><tbody>`
      + (days.map(i=>{ const f = fl[i]; return `<tr><td>${dayISO(i)}</td><td>${ANM.wd[dayW(i)]}</td><td class="n">${nfmt(s[i])}</td><td class="n">${nfmt(f.m)}</td><td class="n ${f.hi?'':'neg'}">${nfmt(s[i]-f.m)}</td><td class="n"><span class="pill ${f.hi?'bad':'warn'}">${f.z>0?'+':''}${f.z.toFixed(1)}</span></td></tr>`; }).join('') || `<tr><td colspan="6" class="an-empty">No day outside ± ${st.k}σ in this period.</td></tr>`) + '</tbody></table></div>';
    cDoc.innerHTML = docTable(w.a, w.b);
    cCash.innerHTML = cashTable(w.a, w.b);
    cExc.innerHTML = excTable(w.a, w.b);
    cExc.querySelectorAll('.an-tab').forEach(b => b.onclick = () => { st.exc = b.dataset.k; render(); });
    const q = cExc.querySelector('#ai-q'); if(q){ q.oninput = () => { st.q = q.value; const pos = q.selectionStart; cExc.innerHTML = excTable(w.a, w.b); rewireExc(w); const q2 = cExc.querySelector('#ai-q'); q2.focus(); q2.setSelectionRange(pos,pos); }; }
    rewireExc(w);
  }
  function rewireExc(w){
    cExc.querySelectorAll('.an-tab').forEach(b => b.onclick = () => { st.exc = b.dataset.k; render(); });
    const q = cExc.querySelector('#ai-q'); if(q) q.oninput = () => { st.q = q.value; const pos = q.selectionStart; cExc.innerHTML = excTable(w.a, w.b); rewireExc(w); const q2 = cExc.querySelector('#ai-q'); q2.focus(); try{ q2.setSelectionRange(pos,pos); }catch(e){} };
    const h = cExc.querySelector('#ai-hph'); if(h) h.onchange = () => { st.hidePh = h.checked; cExc.innerHTML = excTable(w.a, w.b); rewireExc(w); };
  }
  let lastCC = TI.cc;
  TI.on(() => { if(TI.cc !== lastCC){ lastCC = TI.cc; st.cc = ANM.ccFromTI(); } render(); });
  render();
})();

/* ---------------------------------------------------------------- B ---- */
/* Expense anomalies — GL account by account                                */
(function(){
  const sec = document.getElementById('sec-aud-anom-exp'); if(!sec || !DATA.exp) return;
  const E = DATA.exp;
  const TESTS = [
    ['RND','Round amount','مبالغ مقربة','Debit of 1,000+ that is an exact multiple of 500'],
    ['WKD','Friday manual entry','قيد يدوي يوم جمعة','Manual journal (VM type J) dated on a Friday'],
    ['OUT','Outlier line','بند شاذ','Debit above the account\'s average + 3σ and above 3 × average (1,000+)'],
    ['DUP','Possible duplicate','تكرار محتمل','Same account and same debit (500+) on a different voucher within ±7 days'],
    ['SLF','Self-posted','مرحّل من نفس المدخل','Manual journal entered and posted by the same user'],
    ['NDS','No description','بدون بيان','Description missing or shorter than 6 characters'],
    ['NAT','No attachment','بدون مرفق','Manual journal of 1,000+ with no attached document'],
    ['THR','Just below a limit','أقل من حد الاعتماد','Debit just under 5k, 10k, 20k or 50k — a classic approval-limit split'],
    ['REV','Manual credit','قيد دائن يدوي','Credit to an expense account through a manual journal (reversal or reclass)']];
  const W8 = [1,1,3,2,1,1,1,2,1];
  // payroll-type accounts repeat identical round amounts every month by nature — round/duplicate/limit/Friday tests are shown but not scored there
  const PAYROLL = a => /^319/.test(a) || a === '3140002' || a === '3200000';
  const w8For = (a, i) => PAYROLL(a) && [0,1,3,7].includes(i) ? 0 : W8[i];
  audHead(sec, 'Accounting Audit · Anomaly Detection', 'Expense Anomalies', 'كشف الشذوذ في المصروفات',
    'Every expense account (type Expenses, 3xxxxxx) tested month by month and line by line. The monthly test is a year-to-date control band: a month outside the year-to-date average ± 2σ. The line tests are standard fraud and error red flags — round amounts, duplicates, outliers, self-posting, missing documents, amounts just under an approval limit. A flag is a reason to look, not a finding.');
  const st = {cc: ANM.ccFromTI(), acct: 'ALL', k: 2, test: 'ALL', user: 'ALL', q: '', open: null};
  const barBox = el('div','aud-bar'); sec.appendChild(barBox);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const cAcc = el('div','card'); cAcc.style.marginTop = '16px'; sec.appendChild(cAcc);
  const row = el('div','grid grid-2'); row.style.marginTop = '16px'; row.style.alignItems = 'start'; sec.appendChild(row);
  const cTest = el('div','card'), cUser = el('div','card'); row.appendChild(cTest); row.appendChild(cUser);
  const cLines = el('div','card'); cLines.style.marginTop = '16px'; sec.appendChild(cLines);
  sec.appendChild(el('div','note', `<b>Source.</b> Cure / EXSYS <code>GL_TRANSACTIONS_DETAILS</code> in each branch database, ACCOUNT_TYPE = Expenses, posted + open vouchers, Jan 2024 – Sep 2026, year-end closing entries removed. Riyadh's ledger carries head-office and most shared costs (Bur-2 books almost nothing locally). The line list holds the highest-scoring lines per ledger (Riyadh 195, Bur-1 80, Rafha 80; score = sum of test weights, outlier ×3, duplicate and limit ×2); counts by test and month cover every line. Monthly figures are debit − credit. Salary, allowance, GOSI and board-remuneration accounts (319xxxx, 3140002, 3200000) repeat identical round amounts by design, so their round, Friday, duplicate and limit counts are shown in grey and left out of the score.`));
  const ACCTS = Object.keys(E.names).sort();
  const brs = () => st.cc === 'ALL' ? ANM.BR : [st.cc];
  const ymList = []; for(const y of [2024,2025,2026]) for(let m=1;m<=12;m++){ const ym = y*100+m; if(ym <= 202609) ymList.push(ym); }

  function drawBar(){
    barBox.innerHTML = ANM.bar('ae-cc','Ledger',[['ALL','All ledgers'],['01','Riyadh (incl. HQ)'],['02','Bur-1'],['03','Bur-2'],['04','Rafha']],st.cc)
      + ANM.bar('ae-acct','Account',[['ALL','All expense accounts'],...ACCTS.map(a=>[a, a+' · '+E.names[a]])],st.acct)
      + ANM.bar('ae-k','Monthly sensitivity',[[2,'± 2σ (NextGen)'],[2.5,'± 2.5σ'],[3,'± 3σ']],st.k);
    const on = (id, fn) => barBox.querySelector('#'+id).onchange = e => { fn(e.target); render(); };
    on('ae-cc', t => st.cc = t.value); on('ae-acct', t => { st.acct = t.value; st.open = t.value==='ALL' ? null : t.value; }); on('ae-k', t => st.k = +t.value);
  }
  function monthly(a){ const m = {}; for(const cc of brs()){ const x = (E.mon[cc]||{})[a]; if(!x) continue; for(const ym in x){ const v = x[ym]; (m[ym] = m[ym] || [0,0,0,0]); m[ym][0] += v[0]; m[ym][1] += v[1]; m[ym][2] += v[2]; m[ym][3] += v[3]; } } return m; }
  function flagsFor(a, from, to){ const t = new Array(10).fill(0); for(const cc of brs()){ const x = (E.flg[cc]||{})[a]; if(!x) continue; for(const ym in x){ if(+ym < from || +ym > to) continue; x[ym].forEach((v,i)=>t[i]+=v); } } return t; }
  // NextGen monthly rule: month net vs mean ± kσ of the same year's months up to and including it (blank months skipped)
  function spikes(m){ const out = {}; let yr = 0, vals = [];
    for(const ym of ymList){ const y = Math.floor(ym/100); if(y !== yr){ yr = y; vals = []; } const v = m[ym] ? m[ym][0]-m[ym][1] : 0; if(!v) continue; vals.push(v);
      const mu = ANM.mean(vals), sd = ANM.sdp(vals); if(vals.length >= 3 && sd && (v > mu + st.k*sd || v < mu - st.k*sd)) out[ym] = (v-mu)/sd; }
    return out; }
  function spark(m, sp, a, b){
    const W = 360, H = 70, xs = ymList, vals = xs.map(ym => m[ym] ? m[ym][0]-m[ym][1] : 0), mx = Math.max(1, ...vals.map(Math.abs));
    const bw = W/xs.length;
    return `<svg viewBox="0 0 ${W} ${H}" class="an-spark" role="img" aria-label="Monthly net expense">` + xs.map((ym,i)=>{ const v = vals[i], h = Math.abs(v)/mx*(H-8); const inW = ym>=a && ym<=b;
      return `<rect x="${i*bw+1}" y="${v>=0?H-4-h:H-4}" width="${Math.max(1,bw-2)}" height="${Math.max(0.5,h)}" rx="1" class="${sp[ym]!==undefined?'an-sb-hi':inW?'an-sb-in':'an-sb'}"><title>${ymLab(ym)}: ${nfmt(v)}${sp[ym]!==undefined?' · anomaly z '+sp[ym].toFixed(1):''}</title></rect>`; }).join('') + '</svg>';
  }
  function lineOK(r, a, b){ const ym = +r[3].slice(0,7).replace('-',''); return ym >= a && ym <= b && (st.cc==='ALL'||r[0]===st.cc) && (st.acct==='ALL'||r[1]===st.acct); }
  const TKEY = ['RND','WKD','OUT','DUP','SLF','NDS','NAT','THR','REV'];
  function render(){
    drawBar();
    const w = audWindow(), a = w.a, b = w.b;
    const list = (st.acct==='ALL' ? ACCTS : [st.acct]).map(ac => {
      const m = monthly(ac); let net = 0, lines = 0, manual = 0, prev = [];
      for(const ym in m){ const v = m[ym]; if(+ym>=a && +ym<=b){ net += v[0]-v[1]; lines += v[2]; manual += v[3]; } }
      for(const ym of ymList){ if(ym < a && ym >= ymAdd(a,-12) && m[ym]) prev.push(m[ym][0]-m[ym][1]); }
      const sp = spikes(m), spIn = Object.keys(sp).filter(ym => +ym>=a && +ym<=b);
      const f = flagsFor(ac, a, b), score = f.slice(1).reduce((s,x,i)=>s+x*w8For(ac,i),0);
      const avg12 = prev.length ? prev.reduce((s,x)=>s+x,0)/12 : 0;
      return {ac, name: E.names[ac], m, net, lines, manual, avg12, sp, spIn, f, score, risk: lines ? score/lines*100 : 0};
    }).filter(r => r.lines || r.net);
    list.sort((x,y)=> (y.spIn.length>0) - (x.spIn.length>0) || y.score - x.score);
    const tot = list.reduce((s,r)=>s+r.net,0), totL = list.reduce((s,r)=>s+r.lines,0), totM = list.reduce((s,r)=>s+r.manual,0);
    const flagT = new Array(10).fill(0); list.forEach(r => r.f.forEach((v,i)=>flagT[i]+=v));
    const hard = flagT[3]+flagT[4]+flagT[8];
    let ly = null; if(w.c){ ly = 0; for(const r of list){ for(const ym in r.m){ if(+ym>=w.c.a && +ym<=w.c.b) ly += r.m[ym][0]-r.m[ym][1]; } } }
    kp.innerHTML = kpiTile('Expenses in period', nfmt(tot), ly!==null ? dPct(tot, ly) : periodLabel('en'))
      + kpiTile('Accounts with an anomaly month', `${list.filter(r=>r.spIn.length).length}`, `of ${list.length} active accounts · ± ${st.k}σ YTD`, list.some(r=>r.spIn.length))
      + kpiTile('High-weight line flags', nfmt(hard), `${nfmt(flagT[3])} outliers · ${nfmt(flagT[4])} duplicates · ${nfmt(flagT[8])} near a limit`, hard>0)
      + kpiTile('Manual journal share', totL ? (totM/totL*100).toFixed(1)+'%' : '—', `${nfmt(totM)} of ${nfmt(totL)} lines`);
    let h = `<h3>Account by account <span class="tag">${list.length}</span></h3><p class="card-sub">تحليل الحسابات حساباً حساباً · ${esc(periodLabel('en'))} · accounts with an anomaly month first, then by weighted flag score · click a row for its months and flagged lines</p><div class="aud-scroll" style="max-height:620px"><table class="aud-t an-acc"><thead><tr><th>Account</th><th class="n">Net expense</th><th class="n">Avg / month (prior 12)</th><th class="n">Anomaly months</th>${TESTS.map(t=>`<th class="n" title="${esc(t[3])}">${t[0]}</th>`).join('')}<th class="n">Score / 100 lines</th><th>Status</th></tr></thead><tbody>`;
    for(const r of list){
      const status = r.spIn.length ? '<span class="pill bad">Anomaly month</span>' : r.risk >= 25 ? '<span class="pill warn">Review</span>' : '<span class="pill ok">Normal</span>';
      h += `<tr class="aud-row-click${st.open===r.ac?' open':''}" data-ac="${r.ac}"><td>${r.ac}<div class="an-sub ar-inline">${esc(r.name)}</div></td><td class="n">${nfmt(r.net)}</td><td class="n">${nfmt(r.avg12)}</td><td class="n">${r.spIn.length ? `<span class="pill bad">${r.spIn.length}</span>` : '—'}</td>${r.f.slice(1).map((v,i)=>`<td class="n ${v&&w8For(r.ac,i)>1?'neg':''}${v&&!w8For(r.ac,i)?' an-z':''}">${v||'<span class="an-z">·</span>'}</td>`).join('')}<td class="n">${r.risk.toFixed(0)}</td><td>${status}</td></tr>`;
      if(st.open === r.ac){
        const ls = E.lines.filter(x => x[1]===r.ac && lineOK(x, a, b));
        h += `<tr class="aud-sub"><td colspan="${6+TESTS.length}"><div class="an-open"><div><div class="an-sub">Net expense by month, Jan 2024 – Sep 2026 (red = anomaly month, dark = in period)</div>${spark(r.m, r.sp, a, b)}<div class="an-sub">${r.spIn.map(ym=>`${ymLab(+ym)} z ${r.sp[ym].toFixed(1)}`).join(' · ') || 'No anomaly month in the period.'}</div></div><div>${ls.length ? `<table class="aud-t"><thead><tr><th>Date</th><th>Voucher</th><th class="n">Debit</th><th>Entered by</th><th>Description</th><th>Flags</th></tr></thead><tbody>${ls.slice(0,40).map(x=>`<tr><td>${x[3]}</td><td>${esc(x[2])}</td><td class="n">${nfmt(x[4]||-x[5],2)}</td><td>${esc(x[8])}</td><td class="ar">${esc(x[11])}</td><td>${flagPills(x[12])}</td></tr>`).join('')}</tbody></table>` : '<div class="an-sub">None of this account\'s lines are among the top-scoring lines in the period.</div>'}</div></div></td></tr>`;
      }
    }
    cAcc.innerHTML = h + '</tbody></table></div>';
    cAcc.querySelectorAll('tr[data-ac]').forEach(tr => tr.onclick = () => { st.open = st.open === tr.dataset.ac ? null : tr.dataset.ac; render(); });
    // tests card
    cTest.innerHTML = `<h3>Red-flag tests</h3><p class="card-sub">اختبارات مؤشرات الخطر · count of lines in the period for the selected ledger/account · click a test to filter the line list</p><table class="aud-t"><thead><tr><th>Test</th><th>What it catches</th><th class="n">Lines</th></tr></thead><tbody>${TESTS.map((t,i)=>`<tr class="aud-row-click${st.test===t[0]?' open':''}" data-t="${t[0]}"><td>${t[1]}<div class="an-sub ar-inline">${t[2]}</div></td><td class="an-sub">${esc(t[3])}</td><td class="n">${nfmt(flagT[i+1])}</td></tr>`).join('')}</tbody></table>`;
    cTest.querySelectorAll('tr[data-t]').forEach(tr => tr.onclick = () => { st.test = st.test === tr.dataset.t ? 'ALL' : tr.dataset.t; render(); });
    // users card (from scored lines)
    const L = E.lines.filter(x => lineOK(x, a, b)); const us = {};
    for(const x of L){ const u = us[x[8]||x[7]] = us[x[8]||x[7]] || {n:0, amt:0, slf:0, nat:0, sc:0}; u.n++; u.amt += x[4]; u.sc += x[13]; if(x[12][4]==='1') u.slf++; if(x[12][6]==='1') u.nat++; }
    const ur = Object.entries(us).sort((x,y)=>y[1].sc-x[1].sc);
    cUser.innerHTML = `<h3>Who entered the flagged lines</h3><p class="card-sub">المستخدمون أصحاب القيود المؤشرة · among the top-scoring lines in the period · click to filter</p><table class="aud-t"><thead><tr><th>Entry user</th><th class="n">Lines</th><th class="n">Debit</th><th class="n">Self-posted</th><th class="n">No attachment</th></tr></thead><tbody>${ur.map(([u,o])=>`<tr class="aud-row-click${st.user===u?' open':''}" data-u="${esc(u)}"><td>${esc(u)}</td><td class="n">${o.n}</td><td class="n">${nfmt(o.amt)}</td><td class="n">${o.slf}</td><td class="n">${o.nat}</td></tr>`).join('') || '<tr><td colspan="5" class="an-empty">No scored lines in this period.</td></tr>'}</tbody></table>`;
    cUser.querySelectorAll('tr[data-u]').forEach(tr => tr.onclick = () => { st.user = st.user === tr.dataset.u ? 'ALL' : tr.dataset.u; render(); });
    drawLines(a, b);
  }
  function flagPills(s){ return TKEY.map((k,i)=> s[i]==='1' ? `<span class="pill ${W8[i]>1?'bad':'warn'}" title="${esc(TESTS[i][1])}">${k}</span>` : '').join(' '); }
  function drawLines(a, b){
    const ti = TKEY.indexOf(st.test), q = st.q.trim().toLowerCase();
    const rows = E.lines.filter(x => lineOK(x, a, b) && (ti<0 || x[12][ti]==='1') && (st.user==='ALL' || (x[8]||x[7])===st.user) && (!q || [x[1],x[2],x[7],x[8],x[11],E.names[x[1]]].some(v=>String(v||'').toLowerCase().includes(q)))).sort((x,y)=>y[13]-x[13] || y[4]-x[4]);
    cLines.innerHTML = `<h3>Flagged lines <span class="tag">${rows.length}</span></h3><p class="card-sub">البنود المؤشرة · highest score first${st.test!=='ALL'?' · test: '+esc(TESTS[ti][1]):''}${st.user!=='ALL'?' · user: '+esc(st.user):''}</p>
      <div class="aud-bar" style="margin:6px 0 10px"><div class="f"><label for="ae-q">Search</label><input type="search" id="ae-q" placeholder="voucher, user, account, description" value="${esc(st.q)}"></div>${st.test!=='ALL'||st.user!=='ALL'?'<button class="clr" id="ae-clr">Clear test / user filter</button>':''}</div>
      <div class="aud-scroll"><table class="aud-t"><thead><tr><th>Date</th><th>Ledger</th><th>Account</th><th>Voucher</th><th>Type</th><th class="n">Debit</th><th class="n">Credit</th><th>Entered by</th><th>Posted by</th><th>Description</th><th>Flags</th><th class="n">Score</th></tr></thead><tbody>${rows.map(x=>`<tr><td>${x[3]}</td><td>${ANM.brName(x[0])}</td><td>${x[1]}<div class="an-sub ar-inline">${esc(E.names[x[1]]||'')}</div></td><td>${esc(x[2])}</td><td>${x[6]==='J'?'Manual':'System'}</td><td class="n">${nfmt(x[4],2)}</td><td class="n">${nfmt(x[5],2)}</td><td>${esc(x[8])}</td><td>${esc(x[9])||'<span class="pill warn">not posted</span>'}</td><td class="ar">${esc(x[11])}</td><td>${flagPills(x[12])}</td><td class="n">${x[13]}</td></tr>`).join('') || '<tr><td colspan="12" class="an-empty">No flagged lines match.</td></tr>'}</tbody></table></div>`;
    const q2 = cLines.querySelector('#ae-q'); q2.oninput = () => { st.q = q2.value; const pos = q2.selectionStart; drawLines(a, b); const q3 = cLines.querySelector('#ae-q'); q3.focus(); try{ q3.setSelectionRange(pos,pos); }catch(e){} };
    const c = cLines.querySelector('#ae-clr'); if(c) c.onclick = () => { st.test = 'ALL'; st.user = 'ALL'; render(); };
  }
  let lastCC = TI.cc;
  TI.on(() => { if(TI.cc !== lastCC){ lastCC = TI.cc; st.cc = ANM.ccFromTI(); } render(); });
  render();
})();
