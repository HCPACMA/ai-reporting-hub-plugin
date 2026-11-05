# Idempotent: installs the Normalization switch (load-time shim + global-bar checkbox + banner + state restore) into the Desk.
import re, sys, os
P = os.environ.get('DESK', '/home/claude/work/AlFaihaa_Modeling_Desk.html')
s = open(P, encoding='utf8').read()
SHIM = r'''/* NORM:shim:begin */
const NORM = (function(){
  const KEY = 'faihaa_norm', N = DATA.norm;
  const rd = () => { try{ const v = localStorage.getItem(KEY); if(v !== null) return v === '1'; }catch(e){} try{ return /(^|;)norm=1/.test(window.name || ''); }catch(e){} return false; };
  const wr = on => { try{ localStorage.setItem(KEY, on ? '1' : '0'); }catch(e){} try{ window.name = (window.name || '').replace(/(^|;)norm=[01]/g, '') + ';norm=' + (on ? 1 : 0); }catch(e){} };
  const on = !!(N && N.vouchers && N.vouchers.length) && rd();
  const sub = (ser, d, months) => { if(!ser) return; for(const mo in d){ const i = months.indexOf(mo); if(i >= 0) ser[i] = ser[i] - d[mo]; } };
  if(on){
    for(const k in N.m) sub(DATA.m.series[k], N.m[k], DATA.m.months);
    for(const k in N.ifrs.fser) sub(DATA.ifrs.fser[k], N.ifrs.fser[k], DATA.ifrs.months);
    for(const k in N.ifrs.ser) sub(DATA.ifrs.ser[k], N.ifrs.ser[k], DATA.ifrs.months);
    for(const k in N.drv) sub(DATA.drv.ser[k], N.drv[k], DATA.drv.m);
    for(const cc in N.bd.ln) for(const k in N.bd.ln[cc]) sub(DATA.bd.ln[cc] && DATA.bd.ln[cc][k], N.bd.ln[cc][k], DATA.bd.months);
    for(const cc in N.bd.nat) for(const k in N.bd.nat[cc]) sub(DATA.bd.nat[cc] && DATA.bd.nat[cc][k], N.bd.nat[cc][k], DATA.bd.months);
    const E = DATA.ext, I = E.is_, Y = E.years, R = E.ratios_full, D = E.dupont;
    for(const y in N.ext){ const yi = Y.indexOf(+y); if(yi < 0) continue;
      for(const k in N.ext[y]) if(I[k]) I[k][yi] += N.ext[y][k];
      const rev = I.total_revenue[yi], ni = I.net_income[yi], eq = E.bs.equity[yi], ta = E.bs.total_assets[yi];
      if(rev){ if(R.net_margin) R.net_margin[yi] = ni / rev; if(R.ebitda_margin) R.ebitda_margin[yi] = I.ebitda[yi] / rev; }
      if(eq && R.roe) R.roe[yi] = ni / eq; if(ta && R.roa) R.roa[yi] = ni / ta;
      const di = D && D.years ? D.years.indexOf(+y) : -1;
      if(di >= 0){ if(D.net_margin && rev) D.net_margin[di] = ni / rev; if(D.roe && eq) D.roe[di] = ni / eq; }
    }
  }
  const stateKey = 'faihaa_state';
  const api = { available: !!(N && N.vouchers && N.vouchers.length), on, data: N,
    set(v){ wr(v); try{ const sec = document.querySelector('.section.active'); const st = { sec: sec ? sec.id.slice(4) : null, grain: TI.grain, a: TI.a, b: TI.b, cc: TI.cc, cmp: TI.cmp };
      const j = JSON.stringify(st); try{ sessionStorage.setItem(stateKey, j); }catch(e){} try{ window.name = (window.name || '').replace(/(^|;)state=[^;]*/g, '') + ';state=' + encodeURIComponent(j); }catch(e){} }catch(e){}
      location.reload(); },
    saved(){ let j = null; try{ j = sessionStorage.getItem(stateKey); sessionStorage.removeItem(stateKey); }catch(e){}
      if(!j){ const m = /(^|;)state=([^;]*)/.exec(window.name || ''); if(m){ try{ j = decodeURIComponent(m[2]); }catch(e){} } }
      try{ window.name = (window.name || '').replace(/(^|;)state=[^;]*/g, ''); }catch(e){}
      try{ return j ? JSON.parse(j) : null; }catch(e){ return null; } } };
  return api;
})();
/* NORM:shim:end */
'''
# 1 shim after the last DATA line
s = re.sub(r'/\* NORM:shim:begin \*/.*?/\* NORM:shim:end \*/\n', '', s, flags=re.S)
i = s.index('\nDATA.bd = '); j = s.index('\n', i + 1)
k = s.find('\nDATA.norm = ')
if k >= 0 and k > i: j = s.index('\n', k + 1)
s = s[:j + 1] + SHIM + s[j + 1:]
# 2 css
CSS = '''/* NORM:css:begin */
.ti-chk.ti-norm{padding:5px 10px 7px; border:1px solid var(--border); border-radius:8px; background:var(--surface-2); color:var(--ink); font-weight:600}
.ti-chk.ti-norm.on{background:var(--accent-soft); color:var(--accent); border-color:var(--accent)}
.norm-bar{margin:0 0 10px; padding:9px 14px; border:1px solid var(--accent); background:var(--accent-soft); color:var(--ink); border-radius:10px; font-size:12.5px; line-height:1.55}
.norm-bar b{color:var(--accent)} .norm-bar summary{cursor:pointer; font-weight:600; color:var(--accent)}
.norm-bar table{border-collapse:collapse; margin-top:8px; font-size:12px; width:100%} .norm-bar th,.norm-bar td{padding:3px 10px; text-align:start; border-bottom:1px solid var(--border)}
.norm-bar td.num,.norm-bar th.num{text-align:end; font-variant-numeric:tabular-nums} .norm-bar .fl{color:var(--critical)}
/* NORM:css:end */
'''
s = re.sub(r'/\* NORM:css:begin \*/.*?/\* NORM:css:end \*/\n', '', s, flags=re.S)
a = '.ti-chk{display:flex; align-items:center; gap:7px; font-size:12px; color:var(--ink-muted); padding-bottom:7px;}'
assert a in s; s = s.replace(a, a + '\n' + CSS, 1)
# 3 checkbox in the global bar
chk = '''  <label class="ti-chk ti-norm" id="ti-normwrap" style="display:none" title="Exclude the non-recurring vouchers listed in Normalization.xlsx · استبعاد القيود غير المتكررة"><input type="checkbox" id="ti-norm"> Normalization · استبعاد القيود غير المتكررة</label>
'''
s = re.sub(r'  <label class="ti-chk ti-norm".*?</label>\n', '', s, flags=re.S)
a = '  <div class="ti-read" id="ti-read"></div>`;'
assert a in s; s = s.replace(a, chk + a, 1)
# 4 handler + banner + restore, right after the bar is mounted
HAND = r'''/* NORM:ui:begin */
(function(){
  const cb = tiBar.querySelector('#ti-norm'), wrap = tiBar.querySelector('#ti-normwrap'); if(!NORM.available) return;
  wrap.style.display = ''; cb.checked = NORM.on; wrap.classList.toggle('on', NORM.on);
  cb.addEventListener('change', () => NORM.set(cb.checked));
  if(NORM.on){
    const N = NORM.data, f = n => 'SAR ' + (Math.abs(n) / 1e6).toFixed(2) + 'M';
    const yrs = Object.keys(N.ext).sort().map(y => y + ' ' + (N.ext[y].net_income >= 0 ? '+' : '−') + (Math.abs(N.ext[y].net_income) / 1e6).toFixed(2) + 'M').join(' · ');
    const bar = document.createElement('div'); bar.className = 'norm-bar'; bar.id = 'norm-bar';
    const rows = N.vouchers.map(v => `<tr><td>${v.v}</td><td>${v.note || v.tag}</td><td>${v.db || '—'}</td><td class="num">${Math.round(v.amt).toLocaleString()}</td><td class="fl">${(v.fl || []).join('; ')}</td></tr>`).join('');
    bar.innerHTML = `<b>Normalization ON · الاستبعاد مفعّل</b> — ${N.vouchers.length} non-recurring vouchers excluded (${f(N.total)} of expense) · ${N.vouchers.length} قيود غير متكررة مستبعدة بإجمالي ${f(N.total)}. Effect on net income: ${yrs}.<br>
      <span>Applied to: statements, IFRS 18 income statement, deep-analysis drivers, monthly time intelligence, Branches &amp; Departments · مطبق على: القوائم، قائمة الدخل IFRS 18، تحليل المحركات، التحليل الشهري، الفروع والأقسام. Not applied to (cash-based or pre-computed): cash-flow statements, zakat, forecasts, valuation · غير مطبق على: التدفقات النقدية، الزكاة، التنبؤات، التقييم.</span>
      <details><summary>Vouchers · القيود</summary><table><tr><th>Voucher</th><th>Note</th><th>Ledger date</th><th class="num">SAR</th><th></th></tr>${rows}</table></details>`;
    tiBar.after(bar);
  }
  window.addEventListener('load', () => setTimeout(() => {
    const st = NORM.saved(); if(!st) return;
    try{
      const gb = tiBar.querySelector(`#ti-grain button[data-g="${st.grain}"]`); if(gb) gb.click();
      if(st.grain === 'R'){ const fr = tiBar.querySelector('#ti-from'), to = tiBar.querySelector('#ti-to'); fr.value = st.a; fr.dispatchEvent(new Event('change')); to.value = st.b; to.dispatchEvent(new Event('change')); }
      else { const pr = tiBar.querySelector('#ti-period'); pr.value = st.a + ':' + st.b; if(pr.value === st.a + ':' + st.b) pr.dispatchEvent(new Event('change')); }
      const cc = tiBar.querySelector('#ti-cc'); cc.value = st.cc; cc.dispatchEvent(new Event('change'));
      const cm = tiBar.querySelector('#ti-cmp'); if(cm.checked !== st.cmp){ cm.checked = st.cmp; cm.dispatchEvent(new Event('change')); }
      if(st.sec){ const t = st.sec.startsWith('cfo-') ? document.querySelector(`.cfo-tab[data-target="${st.sec}"]`) : document.querySelector(`.nav-item[data-target="${st.sec}"]`); if(t) t.click(); }
    }catch(e){ console.error(e); }
  }, 80));
})();
/* NORM:ui:end */
'''
s = re.sub(r'/\* NORM:ui:begin \*/.*?/\* NORM:ui:end \*/\n', '', s, flags=re.S)
a = '  main.insertBefore(tiBar, main.firstChild);\n})();\n'
assert a in s; s = s.replace(a, a + HAND, 1)
open(P, 'w', encoding='utf8').write(s); print('norm ui installed', len(s))
