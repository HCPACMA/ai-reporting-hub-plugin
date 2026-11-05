
/* ======================================================================
   Competitive Analysis · Saudi market only — Tadawul main market (TASI)
   and the Nomu parallel market.  The peer set is every Saudi-listed
   healthcare *provider*; equipment and distribution names are listed
   separately with the reason they are out.
   ====================================================================== */
(function(){
  const sec = document.getElementById('sec-compet'); if(!sec) return;
  const P = DATA.peers; if(!P) return;
  const R = DATA.ext.ratios_full, IS = DATA.ext.is_, Y = DATA.ext.years;
  const i25 = Y.indexOf(2025), i26 = Y.indexOf(2026);
  const SUB = {name:'Al Faihaa Group', rev: IS.total_revenue[i25], ebitda: IS.ebitda[i25],
               ni: IS.net_income[i25], mkt:'—'};
  SUB.ebitda_margin = SUB.ebitda / SUB.rev;

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Strategy &amp; QC</div>
    <h2>Competitive Analysis · Saudi listed healthcare</h2>
    <p>Al Faihaa Group against <b>every healthcare provider listed in Saudi Arabia</b> — ${P.med.TASI.n} on the Tadawul main market (TASI) and ${P.med.Nomu.n} on the Nomu parallel market. No international names: a Riyadh polyclinic group competes for Saudi patients, Saudi insurers and Saudi staff, so the comparison that means anything is the domestic one. Peer figures as of ${P.asof} — market data per company is dated in the table, revenue and earnings are audited FY2025.</p>
  `));

  /* ---------------- where Al Faihaa sits ---------------- */
  const all = P.peers.concat([Object.assign({}, SUB, {ticker:'—', mkt:'private', note:'Four branches — Riyadh, Buraydah 1, Buraydah 2, Rafha', hi:true})]);
  const byRev = all.slice().sort((a,b)=>b.rev-a.rev);
  const rank = byRev.findIndex(x=>x.hi) + 1;
  const nomu = P.peers.filter(p=>p.mkt==='Nomu').sort((a,b)=>b.rev-a.rev);
  const above = nomu.filter(p=>p.rev>SUB.rev).slice(-1)[0];
  const below = nomu.filter(p=>p.rev<SUB.rev)[0];

  const kp = el('div','grid grid-4'); sec.appendChild(kp);
  kp.innerHTML =
      kpiTile('FY2025 revenue', fmtSAR(SUB.rev), `${rank}th of ${all.length} Saudi healthcare providers`, false)
    + kpiTile('EBITDA margin', (SUB.ebitda_margin*100).toFixed(1)+'%',
        `Nomu median ${(P.med.Nomu.ebitda_margin*100).toFixed(1)}% · TASI median ${(P.med.TASI.ebitda_margin*100).toFixed(1)}%`,
        SUB.ebitda_margin < P.med.Nomu.ebitda_margin)
    + kpiTile('Nearest listed peer by size', below ? below.name.split('(')[0].trim().split(' ').slice(0,3).join(' ') : '—',
        below ? `${below.mkt} ${below.ticker} · ${fmtSAR(below.rev)} revenue` : '', false)
    + kpiTile('Market it belongs to', 'Nomu', 'On revenue, every TASI name is 20×–240× larger', false);

  /* ---------------- revenue ladder ---------------- */
  const c1 = el('div','card'); c1.style.marginTop='16px'; sec.appendChild(c1);
  c1.innerHTML = `<h3>Where Al Faihaa sits by size</h3>
    <p class="card-sub">FY2025 revenue, log scale — the TASI names are a different weight class, the Nomu names are the real peer group</p>`;
  const lo = Math.log10(Math.min(...all.map(x=>x.rev))), hi = Math.log10(Math.max(...all.map(x=>x.rev)));
  const w1 = el('div','pk-bars'); c1.appendChild(w1);
  byRev.forEach(x=>{
    const pct = ((Math.log10(x.rev)-lo)/(hi-lo))*94 + 6;
    const row = el('div','pk-row'+(x.hi?' pk-hi':''));
    row.innerHTML = `<div class="pk-lb"><span class="pk-mk pk-mk-${x.mkt==='TASI'?'t':x.mkt==='Nomu'?'n':'p'}">${x.mkt==='private'?'private':x.mkt}</span>${esc(x.name)}</div>
      <div class="pk-tr"><i style="width:${pct.toFixed(1)}%"></i></div>
      <div class="pk-v">${fmtSAR(x.rev)}</div>`;
    w1.appendChild(row);
  });

  /* ---------------- the margin gap ---------------- */
  const c2 = el('div','card'); c2.style.marginTop='16px'; sec.appendChild(c2);
  c2.innerHTML = `<h3>The gap that matters is margin, not size</h3>
    <p class="card-sub">EBITDA margin, FY2025. Being small is not the problem — the smallest listed peer on this page earns a better margin than Al Faihaa does</p>`;
  const byM = all.slice().sort((a,b)=>b.ebitda_margin-a.ebitda_margin);
  const mMax = Math.max(...byM.map(x=>x.ebitda_margin));
  const w2 = el('div','pk-bars'); c2.appendChild(w2);
  byM.forEach(x=>{
    const row = el('div','pk-row'+(x.hi?' pk-hi':''));
    row.innerHTML = `<div class="pk-lb"><span class="pk-mk pk-mk-${x.mkt==='TASI'?'t':x.mkt==='Nomu'?'n':'p'}">${x.mkt==='private'?'private':x.mkt}</span>${esc(x.name)}</div>
      <div class="pk-tr"><i style="width:${(x.ebitda_margin/mMax*100).toFixed(1)}%"></i></div>
      <div class="pk-v">${(x.ebitda_margin*100).toFixed(1)}%</div>`;
    w2.appendChild(row);
  });
  c2.appendChild(el('div','note', `<b>Read it plainly.</b> Al Faihaa turned ${fmtSAR(SUB.rev)} of FY2025 revenue into ${fmtSAR(SUB.ebitda)} of EBITDA — ${(SUB.ebitda_margin*100).toFixed(1)}%. The median Nomu-listed provider, on a fraction of the revenue, earns ${(P.med.Nomu.ebitda_margin*100).toFixed(1)}%. Closing to the Nomu median on FY2025 revenue would be worth about ${fmtSAR(SUB.rev*P.med.Nomu.ebitda_margin - SUB.ebitda)} of additional EBITDA a year. The Costing tabs show where the leakage is at service level; the IFRS 18 statement shows that in FY2025 rental income, not the clinics, carried the group.`));

  /* ---------------- the peer table ---------------- */
  const c3 = el('div','card'); c3.style.marginTop='16px'; sec.appendChild(c3);
  let h = `<h3>The Saudi listed universe</h3>
    <p class="card-sub">Every listed provider on both markets. Revenue, operating profit and net income are audited FY2025; market cap, enterprise value and EBITDA are as of the date shown per company</p>
    <div class="aud-x"><table class="aud-t pk-t"><thead><tr>
      <th>Market</th><th>Ticker</th><th>Company</th><th class="n">Revenue FY25</th><th class="n">EBITDA</th>
      <th class="n">Margin</th><th class="n">Net income</th><th class="n">EV</th><th class="n">EV/Rev</th>
      <th class="n">EV/EBITDA</th><th class="n">P/E</th><th class="n">Data as of</th></tr></thead><tbody>`;
  const row = p => `<tr${p.hi?' class="pk-subj"':''}>
      <td><span class="pk-mk pk-mk-${p.mkt==='TASI'?'t':p.mkt==='Nomu'?'n':'p'}">${p.mkt==='private'?'private':p.mkt}</span></td>
      <td class="mono">${p.ticker}</td><td>${esc(p.name)}<span class="pk-note">${esc(p.note||'')}</span></td>
      <td class="n">${fmtSAR(p.rev)}</td><td class="n">${p.ebitda?fmtSAR(p.ebitda):'—'}</td>
      <td class="n">${(p.ebitda_margin*100).toFixed(1)}%</td><td class="n">${fmtSAR(p.ni)}</td>
      <td class="n">${p.ev?fmtSAR(p.ev):'—'}</td>
      <td class="n">${p.ev_rev?p.ev_rev.toFixed(2)+'x'+(p.computed?'<sup>c</sup>':''):'—'}</td>
      <td class="n">${p.ev_ebitda?p.ev_ebitda.toFixed(2)+'x'+(p.computed?'<sup>c</sup>':''):'—'}</td>
      <td class="n">${p.pe?p.pe.toFixed(1)+'x':'—'}</td><td class="n pk-dt">${p.asof||'—'}</td></tr>`;
  ['TASI','Nomu'].forEach(m=>{
    h += `<tr class="pk-hd"><td colspan="12">${m==='TASI'?'Tadawul main market · TASI':'Parallel market · Nomu'}</td></tr>`;
    P.peers.filter(p=>p.mkt===m).sort((a,b)=>b.rev-a.rev).forEach(p=>{ h += row(p); });
    const M = P.med[m];
    h += `<tr class="pk-med"><td colspan="3"><b>${m} median</b> (${M.n} companies)</td><td colspan="2"></td>
      <td class="n"><b>${(M.ebitda_margin*100).toFixed(1)}%</b></td><td colspan="2"></td>
      <td class="n"><b>${M.ev_rev.toFixed(2)}x</b></td><td class="n"><b>${M.ev_ebitda.toFixed(2)}x</b></td><td colspan="2"></td></tr>`;
  });
  h += `<tr class="pk-hd"><td colspan="12">Subject</td></tr>` + row(Object.assign({}, SUB, {ticker:'—', mkt:'private', ev:null, ev_rev:null, ev_ebitda:null, pe:null, asof:'FY2025 audited', note:'Four branches — Riyadh, Buraydah 1, Buraydah 2, Rafha', hi:true}));
  h += `</tbody></table></div>
    <p class="card-sub" style="margin-top:10px"><sup>c</sup> computed as (market cap + net debt) ÷ revenue or ÷ EBITDA rather than taken from the source. Everything else is the reported multiple.</p>`;
  c3.innerHTML = h;

  /* ---------------- excluded ---------------- */
  const c4 = el('div','card'); c4.style.marginTop='16px'; sec.appendChild(c4);
  c4.innerHTML = `<h3>Listed, healthcare, and deliberately left out</h3>
    <p class="card-sub">These trade in the same sector classification but do not run clinics or hospitals, so including them would flatter or distort the medians</p>
    <table class="aud-t pk-t"><tbody>${P.excluded.map(e=>
      `<tr><td><span class="pk-mk pk-mk-${e.mkt==='TASI'?'t':'n'}">${e.mkt}</span></td><td class="mono">${e.ticker}</td>
       <td>${esc(e.name)}</td><td style="color:var(--ink-muted)">${esc(e.why)}</td></tr>`).join('')}</tbody></table>`;

  /* ---------------- SWOT, grounded in the Saudi comparison ---------------- */
  const sw = el('div','swot-grid'); sw.style.marginTop='16px'; sec.appendChild(sw);
  sw.innerHTML = `
    <div class="swot-box swot-s"><h4>Strengths</h4><ul>
      <li>At ${fmtSAR(SUB.rev)} of revenue Al Faihaa is larger than ${P.peers.filter(p=>p.mkt==='Nomu'&&p.rev<SUB.rev).length} of the ${P.med.Nomu.n} Nomu-listed providers — it already has the scale several of them listed on.</li>
      <li>Four sites across three cities. Most Nomu-listed providers run one facility; ${above?esc(above.name.split('(')[0].trim()):'the largest'} is the only one with a comparable footprint.</li>
      <li>Debt/equity of ${fmtX(R.debt_to_equity[i25])} at FY2025 against a sector where Dallah and Almoosa carry 5.7× and 4.7× net debt to EBITDA.</li>
    </ul></div>
    <div class="swot-box swot-w"><h4>Weaknesses</h4><ul>
      <li><b>Margin.</b> ${(SUB.ebitda_margin*100).toFixed(1)}% EBITDA against a Nomu median of ${(P.med.Nomu.ebitda_margin*100).toFixed(1)}% and a TASI median of ${(P.med.TASI.ebitda_margin*100).toFixed(1)}%. Every single listed provider on both markets earns more per riyal of revenue.</li>
      <li>FY2025 operating profit under IFRS 18 was ${fmtSAR(564292)} — the clinics roughly broke even and rental income carried the year.</li>
      <li>Current ratio ${fmtX(R.current_ratio[i25])} at FY2025, down from 4.1× at FY2023.</li>
    </ul></div>
    <div class="swot-box swot-o"><h4>Opportunities</h4><ul>
      <li>The margin gap is the whole opportunity: closing to the Nomu median on today's revenue is worth roughly ${fmtSAR(SUB.rev*P.med.Nomu.ebitda_margin - SUB.ebitda)} of EBITDA a year, with no new site and no new patient.</li>
      <li>Nomu is a realistic listing venue at this size — Basma Adeem listed in Feb 2026 on ${fmtSAR(45.5e6)} of revenue, well below Al Faihaa's. Margin, not scale, is what would need fixing first.</li>
      <li>2026 YTD EBITDA margin is ${fmtPct(R.ebitda_margin[i26],1)} against ${fmtPct(R.ebitda_margin[i25],1)} for FY2025 — the trend has turned.</li>
    </ul></div>
    <div class="swot-box swot-t"><h4>Threats</h4><ul>
      <li>Insurer concentration: the listed operators negotiate with the same payers from a far larger base, and Al Faihaa's own ledger books an annual insurance claim deduction of ${fmtSAR(3653273)} in a single December entry.</li>
      <li>Middle East Healthcare's shares fell ~47% over the past year on a 19% EBITDA margin. The market is not paying for revenue in this sector without earnings behind it.</li>
      <li>Al Hammadi, Almoosa and HMG are all adding Riyadh or Eastern Province capacity through 2026–28, into the same catchment.</li>
    </ul></div>`;

  sec.appendChild(el('div','note', `<b>Sources.</b> Market capitalisation, enterprise value, net debt, trailing EBITDA and P/E from StockAnalysis.com, with each company's data date shown in the table (22 July – 24 September 2026); revenue, operating profit and net income from the audited FY2025 statements, all peers on a 31 December year-end; listings, tickers and company profiles from the Saudi Exchange and Argaam. Al Faihaa's own figures come from the FS model and the EXSYS ledger, refreshed ${DATA.ext.asOf||'24 Sep 2026'}. <b>Two limits worth naming:</b> peer EBITDA is trailing twelve months while revenue is FY2025, so the margins are not perfectly period-matched; and six of the peer market caps are a month or more old, so their multiples move with the share price and should be read as indicative rather than live.`));
})();
