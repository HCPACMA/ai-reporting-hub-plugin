
/* ---------------------------------------------------------------- 4b --- */
/* VAT return ↔ trial balance reconciliation (all branches, month / year)   */
(function(){
  const sec = document.getElementById('sec-aud-vat'); if(!sec || !DATA.vatr) return;
  const V = DATA.vatr, BR = ['01','02','03','04'];
  const LINES = [
    [1,'المبيعات الداخلية الخاضعة للنسبة الأساسية 15%','Standard-rated sales 15%'],
    [2,'المبيعات للمواطنين (الخدمات الصحية الخاصة)','Sales to citizens (private health)'],
    [3,'المبيعات الداخلية الخاضعة لنسبة الصفر','Zero-rated domestic sales'],
    [4,'الصادرات الخاضعة لنسبة الصفر','Exports'],
    [5,'المبيعات المعفاة','Exempt sales'],
    [6,'المشتريات الداخلية الخاضعة للنسبة الأساسية 15%','Standard-rated purchases 15%'],
    [7,'التوريدات المسددة للجمارك','Imports — VAT paid at customs'],
    [8,'الاستيراد وفق آلية الاحتساب العكسي','Reverse-charge imports'],
    [9,'المشتريات الخاضعة لنسبة الصفر','Zero-rated purchases'],
    [10,'المشتريات المعفاة','Exempt purchases']];
  const DED = [
    ['4300001','ايرادات اخرى (اقفال حسابات وفروقات)','Other revenue'],
    ['4300002','خصم مكتسب (خصم سداد موردين)','Discount earned'],
    ['4300003','ايرادات ايجارات (الضريبة تورد وقت التحصيل)','Rental revenue'],
    ['4300004','ايرادات تعقيب (مبالغ مستقطعة من العاملين)','Government-errand fees'],
    ['4300005','ايراد تعويضات عاملين (بدل انذار)','Staff compensation'],
    ['4300006','استقطاعات عاملين','Staff deductions'],
    ['4300008','أرباح رأسمالية','Capital gains'],
    ['4300009','فروق حسابات البنوك','Bank differences']];
  const MAN = [
    ['disc','خصم يدوي على الايراد','Manual discount on revenue'],
    ['adv','ايرادات مقبوضة مقدما','Advance-collected revenue'],
    ['lab','عكس مبيعات بين الفروع (مختبر الرياض ↔ مختبر رفحاء)','Inter-branch lab sales reversal'],
    ['oth','بنود أخرى موثقة','Other documented items']];
  const MONTHS = []; for(const y of [2025,2026]) for(let m=1;m<=12;m++){ const ym = y*100+m; if(ym <= 202609) MONTHS.push(ym); }
  const YEARS = [2025, 2026];

  /* ---------- manual items: per viewer, per branch scope, per month ---------- */
  const LSK = 'aud-vatrec-manual-v1';
  let MANV = {}; try { MANV = JSON.parse(localStorage.getItem(LSK) || '{}') || {}; } catch(e){ MANV = {}; }
  const saveMan = () => { try { localStorage.setItem(LSK, JSON.stringify(MANV)); } catch(e){} };
  const manGet = (scope, ym, k) => +(((MANV[scope]||{})[ym]||{})[k] || 0);

  /* ---------- aggregation over a set of months and branches ---------- */
  function calc(yms, ccs, scope){
    const o = {lines:{}, byBr:{}, tb:{}, rev:0, d43:{}, out:0, inV:0, pay:0, med:0, inv:0, cnTB:0, cnRet:0, man:{}};
    for(const [l] of LINES){ o.lines[l] = [0,0]; }
    for(const cc of ccs){
      const br = o.byBr[cc] = {}; for(const [l] of LINES) br[l] = [0,0];
      for(const ym of yms){
        const R = (V.ret[cc]||{})[ym] || {};
        for(const l in R){ const x = R[l]; br[l][0] += x[0]; br[l][1] += x[1]; o.lines[l][0] += x[0]; o.lines[l][1] += x[1]; if(+l <= 5) o.cnRet += x[2]; }
        const A = (V.adj[cc]||{})[ym] || {};
        o.med += A.MED||0; o.inv += A.INV||0; o.cnTB += (A.CN||0) + (A.VCN||0);
      }
      const T = V.tb[cc] || {};
      for(const a in T){
        let dr = 0, cr = 0; for(const ym of yms){ const x = T[a][ym]; if(x){ dr += x[0]; cr += x[1]; } }
        if(!dr && !cr) continue;
        const t = o.tb[a] = o.tb[a] || {dr:0, cr:0, br:{}}; t.dr += dr; t.cr += cr; t.br[cc] = (t.br[cc]||0) + cr - dr;
        if(a[0] === '4'){ o.rev += cr - dr; if(a.startsWith('43')) o.d43[a] = (o.d43[a]||0) + cr - dr; }
        if(a === '21230071') o.out += cr - dr;
        if(a === '1263000') o.inV += dr - cr;
        if(a === '21230072') o.pay += dr - cr;
      }
    }
    for(const [k] of MAN){ o.man[k] = 0; for(const ym of yms) o.man[k] += manGet(scope, ym, k); }
    o.retSales = [1,2,3,4,5].reduce((s,l)=>s+o.lines[l][0],0);
    o.retOutVat = [1,2,3,4,5].reduce((s,l)=>s+o.lines[l][1],0);
    o.retPurch = [6,7,8,9,10].reduce((s,l)=>s+o.lines[l][0],0);
    o.retInVat = [6,7,8].reduce((s,l)=>s+o.lines[l][1],0);
    o.cnGap = o.cnTB - o.cnRet;
    o.manTot = Object.values(o.man).reduce((s,x)=>s+x,0);
    o.dedTot = Object.values(o.d43).reduce((s,x)=>s+x,0);
    o.salesAdj = o.rev - o.dedTot + o.med + o.inv + o.cnGap + o.manTot;
    o.salesRes = o.salesAdj - o.retSales;
    o.outRes = o.out - o.retOutVat;
    o.inRes = o.inV + o.pay - o.retInVat - o.pay;   // TB input VAT + settlements − return − prior-month payment
    o.payable = o.retOutVat - o.retInVat;
    return o;
  }
  const hasData = ym => BR.some(cc => (V.ret[cc]||{})[ym]);
  // a month whose adjusted TB sales fall >10% short of the return is treated as "revenue not posted yet"
  const unposted = c => c.retSales > 0 && c.salesRes < -0.1*c.retSales;
  function defaultYm(){
    for(let i = MONTHS.length-1; i >= 0; i--){ const ym = MONTHS[i]; if(!hasData(ym)) continue;
      if(!unposted(calc([ym], BR, 'ALL'))) return ym; }
    return MONTHS[MONTHS.length-1];
  }
  const st = {year: 2026, month: 0, cc: 'ALL', tbOpen: false};
  { const d = defaultYm(); st.year = Math.floor(d/100); st.month = d%100; }
  if(TI.cc && TI.cc !== 'ALL' && BR.includes(TI.cc)) st.cc = TI.cc;

  const box = el('div','card vr'); box.style.marginTop = '16px';
  const h0 = sec.querySelector('.grid-4'); sec.insertBefore(box, h0);
  const f2 = v => nfmt(v, 2);
  const resPill = (v, tol) => Math.abs(v) < 0.5 ? '<span class="pill ok">Reconciled</span>' : Math.abs(v) <= (tol||1000) ? '<span class="pill warn">Minor gap</span>' : '<span class="pill bad">Explain</span>';

  function yms(){ return st.month ? [st.year*100+st.month] : MONTHS.filter(m => Math.floor(m/100) === st.year); }
  function lyYms(){ return yms().map(m => m-100).filter(m => MONTHS.includes(m)); }
  function scopeCC(){ return st.cc === 'ALL' ? BR : [st.cc]; }

  function render(){
    const Y = yms(), cur = calc(Y, scopeCC(), st.cc);
    const LYm = TI.cmp ? lyYms() : [], ly = LYm.length ? calc(LYm, scopeCC(), st.cc) : null;
    const plab = st.month ? ymLab(st.year*100+st.month) : `FY ${st.year}` + (st.year === 2026 ? ' (Jan–Sep)' : '');
    const single = !!st.month;
    const lyTh = ly ? `<th class="n">Same period LY</th>` : '';
    const lyTd = f => ly ? `<td class="n">${f2(f(ly))}</td>` : '';

    let h = `<div class="vr-head"><div><h3>VAT return ↔ trial balance reconciliation <span class="tag">${plab}</span></h3>
      <p class="card-sub">تسوية الإقرار الضريبي الموحد مع ميزان المراجعة الموحد · VAT_FORM + GLTRIAL, all four branch databases merged</p></div>
      <div class="aud-bar vr-bar">
        <div class="f"><label for="vr-year">Year</label><select id="vr-year">${YEARS.map(y=>`<option value="${y}"${y===st.year?' selected':''}>${y}</option>`).join('')}</select></div>
        <div class="f"><label for="vr-month">Month</label><select id="vr-month"><option value="0"${!st.month?' selected':''}>Whole year</option>${Array.from({length:12},(_,i)=>i+1).filter(m=>MONTHS.includes(st.year*100+m)).map(m=>`<option value="${m}"${m===st.month?' selected':''}>${EN_MON[m-1]}</option>`).join('')}</select></div>
        <div class="f"><label for="vr-cc">Branch</label><select id="vr-cc"><option value="ALL">All branches (consolidated)</option>${BR.map(cc=>`<option value="${cc}"${cc===st.cc?' selected':''}>${CC_LBL(cc)}</option>`).join('')}</select></div>
      </div></div>`;

    const unpM = single ? [] : Y.filter(ym => hasData(ym) && unposted(calc([ym], scopeCC(), st.cc)));
    if(unpM.length) h += `<div class="vr-warn">Includes ${unpM.length} month${unpM.length>1?'s':''} whose revenue is not fully posted to the ledger yet (${unpM.map(ymLab).join(', ')}) — their gaps will close once the month's revenue journals are posted. Pick a month below to see it on its own.</div>`;
    /* status strip */
    h += `<div class="vr-strip">
      <div><span>Output VAT</span><b class="num">${f2(cur.outRes)}</b>${resPill(cur.outRes, 100)}</div>
      <div><span>Sales</span><b class="num">${f2(cur.salesRes)}</b>${resPill(cur.salesRes, 1000)}</div>
      <div><span>Input VAT</span><b class="num">${f2(cur.inRes)}</b>${resPill(cur.inRes, 100)}</div>
      <div><span>Net VAT payable (return)</span><b class="num">${f2(cur.payable)}</b><em>${nfmt(cur.retOutVat,2)} out − ${nfmt(cur.retInVat,2)} in</em></div></div>`;

    /* 1 — consolidated return */
    const ccs = scopeCC();
    h += `<h4 class="vr-h">1 · Consolidated VAT return <span>الإقرار الضريبي الموحد</span></h4><div class="vr-x"><table class="aud-t vr-t"><thead><tr><th>Box</th><th>البيان</th>${ccs.map(cc=>`<th class="n">${CC_LBL(cc)}</th>`).join('')}<th class="n">Net amount</th><th class="n">VAT</th>${lyTh}</tr></thead><tbody>`;
    for(const [l, ar, en] of LINES){
      if(l === 6) h += `<tr class="tot"><td></td><td class="ar">إجمالي المبيعات · Total sales</td>${ccs.map(cc=>`<td class="n">${f2([1,2,3,4,5].reduce((s,k)=>s+cur.byBr[cc][k][0],0))}</td>`).join('')}<td class="n">${f2(cur.retSales)}</td><td class="n">${f2(cur.retOutVat)}</td>${lyTd(o=>o.retSales)}</tr>`;
      const x = cur.lines[l];
      h += `<tr><td>${l}</td><td class="ar" title="${en}">${ar}</td>${ccs.map(cc=>`<td class="n">${f2(cur.byBr[cc][l][0])}</td>`).join('')}<td class="n">${f2(x[0])}</td><td class="n">${f2(x[1])}</td>${lyTd(o=>o.lines[l][0])}</tr>`;
    }
    h += `<tr class="tot"><td></td><td class="ar">إجمالي المشتريات · Total purchases</td>${ccs.map(cc=>`<td class="n">${f2([6,7,8,9,10].reduce((s,k)=>s+cur.byBr[cc][k][0],0))}</td>`).join('')}<td class="n">${f2(cur.retPurch)}</td><td class="n">${f2(cur.retInVat)}</td>${lyTd(o=>o.retPurch)}</tr>
      <tr class="tot"><td></td><td class="ar">صافي الضريبة المستحقة · Net VAT due</td>${ccs.map(()=>'<td></td>').join('')}<td></td><td class="n">${f2(cur.payable)}</td>${lyTd(o=>o.payable)}</tr></tbody></table></div>`;

    /* 2 — output VAT */
    h += `<div class="vr-2"><div><h4 class="vr-h">2 · Output VAT <span>ضريبة المخرجات</span></h4><table class="aud-t vr-t"><thead><tr><th>Item</th><th>Account</th><th class="n">Amount</th>${lyTh}</tr></thead><tbody>
      <tr><td class="ar">ضريبة المخرجات في ميزان المراجعة (دائن − مدين)</td><td>21230071</td><td class="n">${f2(cur.out)}</td>${lyTd(o=>o.out)}</tr>
      <tr><td class="ar">ضريبة المخرجات في إقرار المكلف</td><td>Return</td><td class="n">${f2(-cur.retOutVat)}</td>${lyTd(o=>-o.retOutVat)}</tr>
      <tr class="tot"><td class="ar">الفرق · Difference</td><td></td><td class="n ${Math.abs(cur.outRes)>=0.5?'neg':''}">${f2(cur.outRes)}</td>${lyTd(o=>o.outRes)}</tr></tbody></table></div>`;

    /* 4 — input VAT (placed beside output VAT) */
    h += `<div><h4 class="vr-h">3 · Input VAT <span>ضريبة المدخلات</span></h4><table class="aud-t vr-t"><thead><tr><th>Item</th><th>Account</th><th class="n">Amount</th>${lyTh}</tr></thead><tbody>
      <tr><td class="ar">ضريبة المدخلات في الميزان (مدين − دائن)</td><td>1263000</td><td class="n">${f2(cur.inV)}</td>${lyTd(o=>o.inV)}</tr>
      <tr><td class="ar">تسويات الضريبة (مدين − دائن)</td><td>21230072</td><td class="n">${f2(cur.pay)}</td>${lyTd(o=>o.pay)}</tr>
      <tr><td class="ar">ضريبة المدخلات في إقرار المكلف</td><td>Return</td><td class="n">${f2(-cur.retInVat)}</td>${lyTd(o=>-o.retInVat)}</tr>
      <tr><td class="ar">يخصم: سداد ضريبة الشهر السابق</td><td>21230072 Dr</td><td class="n">${f2(-cur.pay)}</td>${lyTd(o=>-o.pay)}</tr>
      <tr class="tot"><td class="ar">الفرق · Difference</td><td></td><td class="n ${Math.abs(cur.inRes)>=0.5?'neg':''}">${f2(cur.inRes)}</td>${lyTd(o=>o.inRes)}</tr></tbody></table></div></div>`;

    /* 3 — sales reconciliation */
    h += `<h4 class="vr-h">4 · Sales reconciliation <span>تسوية المبيعات بين الميزان والإقرار</span></h4><table class="aud-t vr-t vr-sales"><thead><tr><th>Item</th><th>Account / source</th><th class="n">Amount</th>${lyTh}</tr></thead><tbody>
      <tr><td class="ar">إجمالي المبيعات في ميزان المراجعة (41x · 42x · 43x، دائن − مدين)</td><td>TB</td><td class="n">${f2(cur.rev)}</td>${lyTd(o=>o.rev)}</tr>
      <tr><td class="ar">إجمالي المبيعات في إقرار المكلف</td><td>Return</td><td class="n">${f2(-cur.retSales)}</td>${lyTd(o=>-o.retSales)}</tr>
      <tr class="tot"><td class="ar">الفرق قبل التسوية</td><td></td><td class="n">${f2(cur.rev - cur.retSales)}</td>${lyTd(o=>o.rev-o.retSales)}</tr>
      <tr class="vr-sub"><td colspan="${ly?4:3}">يخصم · Deduct — revenue outside the VAT return</td></tr>`;
    for(const [a, ar, en] of DED) h += `<tr><td class="ar" title="${en}">${ar}</td><td>${a}</td><td class="n">${f2(-(cur.d43[a]||0))}</td>${lyTd(o=>-(o.d43[a]||0))}</tr>`;
    h += `<tr class="vr-sub"><td colspan="${ly?4:3}">يضاف · Add — items in the return but not (or reversed) in revenue</td></tr>
      <tr><td class="ar">تكلفة مشتريات الأدوية المعكوسة على الإيراد بقيد يدوي (صيدليات مؤجرة)</td><td>JV «ادوية عن شهر»</td><td class="n">${f2(cur.med)}</td>${lyTd(o=>o.med)}</tr>
      <tr><td class="ar">فواتير مبيعات ايجارات بضريبة (تُحوّل للإيرادات المقدمة وتُستهلك شهرياً)</td><td>4300003 · VAT invoice</td><td class="n">${f2(cur.inv)}</td>${lyTd(o=>o.inv)}</tr>
      <tr><td class="ar">إشعارات دائنة للعملاء لم يُسترد عنها الضريبة (Credit Memo)</td><td>CN in TB ${nfmt(cur.cnTB,2)} − in return ${nfmt(cur.cnRet,2)}</td><td class="n">${f2(cur.cnGap)}</td>${lyTd(o=>o.cnGap)}</tr>`;
    for(const [k, ar, en] of MAN){
      const v = cur.man[k];
      h += `<tr><td class="ar" title="${en}">${ar}</td><td>${single ? `<span class="vr-man-tag">Manual</span>` : 'Manual · sum of months'}</td><td class="n">${single ? `<input class="vr-in" id="vr-man-${k}" data-k="${k}" type="text" inputmode="decimal" value="${v ? v : ''}" placeholder="0.00" aria-label="${en}">` : f2(v)}</td>${lyTd(o=>o.man[k])}</tr>`;
    }
    h += `<tr class="tot"><td class="ar">المبيعات بعد التسوية</td><td></td><td class="n">${f2(cur.salesAdj)}</td>${lyTd(o=>o.salesAdj)}</tr>
      <tr class="tot vr-res"><td class="ar">المتبقي بعد التسوية — يجب أن يكون صفراً</td><td>${resPill(cur.salesRes, 1000)}</td><td class="n ${Math.abs(cur.salesRes)>=0.5?'neg':''}">${f2(cur.salesRes)}</td>${lyTd(o=>o.salesRes)}</tr></tbody></table>`;

    /* 5 — monthly track for the year */
    const yr = MONTHS.filter(m => Math.floor(m/100) === st.year);
    h += `<h4 class="vr-h">5 · Month by month, ${st.year} <span>متابعة التسوية شهرياً</span></h4><div class="vr-x"><table class="aud-t vr-t vr-months"><thead><tr><th>Month</th><th class="n">Return sales</th><th class="n">TB revenue</th><th class="n">Sales residual</th><th class="n">Output VAT gap</th><th class="n">Input VAT gap</th><th class="n">VAT payable</th><th>Status</th></tr></thead><tbody>`;
    let tS=0,tR=0,tRes=0,tO=0,tI=0,tP=0;
    for(const ym of yr){
      if(!hasData(ym)) continue;
      const c = calc([ym], scopeCC(), st.cc);
      tS+=c.retSales; tR+=c.rev; tRes+=c.salesRes; tO+=c.outRes; tI+=c.inRes; tP+=c.payable;
      const unp = unposted(c);
      const worst = Math.max(Math.abs(c.salesRes)/1000, Math.abs(c.outRes)/100, Math.abs(c.inRes)/100);
      const pill = unp ? '<span class="pill warn">Revenue not posted yet</span>' : worst < 0.005 ? '<span class="pill ok">Reconciled</span>' : worst <= 1 ? '<span class="pill warn">Minor gap</span>' : '<span class="pill bad">Explain</span>';
      h += `<tr class="aud-row-click vr-mrow${ym%100===st.month?' on':''}" data-m="${ym%100}"><td>${ymLab(ym)}</td><td class="n">${f2(c.retSales)}</td><td class="n">${f2(c.rev)}</td><td class="n ${Math.abs(c.salesRes)>1000?'neg':''}">${f2(c.salesRes)}</td><td class="n">${f2(c.outRes)}</td><td class="n">${f2(c.inRes)}</td><td class="n">${f2(c.payable)}</td><td>${pill}</td></tr>`;
    }
    h += `<tr class="tot"><td>Year</td><td class="n">${f2(tS)}</td><td class="n">${f2(tR)}</td><td class="n">${f2(tRes)}</td><td class="n">${f2(tO)}</td><td class="n">${f2(tI)}</td><td class="n">${f2(tP)}</td><td></td></tr></tbody></table></div>`;

    /* 6 — consolidated TB (collapsible) */
    const accts = Object.keys(cur.tb).sort();
    h += `<details class="vr-tb"${st.tbOpen?' open':''}><summary><h4 class="vr-h" style="display:inline">6 · Consolidated trial balance — VAT and revenue accounts <span>ميزان المراجعة الموحد · ${accts.length} accounts</span></h4></summary><div class="vr-x" style="margin-top:10px"><table class="aud-t vr-t"><thead><tr><th>Account</th><th>اسم الحساب</th>${ccs.map(cc=>`<th class="n">${CC_LBL(cc)}</th>`).join('')}<th class="n">Debit</th><th class="n">Credit</th><th class="n">Net (Cr − Dr)</th></tr></thead><tbody>`;
    let sd=0, sc=0;
    for(const a of accts){ const t = cur.tb[a]; if(a[0]==='4'){ sd+=t.dr; sc+=t.cr; }
      h += `<tr><td>${a}</td><td class="ar">${esc(V.names[a]||'')}</td>${ccs.map(cc=>`<td class="n">${t.br[cc]!==undefined?f2(t.br[cc]):'—'}</td>`).join('')}<td class="n">${f2(t.dr)}</td><td class="n">${f2(t.cr)}</td><td class="n">${f2(t.cr-t.dr)}</td></tr>`; }
    h += `<tr class="tot"><td></td><td class="ar">إجمالي الإيرادات · Total revenue</td>${ccs.map(()=>'<td></td>').join('')}<td class="n">${f2(sd)}</td><td class="n">${f2(sc)}</td><td class="n">${f2(sc-sd)}</td></tr></tbody></table></div></details>`;

    h += `<p class="aud-note" style="margin:14px 0 0">
      <b>How it's built.</b> Return = <code>GL_VAT_AMT_BY_PERIOD_ITEMS_MV</code> per branch (the VAT_FORM source), by invoice date: sales net = invoices − returns − credit notes (ex-VAT); box 6 includes purchase returns at VAT ÷ 15%. TB = <code>GL_TRANSACTIONS_DETAILS</code> movements, posted and open vouchers (cancelled excluded), with the monthly VAT closing entry (<i>اقفال ضريبة القيمة المضافة</i>) and the year-end closing entry removed so the accounts show their real activity.
      Auto items: rent in 4300003 is deducted in full and the rent invoices that carried VAT are added back; medicine cost reversed against revenue comes from the monthly «ادوية عن شهر» journal; the credit-memo line is credit notes booked to revenue minus the credit notes already in the return. Manual lines are saved in this browser only, per month and branch scope.
      Checked against <i>VAT_Riyadh ALL July 2026.xlsx</i>: output VAT 422,547.77 vs 422,564.45 (−16.68), input VAT 89,879.00 ties, sales after adjustments 6,207,595.38 — identical to the workbook. The workbook's TB snapshot was taken before voucher JV1-26/02413 (Bur-2 pharmacy rent moved to deferred, 450,000), so live July revenue is 450,000 lower; the rent add-back logic absorbs it.</p>`;
    box.innerHTML = h;

    box.querySelector('#vr-year').onchange = e => { st.year = +e.target.value; if(st.month && !MONTHS.includes(st.year*100+st.month)) st.month = 0; render(); };
    box.querySelector('#vr-month').onchange = e => { st.month = +e.target.value; render(); };
    box.querySelector('#vr-cc').onchange = e => { st.cc = e.target.value; render(); };
    box.querySelector('.vr-tb').ontoggle = e => { st.tbOpen = e.target.open; };
    box.querySelectorAll('.vr-mrow').forEach(tr => tr.onclick = () => { st.month = +tr.dataset.m; render(); box.scrollIntoView({behavior:'smooth', block:'start'}); });
    box.querySelectorAll('.vr-in').forEach(inp => inp.onchange = () => {
      const ym = st.year*100 + st.month, v = parseFloat(String(inp.value).replace(/[, ]/g,'')) || 0;
      ((MANV[st.cc] = MANV[st.cc] || {})[ym] = MANV[st.cc][ym] || {})[inp.dataset.k] = v; saveMan(); render();
      const again = box.querySelector('#vr-man-' + inp.dataset.k); if(again) again.focus();
    });
  }
  let lastCC = TI.cc;
  TI.on(() => { if(TI.cc !== lastCC){ lastCC = TI.cc; if(TI.cc === 'ALL' || BR.includes(TI.cc)) st.cc = TI.cc; } render(); });
  render();
})();
