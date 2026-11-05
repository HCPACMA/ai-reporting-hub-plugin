/* ======================================================================
   NPHIES Invoices · Sehati fees — the monthly NPHIES platform-fee invoices
   (folder PDFs) matched to their ledger booking and payment, and the Rafha
   fee laid against the NPHIES claim activity behind it
   ====================================================================== */
(function(){
  const D = DATA.nphi, sec = document.getElementById('sec-aud-nphi');
  if(!D || !sec) return;
  const n2 = v => (v === null || v === undefined || isNaN(v)) ? '—' : (v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
  const n0 = v => (v === null || v === undefined || isNaN(v)) ? '—' : Math.round(v).toLocaleString('en-US');
  const pc = (v, d=1) => (v === null || v === undefined || isNaN(v)) ? '—' : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toFixed(d) + '%';
  const dmy = d => d ? `${d.slice(8,10)}/${d.slice(5,7)}/${d.slice(0,4)}` : '—';
  const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const ml = ym => ym ? `${MON[+ym.slice(5,7)-1]} ${ym.slice(0,4)}` : '—';
  const BR = {Riyadh:'Riyadh', BUR1:'Buraydah 1', BUR2:'Buraydah 2', Rafha:'Rafha', ALL:'All branches'};
  const BRS = ['Riyadh','BUR1','BUR2','Rafha'];
  const ST = {
    paid:      ['ok',  'Paid',                 'مسددة'],
    unpaid:    ['bad', 'Booked · not paid',    'مقيدة ولم تُسدد'],
    offset:    ['ok',  'Paid · net of credit', 'مسددة بعد خصم إشعار دائن'],
    paid_open: ['warn','Paid · voucher not posted', 'مسددة بقيد مفتوح لم يُرحّل'],
    part:      ['warn','Part paid',            'مسددة جزئياً'],
    over:      ['warn','Paid more than billed','مسدد أكثر من الفاتورة'],
    cancelled: ['',    'Issued twice · credited','صدرت مرتين وأُلغيت بإشعار دائن'],
    credit:    ['',    'Credit note',          'إشعار دائن'] };
  const pill = k => `<span class="pill ${ST[k][0]}" title="${esc(ST[k][2])}">${esc(ST[k][1])}</span>`;
  const FL = {
    pay_open: 'Payment is in an open (not yet posted) voucher — post it to close the item', noinv: 'No invoice number in the narration', paid_no_ref: 'Payment narration has no invoice number — paired by branch, month and amount',
    ap_diff: 'Supplier-account (2122001) credit differs from net + VAT', ap_missing: 'No supplier-account credit carries this invoice number',
    multi_voucher: 'Booked in more than one voucher', vat_rate: 'VAT is not 15% of the net', dup_credit: 'Second copy of the Oct-2023 invoice, cancelled by credit note 402699' };
  const I = D.inv, byNo = {}; I.forEach(x => { if(x.no) byNo[x.no] = x; });
  const A = D.act, byM = {}; A.forEach(r => byM[r.m] = r);

  audHead(sec, 'AR · Accounts Receivable', 'NPHIES Invoices', 'فواتير رسوم نفيس',
    `Every month <b>Sehati</b> (the NPHIES operator) bills each branch a platform fee — one line, <i>“NPHIES Fees &lt;month&gt; · Provider Share”</i>, plus 15% VAT. This tab takes the invoice PDFs saved in <code>${esc(D.folder)}</code>, finds each one in the ledger (accrual and payment, matched on invoice number and amount), lists every Sehati invoice booked since 2023 so gaps and unpaid months stand out, and — for Rafha, the one branch whose NPHIES claim traffic sits in the database — sets the fee beside the claims sent that month to show what it amounts to per claim and per riyal claimed.`);

  // ---------------------------------------------------------------- KPIs
  const since = '2025-01', lastM = D.months[D.months.length - 1];
  const missing = []; D.months.filter(m => m >= since).forEach(m => BRS.forEach(b => { if(!I.some(x => x.br === b && x.m === m && x.net > 0)) missing.push([b, m]); }));
  const unpaid = I.filter(x => x.st === 'unpaid');
  const pdfOk = D.pdf.filter(p => p.st === 'matched').length;
  const withPdf = I.filter(x => x.pdf).length, billable = I.filter(x => x.net > 0);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  kp.innerHTML = kpiTile('Invoices in the folder', `${pdfOk} / ${D.pdf.length}`, `matched to the ledger · ${withPdf} of ${billable.length} booked invoices have a PDF`)
    + kpiTile('Sehati invoices booked', n0(billable.length), `SAR ${n2(billable.reduce((s,x)=>s+x.tot,0))} incl. VAT · ${ml(billable[0] && billable.map(x=>x.m).sort()[0])} → ${ml(lastM)}`)
    + kpiTile('Sehati supplier balance · S0471', n2(D.sup.P + D.sup.O), `your ledger, 2122001 · S0471: posted ${n2(D.sup.P)}${D.sup.O ? ` + open voucher ${D.sup.openV.join(', ')} ${n2(D.sup.O)}` : ''}`, Math.abs(D.sup.P + D.sup.O) > 1)
    + kpiTile('Months with no invoice in your ledger', n0(missing.length), `since ${ml(since)} · ${missing.slice(-4).map(([b,m])=>`${BR[b]} ${ml(m)}`).join(', ')}`, missing.length > 0);

  // ---------------------------------------------------------------- 1. folder check
  const cPdf = el('div','card'); cPdf.style.marginTop = '16px'; sec.appendChild(cPdf);
  const pdfRows = D.pdf.map(p => { const g = p.gl ? byNo[p.gl] : null;
    const stp = p.st === 'matched' ? '<span class="pill ok">Matched</span>' : p.st === 'mismatch' ? `<span class="pill warn" title="${esc((p.issues||[]).join(', '))}">Differs · ${esc((p.issues||[]).join(', '))}</span>` : '<span class="pill bad">Not in the ledger</span>';
    return `<tr><td>${esc(p.file)}<span class="sm">${esc(p.seller || '—')} · ${esc(p.share || '')} share</span></td>
      <td>${esc(p.no || '—')}<span class="sm">issued ${dmy(p.date)} · due ${dmy(p.due)}</span></td>
      <td>${ml(p.period)}<span class="sm">${esc(p.br_hint ? BR[p.br_hint] || p.br_hint : '—')}</span></td>
      <td class="n">${n2(p.net)}</td><td class="n">${n2(p.vat)}</td><td class="n"><b>${n2(p.tot)}</b></td>
      <td>${g ? g.acc.map(a => `${esc(a[0])}<span class="sm">${dmy(a[1])}</span>`).join('') : '—'}</td>
      <td class="n">${g ? n2(g.tot) : '—'}${g ? `<span class="sm">diff ${n2(p.d_tot)}</span>` : ''}</td>
      <td>${g ? (g.pays.length ? g.pays.map(a => `${esc(a[0])}<span class="sm">${dmy(a[1])}</span>`).join('') : '—') : '—'}${g ? pill(g.st) : ''}</td>
      <td>${stp}</td></tr>`; }).join('');
  const noPdf = billable.filter(x => !x.pdf && x.m >= '2026-01').sort((a,b) => b.m.localeCompare(a.m) || a.br.localeCompare(b.br));
  cPdf.innerHTML = `<h3>Invoice folder check · مطابقة فواتير المجلد</h3>
    <p class="card-sub">Each PDF is read on your computer (invoice no., issue and due dates, service month, net, VAT, total, buyer city) and looked up in the Riyadh ledger, which books the Sehati invoices of all four branches. Matched = same invoice number, same net and total to the halala, same service month and branch.</p>
    <div class="tbl-wrap"><table class="aud-t nphi-t"><thead><tr><th>File</th><th>Invoice</th><th>Service month · branch</th><th class="n">Net</th><th class="n">VAT 15%</th><th class="n">Total</th><th>Accrual voucher</th><th class="n">Ledger total</th><th>Payment</th><th>Result</th></tr></thead><tbody>${pdfRows || '<tr><td colspan="10">No PDFs in the folder.</td></tr>'}</tbody></table></div>
    <details class="nphi-miss"><summary>${noPdf.length} invoice${noPdf.length===1?'':'s'} booked in 2026 have no PDF in the folder yet</summary>
      <div class="nphi-chips">${noPdf.map(x => `<span class="chip" title="${esc(x.acc.map(a=>a[0]).join(', '))}">${esc(BR[x.br])} · ${ml(x.m)} · ${esc(x.no || '—')} · ${n2(x.tot)}</span>`).join('')}</div>
      <p class="hint">Save the missing PDFs into the folder and refresh: each will be read and matched the same way.</p></details>`;

  // ---------------------------------------------------------------- 2. how the Rafha fee relates to NPHIES
  const cCalc = el('div','card'); cCalc.style.marginTop = '16px'; sec.appendChild(cCalc);
  const feeMonths = A.filter(r => r.fee);
  const defM = (D.pdf.find(p => p.br_hint === 'Rafha' && byM[p.period]) || {}).period || feeMonths[feeMonths.length-1].m;
  cCalc.innerHTML = `<h3>Rafha · what the fee amounts to in NPHIES terms · الرسوم مقابل حركة نفيس</h3>
    <p class="card-sub">The invoice carries one line with quantity 1 — Sehati does not print the transaction count, and the tariff (CHI directive PD04-2023) is not stored in the EXSYS database. What the database does hold for Rafha is every claim sent to NPHIES (<code>HS_NPHIES_CLAIM_REQUEST</code>), so the fee can be expressed per accepted claim and as a share of the company amount claimed, and checked against the branch's own history.</p>
    <div class="aud-bar"><div class="f"><label for="nphi-m">Service month</label><select id="nphi-m">${feeMonths.slice().reverse().map(r => `<option value="${r.m}"${r.m===defM?' selected':''}>${ml(r.m)} · invoice ${esc(r.inv)}</option>`).join('')}</select></div></div>
    <div class="nphi-calc" id="nphi-calc"></div>
    <h4 class="nphi-h">Month by month</h4>
    <div class="tbl-wrap"><table class="aud-t nphi-t" id="nphi-hist"></table></div>`;
  const TL = {professional:'Professional (clinics)', pharmacy:'Pharmacy', oral:'Dental'};
  function renderCalc(){
    const m = document.getElementById('nphi-m').value, r = byM[m], inv = I.find(x => x.br === 'Rafha' && x.m === m && x.net > 0);
    const rowsT = Object.keys(TL).map(t => { const x = r.types[t]; const sent = x.complete[0] + x.error[0] + x.other[0];
      return `<tr><td>${TL[t]}</td><td class="n">${n0(sent)}</td><td class="n">${n0(x.complete[0])}</td><td class="n">${n0(x.error[0])}</td><td class="n">${n0(x.other[0])}</td><td class="n">${n2(x.complete[1])}</td><td class="n">${n2(x.complete[2])}</td></tr>`; }).join('');
    const pdf = D.pdf.find(p => p.no === r.inv);
    const band = v => Math.abs(v) <= 15 ? '<span class="pill ok">within ±15%</span>' : '<span class="pill warn">outside ±15% — ask Sehati for the statement</span>';
    document.getElementById('nphi-calc').innerHTML = `
      <div class="nphi-inv">
        <div><span class="lbl">Invoice ${esc(r.inv)}</span><b class="big">SAR ${n2(r.fee)}</b><span class="sm">net · + VAT ${n2(inv ? inv.vat : null)} = ${n2(inv ? inv.tot : null)}</span></div>
        <div><span class="lbl">In the folder</span>${pdf ? `<span class="pill ok">PDF ✓</span><span class="sm">${esc(pdf.file)}</span>` : '<span class="pill">no PDF yet</span>'}</div>
        <div><span class="lbl">Ledger</span>${inv ? inv.acc.map(a => esc(a[0])).join(', ') : '—'}<span class="sm">${inv ? (inv.pays.length ? 'paid ' + inv.pays.map(a => `${esc(a[0])} · ${dmy(a[1])}`).join(', ') : 'not paid yet') : ''}</span></div>
      </div>
      <div class="tbl-wrap"><table class="aud-t nphi-t"><thead><tr><th>Claims sent to NPHIES in ${ml(m)}</th><th class="n">Sent</th><th class="n">Accepted</th><th class="n">Error</th><th class="n">Queued / cancelled</th><th class="n">Company share (accepted)</th><th class="n">Net incl. VAT (accepted)</th></tr></thead>
      <tbody>${rowsT}</tbody><tfoot><tr><td>Total</td><td class="n">${n0(r.sent)}</td><td class="n">${n0(r.acc)}</td><td class="n">${n0(Object.values(r.types).reduce((s,x)=>s+x.error[0],0))}</td><td class="n">${n0(Object.values(r.types).reduce((s,x)=>s+x.other[0],0))}</td><td class="n">${n2(r.co)}</td><td class="n">${n2(r.net)}</td></tr></tfoot></table></div>
      <p class="nphi-also">Other NPHIES messages that month: ${n0(r.elig)} eligibility checks · ${n0(r.pre_complete + r.pre_error + r.pre_cancel + r.pre_other)} prior authorisations · ${n0(r.comm)} communications · ${n0(r.poll)} poll requests.</p>
      <div class="nphi-eq">
        <div class="q"><span class="lbl">Per accepted claim</span><code>${n2(r.fee)} ÷ ${n0(r.acc)}</code><b>= SAR ${r.perClaim.toFixed(4)}</b>
          <span class="sm">Rafha median ${D.medClaim.toFixed(4)} → expected ${n2(r.estClaim)} · difference ${pc(r.vClaim)}</span>${band(r.vClaim)}</div>
        <div class="q"><span class="lbl">Share of company amount claimed</span><code>${n2(r.fee)} ÷ ${n2(r.co)}</code><b>= ${r.pct.toFixed(3)}%</b>
          <span class="sm">Rafha median ${D.medPct.toFixed(3)}% → expected ${n2(r.estPct)} · difference ${pc(r.vPct)}</span>${band(r.vPct)}</div>
      </div>`;
  }
  function renderHist(){
    const rows = A.filter(r => r.fee).map(r => `<tr class="${r.m===document.getElementById('nphi-m').value?'on':''}"><td>${ml(r.m)}<span class="sm">${esc(r.inv)}</span></td><td class="n">${n2(r.fee)}</td><td class="n">${n0(r.sent)}</td><td class="n">${n0(r.acc)}</td><td class="n">${n2(r.co)}</td>
      <td class="n">${r.perClaim.toFixed(3)}</td><td class="n ${Math.abs(r.vClaim)>15?'warn':''}">${pc(r.vClaim)}</td><td class="n">${r.pct.toFixed(3)}%</td><td class="n ${Math.abs(r.vPct)>15?'warn':''}">${pc(r.vPct)}</td></tr>`).join('');
    const open = A.filter(r => !r.fee && r.acc).map(r => `<tr class="est"><td>${ml(r.m)}<span class="sm">not invoiced yet · NPHIES data to ${dmy(D.nphAsOf)}</span></td><td class="n">≈ ${n2(r.estClaim)}</td><td class="n">${n0(r.sent)}</td><td class="n">${n0(r.acc)}</td><td class="n">${n2(r.co)}</td><td class="n" colspan="4">estimate at the median SAR per accepted claim — month still open</td></tr>`).join('');
    document.getElementById('nphi-hist').innerHTML = `<thead><tr><th>Service month</th><th class="n">Fee (net)</th><th class="n">Claims sent</th><th class="n">Accepted</th><th class="n">Company share</th><th class="n">SAR / accepted claim</th><th class="n">vs median</th><th class="n">% of company share</th><th class="n">vs median</th></tr></thead><tbody>${rows}${open}</tbody>`;
  }
  // ---------------------------------------------------------------- 2b. invoice breakdown by NPHIES claims + correctness checks
  const cBd = el('div','card'); cBd.style.marginTop = '16px'; sec.appendChild(cBd);
  const TS = {pr:'Professional', ph:'Pharmacy', or:'Dental'}, OS = {A:'Accepted', E:'Error', O:'Queued / cancelled'};
  const OC = {co:'A', er:'E'};
  const subN = ac => D.subs[ac] || (ac === '-' ? 'No episode invoice' : ac);
  const bd = {m:null, q:'', ac:'', o:'', page:0};
  cBd.innerHTML = `<h3>Invoice breakdown from NPHIES data · تفصيل الفاتورة من بيانات نفيس</h3>
    <p class="card-sub">For the service month picked above: first the checks on the invoice itself, then the claims Rafha sent to NPHIES in that month by insurer, with the fee spread over the accepted claims, and — for invoices whose PDF is in the folder — every claim behind it.</p>
    <div id="nphi-chk" class="nphi-chk"></div>
    <h4 class="nphi-h">By insurer · حسب شركة التأمين</h4>
    <div class="tbl-wrap"><table class="aud-t nphi-t" id="nphi-bi"></table></div>
    <h4 class="nphi-h">Claim by claim · مطالبة بمطالبة</h4>
    <div id="nphi-cl"></div>`;
  function renderBd(){
    const m = document.getElementById('nphi-m').value, r = byM[m], inv = I.find(x => x.br === 'Rafha' && x.m === m && x.net > 0);
    const pdf = D.pdf.find(p => p.no === r.inv), C = D.clm[m];
    if(bd.m !== m){ bd.m = m; bd.q = ''; bd.ac = ''; bd.o = ''; bd.page = 0; }
    // --- checks
    const vatOk = inv && Math.abs(inv.net * 0.15 - inv.vat) < 0.01, totOk = inv && Math.abs(inv.net + inv.vat - inv.tot) < 0.01;
    const pdfOk = pdf ? (pdf.st === 'matched') : null, paid = inv && (inv.st === 'paid' || inv.st === 'offset' || inv.st === 'paid_open');
    const volOk = Math.abs(r.vClaim) <= 15 && Math.abs(r.vPct) <= 15;
    const acc = r.acc, err = Object.values(r.types).reduce((s,x)=>s+x.error[0],0), oth = Object.values(r.types).reduce((s,x)=>s+x.other[0],0);
    const res = C ? C.filter(c => c[12] > 0).length : null, resA = C ? C.filter(c => c[12] > 0 && c[5] === 'co').length : null;
    const svc = C ? Object.entries(C.filter(c => c[5]==='co').reduce((o,c) => (o[c[7]] = (o[c[7]]||0) + 1, o), {})).sort((a,b)=>b[1]-a[1]) : null;
    const ck = (ok, t, d) => `<li class="${ok===null?'na':ok?'ok':'bad'}"><span class="ic">${ok===null?'–':ok?'✓':'✕'}</span><div><b>${t}</b><span class="sm">${d}</span></div></li>`;
    const verdict = (vatOk && totOk && (pdfOk !== false) && volOk) ? `<span class="pill ok">Consistent</span> The invoice adds up, is booked${paid?' and paid':''}, and the fee is in line with Rafha's NPHIES volume for the month.` : `<span class="pill warn">Check</span> At least one check below needs a look.`;
    document.getElementById('nphi-chk').innerHTML = `<p class="nphi-verdict">${verdict} <span class="sm">Exact to the riyal needs Sehati's transaction statement: the tariff and the count they billed are not in the EXSYS database.</span></p><ul class="nphi-cl-list">
      ${ck(vatOk && totOk, 'Invoice arithmetic', inv ? `${n2(inv.net)} × 15% = ${n2(inv.net*0.15)} → VAT ${n2(inv.vat)}; ${n2(inv.net)} + ${n2(inv.vat)} = ${n2(inv.tot)}` : 'not booked')}
      ${ck(pdfOk, 'PDF = ledger', pdf ? `${esc(pdf.file)} · net ${n2(pdf.net)} vs ${n2(inv.net)}, total ${n2(pdf.tot)} vs ${n2(inv.tot)}` : 'no PDF for this month in the folder yet')}
      ${ck(inv ? paid : false, 'Paid to Sehati · your ledger (2122001 · S0471)', inv ? (inv.pays.length ? inv.pays.map(a => `${esc(a[0])} · ${dmy(a[1])}${a[2]==='O'?' (open voucher, not posted)':''}`).join(', ') + ` · SAR ${n2(inv.pay)}` : 'no payment on 2122001 yet') : '—')}
      ${ck(volOk, 'Fee vs NPHIES volume', `SAR ${r.perClaim.toFixed(3)} per accepted claim (${pc(r.vClaim)} vs median) · ${r.pct.toFixed(3)}% of company share (${pc(r.vPct)})`)}
      ${ck(null, 'What was sent', `${n0(r.sent)} claims sent in ${ml(m)}: ${n0(acc)} accepted, ${n0(err)} rejected with an error, ${n0(oth)} queued/cancelled${res!==null?` · ${n0(res)} were re-sends of earlier claims (${n0(resA)} accepted)`:''}${svc?` · accepted claims are for service month${svc.length>1?'s':''} ${svc.map(([k,v])=>`${ml(k)} (${n0(v)})`).join(', ')}`:''}`)}
    </ul>`;
    // --- by insurer
    const rows = D.ins[m] || [], g = {};
    rows.forEach(([ac, t, o, n, co, net]) => { const x = g[ac] = g[ac] || {ac, A:0, E:0, O:0, co:0, net:0, t:{}}; x[o] += n; if(o === 'A'){ x.co += co; x.net += net; x.t[t] = (x.t[t]||0) + n; } });
    const L = Object.values(g).sort((a,b) => b.A - a.A), tA = L.reduce((s,x)=>s+x.A,0);
    const fee = r.fee || 0;
    document.getElementById('nphi-bi').innerHTML = `<thead><tr><th>Insurer (sub-account)</th><th class="n">Sent</th><th class="n">Accepted</th><th class="n">Error</th><th class="n">Queued / cancelled</th><th>Accepted by type</th><th class="n">Company share</th><th class="n">Net incl. VAT</th><th class="n">Fee share (per accepted claim)</th><th class="n">% of fee</th></tr></thead><tbody>
      ${L.map(x => `<tr class="nphi-bi-r" data-ac="${esc(x.ac)}"><td class="ar">${esc(subN(x.ac))}<span class="sm">${esc(x.ac)}</span></td><td class="n">${n0(x.A+x.E+x.O)}</td><td class="n">${n0(x.A)}</td><td class="n">${n0(x.E)}</td><td class="n">${n0(x.O)}</td><td class="sm">${Object.entries(x.t).map(([k,v])=>`${TS[k]||k} ${n0(v)}`).join(' · ')}</td><td class="n">${n2(x.co)}</td><td class="n">${n2(x.net)}</td><td class="n">${n2(tA ? fee * x.A / tA : 0)}</td><td class="n">${tA ? (x.A/tA*100).toFixed(1)+'%' : '—'}</td></tr>`).join('')}</tbody>
      <tfoot><tr><td>Total · ${L.length} insurers</td><td class="n">${n0(L.reduce((s,x)=>s+x.A+x.E+x.O,0))}</td><td class="n">${n0(tA)}</td><td class="n">${n0(L.reduce((s,x)=>s+x.E,0))}</td><td class="n">${n0(L.reduce((s,x)=>s+x.O,0))}</td><td></td><td class="n">${n2(L.reduce((s,x)=>s+x.co,0))}</td><td class="n">${n2(L.reduce((s,x)=>s+x.net,0))}</td><td class="n">${n2(fee)}</td><td class="n">100%</td></tr></tfoot>`;
    document.querySelectorAll('#nphi-bi .nphi-bi-r').forEach(tr => tr.addEventListener('click', () => { if(!C) return; bd.ac = bd.ac === tr.dataset.ac ? '' : tr.dataset.ac; bd.page = 0; renderClaims(); }));
    renderClaims();
  }
  function renderClaims(){
    const m = bd.m, C = D.clm[m], box = document.getElementById('nphi-cl'), r = byM[m];
    if(!C){ box.innerHTML = `<p class="hint">The claim-by-claim list is built for the invoices whose PDF is in the folder (${Object.keys(D.clm).map(ml).join(', ') || 'none yet'}). Save the ${ml(m)} invoice PDF in the folder and refresh to get its list.</p>`; return; }
    const per = r.acc ? r.fee / r.acc : 0;
    const q = bd.q.trim().toLowerCase();
    const F = C.filter(c => (!bd.ac || c[6] === bd.ac) && (!bd.o || (OC[c[5]]||'O') === bd.o) && (!q || c[2].toLowerCase().includes(q) || c[3].includes(q) || String(c[0]).includes(q)));
    const PS = 50, pages = Math.max(1, Math.ceil(F.length / PS)); bd.page = Math.min(bd.page, pages - 1);
    const acs = [...new Set(C.map(c => c[6]))].sort((a,b) => subN(a).localeCompare(subN(b)));
    box.innerHTML = `<div class="aud-bar">
        <div class="f"><label for="nphi-cq">Search</label><input type="search" id="nphi-cq" placeholder="episode invoice, file no. or claim no." value="${esc(bd.q)}"></div>
        <div class="f"><label for="nphi-cac">Insurer</label><select id="nphi-cac"><option value="">All insurers</option>${acs.map(a => `<option value="${esc(a)}"${a===bd.ac?' selected':''}>${esc(subN(a))}</option>`).join('')}</select></div>
        <div class="f"><label for="nphi-co">Outcome</label><select id="nphi-co"><option value="">All</option>${Object.entries(OS).map(([k,v]) => `<option value="${k}"${k===bd.o?' selected':''}>${v}</option>`).join('')}</select></div>
        <button type="button" class="ar-xbtn" id="nphi-csv" hidden>⤓ Download claim list (.csv)</button></div>
      <p class="sm">${n0(F.length)} of ${n0(C.length)} claims · fee spread evenly over the ${n0(r.acc)} accepted claims = SAR ${per.toFixed(4)} each. Patient names are not shown — file numbers only.</p>
      <div class="tbl-wrap"><table class="aud-t nphi-t"><thead><tr><th>Claim no.</th><th>Sent</th><th>Episode invoice</th><th>File no.</th><th>Type</th><th>Outcome</th><th>Insurer</th><th>Service month</th><th class="n">Gross</th><th class="n">Patient share</th><th class="n">Company share</th><th class="n">VAT</th><th class="n">Fee share</th></tr></thead><tbody>
      ${F.slice(bd.page*PS, bd.page*PS + PS).map(c => { const o = OC[c[5]] || 'O'; return `<tr><td>${esc(c[0])}${c[12]>0?`<span class="sm">re-sent ×${c[12]}</span>`:''}</td><td>${dmy(c[1])}</td><td>${esc(c[2])}</td><td>${esc(c[3])}</td><td>${TS[c[4]]||esc(c[4])}</td><td><span class="pill ${o==='A'?'ok':o==='E'?'bad':''}">${OS[o]}</span></td><td class="ar">${esc(subN(c[6]))}</td><td>${ml(c[7])}</td><td class="n">${n2(c[8])}</td><td class="n">${n2(c[9])}</td><td class="n">${n2(c[10])}</td><td class="n">${n2(c[11])}</td><td class="n">${o==='A'?per.toFixed(4):'—'}</td></tr>`; }).join('')}</tbody></table></div>
      <div class="nphi-pg"><button type="button" id="nphi-pp" ${bd.page===0?'disabled':''}>‹ Previous</button><span>Page ${bd.page+1} of ${pages}</span><button type="button" id="nphi-pn" ${bd.page>=pages-1?'disabled':''}>Next ›</button></div>`;
    const q1 = document.getElementById('nphi-cq');
    q1.addEventListener('input', () => { bd.q = q1.value; bd.page = 0; const pos = q1.selectionStart; renderClaims(); const q2 = document.getElementById('nphi-cq'); q2.focus(); q2.setSelectionRange(pos, pos); });
    document.getElementById('nphi-cac').addEventListener('change', e => { bd.ac = e.target.value; bd.page = 0; renderClaims(); });
    document.getElementById('nphi-co').addEventListener('change', e => { bd.o = e.target.value; bd.page = 0; renderClaims(); });
    document.getElementById('nphi-pp').addEventListener('click', () => { bd.page--; renderClaims(); });
    document.getElementById('nphi-pn').addEventListener('click', () => { bd.page++; renderClaims(); });
    const btn = document.getElementById('nphi-csv');
    const use = window.claude && window.claude.use ? window.claude.use('downloads') : Promise.resolve(null);
    use.then(dl => { if(!dl) return; btn.hidden = false;
      btn.addEventListener('click', async () => {
        const hd = ['claim_no','sent_date','episode_invoice','file_no','type','outcome','sub_account','insurer','service_month','gross','patient_share','company_share','vat','resend_count','fee_share'];
        const csv = [hd.join(',')].concat(F.map(c => { const o = OC[c[5]] || 'O'; return [c[0], c[1], c[2], c[3], TS[c[4]]||c[4], OS[o], c[6], `"${subN(c[6]).replace(/"/g,'""')}"`, c[7], c[8], c[9], c[10], c[11], c[12], o==='A' ? per.toFixed(4) : 0].join(','); })).join('\r\n');
        try { await dl.save({filename: `NPHIES_fee_${r.inv}_${m}_claims.csv`, data: new Blob(['﻿' + csv], {type:'text/csv'})}); } catch(e) {}
      });
    });
  }
  document.getElementById('nphi-m').addEventListener('change', () => { renderCalc(); renderHist(); renderBd(); });
  renderCalc(); renderHist(); renderBd();

  // ---------------------------------------------------------------- 3. register grid
  const cReg = el('div','card'); cReg.style.marginTop = '16px'; sec.appendChild(cReg);
  const yrs = [...new Set(D.months.map(m => m.slice(0,4)))];
  cReg.innerHTML = `<h3>Sehati invoice register · all branches · سجل فواتير صحتي</h3>
    <p class="card-sub"><b>Amounts include 15% VAT</b> (net fee on 3320004 — 3140001 in 2024 — plus input VAT on 1263000), per branch and service month. <b>Payment status comes from your ledger, not from NPHIES:</b> it is the Sehati supplier sub-account <b>2122001 · S0471</b>, posted and open vouchers. NPHIES and Sehati send no payment status to EXSYS. An empty cell from 2025 on means no Sehati invoice is booked in your ledger for that month. Click a cell for the vouchers.</p>
    <div class="aud-bar"><div class="f"><label for="nphi-y">Year</label><select id="nphi-y">${yrs.slice().reverse().map(y => `<option>${y}</option>`).join('')}</select></div>
      <div class="nphi-legend"><span class="k paid"></span>Paid · posted <span class="k popen"></span>Paid · voucher not posted <span class="k unpaid"></span>Not paid in the ledger <span class="k miss"></span>No invoice in the ledger</div><div class="nphi-src">Source of every colour: your ledger · 2122001 · S0471 (شركة صحتي للخدمات المعلوماتية - نفيس)</div></div>
    <div class="tbl-wrap"><table class="aud-t nphi-grid" id="nphi-grid"></table></div>
    <div id="nphi-det" class="nphi-det"></div>
    <div id="nphi-flags"></div>`;
  function cellInv(b, m){ return I.filter(x => x.br === b && x.m === m); }
  function renderGrid(){
    const y = document.getElementById('nphi-y').value, ms = [...Array(12)].map((_,i) => `${y}-${String(i+1).padStart(2,'0')}`);
    let h = `<thead><tr><th>Branch</th>${ms.map(m => `<th class="n">${MON[+m.slice(5)-1]}</th>`).join('')}<th class="n">Year</th></tr></thead><tbody>`;
    BRS.forEach(b => { let t = 0;
      h += `<tr><td>${BR[b]}</td>` + ms.map(m => { const xs = cellInv(b, m);
        if(!xs.length){ const miss = m >= since && m <= lastM; return `<td class="n ${miss?'miss':''}" ${miss?`title="No Sehati invoice for ${BR[b]} ${ml(m)} in your ledger (3320004 / 2122001 · S0471) — ask Sehati whether it was issued"`:''}>${miss?'—':''}</td>`; }
        const net = xs.reduce((s,x)=>s+x.tot,0); t += net; const st = xs.some(x=>x.st==='unpaid'||x.st==='part') ? 'unpaid' : xs.some(x=>x.st==='paid_open') ? 'popen' : 'paid';
        return `<td class="n c ${st}" data-b="${b}" data-m="${m}" title="${esc(xs.map(x=>`${x.no||'no invoice no.'} · ${ST[x.st][1]}`).join(' | '))}">${n2(net)}${xs.some(x=>x.pdf)?'<span class="pdf" title="PDF in the folder">▣</span>':''}</td>`; }).join('') + `<td class="n"><b>${n2(t)}</b></td></tr>`; });
    const all = I.filter(x => x.m && x.m.startsWith(y) && x.br === 'ALL');
    if(all.length) h += `<tr><td>All branches</td><td colspan="13" class="sm">${all.map(x => `${esc(x.no)} · ${n2(x.tot)} incl. VAT — fees for transactions sent outside the platform, Jun 2023 → Jun 2024 (booked ${dmy(x.acc[0][1])})`).join('<br>')}</td></tr>`;
    document.getElementById('nphi-grid').innerHTML = h + '</tbody>';
    document.querySelectorAll('#nphi-grid td.c').forEach(td => td.addEventListener('click', () => showDet(td.dataset.b, td.dataset.m)));
  }
  function showDet(b, m){
    const xs = cellInv(b, m);
    document.getElementById('nphi-det').innerHTML = `<h4>${BR[b]} · ${ml(m)}</h4><table class="aud-t nphi-t"><thead><tr><th>Invoice</th><th class="n">Net</th><th class="n">VAT</th><th class="n">Total</th><th>Accrual</th><th>Payment</th><th>Status</th><th>Notes</th></tr></thead><tbody>${xs.map(x => `<tr><td>${esc(x.no || '—')}${x.pdf?`<span class="sm">▣ ${esc(x.pdf)}</span>`:''}</td><td class="n">${n2(x.net)}</td><td class="n">${n2(x.vat)}</td><td class="n">${n2(x.tot)}</td>
      <td>${x.acc.map(a => `${esc(a[0])}<span class="sm">${dmy(a[1])}</span>`).join('')}</td><td>${x.pays.map(a => `${esc(a[0])}<span class="sm">${dmy(a[1])}${a[2]==='O'?' · <b>open, not posted</b>':' · posted'}</span>`).join('') || '—'}</td><td>${pill(x.st)}</td>
      <td class="sm">${x.fl.map(f => esc(FL[f]||f)).join('; ')}${x.st==='offset'?`Short-paid ${n2(x.offAmt)} = credit note ${esc(x.offset)} (duplicate Oct-2023 invoice) set off by Sehati`:''}</td></tr>`).join('')}</tbody></table>`;
  }
  function renderFlags(){
    const fx = I.filter(x => x.st !== 'paid' || x.fl.length);
    document.getElementById('nphi-flags').innerHTML = `<h4 class="nphi-h">Points to follow up · نقاط للمتابعة</h4><ul class="nphi-list">
      ${unpaid.map(x => `<li><b>${BR[x.br]} ${ml(x.m)}</b> — invoice ${esc(x.no)}, SAR ${n2(x.tot)}, accrued in ${esc(x.acc[0][0])} on ${dmy(x.acc[0][1])}; no payment on 2122001 yet.</li>`).join('')}
      ${D.sup.O ? `<li><b>Open voucher ${D.sup.openV.join(', ')}</b> (06/06/2026) pays the May 2026 invoices of Buraydah 2 (8,178.28) and Rafha (2,689.39) but is not posted yet — the posted balance of S0471 is ${n2(D.sup.P)}; it is zero once the voucher is posted. Its bank line for 2,689.39 is narrated “بريدة 1 · 202605803”; it belongs to Rafha 202605655.</li>` : ''}
      ${missing.map(([b,m]) => `<li><b>${BR[b]} ${ml(m)}</b> — no Sehati invoice in your ledger (nothing on 3320004 or S0471). Not a payment issue: check with Sehati whether the invoice was issued, then book it.</li>`).join('')}
      ${fx.filter(x => x.st !== 'unpaid').map(x => `<li><b>${BR[x.br]} ${ml(x.m)}</b> ${esc(x.no || '(no invoice no.)')} — ${pill(x.st)} ${x.fl.map(f => esc(FL[f]||f)).join('; ')}${x.st==='offset'?` Short-paid ${n2(x.offAmt)} = credit note ${esc(x.offset)} set off.`:''}</li>`).join('')}</ul>`;
  }
  document.getElementById('nphi-y').addEventListener('change', () => { renderGrid(); document.getElementById('nphi-det').innerHTML = ''; });
  renderGrid(); renderFlags();

  sec.appendChild(el('div','note', `<b>Source.</b> Invoice PDFs: <code>${esc(D.folder)}</code>, read with <code>pdftotext</code> on your computer (the PDFs are not changed). Ledger: EXSYS Riyadh <code>GL_TRANSACTIONS_DETAILS</code>, posted vouchers only (status P), accounts 3320004 / 3140001 (fee), 1263000 (input VAT) and 2122001 (Sehati payable), narrations naming the NPHIES platform fee; Digital Healthcare Solutions integration fees and bank charges are left out. Read ${dmy(D.asOf)}. NPHIES activity: Rafha <code>HS_NPHIES_CLAIM_REQUEST</code> (claims by creation month, type and outcome), <code>HS_NPHIES_PREAUTH_REQUEST</code>, <code>HS_NPHIES_API_HISTORY</code> (eligibility), <code>HS_NPHIES_COMMUNICATION</code>, <code>HS_NPHIES_POLL_HISTORY</code>; claim data runs to ${dmy(D.nphAsOf)}. Riyadh, Buraydah 1 and Buraydah 2 send their claims through a different channel — their NPHIES tables are empty — so their fees can be matched and tracked but not set against claim counts. Medians use Feb 2025 → Aug 2026 (Jan 2025 was the go-live month with 45% of claims still queued). No single driver in the database explains the fee exactly: month to month it moves about ±12% around the median, so a month outside ±15% is worth checking against Sehati's transaction statement.`));
})();
