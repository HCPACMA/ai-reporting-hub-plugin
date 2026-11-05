
/* ======================================================================
   Trading Comparables · Saudi-listed healthcare providers only
   ====================================================================== */
(function(){
  const sec = document.getElementById('sec-comps'); if(!sec) return;
  const P = DATA.peers; if(!P) return;
  const Y = DATA.ext.years, i25 = Y.indexOf(2025);
  const rev = DATA.ext.is_.total_revenue[i25], ebitda = DATA.ext.is_.ebitda[i25];
  const nd = DATA.ext.ratios_full.net_debt[i25];
  const d = P.discount;

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Valuation</div>
    <h2>Trading Comparables · Saudi market</h2>
    <p>Every healthcare provider listed in Saudi Arabia — ${P.med.TASI.n} on TASI, ${P.med.Nomu.n} on Nomu — and nothing else. Al Faihaa competes domestically, so an international peer set would price it against markets it does not operate in. <b>Nomu is the reference set</b>: on revenue the smallest TASI name is still 20× larger. Peer data ${P.asof}; the implied multiples apply a disclosed private-company discount and are not sourced figures.</p>
  `));

  const card = el('div','card');
  let h = `<h3>Peer set</h3><p class="card-sub">Sorted by revenue within each market</p>
    <div class="aud-x"><table class="aud-t pk-t"><thead><tr><th>Ticker</th><th>Company</th>
    <th class="n">Revenue FY25</th><th class="n">EBITDA margin</th><th class="n">EV/Revenue</th><th class="n">EV/EBITDA</th></tr></thead><tbody>`;
  ['Nomu','TASI'].forEach(m=>{
    h += `<tr class="pk-hd"><td colspan="6">${m==='TASI'?'Tadawul main market · TASI — scale reference only':'Parallel market · Nomu — the comparable set'}</td></tr>`;
    P.peers.filter(p=>p.mkt===m).sort((a,b)=>b.rev-a.rev).forEach(p=>{
      h += `<tr><td class="mono">${p.ticker}</td><td>${esc(p.name)}</td>
        <td class="n">${fmtSAR(p.rev)}</td><td class="n">${(p.ebitda_margin*100).toFixed(1)}%</td>
        <td class="n assump">${p.ev_rev.toFixed(2)}x${p.computed?'<sup>c</sup>':''}</td>
        <td class="n assump">${p.ev_ebitda.toFixed(2)}x${p.computed?'<sup>c</sup>':''}</td></tr>`;
    });
    const M = P.med[m];
    h += `<tr class="pk-med"><td colspan="3"><b>${m} median</b></td><td class="n"><b>${(M.ebitda_margin*100).toFixed(1)}%</b></td>
      <td class="n"><b>${M.ev_rev.toFixed(2)}x</b></td><td class="n"><b>${M.ev_ebitda.toFixed(2)}x</b></td></tr>`;
  });
  h += `</tbody></table></div>
    <p class="card-sub" style="margin-top:10px"><sup>c</sup> computed from (market cap + net debt) rather than taken from the source.</p>`;
  card.innerHTML = h; sec.appendChild(card);

  const c2 = el('div','card'); c2.style.marginTop='16px'; sec.appendChild(c2);
  const rows = [];
  ['Nomu','TASI'].forEach(m=>{
    const M = P.med[m];
    rows.push([`${m} median EV/Revenue`, M.ev_rev.toFixed(2)+'x', true]);
    rows.push([`${m} median EV/EBITDA`, M.ev_ebitda.toFixed(2)+'x', true]);
    rows.push([`&nbsp;&nbsp;→ implied EV on FY2025 revenue`, fmtSARFull(rev*M.ev_rev*d), false]);
    rows.push([`&nbsp;&nbsp;→ implied EV on FY2025 EBITDA`, fmtSARFull(ebitda*M.ev_ebitda*d), false]);
  });
  c2.innerHTML = `<h3>Implied valuation for Al Faihaa Group</h3>
    <p class="card-sub">FY2025 revenue ${fmtSARFull(rev)} · EBITDA ${fmtSARFull(ebitda)} (${(ebitda/rev*100).toFixed(1)}% margin) · net debt ${fmtSARFull(nd)}</p>
    <table class="aud-t pk-t"><tbody>
    <tr><td>Private-company discount applied to every peer multiple</td><td class="n assump">${((1-d)*100).toFixed(0)}%</td></tr>
    ${rows.map(([l,v,a])=>`<tr><td>${l}</td><td class="n${a?' assump':''}">${v}</td></tr>`).join('')}
    </tbody></table>
    <div class="note" style="margin-top:14px"><b>The two answers disagree, and that is the finding.</b> On revenue the Nomu median values Al Faihaa at about ${fmtSAR(rev*P.med.Nomu.ev_rev*d)}. On EBITDA it values the same company at about ${fmtSAR(ebitda*P.med.Nomu.ev_ebitda*d)} — a third as much. The whole gap is margin: ${(ebitda/rev*100).toFixed(1)}% against a Nomu median of ${(P.med.Nomu.ebitda_margin*100).toFixed(1)}%. A buyer pays for earnings, so the EBITDA figure is the one to plan around, and the revenue figure is what the business would be worth if it earned what its listed peers earn.</div>
    <div class="note" style="margin-top:10px"><b>What this is not.</b> A median of ${P.med.Nomu.n} Nomu companies is a thin sample, three of them single-site. The ${((1-d)*100).toFixed(0)}% discount is a judgment for being unlisted and unable to offer a buyer liquidity — it is stated here rather than buried, and it is the single assumption that moves these numbers most. Peer EBITDA is trailing twelve months against FY2025 revenue, so the margins are not perfectly period-matched, and six peer market caps are a month or more old.</div>`;
})();
