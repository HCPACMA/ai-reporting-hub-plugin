/* ======================================================================
   IFRS 18 · Statement of profit or loss
   Rebuilt against EY, Good Group (International) Limited — Illustrative
   consolidated financial statements under IFRS 18 (v2, May 2025):
   the five categories, the two mandated subtotals, expenses analysed by
   nature, the IFRS 18.83 specified-expenses note and a full MPM note.
   Every figure comes from the account-level GL detail, not the desk's
   aggregate buckets, because four of the reclassifications the standard
   forces sit *inside* those buckets.
   ====================================================================== */
(function(){
  const sec = document.getElementById('sec-stmt-ifrs18'); if(!sec) return;
  const F = DATA.ifrs; if(!F) return;

  audHead(sec, 'Statements', 'Statement of profit or loss — IFRS 18', 'قائمة الأرباح أو الخسائر — معيار IFRS 18 للعرض والإفصاح',
    'IFRS 18 replaces IAS 1 for periods beginning on or after <b>1 January 2027</b> (early adoption permitted, comparatives restated). It does not change profit — it changes where each line sits. Every income and expense is classified into one of <b>five categories</b> — operating, investing, financing, income taxes, discontinued operations — and two subtotals become mandatory: <b>operating profit</b> and <b>profit before financing and income taxes</b>. This tab has been rebuilt line by line against EY’s <i>Good Group (International) Limited — IFRS 18</i> illustrative statements (v2, May 2025); the audit card at the foot lists what that review changed.');

  /* ------------------------------------------------------------ state */
  const st = {view:'nat', rent:'inv', disp:'op', eosb:'fin', ded:'exp'};
  const CCS = () => (TI.cc === 'ALL' ? TIM.ccs : [TI.cc]);
  const NATM = {}; F.nat.forEach(g => NATM[g[0]] = g);

  const accFlow = (acc, a, b, cc) => {
    let t = 0;
    for(const k of (cc === 'ALL' ? TIM.ccs : [cc])){
      const s = F.ser[acc + '|' + k]; if(!s) continue;
      for(let i = a; i <= b; i++) t += (s[i] || 0);
    }
    return t;
  };
  const grpFlow = (g, a, b, cc) => NATM[g][3].reduce((t,x) => t + accFlow(x,a,b,cc), 0);
  /* expenses by function: the cost centre's function (clinics = cost of revenue; administration,
     insurance-claims departments and head office = general and administrative, as in the audited statements) */
  const FNL = ['COR','GA'];
  const FNM = F.fnMap || {COR:'COR', GA:'GA', INS:'GA', HO:'GA', X:'GA'};
  const fnFlow = (acc, a, b, cc, line) => {
    let t = 0;
    for(const k of (cc === 'ALL' ? TIM.ccs : [cc])){
      for(const f of ['COR','GA','INS','HO','X']){
        if(FNM[f] !== line) continue;
        const s = (F.fser||{})[acc + '|' + k + '|' + f]; if(!s) continue;
        for(let i = a; i <= b; i++) t += (s[i] || 0);
      }
    }
    return t;
  };
  const grpFn = (g, a, b, cc, line) => NATM[g][3].reduce((t,x) => t + fnFlow(x,a,b,cc,line), 0);
  const inc = v => -v;                    // GL sign: DR +, CR −. Income shown +.
  const nm = a => F.acc[a] || [a, a];

  /* the order the operating expenses are presented in, by nature */
  const NAT_ORDER = ['emp','cons','extmed','insadm','ded','dep','rent','util',
                     'maint','govt','prof','fac','trav','admin','wdown','disp','bankc'];
  const OTH_OP_ACC = ['4300001','4300002','4300004','4300005','4300006'];

  /* ------------------------------------------------------------ build */
  function build(a, b, cc){
    if(a == null || a < 0 || b < a) return null;

    // revenue — the bucket series, which ties to invoice revenue
    const cash   = inc(flow(['B08'], a, b, cc));
    const cred   = inc(flow(['B10'], a, b, cc));
    const contra = flow(['B11'], a, b, cc);
    const ded    = grpFlow('ded', a, b, cc);          // insurance claim deductions
    const revGross = cash + cred - contra;
    const rev = revGross - (st.ded === 'rev' ? ded : 0);

    // income lines the standard forces out of "other revenue"
    const rent = inc(accFlow('4300003', a, b, cc));   // rental income
    const gain = inc(accFlow('4300008', a, b, cc));   // gains on disposal
    const loss = grpFlow('disp', a, b, cc);           // losses on disposal
    const cashFx = inc(accFlow('4300009', a, b, cc)); // differences on bank accounts
    let othOp = OTH_OP_ACC.reduce((t,x) => t + inc(accFlow(x,a,b,cc)), 0);
    if(st.rent === 'op') othOp += rent;
    if(st.disp === 'op') othOp += gain;

    // operating expenses, by nature
    const nat = [];
    NAT_ORDER.forEach(g => {
      if(g === 'ded'  && st.ded  === 'rev') return;   // presented as contra-revenue
      if(g === 'disp' && st.disp === 'inv') return;   // presented in investing
      nat.push([g, NATM[g][1], NATM[g][2], grpFlow(g,a,b,cc)]);
    });
    const opexTot = nat.reduce((t,x) => t + x[3], 0);
    const opProfit = rev + othOp - opexTot;

    // investing (IFRS 18.53) — assets that return income independently
    const invRows = [];
    if(st.rent === 'inv') invRows.push(['إيرادات إيجارات','Rental income', rent, 'IFRS 18.53(c)']);
    if(st.disp === 'inv'){
      invRows.push(['أرباح استبعاد أصول','Gains on disposal of assets', gain, 'IFRS 18.53']);
      invRows.push(['خسائر استبعاد أصول','Losses on disposal of assets', -loss, 'IFRS 18.53']);
    }
    invRows.push(['فروق حسابات البنوك والودائع','Differences on cash and short-term deposits', cashFx, 'IFRS 18.53(b)']);
    const investing = invRows.reduce((t,x) => t + x[2], 0);
    const pbft = opProfit + investing;

    // financing (IFRS 18.59–61)
    const loanInt = accFlow('3290001', a, b, cc);
    const eosbInt = accFlow('3390000', a, b, cc);
    const finRows = [['فوائد قروض','Interest expenses on loans and borrowings', -loanInt, 'IFRS 18.60(a)']];
    if(st.eosb === 'fin') finRows.push(['تكلفة العمولة على التزامات منافع الموظفين','Interest expenses on other liabilities', -eosbInt, 'IFRS 18.61(a)']);
    const financing = finRows.reduce((t,x) => t + x[2], 0);
    const pbt = pbft + financing;

    // income taxes category — Zakat, read from the ledger for any period
    const zak = accFlow('3280005', a, b, cc);
    const profit = pbt - zak;

    // IFRS 18.83 specified expenses by nature
    const empAcc = NATM['emp'][3].map(x => [x, accFlow(x,a,b,cc)]).filter(x => Math.abs(x[1]) > 0.5);
    const spec = {
      dep:   grpFlow('dep', a, b, cc),
      amort: 0,
      emp:   grpFlow('emp', a, b, cc),
      imp:   0,
      wdown: grpFlow('wdown', a, b, cc),
      empAcc
    };

    // by function: every operating expense group except the two presented as their own lines
    const SEP = ['ded','disp'];                      // claim deductions and disposal losses stay separate lines
    const natFn = NAT_ORDER.filter(g => !SEP.includes(g)).map(g => {
      const o = {g, ar:NATM[g][1], en:NATM[g][2]}; FNL.forEach(l => o[l] = grpFn(g,a,b,cc,l)); o.tot = FNL.reduce((t,l)=>t+o[l],0); return o; });
    const fnTot = {}; FNL.forEach(l => fnTot[l] = natFn.reduce((t,o) => t + o[l], 0));
    const specFn = {}; ['dep','emp','wdown'].forEach(g => { specFn[g] = {}; FNL.forEach(l => specFn[g][l] = grpFn(g,a,b,cc,l)); });
    const sepExp = (st.ded === 'exp' ? ded : 0) + (st.disp === 'op' ? loss : 0);

    // reconciliation back to the desk's own net result for the same window
    const p = pnl(a, b, cc);
    return {cash, cred, contra, revGross, rev, ded, rent, gain, loss, cashFx, othOp,
            nat, opexTot, opProfit, invRows, investing, pbft, finRows, financing,
            loanInt, eosbInt, pbt, zak, profit, spec, natFn, fnTot, specFn, sepExp,
            deskNet: p ? p.net : null, deskEbitda: p ? p.ebitda : null};
  }

  /* --------------------------------------------------------------- UI */
  const bar   = el('div','aud-bar');                       sec.appendChild(bar);
  const kp    = el('div','grid grid-4');                   sec.appendChild(kp);
  const cMain = el('div','card'); cMain.style.marginTop='16px'; sec.appendChild(cMain);
  const row   = el('div','grid grid-2'); row.style.marginTop='16px'; row.style.alignItems='start'; sec.appendChild(row);
  const cNat  = el('div','card'); cNat.style.marginTop='16px'; sec.insertBefore(cNat, row);
  const cSpec = el('div','card'), cMpm = el('div','card');
  row.appendChild(cSpec); row.appendChild(cMpm);
  const cAud  = el('div','card'); cAud.style.marginTop='16px';  sec.appendChild(cAud);
  const cRec  = el('div','card'); cRec.style.marginTop='16px';  sec.appendChild(cRec);
  sec.appendChild(el('div','note', `<b>Source.</b> Account-level GL detail pulled through the Cure MCP for every profit-or-loss account across the four ledgers (posted + open vouchers, year-end and VAT closing entries excluded, cost-centre prefix = branch), plus the desk’s revenue buckets <code>B08</code>/<code>B10</code>/<code>B11</code>, which tie to the invoice tables. The aggregate expense buckets are no longer used here: four of the reclassifications IFRS 18 forces — Zakat, interest on employee-benefit obligations, losses on disposal and the insurance claim deductions — all sit <i>inside</i> a single bucket called “Provisions” or “Other operating expenses”, so the statement cannot be built from them. Benchmark: EY, <i>Good Group (International) Limited — Illustrative consolidated financial statements under IFRS 18</i>, v2, May 2025.`));

  const SW = [
    ['view','عرض المصروفات التشغيلية · Operating expenses',[['nat','بطبيعتها — IFRS 18.78'],['fn','بوظيفتها — IFRS 18.78 (+ إيضاح 18.83)']]],
    ['rent','إيرادات الإيجارات · Rental income',[['inv','استثماري — افتراضي (IFRS 18.53(c))'],['op','تشغيلي']]],
    ['disp','استبعاد الأصول · Asset disposals',[['op','تشغيلي — افتراضي (IFRS 18.B60)'],['inv','استثماري']]],
    ['eosb','عمولة التزامات نهاية الخدمة · EOSB interest',[['fin','تمويلي — افتراضي (IFRS 18.61(a))'],['op','تشغيلي']]],
    ['ded','حسميات مطالبات التأمين · Claim deductions',[['exp','مصروف تشغيلي — كما في القوائم'],['rev','خصم من الإيراد (IFRS 15.50)']]]
  ];

  /* ---- presentation by function: the IFRS 18.83 note and the full analysis by nature ---- */
  function renderFnNotes(C, L){
    const FL = {COR:['تكلفة الإيرادات','Cost of revenue'], GA:['مصروفات عمومية وإدارية','General and administrative expenses']};
    const n0 = v => (Math.abs(v) < 0.5 ? '—' : nfmt(v));
    const S = C.spec, SF = C.specFn, LF = L ? L.specFn : null;
    const th = L ? '<th class="n">الفترة المقارنة<span class="i18-en">Restated</span></th>' : '';
    const line = (ar, en, v, lv, cls) => `<tr class="${cls||''}"><td>${ar}<span class="i18-en">${en}</span></td><td class="n">${n0(v)}</td>${L?`<td class="n">${lv===null||lv===undefined?'—':n0(lv)}</td>`:''}</tr>`;
    const block = (ar, en, key, ref, nilNote) => {
      let h = `<tr class="i18-cat"><td colspan="${L?3:2}">${ar}<span class="i18-en">${en}${ref?` · <i class="i18-ref">${ref}</i>`:''}</span></td></tr>`;
      if(!key){ return h + line(`${nilNote}`, 'Nil', 0, L?0:null) + line('الإجمالي', 'Total', 0, L?0:null, 'i18-sub'); }
      let tot = 0, ltot = 0;
      FNL.forEach(l => { const v = SF[key][l], lv = LF ? LF[key][l] : null; tot += v; ltot += (lv||0);
        if(Math.abs(v) >= 0.5 || (lv !== null && Math.abs(lv) >= 0.5)) h += line('— ' + FL[l][0], FL[l][1], v, lv); });
      return h + line('الإجمالي', 'Total ' + en.toLowerCase(), tot, L ? ltot : null, 'i18-sub');
    };
    cSpec.innerHTML = `<h3>المصروفات المحددة بطبيعتها ضمن الفئة التشغيلية</h3>
      <p class="card-sub">IFRS 18.83 — إلزامي عند عرض أي بند مصروفات بوظيفته: إيضاح واحد يبيّن الإهلاك والإطفاء ومنافع الموظفين وخسائر الانخفاض وعكسها وتخفيض المخزون، الإجمالي لكل منها والمبلغ الوارد في كل بند من بنود الفئة التشغيلية (نمط إيضاح 13.5 في دليل EY)</p>
      <div class="aud-x"><table class="aud-t i18-t"><thead><tr><th>البند</th><th class="n">الفترة</th>${th}</tr></thead><tbody>
      ${block('الإهلاك','Depreciation','dep','IFRS 18.83(a)(i)')}
      ${block('الإطفاء','Amortisation',null,'IFRS 18.83(a)(ii)','لا توجد أصول غير ملموسة قابلة للإطفاء في الدفتر')}
      ${block('منافع الموظفين','Employee benefits','emp','IFRS 18.83(a)(iii)')}
      ${block('خسائر الانخفاض في القيمة وعكسها','Impairment losses and reversals',null,'IFRS 18.83(a)(iv)','لا يوجد حساب انخفاض قيمة أو مخصص خسائر ائتمانية في الدفتر')}
      ${block('تخفيض قيمة المخزون','Write-down of inventories','wdown','IFRS 18.83(a)(v)')}
      </tbody></table></div>
      <div class="note" style="margin-top:12px"><b>بنود خارج الفئة التشغيلية تتضمن جزءاً من هذه المبالغ (IFRS 18.83(b)).</b> تكلفة العمولة على التزامات منافع الموظفين (${nfmt(C.eosbInt)}) معروضة ضمن فئة التمويل، وهي جزء من إجمالي منافع الموظفين خارج الأرقام أعلاه. لا توجد مبالغ إهلاك أو منافع موظفين مرسملة في المخزون في نهاية الفترة (IFRS 18.B84).</div>`;

    // full analysis by nature, per function line item — ties to the face of the statement
    const NF = C.natFn, LN = L ? L.natFn : null;
    const cols = FNL.map(l => `<th class="n">${FL[l][0]}<span class="i18-en">${FL[l][1]}</span></th>`).join('');
    let h = `<h3>تحليل المصروفات التشغيلية بطبيعتها — لكل بند وظيفي</h3>
      <p class="card-sub">القائمة معروضة بالوظيفة، وهذا الجدول يحلّل كل بند وظيفي إلى طبيعة مصروفاته من الحسابات مباشرة، ويطابق مجاميعه مع وجه القائمة (IFRS 18.78، B80–B85؛ نمط إيضاح 13.8 في دليل EY)</p>
      <div class="aud-x"><table class="aud-t i18-t"><thead><tr><th>طبيعة المصروف</th>${cols}<th class="n">الإجمالي</th>${L?'<th class="n">المقارنة</th>':''}</tr></thead><tbody>`;
    NF.forEach((o,i) => {
      const lv = LN ? LN[i].tot : null;
      if(Math.abs(o.tot) < 0.5 && (lv === null || Math.abs(lv) < 0.5)) return;
      h += `<tr><td>${o.ar}<span class="i18-en">${o.en}</span></td>${FNL.map(l => `<td class="n">${n0(o[l])}</td>`).join('')}<td class="n"><b>${n0(o.tot)}</b></td>${L?`<td class="n">${n0(lv)}</td>`:''}</tr>`;
    });
    const tot = FNL.reduce((t,l) => t + C.fnTot[l], 0), ltot = L ? FNL.reduce((t,l) => t + L.fnTot[l], 0) : null;
    h += `<tr class="i18-sub"><td><b>الإجمالي = وجه القائمة</b><span class="i18-en">Total, as presented by function</span></td>${FNL.map(l => `<td class="n"><b>${nfmt(C.fnTot[l])}</b></td>`).join('')}<td class="n"><b>${nfmt(tot)}</b></td>${L?`<td class="n"><b>${nfmt(ltot)}</b></td>`:''}</tr>`;
    if(C.sepExp) h += `<tr class="i18-detail"><td>بنود معروضة بطبيعتها على وجه القائمة (حسميات المطالبات، خسائر الاستبعاد)<span class="i18-en">Presented separately by nature</span></td>${FNL.map(() => '<td class="n"></td>').join('')}<td class="n">${nfmt(C.sepExp)}</td>${L?`<td class="n">${nfmt(L.sepExp)}</td>`:''}</tr>`;
    h += `<tr class="i18-sub"><td><b>إجمالي المصروفات التشغيلية</b><span class="i18-en">Operating expenses — equals the analysis by nature</span></td>${FNL.map(() => '<td class="n"></td>').join('')}<td class="n"><b>${nfmt(tot + C.sepExp)}</b></td>${L?`<td class="n"><b>${nfmt(ltot + L.sepExp)}</b></td>`:''}</tr>`;
    h += `</tbody></table></div>
      <div class="note" style="margin-top:12px"><b>أساس التوزيع على الوظائف.</b> من مركز التكلفة في كل قيد: مراكز العيادات والأقسام الطبية = تكلفة الإيرادات؛ الإدارة وأقسام مطالبات التأمين والمركز الرئيسي = مصروفات عمومية وإدارية — نفس تبويب القوائم المالية المدققة. حسميات مطالبات التأمين وخسائر استبعاد الأصول تبقى بنداً مستقلاً بطبيعته على وجه القائمة (IFRS 18.B79 يسمح بعرض بنود بالطبيعة إلى جانب الوظيفة). عرض أي بند بالوظيفة يوجب إيضاح المصروفات المحددة بطبيعتها (IFRS 18.83) — وهو أدناه.</div>`;
    cNat.innerHTML = h; cNat.style.display = '';
  }

  function render(){
    const w  = {a: TI.a, b: TI.b};
    const cw = TI.cmp ? cmpWindow() : null;
    const C  = build(w.a, w.b, TI.cc);
    const L  = cw ? build(cw.a, cw.b, TI.cc) : null;
    if(!C){ cMain.innerHTML = '<p class="card-sub">No period selected.</p>'; return; }

    bar.innerHTML = SW.map(([k,lab,opts]) =>
      `<div class="f"><label for="i18-${k}">${lab}</label><select id="i18-${k}">` +
      opts.map(([v,t]) => `<option value="${v}"${st[k]===v?' selected':''}>${t}</option>`).join('') +
      `</select></div>`).join('');
    SW.forEach(([k]) => bar.querySelector('#i18-'+k).onchange = e => { st[k] = e.target.value; render(); });

    /* ---- KPI tiles ---- */
    const bd = t => `<bdi>${t}</bdi>`;
    const pc = (c,l) => (l && l !== 0) ? dPct(c,l) : '';
    kp.innerHTML =
        kpiTile('Operating profit · الربح التشغيلي', nfmt(C.opProfit),
                (L?bd(pc(C.opProfit,L.opProfit))+' · ':'') + 'الهامش ' + bd(`${C.rev?((C.opProfit/C.rev)*100).toFixed(1):'—'}%`), C.opProfit<0)
      + kpiTile('Profit before financing &amp; income taxes · الربح قبل التمويل والزكاة', nfmt(C.pbft),
                L?bd(pc(C.pbft,L.pbft)):'مجموع فرعي إلزامي — IFRS 18.69(b)', C.pbft<0)
      + kpiTile('Profit before Zakat · الربح قبل الزكاة', nfmt(C.pbt),
                'تكلفة التمويل ' + bd(nfmt(-C.financing)), C.pbt<0)
      + kpiTile('Profit · ربح الفترة', nfmt(C.profit), 'بعد زكاة ' + bd(nfmt(C.zak)), C.profit<0);

    /* ---- the statement ---- */
    const th  = L ? '<th class="n">الفترة المقارنة<span class="i18-en">Restated</span></th><th class="n">التغير</th>' : '';
    const td  = (cv,lv) => L ? `<td class="n">${nfmt(lv)}</td><td class="n">${(lv!==null&&lv!==0)?(((cv-lv)>=0?'+':'−')+Math.abs((cv-lv)/Math.abs(lv)*100).toFixed(1)+'%'):'—'}</td>` : '';
    const r   = (ar,en,cv,lv,ref,cls) => `<tr class="${cls||''}"><td>${ar}<span class="i18-en">${en}${ref?` · <i class="i18-ref">${ref}</i>`:''}</span></td><td class="n">${nfmt(cv)}</td>${td(cv,lv)}</tr>`;
    const nil = (ar,en,ref) => `<tr class="i18-nil"><td>${ar}<span class="i18-en">${en}${ref?` · <i class="i18-ref">${ref}</i>`:''}</span></td><td class="n">—</td>${L?'<td class="n">—</td><td class="n">—</td>':''}</tr>`;
    const cat = (t,s) => `<tr class="i18-cat"><td colspan="${L?4:2}">${t}${s?`<span class="i18-en">${s}</span>`:''}</td></tr>`;
    const sub = (ar,en,cv,lv,ref) => `<tr class="i18-sub"><td><b>${ar}</b><span class="i18-en">${en}${ref?` · <i class="i18-ref">${ref}</i>`:''}</span></td><td class="n"><b>${nfmt(cv)}</b></td>${td(cv,lv)}</tr>`;

    let h = `<h3>قائمة الأرباح أو الخسائر <span class="tag">${esc(TIM.ccName[TI.cc]?TIM.ccName[TI.cc][0]:'كل الفروع')}</span></h3>
      <p class="card-sub">الفترة ${mLabEN(w.a)} – ${mLabEN(w.b)}${L?` · مقارنة مع ${mLabEN(cw.a)} – ${mLabEN(cw.b)} (مُعاد عرضها)`:''} · بالريال السعودي · ${st.view==='fn'?'المصروفات معروضة بوظيفتها (IFRS 18.78) — تحليلها بطبيعتها في الإيضاح أدناه (IFRS 18.83)':'المصروفات معروضة بطبيعتها (IFRS 18.78)'}</p>
      <div class="aud-x"><table class="aud-t i18-t"><thead><tr><th>البند</th><th class="n">الفترة</th>${th}</tr></thead><tbody>`;

    h += cat('العمليات المستمرة — الفئة التشغيلية','Continuing operations — operating category · IFRS 18.52');
    h += r('إيرادات نقدية','Cash revenue', C.cash, L&&L.cash);
    h += r('إيرادات آجلة / تأمين','Credit and insurance revenue', C.cred, L&&L.cred);
    h += r('مبيعات أدوية التأمين — بند مقابل','Insurance drug sales — contra', -C.contra, L&&-L.contra);
    if(st.ded === 'rev') h += r('حسميات مطالبات التأمين','Insurance claim deductions', -C.ded, L&&-L.ded, 'IFRS 15.50');
    h += sub('إيرادات من عقود مع العملاء','Revenue from contracts with customers', C.rev, L&&L.rev, 'IFRS 15.113(a)');
    if(st.view === 'fn'){
      h += r('تكلفة الإيرادات','Cost of revenue', -C.fnTot.COR, L&&-L.fnTot.COR, 'IFRS 18.78(b), 82');
      h += sub('مجمل الربح','Gross profit', C.rev - C.fnTot.COR, L&&(L.rev - L.fnTot.COR), 'IFRS 18.B78');
      h += r('إيرادات تشغيلية أخرى','Other operating income', C.othOp, L&&L.othOp, 'IFRS 18.B79');
      h += r('مصروفات عمومية وإدارية','General and administrative expenses', -C.fnTot.GA, L&&-L.fnTot.GA, 'IFRS 18.78(b), 82');
      if(st.ded === 'exp') h += r(NATM['ded'][1], NATM['ded'][2], -C.ded, L&&-L.ded, 'IFRS 18.B79 — بطبيعته');
      if(st.disp === 'op') h += r(NATM['disp'][1], NATM['disp'][2], -C.loss, L&&-L.loss, 'IFRS 18.B60 — بطبيعته');
    } else {
    h += r('إيرادات تشغيلية أخرى','Other operating income', C.othOp, L&&L.othOp, 'IFRS 18.B79');
    C.nat.forEach((x,i) => {
      const lv = L && L.nat[i] ? -L.nat[i][3] : null;
      if(Math.abs(x[3]) < 1 && (lv === null || Math.abs(lv) < 1)) return;
      h += r(x[1], x[2], -x[3], lv, 'IFRS 18.78');
    });
    }
    h += nil('خسائر الانخفاض في القيمة (المعيار 9)','Impairment losses determined under IFRS 9','IFRS 18.75');
    h += sub('الربح التشغيلي','Operating profit', C.opProfit, L&&L.opProfit, 'IFRS 18.69(a), 70');

    h += cat('الفئة الاستثمارية','Investing category · IFRS 18.53');
    h += nil('الحصة في نتائج شركات زميلة ومشاريع مشتركة','Share of profit of associates and joint ventures','IFRS 18.75(a)(iii)');
    C.invRows.forEach((x,i) => { const lv = L && L.invRows[i] ? L.invRows[i][2] : null;
      h += r(x[0], x[1], x[2], lv, x[3]); });
    h += sub('الربح قبل التمويل والزكاة','Profit before financing and income taxes', C.pbft, L&&L.pbft, 'IFRS 18.69(b)');

    h += cat('فئة التمويل','Financing category · IFRS 18.59–61');
    C.finRows.forEach((x,i) => { const lv = L && L.finRows[i] ? L.finRows[i][2] : null;
      h += r(x[0], x[1], x[2], lv, x[3]); });
    h += sub('الربح قبل الزكاة','Profit before Zakat', C.pbt, L&&L.pbt, 'IFRS 18.71');

    h += cat('فئة ضرائب الدخل — الزكاة','Income taxes category — Zakat · IFRS 18.67');
    h += r('مخصص الزكاة الشرعية','Zakat charge', -C.zak, L&&-L.zak, 'حساب 3280005');
    h += sub('الربح من العمليات المستمرة','Profit from continuing operations', C.profit, L&&L.profit, 'IFRS 18.24');

    h += cat('العمليات غير المستمرة','Discontinued operations · IFRS 18.68');
    h += nil('الربح/(الخسارة) بعد الضريبة من العمليات غير المستمرة','Profit/(loss) after tax from discontinued operations','IFRS 18.75(a)(v)');
    h += sub('ربح الفترة','Profit', C.profit, L&&L.profit, 'IFRS 18.72');
    h += `</tbody></table></div>
      <div class="note" style="margin-top:14px"><b>الفئات الخمس.</b> المعيار يفرض تصنيف كل بند إلى واحدة من خمس فئات. المنشأة ليس لديها نشاط رئيسي محدد بالاستثمار في الأصول أو تمويل العملاء، فتنطبق عليها القواعد العامة (نفس استنتاج EY لمجموعة Good Group). الزكاة ليست ضريبة دخل ضمن نطاق المعيار 12، لكنها تُعرض هنا في موقع فئة ضرائب الدخل لأنها العبء الوحيد من هذا النوع — وهذا إفصاح يجب ذكره في السياسات المحاسبية. لا توجد عمليات غير مستمرة ولا استثمارات بطريقة حقوق الملكية، والبندان معروضان بصفر لأن المعيار يطلبهما كبنود مستقلة عند وجودهما.</div>`;
    cMain.innerHTML = h;

    /* ---- IFRS 18.83 specified expenses by nature ---- */
    const S = C.spec;
    if(st.view === 'fn') renderFnNotes(C, L); else cNat.style.display = 'none';
    const sr = (ar,en,v,note) => `<tr><td>${ar}<span class="i18-en">${en}</span></td><td class="n">${v===null?'—':nfmt(v)}</td><td class="i18-note2">${note||''}</td></tr>`;
    if(st.view !== 'fn') cSpec.innerHTML = `<h3>المصروفات المحددة بطبيعتها ضمن الفئة التشغيلية</h3>
      <p class="card-sub">IFRS 18.83 — إيضاح واحد يجمع خمسة بنود بعينها، مع بيان البنود خارج الفئة التشغيلية التي تتضمن جزءاً منها. القائمة أعلاه معروضة بالكامل بالطبيعة، فهذا الإيضاح يُظهر التفصيل لا التحويل</p>
      <div class="aud-x"><table class="aud-t i18-t"><thead><tr><th>البند</th><th class="n">الفترة</th><th>ملاحظة</th></tr></thead><tbody>
      ${sr('الإهلاك','Depreciation', S.dep, 'كامله ضمن الفئة التشغيلية')}
      ${sr('الإطفاء','Amortisation', null, 'لا توجد أصول غير ملموسة قابلة للإطفاء في الدفتر')}
      ${sr('منافع الموظفين','Employee benefits', S.emp, 'تشمل التأمينات الاجتماعية وعلاج العاملين وتكلفة الخدمة الحالية')}
      ${S.empAcc.map(([a,v]) => `<tr class="i18-detail"><td>— ${nm(a)[0]}<span class="i18-en">${nm(a)[1]}</span></td><td class="n">${nfmt(v)}</td><td class="i18-note2">${a}</td></tr>`).join('')}
      ${sr('خسائر الانخفاض في القيمة وعكسها','Impairment losses and reversals', null, '<b>لا يوجد حساب مخصص ديون مشكوك في تحصيلها في شجرة الحسابات إطلاقاً</b>')}
      ${sr('تخفيض قيمة المخزون','Write-down of inventories', S.wdown, 'حساب التسويات الجردية والبضاعة التالفة — صافيه صفر في هذه الفترة')}
      </tbody></table></div>
      <div class="note" style="margin-top:12px"><b>بنود خارج الفئة التشغيلية تتضمن جزءاً من هذه المبالغ (IFRS 18.83).</b> تكلفة العمولة على التزامات منافع الموظفين (${nfmt(C.eosbInt)}) معروضة ضمن فئة التمويل وليست ضمن إجمالي منافع الموظفين أعلاه. ولا توجد مبالغ إهلاك أو إطفاء أو انخفاض قيمة مرسملة ضمن المخزون في نهاية الفترة.</div>`;

    /* ---- MPM note (IFRS 18.121–123) ---- */
    const dep = S.dep, ebitda = C.opProfit + dep;
    const m3 = (ar,en,v,tax,nci,cls) => `<tr class="${cls||''}"><td>${ar}<span class="i18-en">${en}</span></td><td class="n">${nfmt(v)}</td><td class="n">${tax}</td><td class="n">${nci}</td></tr>`;
    cMpm.innerHTML = `<h3>المقياس المعرَّف من الإدارة (MPM)</h3>
      <p class="card-sub">IFRS 18.121–123 — إيضاح واحد يذكر لماذا يُستخدم المقياس، وكيف يُحتسب، ومطابقته بأقرب مجموع فرعي يفرضه المعيار، مع <b>الأثر الضريبي وأثر الحقوق غير المسيطرة لكل بند تسوية</b></p>
      <div class="aud-x"><table class="aud-t i18-t"><thead><tr><th>المطابقة</th><th class="n">الفترة</th><th class="n">الأثر الزكوي</th><th class="n">حقوق غير مسيطرة</th></tr></thead><tbody>
      <tr class="i18-sub"><td><b>الربح التشغيلي</b><span class="i18-en">Operating profit — mandated subtotal · IFRS 18.69(a)</span></td><td class="n"><b>${nfmt(C.opProfit)}</b></td><td class="n">—</td><td class="n">—</td></tr>
      ${m3('يُضاف: الإهلاك','add back: depreciation', dep, '—', '—')}
      <tr class="i18-sub"><td><b>EBITDA</b><span class="i18-en">Management-defined performance measure</span></td><td class="n"><b>${nfmt(ebitda)}</b></td><td class="n">—</td><td class="n">—</td></tr>
      </tbody></table></div>
      <div class="note" style="margin-top:12px"><b>شرطان قبل تسمية هذا المقياس MPM.</b> (١) المعيار يعرّف الـMPM بأنه مجموع فرعي <i>تستخدمه الإدارة في تواصلها العلني خارج القوائم المالية</i> — في العروض للمستثمرين أو البيانات الصحفية أو تقرير مجلس الإدارة. إن كانت EBITDA تُستخدم داخلياً فقط فهي ليست MPM ولا يلزم هذا الإيضاح؛ وإن ذُكرت علناً فالإيضاح إلزامي بهذا الشكل. (٢) الأثر الضريبي: المعيار يطلب بيان أثر ضريبة الدخل وأثر الحقوق غير المسيطرة لكل بند تسوية (IFRS 18.123(c),(d)). الزكاة في المنشأة تُحتسب على الوعاء الزكوي لا على الربح المحاسبي، فأثر إضافة الإهلاك على عبء الزكاة صفر — وهذا في ذاته إفصاح يجب ذكره، ولا يُترك فراغاً. ولا توجد حقوق غير مسيطرة.</div>
      <p class="card-sub" style="margin-top:10px">EBITDA هنا مبنية على الربح التشغيلي وفق IFRS 18 — أي بعد نقل إيراد الإيجار وفوائد القروض وعمولة التزامات نهاية الخدمة خارج الفئة التشغيلية — فتختلف عن EBITDA في شريط اللوحة (${nfmt(C.deskEbitda)}) بمقدار ${nfmt(Math.abs((C.deskEbitda||0)-ebitda))}.</p>`;

    /* ---- audit findings ---- */
    const iso = t => t.replace(/((?:IFRS|IAS)\s*[0-9][0-9.]*(?:–[0-9]+)?(?:\([a-z0-9]+\))*|\b[0-9]{7}\b)/g,'<bdi>$1</bdi>');
  const fnd = (sev, ar, en, val) => `<div class="i18-f i18-f-${sev}"><div class="i18-fh"><span class="i18-fb">${sev==='fix'?'صُحِّح':sev==='cls'?'أُعيد التصنيف':'مرفوع للإدارة'}</span><b>${ar}</b>${val!==undefined?`<span class="i18-fv">${nfmt(val)}</span>`:''}</div><div class="i18-fd">${iso(en)}</div></div>`;
    cAud.innerHTML = `<h3>مراجعة هذا التبويب مقابل دليل EY — Good Group (IFRS 18)</h3>
      <p class="card-sub">ما وجدته المراجعة، ومكان كل تصحيح في القائمة أعلاه. الأرقام بين قوسين هي أثر البند على السنة المالية 2025</p>
      <div class="i18-flist">
      ${fnd('fix','الزكاة كانت محمَّلة مرتين','مخصص الزكاة (حساب 3280005) يقع داخل مجموعة «المخصصات» التي كانت تُطرح كمصروف تشغيلي، ثم كانت الزكاة تُطرح مرة ثانية من القوائم المدققة. النتيجة: الربح التشغيلي وربح الفترة كلاهما ناقص بمقدار الزكاة، و«الربح قبل الزكاة» المعروض كان في الحقيقة صافي الربح بعدها. الآن الزكاة تُقرأ من الدفتر مباشرة وتُطرح مرة واحدة فقط في فئة ضرائب الدخل — والقائمة صارت تُطابق القوائم المدققة للسنة 2025 في حدود 40 ريالاً.', 147643)}
      ${fnd('cls','تكلفة العمولة على التزامات منافع الموظفين → فئة التمويل','كانت داخل «مصروفات تشغيلية أخرى». دليل EY (إيضاح 13.4، IFRS 18.61(a)) يضع صافي عمولة التزامات المنافع بعد انتهاء الخدمة في فئة التمويل ضمن «فوائد على التزامات أخرى». النقل لا يغيّر الربح لكنه يرفع الربح التشغيلي ويخفض الربح قبل التمويل والزكاة.', 334391)}
      ${fnd('cls','فروق حسابات البنوك → الفئة الاستثمارية','حساب 4300009 كان ضمن الإيرادات التشغيلية الأخرى. IFRS 18.53(b) يضع دخل ومصروفات النقد وما في حكمه في الفئة الاستثمارية، وهذا ما فعله EY بـ«فروق العملة على النقد والودائع قصيرة الأجل».', 4908)}
      ${fnd('cls','خسائر استبعاد الأصول صارت بنداً مستقلاً','الأرباح الرأسمالية (4300008) كانت معروضة ومربوطة بمفتاح تبديل، بينما الخسائر الرأسمالية (3380000) كانت مدفونة داخل «مصروفات تشغيلية أخرى» وتبقى تشغيلية مهما كان إعداد المفتاح. IFRS 18.44 يمنع المقاصة، و B60 يطلب تصنيف الطرفين في نفس الفئة — البندان الآن مربوطان بمفتاح واحد.', 839920)}
      ${fnd('flag','حسميات مطالبات التأمين: مصروف أم خصم من الإيراد؟','حساب 3280004 «خصم إضافي عملاء شركات التأمين» يُقيَّد <b>مرة واحدة في ديسمبر من كل سنة</b> كتسوية سنوية. بمقتضى IFRS 15.50–53 هذا مقابل متغير يُخفّض الإيراد لا مصروف تشغيلي. الأثر على الربح التشغيلي صفر، لكن الإيراد المعلن أعلى بهذا المبلغ. والأهم: قيده في ديسمبر وحده يجعل أحد عشر شهراً تظهر بربح تشغيلي مبالغ فيه وشهراً واحداً يمتصّ الفرق كله. المفتاح أعلاه يعرض الطريقتين.', 3653273)}
      ${fnd('flag','لا يوجد مخصص خسائر ائتمانية متوقعة','IFRS 18.75 يطلب عرض خسائر الانخفاض في القيمة المحددة وفق المعيار 9 كبند مستقل في القائمة. لا يوجد في شجرة الحسابات حساب لمخصص الديون المشكوك في تحصيلها، على محفظة ذمم تأمين بهذا الحجم. البند معروض بصفر أعلاه لأن هذا هو ما يقوله الدفتر، وليس لأن المخصص غير مطلوب.')}
      ${fnd('fix','المصروفات صارت معروضة بطبيعتها','كانت القائمة تعرض مجموعات اللوحة، وأكبرها «مصروفات تشغيلية أخرى» بنحو ٢٠٪ من الإيراد — وهي تخلط المستهلكات والإيجار وخسائر الاستبعاد وعمولة نهاية الخدمة. IFRS 18.B79 يمنع تسمية بند جوهري «أخرى»، و 18.78 يطلب تحليلاً بالطبيعة أو بالوظيفة يقدّم أنفع ملخّص. القائمة الآن مبنية من الحسابات مباشرة على نمط الملحق ٢ في دليل EY، و«مصروفات إدارية أخرى» صارت أقل من ٠٫٥٪ من الإيراد.')}
      ${fnd('fix','إيضاح المقياس المعرَّف من الإدارة اكتمل','كان يعرض المطابقة فقط. IFRS 18.123 يطلب أيضاً الأثر الضريبي وأثر الحقوق غير المسيطرة لكل بند تسوية وطريقة احتسابهما، ويشترط قبل ذلك كله أن يكون المقياس مستخدماً في التواصل العلني خارج القوائم — وهذا شرط تحقّق لا حساب.')}
      ${fnd('fix','بنود وعناوين مطلوبة أُضيفت','عناوين الفئات الخمس، والحصة في نتائج الشركات الزميلة (IFRS 18.75(a)(iii))، والعمليات غير المستمرة (75(a)(v))، ووسم الفترة المقارنة بأنها مُعاد عرضها (IFRS 18.27(d),(e))، وتسمية القائمة «قائمة الأرباح أو الخسائر» كما يقترح IFRS 18.10(a) بدل «قائمة الدخل».')}
      </div>
      <div class="note" style="margin-top:14px"><b>ما لم يتغيّر، وسببه.</b> العمولات البنكية (${nfmt(NATM['bankc'][3].reduce((t,x)=>t+accFlow(x,w.a,w.b,TI.cc),0))}) بقيت تشغيلية: المعيار يضع في فئة التمويل الدخل والمصروف من التزامات غرضها الوحيد جمع التمويل، والعمولة البنكية مقابل خدمة لا مقابل تمويل. وعناوين «الفئة الاستثمارية» و«فئة التمويل» في القائمة أعلاه ليست مطلوبة — دليل EY لا يضع عناوين فئات على وجه القائمة، والمعيار لا يفرض مجموعاً فرعياً أو عنواناً موصوفاً بأنه «استثماري». أُبقيت هنا لأن الغرض شرح التصنيف؛ عند إصدار قوائم فعلية تُحذف ويُكتفى بالمجموعين الفرعيين.</div>`;

    /* ---- bridge back to the desk ---- */
    const movedInv = C.investing, movedFin = -C.financing;
    cRec.innerHTML = `<h3>الجسر من صافي النتيجة في اللوحة إلى الربح التشغيلي وفق IFRS 18</h3>
      <p class="card-sub">نفس الربح، مكان مختلف — هذا مصدر الفرق بين «الربح التشغيلي» هنا وأي رقم تشغيلي آخر في اللوحة</p>
      <table class="aud-t i18-t"><tbody>
      ${r('صافي النتيجة في شريط اللوحة','Net result, period strip', C.deskNet, L&&L.deskNet)}
      ${r('يُضاف: الزكاة (كانت مُحمَّلة ضمن المخصصات)','add back: Zakat, previously inside provisions', C.zak, L&&L.zak)}
      ${r('يُنقل إلى الفئة الاستثمارية','reclassified to investing', -movedInv, L?-L.investing:null)}
      ${r('يُنقل إلى فئة التمويل','reclassified to financing', movedFin, L?-L.financing:null)}
      ${r('فروق تفصيل الحسابات مقابل مجموعات اللوحة','GL detail vs the desk’s aggregate buckets', C.opProfit - ((C.deskNet||0) + C.zak - movedInv + movedFin), null)}
      ${sub('= الربح التشغيلي وفق IFRS 18','= Operating profit under IFRS 18', C.opProfit, L&&L.opProfit)}
      </tbody></table>`;
  }
  TI.on(render); render();
})();
