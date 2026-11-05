/* ---- Department Assessment ---- */
(function(){
  const sec = document.getElementById('sec-dept');
  const DP = DATA.dept, BRN = DP.branches, YD = DP.ytd_days, ANNFAC = 365/YD;
  const asOfTxt = new Date(DP.asOf+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Departments</div>
    <h2>Department Assessment</h2>
    <p>Revenue, direct cost and contribution by clinical department, for each branch or the group, read from the cost centre on every journal line in the four EXSYS ledgers. Pick a branch, a period and the view recalculates.</p>
  `));

  const filterBar = el('div','filter-bar');
  filterBar.innerHTML = `
    <div class="filter-group">
      <div class="filter-field"><label for="dept-branch">Branch</label>
        <select id="dept-branch"><option value="all">All branches</option>${Object.entries(BRN).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></div>
      <div class="filter-field"><label for="dept-period">Period</label>
        <select id="dept-period"><option value="2026">FY2026 YTD (1 Jan – ${asOfTxt})</option><option value="2025">FY2025 (full year)</option></select></div>
    </div>
    <div class="as-of" id="dept-asof"></div>`;
  sec.appendChild(filterBar);

  const kpiWrap = el('div','grid grid-4'); kpiWrap.style.marginTop='4px'; sec.appendChild(kpiWrap);
  const tableCard = el('div','card'); tableCard.style.marginTop='16px'; sec.appendChild(tableCard);
  const chartsRow = el('div','grid grid-2'); chartsRow.style.marginTop='16px'; sec.appendChild(chartsRow);
  const revChartCard = el('div','card'), marginChartCard = el('div','card');
  chartsRow.appendChild(revChartCard); chartsRow.appendChild(marginChartCard);
  const brCard = el('div','card'); brCard.style.marginTop='16px'; sec.appendChild(brCard);
  sec.appendChild(el('div','note', DP.note));

  function agg(list, branch){
    const src = branch==='all' ? list : list.filter(r=>r.branch===branch);
    const m = {};
    src.forEach(r=>{
      const k = branch==='all' ? r.key : r.dept_no;
      const o = m[k] || (m[k] = {key:r.key, name:r.name, cash:0, credit:0, cost:0});
      o.cash += r.cash; o.credit += r.credit; o.cost += r.cost_dr - r.cost_cr;
    });
    return Object.values(m).map(o=>({...o, revenue:o.cash+o.credit}));
  }
  function rowsFor(period, branch){
    const cur = agg(period==='2026'?DP.all_2026ytd:DP.all_2025, branch);
    const base = Object.fromEntries(agg(DP.all_2025, branch).map(r=>[r.key,r]));
    return cur.map(r=>{
      const contribution = r.revenue - r.cost;
      const margin = r.revenue > 0 ? contribution / r.revenue : null;
      const b = base[r.key];
      const yoy = (period==='2026' && b && b.revenue > 0) ? (r.revenue*ANNFAC)/b.revenue - 1 : null;
      return {...r, contribution, margin, yoy};
    }).filter(r=>Math.abs(r.revenue)>1 || Math.abs(r.cost)>1).sort((a,b)=>b.revenue-a.revenue);
  }

  function render(){
    const period = document.getElementById('dept-period').value;
    const branch = document.getElementById('dept-branch').value;
    const bname = branch==='all' ? 'All branches' : BRN[branch];
    const rows = rowsFor(period, branch);
    const withRev = rows.filter(r=>r.revenue>0);
    const totRev = rows.reduce((s,r)=>s+r.revenue,0), totCost = rows.reduce((s,r)=>s+r.cost,0);
    const totContrib = totRev - totCost;
    const top = withRev[0];
    document.getElementById('dept-asof').innerHTML = period==='2026'
      ? `ledger read ${asOfTxt} &middot; ${YD} days (${fmtPct(YD/365)} of FY2026)` : `FY2025 &middot; full year, closed`;

    kpiWrap.innerHTML = '';
    [
      ['Department revenue', fmtSAR(totRev), `${bname} · ${period==='2026'?'FY2026 YTD':'FY2025'}`],
      ['Contribution', fmtSAR(totContrib), totRev ? fmtPct(totContrib/totRev)+' of revenue, before overhead' : '—'],
      ['Direct cost', fmtSAR(totCost), 'salaries · consumables · commissions'],
      ['Top department', top ? top.name : '—', top ? fmtSAR(top.revenue)+' revenue' : ''],
    ].forEach(([label,val,sub])=>{
      const c = el('div','card kpi');
      c.innerHTML = `<div class="label">${label}</div><div class="value num" style="font-size:22px">${val}</div><div class="delta flat">${sub}</div>`;
      kpiWrap.appendChild(c);
    });

    const mc = r => r.margin===null ? 'var(--ink-faint)' : (marginPillClass(r.margin)==='good'?'var(--good)':marginPillClass(r.margin)==='warn'?'var(--warning)':'var(--critical)');
    const wrap = el('div','tbl-scroll'); const t = el('table');
    t.innerHTML = '<tr><th>Department</th><th>Cash rev</th><th>Credit rev</th><th>Total rev</th><th>Direct cost</th><th>Contribution</th><th>Margin</th><th>'+(period==='2026'?'vs FY2025 (ann.)':'&nbsp;')+'</th></tr>'
      + rows.map(r=>`<tr><td>${r.name}</td><td class="num">${fmtSARFull(r.cash)}</td><td class="num">${fmtSARFull(r.credit)}</td><td class="num" style="font-weight:600">${fmtSARFull(r.revenue)}</td><td class="num">${fmtSARFull(r.cost)}</td><td class="num ${r.contribution<0?'neg':''}">${fmtSARFull(r.contribution)}</td><td class="num" style="color:${mc(r)};font-weight:600">${r.margin===null?'—':fmtPct(r.margin)}</td><td class="num">${r.yoy===null?'—':(r.yoy>=0?'+':'')+fmtPct(r.yoy)}</td></tr>`).join('')
      + `<tr style="font-weight:700"><td>Total</td><td class="num">${fmtSARFull(rows.reduce((s,r)=>s+r.cash,0))}</td><td class="num">${fmtSARFull(rows.reduce((s,r)=>s+r.credit,0))}</td><td class="num">${fmtSARFull(totRev)}</td><td class="num">${fmtSARFull(totCost)}</td><td class="num">${fmtSARFull(totContrib)}</td><td class="num">${totRev?fmtPct(totContrib/totRev):'—'}</td><td></td></tr>`;
    wrap.appendChild(t);
    tableCard.innerHTML = '';
    tableCard.appendChild(el('h3',null, `Departments — ${bname}, ${period==='2026'?'FY2026 YTD':'FY2025'}`));
    tableCard.appendChild(el('p','card-sub', `Sorted by revenue · ${branch==='all'?'the same department in each branch is added together · ':''}the FY2026 comparison annualises year-to-date revenue over ${YD} days · SAR`));
    tableCard.appendChild(wrap);
    tableCard.appendChild(el('div','note', `Departments with cost and no revenue — laboratory, radiology, emergency and pharmacy in most branches — are support units: their revenue is billed through the clinics that order the test or the dispensing, so a negative contribution there is expected and is not a loss on its own.`));

    revChartCard.innerHTML = `<h3>Revenue by department</h3><p class="card-sub">${bname} · top 10 · <span style="color:${PALETTE.cash};font-weight:700">■</span> cash <span style="color:${PALETTE.net};font-weight:700">■</span> credit</p>`;
    revChartCard.appendChild(buildHBarList(withRev.slice(0,10).map(r=>({label:r.name, values:[{v:Math.max(r.cash,0),color:PALETTE.cash},{v:Math.max(r.credit,0),color:PALETTE.net}]})), {labelWidth:'170px', valueWidth:'130px'}));

    marginChartCard.innerHTML = `<h3>Contribution margin</h3><p class="card-sub">revenue less direct cost · revenue-earning departments</p>`;
    const wm = withRev.filter(r=>r.margin!==null).slice(0,10);
    const maxM = Math.max(...wm.map(r=>Math.abs(r.margin)), 0.01);
    const mw = el('div'); mw.style.cssText='display:flex;flex-direction:column;gap:9px;margin-top:6px;';
    wm.forEach(r=>{
      const color = mc(r);
      const row = el('div'); row.style.cssText='display:grid;grid-template-columns:170px 1fr 60px;align-items:center;gap:10px;';
      row.innerHTML = `<div style="font-size:12.5px" title="${r.name}">${r.name.length>26?r.name.slice(0,25)+'…':r.name}</div><div style="background:var(--surface-2);border-radius:5px;height:14px;overflow:hidden"><div style="background:${color};height:100%;width:${(Math.max(r.margin,0)/maxM*100).toFixed(2)}%"></div></div><div style="font-size:12px;text-align:right;font-variant-numeric:tabular-nums;color:${color};font-weight:700">${fmtPct(r.margin)}</div>`;
      mw.appendChild(row);
    });
    marginChartCard.appendChild(mw);

    // branch comparison
    const bl = Object.keys(BRN).map(k=>{
      const r = rowsFor(period,k); const rev=r.reduce((s,x)=>s+x.revenue,0), cost=r.reduce((s,x)=>s+x.cost,0);
      return {k, rev, cost, n:r.filter(x=>x.revenue>0).length};
    });
    brCard.innerHTML = `<h3>Branches side by side</h3><p class="card-sub">${period==='2026'?'FY2026 YTD':'FY2025'} · department revenue and direct cost</p>
      <div class="tbl-scroll"><table><tr><th>Branch</th><th>Revenue-earning departments</th><th>Revenue</th><th>Direct cost</th><th>Contribution</th><th>Margin</th></tr>
      ${bl.map(b=>`<tr><td>${BRN[b.k]}</td><td class="num">${b.n}</td><td class="num">${fmtSARFull(b.rev)}</td><td class="num">${fmtSARFull(b.cost)}</td><td class="num">${fmtSARFull(b.rev-b.cost)}</td><td class="num">${b.rev?fmtPct((b.rev-b.cost)/b.rev):'—'}</td></tr>`).join('')}</table></div>`;
  }
  ['dept-period','dept-branch'].forEach(id=>document.getElementById(id).addEventListener('change', render));
  render();
})();

/* ---- Cost Center Assessment ---- */
(function(){
  const sec = document.getElementById('sec-costcenter');
  const escH = s => String(s == null ? '' : s).replace(/[&<>"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
  const CCD = DATA.cc, cc = CCD.cost_centers, BRN = CCD.branches, YD = CCD.ytd_days, ANNFAC = 365/YD;
  const asOfTxt = new Date(CCD.asOf+'T00:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});
  const depts = [...new Set(cc.map(r=>r.dept))].sort();

  sec.appendChild(el('div','section-head', `
    <div class="eyebrow">Departments</div>
    <h2>Cost Center Assessment</h2>
    <p>Revenue, direct cost and contribution for every doctor and clinic cost centre in the four ledgers. Filter by branch and department; the view recalculates.</p>
  `));
  const filterBar = el('div','filter-bar');
  filterBar.innerHTML = `
    <div class="filter-group">
      <div class="filter-field"><label for="cc-branch">Branch</label>
        <select id="cc-branch"><option value="all">All branches</option>${Object.entries(BRN).map(([k,v])=>`<option value="${k}">${v}</option>`).join('')}</select></div>
      <div class="filter-field"><label for="cc-dept">Department</label>
        <select id="cc-dept"><option value="all">All departments</option>${depts.map(d=>`<option value="${escH(d)}">${escH(d)}</option>`).join('')}</select></div>
      <div class="filter-field"><label for="cc-period">Period</label>
        <select id="cc-period"><option value="2026">FY2026 YTD (1 Jan – ${asOfTxt})</option><option value="2025">FY2025 (full year)</option></select></div>
    </div>
    <div class="as-of" id="cc-asof"></div>`;
  sec.appendChild(filterBar);
  const kpiWrap = el('div','grid grid-4'); kpiWrap.style.marginTop='4px'; sec.appendChild(kpiWrap);
  const tableCard = el('div','card'); tableCard.style.marginTop='16px'; sec.appendChild(tableCard);
  const chartsRow = el('div','grid grid-2'); chartsRow.style.marginTop='16px'; sec.appendChild(chartsRow);
  const revChartCard = el('div','card'), lossCard = el('div','card');
  chartsRow.appendChild(revChartCard); chartsRow.appendChild(lossCard);
  sec.appendChild(el('div','note', CCD.note));

  function render(){
    const period = document.getElementById('cc-period').value, s = period;
    const branch = document.getElementById('cc-branch').value, dept = document.getElementById('cc-dept').value;
    let rows = cc.filter(r=>(branch==='all'||r.branch===branch) && (dept==='all'||r.dept===dept)).map(r=>{
      const cash=r['cash_'+s], credit=r['credit_'+s], revenue=cash+credit, cost=r['cost_'+s];
      const contribution=revenue-cost, margin=revenue>0?contribution/revenue:null;
      const b = r.cash_2025 + r.credit_2025;
      const yoy = (period==='2026' && b>0) ? (revenue*ANNFAC)/b - 1 : null;
      return {name:r.name, org:r.org_no, br:BRN[r.branch], dept:r.dept, cash, credit, revenue, cost, contribution, margin, yoy};
    }).filter(r=>r.revenue>1).sort((a,b)=>b.revenue-a.revenue);
    const totRev = rows.reduce((x,r)=>x+r.revenue,0), totCost = rows.reduce((x,r)=>x+r.cost,0);
    const losers = rows.filter(r=>r.contribution<0);
    document.getElementById('cc-asof').innerHTML = period==='2026' ? `ledger read ${asOfTxt} &middot; ${YD} days of FY2026` : 'FY2025 &middot; full year, closed';
    kpiWrap.innerHTML='';
    [
      ['Clinic revenue', fmtSAR(totRev), `${rows.length} clinics with revenue`],
      ['Contribution', fmtSAR(totRev-totCost), totRev?fmtPct((totRev-totCost)/totRev)+' of revenue':'—'],
      ['Clinics below direct cost', String(losers.length), losers.length?fmtSAR(losers.reduce((x,r)=>x+r.contribution,0))+' combined':'none'],
      ['Top clinic', rows[0]?`<span dir="rtl" style="font-size:17px">${escH(rows[0].name)}</span>`:'—', rows[0]?fmtSAR(rows[0].revenue)+' · '+rows[0].br:''],
    ].forEach(([label,val,sub])=>{
      const c = el('div','card kpi');
      c.innerHTML = `<div class="label">${label}</div><div class="value num" style="font-size:20px">${val}</div><div class="delta flat">${sub}</div>`;
      kpiWrap.appendChild(c);
    });
    const mc = r => r.margin===null ? 'var(--ink-faint)' : (marginPillClass(r.margin)==='good'?'var(--good)':marginPillClass(r.margin)==='warn'?'var(--warning)':'var(--critical)');
    const wrap = el('div','tbl-scroll'); wrap.style.maxHeight='620px';
    const t = el('table');
    t.innerHTML = '<tr><th>Clinic</th><th>Branch</th><th>Department</th><th>Cash rev</th><th>Credit rev</th><th>Total rev</th><th>Direct cost</th><th>Contribution</th><th>Margin</th><th>'+(period==='2026'?'vs FY2025 (ann.)':'&nbsp;')+'</th></tr>'
      + rows.map(r=>`<tr><td dir="rtl" style="text-align:right;min-width:170px">${escH(r.name)}<span style="display:block;color:var(--ink-faint);font-size:11px"><bdi>${r.org}</bdi></span></td><td style="font-size:12px">${r.br}</td><td style="font-size:12px;color:var(--ink-muted)">${escH(r.dept)}</td><td class="num">${fmtSARFull(r.cash)}</td><td class="num">${fmtSARFull(r.credit)}</td><td class="num" style="font-weight:600">${fmtSARFull(r.revenue)}</td><td class="num">${fmtSARFull(r.cost)}</td><td class="num ${r.contribution<0?'neg':''}">${fmtSARFull(r.contribution)}</td><td class="num" style="color:${mc(r)};font-weight:600">${r.margin===null?'—':fmtPct(r.margin)}</td><td class="num">${r.yoy===null?'—':(r.yoy>=0?'+':'')+fmtPct(r.yoy)}</td></tr>`).join('');
    wrap.appendChild(t);
    tableCard.innerHTML='';
    tableCard.appendChild(el('h3',null,`Clinics — ${branch==='all'?'all branches':BRN[branch]}${dept==='all'?'':', '+escH(dept)}, ${period==='2026'?'FY2026 YTD':'FY2025'}`));
    tableCard.appendChild(el('p','card-sub','Sorted by revenue · every clinic with revenue in the period · SAR'));
    tableCard.appendChild(wrap);

    revChartCard.innerHTML = `<h3>Top 10 clinics by revenue</h3><p class="card-sub"><span style="color:${PALETTE.cash};font-weight:700">■</span> cash <span style="color:${PALETTE.net};font-weight:700">■</span> credit</p>`;
    revChartCard.appendChild(buildHBarList(rows.slice(0,10).map(r=>({label:r.name+' · '+r.br, values:[{v:Math.max(r.cash,0),color:PALETTE.cash},{v:Math.max(r.credit,0),color:PALETTE.net}]})), {labelWidth:'190px', valueWidth:'130px'}));
    lossCard.innerHTML = `<h3>Clinics below direct cost</h3><p class="card-sub">revenue did not cover the cost tagged to the clinic · a reason to look, not a verdict</p>`;
    const lw = el('div','tbl-scroll'); const lt = el('table');
    lt.innerHTML = '<tr><th>Clinic</th><th>Branch</th><th>Revenue</th><th>Direct cost</th><th>Shortfall</th></tr>' + (losers.length ? losers.sort((a,b)=>a.contribution-b.contribution).slice(0,12).map(r=>`<tr><td dir="rtl" style="text-align:right">${escH(r.name)}</td><td style="font-size:12px">${r.br}</td><td class="num">${fmtSARFull(r.revenue)}</td><td class="num">${fmtSARFull(r.cost)}</td><td class="num neg">${fmtSARFull(r.contribution)}</td></tr>`).join('') : '<tr><td colspan="5">None in this selection.</td></tr>');
    lw.appendChild(lt); lossCard.appendChild(lw);
  }
  ['cc-period','cc-branch','cc-dept'].forEach(id=>document.getElementById(id).addEventListener('change', render));
  render();
})();
