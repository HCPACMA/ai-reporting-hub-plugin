/* ---- Cash Flow (audited) ---- */
window.__ncCard = function(sec, NC, YS, lastY){
  const f0 = v => (v === null || v === undefined || Math.abs(v) < 0.005) ? '—' : nfmt(v);
  const card = el('div','card'); card.style.marginTop='16px'; sec.appendChild(card);
  const kinds = {}; NC.forEach(r => { (kinds[r.k] = kinds[r.k] || {en:r.en, ar:r.ar, y:{}}); kinds[r.k].y[r.y] = (kinds[r.k].y[r.y]||0) + r.amt; });
  let h = `<h3>Non-cash investing and financing transactions <span class="tag">${NC.length}</span></h3>
    <p class="card-sub">بيان المعاملات غير النقدية · IAS 7.43 — excluded from the statement above because no cash moved; listed so the reader sees them. Amounts: for assets and equity entries, what the balance-movement method used to count as investing or financing cash (+ = inflow it would have shown); for dividends, the amount declared and still payable.</p>
    <div class="aud-x"><table class="aud-t cfa-t"><thead><tr><th>Type</th>${YS.map(y=>`<th class="n">FY ${y}${y===lastY?' YTD':''}</th>`).join('')}</tr></thead><tbody>`;
  Object.values(kinds).forEach(k => { h += `<tr><td>${k.en}<span class="cfa-ar">${k.ar}</span></td>${YS.map(y=>`<td class="n ${(k.y[y]||0)<0?'neg':''}">${f0(k.y[y])}</td>`).join('')}</tr>`; });
  h += `</tbody></table></div>
    <div class="aud-scroll" style="max-height:380px;margin-top:12px"><table class="aud-t cfa-t cfd-nc"><thead><tr><th>Date</th><th>Voucher</th><th>Type</th><th>Description</th><th class="n">Amount</th></tr></thead><tbody>`;
  NC.slice().sort((a,b)=>Math.abs(b.amt)-Math.abs(a.amt)).forEach(r => {
    h += `<tr><td class="nw">${r.d}</td><td class="nw">${esc(r.v)}</td><td>${r.en}${r.full!==undefined?`<span class="cfa-ar2" style="display:block">cost ${nfmt(r.full)} · cash ${nfmt(r.cash)}</span>`:''}</td><td dir="rtl" class="ar">${esc(r.ds||'')}</td><td class="n ${r.amt<0?'neg':''}">${nfmt(r.amt)}</td></tr>`;
  });
  h += `</tbody></table></div><p class="card-sub" style="margin-top:8px">Items of SAR 10,000 or more are listed; smaller ones are inside the yearly totals of the reconciliation line.</p>`;
  card.innerHTML = h;
};
(function(){
  const sec = document.getElementById('sec-cashflow');
  const C = DATA.cfa; if(!sec || !C) return;
  const YS = C.years;
  const f0 = v => (v === null || v === undefined || Math.abs(v) < 0.005) ? '—' : nfmt(v);
  const val = (y, spec) => {
    const v = C.v[y];
    if(spec === null) return null;
    if(typeof spec === 'string') return v[spec];
    let t = 0, any = false;
    spec.forEach(o => { const x = v['o'+o]; if(x !== undefined){ t += x; any = true; } });
    return any ? t : null;
  };
  const lastY = YS[YS.length-1];
  const eqYears = YS.filter(y => Math.abs(C.eq[y]) > 100);
  const resid = y => C.audit.reduce((x,r)=>x+r.y[y][2],0);
  const broken = YS.filter(y => Math.abs(resid(y)) > 0.5 || Math.abs(C.v[y].CLOSE - C.bs[y].cash) > 0.5);

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Statements</div>
    <h2>Cash Flow · Indirect — audited <span style="font-family:'IBM Plex Sans',sans-serif;font-size:17px;color:var(--ink-muted);font-weight:500">· قائمة التدفقات النقدية — مدققة</span></h2>
    <p>Built line by line from the journal entries in the four EXSYS ledgers. Each cash-flow line is the movement in the balance-sheet line it stands for, and the audit at the bottom of this page checks every one of those pairs. The statement closes to the balance-sheet cash in every year without a balancing figure. Investing and financing lines are <b>cash only</b>: entries that moved no cash (assets settled against the owner or the related company, assets bought on credit, remeasurements booked to equity) are taken out through one operating line and listed at the bottom (IAS 7.43), so operating cash here equals the voucher-level direct method to the riyal.</p>`));

  /* ---------- tie-out ---------- */
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  kp.innerHTML = kpiTile('Years audited', String(YS.length), `${YS[0]} – ${lastY}, from the ledger`)
    + kpiTile('Years that do not tie', String(broken.length), broken.length ? broken.join(', ') : 'every year closes to the balance sheet', broken.length>0)
    + kpiTile('Operating cash ' + lastY + ' YTD', nfmt(C.v[lastY].CFO), `against net income of ${nfmt(C.v[lastY].o1)}`, C.v[lastY].CFO < C.v[lastY].o1)
    + kpiTile('Closing cash ' + lastY, nfmt(C.bs[lastY].cash), 'cash and bank per the ledger, net of overdrawn accounts', C.bs[lastY].cash < 0);

  const cTie = el('div','card'); cTie.style.marginTop='16px'; sec.appendChild(cTie);
  let h = `<h3>Tie-out — closing cash against the balance sheet</h3>
    <p class="card-sub">التحقق من تطابق رصيد النقد في نهاية الفترة مع الميزانية · the test the statement has to pass</p>
    <div class="aud-x"><table class="aud-t cfa-t"><thead><tr><th>Year</th><th class="n">Opening cash</th><th class="n">Operating</th><th class="n">Investing</th><th class="n">Financing</th><th class="n">Net change</th><th class="n">Closing per statement</th><th class="n">Cash per balance sheet</th><th class="n">Variance</th><th class="n">Operating per direct method</th><th>Status</th></tr></thead><tbody>`;
  YS.forEach(y => {
    const v = C.v[y], b = C.bs[y];
    const d = v.CLOSE - b.cash;
    h += `<tr><td><b>FY ${y}${y===lastY?' YTD':''}</b></td><td class="n">${f0(v.OPEN)}</td><td class="n">${f0(v.CFO)}</td><td class="n">${f0(v.CFI)}</td>
      <td class="n">${f0(v.CFF)}</td><td class="n">${f0(v.NET)}</td><td class="n"><b>${f0(v.CLOSE)}</b></td><td class="n">${f0(b.cash)}</td>
      <td class="n ${Math.abs(d)>0.5?'neg':''}">${Math.abs(d)<0.5?'0':nfmt(d,2)}</td>
      <td class="n">${DATA.cfd && DATA.cfd.recon[y] ? f0(DATA.cfd.recon[y].dir[0]) : '—'}</td>
      <td>${Math.abs(d)<0.5 && (!DATA.cfd || !DATA.cfd.recon[y] || Math.abs(DATA.cfd.recon[y].dir[0]-v.CFO)<1)?'<span class="pill ok">Ties</span>':'<span class="pill bad">Breaks</span>'}</td></tr>`;
  });
  h += `</tbody></table></div>`;
  cTie.innerHTML = h;

  /* ---------- the statement ---------- */
  const cSt = el('div','card'); cSt.style.marginTop='16px'; sec.appendChild(cSt);
  let s = `<h3>Statement of cash flows</h3><p class="card-sub">Indirect method · SAR · ${YS[0]}–${lastY}. FY${lastY} runs to the last voucher posted in the ledger (read ${C.asOf}).</p>
    <div class="aud-x"><table class="aud-t cfa-t cfa-st"><thead><tr><th>&nbsp;</th>${YS.map(y=>`<th class="n">FY ${y}</th>`).join('')}</tr></thead><tbody>`;
  C.layout.forEach(([kind, en, ar, spec]) => {
    if(kind === 'h'){ s += `<tr class="cfa-h"><td colspan="${YS.length+1}">${en}<span class="cfa-ar">${ar}</span></td></tr>`; return; }
    if(kind === 's'){ s += `<tr class="cfa-s"><td colspan="${YS.length+1}">${en} <span class="cfa-ar2">${ar}</span></td></tr>`; return; }
    const vals = YS.map(y => val(y, spec));
    if(kind === 'l' && vals.every(v => v === null || Math.abs(v) < 0.005)) return;     // line never used
    const cls = kind === 'T' ? 'cfa-tot' : kind === 't' ? 'cfa-sub' : (spec === 'EQ' ? 'cfa-fix' : '');
    s += `<tr class="${cls}"><td>${en}<span class="cfa-ar">${ar}</span></td>`
       + vals.map(v => `<td class="n ${v<0?'neg':''}">${f0(v)}</td>`).join('') + `</tr>`;
  });
  s += `</tbody></table></div>
    <div class="note" style="margin-top:14px"><b>Non-cash entries removed.</b> The indirect method reads balance movements, so it used to report entries that moved no cash as investing or financing cash — e.g. FY2019 assets of 3.84M moved to the related company and FY2023 land of 4.58M moved from the owner's account. Those amounts are now reversed out through the line <i>Non-cash investing &amp; financing entries removed</i> and listed below; the investing and financing sections show the cash the vouchers actually moved.</div>`;
  cSt.innerHTML = s;
  if(C.nc && C.nc.length) window.__ncCard(sec, C.nc, YS, lastY);

  /* ---------- line-by-line audit ---------- */
  const cAud = el('div','card'); cAud.style.marginTop='16px'; sec.appendChild(cAud);
  let a = `<h3>Line-by-line audit</h3>
    <p class="card-sub">For every balance-sheet line: the movement in the balance itself against the accrual-based cash-flow lines it stands for, before the non-cash entries are removed. A non-zero residual is cash the statement cannot account for.</p>
    <div class="aud-x"><table class="aud-t cfa-t cfa-aud"><thead><tr><th rowspan="2">Balance-sheet line</th>${YS.map(y=>`<th class="n" colspan="3">FY ${y}</th>`).join('')}</tr>
    <tr>${YS.map(()=>'<th class="n sm">Δ balance</th><th class="n sm">per cash flow</th><th class="n sm">residual</th>').join('')}</tr></thead><tbody>`;
  C.audit.forEach(r => {
    a += `<tr><td>${r.en}<span class="cfa-ar">${r.ar}</span></td>`;
    YS.forEach(y => {
      const [bsv, cfv, res] = r.y[y];
      const bad = Math.abs(res) > 0.5;
      a += `<td class="n sm">${f0(bsv)}</td><td class="n sm">${f0(cfv)}</td><td class="n sm ${bad?'cfa-bad':''}">${bad?nfmt(res):'0'}</td>`;
    });
    a += `</tr>`;
  });
  a += `<tr class="cfa-tot"><td>Residual — cash unaccounted for</td>`;
  YS.forEach(y => { const t = resid(y); a += `<td class="n sm" colspan="3">${Math.abs(t)<0.5?'0':nfmt(t)}</td>`; });
  a += `</tr></tbody></table></div>`;
  cAud.innerHTML = a;

  /* ---------- findings ---------- */
  const v = C.v[lastY], vp = C.v[lastY-1];
  const wc = ['o15','o16','o17','o18','o19','o20','o21','o22','o26','o27'].reduce((x,k)=>x+(v[k]||0),0);
  const cFind = el('div','card'); cFind.style.marginTop='16px'; sec.appendChild(cFind);
  cFind.innerHTML = `<h3>What the audit found</h3>
    <p class="card-sub">In the order they matter</p>
    <ol class="cfa-find">
      <li><b>${lastY} profit is not turning into cash.</b> Net income to date is <b>${nfmt(v.o1)}</b>; cash from operations is <b>${nfmt(v.CFO)}</b>. Working capital absorbed <b>${nfmt(-wc)}</b>, and most of it is receivables: receivables alone took <b>${nfmt(-v.o15)}</b>. That is where the cash went, and it is the number to chase before the year closes.</li>
      <li><b>Cash has gone negative.</b> The group opened ${lastY} with <b>${nfmt(v.OPEN)}</b> and stands at <b>${nfmt(C.bs[lastY].cash)}</b>, after <b>${nfmt(-v.o31)}</b> of spending on assets in progress and <b>${nfmt(-(v.o34||0))}</b> of loan repayments. A negative consolidated cash balance means at least one bank account is overdrawn in the ledger — confirm against the bank statements.</li>
      ${C.open_vouchers ? `<li><b>${C.open_vouchers.n} vouchers dated ${lastY} are still open (not posted).</b> Together they move cash by <b>${nfmt(C.open_vouchers.cash)}</b> — Riyadh's ${C.open_vouchers.by.Riyadh[0]} open vouchers alone take out <b>${nfmt(-C.open_vouchers.by.Riyadh[1])}</b>. This statement and the period strip both include them. Posting or cancelling these vouchers is the first step of the month-end close.</li>` : ''}
      <li><b>Every balance-sheet line is accounted for.</b> Receivables, related parties, inventory, provisions, fixed assets, loans, zakat and equity each pair to their cash-flow lines with a nil residual in all ${YS.length} years. Depreciation charged equals the credit to accumulated depreciation every year, so no depreciation is sitting outside the fixed-asset accounts.</li>
      <li><b>The ${lastY} year is not complete.</b> So far this year the end-of-service charge is <b>${nfmt(v.o11)}</b> and the doubtful-debt charge <b>${nfmt(v.o8)}</b>, against <b>${nfmt(vp.o11)}</b> and <b>${nfmt(vp.o8)}</b> for all of ${lastY-1}. Both are booked at year end, so ${lastY} profit is overstated until they are. Operating cash is not affected — both are non-cash charges.</li>
    </ol>`;

  sec.appendChild(el('div','note', `<b>Source.</b> EXSYS ledger, all four databases (Riyadh, Buraydah 1, Buraydah 2, Rafha), read ${C.asOf} through the Cure connection: <code>GL_TRANSACTIONS_DETAILS</code> net movements by account and year, plus debit and credit totals for fixed assets, accumulated depreciation, assets in progress, loans, deferred interest, dividends payable and the provision accounts; <code>ACCOUNTS</code> for classification. Cancelled vouchers, the year-end closing vouchers (<code>FINANCIAL_YEARS.GL_VOUCHER_NO</code>) and JV1-24/04043 are excluded. Nothing on this page comes from Power BI.`));
})();