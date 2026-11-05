
  /* ------------------------------ tab 1 · income statement ------------------------------ */
  function timeCols(){
    const out = [], g = ST.grain;
    if(g === 'Y' && yOf(ST.a) === yOf(ST.b)){          // like-for-like: the selected months of every year
      const ma = mOf(ST.a), mb = mOf(ST.b), full = ma===0 && mb===11, rng = ma===mb;
      for(let y = 2023; y <= yOf(ST.b); y++){
        const a = MO.indexOf(y+'-'+String(ma+1).padStart(2,'0')), b = Math.min(MO.indexOf(y+'-'+String(mb+1).padStart(2,'0')), LAST_I);
        if(a < 0 || b < 0) continue;
        out.push({a,b,en:full?'FY'+y:(rng?ENM[ma]:ENM[ma]+'–'+ENM[mb])+' '+y, ar:full?'السنة '+y:(rng?ARM[ma]:ARM[ma]+'–'+ARM[mb])+' '+y});
      }
    } else if(g === 'Y'){
      for(let y = 2023; y <= yOf(ST.b); y++){
        const a = MO.indexOf(y+'-01'); let b = (y < yOf(ST.b)) ? Math.min(MO.indexOf(y+'-12'), LAST_I) : ST.b;
        if(y < yOf(ST.b) && yOf(LASTC) === y && b > LASTC) b = LASTC;
        const part = mOf(b) < 11;
        out.push({a,b,en:part?y+' YTD':'FY'+y, ar:part?y+' حتى تاريخه':'السنة '+y});
      }
    } else if(g === 'Q'){
      const qa = Math.floor(ST.b/3)*3;
      for(let k = 7; k >= 0; k--){ const a = qa-3*k; if(a < 0) continue; const b = Math.min(a+2, LAST_I), q = Math.floor(mOf(a)/3)+1;
        out.push({a,b,en:'Q'+q+' '+yOf(a), ar:'ر'+q+' '+yOf(a)}); }
    } else {
      const from = g==='R' ? Math.max(ST.a, ST.b-23) : Math.max(0, ST.b-11);
      for(let i = from; i <= ST.b; i++) out.push({a:i,b:i,en:labEN(i),ar:labAR(i)});
    }
    return out.map(c => ({...c, cc:ST.cc}));
  }
  function branchCols(){
    const w = W(); const cs = [];
    const list = ST.cc==='ALL' ? BR.concat(ST.alloc?[]:['00']) : (ST.cc==='00' && ST.alloc ? [] : [ST.cc]);
    list.forEach(c => cs.push({cc:c, a:w.a, b:w.b, en:NAME[c][0], ar:NAME[c][1], color:COL[c]}));
    cs.push({cc:'ALL', a:w.a, b:w.b, en:'Group', ar:'المجموعة', color:COL.ALL, grp:true});
    return cs;
  }
  const ratioRows = [
    ['Gross margin %','هامش مجمل الربح',s=>s.gm/s.rev],['Operating margin %','هامش الربح التشغيلي',s=>s.op/s.rev],
    ['EBITDA margin %','هامش EBITDA',s=>s.ebitda/s.rev],['Net margin %','هامش صافي الدخل',s=>s.net/s.rev],
    ['Credit share of revenue %','نسبة الإيراد الآجل',s=>s.cred/s.rev],['Cost of revenue % of revenue','تكلفة الإيراد % من الإيراد',s=>s.cor/s.rev]];
  function isTable(cols){
    const mode = ST.mode, pv = ST.cmp && mode==='amt';
    const S = cols.map(c => { const p = winPrev(c); return {c, s:stat(c.cc,c.a,c.b,ST.alloc), p:p?stat(c.cc,p.a,p.b,ST.alloc):null}; });
    let h = `<tr><th>SAR</th>${S.map(x=>`<th class="${x.c.grp?'bd-grp':''}">${x.c.color?`<i class="bd-dot" style="background:${x.c.color}"></i>`:''}${t(x.c.en,x.c.ar)}</th>`).join('')}</tr>`;
    ISR.forEach(r => {
      const st = r[4]===2 ? 'font-weight:700;border-top:2px solid var(--border)' : r[4]===1 ? 'font-weight:600' : '';
      h += `<tr style="${st}"><td>${t(r[1],r[2])}</td>` + S.map(x => {
        const v = r[3](x.s), pvv = x.p ? r[3](x.p) : null; let txt = '';
        if(mode==='amt'){ txt = fm(v); if(pv && x.p){ const d = delta(v,pvv); txt += `<span class="bd-d ${favCls(v-pvv)}">${fdp(v-pvv,d)}</span>`; } }
        else if(mode==='pct') txt = x.s.rev ? fp(v/x.s.rev) : '—';
        else { const d = x.p ? delta(v,pvv) : null; txt = d===null ? '—' : `<span class="${favCls(v-pvv)}">${fs(d)}</span><span class="bd-d ${favCls(v-pvv)}">${fd(v-pvv)}</span>`; }
        return `<td class="num ${x.c.grp?'bd-grp':''}${v<0&&mode==='amt'?' neg':''}">${txt}</td>`; }).join('') + '</tr>';
    });
    h += `<tr class="bd-sep"><td colspan="${S.length+1}">${t('Ratios','النسب')}</td></tr>`;
    ratioRows.forEach((r,ri) => { h += `<tr><td>${t(r[0],r[1])}</td>${S.map(x=>{ const cur = x.s.rev?r[2](x.s):null, pr = x.p&&x.p.rev?r[2](x.p):null; let dd = '';
        if(pv && cur!==null && pr!==null){ const pp = (cur-pr)*100, good = ri===5 ? -pp : ri===4 ? 0 : pp; dd = `<span class="bd-d ${ri===4?'':favCls(good)}">${(pp>=0?'+':'−')+Math.abs(pp).toFixed(1)} pp</span>`; }
        return `<td class="num ${x.c.grp?'bd-grp':''}">${cur!==null?fp(cur):'—'}${dd}</td>`; }).join('')}</tr>`; });
    return `<div class="tbl-scroll"><table class="bd-t">${h}</table></div>`;
  }
  function tieNote(){
    const rows = []; let bad = false;
    [[2023,11],[2024,11],[2025,11]].forEach(([y,m]) => { const a = MO.indexOf(y+'-01'), b = MO.indexOf(y+'-12'); const g = stat('ALL',a,b,false), e = EXT.is_.net_income[EXT.years.indexOf(y)];
      rows.push(`FY${y}: ${Math.abs(g.net-e)<=15 ? '✓' : fm(g.net-e)}`); if(Math.abs(g.net-e)>15) bad = true; });
    const a26 = MO.indexOf('2026-01'), g26 = stat('ALL',a26,LAST_I,false), e26 = EXT.is_.net_income[EXT.years.indexOf(2026)], d26 = g26.net-e26;
    const en = `<b>Tie-out to the Statements.</b> Group net income built from the four branches plus head office equals the Income Statement (by nature) above to within SAR 15 (monthly rounding) for FY2023–FY2025 (${rows.join(' · ')}). 2026 through the latest ledger date (Jan–${ENM[mOf(LAST_I)]}, as at ${DB.asOf}) ${Math.abs(d26)<=15?'also ties (difference SAR '+fm(d26)+')':'differs by SAR '+fm(d26)+' because the statements were struck on '+EXT.asOf}. All figures include posted and open vouchers (every status except cancelled), exactly as the Statements do; the open-voucher share is shown in the memo below. Revenue is cash (41x) plus credit (42x) excluding 4200027 insurance drug sales; the net of 4200027 sits in other revenue of the head-office column. G&amp;A and head-office costs are posted on the head-office cost centre — switch on <i>Allocate head-office costs</i> to see fully-loaded branch profit. Branch history starts Jan 2023 (cost-centre tagging).`;
    const ar = `<b>مطابقة مع القوائم.</b> صافي دخل المجموعة المبني من الفروع الأربعة والإدارة العامة يساوي قائمة الدخل (حسب الطبيعة) أعلاه بفارق أقل من 15 ريال (تقريب شهري) للسنوات 2023–2025 (${rows.join(' · ')}). 2026 حتى آخر تاريخ في الدفتر (يناير–${ARM[mOf(LAST_I)]}، بتاريخ ${DB.asOf}) ${Math.abs(d26)<=15?'يطابق أيضًا (الفرق '+fm(d26)+' ريال)':'يختلف بمقدار '+fm(d26)+' ريال لأن القوائم أُعدت بتاريخ '+EXT.asOf}. كل الأرقام تشمل القيود المرحّلة والمفتوحة (كل الحالات عدا الملغاة) تمامًا كما في القوائم، ونسبة القيود المفتوحة موضحة في الجدول التالي. الإيراد = نقدي (41x) + آجل (42x) باستثناء مبيعات أدوية التأمين 4200027 التي يظهر صافيها ضمن الإيرادات الأخرى في عمود الإدارة العامة. المصروفات العمومية والإدارة العامة مسجلة على مركز تكلفة الإدارة العامة — فعّل خيار <i>توزيع تكاليف الإدارة العامة</i> لرؤية ربح الفرع بعد التحميل الكامل. تاريخ الفروع يبدأ يناير 2023 (وسم مراكز التكلفة).`;
    return `<div class="note">${ST.lang==='ar'?ar:en}${ST.lang==='both'?`<div class="bd-ar" dir="rtl">${ar}</div>`:''}</div>`;
  }
  function openMemo(){
    const cols = branchCols(), O = DB.open || {}; if(!Object.keys(O).length) return '';
    const S = cols.map(c => { const keys = c.cc==='ALL' ? Object.keys(O) : (O[c.cc]?[c.cc]:[]); const sm = k => keys.reduce((s,cc)=>{ for(let i=c.a;i<=c.b;i++) s += O[cc][k][i]||0; return s; },0);
      const st = stat(c.cc,c.a,c.b,false); return {c, n:sm('n'), rev:sm('rev'), exp:sm('exp'), st}; });
    const row = (en,ar,f,cls='') => `<tr class="${cls}"><td>${t(en,ar)}</td>${S.map(x=>`<td class="num ${x.c.grp?'bd-grp':''}">${f(x)}</td>`).join('')}</tr>`;
    const costs = x => x.st.cor+x.st.ins+x.st.ga+x.st.ho;
    const h = `<tr><th>SAR</th>${S.map(x=>`<th class="${x.c.grp?'bd-grp':''}">${x.c.color?`<i class="bd-dot" style="background:${x.c.color}"></i>`:''}${t(x.c.en,x.c.ar)}</th>`).join('')}</tr>` +
      row('Open vouchers (count)','عدد القيود المفتوحة',x=>Math.round(x.n).toLocaleString()) +
      row('Revenue in open vouchers','إيراد في قيود مفتوحة',x=>fm(x.rev)) +
      row('Expenses in open vouchers','مصروفات في قيود مفتوحة',x=>fm(-x.exp)) +
      row('Net effect on profit','الأثر على الربح',x=>fm(x.rev-x.exp),'bd-tot') +
      row('Open revenue % of revenue','الإيراد المفتوح % من الإيراد',x=>x.st.rev?fp(x.rev/x.st.rev,2):'—') +
      row('Open expenses % of costs','المصروفات المفتوحة % من التكاليف',x=>costs(x)?fp(x.exp/costs(x),2):'—');
    return `<div class="card" style="margin-top:14px"><h3>${t('Memo · open vouchers included above','ملحق · القيود المفتوحة المضمّنة أعلاه')}</h3><p class="card-sub">${ti('Posted + open vouchers are both in the figures (as in the Statements). Open = not yet posted; shown so you can see how much of the period still depends on them.','القيود المرحّلة والمفتوحة كلاهما ضمن الأرقام (كما في القوائم). المفتوح = لم يُرحّل بعد؛ يظهر هنا لتعرف كم تعتمد الفترة عليه.')}</p><div class="tbl-scroll"><table class="bd-t">${h}</table></div></div>`;
  }
  function tabIS(){
    const w = W(), pw = ST.cmp ? winPrev(w) : null, s = stat(ST.cc,w.a,w.b,ST.alloc), p = pw ? stat(ST.cc,pw.a,pw.b,ST.alloc) : null;
    const sub = (cur,prev) => prev===null||prev===undefined ? '' : fdp(cur-prev,delta(cur,prev))+' '+ti('vs PY','مقابل العام السابق');
    let h = `<div class="grid grid-4" style="margin-bottom:14px">` +
      kpiTile(ti('Revenue','الإيرادات'), 'SAR '+fM(s.rev), sub(s.rev,p&&p.rev)) +
      kpiTile(ti('Operating profit','الربح التشغيلي'), 'SAR '+fM(s.op), sub(s.op,p&&p.op), s.op<0) +
      kpiTile(ti('Net income','صافي الدخل'), 'SAR '+fM(s.net), sub(s.net,p&&p.net), s.net<0) +
      kpiTile(ti('Cash share of revenue','نسبة الإيراد النقدي'), fp(s.cash/s.rev), ti('credit','آجل')+' '+fp(s.cred/s.rev)) + `</div>`;
    h += `<div class="card"><div class="bd-ch"><div><h3>${t('Income Statement (by nature)','قائمة الدخل (حسب الطبيعة)')}</h3>
      <p class="card-sub">SAR · ${ST.view==='branch' ? ti('Branches side by side for the selected period','الفروع جنبًا إلى جنب للفترة المحددة') : ti('Selected branch over time','الفرع المحدد عبر الزمن')}${ST.alloc?' · '+ti('head office allocated','الإدارة العامة موزعة'):''}</p></div>
      <div class="bd-ctl"><div class="ti-seg" id="bd-view"><button data-v="branch" class="${ST.view==='branch'?'on':''}">${ti('By branch','حسب الفرع')}</button><button data-v="time" class="${ST.view==='time'?'on':''}">${ti('Over time','عبر الزمن')}</button></div>
      <div class="ti-seg" id="bd-mode"><button data-m="amt" class="${ST.mode==='amt'?'on':''}">SAR</button><button data-m="pct" class="${ST.mode==='pct'?'on':''}">${ti('% of revenue','% من الإيراد')}</button><button data-m="yoy" class="${ST.mode==='yoy'?'on':''}">${ti('YoY %','تغير %')}</button></div></div></div>
      ${isTable(ST.view==='branch' ? branchCols() : timeCols())}</div>` + openMemo() + tieNote();
    body.innerHTML = h;
    body.querySelectorAll('#bd-view button').forEach(b => b.onclick = () => { ST.view = b.dataset.v; render(); });
    body.querySelectorAll('#bd-mode button').forEach(b => b.onclick = () => { ST.mode = b.dataset.m; render(); });
  }

  /* ------------------------------ tab 2 · impact on the Group ------------------------------ */
  function narr(en,ar){ return `<p class="bd-nar">${ST.lang==='ar'?ar:en}${ST.lang==='both'?`<span class="bd-ar" dir="rtl">${ar}</span>`:''}</p>`; }
  const need12 = () => `<div class="note">${t('Impact analysis compares two windows, so it needs 12 months of history before the period. Pick 2024 or later (the ledger history starts Jan 2023).','تحليل التأثير يقارن فترتين لذلك يحتاج 12 شهرًا من السجل قبل الفترة. اختر 2024 أو أحدث (السجل يبدأ يناير 2023).')}</div>`;
  function tabImpact(){
    const w = W(), pw = winPrev(w); if(!pw){ body.innerHTML = need12(); return; }
    const C = {}, P = {}; ALLC.forEach(c => { C[c] = stat(c,w.a,w.b,false); P[c] = stat(c,pw.a,pw.b,false); });
    const G = stat('ALL',w.a,w.b,false), GP = stat('ALL',pw.a,pw.b,false);
    const dContrib = c => C[c].contrib - P[c].contrib;
    const sumB = BR.reduce((s,c)=>s+dContrib(c),0), dCentral = (G.op-GP.op) - sumB;
    const wf1 = [{label:ti('PY','العام السابق'),v:GP.op,total:true}].concat(BR.map(c=>({label:pick(NAME[c]),v:dContrib(c)})), [{label:ti('Central','المركزية'),v:dCentral}], [{label:ti('Now','الحالي'),v:G.op,total:true}]);
    const lines = [['cash','Cash rev.','نقدي',1],['cred','Credit rev.','آجل',1],['cor','Cost of rev.','تكلفة',-1],['ins','Insurance','تأمين',-1],['ga','G&A','عمومية',-1],['ho','Head office','الإدارة',-1]];
    const wf2 = [{label:ti('PY','العام السابق'),v:GP.op,total:true}].concat(lines.map(l=>({label:pick([l[1],l[2]]),v:l[3]*(G[l[0]]-GP[l[0]])})), [{label:ti('Now','الحالي'),v:G.op,total:true}]);
    // matrix of favourable changes
    const LN2 = {cash:['Cash revenue','إيراد نقدي'],cred:['Credit revenue','إيراد آجل'],cor:['Cost of revenue','تكلفة الإيراد'],ins:['Insurance expenses','مصروفات التأمين'],ga:['G&A','عمومية وإدارية'],ho:['Head office','الإدارة العامة']};
    const mrows = lines.map(l=>[l[0],LN2[l[0]][0],LN2[l[0]][1],l[3]]).concat([['oth','Other revenue','إيرادات أخرى',1],['zak','Zakat','الزكاة',-1]]);
    const cols = BR.concat(['00']); let mx = 1; mrows.forEach(l => cols.forEach(c => mx = Math.max(mx, Math.abs(l[3]*(C[c][l[0]]-P[c][l[0]])))));
    let mt = `<tr><th>${t('Favourable (+) / adverse (−) change, SAR · and % change of the line','التغير الإيجابي (+) / السلبي (−) بالريال، ونسبة التغير في البند')}</th>${cols.map(c=>`<th><i class="bd-dot" style="background:${COL[c]}"></i>${t(NAME[c][0],NAME[c][1])}</th>`).join('')}<th class="bd-grp">${t('Group','المجموعة')}</th></tr>`;
    mrows.forEach(l => { const gv = l[3]*(G[l[0]]-GP[l[0]]);
      mt += `<tr><td>${t(l[1],l[2])}</td>${cols.map(c=>{ const v = l[3]*(C[c][l[0]]-P[c][l[0]]); const pc = delta(C[c][l[0]],P[c][l[0]]); return `<td class="num" ${heat(v,mx)}>${fm(v)}<span class="bd-d ${favCls(v)}">${fs(pc)}</span></td>`; }).join('')}<td class="num bd-grp" style="font-weight:700">${fm(gv)}<span class="bd-d ${favCls(gv)}">${fs(delta(G[l[0]],GP[l[0]]))}</span></td></tr>`; });
    mt += `<tr style="font-weight:700;border-top:2px solid var(--border)"><td>${t('Change in net income','التغير في صافي الدخل')}</td>${cols.map(c=>`<td class="num">${fm(C[c].net-P[c].net)}<span class="bd-d ${favCls(C[c].net-P[c].net)}">${fs(delta(C[c].net,P[c].net))}</span></td>`).join('')}<td class="num bd-grp">${fm(G.net-GP.net)}<span class="bd-d ${favCls(G.net-GP.net)}">${fs(delta(G.net,GP.net))}</span></td></tr>`;
    // shares
    const shr = [['rev','Revenue','الإيراد'],['cash','Cash revenue','الإيراد النقدي'],['cred','Credit revenue','الإيراد الآجل'],['cor','Cost of revenue','تكلفة الإيراد'],['ins','Insurance expenses','مصروفات التأمين'],['contrib','Contribution (rev − direct − insurance)','المساهمة (إيراد − مباشر − تأمين)'],['dep','Depreciation','الإهلاك']];
    let st = `<tr><th>${t('Share of Group, selected period','حصة المجموعة للفترة المحددة')}</th>${BR.map(c=>`<th><i class="bd-dot" style="background:${COL[c]}"></i>${t(NAME[c][0],NAME[c][1])}</th>`).join('')}<th>${t('Group SAR','المجموعة ريال')}</th></tr>`;
    shr.forEach(r => st += `<tr><td>${t(r[1],r[2])}</td>${BR.map(c=>{ const sh = G[r[0]] ? C[c][r[0]]/G[r[0]] : 0; return `<td class="num"><span class="bd-bar"><i style="width:${Math.max(0,Math.min(100,sh*100))}%;background:${COL[c]}"></i></span>${fp(sh)}</td>`; }).join('')}<td class="num">${fm(G[r[0]])}</td></tr>`);
    // narrative
    const best = BR.slice().sort((a,b)=>dContrib(b)-dContrib(a)), top = best[0], low = best[best.length-1];
    const dRev = G.rev-GP.rev, gRevPct = delta(G.rev,GP.rev), dCred = G.cred-GP.cred, dCash = G.cash-GP.cash;
    let nar = narr(`Group operating profit moved from SAR ${fm(GP.op)} to SAR ${fm(G.op)} (${fm(G.op-GP.op)}). ${NAME[top][0]} added the most (${fm(dContrib(top))}); ${NAME[low][0]} ${dContrib(low)<0?'subtracted':'added least'} (${fm(dContrib(low))}). Central costs (G&A + head office) moved by ${fm(dCentral)}.`,
      `تحرك الربح التشغيلي للمجموعة من ${fm(GP.op)} إلى ${fm(G.op)} ريال (${fm(G.op-GP.op)}). ${NAME[top][1]} كان الأعلى مساهمة (${fm(dContrib(top))})، و${NAME[low][1]} ${dContrib(low)<0?'خصم':'كان الأقل إضافة'} (${fm(dContrib(low))}). أما التكاليف المركزية (عمومية وإدارة عامة) فتغيرت بمقدار ${fm(dCentral)}.`);
    nar += narr(`Revenue ${gRevPct>=0?'grew':'fell'} ${fs(gRevPct)}: cash ${fm(dCash)} and credit ${fm(dCred)}. Cost of revenue ${fm(-(G.cor-GP.cor))} and insurance expenses ${fm(-(G.ins-GP.ins))} are shown as favourable/adverse effects in the table below.`,
      `الإيراد ${gRevPct>=0?'نما':'انخفض'} ${fs(gRevPct)}: النقدي ${fm(dCash)} والآجل ${fm(dCred)}. تأثير تكلفة الإيراد ${fm(-(G.cor-GP.cor))} ومصروفات التأمين ${fm(-(G.ins-GP.ins))} موضح في الجدول أدناه (موجب = إيجابي).`);
    body.innerHTML = nar +
      `<div class="grid grid-2" style="margin-top:14px"><div class="card"><h3>${t('Operating profit bridge — by branch','جسر الربح التشغيلي — حسب الفرع')}</h3><p class="card-sub">${ti('Change in each branch’s contribution plus central costs','تغير مساهمة كل فرع + التكاليف المركزية')}</p>${waterfall(wf1)}</div>
      <div class="card"><h3>${t('Operating profit bridge — by line','جسر الربح التشغيلي — حسب البند')}</h3><p class="card-sub">${ti('Which income-statement lines moved the Group','أي بنود قائمة الدخل حرّكت المجموعة')}</p>${waterfall(wf2)}</div></div>
      <div class="card" style="margin-top:14px"><h3>${t('Every line × every branch','كل بند × كل فرع')}</h3><p class="card-sub">${ti('Where each line’s change came from; green helps profit, red hurts it','من أين جاء تغير كل بند؛ الأخضر يخدم الربح والأحمر يضره')}</p><div class="tbl-scroll"><table class="bd-t">${mt}</table></div></div>
      <div class="card" style="margin-top:14px"><h3>${t('Weight of each branch in the Group','وزن كل فرع في المجموعة')}</h3><div class="tbl-scroll"><table class="bd-t">${st}</table></div></div>`;
  }
