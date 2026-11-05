
  /* ------------------------------ tab 7 · what-if (stop a branch, a department or a doctor) ------------------------------ */
  const DRV = DATA.drv, DOFF = 12;                                   // the drivers payload starts Jan 2024 = month index 12
  const SHARED = n => /Non-clinical|Branch activity|head-office/i.test(n);
  const SPEC2DEPT = {'General practitioner':'General practice','Pediatrics':"Children's clinics",'Internal Medicine':'Internal medicine','E.N.T':'ENT','Emergency':'Emergency & dressing',
    'General Surgery':'Surgery','Plastic Surgery':'Surgery','Vascular Surgery':'Surgery','Home Care':'Home care','Obstetrics & Gynecology':'Obstetrics & gynaecology','Opthalmology':'Ophthalmology',
    'Renal Dialysis':'Dialysis','Worker Examination':'Health certificates','X-Ray Department':'Radiology'};
  const WI_VAR = ['cons','extmed','insadm','ded','bankc','wdown','disp'];            // move with the activity: stop when the activity stops
  const WI_FIX = ['emp','rent','util','maint','govt','prof','fac','trav','admin','dep'];   // fixed: each one has a "keeps running" box
  const WI = {br:[], dept:[], doc:[], annual:false, retain:0, deptFixed:0, insVar:true, central:0, notice:3, eosb:0, salePct:100, bv:{},
    keepC:{emp:false,rent:true,util:true,maint:true,fac:true,admin:true,dep:true,govt:false,prof:false,trav:false},
    keepS:{emp:false,rent:false,util:false,maint:false,fac:false,admin:false,dep:false,govt:false,prof:false,trav:false}};
  const wiDept = Object.entries(DRV.dept).filter(([k,v]) => BR.includes(v[0]) && !SHARED(v[1])).map(([k,v]) => ({k, br:v[0], en:v[1], ar:v[2]||v[1]}));
  const wiDocs = (() => { const m = {}; DRV.vis.forEach(r => { if(!BR.includes(r[0]) || r[2]==='-') return; const k = r[0]+'|'+r[3]+'|'+r[2]; (m[k] = m[k] || {k, br:r[0], doc:r[3], spec:r[2], rows:[]}).rows.push(r); }); return Object.values(m); })();
  const dRange = w => { const a = Math.max(w.a,DOFF)-DOFF, b = w.b-DOFF; return b>=a ? [a,b] : null; };
  const sumR = (arr,a,b) => { let s = 0; for(let i=a;i<=b;i++) s += (arr && arr[i]) || 0; return s; };
  function deptStat(k,w){ const r = dRange(w), s = DRV.dser[k]; if(!r || !s) return {cash:0,cred:0,cost:0}; return {cash:sumR(s[0],r[0],r[1]), cred:sumR(s[1],r[0],r[1]), cost:sumR(s[2],r[0],r[1])}; }
  function docStat(d,w){ const r = dRange(w); let rev = 0, cred = 0; if(r) d.rows.forEach(x => { const v = sumR(x[5],r[0],r[1]); rev += v; if(x[1]==='Credit') cred += v; }); return {rev, cred}; }
  const insRate = (c,w) => { const s = stat(c,w.a,w.b,false); return s.cred ? s.ins/s.cred : 0; };
  const staffShare = (c,w) => { const s = stat(c,w.a,w.b,false), tot = s.cor + s.ins; return tot ? Math.max(0, natSum(c,'emp',w.a,w.b))/tot : 0; };
  function costRatio(d,w){                                              // direct cost per SAR of revenue: the doctor's department in the same branch, else the branch
    const nm = SPEC2DEPT[d.spec] || d.spec; let rev = 0, cost = 0;
    wiDept.forEach(x => { if(x.br===d.br && x.en===nm){ const s = deptStat(x.k,w); rev += s.cash+s.cred; cost += s.cost; } });
    if(rev > 0) return {r:Math.min(1.2,Math.max(0,cost/rev)), basis:'dept'};
    const s = stat(d.br,w.a,w.b,false); return {r:s.rev ? s.cor/s.rev : 0, basis:'branch'};
  }
  const lastYear = () => { const b = Math.min(LASTC, LAST_I), a = Math.max(0,b-11); return {a,b}; };
  function estBV(c){                                                    // book value of fixed assets attributed to the branch: Group fixed assets by the branch's share of depreciation
    const ei = EXT.years.length-1; let fa = null;
    for(let i = EXT.years.length-1; i >= 0; i--) if(EXT.bs.fixed_net[i]){ fa = EXT.bs.fixed_net[i]; break; }
    const lw = lastYear(); const tot = ALLC.reduce((s,x) => s + natSum(x,'dep',lw.a,lw.b), 0), mine = natSum(c,'dep',lw.a,lw.b);
    return fa && tot ? Math.round(fa*mine/tot) : 0;
  }
  const bvOf = c => (WI.bv[c]!==undefined && WI.bv[c]!==null && WI.bv[c]!=='') ? +WI.bv[c] : estBV(c);

  /* the engine: window totals for one exit type ('ces' = stop trading, 'sale' = sell the business) */
  function wiCalc(w, P, mode){
    const keep = mode==='ces' ? P.keepC : P.keepS, mon = months(w), base = stat('ALL',w.a,w.b,false), cen = stat('00',w.a,w.b,false);
    const rows = [], stBr = new Set(P.br); let lost = 0, vsv = 0, fsv = 0, isv = 0, strand = 0, notice = 0, bv = 0, ovl = {dept:[], doc:[]};
    const keptBy = {}; WI_FIX.forEach(k => keptBy[k] = 0);
    P.br.forEach(c => {
      const s = stat(c,w.a,w.b,false); const rv = s.rev + s.oth; let vs = 0, fs_ = 0, st = 0, emp = 0;
      natCodes.forEach(code => { const v = natSum(c,code,w.a,w.b); if(!v) return;
        if(WI_FIX.includes(code)){ if(code==='emp') emp = v; if(keep[code]){ st += v; keptBy[code] += v; } else fs_ += v; } else vs += v; });
      rows.push({k:'br:'+c, en:NAME[c][0], ar:NAME[c][1], kind:'br', lost:rv, saved:vs+fs_, strand:st});
      lost += rv; vsv += vs; fsv += fs_; strand += st;
      if(mode==='ces' && !keep.emp) notice += (emp/mon) * P.notice;
      bv += bvOf(c);
    });
    const dsel = new Set();
    P.dept.forEach(k => { const x = wiDept.find(z => z.k===k); if(!x) return; if(stBr.has(x.br)){ ovl.dept.push(x); return; } dsel.add(x.br+'|'+x.en);
      const d = deptStat(k,w), rv = d.cash+d.cred, sv = d.cost*(1-P.deptFixed/100), st = d.cost*P.deptFixed/100, ins = P.insVar ? d.cred*insRate(x.br,w) : 0;
      rows.push({k:'dept:'+k, en:NAME[x.br][0]+' · '+x.en, ar:NAME[x.br][1]+' · '+x.ar, kind:'dept', lost:rv, saved:sv+ins, strand:st});
      lost += rv; vsv += sv; isv += ins; strand += st; if(mode==='ces') notice += (sv/mon) * staffShare(x.br,w) * P.notice; });
    P.doc.forEach(k => { const d = wiDocs.find(z => z.k===k); if(!d) return; if(stBr.has(d.br) || dsel.has(d.br+'|'+(SPEC2DEPT[d.spec]||d.spec))){ ovl.doc.push(d); return; }
      const s = docStat(d,w), cr = costRatio(d,w), lo = s.rev*(1-P.retain/100), sv = lo*cr.r, ins = P.insVar && s.rev ? (s.cred/s.rev)*lo*insRate(d.br,w) : 0;
      rows.push({k:'doc:'+k, en:d.doc+' · '+d.spec+' · '+NAME[d.br][0], ar:d.doc+' · '+d.spec+' · '+NAME[d.br][1], kind:'doc', lost:lo, saved:sv+ins, strand:0, basis:cr.basis});
      lost += lo; vsv += sv; isv += ins; if(mode==='ces') notice += (sv/mon) * staffShare(d.br,w) * P.notice; });
    const central = P.central/100 * (cen.ga + cen.ho) * (base.rev ? lost/base.rev : 0);
    const f = P.annual ? 12/mon : 1;
    const rec = (-lost + vsv + fsv + isv + central) * f;
    const oneoff = mode==='ces' ? [['Notice period & staff termination','مهلة الإشعار وإنهاء خدمات الموظفين',-notice], ['Extra settlement / end-of-service top-up','تسوية إضافية / مكافأة نهاية الخدمة',-P.eosb], ['Write-off of the branch assets (book value)','شطب أصول الفرع (القيمة الدفترية)',-bv]]
                              : [['Sale price less book value (gain / loss)','سعر البيع ناقص القيمة الدفترية (ربح / خسارة)', bv*(P.salePct/100) - bv]];
    const one = oneoff.reduce((s,x) => s + x[2], 0);
    return {mode, f, mon, base:base.net*f, lost:-lost*f, vsv:vsv*f, fsv:fsv*f, isv:isv*f, central:central*f, rec, one, oneoff, after:base.net*f + rec, afterAll:base.net*f + rec + one, strand:strand*f, keptBy, rows, ovl, bv};
  }
  const wiHas = () => WI.br.length + WI.dept.length + WI.doc.length > 0;
  function quickStop(c,w){ const P = Object.assign({}, WI, {br:[c], dept:[], doc:[], annual:false}); const a = wiCalc(w,P,'ces'), b = wiCalc(w,P,'sale'); return {ces:a.rec, sale:b.rec, cesAll:a.afterAll-a.base, saleAll:b.afterAll-b.base}; }

  function tabWhatIf(){
    const w = W(), r0 = dRange(w); const wDocs = wiDocs.map(d => ({d, s:docStat(d,w)})).filter(x => x.s.rev > 0).sort((a,b) => b.s.rev-a.s.rev);
    const base = stat('ALL',w.a,w.b,false);
    const chipB = BR.map(c => `<button class="wi-chip ${WI.br.includes(c)?'on':''}" data-br="${c}"><i class="bd-dot" style="background:${COL[c]}"></i>${pick(NAME[c])}</button>`).join('');
    const chips = (list, kind, lab) => list.map(k => `<span class="wi-tag">${esc(lab(k))}<button data-rm="${kind}:${esc(k)}" aria-label="remove">×</button></span>`).join('');
    const dOpts = wiDept.filter(x => !WI.dept.includes(x.k)).map(x => ({x, s:deptStat(x.k,w)})).filter(o => o.s.cash+o.s.cred > 0).sort((a,b) => a.x.br.localeCompare(b.x.br) || (b.s.cash+b.s.cred)-(a.s.cash+a.s.cred));
    const dSel = `<select id="wi-dept-add"><option value="">${ti('Add a department…','أضف قسمًا…')}</option>` + BR.map(c => { const o = dOpts.filter(z => z.x.br===c); return o.length ? `<optgroup label="${esc(pick(NAME[c]))}">` + o.map(z => `<option value="${z.x.k}">${esc(ST.lang==='ar'?z.x.ar:z.x.en)} · ${fM(z.s.cash+z.s.cred)}</option>`).join('') + '</optgroup>' : ''; }).join('') + '</select>';
    const kSel = `<select id="wi-doc-add"><option value="">${ti('Add a doctor…','أضف طبيبًا…')}</option>` + BR.map(c => { const o = wDocs.filter(z => z.d.br===c && !WI.doc.includes(z.d.k)); return o.length ? `<optgroup label="${esc(pick(NAME[c]))}">` + o.map(z => `<option value="${esc(z.d.k)}">${esc(z.d.doc)} · ${esc(z.d.spec)} · ${fM(z.s.rev)}</option>`).join('') + '</optgroup>' : ''; }).join('') + '</select>';
    const sel = `<div class="card"><h3>${t('What to stop','ماذا نوقف')}</h3><p class="card-sub">${ti('Pick any one, or all three together. A department inside a stopped branch, or a doctor inside a stopped department, is counted once.','اختر أي واحد أو الثلاثة معًا. القسم داخل فرع موقوف أو الطبيب داخل قسم موقوف يُحسب مرة واحدة.')}</p>
      <div class="wi-row"><span class="wi-lab">${ti('Branches','الفروع')}</span><div class="wi-chips">${chipB}</div></div>
      <div class="wi-row"><span class="wi-lab">${ti('Departments','الأقسام')}</span><div class="wi-chips">${dSel}${chips(WI.dept,'dept',k => { const x = wiDept.find(z => z.k===k); return x ? pick(NAME[x.br])+' · '+(ST.lang==='ar'?x.ar:x.en) : k; })}</div></div>
      <div class="wi-row"><span class="wi-lab">${ti('Doctors','الأطباء')}</span><div class="wi-chips">${kSel}${chips(WI.doc,'doc',k => { const d = wiDocs.find(z => z.k===k); return d ? d.doc+' · '+d.spec+' · '+pick(NAME[d.br]) : k; })}</div></div>
      ${wiHas() ? `<div class="wi-row"><span class="wi-lab"></span><button class="wi-link" id="wi-clear">${ti('Clear selection','مسح الاختيار')}</button></div>` : ''}
      ${r0 && w.a>=DOFF ? '' : `<div class="note" style="margin-top:8px">${ti('Departments and doctors are available from Jan 2024. The selected window starts earlier, so only the months from Jan 2024 are counted for them.','الأقسام والأطباء متاحون من يناير 2024. الفترة المحددة تبدأ قبل ذلك، لذا تُحسب لهم الأشهر من يناير 2024 فقط.')}</div>`}</div>`;
    if(!wiHas()){ body.innerHTML = sel + `<div class="note" style="margin-top:14px">${t('Choose a branch, a department or a doctor above to see what stopping it would do to Group net income, as a cessation of trading and as a sale. The period, branch and compare filters at the top set the window.','اختر فرعًا أو قسمًا أو طبيبًا أعلاه لترى أثر إيقافه على صافي ربح المجموعة، كتوقف عن العمل وكبيع. فلاتر الفترة في الأعلى تحدد النافذة.')}</div>`; wireWI(); return; }
    const A = wiCalc(w,WI,'ces'), B = wiCalc(w,WI,'sale'), scope = WI.br;
    // assumptions
    const fixRows = WI_FIX.map(k => { const v = scope.reduce((s,c) => s + natSum(c,k,w.a,w.b), 0) * A.f; const lab = DB.natLab[k] || [k,k];
      return `<tr><td>${ti(lab[0],lab[1])}</td><td class="num">${fm(v)}</td><td class="num"><input type="checkbox" data-keep="C:${k}" ${WI.keepC[k]?'checked':''}></td><td class="num"><input type="checkbox" data-keep="S:${k}" ${WI.keepS[k]?'checked':''}></td></tr>`; }).join('');
    const varV = scope.reduce((s,c) => s + WI_VAR.reduce((q,k) => q + natSum(c,k,w.a,w.b), 0), 0) * A.f;
    const num = (k,lab,val,step,suf='') => `<label class="wi-in"><span>${lab}</span><input type="number" data-p="${k}" value="${val}" step="${step}">${suf}</label>`;
    const bvIn = WI.br.map(c => num('bv:'+c, ti('Assets book value','القيمة الدفترية للأصول')+' · '+pick(NAME[c]), bvOf(c), 100000, ' SAR')).join('');
    const ass = `<div class="card" style="margin-top:14px"><h3>${t('What keeps running','ما الذي يستمر')}</h3><p class="card-sub">${ti('Tick a cost to keep it after the stop. The defaults are planning assumptions — edit them to match your contracts. Costs that move with activity always stop.','علّم على أي مصروف لإبقائه بعد الإيقاف. القيم الافتراضية افتراضات للتخطيط — عدّلها حسب عقودك. المصروفات المرتبطة بالنشاط تتوقف دائمًا.')}</p>
      <div class="grid grid-2"><div>${WI.br.length ? `<div class="tbl-scroll"><table class="bd-t"><tr><th>${t('Fixed cost of the stopped branches','تكلفة ثابتة للفروع الموقوفة')}</th><th class="num">${ti(P_en(A.f),P_ar(A.f))}</th><th class="num">${t('Keeps running · stop trading','تستمر · توقف')}</th><th class="num">${t('Keeps running · sale','تستمر · بيع')}</th></tr>${fixRows}
        <tr class="bd-tot"><td>${ti('Moves with activity (always stops)','يتحرك مع النشاط (يتوقف دائمًا)')}</td><td class="num">${fm(varV)}</td><td></td><td></td></tr></table></div>` : `<div class="note">${ti('Fixed-cost choices apply when a whole branch is selected. A stopped department or doctor releases its own direct cost; the branch rent, utilities and shared staff stay.','خيارات التكاليف الثابتة تنطبق عند اختيار فرع كامل. القسم أو الطبيب الموقوف يحرر تكلفته المباشرة فقط، أما إيجار الفرع والمرافق والموظفون المشتركون فتبقى.')}</div>`}</div>
        <div class="wi-form">
          ${num('notice', ti('Notice period (months of staff cost)','مهلة الإشعار (أشهر من تكلفة الموظفين)'), WI.notice, 1)}
          ${num('eosb', ti('Extra settlement (SAR, one-off)','تسوية إضافية (ريال، مرة واحدة)'), WI.eosb, 50000)}
          ${num('salePct', ti('Sale price as % of book value','سعر البيع كنسبة من القيمة الدفترية'), WI.salePct, 5, '%')}
          ${bvIn}
          ${num('deptFixed', ti('Share of a department’s direct cost that keeps running','نسبة تكلفة القسم المباشرة التي تستمر'), WI.deptFixed, 5, '%')}
          ${num('retain', ti('Doctor’s revenue kept by other doctors of the same specialty','إيراد الطبيب الذي يحتفظ به أطباء آخرون بنفس التخصص'), WI.retain, 5, '%')}
          ${num('central', ti('Central cost saved (% of the stopped revenue’s share)','وفر تكاليف مركزية (% من حصة الإيراد الموقوف)'), WI.central, 5, '%')}
          <label class="ti-chk"><input type="checkbox" data-p="insVar" ${WI.insVar?'checked':''}> ${ti('Insurance-company charges fall with credit revenue','مصروفات شركات التأمين تنخفض مع الإيراد الآجل')}</label>
          <label class="ti-chk"><input type="checkbox" data-p="annual" ${WI.annual?'checked':''}> ${ti('Show as a 12-month run-rate','عرض كمعدل سنوي (12 شهرًا)')}</label>
        </div></div></div>`;
    // results
    const pct = (x,b) => b ? x/Math.abs(b) : null, cls = x => x>=0 ? 'bd-up' : 'bd-dn';
    const L = [['Group net income today','صافي ربح المجموعة حاليًا','base',1],['Revenue lost','الإيراد المفقود','lost',0],['Variable costs saved','تكاليف متغيرة موفّرة','vsv',0],['Fixed costs removed (not ticked)','تكاليف ثابتة أُزيلت (غير معلّمة)','fsv',0],['Insurance charges saved','مصروفات تأمين موفّرة','isv',0],['Central costs saved','تكاليف مركزية موفّرة','central',0]];
    let tb = `<tr><th>SAR · ${ti(P_en(A.f),P_ar(A.f))}</th><th class="num">${t('Stop trading','التوقف عن العمل')}</th><th class="num">${t('Sale','البيع')}</th></tr>`;
    L.forEach(l => tb += `<tr style="${l[3]?'font-weight:700':''}"><td>${ti(l[0],l[1])}</td><td class="num ${l[3]?'':cls(A[l[2]])}">${fm(A[l[2]])}</td><td class="num ${l[3]?'':cls(B[l[2]])}">${fm(B[l[2]])}</td></tr>`);
    tb += `<tr class="bd-tot"><td>${ti('Recurring effect on net income','الأثر المتكرر على صافي الدخل')}</td><td class="num ${cls(A.rec)}">${fm(A.rec)}<span class="bd-d ${cls(A.rec)}">${fs(pct(A.rec,A.base))}</span></td><td class="num ${cls(B.rec)}">${fm(B.rec)}<span class="bd-d ${cls(B.rec)}">${fs(pct(B.rec,B.base))}</span></td></tr>
      <tr style="font-weight:700"><td>${ti('Net income after the stop (recurring)','صافي الدخل بعد الإيقاف (المتكرر)')}</td><td class="num">${fm(A.after)}</td><td class="num">${fm(B.after)}</td></tr>
      <tr class="bd-sep"><td colspan="3">${t('One-off items (not annualised)','بنود لمرة واحدة (غير سنوية)')}</td></tr>`;
    A.oneoff.forEach(a => tb += `<tr><td>${ti(a[0],a[1])}</td><td class="num ${cls(a[2])}">${fm(a[2])}</td><td class="num"></td></tr>`);
    B.oneoff.forEach(b => tb += `<tr><td>${ti(b[0],b[1])}</td><td class="num"></td><td class="num ${cls(b[2])}">${fm(b[2])}</td></tr>`);
    tb += `<tr style="font-weight:700"><td>${ti('Net income, first year incl. one-offs','صافي الدخل في السنة الأولى شاملًا البنود لمرة واحدة')}</td><td class="num">${fm(A.afterAll)}</td><td class="num">${fm(B.afterAll)}</td></tr>
      <tr><td>${ti('Fixed costs still running with no revenue behind them','تكاليف ثابتة مستمرة دون إيراد يقابلها')}</td><td class="num bd-dn">${fm(-A.strand)}</td><td class="num bd-dn">${fm(-B.strand)}</td></tr>`;
    const wf = X => [{label:ti('Today','حاليًا'),v:X.base,total:true},{label:ti('Revenue','الإيراد'),v:X.lost},{label:ti('Variable','متغير'),v:X.vsv+X.isv},{label:ti('Fixed','ثابت'),v:X.fsv},{label:ti('Central','مركزي'),v:X.central},{label:ti('After','بعد'),v:X.after,total:true}];
    const kp = (lab,val,sub,neg) => kpiTile(lab, val, sub, neg);
    const tiles = `<div class="grid grid-4" style="margin-bottom:14px">` +
      kp(ti('Net income today','صافي الدخل حاليًا'), 'SAR '+fM(A.base), ti(P_en(A.f),P_ar(A.f)), A.base<0) +
      kp(ti('After stopping trading','بعد التوقف عن العمل'), 'SAR '+fM(A.after), fdp(A.rec,pct(A.rec,A.base)) + ' · ' + ti('first year','السنة الأولى') + ' ' + fd(A.afterAll-A.base), A.after<0) +
      kp(ti('After a sale','بعد البيع'), 'SAR '+fM(B.after), fdp(B.rec,pct(B.rec,B.base)) + ' · ' + ti('first year','السنة الأولى') + ' ' + fd(B.afterAll-B.base), B.after<0) +
      kp(ti('Selection','المختار'), `${WI.br.length+WI.dept.length+WI.doc.length}`, `${WI.br.length} ${ti('branch','فرع')} · ${WI.dept.length} ${ti('dept','قسم')} · ${WI.doc.length} ${ti('doctor','طبيب')}`) + `</div>`;
    let rt = `<tr><th>${t('Stopped item','البند الموقوف')}</th><th class="num">${t('Revenue lost','إيراد مفقود')}</th><th class="num">${t('Direct cost saved','تكلفة مباشرة موفّرة')}</th><th class="num">${t('Effect on net income','الأثر على صافي الدخل')}</th><th class="num">${t('Fixed cost left running','تكلفة ثابتة مستمرة')}</th></tr>`;
    A.rows.forEach(x => rt += `<tr><td>${t(x.en,x.ar)}${x.basis==='branch'?`<span class="bd-d">${ti('cost ratio: branch average','نسبة التكلفة: متوسط الفرع')}</span>`:''}</td><td class="num">${fm(-x.lost*A.f)}</td><td class="num">${fm(x.saved*A.f)}</td><td class="num ${cls(x.saved-x.lost)}">${fm((x.saved-x.lost)*A.f)}</td><td class="num">${fm(x.strand*A.f)}</td></tr>`);
    const ov = A.ovl.dept.length + A.ovl.doc.length ? `<div class="note" style="margin-top:10px">${ti(`Counted once: ${A.ovl.dept.length} department(s) and ${A.ovl.doc.length} doctor(s) already sit inside something you selected.`,`حُسبت مرة واحدة: ${A.ovl.dept.length} قسم و${A.ovl.doc.length} طبيب داخل ما اخترته بالفعل.`)}</div>` : '';
    const how = `<div class="note" style="margin-top:14px">${t(`<b>How this is worked out.</b> Window: the period selected at the top (${months(w)} months), on posted + open vouchers${(typeof NORM!=='undefined' && NORM.on) ? ', with the Normalization switch ON' : ''}. A branch’s revenue and each cost nature come from its cost centre; a department’s revenue and direct cost from its clinic cost centres; a doctor’s revenue from invoices, with the cost estimated at the department’s direct-cost ratio in the same branch (branch average when the department has no data). Head-office and central costs stay unless you enter a saving. A sale assumes the buyer takes the staff and the lease, so no notice, no rent and no depreciation stay with you; stopping trading assumes the ticked costs keep running and the branch assets are written off at book value. Asset book value is an estimate (Group fixed assets by the branch’s share of depreciation) — replace it with your own figure. This is a planning view, not a forecast of cash.`,
      `<b>طريقة الحساب.</b> النافذة: الفترة المحددة في الأعلى (${months(w)} شهرًا) على القيود المرحّلة والمفتوحة${(typeof NORM!=='undefined' && NORM.on) ? ' مع تفعيل زر الاستبعاد' : ''}. إيراد الفرع وكل طبيعة مصروف من مركز تكلفته؛ إيراد القسم وتكلفته المباشرة من مراكز تكلفة العيادات؛ إيراد الطبيب من الفواتير مع تقدير التكلفة بنسبة التكلفة المباشرة للقسم في نفس الفرع (متوسط الفرع عند غياب بيانات القسم). تكاليف الإدارة العامة والمركزية تبقى ما لم تُدخل وفرًا. البيع يفترض أن المشتري يتولى الموظفين والإيجار فلا مهلة إشعار ولا إيجار ولا إهلاك عليك؛ أما التوقف عن العمل فيفترض استمرار المصروفات المعلَّمة وشطب أصول الفرع بقيمتها الدفترية. القيمة الدفترية تقدير (الأصول الثابتة للمجموعة بحصة الفرع من الإهلاك) — استبدلها برقمك. هذه صورة تخطيطية وليست توقعًا للنقد.`)}</div>`;
    body.innerHTML = sel + tiles + ass + `<div class="card" style="margin-top:14px"><h3>${t('Effect on Group net income','الأثر على صافي ربح المجموعة')}</h3><div class="tbl-scroll"><table class="bd-t">${tb}</table></div></div>
      <div class="grid grid-2" style="margin-top:14px"><div class="card"><h3>${t('Stop trading','التوقف عن العمل')}</h3>${waterfall(wf(A))}</div><div class="card"><h3>${t('Sale','البيع')}</h3>${waterfall(wf(B))}</div></div>
      <div class="card" style="margin-top:14px"><h3>${t('By selected item (stop trading)','حسب كل بند مختار (التوقف عن العمل)')}</h3><div class="tbl-scroll"><table class="bd-t">${rt}</table></div>${ov}</div>` + how;
    wireWI();
  }
  const P_en = f => f===1 ? 'selected period' : '12-month run-rate', P_ar = f => f===1 ? 'الفترة المحددة' : 'معدل 12 شهرًا';
  function wireWI(){
    body.querySelectorAll('[data-br]').forEach(b => b.onclick = () => { const c = b.dataset.br, i = WI.br.indexOf(c); if(i>=0) WI.br.splice(i,1); else WI.br.push(c); render(); });
    const ad = (id,kind) => { const s = body.querySelector(id); if(s) s.onchange = () => { if(s.value && !WI[kind].includes(s.value)) WI[kind].push(s.value); render(); }; };
    ad('#wi-dept-add','dept'); ad('#wi-doc-add','doc');
    body.querySelectorAll('[data-rm]').forEach(b => b.onclick = () => { const [kind,k] = b.dataset.rm.split(/:(.*)/s); WI[kind] = WI[kind].filter(x => x !== k); render(); });
    const cl = body.querySelector('#wi-clear'); if(cl) cl.onclick = () => { WI.br = []; WI.dept = []; WI.doc = []; render(); };
    body.querySelectorAll('[data-keep]').forEach(i => i.onchange = () => { const [m,k] = i.dataset.keep.split(':'); (m==='C' ? WI.keepC : WI.keepS)[k] = i.checked; render(); });
    body.querySelectorAll('[data-p]').forEach(i => i.onchange = () => { const k = i.dataset.p;
      if(i.type==='checkbox') WI[k] = i.checked; else if(k.startsWith('bv:')) WI.bv[k.slice(3)] = i.value; else WI[k] = Math.max(0, +i.value || 0); render(); });
  }
