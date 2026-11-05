
  /* ------------------------------ capital + metrics (shared by scorecard / drivers) ------------------------------ */
  function capital(cc,b){
    const yi = EXT.years.indexOf(yOf(b)); if(yi < 0) return null; const bs = EXT.bs, v = (k,i) => bs[k][i] || 0;
    const bal = i => ({fix:v('fixed_net',i)+v('wip',i), rec:v('ar',i)+v('other_debtors',i), inv:v('inventory',i)+v('prepaid',i)});
    const cl = bal(yi), op = yi > 0 ? bal(yi-1) : cl, av = {fix:(cl.fix+op.fix)/2, rec:(cl.rec+op.rec)/2, inv:(cl.inv+op.inv)/2};
    const a2 = Math.max(0,b-11);
    const depBr = c => sumLn(c,'dep',a2,b) + sumLn('00','dep',a2,b)*revShare(c,a2,b);
    const sD = BR.reduce((s,c)=>s+depBr(c),0), sC = BR.reduce((s,c)=>s+sumLn(c,'cred',a2,b),0);
    const ds = cc==='ALL' ? 1 : (sD ? depBr(cc)/sD : 0), cs = cc==='ALL' ? 1 : (sC ? sumLn(cc,'cred',a2,b)/sC : 0), rs = cc==='ALL' ? 1 : revShare(cc,a2,b);
    const o = {fix:av.fix*ds, rec:av.rec*cs, inv:av.inv*rs}; o.total = o.fix+o.rec+o.inv; return o;
  }
  function metricsOf(c,w){
    const d = stat(c,w.a,w.b,false), s = stat(c,w.a,w.b,true), pw = winPrev(w), p = pw ? stat(c,pw.a,pw.b,false) : null;
    const emp = natOf(c,'emp',w.a,w.b), n = months(w), cap = capital(c,w.b), ms = [];
    for(let i = w.a; i <= w.b; i++){ const r = (c==='ALL'?ALLC:[c]).reduce((q,k)=>q+sumLn(k,'cash',i,i)+sumLn(k,'cred',i,i),0), k2 = (c==='ALL'?ALLC:[c]).reduce((q,k)=>q+sumLn(k,'cor',i,i)+sumLn(k,'ins',i,i),0); if(r > 0) ms.push((r-k2)/r); }
    const mean = ms.reduce((a,x)=>a+x,0)/(ms.length||1), sd = ms.length > 2 ? Math.sqrt(ms.reduce((a,x)=>a+(x-mean)*(x-mean),0)/ms.length) : null;
    const dr = p ? delta(d.rev,p.rev) : null, dc = p ? delta(d.contrib,p.contrib) : null;
    return {d,s,p,cap,n, contribM:d.contrib/d.rev, opM:s.op/s.rev, ebitdaM:s.ebitda/s.rev, netM:s.net/s.rev, growth:dr, cashSh:d.cash/d.rev, credSh:d.cred/d.rev,
      costEff:d.rev/(d.cor+d.ins), corR:d.cor/d.rev, insR:d.cred ? d.ins/d.cred : null, payR:emp/d.rev, payEff:emp ? d.rev/emp : null, depInt:d.dep/d.rev, sd,
      dol:(dr!==null && dc!==null && Math.abs(dr) > .005) ? dc/dr : null,
      roce:cap ? s.op*12/n/cap.total : null, turn:cap ? d.rev*12/n/cap.total : null};
  }
  const MET = [ // id, EN, AR, fmt, higherBetter, weight, group
    ['contribM','Contribution margin (rev − direct − insurance − G&A)','هامش المساهمة (إيراد − مباشر − تأمين − عمومية)',v=>fp(v),1,25,'a'],
    ['opM','Operating margin after head-office allocation','هامش التشغيل بعد توزيع الإدارة العامة',v=>fp(v),1,15,'a'],
    ['ebitdaM','EBITDA margin (allocated)','هامش EBITDA (بعد التوزيع)',v=>fp(v),1,0,'a'],
    ['netM','Net margin (allocated)','هامش صافي الدخل (بعد التوزيع)',v=>fp(v),1,0,'a'],
    ['growth','Revenue growth vs same period last year','نمو الإيراد مقابل نفس الفترة العام السابق',v=>fs(v),1,15,'h'],
    ['dol','Operating leverage (Δ contribution ÷ Δ revenue)','الرافعة التشغيلية (تغير المساهمة ÷ تغير الإيراد)',v=>fx(v),1,0,'h'],
    ['corR','Cost of revenue % of revenue','تكلفة الإيراد % من الإيراد',v=>fp(v),0,0,'o'],
    ['costEff','Revenue per SAR of direct + insurance cost','الإيراد لكل ريال تكلفة مباشرة وتأمين',v=>fx(v),1,10,'o'],
    ['payR','Payroll % of revenue (direct)','الرواتب % من الإيراد (مباشرة)',v=>fp(v),0,0,'o'],
    ['payEff','Revenue per SAR of payroll','الإيراد لكل ريال راتب',v=>fx(v),1,5,'o'],
    ['insR','Insurance-company expenses % of credit revenue','مصروفات شركات التأمين % من الإيراد الآجل',v=>fp(v),0,0,'o'],
    ['depInt','Depreciation % of revenue (capital intensity)','الإهلاك % من الإيراد (كثافة رأس المال)',v=>fp(v,2),0,0,'c'],
    ['turn','Capital turnover (annualised revenue ÷ attributed capital)','دوران رأس المال (الإيراد السنوي ÷ رأس المال المنسوب)',v=>fx(v),1,0,'c'],
    ['roce','ROCE (annualised operating profit ÷ attributed capital)','العائد على رأس المال المستثمر (الربح التشغيلي السنوي ÷ رأس المال المنسوب)',v=>fp(v),1,15,'c'],
    ['cashSh','Cash share of revenue','نسبة الإيراد النقدي',v=>fp(v),1,5,'k'],
    ['sd','Stability — volatility of monthly contribution margin','الاستقرار — تذبذب هامش المساهمة الشهري',v=>fp(v),0,10,'k']];
  const GRP = {a:['Profitability','الربحية'], h:['Growth (horizontal)','النمو (أفقي)'], o:['Operating efficiency','كفاءة التشغيل'], c:['Capital efficiency','كفاءة رأس المال'], k:['Cash quality & stability','جودة النقد والاستقرار']};

  function score(M){ // M: {cc: metrics}; min–max across the four branches
    const sc = {}; BR.forEach(c => sc[c] = {tot:0,w:0,parts:{}});
    MET.forEach(m => { if(!m[5]) return; const vals = BR.map(c => M[c][m[0]]); if(vals.some(v=>v===null||!isFinite(v))) return;
      const lo = Math.min(...vals), hi = Math.max(...vals);
      BR.forEach(c => { const v = M[c][m[0]], s = hi===lo ? 50 : (m[4] ? (v-lo)/(hi-lo) : (hi-v)/(hi-lo))*100; sc[c].tot += s*m[5]; sc[c].w += m[5]; sc[c].parts[m[0]] = s; }); });
    BR.forEach(c => sc[c].v = sc[c].w ? sc[c].tot/sc[c].w : null);
    return sc;
  }
  const rating = v => v===null ? ['—','—','bd-n'] : v >= 65 ? ['Strong','قوي','bd-ok'] : v >= 40 ? ['Moderate','متوسط','bd-mid'] : ['Weak','ضعيف','bd-bad'];

  function branchVerdict(c, M, G){
    const m = M[c], en = [], ar = [], nm = NAME[c];
    if(m.contribM > G.contribM+.02){ en.push(`Contribution margin ${fp(m.contribM)} is ${((m.contribM-G.contribM)*100).toFixed(1)} pp above the Group (${fp(G.contribM)}).`); ar.push(`هامش المساهمة ${fp(m.contribM)} أعلى من المجموعة بـ ${((m.contribM-G.contribM)*100).toFixed(1)} نقطة (${fp(G.contribM)}).`); }
    else if(m.contribM < G.contribM-.02){ en.push(`Contribution margin ${fp(m.contribM)} is ${((G.contribM-m.contribM)*100).toFixed(1)} pp below the Group (${fp(G.contribM)}) — direct cost is the issue.`); ar.push(`هامش المساهمة ${fp(m.contribM)} أقل من المجموعة بـ ${((G.contribM-m.contribM)*100).toFixed(1)} نقطة (${fp(G.contribM)}) — المشكلة في التكلفة المباشرة.`); }
    if(m.opM < 0){ en.push(`After its share of central costs the branch loses ${fp(-m.opM)} of revenue: it does not carry its overhead.`); ar.push(`بعد حصته من التكاليف المركزية يخسر الفرع ${fp(-m.opM)} من الإيراد: لا يغطي نصيبه من المصاريف العامة.`); }
    else { en.push(`Still earns ${fp(m.opM)} operating margin after allocated central costs.`); ar.push(`ما زال يحقق هامش تشغيلي ${fp(m.opM)} بعد توزيع التكاليف المركزية.`); }
    if(m.growth !== null){ const gd = m.growth - (G.growth||0);
      if(gd > .03){ en.push(`Revenue growth ${fs(m.growth)} beats the Group (${fs(G.growth)}).`); ar.push(`نمو الإيراد ${fs(m.growth)} يتفوق على المجموعة (${fs(G.growth)}).`); }
      else if(gd < -.03){ en.push(`Revenue growth ${fs(m.growth)} trails the Group (${fs(G.growth)}).`); ar.push(`نمو الإيراد ${fs(m.growth)} أقل من المجموعة (${fs(G.growth)}).`); } }
    if(m.cashSh < G.cashSh-.08){ en.push(`Credit-heavy: only ${fp(m.cashSh,0)} of revenue is collected in cash (Group ${fp(G.cashSh,0)}) — receivable and collection risk.`); ar.push(`يعتمد على الآجل: ${fp(m.cashSh,0)} فقط من الإيراد نقدي (المجموعة ${fp(G.cashSh,0)}) — مخاطر التحصيل والذمم.`); }
    else if(m.cashSh > G.cashSh+.08){ en.push(`Cash-rich mix: ${fp(m.cashSh,0)} of revenue is cash (Group ${fp(G.cashSh,0)}) — faster conversion.`); ar.push(`مزيج غني بالنقد: ${fp(m.cashSh,0)} من الإيراد نقدي (المجموعة ${fp(G.cashSh,0)}) — تحويل أسرع للنقد.`); }
    if(m.roce !== null){ en.push(`Return on attributed capital ${fp(m.roce)}; capital turns ${fx(m.turn)}.`); ar.push(`العائد على رأس المال المنسوب ${fp(m.roce)}؛ دوران رأس المال ${fx(m.turn)}.`); }
    return {en,ar};
  }

  /* ------------------------------ tab 3 · branch scorecard ------------------------------ */
  function tabScore(){
    const w = W(), M = {}; BR.concat(['ALL']).forEach(c => M[c] = metricsOf(c,w)); const sc = score(M), G = M.ALL;
    const order = BR.slice().sort((a,b)=>(sc[b].v||0)-(sc[a].v||0));
    let cards = `<div class="grid grid-4">` + BR.map(c => { const r = rating(sc[c].v), rk = order.indexOf(c)+1;
      return `<div class="card bd-sc"><div class="bd-sch"><i class="bd-dot" style="background:${COL[c]}"></i><b>${t(NAME[c][0],NAME[c][1])}</b><span class="bd-chip ${r[2]}">${ti(r[0],r[1])}</span></div>
        <div class="bd-big">${sc[c].v===null?'—':sc[c].v.toFixed(0)}<small>/100</small></div><div class="bd-sub">${ti('Rank','الترتيب')} ${rk} ${ti('of 4','من 4')} · ${ti('Contribution','المساهمة')} ${fp(M[c].contribM)}</div>${(q => `<div class="bd-sub bd-wi">${ti('If stopped, Group net income','لو أُوقف، صافي ربح المجموعة')}: <b class="${q.ces>=0?'bd-up':'bd-dn'}">${fd(q.ces)}</b> ${ti('stop trading','توقف')} · <b class="${q.sale>=0?'bd-up':'bd-dn'}">${fd(q.sale)}</b> ${ti('sale','بيع')}</div>`)(quickStop(c,w))}</div>`; }).join('') + `</div>`;
    // ratio table
    const cols = BR.concat(['ALL']); let t1 = `<tr><th>${t('Ratio','النسبة')}</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${c==='ALL'?'':`<i class="bd-dot" style="background:${COL[c]}"></i>`}${t(NAME[c][0],NAME[c][1])}</th>`).join('')}<th>${t('Weight','الوزن')}</th></tr>`;
    let lastG = '';
    MET.forEach(m => { if(m[6] !== lastG){ lastG = m[6]; t1 += `<tr class="bd-sep"><td colspan="${cols.length+2}">${t(GRP[m[6]][0],GRP[m[6]][1])}</td></tr>`; }
      const vals = BR.map(c => M[c][m[0]]).filter(v=>v!==null&&isFinite(v)); const lo = Math.min(...vals), hi = Math.max(...vals);
      t1 += `<tr><td>${t(m[1],m[2])}</td>${cols.map(c => { const v = M[c][m[0]]; let cls = ''; if(c!=='ALL' && vals.length>1 && lo!==hi){ if(v===(m[4]?hi:lo)) cls='bd-best'; else if(v===(m[4]?lo:hi)) cls='bd-worst'; }
        return `<td class="num ${c==='ALL'?'bd-grp':''} ${cls}">${v===null||!isFinite(v)?'—':m[3](v)}</td>`; }).join('')}<td class="num">${m[5]?m[5]+'%':'—'}</td></tr>`; });
    // vertical + horizontal
    const vr = ISR.filter(r=>!['dep','ebitda'].includes(r[0])); const SS = {}; cols.forEach(c => SS[c] = stat(c,w.a,w.b,ST.alloc));
    let t2 = `<tr><th>${t('Vertical analysis — % of revenue','التحليل الرأسي — % من الإيراد')}</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${t(NAME[c][0],NAME[c][1])}</th>`).join('')}</tr>`;
    vr.forEach(r => t2 += `<tr style="${r[4]===2?'font-weight:700;border-top:2px solid var(--border)':r[4]===1?'font-weight:600':''}"><td>${t(r[1],r[2])}</td>${cols.map(c=>`<td class="num ${c==='ALL'?'bd-grp':''}">${fp(r[3](SS[c])/SS[c].rev)}</td>`).join('')}</tr>`);
    const pw = winPrev(w); let t3 = '';
    if(pw){ const PS = {}; cols.forEach(c => PS[c] = stat(c,pw.a,pw.b,ST.alloc));
      t3 = `<tr><th>${t('Horizontal analysis — change vs same period last year','التحليل الأفقي — التغير مقابل نفس الفترة العام السابق')}</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${t(NAME[c][0],NAME[c][1])}</th>`).join('')}</tr>`;
      vr.forEach(r => t3 += `<tr style="${r[4]===2?'font-weight:700;border-top:2px solid var(--border)':r[4]===1?'font-weight:600':''}"><td>${t(r[1],r[2])}</td>${cols.map(c=>{ const d = delta(r[3](SS[c]),r[3](PS[c])); return `<td class="num ${c==='ALL'?'bd-grp':''} ${favCls(d)}">${fs(d)}</td>`; }).join('')}</tr>`); }
    // narratives
    const verd = BR.map(c => { const v = branchVerdict(c,M,G); const r = rating(sc[c].v);
      return `<div class="card"><div class="bd-sch"><i class="bd-dot" style="background:${COL[c]}"></i><b>${t(NAME[c][0],NAME[c][1])}</b><span class="bd-chip ${r[2]}">${ti(r[0],r[1])}</span></div><ul class="bd-ul">${v.en.map((x,i)=>`<li>${ST.lang==='ar'?v.ar[i]:x}${ST.lang==='both'?`<span class="bd-ar" dir="rtl">${v.ar[i]}</span>`:''}</li>`).join('')}</ul></div>`; }).join('');
    const cap = BR.map(c => M[c].cap).filter(Boolean); const capNote = cap.length ? `<div class="note">${t(`<b>How the score works.</b> Each branch is scored 0–100 against the other three (best = 100, worst = 0) on eight weighted measures — contribution margin 25%, operating margin 15%, growth 15%, ROCE 15%, revenue per SAR of cost 10%, stability 10%, revenue per SAR of payroll 5%, cash share 5%. It ranks the branches against each other; it is not an absolute grade. <b>Capital.</b> The ledger does not hold a balance sheet per branch (fixed assets, receivables and cash are held centrally and in the Riyadh ledger), so the Group’s operating assets from the Statements are attributed: fixed assets by depreciation share (head-office depreciation by revenue share), receivables by credit-revenue share, inventory and prepaid by revenue share, on the average of opening and closing balances. Group totals tie to the Statements; the split between branches is an attribution, not a booked figure.`,
      `<b>طريقة التقييم.</b> يُقيَّم كل فرع من 0 إلى 100 مقارنة بالفروع الثلاثة الأخرى (الأفضل 100 والأضعف 0) على ثمانية مقاييس موزونة — هامش المساهمة 25% والهامش التشغيلي 15% والنمو 15% والعائد على رأس المال 15% والإيراد لكل ريال تكلفة 10% والاستقرار 10% والإيراد لكل ريال راتب 5% ونسبة النقدي 5%. التقييم نسبي بين الفروع وليس درجة مطلقة. <b>رأس المال.</b> لا يحتفظ الدفتر بميزانية لكل فرع (الأصول الثابتة والذمم والنقد مسجلة مركزيًا وفي دفتر الرياض)، لذلك تُنسب أصول المجموعة التشغيلية من القوائم: الأصول الثابتة بنسبة الإهلاك (وإهلاك الإدارة العامة بنسبة الإيراد)، والذمم بنسبة الإيراد الآجل، والمخزون والمدفوع مقدمًا بنسبة الإيراد، على متوسط الرصيد الافتتاحي والختامي. مجموع المجموعة يطابق القوائم أما التوزيع بين الفروع فهو نسبة وليس رقمًا مسجلاً.`)}</div>` : '';
    const capT = cap.length ? `<tr class="bd-sep"><td colspan="${cols.length+2}">${t('Attributed capital employed, SAR','رأس المال المستثمر المنسوب، ريال')}</td></tr>` + [['fix','Fixed assets & WIP','أصول ثابتة وتحت التنفيذ'],['rec','Receivables & other debtors','ذمم وأرصدة مدينة'],['inv','Inventory & prepaid','مخزون ومدفوع مقدمًا'],['total','Total','الإجمالي']].map(k=>`<tr style="${k[0]==='total'?'font-weight:700':''}"><td>${t(k[1],k[2])}</td>${cols.map(c=>`<td class="num ${c==='ALL'?'bd-grp':''}">${M[c].cap?fm(M[c].cap[k[0]]):'—'}</td>`).join('')}<td></td></tr>`).join('') : '';
    body.innerHTML = cards + `<div class="card" style="margin-top:14px"><h3>${t('Branch ratios — financial, operating and capital efficiency','نسب الفروع — الكفاءة المالية والتشغيلية وكفاءة رأس المال')}</h3><p class="card-sub">${ti('Green = best branch on the measure, red = weakest; Group column for reference','الأخضر = أفضل فرع في المقياس والأحمر = الأضعف؛ عمود المجموعة للمرجع')}</p><div class="tbl-scroll"><table class="bd-t">${t1}${capT}</table></div></div>`
      + `<div class="card" style="margin-top:14px"><div class="tbl-scroll"><table class="bd-t">${t2}</table></div></div>${t3?`<div class="card" style="margin-top:14px"><div class="tbl-scroll"><table class="bd-t">${t3}</table></div></div>`:need12()}`
      + `<h3 class="bd-h3">${t('Assessment of each branch','تقييم كل فرع')}</h3><div class="grid grid-2">${verd}</div>` + capNote;
  }

  /* ------------------------------ tab 4 · cash vs credit ------------------------------ */
  function tabCC(){
    const w = W(), pw = winPrev(w), cols = BR.concat(['ALL']); const S = {}, P = {}; cols.forEach(c => { S[c] = stat(c,w.a,w.b,false); P[c] = pw ? stat(c,pw.a,pw.b,false) : null; });
    const G = S.ALL, GP = P.ALL;
    let tiles = `<div class="grid grid-4" style="margin-bottom:14px">` + kpiTile(ti('Cash revenue','الإيراد النقدي'),'SAR '+fM(G.cash), GP?fs(delta(G.cash,GP.cash))+' '+ti('vs PY','مقابل العام السابق'):'') +
      kpiTile(ti('Credit revenue','الإيراد الآجل'),'SAR '+fM(G.cred), GP?fs(delta(G.cred,GP.cred))+' '+ti('vs PY','مقابل العام السابق'):'') +
      kpiTile(ti('Credit share','نسبة الآجل'), fp(G.cred/G.rev), GP?((G.cred/G.rev-GP.cred/GP.rev)*100>=0?'+':'−')+Math.abs((G.cred/G.rev-GP.cred/GP.rev)*100).toFixed(1)+' pp':'') +
      kpiTile(ti('Insurance expenses ÷ credit revenue','مصروفات التأمين ÷ الإيراد الآجل'), fp(G.ins/G.cred), GP?((G.ins/G.cred-GP.ins/GP.cred)*100>=0?'+':'−')+Math.abs((G.ins/G.cred-GP.ins/GP.cred)*100).toFixed(1)+' pp':'') + `</div>`;
    let tb = `<tr><th>SAR</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${c==='ALL'?'':`<i class="bd-dot" style="background:${COL[c]}"></i>`}${t(NAME[c][0],NAME[c][1])}</th>`).join('')}</tr>`;
    const rws = [['Cash revenue','الإيراد النقدي',s=>s.cash,'v'],['Credit revenue','الإيراد الآجل',s=>s.cred,'v'],['Credit share %','نسبة الآجل %',s=>s.cred/s.rev,'p'],
      ['Insurance-company expenses','مصروفات شركات التأمين',s=>s.ins,'v'],['Insurance expenses % of credit revenue','مصروفات التأمين % من الآجل',s=>s.ins/s.cred,'p'],['Net credit revenue (credit − insurance expenses)','صافي الإيراد الآجل (آجل − مصروفات التأمين)',s=>s.cred-s.ins,'v'],
      ['Share of Group cash revenue','حصة المجموعة من النقدي',(s,c)=>G.cash?S[c].cash/G.cash:0,'p'],['Share of Group credit revenue','حصة المجموعة من الآجل',(s,c)=>G.cred?S[c].cred/G.cred:0,'p']];
    rws.forEach(r => tb += `<tr><td>${t(r[0],r[1])}</td>${cols.map(c=>{ const v = r[2](S[c],c); return `<td class="num ${c==='ALL'?'bd-grp':''}">${r[3]==='p'?fp(v):fm(v)}</td>`; }).join('')}</tr>`);
    if(pw){ [['Cash revenue growth','نمو الإيراد النقدي','cash'],['Credit revenue growth','نمو الإيراد الآجل','cred']].forEach(r => tb += `<tr><td>${t(r[0],r[1])}</td>${cols.map(c=>{ const d = delta(S[c][r[2]],P[c][r[2]]); return `<td class="num ${c==='ALL'?'bd-grp':''} ${favCls(d)}">${fs(d)}</td>`; }).join('')}</tr>`); }
    // charts
    const stk = stack100(BR.concat(['ALL']).map(c => ({label:pick(NAME[c]), parts:[{v:S[c].cash,color:'#146356'},{v:S[c].cred,color:'#3D6FB5'}]})));
    const qs = []; for(let i = 0; i+2 <= LASTC; i += 3) qs.push([i,i+2]);
    const ql = qs.map(q => 'Q'+(Math.floor(mOf(q[0])/3)+1)+' '+String(yOf(q[0])).slice(2));
    const ser = BR.concat(['ALL']).map(c => ({name:pick(NAME[c]),color:COL[c],w:c==='ALL'?2.6:1.8,dash:c==='ALL',vals:qs.map(q=>{ const s = stat(c,q[0],q[1],false); return s.rev ? s.cred/s.rev : null; })}));
    // credit exposure (group)
    const yi = EXT.years.indexOf(yOf(w.b)), ar = EXT.bs.ar[yi], arP = yi>0 ? EXT.bs.ar[yi-1] : null, t12 = stat('ALL',Math.max(0,w.b-11),w.b,false).cred, dso = t12 ? ar/t12*365 : null;
    const dsoP = (yi>0 && w.b-12>=0) ? EXT.bs.ar[yi-1]/Math.max(1,stat('ALL',Math.max(0,w.b-23),w.b-12,false).cred)*365 : null;
    // ledger-held
    const LYE = DB.dbDates.length-2;   // latest year-end held in DATA.bd.db
    let lt = `<tr><th>${t('Ledger-held balances (as booked)','أرصدة الدفتر (كما هي مسجلة)')}</th>${BR.map(c=>`<th>${t(NAME[c][0],NAME[c][1])}</th>`).join('')}<th>${t('Sum','المجموع')}</th></tr>`;
    [['ar','Receivables (124)','ذمم مدينة (124)'],['cash','Cash & bank accounts (121–122)','النقد والبنوك (121–122)']].forEach(k => { lt += `<tr><td>${t(k[1],k[2])} · ${DB.dbDates[LYE]}</td>${BR.map(c=>`<td class="num">${fm(DB.db[c][k[0]][LYE])}</td>`).join('')}<td class="num">${fm(BR.reduce((s,c)=>s+DB.db[c][k[0]][LYE],0))}</td></tr>`; });
    const topCred = BR.slice().sort((a,b)=>S[b].cred/S[b].rev - S[a].cred/S[a].rev)[0], topCash = BR.slice().sort((a,b)=>S[b].cash/S[b].rev - S[a].cash/S[a].rev)[0];
    let nar = narr(`Cash is ${fp(G.cash/G.rev,0)} of Group revenue and credit ${fp(G.cred/G.rev,0)}. ${NAME[topCred][0]} is the most credit-dependent branch (${fp(S[topCred].cred/S[topCred].rev,0)} credit); ${NAME[topCash][0]} is the most cash-based (${fp(S[topCash].cash/S[topCash].rev,0)} cash).` + (pw ? ` Cash revenue ${fs(delta(G.cash,GP.cash))} and credit revenue ${fs(delta(G.cred,GP.cred))} versus the same period last year.` : ''),
      `النقدي ${fp(G.cash/G.rev,0)} من إيراد المجموعة والآجل ${fp(G.cred/G.rev,0)}. ${NAME[topCred][1]} هو الأكثر اعتمادًا على الآجل (${fp(S[topCred].cred/S[topCred].rev,0)})، و${NAME[topCash][1]} هو الأكثر نقدية (${fp(S[topCash].cash/S[topCash].rev,0)}).` + (pw ? ` الإيراد النقدي ${fs(delta(G.cash,GP.cash))} والآجل ${fs(delta(G.cred,GP.cred))} مقابل نفس الفترة العام السابق.` : ''));
    nar += narr(`Credit exposure: Group receivables are SAR ${fM(ar)} at ${EXT.year_labels?EXT.year_labels[yi]:yOf(w.b)}${arP!==null?` (SAR ${fM(arP)} a year earlier)`:''}, about ${dso===null?'—':dso.toFixed(0)} days of trailing-12-month credit revenue${dsoP!==null?` (${dsoP.toFixed(0)} days a year earlier)`:''}. Every SAR of credit revenue also carries insurance-company charges of ${fp(G.ins/G.cred,1)}, so net credit revenue is ${fm(G.cred-G.ins)}.`,
      `التعرض الآجل: ذمم المجموعة ${fM(ar)} ريال${arP!==null?` (مقابل ${fM(arP)} قبل عام)`:''}، أي نحو ${dso===null?'—':dso.toFixed(0)} يومًا من الإيراد الآجل لآخر 12 شهرًا${dsoP!==null?` (${dsoP.toFixed(0)} يومًا قبل عام)`:''}. كل ريال آجل يحمل أيضًا مصروفات شركات التأمين بنسبة ${fp(G.ins/G.cred,1)} فيكون صافي الإيراد الآجل ${fm(G.cred-G.ins)}.`);
    body.innerHTML = tiles + nar + `<div class="grid grid-2" style="margin-top:14px"><div class="card"><h3>${t('Revenue mix by branch','مزيج الإيراد حسب الفرع')}</h3><p class="card-sub">${ti('Cash vs credit, share of revenue','النقدي مقابل الآجل، نسبة من الإيراد')}</p>${legend([[ti('Cash','نقدي'),'#146356'],[ti('Credit','آجل'),'#3D6FB5']])}${stk}</div>
      <div class="card"><h3>${t('Credit share over time','نسبة الآجل عبر الزمن')}</h3><p class="card-sub">${ti('Quarterly, closed months','ربع سنوي، الأشهر المغلقة')}</p>${legend(ser.map(s=>[s.name,s.color]))}${lines(ser,ql,{pct:true})}</div></div>
      <div class="card" style="margin-top:14px"><h3>${t('Cash and credit revenue by branch','الإيراد النقدي والآجل حسب الفرع')}</h3><div class="tbl-scroll"><table class="bd-t">${tb}</table></div></div>
      <div class="card" style="margin-top:14px"><div class="tbl-scroll"><table class="bd-t">${lt}</table></div><p class="card-sub" style="margin-top:8px">${ti('Receivables are booked across the four ledgers: Riyadh carries a net credit balance because collections for the other branches are posted there, so ledger balances are shown for transparency, not as a branch ranking.','الذمم مسجلة عبر الدفاتر الأربعة: لدفتر الرياض رصيد دائن صافٍ لأن تحصيلات الفروع الأخرى تُسجل فيه، لذلك تُعرض الأرصدة للشفافية وليس لترتيب الفروع.')}</p></div>`;
  }

  /* ------------------------------ tab 5 · cash & profit drivers ------------------------------ */
  function tabDrv(){
    const w = W(), pw = winPrev(w), cc = ST.cc==='00' ? 'ALL' : ST.cc, cols = BR.concat(['ALL']);
    const S = stat(cc,w.a,w.b,false), P = pw ? stat(cc,pw.a,pw.b,false) : null; let h = '';
    if(ST.cc==='00') h += `<div class="note">${ti('Head office has no revenue, so the drivers below are shown for the Group.','الإدارة العامة بلا إيراد لذلك تُعرض المحركات للمجموعة.')}</div>`;
    // profit drivers
    const natRows = natCodes.map(k => ({k, cur:natOf(cc,k,w.a,w.b), prv:pw?natOf(cc,k,pw.a,pw.b):0})).filter(r => r.cur || r.prv);
    if(pw){
      const eff = natRows.map(r => ({...r, e:-(r.cur/S.rev - r.prv/P.rev)})).sort((a,b)=>a.e-b.e);
      const mCur = S.op/S.rev, mPrv = P.op/P.rev, natT = eff.reduce((s,r)=>s+r.e,0), other = (mCur-mPrv) - natT;
      const items = eff.filter(r=>Math.abs(r.e)>0.0004).map(r => ({label:pick(DB.natLab[r.k]), v:r.e*100, color:r.e>=0?'var(--good)':'var(--critical)', text:(r.e>=0?'+':'−')+Math.abs(r.e*100).toFixed(2)+' pp'}));
      if(Math.abs(other)>0.0004) items.push({label:ti('Other revenue, zakat & cost-mix','إيرادات أخرى وزكاة وتوزيع التكلفة'), v:other*100, color:other>=0?'var(--good)':'var(--critical)', text:(other>=0?'+':'−')+Math.abs(other*100).toFixed(2)+' pp'});
      h += `<div class="card"><h3>${t('What moved the operating margin','ما الذي حرّك الهامش التشغيلي')} — ${TL(cc==='ALL'?['Group','المجموعة']:NAME[cc])}</h3><p class="card-sub">${ti('Operating margin','الهامش التشغيلي')} ${fp(mPrv)} → ${fp(mCur)} (${((mCur-mPrv)*100>=0?'+':'−')+Math.abs((mCur-mPrv)*100).toFixed(2)} pp) · ${ti('effect of each cost nature, percentage points of revenue; positive helps','أثر كل نوع تكلفة بنقاط النسبة من الإيراد؛ الموجب يخدم الربح')}</p>${hbars(items,{lw:230})}</div>`;
    } else h += need12();
    // nature × branch matrix
    let mt = `<tr><th>${t('Cost nature, % of revenue','نوع التكلفة، % من الإيراد')}</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${t(NAME[c][0],NAME[c][1])}</th>`).join('')}</tr>`;
    const SB = {}; cols.forEach(c => SB[c] = stat(c,w.a,w.b,false));
    natCodes.forEach(k => { const vals = BR.map(c => SB[c].rev ? natOf(c,k,w.a,w.b)/SB[c].rev : 0), mean = vals.reduce((a,x)=>a+x,0)/4; if(Math.max(...vals) < .0005 && !natOf('ALL',k,w.a,w.b)) return;
      mt += `<tr><td>${t(DB.natLab[k][0],DB.natLab[k][1])}</td>${cols.map(c => { const v = SB[c].rev ? natOf(c,k,w.a,w.b)/SB[c].rev : 0; const hv = c==='ALL' ? '' : heat(-(v-mean),0.06); return `<td class="num ${c==='ALL'?'bd-grp':''}" ${hv}>${fp(v)}</td>`; }).join('')}</tr>`; });
    mt += `<tr class="bd-sep"><td colspan="${cols.length+1}">${t('Head-office costs are not in the branch columns; the Group column includes them.','تكاليف الإدارة العامة ليست في أعمدة الفروع؛ عمود المجموعة يشملها.')}</td></tr>`;
    h += `<div class="card" style="margin-top:14px"><h3>${t('Profitability drivers by branch','محركات الربحية حسب الفرع')}</h3><p class="card-sub">${ti('Cost structure as % of revenue; a darker red cell means that branch spends more on the item than the average branch','هيكل التكلفة كنسبة من الإيراد؛ الأحمر الأغمق يعني إنفاقًا أعلى من متوسط الفروع')}</p><div class="tbl-scroll"><table class="bd-t">${mt}</table></div></div>`;
    // cash drivers — group by year
    const yrs = [2023,2024,2025,2026], X = EXT, ix = y => X.years.indexOf(y); let gt = `<tr><th>${t('Group cash drivers, SAR','محركات النقد للمجموعة، ريال')}</th>${yrs.map(y=>`<th>${y===2026?'2026 YTD':'FY'+y}</th>`).join('')}</tr>`;
    const gv = (y,f) => { const i = ix(y); return (i>0) ? f(i) : null; };
    const g_ebitda = y => X.is_.ebitda[ix(y)], g_dar = y => gv(y,i=>-(X.bs.ar[i]-X.bs.ar[i-1])), g_dinv = y => gv(y,i=>-((X.bs.inventory[i]+X.bs.prepaid[i])-(X.bs.inventory[i-1]+X.bs.prepaid[i-1]))),
      g_dpay = y => gv(y,i=>((X.bs.trade_payables[i]+X.bs.other_creditors[i])-(X.bs.trade_payables[i-1]+X.bs.other_creditors[i-1]))), g_cfo = y => DATA.cfa && DATA.cfa.v[y] ? DATA.cfa.v[y].CFO : null;
    [['EBITDA','EBITDA',g_ebitda],['Δ Receivables (build = cash out)','التغير في الذمم (الزيادة = خروج نقد)',g_dar],['Δ Inventory & prepaid','التغير في المخزون والمدفوع مقدمًا',g_dinv],['Δ Payables & accruals','التغير في الدائنين والمستحقات',g_dpay]].forEach(r => gt += `<tr><td>${t(r[0],r[1])}</td>${yrs.map(y=>`<td class="num">${r[2](y)===null?'—':fm(r[2](y))}</td>`).join('')}</tr>`);
    gt += `<tr style="font-weight:700;border-top:2px solid var(--border)"><td>${t('Operating cash proxy (sum)','مؤشر النقد التشغيلي (المجموع)')}</td>${yrs.map(y=>{ const a = g_ebitda(y), b = g_dar(y), c = g_dinv(y), d = g_dpay(y); return `<td class="num">${b===null?'—':fm(a+b+c+d)}</td>`; }).join('')}</tr>`;
    gt += `<tr><td>${t('Cash from operations — Cash Flow statement','النقد من التشغيل — قائمة التدفقات النقدية')}</td>${yrs.map(y=>`<td class="num">${g_cfo(y)===null?'—':fm(g_cfo(y))}</td>`).join('')}</tr>`;
    gt += `<tr><td>${t('Cash conversion (CFO ÷ EBITDA)','التحويل النقدي (التشغيلي ÷ EBITDA)')}</td>${yrs.map(y=>`<td class="num">${g_cfo(y)===null||g_ebitda(y)<=0?'n/m':fp(g_cfo(y)/g_ebitda(y),0)}</td>`).join('')}</tr>`;
    h += `<div class="card" style="margin-top:14px"><h3>${t('Cash drivers — Group','محركات النقد — المجموعة')}</h3><p class="card-sub">${ti('How EBITDA turns into cash: receivable build and working capital explain the gap; the Cash Flow statement is the reference','كيف يتحول EBITDA إلى نقد: زيادة الذمم ورأس المال العامل تفسر الفجوة؛ المرجع قائمة التدفقات النقدية')}</p><div class="tbl-scroll"><table class="bd-t">${gt}</table></div></div>`;
    // branch cash drivers
    const dEnd = DB.dbDates, yeI = y => dEnd.indexOf(y+'-12-31'), lastI = dEnd.length-1, dbPair = y => { const p = yeI(y-1); if(p < 0) return null; const q = yeI(y); return [p, q >= 0 ? q : lastI]; }; let bt = `<tr><th>${t('Branch cash drivers, selected period','محركات النقد للفروع، الفترة المحددة')}</th>${cols.map(c=>`<th class="${c==='ALL'?'bd-grp':''}">${t(NAME[c][0],NAME[c][1])}</th>`).join('')}</tr>`;
    [['Cash revenue (collected at once)','إيراد نقدي (يُحصَّل فورًا)',c=>SB[c].cash],['Credit revenue (collected later)','إيراد آجل (يُحصَّل لاحقًا)',c=>SB[c].cred],['Direct payroll (cash cost)','رواتب مباشرة (تكلفة نقدية)',c=>-natOf(c,'emp',w.a,w.b)],
     ['Insurance-company expenses','مصروفات شركات التأمين',c=>-SB[c].ins],['Depreciation (non-cash, add-back)','الإهلاك (غير نقدي)',c=>SB[c].dep],['Contribution before head-office costs','المساهمة قبل مصروفات الإدارة العامة',c=>SB[c].contrib]].forEach(r => bt += `<tr><td>${t(r[0],r[1])}</td>${cols.map(c=>`<td class="num ${c==='ALL'?'bd-grp':''}">${fm(r[2](c))}</td>`).join('')}</tr>`);
    const yy = yOf(w.b), pair = dbPair(yy), ytdLab = yeI(yy) < 0;
    if(pair && ST.grain==='Y'){ bt += `<tr class="bd-sep"><td colspan="${cols.length+1}">${t('Movement in each ledger’s cash & bank accounts over the year','حركة حسابات النقد والبنوك في كل دفتر خلال السنة')}</td></tr><tr><td>${t('Net movement, '+(ytdLab?yy+' YTD (to '+dEnd[lastI]+')':'FY'+yy),'صافي الحركة، '+(ytdLab?yy+' حتى '+dEnd[lastI]:'السنة '+yy))}</td>${cols.map(c => c==='ALL' ? `<td class="num bd-grp">${fm(BR.reduce((s,k)=>s+DB.db[k].cash[pair[1]]-DB.db[k].cash[pair[0]],0))}</td>` : `<td class="num">${fm(DB.db[c].cash[pair[1]]-DB.db[c].cash[pair[0]])}</td>`).join('')}</tr>`; }
    h += `<div class="card" style="margin-top:14px"><div class="tbl-scroll"><table class="bd-t">${bt}</table></div><p class="card-sub" style="margin-top:8px">${ti('The three collection branches bank their takings in their own ledgers; Riyadh’s ledger pays suppliers, payroll and head-office costs for the whole Group, so its cash movement is negative while the Group total is close to flat. Select a year (Y-to-Y) to see the movement row.','فروع التحصيل الثلاثة تودع إيراداتها في دفاترها؛ بينما يسدد دفتر الرياض الموردين والرواتب وتكاليف الإدارة العامة للمجموعة كلها، لذلك حركته سالبة ويقارب مجموع المجموعة الصفر. اختر سنة (سنوي) لرؤية صف الحركة.')}</p></div>`;
    body.innerHTML = h;
  }

