
/* ======================================================================
   TIME INTELLIGENCE  ·  global period + cost-centre filter
   ====================================================================== */
const TIM = DATA.m;
const TIMONTHS = TIM.months;
const AR_MON = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
const EN_MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const LAST_I = TIMONTHS.length - 1;                       // 2026-09
const mYear = i => +TIMONTHS[i].slice(0,4);
const mMon  = i => +TIMONTHS[i].slice(5,7) - 1;           // 0-based
const mLabEN = i => EN_MON[mMon(i)] + ' ' + mYear(i);
const mLabAR = i => AR_MON[mMon(i)] + ' ' + mYear(i);

const TI = {
  grain : 'Y',          // 'M' | 'Q' | 'Y' | 'R'
  a     : 36,           // first month index (2026-01)
  b     : LAST_I,       // last month index
  cc    : 'ALL',
  cmp   : true,
  subs  : [],
  on(fn){ this.subs.push(fn); },
  fire(){ this.subs.forEach(f => { try{ f(); }catch(e){ console.error(e); } }); }
};

/* ---------- aggregation over the bucket series ---------- */
function _ccList(cc){ return cc === 'ALL' ? TIM.ccs : [cc]; }

/* flow: sum of monthly movements a..b, raw GL sign (DR-CR) */
function flow(codes, a, b, cc){
  if(a < 0 || b < a) return null;
  let t = 0;
  for(const c of codes) for(const k of _ccList(cc)){
    const s = TIM.series[c + '|' + k]; if(!s) continue;
    for(let i = a; i <= b; i++) t += s[i];
  }
  return t;
}
/* stock: cumulative balance at the END of month b, raw GL sign */
function stock(codes, b, cc){
  if(b < 0) return null;
  let t = 0;
  for(const c of codes) for(const k of _ccList(cc)){
    t += (TIM.open[c + '|' + k] || 0);
    const s = TIM.series[c + '|' + k]; if(!s) continue;
    for(let i = 0; i <= b; i++) t += s[i];
  }
  return t;
}
/* ---------- derived P&L for a window ---------- */
function pnl(a, b, cc){
  if(a < 0 || b < a) return null;
  const revenue = -flow(TIM.rev, a, b, cc);
  const contra  =  flow(TIM.revContra, a, b, cc);
  const expense =  flow(TIM.exp, a, b, cc) + contra;
  const dep     =  flow(['B13'], a, b, cc);
  const net     =  revenue - expense;
  return { revenue, expense, net, dep,
           ebitda: net + dep,
           margin: revenue ? net / revenue : null,
           cashRev: -flow(['B08'], a, b, cc),
           credRev: -flow(['B10'], a, b, cc),
           othRev : -flow(['B27'], a, b, cc),
           salaries: flow(['B33'], a, b, cc) };
}
/* ---------- financial position at a point ---------- */
function position(b, cc){
  if(b < 0) return null;
  const ca  =  stock(TIM.currentAssets, b, cc);
  const cl  = -stock(TIM.currentLiab, b, cc);
  const cash=  stock(['B07'], b, cc);
  const inv =  stock(['B21'], b, cc);
  const debt= -stock(TIM.debt, b, cc) + stock(['B12'], b, cc);
  return { cash, inv,
           ar      : stock(['B02'], b, cc),
           related : stock(['B38'], b, cc),
           fixed   : stock(['B17'], b, cc) + stock(['B29'], b, cc) + stock(['B20'], b, cc),
           currentAssets: ca, currentLiab: cl,
           workingCap   : ca - cl,
           currentRatio : cl ? ca / cl : null,
           quickRatio   : cl ? (ca - inv) / cl : null,
           debt, netDebt: debt - cash,
           eosb: -stock(['B15'], b, cc) };
}
/* ---------- period resolution ---------- */
function periodOptions(grain){
  const out = [];
  if(grain === 'M') TIMONTHS.forEach((m,i) => out.push({v:i+':'+i, en:mLabEN(i), ar:mLabAR(i)}));
  else if(grain === 'Q'){
    for(let i = 0; i <= LAST_I; i += 3){
      const b = Math.min(i+2, LAST_I), q = Math.floor(mMon(i)/3)+1;
      out.push({v:i+':'+b, en:'Q'+q+' '+mYear(i), ar:'الربع '+q+' '+mYear(i)});
    }
  } else {
    for(let y = 2023; y <= 2026; y++){
      const a = TIMONTHS.indexOf(y+'-01'); if(a < 0) continue;
      let b = a; while(b+1 <= LAST_I && mYear(b+1) === y) b++;
      const partial = mMon(b) < 11;
      out.push({v:a+':'+b,
        en:(partial ? y+' YTD (Jan–'+EN_MON[mMon(b)]+')' : 'FY'+y),
        ar:(partial ? y+' حتى تاريخه (يناير–'+AR_MON[mMon(b)]+')' : 'السنة المالية '+y)});
    }
  }
  return out;
}
function cmpWindow(){
  const a = TI.a - 12, b = TI.b - 12;
  return (a >= 0) ? {a, b} : null;
}
function periodLabel(lang){
  const a = TI.a, b = TI.b;
  if(a === b) return lang === 'ar' ? mLabAR(a) : mLabEN(a);
  return lang === 'ar' ? (mLabAR(a) + ' – ' + mLabAR(b)) : (mLabEN(a) + ' – ' + mLabEN(b));
}
function ccLabel(lang){
  if(TI.cc === 'ALL') return lang === 'ar' ? 'المجموعة (كل مراكز التكلفة)' : 'Group (all cost centres)';
  return TIM.ccName[TI.cc][lang === 'ar' ? 1 : 0];
}

/* ---------- the toolbar ---------- */
const tiBar = el('div','ti-bar');
tiBar.innerHTML = `
  <div class="ti-grp"><span class="ti-lab">Grain</span>
    <div class="ti-seg" id="ti-grain">
      <button data-g="M">M-to-M</button><button data-g="Q">Q-to-Q</button>
      <button data-g="Y" class="on">Y-to-Y</button><button data-g="R">Date range</button>
    </div>
  </div>
  <div class="ti-grp" id="ti-pwrap"><span class="ti-lab">Period</span><select id="ti-period"></select></div>
  <div class="ti-grp" id="ti-rwrap" style="display:none"><span class="ti-lab">From</span><select id="ti-from"></select></div>
  <div class="ti-grp" id="ti-rwrap2" style="display:none"><span class="ti-lab">To</span><select id="ti-to"></select></div>
  <div class="ti-grp"><span class="ti-lab">Branch / cost centre</span><select id="ti-cc"></select></div>
  <label class="ti-chk"><input type="checkbox" id="ti-cmp" checked> Compare vs same period last year</label>
  <div class="ti-read" id="ti-read"></div>`;

(function initToolbar(){
  const selCC = tiBar.querySelector('#ti-cc');
  selCC.innerHTML = '<option value="ALL">All — Group consolidated</option>' +
    TIM.ccs.map(k => `<option value="${k}">${k} · ${TIM.ccName[k][0]} — ${TIM.ccName[k][1]}</option>`).join('');
  const optsMonth = TIMONTHS.map((m,i) => `<option value="${i}">${mLabEN(i)}</option>`).join('');
  tiBar.querySelector('#ti-from').innerHTML = optsMonth;
  tiBar.querySelector('#ti-to').innerHTML   = optsMonth;

  function fillPeriods(){
    const opts = periodOptions(TI.grain);
    tiBar.querySelector('#ti-period').innerHTML =
      opts.map(o => `<option value="${o.v}">${o.en}</option>`).join('');
    const want = TI.a + ':' + TI.b;
    const hit = opts.find(o => o.v === want) || opts[opts.length-1];
    tiBar.querySelector('#ti-period').value = hit.v;
    [TI.a, TI.b] = hit.v.split(':').map(Number);
  }
  function syncRangeSelects(){
    tiBar.querySelector('#ti-from').value = TI.a;
    tiBar.querySelector('#ti-to').value   = TI.b;
  }
  function readout(){
    const c = TI.cmp ? cmpWindow() : null;
    tiBar.querySelector('#ti-read').innerHTML =
      `Period <b>${periodLabel('en')}</b> · ${TI.b - TI.a + 1} month${TI.b === TI.a ? '' : 's'}<br>` +
      (c ? `Compared with <b>${mLabEN(c.a)}${c.a === c.b ? '' : ' – ' + mLabEN(c.b)}</b>`
         : `<span class="fl">No comparison period available</span>`) +
      ` · <b>${ccLabel('en')}</b>`;
  }
  tiBar.querySelectorAll('#ti-grain button').forEach(btn => btn.addEventListener('click', () => {
    TI.grain = btn.dataset.g;
    tiBar.querySelectorAll('#ti-grain button').forEach(x => x.classList.toggle('on', x === btn));
    const custom = TI.grain === 'R';
    tiBar.querySelector('#ti-pwrap').style.display  = custom ? 'none' : '';
    tiBar.querySelector('#ti-rwrap').style.display  = custom ? '' : 'none';
    tiBar.querySelector('#ti-rwrap2').style.display = custom ? '' : 'none';
    if(!custom) fillPeriods(); else syncRangeSelects();
    readout(); TI.fire();
  }));
  tiBar.querySelector('#ti-period').addEventListener('change', e => {
    [TI.a, TI.b] = e.target.value.split(':').map(Number); readout(); TI.fire();
  });
  tiBar.querySelector('#ti-from').addEventListener('change', e => {
    TI.a = +e.target.value; if(TI.b < TI.a){ TI.b = TI.a; syncRangeSelects(); } readout(); TI.fire();
  });
  tiBar.querySelector('#ti-to').addEventListener('change', e => {
    TI.b = +e.target.value; if(TI.b < TI.a){ TI.a = TI.b; syncRangeSelects(); } readout(); TI.fire();
  });
  tiBar.querySelector('#ti-cc').addEventListener('change', e => { TI.cc = e.target.value; readout(); TI.fire(); });
  tiBar.querySelector('#ti-cmp').addEventListener('change', e => { TI.cmp = e.target.checked; readout(); TI.fire(); });

  fillPeriods(); syncRangeSelects(); readout();
  main.insertBefore(tiBar, main.firstChild);
})();

/* ---------- per-page period strip ---------- */
function deltaHTML(cur, prev, betterUp = true){
  if(prev === null || prev === undefined || !isFinite(prev) || prev === 0) return '<span class="fl">—</span>';
  const d = cur - prev, p = d / Math.abs(prev);
  const good = betterUp ? d >= 0 : d <= 0;
  const cls = Math.abs(p) < 0.0005 ? 'fl' : (good ? 'up' : 'dn');
  return `<span class="${cls}">${d >= 0 ? '+' : '−'}${fmtM(Math.abs(d))} (${d >= 0 ? '+' : '−'}${(Math.abs(p)*100).toFixed(1)}%)</span>`;
}
SECTIONS.forEach(s => {
  const sec = document.getElementById('sec-' + s.id); if(!sec) return;
  const strip = el('div','ps'); strip.id = 'ps-' + s.id;
  sec.insertBefore(strip, sec.firstChild);
});
function renderStrips(){
  const cur = pnl(TI.a, TI.b, TI.cc);
  const cw  = TI.cmp ? cmpWindow() : null;
  const prv = cw ? pnl(cw.a, cw.b, TI.cc) : null;
  const pos = position(TI.b, TI.cc);
  const cells = [
    ['Revenue',    fmtSAR(cur.revenue), prv ? deltaHTML(cur.revenue, prv.revenue, true) : ''],
    ['Expenses',   fmtSAR(cur.expense), prv ? deltaHTML(cur.expense, prv.expense, false) : ''],
    ['Net result', fmtSAR(cur.net),     prv ? deltaHTML(cur.net, prv.net, true) : ''],
    ['Net margin', fmtPct(cur.margin),  prv && prv.margin !== null
        ? `<span class="${cur.margin >= prv.margin ? 'up' : 'dn'}">${cur.margin >= prv.margin ? '+' : '−'}${(Math.abs(cur.margin - prv.margin)*100).toFixed(1)} pp</span>` : ''],
    ['EBITDA',     fmtSAR(cur.ebitda),  prv ? deltaHTML(cur.ebitda, prv.ebitda, true) : ''],
    ['Cash at period end', fmtSAR(pos.cash), `<span class="fl">posted only</span>`],
  ];
  const html = cells.map(([k,v,d]) =>
    `<div class="ps-c"><div class="ps-k">${k}</div><div class="ps-v">${v}</div><div class="ps-d">${d}</div></div>`).join('');
  SECTIONS.forEach(s => { const n = document.getElementById('ps-' + s.id); if(n) n.innerHTML = html; });
}
TI.on(renderStrips);
