/* ======================================================================
   Unlinked JV · tax vouchers — every journal-tax (VOUCHTAX) and cash-tax
   (CMVCHTAX) transaction checked against the voucher it posts; live JVs
   left behind when a tax transaction was cancelled or posted twice
   ====================================================================== */
(function(){
  const D = DATA.ujv, sec = document.getElementById('sec-aud-ujv');
  if(!D || !sec) return;
  const n2 = v => (v === null || v === undefined || isNaN(v)) ? '—' : (v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
  const n0 = v => (v === null || v === undefined) ? '—' : Math.round(v).toLocaleString('en-US');
  const dmy = d => d ? `${d.slice(8,10)}/${d.slice(5,7)}/${d.slice(0,4)}` : '—';
  const BR = {Riyadh:'Riyadh', BUR1:'Buraydah 1', BUR2:'Buraydah 2', Rafha:'Rafha'};
  const SRC = {GL:'Journal tax · قيد يومية ضريبي', CM:'Cash tax · قيد نقدية ضريبي'};
  const VST = {P:'posted', O:'open', C:'cancelled'};
  // one list of exceptions, worst first
  const T = {
    orphan:      ['bad', 1, 'JV live · tax transaction cancelled', 'قيد مرحّل وحركته الضريبية ملغاة',
                  'The JV is posted, but the tax transaction that created it is cancelled, so the JV is linked to nothing. Either cancel the JV (if the transaction was re-entered elsewhere) or re-post the tax transaction so the two are linked again — the VAT return reads the tax transaction, the ledger reads the JV.'],
    orphan_cm:   ['warn', 2, 'Cash voucher live · cash-tax transaction cancelled', 'سند نقدية مرحّل وحركته الضريبية ملغاة',
                  'Same date, cash account and amount as a cancelled cash-tax transaction, and no tax transaction points to it. Check whether it is the left-over voucher of that transaction.'],
    duplicate:   ['bad', 1, 'Duplicate JV', 'قيد مكرر',
                  'Identical lines, date and amount to the JV the tax transaction points to — the screen posted twice. Cancel the unlinked copy.'],
    jv_cancelled:['bad', 1, 'Tax transaction posted · its JV cancelled', 'حركة مرحّلة وقيدها ملغي',
                  'The tax transaction is posted but the JV it points to is cancelled, so the amount is not in the ledger. Re-open and re-post the transaction.'],
    jv_missing:  ['bad', 1, 'Tax transaction posted · JV not found', 'حركة مرحّلة وقيدها غير موجود', 'Re-post the transaction.'],
    posted_nojv: ['bad', 1, 'Tax transaction posted · no JV number', 'حركة مرحّلة بدون رقم قيد', 'Re-post the transaction.'],
    jv_open:     ['warn', 2, 'Tax transaction posted · JV still open', 'حركة مرحّلة وقيدها مفتوح', 'Post the JV.'],
    cancelled_live_jv:['bad', 1, 'Tax transaction cancelled · JV live', 'حركة ملغاة وقيدها مرحّل', 'Cancel the JV or re-post the transaction.'],
    shared_jv:   ['bad', 1, 'Two tax transactions point to one JV', 'حركتان على قيد واحد', 'Only one transaction may own a JV.'],
    system:      ['warn', 2, 'System JV · no tax transaction found', 'قيد نظام بدون حركة ضريبية',
                  'A system-type JV (VM type S) that no tax transaction points to and that matches no cancelled one by date and amount. Confirm which screen produced it.'],
    amt_diff:    ['', 3, 'Amount differs · tax transaction vs JV', 'اختلاف المبلغ بين الحركة والقيد',
                  'Linked correctly, but the debit total of the tax lines differs from the JV debit total.'],
    open_pending:['', 4, 'Open · waiting to be posted', 'مفتوحة · لم تُرحّل بعد',
                  'Normal while it is being edited: the old JV is cancelled and a new number is issued on posting.'] };
  const SHORT = {"orphan": "Cancel the JV, or re-post the tax transaction", "orphan_cm": "Check; cancel if it is the left-over voucher", "duplicate": "Cancel the unlinked copy", "jv_cancelled": "Re-open and re-post the transaction", "jv_missing": "Re-post the transaction", "posted_nojv": "Re-post the transaction", "jv_open": "Post the JV", "cancelled_live_jv": "Cancel the JV or re-post", "shared_jv": "Unlink one transaction", "system": "Confirm the source screen", "amt_diff": "Compare lines; correct the JV", "open_pending": "Post when finished"};
  const pill = k => `<span class="pill ${T[k][0]}" title="${esc(T[k][3])}">${esc(T[k][2])}</span>`;
  const rows = [];
  D.gls.filter(g => !['closing','purchase_2019'].includes(g.kind)).forEach(g => rows.push({k:g.kind, br:g.br, src:g.kind==='orphan_cm'?'CM':'GL', tno:g.tno||'', tst:g.tst||'', jv:g.v, jvst:g.st, d:g.d, amt:g.dr, ds:g.ds, extra:g.lv ? `linked copy ${g.lv}` : '', eu:g.eu}));
  D.tx.forEach(t => t.fl.forEach(k => rows.push({k, br:t.br, src:t.src, tno:t.tno, tst:t.st, jv:t.v||'', jvst:t.vst||'', d:t.d, amt:t.tdr, ds:t.ds, extra:k==='amt_diff' ? `tax lines ${n2(t.tdr)} · JV ${n2(t.vdr)}` : '', eu:t.eu})));
  rows.sort((a,b) => T[a.k][1] - T[b.k][1] || (b.amt||0) - (a.amt||0));

  audHead(sec, 'Accounting Audit', 'Unlinked JV · Tax Vouchers', 'قيود غير مربوطة بحركة ضريبية',
    `Every transaction entered on the two tax screens — <b>journal tax vouchers</b> (<code>VOUCHTAX</code>) and <b>cash-management tax vouchers</b> (<code>CMVCHTAX</code>) — must own exactly one live JV. Posting gives it a JV number; re-opening cancels that JV and keeps the transaction; re-posting issues a new JV. When the screen misfires, a JV stays posted with no transaction behind it, or the same transaction posts twice. This tab checks all ${n0(D.total)} tax transactions in the four branches against <code>VOUCHER_MASTERS</code> / <code>CM_VOUCHER_MASTER</code>.`);

  const high = rows.filter(r => T[r.k][1] === 1), orph = rows.filter(r => r.k === 'orphan' || r.k === 'orphan_cm' || r.k === 'duplicate');
  const posted = Object.entries(D.n).filter(([k]) => k.endsWith('|P')).reduce((s,[,v]) => s+v, 0);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  kp.innerHTML = kpiTile('Posted tax transactions', n0(posted), `${n0(D.ok)} linked to one live JV with matching amounts`)
    + kpiTile('Live JVs with no tax transaction', n0(orph.length), `SAR ${n2(orph.reduce((s,r)=>s+(r.amt||0),0))} · cancelled transaction left its JV posted, or posted twice`, orph.length > 0)
    + kpiTile('Posted transactions without a live JV', n0(rows.filter(r => ['jv_cancelled','jv_missing','posted_nojv'].includes(r.k)).length), 'amount missing from the ledger', rows.some(r => ['jv_cancelled','jv_missing','posted_nojv'].includes(r.k)))
    + kpiTile('Open · waiting to be posted', n0(rows.filter(r => r.k === 'open_pending').length), rows.filter(r => r.k === 'open_pending').map(r => `${r.tno} · ${dmy(r.d)}`).join(', ') || 'none');

  // ------------------------------------------------ exceptions
  const c1 = el('div','card'); c1.style.marginTop = '16px'; sec.appendChild(c1);
  const kinds = [...new Set(rows.map(r => r.k))];
  c1.innerHTML = `<h3>Exceptions · الاستثناءات</h3><p class="card-sub">Worst first. Point at a type for its meaning; the last column says what to do.</p>
    <div class="aud-bar">
      <div class="f"><label for="ujv-k">Type</label><select id="ujv-k"><option value="">All types (${rows.length})</option>${kinds.map(k => `<option value="${k}">${esc(T[k][2])} (${rows.filter(r=>r.k===k).length})</option>`).join('')}</select></div>
      <div class="f"><label for="ujv-b">Branch</label><select id="ujv-b"><option value="">All branches</option>${Object.keys(BR).map(b => `<option value="${b}">${BR[b]}</option>`).join('')}</select></div>
      <div class="f"><label for="ujv-q">Search</label><input type="search" id="ujv-q" placeholder="JV, tax no., text"></div></div>
    <div class="ujv-wrap"><table class="aud-t ujv-t" id="ujv-tab"></table></div>`;
  function render(){
    const k = document.getElementById('ujv-k').value, b = document.getElementById('ujv-b').value, q = document.getElementById('ujv-q').value.trim().toLowerCase();
    const F = rows.filter(r => (!k || r.k === k) && (!b || r.br === b) && (!q || `${r.jv} ${r.tno} ${r.ds}`.toLowerCase().includes(q)));
    document.getElementById('ujv-tab').innerHTML = `<thead><tr><th>Type</th><th>Branch · screen</th><th>Tax transaction</th><th>JV</th><th>Date</th><th class="n">Amount (debit)</th><th>Description</th><th>What to do</th></tr></thead><tbody>
      ${F.map(r => `<tr><td>${pill(r.k)}</td><td>${BR[r.br]||r.br}<span class="sm">${SRC[r.src]}</span></td>
        <td>${esc(r.tno||'—')}${r.tst?`<span class="sm">${VST[r.tst]||r.tst}</span>`:''}</td>
        <td><b>${esc(r.jv||'—')}</b>${r.jvst?`<span class="sm">${VST[r.jvst]||r.jvst}</span>`:''}${r.extra?`<span class="sm">${esc(r.extra)}</span>`:''}</td>
        <td>${dmy(r.d)}</td><td class="n">${n2(r.amt)}</td><td class="ar">${esc(r.ds)}<span class="sm">entered by ${esc(r.eu||'—')}</span></td><td class="ujv-do" title="${esc(T[r.k][4])}">${esc(SHORT[r.k])}</td></tr>`).join('') || '<tr><td colspan="8">Nothing to show.</td></tr>'}</tbody>`;
  }
  ['ujv-k','ujv-b'].forEach(id => document.getElementById(id).addEventListener('change', render));
  document.getElementById('ujv-q').addEventListener('input', render);
  render();

  // ------------------------------------------------ same supplier invoice in more than one tax transaction
  const c2 = el('div','card'); c2.style.marginTop = '16px'; sec.appendChild(c2);
  const DI = D.di.slice().sort((a,b) => (b.same - a.same) || b.vat - a.vat);
  c2.innerHTML = `<h3>Same supplier invoice in more than one tax transaction · نفس فاتورة المورد في أكثر من حركة</h3>
    <p class="card-sub">Posted tax lines carrying the same invoice number and supplier VAT number in different tax transactions — the input VAT may have been claimed twice. "Identical" means every transaction has the same amount and VAT; the others can be legitimate (instalments, credit notes, a reused invoice number).</p>
    <div class="aud-bar"><label class="chk"><input type="checkbox" id="ujv-same" checked> Identical amounts only</label></div>
    <div class="ujv-wrap"><table class="aud-t ujv-t" id="ujv-di"></table></div>`;
  function renderDi(){
    const only = document.getElementById('ujv-same').checked, F = DI.filter(d => !only || d.same);
    document.getElementById('ujv-di').innerHTML = `<thead><tr><th>Branch · screen</th><th>Invoice no.</th><th>Supplier VAT no.</th><th>Tax transactions → JV</th><th class="n">VAT counted</th><th></th></tr></thead><tbody>
      ${F.map(d => `<tr><td>${BR[d.br]||d.br}<span class="sm">${SRC[d.src]}</span></td><td>${esc(d.inv)}</td><td>${esc(d.taxno||'—')}</td>
        <td>${d.its.map(i => `${esc(i.t)} → <b>${esc(i.v)}</b> · ${dmy(i.d)} · ${n2(i.dr)} · VAT ${n2(i.vat)}`).join('<br>')}</td><td class="n">${n2(d.vat)}</td>
        <td>${d.same ? '<span class="pill bad">Identical</span>' : '<span class="pill">Different amounts</span>'}</td></tr>`).join('') || '<tr><td colspan="6">Nothing to show.</td></tr>'}</tbody>`;
  }
  document.getElementById('ujv-same').addEventListener('change', renderDi); renderDi();

  const ex = D.gls.filter(g => g.kind === 'closing').length, pu = D.gls.filter(g => g.kind === 'purchase_2019').length;
  sec.appendChild(el('div','note', `<b>Source.</b> EXSYS, all four branches, read ${dmy(D.asOf)}: <code>GL_VOUCHER_TAX_MASTER/DETAILS</code> (journal tax screen) and <code>CM_VOUCHER_TAX_MASTER/DETAILS</code> (cash tax screen) against <code>VOUCHER_MASTERS/DETAILS</code> and <code>CM_VOUCHER_MASTER/DETAILS</code> — base tables, posted (P), open (O) and cancelled (C). The <i>VOUCHER_TAX_NO</i> shown in the GL view is looked up from the tax master, so it cannot itself reveal an unlinked JV; the link is tested from both ends here. Live JVs with no tax transaction are system-type JVs (VM type S) that no tax transaction points to; they are matched to cancelled tax transactions by branch, date and amount, and to linked JVs by identical lines. Left out: ${ex} year-end closing JVs and ${pu} purchase-interface JVs from Jan–Feb 2019, which are system JVs from other modules. Tax-line VAT is not compared with the JV's VAT line, because VAT netted on reversal lines makes that comparison unreliable.`));
})();
