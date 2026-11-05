/* ---- Cash Flow · Direct (voucher level) ---- */
(function(){
  const sec = document.getElementById('sec-cashflow-direct');
  const D = DATA.cfd; if(!sec || !D) return;
  const YS = D.years, lastY = YS[YS.length-1];
  const f0 = v => (v === null || v === undefined || Math.abs(v) < 0.005) ? '—' : nfmt(v);
  const CAT = {CFO:['Cash flows from operating activities','التدفقات النقدية من الأنشطة التشغيلية','Net cash from operating activities','صافي التدفق النقدي من التشغيل'],
               CFI:['Cash flows from investing activities','التدفقات النقدية من الأنشطة الاستثمارية','Net cash from investing activities','صافي التدفق النقدي من الاستثمار'],
               CFF:['Cash flows from financing activities','التدفقات النقدية من الأنشطة التمويلية','Net cash from financing activities','صافي التدفق النقدي من التمويل']};
  const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const st = {view:'year', y:lastY, line:null, dy:lastY};
  const cols = () => st.view === 'year' ? YS.map(y => ({k:String(y), lab:'FY '+y+(y===lastY?' YTD':'')}))
                                        : MON.map((m,i) => ({k:st.y+String(i+1).padStart(2,'0'), lab:m+' '+String(st.y).slice(2)})).filter(c => Object.values(D.mon).some(s => s[c.k] !== undefined));
  const lineVal = (l, k) => { const s = D.mon[l] || {}; if(k.length === 6) return s[k] || 0; let t = 0; for(const ym in s) if(ym.slice(0,4) === k) t += s[ym]; return t; };
  const catVal = (c, k) => D.lines.filter(l => l[0] === c).reduce((t,l) => t + lineVal(l[1], k), 0);
  const openAt = k => { if(k.length === 4) return D.recon[k].open; const y = k.slice(0,4); let t = D.recon[y].open; for(const l of D.lines) for(const ym in (D.mon[l[1]]||{})) if(ym.slice(0,4)===y && ym < k) t += D.mon[l[1]][ym]; return t; };
  const R = D.recon[lastY];

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Statements</div>
    <h2>Cash Flow · Direct <span style="font-family:'IBM Plex Sans',sans-serif;font-size:17px;color:var(--ink-muted);font-weight:500">· التدفقات النقدية بالطريقة المباشرة — على مستوى القيد</span></h2>
    <p>Every voucher that touches a cash or bank account (121x, 122x — boxes, banks, card networks and visa, overdrafts included) is read from the four EXSYS ledgers as one company. The cash it moved is split over the voucher's other lines: loans, dividends and equity take their full amount, the rest goes pro rata to the lines on the other side of the cash. Transfers between cash accounts net to zero and drop out. Nothing is estimated and nothing is plugged — the statement closes to the ledger cash every month.</p>`));

  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const ties = YS.filter(y => Math.abs(D.recon[y].close - D.recon[y].bs) < 1 && Math.abs(D.recon[y].dir[0] - D.recon[y].ind[0] - (D.recon[y].nc_pure[0]+D.recon[y].nc_pure[1]+D.recon[y].nc_mixed[0]+D.recon[y].nc_mixed[1])) < 1).length;
  kp.innerHTML = kpiTile('Operating cash ' + lastY + ' YTD', nfmt(R.dir[0]), 'receipts less payments, from the vouchers', R.dir[0] < 0)
    + kpiTile('Investing · Financing', nfmt(R.dir[1]) + ' · ' + nfmt(R.dir[2]), 'cash only — non-cash entries listed below')
    + kpiTile('Closing cash ' + lastY, nfmt(R.close), `ledger cash & bank, all four databases · to ${D.asOf}`, R.close < 0)
    + kpiTile('Years that reconcile', ties + ' / ' + YS.length, 'closing = balance sheet · direct = indirect', ties < YS.length);

  /* ---------- statement ---------- */
  const cSt = el('div','card'); cSt.style.marginTop = '16px'; sec.appendChild(cSt);
  const cDet = el('div','card'); cDet.style.marginTop = '16px'; cDet.hidden = true; sec.appendChild(cDet);
  function drawSt(){
    const C = cols();
    let h = `<div class="cfd-bar"><div><h3 style="margin:0">Statement of cash flows — direct method</h3><p class="card-sub" style="margin:2px 0 0">SAR · click a line for its accounts, insurers and vouchers</p></div>
      <div class="cfd-ctl"><div class="nph-seg"><button type="button" data-v="year" class="${st.view==='year'?'on':''}">Years</button><button type="button" data-v="month" class="${st.view==='month'?'on':''}">Months</button></div>
      ${st.view==='month' ? `<select id="cfd-y" aria-label="Year">${YS.map(y=>`<option value="${y}" ${y==st.y?'selected':''}>${y}</option>`).join('')}</select>` : ''}</div></div>
      <div class="aud-x"><table class="aud-t cfa-t cfa-st cfd-t"><thead><tr><th>&nbsp;</th>${C.map(c=>`<th class="n">${c.lab}</th>`).join('')}</tr></thead><tbody>`;
    ['CFO','CFI','CFF'].forEach(cat => {
      h += `<tr class="cfa-h"><td colspan="${C.length+1}">${CAT[cat][0]}<span class="cfa-ar">${CAT[cat][1]}</span></td></tr>`;
      D.lines.filter(l => l[0] === cat).forEach(l => {
        const vals = C.map(c => lineVal(l[1], c.k));
        if(vals.every(v => Math.abs(v) < 0.005)) return;
        h += `<tr class="cfd-row ${st.line===l[1]?'pin':''}" data-l="${l[1]}"><td>${l[2]}<span class="cfa-ar">${l[3]}</span></td>${vals.map(v=>`<td class="n ${v<0?'neg':''}">${f0(v)}</td>`).join('')}</tr>`;
      });
      h += `<tr class="cfa-sub"><td>${CAT[cat][2]}<span class="cfa-ar">${CAT[cat][3]}</span></td>${C.map(c=>{const v=catVal(cat,c.k);return `<td class="n ${v<0?'neg':''}">${f0(v)}</td>`;}).join('')}</tr>`;
    });
    const net = c => catVal('CFO',c.k)+catVal('CFI',c.k)+catVal('CFF',c.k);
    h += `<tr class="cfa-sub"><td>Net change in cash and cash equivalents<span class="cfa-ar">صافي التغير في النقد وما يعادله</span></td>${C.map(c=>`<td class="n">${f0(net(c))}</td>`).join('')}</tr>
      <tr><td>Cash and cash equivalents at the start<span class="cfa-ar">النقد وما يعادله في أول الفترة</span></td>${C.map(c=>`<td class="n">${f0(openAt(c.k))}</td>`).join('')}</tr>
      <tr class="cfa-tot"><td>Cash and cash equivalents at the end<span class="cfa-ar">النقد وما يعادله في آخر الفترة</span></td>${C.map(c=>`<td class="n">${f0(openAt(c.k)+net(c))}</td>`).join('')}</tr>
      </tbody></table></div>`;
    cSt.innerHTML = h;
    cSt.querySelectorAll('.nph-seg button').forEach(b => b.onclick = () => { st.view = b.dataset.v; drawSt(); });
    const ys = cSt.querySelector('#cfd-y'); if(ys) ys.onchange = () => { st.y = +ys.value; drawSt(); };
    cSt.querySelectorAll('.cfd-row').forEach(r => r.onclick = () => { st.line = st.line === r.dataset.l ? null : r.dataset.l; drawSt(); drawDet(); });
  }
  function drawDet(){
    const l = D.lines.find(x => x[1] === st.line);
    if(!l){ cDet.hidden = true; return; }
    cDet.hidden = false;
    const A = D.acc[l[1]] || {};
    const accs = Object.keys(A).sort((a,b) => Math.abs(Object.values(A[b]).reduce((x,y)=>x+y,0)) - Math.abs(Object.values(A[a]).reduce((x,y)=>x+y,0)));
    let h = `<h3>${l[2]} <span class="cfa-ar2">${l[3]}</span></h3><p class="card-sub">Accounts on the other side of the cash · SAR by year</p>
      <div class="aud-scroll" style="max-height:320px"><table class="aud-t cfa-t"><thead><tr><th>Account</th>${YS.map(y=>`<th class="n">FY ${y}</th>`).join('')}</tr></thead><tbody>`;
    accs.forEach(a => { h += `<tr><td><b>${a}</b> <span class="cfa-ar">${esc(D.names[a]||'')}</span></td>${YS.map(y=>{const v=(A[a]||{})[y]||0;return `<td class="n ${v<0?'neg':''}">${f0(v)}</td>`;}).join('')}</tr>`; });
    h += `</tbody></table></div>`;
    if(l[1] === 'r_ins'){
      h += `<h4 style="margin:16px 0 6px">Receipts from insurance companies — by company (sub-account of 1240007)</h4>
        <div class="aud-scroll" style="max-height:360px"><table class="aud-t cfa-t"><thead><tr><th>Insurer</th>${YS.map(y=>`<th class="n">FY ${y}</th>`).join('')}<th class="n">Total</th></tr></thead><tbody>`;
      D.ins.forEach(([sub, nm, v]) => { const t = Object.values(v).reduce((x,y)=>x+y,0); if(Math.abs(t) < 1) return;
        h += `<tr><td><span dir="rtl">${esc(nm)}</span> <span class="cfa-ar2">${sub}</span></td>${YS.map(y=>{const x=v[y]||0;return `<td class="n ${x<0?'neg':''}">${f0(x)}</td>`;}).join('')}<td class="n"><b>${nfmt(t)}</b></td></tr>`; });
      h += `<tr class="cfa-sub"><td>Total</td>${YS.map(y=>`<td class="n">${f0(D.ins.reduce((x,r)=>x+(r[2][y]||0),0))}</td>`).join('')}<td></td></tr></tbody></table></div>`;
    }
    const V = (D.vch[l[1]] || {});
    h += `<h4 style="margin:16px 0 6px;display:flex;gap:10px;align-items:center">Largest vouchers <select id="cfd-dy" aria-label="Year">${YS.map(y=>`<option value="${y}" ${y==st.dy?'selected':''}>${y}</option>`).join('')}</select></h4>
      <div class="aud-scroll" style="max-height:360px"><table class="aud-t cfa-t"><thead><tr><th>Date</th><th>Voucher</th><th>Description</th><th class="n">Cash</th></tr></thead><tbody>`;
    const rows = V[st.dy] || [];
    rows.forEach(([v, d, x, ds]) => { h += `<tr><td class="nw">${d}</td><td class="nw">${esc(v)}</td><td dir="rtl" class="ar">${esc(ds||'')}</td><td class="n ${x<0?'neg':''}">${nfmt(x)}</td></tr>`; });
    if(!rows.length) h += `<tr><td colspan="4" class="sm">No single voucher of SAR 20,000 or more on this line in ${st.dy}.</td></tr>`;
    h += `</tbody></table></div><p class="card-sub" style="margin-top:6px">Vouchers whose cash on this line is SAR 20,000 or more, top 40 by size.</p>`;
    cDet.innerHTML = h;
    cDet.querySelector('#cfd-dy').onchange = e => { st.dy = +e.target.value; drawDet(); };
  }
  drawSt();

  /* ---------- reconciliation ---------- */
  const cRec = el('div','card'); cRec.style.marginTop = '16px'; sec.appendChild(cRec);
  let r = `<h3>Reconciliation</h3><p class="card-sub">المطابقات · the statement is accepted only when every column below is zero</p>
    <div class="aud-x"><table class="aud-t cfa-t"><thead><tr><th>&nbsp;</th>${YS.map(y=>`<th class="n">FY ${y}${y===lastY?' YTD':''}</th>`).join('')}</tr></thead><tbody>`;
  const row = (en, ar, fn, cls) => r += `<tr class="${cls||''}"><td>${en}<span class="cfa-ar">${ar}</span></td>${YS.map(y=>{const v=fn(D.recon[y]);return `<td class="n ${v<0?'neg':''}">${f0(v)}</td>`;}).join('')}</tr>`;
  r += `<tr class="cfa-s"><td colspan="${YS.length+1}">1 · Cash moved = cash in the ledger</td></tr>`;
  row('Opening cash (ledger)','رصيد أول المدة', x => x.open);
  row('Net change per direct method','صافي التغير بالطريقة المباشرة', x => x.dir[0]+x.dir[1]+x.dir[2]);
  row('Closing cash per statement','رصيد آخر المدة حسب القائمة', x => x.open+x.dir[0]+x.dir[1]+x.dir[2], 'cfa-sub');
  row('Cash per balance sheet (indirect statement)','النقدية في الميزانية', x => x.bs);
  row('Difference','الفرق', x => Math.abs(x.open+x.dir[0]+x.dir[1]+x.dir[2]-x.bs) < 0.5 ? 0 : x.open+x.dir[0]+x.dir[1]+x.dir[2]-x.bs, 'cfa-tot');
  r += `<tr class="cfa-s"><td colspan="${YS.length+1}">2 · Direct against indirect — operating activities</td></tr>`;
  row('Operating cash — indirect, balance-movement basis','التشغيل — الطريقة غير المباشرة قبل الاستبعاد', x => x.ind[0]);
  row('Non-cash entries removed — whole vouchers with no cash','استبعاد قيود غير نقدية بالكامل', x => x.nc_pure[0]+x.nc_pure[1]);
  row('Non-cash part of vouchers that also moved cash (assets partly on credit)','استبعاد الجزء غير النقدي من قيود نقدية', x => x.nc_mixed[0]+x.nc_mixed[1]);
  row('Operating cash — indirect, non-cash removed','التشغيل — غير المباشرة بعد الاستبعاد', x => x.ind[0]+x.nc_pure[0]+x.nc_pure[1]+x.nc_mixed[0]+x.nc_mixed[1], 'cfa-sub');
  row('Operating cash — direct method','التشغيل — الطريقة المباشرة', x => x.dir[0]);
  row('Difference','الفرق', x => { const d = x.dir[0]-(x.ind[0]+x.nc_pure[0]+x.nc_pure[1]+x.nc_mixed[0]+x.nc_mixed[1]); return Math.abs(d)<0.5?0:d; }, 'cfa-tot');
  r += `<tr class="cfa-s"><td colspan="${YS.length+1}">3 · Investing and financing are the same cash in both methods</td></tr>`;
  row('Investing — direct','الاستثمار — المباشرة', x => x.dir[1]);
  row('Financing — direct','التمويل — المباشرة', x => x.dir[2]);
  row('Largest monthly gap between allocated cash and ledger cash','أكبر فرق شهري بين التوزيع وحركة النقدية', x => x.chk1 < 0.5 ? 0 : x.chk1);
  r += `</tbody></table></div>`;
  cRec.innerHTML = r;

  /* ---------- bank & cash accounts ---------- */
  const cBk = el('div','card'); cBk.style.marginTop = '16px'; sec.appendChild(cBk);
  const B = D.banks, bk = D.bank1224005;
  let b = `<h3>Cash and bank accounts — year-end balances</h3>
    <p class="card-sub">أرصدة الحسابات النقدية والبنكية · the four databases added together — each bank account is shared, so a branch's own balance is meaningless on its own</p>
    <div class="aud-x"><table class="aud-t cfa-t"><thead><tr><th>Account</th>${YS.map(y=>`<th class="n">${y}${y===lastY?' YTD':''}</th>`).join('')}</tr></thead><tbody>`;
  Object.entries(B).forEach(([a,[nm,v]]) => { b += `<tr><td><b>${a}</b><span class="cfa-ar">${esc(nm)}</span></td>${v.map(x=>`<td class="n ${x<-0.5?'neg':''}">${f0(x)}</td>`).join('')}</tr>`; });
  b += `<tr class="cfa-tot"><td>Total cash and cash equivalents</td>${YS.map((y,i)=>`<td class="n">${f0(Object.values(B).reduce((t,[n,v])=>t+v[i],0))}</td>`).join('')}</tr></tbody></table></div>
    <div class="note" style="margin-top:12px"><b>Book balance, not bank balance.</b> On ${bk.date} the bank statement of account 56000001453104 showed <b>${nfmt(bk.bank,2)}</b> while the ledger (1224005) showed <b>${nfmt(bk.gl)}</b>. The gap is insurance transfers received but not yet booked because the payment details have not arrived. This statement follows the books; a negative bank balance above is that backlog, not an overdraft. Planned fix: book unidentified transfers to a clearing account so the bank ties, then reclass to the customer when the details arrive.</div>`;
  cBk.innerHTML = b;

  /* ---------- non-cash disclosure ---------- */
  window.__ncCard(sec, D.nc, YS, lastY);

  sec.appendChild(el('div','note', `<b>Source.</b> EXSYS ledger, all four databases read through Cure as one company, vouchers dated up to ${D.asOf}: <code>GL_TRANSACTIONS_DETAILS</code> (open and posted, cancelled excluded). Cash and cash equivalents = accounts 121x and 122x. Line mapping follows the chart of accounts: sales-control accounts 13xx/14xx = patients, 1240007 = insurance companies, 2121x/319x/2111x = employees, 2122x = suppliers, 1263000/2123007x = VAT, 2123003 = zakat, 2126x/1246x = owner and related parties, 11x/113x = property and projects, 2112x/2113x/1262000/3290001 = loans, 2128x = dividends. Nothing on this page comes from Power BI.`));
})();
