
/* ======================================================================
   FORECASTING  ·  SARIMA(X) invoice revenue forecast (cash / credit) and
   forecast-vs-actual audit from the append-only forecast ledger
   ====================================================================== */
(function(){
  const F = DATA.fc; if(!F) return;
  const ym2lab = ym => EN_MON[+String(ym).slice(4)-1] + ' ' + String(ym).slice(0,4);
  const ymNext = (ym, k) => { let y = Math.floor(ym/100), m = ym%100 + k; while(m>12){m-=12;y++;} while(m<1){m+=12;y--;} return y*100+m; };
  const pct = (v, d=1) => v==null||!isFinite(v) ? '—' : (v>0?'+':v<0?'−':'') + Math.abs(v*100).toFixed(d) + '%';
  const BRS = ['ALL','01','02','03','04'];
  const KINDS = [['total','Cash + credit'],['cash','Cash'],['credit','Credit']];
  const LF = +F.last_full;
  const keyOf = (br, k) => br==='ALL' ? `ALL|${k}` : (k==='total' ? null : `${br}|${k}`);
  const ccInit = () => (TI.cc && ['01','02','03','04'].includes(TI.cc)) ? TI.cc : 'ALL';
  // series for a branch/kind; branch totals are summed from cash + credit
  function actual(br, k){
    if(br!=='ALL' && k==='total'){ const a = F.act[`${br}|cash`]||{}, b = F.act[`${br}|credit`]||{}; const o = {}; for(const ym of new Set([...Object.keys(a),...Object.keys(b)])){ const x=a[ym]||[0,0,0,0], y=b[ym]||[0,0,0,0]; o[ym]=x.map((v,i)=>v+y[i]); } return o; }
    return F.act[keyOf(br,k)] || {};
  }
  function ledger(br, k){
    if(br!=='ALL' && k==='total'){
      const a = F.led[`${br}|cash`]||[], b = F.led[`${br}|credit`]||[], idx = {};
      for(const r of b) idx[r[0]+'|'+r[1]] = r;
      return a.filter(r => idx[r[0]+'|'+r[1]]).map(r => { const s = idx[r[0]+'|'+r[1]]; return [r[0], r[1], r[2]+s[2], r[3]+s[3], r[4]+s[4], r[5]+s[5], r[6]+s[6], (r[7]||0)+(s[7]||0), r[8], 0, r[10]]; });
    }
    return F.led[keyOf(br,k)] || [];
  }
  const liveVintage = rows => rows.filter(r=>r[8]==='live').reduce((m,r)=> r[0] > m ? r[0] : m, '');
  function barHtml(pfx, st){
    return ANM.bar(pfx+'-br','Branch', BRS.map(b=>[b, F.brn[b]]), st.br) + ANM.bar(pfx+'-k','Revenue', KINDS, st.k);
  }

  /* -------------------------------------------------------------- 1 -- */
  const s1 = document.getElementById('sec-fc-rev');
  if(s1){
    audHead(s1, 'Forecasting', 'Revenue Forecast', 'توقع الإيرادات النقدية والآجلة',
      'Cash and credit invoice revenue forecast month by month with a seasonal ARIMA model (SARIMAX with a Ramadan / Eid / Friday calendar). The model is re-selected every month on its own most recent forecast errors, and every forecast it issues is written to an append-only ledger so the next tab can audit it against the actuals.');
    const st = {br: ccInit(), k: 'total'};
    const bar = el('div','aud-bar'); s1.appendChild(bar);
    const kp = el('div','grid grid-4'); s1.appendChild(kp);
    const cc = el('div','card'); cc.style.marginTop='16px'; s1.appendChild(cc);
    const row = el('div','grid grid-2'); row.style.marginTop='16px'; row.style.alignItems='start'; s1.appendChild(row);
    const ct = el('div','card'), cm = el('div','card'); row.appendChild(ct); row.appendChild(cm);
    s1.appendChild(el('div','note', `<b>Source.</b> Every figure comes from the EXSYS database through the Cure MCP: <code>RC_PATIENT_INVOICES</code> × <code>RC_PATIENT_INVOICE_CHARGES</code> (posted) minus <code>RC_PATIENT_REFUND_INVOICES</code> × <code>RC_PATIENT_RETURN_INV_CHARGES</code>, net of discount, patient share and VAT, payment type from the episode contract (cash contract → Cash, invoice type C/D → Cash, R → Credit). It ties to the daily invoice series of the Invoice Anomalies tab within 0.01 % (2025: 73,579,425 vs 73,580,303). Model fitted in Python statsmodels on the finance PC (<code>_forecast\\sarima_forecast.py</code>), run ${esc(F.run)}, data through ${ym2lab(LF)}.`));
    function render(){
      bar.innerHTML = barHtml('fr', st);
      bar.querySelector('#fr-br').onchange = e => { st.br = e.target.value; if(st.br!=='ALL' && st.k==='total') {} render(); };
      bar.querySelector('#fr-k').onchange = e => { st.k = e.target.value; render(); };
      const A = actual(st.br, st.k), L = ledger(st.br, st.k), v = liveVintage(L);
      const fut = L.filter(r => r[0]===v).sort((a,b)=>a[1]-b[1]);
      const regKey = keyOf(st.br, st.k), reg = regKey ? F.reg[regKey] : null;
      const nx = fut[0], cm0 = nx ? A[nx[1]] : null;
      const ly = nx ? A[String(ymNext(+nx[1], -12))] : null;
      const fy = String(Math.floor(LF/100)+1), fyF = fut.filter(r=>r[1].startsWith(fy)).reduce((s,r)=>s+r[2],0), fyLY = Object.entries(A).filter(([ym])=>ym.startsWith(String(+fy-1))).reduce((s,[,x])=>s+x[0],0);
      const restYr = fut.filter(r=>r[1].startsWith(String(Math.floor(LF/100)))), ytd = Object.entries(A).filter(([ym])=>ym.startsWith(String(Math.floor(LF/100))) && +ym<=LF).reduce((s,[,x])=>s+x[0],0);
      const outlook = ytd + restYr.reduce((s,r)=>s+r[2],0);
      kp.innerHTML = kpiTile(`Forecast ${nx?ym2lab(nx[1]):''}`, nx?nfmt(nx[2]):'—', nx? `80% range ${nfmt(nx[3])} – ${nfmt(nx[4])}${ly?' · '+pct(nx[2]/ly[0]-1)+' vs LY':''}` : '')
        + kpiTile(`${ym2lab(nx?nx[1]:LF)} so far`, cm0 ? nfmt(cm0[0]) : '—', cm0 && nx ? `${(cm0[0]/nx[2]*100).toFixed(0)}% of forecast · month still open` : 'month still open')
        + kpiTile(`FY ${Math.floor(LF/100)} outlook`, nfmt(outlook), `YTD actual ${nfmt(ytd)} + ${restYr.length} forecast months`)
        + kpiTile(`FY ${fy} forecast`, fyF ? nfmt(fyF) : '—', fyLY && fyF ? pct(fyF/fyLY-1)+` vs FY ${+fy-1} actual` : '');
      // chart: last 36 months actual + forecast bands
      const hist = Object.keys(A).map(Number).filter(ym => ym <= LF).sort((a,b)=>a-b).slice(-36);
      const xs = [...hist, ...fut.map(r=>+r[1])];
      const W=1100,H=320,Lm=64,R=14,T=16,B=34; let mx = 0;
      hist.forEach(ym=>mx=Math.max(mx,A[ym][0])); fut.forEach(r=>mx=Math.max(mx,r[6]||r[4]||r[2]));
      mx*=1.06; const X=i=>Lm+(W-Lm-R)*i/(xs.length-1), Y=v=>T+(H-T-B)*(1-v/mx);
      const step=Math.pow(10,Math.floor(Math.log10(mx/4))); const tick=[1,2,2.5,5,10].map(x=>x*step).find(t=>mx/t<=5)||step*10;
      let g=''; for(let t=0;t<=mx;t+=tick) g+=`<line x1="${Lm}" x2="${W-R}" y1="${Y(t)}" y2="${Y(t)}" class="an-grid"/><text x="${Lm-6}" y="${Y(t)+4}" class="an-ax" text-anchor="end">${t>=1e6?(t/1e6).toFixed(t%1e6?1:0)+'M':(t/1000).toFixed(0)+'k'}</text>`;
      const off = hist.length;
      const band = (lo,hi,cls) => { if(!fut.length) return ''; let up='',dn=''; fut.forEach((r,i)=>{ up+=`${X(off+i)},${Y(r[hi])} `; dn=`${X(off+i)},${Y(r[lo])} `+dn; }); return `<polygon points="${X(off-1)},${Y(A[hist[off-1]][0])} ${up}${dn}" class="${cls}"/>`; };
      let al=''; hist.forEach((ym,i)=>al+=`${i?'L':'M'}${X(i).toFixed(1)},${Y(A[ym][0]).toFixed(1)}`);
      let fl=`M${X(off-1).toFixed(1)},${Y(A[hist[off-1]][0]).toFixed(1)}`; fut.forEach((r,i)=>fl+=`L${X(off+i).toFixed(1)},${Y(r[2]).toFixed(1)}`);
      // back-test 1-step forecasts as dots
      let bt=''; hist.forEach((ym,i)=>{ const r = L.find(q=>q[1]===String(ym) && q[0]===String(ym)); if(r) bt+=`<circle cx="${X(i)}" cy="${Y(r[2])}" r="2.6" class="fc-bt"><title>${ym2lab(ym)} · 1-month-ahead forecast ${nfmt(r[2])} · actual ${nfmt(A[ym][0])}</title></circle>`; });
      let ml=''; xs.forEach((ym,i)=>{ if(ym%100===1||i===0) ml+=`<text x="${X(i)}" y="${H-12}" class="an-ax">${ym2lab(ym)}</text>`; });
      const mtd = cm0 && nx ? `<circle cx="${X(off)}" cy="${Y(cm0[0])}" r="4" class="fc-mtd"><title>${ym2lab(nx[1])} to date ${nfmt(cm0[0])}</title></circle>` : '';
      cc.innerHTML = `<h3>Invoice revenue — actual and forecast</h3><p class="card-sub">الإيراد الفعلي والمتوقع · ${esc(F.brn[st.br])} · ${KINDS.find(k=>k[0]===st.k)[1]} · last 36 months and ${fut.length} months ahead</p>
        <div class="an-chart"><svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" role="img" aria-label="Actual and forecast revenue">${g}<line x1="${X(off-0.5)}" x2="${X(off-0.5)}" y1="${T}" y2="${H-B}" class="fc-cut"/>${band(5,6,'fc-b95')}${band(3,4,'fc-b80')}<path d="${al}" class="an-line"/><path d="${fl}" class="fc-line"/>${bt}${mtd}${ml}</svg></div>
        <div class="an-legend"><span><i class="lg-line"></i>Actual</span><span><i class="lg-fc"></i>Forecast</span><span><i class="lg-b80"></i>80% range</span><span><i class="lg-b95"></i>95% range</span><span><i class="lg-bt">●</i>What the model forecast one month ahead (back-test)</span><span><i class="lg-mtd">●</i>Current month to date</span></div>`;
      ct.innerHTML = `<h3>Forecast by month</h3><p class="card-sub">جدول التوقعات · vintage issued ${esc(F.run)} (data through ${ym2lab(LF)})</p><div class="aud-scroll" style="max-height:440px"><table class="aud-t"><thead><tr><th>Month</th><th class="n">Forecast</th><th class="n">80% low</th><th class="n">80% high</th><th class="n">Same month LY</th><th class="n">vs LY</th><th class="n">Visits</th></tr></thead><tbody>${fut.map(r=>{ const l=A[String(ymNext(+r[1],-12))]; return `<tr><td>${ym2lab(r[1])}</td><td class="n"><b>${nfmt(r[2])}</b></td><td class="n">${nfmt(r[3])}</td><td class="n">${nfmt(r[4])}</td><td class="n">${l?nfmt(l[0]):'—'}</td><td class="n">${l?pct(r[2]/l[0]-1):'—'}</td><td class="n">${r[7]?nfmt(r[7]):'—'}</td></tr>`; }).join('')}</tbody></table></div>`;
      const regs = st.br==='ALL' && st.k!=='total' ? [keyOf('ALL',st.k)] : st.k==='total' ? (st.br==='ALL' ? ['ALL|total'] : [`${st.br}|cash`,`${st.br}|credit`]) : [keyOf(st.br,st.k)];
      cm.innerHTML = `<h3>Model card</h3><p class="card-sub">بطاقة النموذج · chosen by back-test, not just by fit</p>` + regs.map(k=>{ const r = F.reg[k]; if(!r) return ''; return `<div class="fc-mc"><div class="fc-mc-h">${esc(k.replace('ALL','Group').replace('|',' · '))}</div><table class="aud-t"><tbody>
        <tr><td>Model</td><td><code>${esc(r.model)}</code></td></tr>
        <tr><td>1-month-ahead error (last 12 months)</td><td>MAPE ${(r.mape1*100).toFixed(1)}%</td></tr>
        <tr><td>3-month-ahead error</td><td>MAPE ${(r.mape3*100).toFixed(1)}%</td></tr>
        <tr><td>Bias correction</td><td>${r.bias ? `<span class="pill warn">${pct(-r.bias)} applied</span> — last 6 forecasts were consistently ${r.bias>0?'too high':'too low'}` : '<span class="pill ok">none needed</span>'}</td></tr>
        <tr><td>Recent 1-month errors</td><td>${(r.recent_err||[]).map(e=>`<span class="pill ${Math.abs(e)<0.05?'ok':Math.abs(e)<0.1?'warn':'bad'}">${pct(e,0)}</span>`).join(' ')}</td></tr>
        <tr><td>Runners-up (AICc)</td><td class="an-sub">${(r.candidates||[]).slice(1,4).map(c=>`(${c[1].join(',')})(${c[2].slice(0,3).join(',')})12`).join(' · ')}</td></tr></tbody></table></div>`; }).join('');
    }
    let lastCC = TI.cc; TI.on(()=>{ if(TI.cc!==lastCC){ lastCC=TI.cc; st.br=ccInit(); } render(); }); render();
  }

  /* -------------------------------------------------------------- 2 -- */
  const s2 = document.getElementById('sec-fc-var');
  if(s2){
    audHead(s2, 'Forecasting', 'Forecast vs Actual Audit', 'مراجعة الانحراف بين التوقع والفعلي',
      'Every forecast issued is kept in the ledger (<code>forecast_ledger.csv</code>) and never overwritten. Pick how far ahead the forecast was made; each closed month shows the forecast, the actual, the variance in SAR and %, whether the actual landed inside the 80% range, and why — split into visits (volume) and revenue per visit (rate), plus calendar and refund effects.');
    const st = {br: ccInit(), k: 'total', h: 1};
    const bar = el('div','aud-bar'); s2.appendChild(bar);
    const kp = el('div','grid grid-4'); s2.appendChild(kp);
    const cv = el('div','card'); cv.style.marginTop='16px'; s2.appendChild(cv);
    const cl = el('div','card'); cl.style.marginTop='16px'; s2.appendChild(cl);
    s2.appendChild(el('div','note', `<b>How variance is justified.</b> Variance = actual − forecast. Volume effect = (actual visits − forecast visits) × forecast revenue per visit; rate effect = (actual − forecast revenue per visit) × actual visits — the two add up to the variance. Calendar notes compare Ramadan days, Eid holiday days and Fridays with the same month last year; refunds are flagged when they run above 1.3× their 12-month average. Vintages marked <i>back-test</i> were reconstructed on the first run by re-fitting the model on data available at the time; <i>live</i> vintages are the forecasts actually issued each month. <b>Auto-enhance:</b> each monthly run re-selects the model on the latest 12 months of errors and applies a bias correction when the last 6 errors lean the same way.`));
    function render(){
      bar.innerHTML = barHtml('fv', st) + ANM.bar('fv-h','Forecast made',[[1,'1 month ahead'],[2,'2 months ahead'],[3,'3 months ahead'],[6,'6 months ahead'],[12,'12 months ahead']], st.h);
      bar.querySelector('#fv-br').onchange = e => { st.br = e.target.value; render(); };
      bar.querySelector('#fv-k').onchange = e => { st.k = e.target.value; render(); };
      bar.querySelector('#fv-h').onchange = e => { st.h = +e.target.value; render(); };
      const A = actual(st.br, st.k), L = ledger(st.br, st.k), w = audWindow();
      const rows = [];
      for(const r of L){ const t = +r[1], v = +r[0]; if(t > LF) continue; const hh = (Math.floor(t/100)-Math.floor(v/100))*12 + (t%100 - v%100) + 1; if(hh !== st.h) continue; const a = A[r[1]]; if(!a) continue;
        rows.push({v:r[0], t:r[1], f:r[2], lo:r[3], hi:r[4], fe:r[7], kind:r[8], a:a[0], ae:a[1], var:a[0]-r[2], pct:(a[0]-r[2])/r[2], inb: a[0]>=r[3] && a[0]<=r[4]}); }
      rows.sort((x,y)=>y.t-x.t);
      const inWin = rows.filter(r => +r.t >= w.a && +r.t <= w.b), use = inWin.length ? inWin : rows;
      const mape = use.length ? use.reduce((s,r)=>s+Math.abs(r.pct),0)/use.length : null, bias = use.length ? use.reduce((s,r)=>s+r.pct,0)/use.length : null;
      const hit = use.length ? use.filter(r=>r.inb).length/use.length : null, sv = use.reduce((s,r)=>s+r.var,0), sf = use.reduce((s,r)=>s+r.f,0);
      kp.innerHTML = kpiTile('Accuracy (MAPE)', mape==null?'—':(mape*100).toFixed(1)+'%', `${use.length} closed months · ${st.h}-month-ahead forecasts${inWin.length?'':' · all months (none in period)'}`)
        + kpiTile('Bias', bias==null?'—':pct(bias), bias==null?'':bias>0?'actuals above forecast on average':'actuals below forecast on average', bias!=null && Math.abs(bias)>0.03)
        + kpiTile('Inside 80% range', hit==null?'—':(hit*100).toFixed(0)+'%', 'a well-calibrated model lands near 80%')
        + kpiTile('Total variance', nfmt(sv), sf ? pct(sv/sf)+' of forecast' : '', sv<0);
      const keyJ = st.br!=='ALL' && st.k==='total' ? null : keyOf(st.br, st.k);
      cv.innerHTML = `<h3>Forecast vs actual by month <span class="tag">${use.length}</span></h3><p class="card-sub">التوقع مقابل الفعلي · ${esc(F.brn[st.br])} · ${KINDS.find(k=>k[0]===st.k)[1]} · forecasts made ${st.h} month${st.h>1?'s':''} before the month</p><div class="aud-scroll" style="max-height:560px"><table class="aud-t"><thead><tr><th>Month</th><th>Issued</th><th class="n">Forecast</th><th class="n">Actual</th><th class="n">Variance</th><th class="n">Var %</th><th>80% range</th><th>Why</th></tr></thead><tbody>${use.map(r=>{ const j = keyJ ? F.just[`${keyJ}|${r.v}|${r.t}`] : null;
        let why = '';
        if(j){ why = j.parts.map(p=>`<div><b>${p[0]}</b> ${nfmt(p[1])} <span class="an-sub">${esc(p[2])}</span></div>`).join('') + (j.notes.length?`<div class="an-sub">${j.notes.map(esc).join(' · ')}</div>`:''); }
        else if(r.fe && r.ae){ const rf=r.f/r.fe, ra=r.a/r.ae; why = `<div><b>Visits</b> ${nfmt((r.ae-r.fe)*rf)}</div><div><b>Revenue per visit</b> ${nfmt((ra-rf)*r.ae)}</div>`; }
        return `<tr><td>${ym2lab(r.t)}</td><td>${ym2lab(r.v)}<div class="an-sub">${r.kind}</div></td><td class="n">${nfmt(r.f)}</td><td class="n">${nfmt(r.a)}</td><td class="n ${r.var<0?'neg':''}">${nfmt(r.var)}</td><td class="n"><span class="pill ${Math.abs(r.pct)<0.05?'ok':Math.abs(r.pct)<0.1?'warn':'bad'}">${pct(r.pct)}</span></td><td>${r.inb?'<span class="pill ok">Inside</span>':'<span class="pill bad">Outside</span>'}</td><td class="fc-why">${why}</td></tr>`; }).join('') || '<tr><td colspan="8" class="an-empty">No closed months for this horizon yet.</td></tr>'}</tbody></table></div>`;
      // model log
      const regs = Object.entries(F.reg).filter(([k]) => st.br==='ALL' ? k.startsWith('ALL') : k.startsWith(st.br+'|'));
      cl.innerHTML = `<h3>Model log</h3><p class="card-sub">سجل النماذج · model chosen at this run and its back-test error; each monthly run adds a row per series so improvements (or drift) stay visible</p><table class="aud-t"><thead><tr><th>Run</th><th>Series</th><th>Model</th><th class="n">MAPE 1m</th><th class="n">MAPE 3m</th><th class="n">Bias correction</th></tr></thead><tbody>${regs.map(([k,r])=>`<tr><td>${esc(F.run)}</td><td>${esc(k.replace('ALL','Group').replace('|',' · '))}</td><td><code>${esc(r.model)}</code></td><td class="n">${(r.mape1*100).toFixed(1)}%</td><td class="n">${(r.mape3*100).toFixed(1)}%</td><td class="n">${r.bias?pct(-r.bias):'—'}</td></tr>`).join('')}</tbody></table>`;
    }
    let lastCC = TI.cc; TI.on(()=>{ if(TI.cc!==lastCC){ lastCC=TI.cc; st.br=ccInit(); } render(); }); render();
  }
})();
