
/* ======================================================================
   ACCOUNTING AUDIT  ·  four tabs driven by the global period + branch filter
   Data: DATA.aud, exported from the NextGen V1.1 Power BI model using the
   same measures and visual filters as its audit pages.
   ====================================================================== */
const AUD = DATA.aud;
const ymOfIdx = i => +TIMONTHS[i].replace('-', '');               // 202608
const ymAdd = (ym, k) => { let y = Math.floor(ym/100), m = ym%100 + k; while(m > 12){ m -= 12; y++; } while(m < 1){ m += 12; y--; } return y*100 + m; };
const ymLab = ym => EN_MON[(ym%100)-1] + ' ' + Math.floor(ym/100);
const ymEndDate = ym => { const y = Math.floor(ym/100), m = ym%100; const d = new Date(Date.UTC(y, m, 0)); return d.toISOString().slice(0,10); };
const nfmt = (v, d=0) => (v === null || v === undefined || isNaN(v)) ? '—'
  : (v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:d, maximumFractionDigits:d});
const ccOK = cc => TI.cc === 'ALL' || cc === TI.cc;
const CC_LBL = cc => (TIM.ccName[cc] || [cc,cc])[0];
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
function audWindow(){
  const a = ymOfIdx(TI.a), b = ymOfIdx(TI.b);
  const c = TI.cmp ? {a: ymAdd(a,-12), b: ymAdd(b,-12)} : null;
  return {a, b, c};
}
function audHead(sec, eyebrow, title, ar, lead){
  sec.appendChild(el('div','section-head', `<div class="eyebrow">${eyebrow}</div><h2>${title} <span style="font-family:'IBM Plex Sans',sans-serif;font-size:17px;color:var(--ink-muted);font-weight:500">· ${ar}</span></h2><p>${lead}</p>`));
}
function kpiTile(label, value, sub, neg){
  return `<div class="card kpi"><div class="label">${label}</div><div class="value num${neg?' neg':''}" style="font-size:23px">${value}</div><div class="delta flat">${sub||''}</div></div>`;
}
function dPct(cur, prev){
  if(prev === null || prev === undefined || !prev) return '';
  const p = (cur - prev) / Math.abs(prev);
  return `${cur-prev >= 0 ? '+' : '−'}${Math.abs(p*100).toFixed(1)}% vs LY`;
}

/* ---------------------------------------------------------------- 1 ---- */
/* Terminated employees who still carry a balance                          */
(function(){
  const sec = document.getElementById('sec-aud-term'); if(!sec) return;
  audHead(sec, 'Accounting Audit', 'Terminated Staff Balances', 'موظفين انتهت خدماتهم لهم أرصدة',
    'Every employee sub-account whose staff record carries an end-of-service date and whose running balance is still open (beyond ±1 riyal). Balances are as of the <b>end of the selected period</b>.');
  const bar = el('div','aud-bar'); bar.innerHTML = `
    <div class="f"><label for="at-q">Search staff</label><input type="search" id="at-q" placeholder="name or staff no."></div>
    <div class="f"><label for="at-sign">Balance side</label><select id="at-sign"><option value="all">Debit and credit</option><option value="dr">Debit — staff owes the company</option><option value="cr">Credit — company owes the staff</option></select></div>
    <label class="chk"><input type="checkbox" id="at-eos"> Only staff who left on or before the period end</label>`;
  sec.appendChild(bar);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const row = el('div','grid grid-2'); row.style.marginTop = '16px'; row.style.alignItems = 'start'; sec.appendChild(row);
  const cMain = el('div','card'); const cAcc = el('div','card'); row.appendChild(cMain); row.appendChild(cAcc);
  sec.appendChild(el('div','note', `<b>Source.</b> NextGen V1.1 — <code>SUB_ACCOUNT</code> × <code>GL_ACCOUNTS</code> × <code>Staff_Master_Info[END_OF_SERVICE_AWARD_DATE]</code> (from <code>PS_STAFF_CONTRACT</code>), measure <code>Balance RT</code>. Staff balances are not split by branch cost centre, so the branch filter does not apply on this tab. Totals tie to the Power BI page: 14 staff, net −5,377 as of today.`));
  const open = new Set();
  const bal = (s, upto) => { let t = 0; for(const [,ym,n] of s.l) if(ym <= upto) t += n; return t; };
  const balAcc = (s, upto) => { const m = {}; for(const [ac,ym,n] of s.l) if(ym <= upto) m[ac] = (m[ac]||0) + n; return m; };
  function render(){
    const w = audWindow(), asOf = ymEndDate(w.b);
    const q = document.getElementById('at-q').value.trim().toLowerCase();
    const side = document.getElementById('at-sign').value;
    const onlyLeft = document.getElementById('at-eos').checked;
    let rows = AUD.term.map(s => ({s, b: bal(s, w.b), ly: w.c ? bal(s, w.c.b) : null}))
      .filter(r => Math.abs(r.b) > 1)
      .filter(r => !q || r.s.nm.toLowerCase().includes(q) || r.s.no.includes(q))
      .filter(r => side === 'all' || (side === 'dr' ? r.b > 0 : r.b < 0))
      .filter(r => !onlyLeft || r.s.eos <= asOf)
      .sort((x,y) => (y.s.eos||'').localeCompare(x.s.eos||''));
    const net = rows.reduce((t,r)=>t+r.b,0), dr = rows.filter(r=>r.b>0).reduce((t,r)=>t+r.b,0), cr = rows.filter(r=>r.b<0).reduce((t,r)=>t+r.b,0);
    const lyAll = w.c ? AUD.term.filter(s => Math.abs(bal(s, w.c.b)) > 1).length : null;
    kp.innerHTML = kpiTile('Staff with open balance', rows.length, lyAll !== null ? `${lyAll} at the same date last year` : '')
      + kpiTile('Net balance', nfmt(net), `as of ${asOf}`, net < 0)
      + kpiTile('Owed by staff (debit)', nfmt(dr), 'advances, custody, deductions to recover')
      + kpiTile('Owed to staff (credit)', nfmt(cr), 'dues, allowances still payable', true);
    let h = `<h3>Staff list <span class="tag">${rows.length}</span></h3><p class="card-sub">Click a row for the account breakdown · balance as of ${asOf}${w.c ? ' · LY = same date last year' : ''}</p><div class="aud-scroll"><table class="aud-t"><thead><tr><th>Staff no.</th><th>Name</th><th>End of service</th><th class="n">Balance</th>${w.c?'<th class="n">LY</th>':''}</tr></thead><tbody>`;
    for(const r of rows){
      const isOpen = open.has(r.s.no);
      h += `<tr class="aud-row-click${isOpen?' open':''}" data-no="${esc(r.s.no)}"><td>${esc(r.s.no)}</td><td>${esc(r.s.nm)}</td><td>${esc(r.s.eos)}</td><td class="n ${r.b<0?'neg':''}">${nfmt(r.b)}</td>${w.c?`<td class="n">${r.ly===null||Math.abs(r.ly)<=1?'—':nfmt(r.ly)}</td>`:''}</tr>`;
      if(isOpen){
        const m = balAcc(r.s, w.b);
        for(const [ac,v] of Object.entries(m).sort((x,y)=>Math.abs(y[1])-Math.abs(x[1]))) if(Math.abs(v) > 0.004)
          h += `<tr class="aud-sub"><td>${esc(ac)}</td><td class="ar" colspan="2">${esc(AUD.tacc[ac]||'')}</td><td class="n ${v<0?'neg':''}">${nfmt(v,2)}</td>${w.c?'<td></td>':''}</tr>`;
      }
    }
    h += `<tr class="tot"><td colspan="3">Total</td><td class="n ${net<0?'neg':''}">${nfmt(net)}</td>${w.c?'<td></td>':''}</tr></tbody></table></div>`;
    cMain.innerHTML = h;
    cMain.querySelectorAll('.aud-row-click').forEach(tr => tr.addEventListener('click', () => { const k = tr.dataset.no; open.has(k) ? open.delete(k) : open.add(k); render(); }));
    // account summary for the listed staff
    const acc = {};
    for(const r of rows){ const m = balAcc(r.s, w.b); for(const [ac,v] of Object.entries(m)) acc[ac] = (acc[ac]||0) + v; }
    const accRows = Object.entries(acc).filter(([,v]) => Math.abs(v) > 0.5).sort((x,y) => y[1]-x[1]);
    let h2 = `<h3>By account</h3><p class="card-sub">Where the open balances of these staff sit</p><table class="aud-t"><thead><tr><th>Account</th><th>Name</th><th class="n">Balance</th></tr></thead><tbody>`;
    for(const [ac,v] of accRows) h2 += `<tr><td>${esc(ac)}</td><td class="ar">${esc(AUD.tacc[ac]||'')}</td><td class="n ${v<0?'neg':''}">${nfmt(v)}</td></tr>`;
    h2 += `<tr class="tot"><td colspan="2">Total</td><td class="n ${net<0?'neg':''}">${nfmt(net)}</td></tr></tbody></table>`;
    cAcc.innerHTML = h2;
  }
  ['at-q','at-sign','at-eos'].forEach(id => document.getElementById(id).addEventListener(id==='at-q'?'input':'change', render));
  TI.on(render); render();
})();

/* ---------------------------------------------------------------- 2 ---- */
/* Control accounts — must clear to zero at every month end                */
(function(){
  const sec = document.getElementById('sec-aud-ctrl'); if(!sec) return;
  audHead(sec, 'Accounting Audit', 'Control Accounts', 'حسابات المراقبة',
    'Sales-control and custody-control accounts are clearing accounts: every month the cashier postings and the matching settlement should net to zero. Any month-end balance outside ±0.03 riyal (rounding tolerance) means something was posted on one side only.');
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const c1 = el('div','card'); c1.style.marginTop = '16px'; sec.appendChild(c1);
  const c2 = el('div','card'); c2.style.marginTop = '16px'; sec.appendChild(c2);
  sec.appendChild(el('div','note', `<b>Source.</b> NextGen V1.1 — accounts 1310000–1410000 exactly as filtered on the Control Account visual, measure <code>Balance RT</code> (cumulative debit − credit from the first posting). Branch comes from the model's <code>Branches</code> dimension; the global branch filter applies. Totals tie to the Power BI visual: −2,012,547 across all branches today.`));
  const accs = Object.keys(AUD.cacc).sort();
  const rt = (acc, upto) => { let t = 0; for(const [cc,a,ym,n] of AUD.ctrl) if(a === acc && ym <= upto && ccOK(cc)) t += n; return t; };
  const mv = (acc, a0, b0) => { let t = 0; for(const [cc,a,ym,n] of AUD.ctrl) if(a === acc && ym >= a0 && ym <= b0 && ccOK(cc)) t += n; return t; };
  const TOL = 0.03;
  function render(){
    const w = audWindow();
    const months = []; for(let m = w.a; m <= w.b; m = ymAdd(m,1)) months.push(m);
    const shown = months.slice(-12);
    let openAcc = 0, openCells = 0, tot = 0, totLY = 0;
    let h = `<h3>Balance at period end</h3><p class="card-sub">${ymLab(w.b)} month-end · ${ccLabel('en')}</p><table class="aud-t"><thead><tr><th>Account</th><th>Name</th><th class="n">Movement in period</th><th class="n">Balance RT</th>${w.c?'<th class="n">Same date LY</th>':''}<th>Months not cleared</th><th>Status</th></tr></thead><tbody>`;
    const gridRows = [];
    for(const a of accs){
      const b = rt(a, w.b), m = mv(a, w.a, w.b), ly = w.c ? rt(a, w.c.b) : null;
      const cells = shown.map(ym => rt(a, ym));
      const bad = months.filter(ym => Math.abs(rt(a, ym)) > TOL).length;
      if(Math.abs(b) < 0.005 && Math.abs(m) < 0.005 && !bad && (ly === null || Math.abs(ly) < 0.005)) continue;
      tot += b; if(ly !== null) totLY += ly; openCells += bad; if(Math.abs(b) > TOL) openAcc++;
      gridRows.push([a, cells]);
      h += `<tr><td>${a}</td><td class="ar">${esc(AUD.cacc[a])}</td><td class="n">${nfmt(m,2)}</td><td class="n ${Math.abs(b)>TOL?'neg':''}">${nfmt(b)}</td>${w.c?`<td class="n">${nfmt(ly)}</td>`:''}<td>${bad} of ${months.length}</td><td>${Math.abs(b)>TOL?'<span class="pill bad">Not cleared</span>':'<span class="pill ok">Cleared</span>'}</td></tr>`;
    }
    h += `<tr class="tot"><td colspan="3">Total</td><td class="n ${Math.abs(tot)>TOL?'neg':''}">${nfmt(tot)}</td>${w.c?`<td class="n">${nfmt(totLY)}</td>`:''}<td colspan="2"></td></tr></tbody></table>`;
    c1.innerHTML = h;
    let g = `<h3>Month-end balance by month</h3><p class="card-sub">Red = not cleared at that month end${months.length > 12 ? ' · showing the last 12 months of the selected period' : ''}</p><div class="tbl-scroll"><table class="aud-t aud-grid"><thead><tr><th>Account</th>${shown.map(m=>`<th class="n">${ymLab(m)}</th>`).join('')}</tr></thead><tbody>`;
    for(const [a,cells] of gridRows) g += `<tr><td class="ar" style="text-align:left;direction:ltr">${a} <span style="color:var(--ink-faint)">${esc(AUD.cacc[a])}</span></td>${cells.map(v=>`<td class="cell ${Math.abs(v)>TOL?'nz':'z'}">${Math.abs(v)>TOL?nfmt(v):'0'}</td>`).join('')}</tr>`;
    g += `</tbody></table></div>`;
    c2.innerHTML = g;
    kp.innerHTML = kpiTile('Accounts not cleared', openAcc, `of ${gridRows.length} with activity`, openAcc>0)
      + kpiTile('Net uncleared balance', nfmt(tot), `${ymLab(w.b)} month-end`, Math.abs(tot)>TOL)
      + kpiTile('Month-ends not cleared', openCells, `across ${months.length} month(s) × ${gridRows.length} account(s)`, openCells>0)
      + kpiTile('Same date last year', w.c ? nfmt(totLY) : '—', w.c ? ymLab(w.c.b) : 'comparison off');
  }
  TI.on(render); render();
})();

/* ---------------------------------------------------------------- 3 ---- */
/* Journal entries with no attachment                                      */
(function(){
  const sec = document.getElementById('sec-aud-uj'); if(!sec) return;
  audHead(sec, 'Accounting Audit', 'Unattached Journal Entries', 'قيود يومية بدون مرفقات',
    'Every voucher posted with no supporting document attached (<code>ATTACH_FILE_PATH</code> empty), excluding automatic cashier-shift postings (<code>FOR_SHIFT</code>), same as the NextGen page. One row per voucher. Filter by the global period and branch, by the controls below, or type into the filter row under each column heading.');
  const users = Object.entries(AUD.users).sort((a,b) => a[0].localeCompare(b[0], undefined, {numeric:true}));
  const types = [...new Set(AUD.uj.map(r => r[3]))].sort(), subs = [...new Set(AUD.uj.map(r => r[4]))].sort();
  const bar = el('div','aud-bar'); bar.innerHTML = `
    <div class="f"><label for="uj-user">Entry user</label><select id="uj-user"><option value="">All users</option>${users.map(([u,n])=>`<option value="${esc(u)}">${esc(u)} — ${esc(n.replace(/\s*\(\s*\d+\s*\)\s*$/,''))}</option>`).join('')}</select></div>
    <div class="f"><label for="uj-type">VM type</label><select id="uj-type"><option value="">All</option>${types.map(t=>`<option>${esc(t)}</option>`).join('')}</select></div>
    <div class="f"><label for="uj-sub">Sub-system</label><select id="uj-sub"><option value="">All</option>${subs.map(t=>`<option>${esc(t)}</option>`).join('')}</select></div>
    <div class="f"><label for="uj-q">Search</label><input type="search" id="uj-q" placeholder="voucher, user or description"></div>
    <button class="clr" id="uj-clear" type="button">Clear filters</button>`;
  sec.appendChild(bar);
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const row = el('div','grid grid-2'); row.style.marginTop = '16px'; row.style.alignItems = 'start'; sec.appendChild(row);
  const cUsers = el('div','card'); const cSubs = el('div','card'); row.appendChild(cUsers); row.appendChild(cSubs);
  const cList = el('div','card'); cList.style.marginTop = '16px'; sec.appendChild(cList);
  sec.appendChild(el('div','note', `<b>Source.</b> NextGen V1.1 GL tables for all four databases (<code>01Riyadh-GL</code> … <code>04RAFHA-GL-2</code>), grouped to voucher level; branch = the database the voucher was posted in. Amount = total debit of the voucher. Covers Jan 2023 onward.`));
  const colF = {v:'', dt:'', br:'', t:'', s:'', u:'', d:''};
  let page = 0; const PER = 100;
  cList.innerHTML = `<h3 id="uj-title">Vouchers</h3><p class="card-sub" id="uj-sub-t"></p><div class="aud-scroll"><table class="aud-t"><thead>
    <tr><th>Voucher</th><th>Date</th><th>Branch</th><th>Type</th><th>Sub-sys</th><th>Entry user</th><th>Description</th><th class="n">Amount</th><th class="n">Lines</th></tr>
    <tr class="flt"><th><input data-k="v" placeholder="filter" aria-label="Filter voucher"></th><th><input data-k="dt" placeholder="yyyy-mm" aria-label="Filter date"></th>
    <th><select data-k="br" aria-label="Filter branch"><option value="">All</option>${['01','02','03','04'].map(c=>`<option value="${c}">${CC_LBL(c)}</option>`).join('')}</select></th>
    <th><select data-k="t" aria-label="Filter type"><option value="">All</option>${types.map(t=>`<option>${esc(t)}</option>`).join('')}</select></th>
    <th><select data-k="s" aria-label="Filter sub-system"><option value="">All</option>${subs.map(t=>`<option>${esc(t)}</option>`).join('')}</select></th>
    <th><input data-k="u" placeholder="code or name" aria-label="Filter entry user"></th><th><input data-k="d" placeholder="contains…" aria-label="Filter description"></th><th></th><th></th></tr>
    </thead><tbody id="uj-body"></tbody></table></div><div class="aud-pager"><span id="uj-count"></span><span><button id="uj-prev" type="button">‹ Prev</button> <span id="uj-pg"></span> <button id="uj-next" type="button">Next ›</button></span></div>`;
  function inWin(dt, a, b){ const ym = +dt.slice(0,7).replace('-',''); return ym >= a && ym <= b; }
  function base(a, b){
    const fu = document.getElementById('uj-user').value, ft = document.getElementById('uj-type').value, fs = document.getElementById('uj-sub').value;
    const q = document.getElementById('uj-q').value.trim().toLowerCase();
    return AUD.uj.filter(r => inWin(r[2], a, b) && ccOK(r[0]) && (!fu || r[5] === fu) && (!ft || r[3] === ft) && (!fs || r[4] === fs)
      && (!q || r[1].toLowerCase().includes(q) || r[6].toLowerCase().includes(q) || r[5].includes(q) || (AUD.users[r[5]]||'').toLowerCase().includes(q)));
  }
  function colFilter(rows){
    return rows.filter(r => (!colF.v || r[1].toLowerCase().includes(colF.v.toLowerCase())) && (!colF.dt || r[2].startsWith(colF.dt))
      && (!colF.br || r[0] === colF.br) && (!colF.t || r[3] === colF.t) && (!colF.s || r[4] === colF.s)
      && (!colF.u || r[5].includes(colF.u) || (AUD.users[r[5]]||'').toLowerCase().includes(colF.u.toLowerCase()))
      && (!colF.d || r[6].toLowerCase().includes(colF.d.toLowerCase())));
  }
  function render(resetPage){
    if(resetPage) page = 0;
    const w = audWindow();
    const rows = colFilter(base(w.a, w.b));
    const ly = w.c ? colFilter(base(w.c.a, w.c.b)) : null;
    const amt = rows.reduce((t,r)=>t+r[7],0);
    const nUsers = new Set(rows.map(r=>r[5])).size;
    kp.innerHTML = kpiTile('Vouchers without attachment', rows.length.toLocaleString('en-US'), ly ? `${ly.length.toLocaleString('en-US')} same period LY · ${dPct(rows.length, ly.length)}` : '', false)
      + kpiTile('Total debit amount', nfmt(amt), ly ? `${nfmt(ly.reduce((t,r)=>t+r[7],0))} LY` : '')
      + kpiTile('Entry users involved', nUsers, 'distinct users posting without support')
      + kpiTile('Manual journals (type J)', rows.filter(r=>r[3]==='J').length.toLocaleString('en-US'), 'the ones a reviewer should see first');
    // by user
    const byU = {}; for(const r of rows){ const k = r[5]; (byU[k] = byU[k] || {n:0,a:0}); byU[k].n++; byU[k].a += r[7]; }
    const ur = Object.entries(byU).sort((x,y)=>y[1].n-x[1].n).slice(0,12); const mx = Math.max(1, ...ur.map(x=>x[1].n));
    const selU = document.getElementById('uj-user').value;
    cUsers.innerHTML = `<h3>By entry user</h3><p class="card-sub">Click a user to filter the list · top 12 by voucher count</p><div class="aud-userbars">${ur.map(([u,o])=>`<div class="r${selU===u?' on':''}" data-u="${esc(u)}"><span class="lb" title="${esc(AUD.users[u]||u)}">${esc(u)} · ${esc((AUD.users[u]||'').replace(/\s*\(\s*\d+\s*\)\s*$/,''))}</span><span class="tr"><span class="fl" style="display:block;width:${(o.n/mx*100).toFixed(1)}%"></span></span><span class="num" style="text-align:right">${o.n.toLocaleString('en-US')}</span></div>`).join('') || '<div class="fl">No vouchers in this selection.</div>'}</div>`;
    cUsers.querySelectorAll('.r').forEach(d => d.addEventListener('click', () => { const s = document.getElementById('uj-user'); s.value = s.value === d.dataset.u ? '' : d.dataset.u; render(true); }));
    // by sub-system × type
    const bs = {}; for(const r of rows){ const k = r[4] + ' · ' + r[3]; (bs[k] = bs[k] || {n:0,a:0}); bs[k].n++; bs[k].a += r[7]; }
    cSubs.innerHTML = `<h3>By sub-system and type</h3><p class="card-sub">CM = cash management, GL = general ledger, AR/IN/PR/FA/HS = sub-ledgers · J = manual journal, S = system</p><table class="aud-t"><thead><tr><th>Sub-system · type</th><th class="n">Vouchers</th><th class="n">Amount</th></tr></thead><tbody>${Object.entries(bs).sort((x,y)=>y[1].n-x[1].n).map(([k,o])=>`<tr><td>${esc(k)}</td><td class="n">${o.n.toLocaleString('en-US')}</td><td class="n">${nfmt(o.a)}</td></tr>`).join('')}<tr class="tot"><td>Total</td><td class="n">${rows.length.toLocaleString('en-US')}</td><td class="n">${nfmt(amt)}</td></tr></tbody></table>`;
    // list
    const pages = Math.max(1, Math.ceil(rows.length / PER)); if(page >= pages) page = pages - 1;
    const slice = rows.slice().reverse().slice(page*PER, page*PER + PER);
    document.getElementById('uj-body').innerHTML = slice.map(r => `<tr><td>${esc(r[1])}</td><td>${r[2]}</td><td>${CC_LBL(r[0])}</td><td>${esc(r[3])}</td><td>${esc(r[4])}</td><td>${esc(r[5])} · ${esc((AUD.users[r[5]]||'').replace(/\s*\(\s*\d+\s*\)\s*$/,''))}</td><td class="ar">${esc(r[6])}</td><td class="n">${nfmt(r[7],2)}</td><td class="n">${r[8]}</td></tr>`).join('')
      || `<tr><td colspan="9" style="color:var(--ink-faint);padding:18px 0">No vouchers match these filters.</td></tr>`;
    document.getElementById('uj-sub-t').textContent = `${periodLabel('en')} · ${ccLabel('en')} · newest first`;
    document.getElementById('uj-count').textContent = `${rows.length.toLocaleString('en-US')} voucher(s) · ${nfmt(amt)} debit`;
    document.getElementById('uj-pg').textContent = `page ${page+1} of ${pages}`;
    document.getElementById('uj-prev').disabled = page === 0; document.getElementById('uj-next').disabled = page >= pages - 1;
  }
  ['uj-user','uj-type','uj-sub'].forEach(id => document.getElementById(id).addEventListener('change', () => render(true)));
  document.getElementById('uj-q').addEventListener('input', () => render(true));
  cList.querySelectorAll('tr.flt [data-k]').forEach(inp => inp.addEventListener(inp.tagName === 'SELECT' ? 'change' : 'input', () => { colF[inp.dataset.k] = inp.value.trim(); render(true); }));
  document.getElementById('uj-prev').addEventListener('click', () => { page--; render(false); });
  document.getElementById('uj-next').addEventListener('click', () => { page++; render(false); });
  document.getElementById('uj-clear').addEventListener('click', () => {
    ['uj-user','uj-type','uj-sub','uj-q'].forEach(id => document.getElementById(id).value = '');
    cList.querySelectorAll('tr.flt [data-k]').forEach(inp => inp.value = ''); Object.keys(colF).forEach(k => colF[k] = ''); render(true);
  });
  TI.on(() => render(true)); render(true);
})();

/* ---------------------------------------------------------------- 4 ---- */
/* VAT audit — sales GL vs sales invoices, credit memos, VAT-suspect lines  */
(function(){
  const sec = document.getElementById('sec-aud-vat'); if(!sec) return;
  audHead(sec, 'Accounting Audit', 'VAT Audit', 'تدقيق ضريبة القيمة المضافة',
    'Revenue booked in the GL by the sales system compared with the sales invoices issued at reception and pharmacy. A gap means invoices that never reached the ledger (or the reverse) — and output VAT follows the invoice, not the ledger. Below it: input-VAT lines whose description suggests a non-deductible expense.');
  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  const row = el('div','grid grid-2'); row.style.marginTop = '16px'; row.style.alignItems = 'start'; sec.appendChild(row);
  const cB = el('div','card'); const cM = el('div','card'); row.appendChild(cB); row.appendChild(cM);
  const cV = el('div','card'); cV.style.marginTop = '16px'; sec.appendChild(cV);
  sec.appendChild(el('div','note', `<b>Source.</b> NextGen V1.1 measures — <code>Revenue GL System Entry</code> (41x/42x revenue, VM type S, excluding AR), <code>Total Sales</code> (reception invoice NET_AMT + pharmacy inventory sales), <code>Variance Sales Invoices VS GL</code>, <code>Credit Memo</code> (revenue posted through AR). VAT-suspect lines = account <i>امانات ضريبة القيمة المضافة مدينة</i> with the NextGen <code>Check VAT</code> keyword flag. Ties to the Power BI page: 2026 GL 46,023,839 vs invoices 52,738,947.`));
  const KW = ['محروقات','زيت','سياره','سيارات','منزل','ضيافة','شاي','سكر','قهوة','قهوه','سكن','افطار','إفطار','غداء','غدا','اكل'];
  const agg = (a0, b0, key) => { const o = {}; for(const [cc,ym,gl,inv,cm] of AUD.vat){ if(ym < a0 || ym > b0 || !ccOK(cc)) continue; const k = key(cc,ym); (o[k] = o[k] || {gl:0,inv:0,cm:0}); o[k].gl += gl; o[k].inv += inv; o[k].cm += cm; } return o; };
  const vchCC = v => { const m = /^[A-Z]+(\d)/.exec(v); return m ? '0' + m[1] : '00'; };
  function render(){
    const w = audWindow();
    const byB = agg(w.a, w.b, cc => cc), byBly = w.c ? agg(w.c.a, w.c.b, cc => cc) : {};
    const tot = Object.values(byB).reduce((t,o)=>({gl:t.gl+o.gl, inv:t.inv+o.inv, cm:t.cm+o.cm}), {gl:0,inv:0,cm:0});
    const totLy = Object.values(byBly).reduce((t,o)=>({gl:t.gl+o.gl, inv:t.inv+o.inv, cm:t.cm+o.cm}), {gl:0,inv:0,cm:0});
    const varc = tot.gl - tot.inv, varLy = totLy.gl - totLy.inv;
    kp.innerHTML = kpiTile('Sales per GL', nfmt(tot.gl), w.c ? dPct(tot.gl, totLy.gl) : '')
      + kpiTile('Sales per invoices', nfmt(tot.inv), w.c ? dPct(tot.inv, totLy.inv) : '')
      + kpiTile('Variance (GL − invoices)', nfmt(varc), w.c ? `${nfmt(varLy)} same period LY` : '', Math.abs(varc) > 1)
      + kpiTile('Credit memos', nfmt(tot.cm), w.c ? `${nfmt(totLy.cm)} LY` : '', tot.cm < 0);
    let h = `<h3>By branch</h3><p class="card-sub">مقارنة المبيعات بين الحسابات والفواتير بالفروع · ${periodLabel('en')}</p><table class="aud-t"><thead><tr><th>Branch</th><th class="n">Sales GL</th><th class="n">Sales invoices</th><th class="n">Variance</th>${w.c?'<th class="n">Variance LY</th>':''}</tr></thead><tbody>`;
    for(const cc of ['00','01','02','03','04']){ const o = byB[cc]; if(!o) continue; const v = o.gl - o.inv; const l = byBly[cc];
      h += `<tr><td>${CC_LBL(cc)}</td><td class="n">${nfmt(o.gl)}</td><td class="n">${nfmt(o.inv)}</td><td class="n ${Math.abs(v)>1?'neg':''}">${nfmt(v)}</td>${w.c?`<td class="n">${l?nfmt(l.gl-l.inv):'—'}</td>`:''}</tr>`; }
    h += `<tr class="tot"><td>Total</td><td class="n">${nfmt(tot.gl)}</td><td class="n">${nfmt(tot.inv)}</td><td class="n ${Math.abs(varc)>1?'neg':''}">${nfmt(varc)}</td>${w.c?`<td class="n">${nfmt(varLy)}</td>`:''}</tr></tbody></table>`;
    cB.innerHTML = h;
    const byM = agg(w.a, w.b, (cc,ym) => ym);
    const ms = Object.keys(byM).map(Number).sort((x,y)=>x-y);
    let m = `<h3>By month</h3><p class="card-sub">مقارنة المبيعات بين الحسابات والفواتير بالشهور · a month with invoices but no GL usually means it is not yet posted</p><div class="aud-scroll" style="max-height:420px"><table class="aud-t"><thead><tr><th>Month</th><th class="n">Sales GL</th><th class="n">Sales invoices</th><th class="n">Variance</th><th></th></tr></thead><tbody>`;
    for(const ym of ms){ const o = byM[ym], v = o.gl - o.inv, big = Math.abs(v) > Math.max(1000, 0.01*Math.abs(o.inv));
      m += `<tr><td>${ymLab(ym)}</td><td class="n">${nfmt(o.gl)}</td><td class="n">${nfmt(o.inv)}</td><td class="n ${big?'neg':''}">${nfmt(v)}</td><td>${big?'<span class="pill bad">Check</span>':Math.abs(v)>1?'<span class="pill warn">Minor</span>':'<span class="pill ok">OK</span>'}</td></tr>`; }
    m += `<tr class="tot"><td>Total</td><td class="n">${nfmt(tot.gl)}</td><td class="n">${nfmt(tot.inv)}</td><td class="n">${nfmt(varc)}</td><td></td></tr></tbody></table></div>`;
    cM.innerHTML = m;
    const vr = AUD.vchk.filter(r => { const ym = +r[1].slice(0,7).replace('-',''); return ym >= w.a && ym <= w.b && ccOK(vchCC(r[0])); }).reverse();
    const vdr = vr.reduce((t,r)=>t+r[2]-r[3],0);
    let v = `<h3>VAT-suspect input lines <span class="tag">${vr.length}</span></h3><p class="card-sub">القيود المحتملة لتواجد بها مخالفات لضريبة القيمة المضافة · input VAT claimed on descriptions that point to non-deductible spend (fuel, vehicles, housing, hospitality, meals) · net ${nfmt(vdr,2)}</p><div class="aud-kw">${KW.filter((k,i)=>KW.indexOf(k)===i).map(k=>`<span>${k}</span>`).join('')}</div><div class="aud-scroll" style="margin-top:12px"><table class="aud-t"><thead><tr><th>Voucher</th><th>Date</th><th>Branch</th><th class="n">Debit</th><th class="n">Credit</th><th>Description</th></tr></thead><tbody>`;
    v += vr.map(r => `<tr><td>${esc(r[0])}</td><td>${r[1]}</td><td>${CC_LBL(vchCC(r[0]))}</td><td class="n">${nfmt(r[2],2)}</td><td class="n">${nfmt(r[3],2)}</td><td class="ar">${esc(r[4])}</td></tr>`).join('') || `<tr><td colspan="6" style="color:var(--ink-faint);padding:18px 0">No flagged lines in this period.</td></tr>`;
    v += `</tbody></table></div>`;
    cV.innerHTML = v;
  }
  TI.on(render); render();
})();
