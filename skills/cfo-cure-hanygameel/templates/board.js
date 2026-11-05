
/* ======================================================================
   تقرير مجلس الإدارة  ·  Board of Directors Report (Arabic, RTL)
   ====================================================================== */
const DEPT_AR = {
  'General Doctor':'الطب العام',
  'Department of Internal Medicine':'الباطنة',
  'Department of Dialysis':'الغسيل الكلوي',
  'Gynecology and Obstetrics Clinic':'النساء والولادة',
  'Dental Section':'الأسنان',
  'Child Clinics':'عيادات الأطفال',
  'Orthopedic Department':'العظام',
  'Urinary Tract':'المسالك البولية',
  'E.N.T':'الأنف والأذن والحنجرة',
  'Department of Ophthalmology':'العيون',
  'Dermatology Clinics':'الجلدية',
  'Home Care Department':'الرعاية المنزلية',
  'Laboratory Management':'إدارة المختبر',
  'Radiology Management':'إدارة الأشعة',
  'Emergency Department':'الطوارئ',
  'Neurology Clinic':'عيادة المخ والأعصاب'
};
const arNum = n => (n === null || n === undefined || isNaN(n)) ? '—'
  : (n < 0 ? '(' + Math.round(Math.abs(n)).toLocaleString('en-US') + ')'
           : Math.round(n).toLocaleString('en-US'));
const arPct = (n,d=1) => (n === null || n === undefined || isNaN(n)) ? '—' : (n*100).toFixed(d) + '%';
/* spoken money: "35.6 مليون ريال" */
function say(n){
  const a = Math.abs(n), s = n < 0 ? 'سالب ' : '';
  if(a >= 1e6) return s + (a/1e6).toFixed(1) + ' مليون ريال';
  if(a >= 1e3) return s + (a/1e3).toFixed(0) + ' ألف ريال';
  return s + Math.round(a) + ' ريال';
}
function chgCell(cur, prv, betterUp = true){
  if(prv === null || prv === undefined || prv === 0 || !isFinite(prv))
    return ['<span class="fl">—</span>','<span class="fl">—</span>'];
  const d = cur - prv, p = d/Math.abs(prv), good = betterUp ? d >= 0 : d <= 0;
  const cls = Math.abs(p) < 0.0005 ? 'fl' : (good ? 'up' : 'dn');
  return [`<span class="${cls}">${d >= 0 ? '+' : '−'}${arNum(Math.abs(d))}</span>`,
          `<span class="${cls}">${d >= 0 ? '+' : '−'}${(Math.abs(p)*100).toFixed(1)}%</span>`];
}

(function boardReport(){
  const sec = document.getElementById('sec-cfo-board');
  if(!sec) return;
  const wrap = el('div','br'); sec.appendChild(wrap);

  function render(){
    const a = TI.a, b = TI.b, cc = TI.cc;
    const cur = pnl(a, b, cc);
    const cw  = TI.cmp ? cmpWindow() : null;
    const prv = cw ? pnl(cw.a, cw.b, cc) : null;
    const pos = position(b, cc);
    const posPrev = cw ? position(cw.b, cc) : null;
    const months = b - a + 1;

    /* ---------- header ---------- */
    let h = `<div class="br-head">
      <div class="t">تقرير مجلس الإدارة</div>
      <div class="s">
        مجموعة الفيحاء الطبية &mdash; الرياض &middot; بريدة 1 &middot; بريدة 2 &middot; رفحاء<br>
        <b>الفترة:</b> ${periodLabel('ar')} (${months} ${months === 1 ? 'شهر' : months === 2 ? 'شهران' : months <= 10 ? 'أشهر' : 'شهراً'})
        &nbsp;&middot;&nbsp; <b>النطاق:</b> ${ccLabel('ar')}<br>
        ${cw ? `<b>المقارنة:</b> نفس الفترة من العام السابق (${mLabAR(cw.a)}${cw.a === cw.b ? '' : ' – ' + mLabAR(cw.b)})`
             : `<b>المقارنة:</b> غير متاحة لهذه الفترة (البيانات تبدأ من يناير 2023)`}<br>
        <b>المصدر:</b> دفتر الأستاذ العام (EXSYS) &mdash; القيود المُرحَّلة فقط، باستثناء قيود الإقفال &middot;
        مركز التكلفة هو بُعد الفرع &middot; جميع المبالغ بالريال السعودي
      </div>
    </div>`;

    /* ---------- KPI cards ---------- */
    const kpi = (k, v, d) => `<div class="br-kpi"><div class="k">${k}</div><div class="v">${v}</div><div class="d">${d}</div></div>`;
    const dl = (c,p,up=true) => p === null ? '<span class="fl">—</span>' : chgCell(c,p,up).join(' &nbsp;');
    h += `<h3>المؤشرات الرئيسية</h3><div class="br-kpis">
      ${kpi('إجمالي الإيرادات', arNum(cur.revenue), dl(cur.revenue, prv && prv.revenue))}
      ${kpi('إجمالي المصروفات', arNum(cur.expense), dl(cur.expense, prv && prv.expense, false))}
      ${kpi('صافي النتيجة', arNum(cur.net), dl(cur.net, prv && prv.net))}
      ${kpi('هامش صافي الربح', arPct(cur.margin), prv && prv.margin !== null
          ? `<span class="${cur.margin >= prv.margin ? 'up':'dn'}">${cur.margin >= prv.margin ? '+':'−'}${(Math.abs(cur.margin-prv.margin)*100).toFixed(1)} نقطة</span>` : '<span class="fl">—</span>')}
      ${kpi('الأرباح قبل الإهلاك (EBITDA)', arNum(cur.ebitda), dl(cur.ebitda, prv && prv.ebitda))}
      ${kpi('النقد في نهاية الفترة', arNum(pos.cash), posPrev ? dl(pos.cash, posPrev.cash) : '<span class="fl">—</span>')}
    </div>`;

    /* ---------- company P&L ---------- */
    const L = c => TIM.labels[c] ? TIM.labels[c][1] : c;
    const revRows = TIM.rev.map(c => ({ lab:L(c), cur:-flow([c],a,b,cc), prv: cw ? -flow([c],cw.a,cw.b,cc) : null, up:true }));
    const expRows = TIM.exp.concat(TIM.revContra)
      .map(c => ({ lab:L(c), cur:flow([c],a,b,cc), prv: cw ? flow([c],cw.a,cw.b,cc) : null, up:false }))
      .filter(r => Math.abs(r.cur) > 0.5 || (r.prv && Math.abs(r.prv) > 0.5))
      .sort((x,y) => y.cur - x.cur);
    const row = r => { const [d,p] = chgCell(r.cur, r.prv, r.up);
      return `<tr><td>${r.lab}</td><td class="n">${arNum(r.cur)}</td><td class="n">${r.prv === null ? '—' : arNum(r.prv)}</td><td class="n">${d}</td><td class="n">${p}</td></tr>`; };
    const totRow = (lab, c, p, up=true) => { const [d,pc] = chgCell(c,p,up);
      return `<tr class="tot"><td>${lab}</td><td class="n">${arNum(c)}</td><td class="n">${p === null ? '—' : arNum(p)}</td><td class="n">${d}</td><td class="n">${pc}</td></tr>`; };
    h += `<h3>أولاً: أداء الشركة (قائمة الدخل)</h3>
      <p class="br-lead">الإيرادات والمصروفات للفترة المختارة، مقارنةً بنفس الفترة من العام السابق. كل بند يعود مباشرةً إلى حسابات دفتر الأستاذ العام.</p>
      <table class="br-t"><thead><tr><th>البند</th><th>الفترة الحالية</th><th>نفس الفترة سابقاً</th><th>التغير</th><th>%</th></tr></thead><tbody>
      ${revRows.map(row).join('')}
      ${totRow('إجمالي الإيرادات', cur.revenue, prv && prv.revenue)}
      ${expRows.map(row).join('')}
      ${totRow('إجمالي المصروفات', cur.expense, prv && prv.expense, false)}
      ${totRow('صافي النتيجة', cur.net, prv && prv.net)}
      </tbody></table>`;

    /* ---------- branch level ---------- */
    h += `<h3>ثانياً: الأداء على مستوى الفروع (مراكز التكلفة)</h3>
      <p class="br-lead">كل فرع يُقاس ببادئة مركز التكلفة الخاصة به وليس بقاعدة البيانات التي سُجِّل فيها القيد &mdash; فمصروفات الرياض تحمل مراكز تكلفة الفروع الأربعة جميعها. البادئة 00 هي الإدارة العامة (مصروفات مشتركة على مستوى المجموعة).</p>
      <table class="br-t"><thead><tr><th>مركز التكلفة</th><th>الإيرادات</th><th>المصروفات</th><th>صافي النتيجة</th><th>الهامش</th><th>التغير في الصافي</th></tr></thead><tbody>`;
    TIM.ccs.forEach(k => {
      const c = pnl(a,b,k), p = cw ? pnl(cw.a,cw.b,k) : null;
      const [d] = chgCell(c.net, p && p.net);
      h += `<tr><td>${k} &mdash; ${TIM.ccName[k][1]}</td><td class="n">${arNum(c.revenue)}</td><td class="n">${arNum(c.expense)}</td><td class="n">${arNum(c.net)}</td><td class="n">${c.revenue > 0 ? arPct(c.margin) : '—'}</td><td class="n">${d}</td></tr>`;
    });
    const g = pnl(a,b,'ALL'), gp = cw ? pnl(cw.a,cw.b,'ALL') : null;
    const [gd] = chgCell(g.net, gp && gp.net);
    h += `<tr class="tot"><td>المجموعة</td><td class="n">${arNum(g.revenue)}</td><td class="n">${arNum(g.expense)}</td><td class="n">${arNum(g.net)}</td><td class="n">${arPct(g.margin)}</td><td class="n">${gd}</td></tr></tbody></table>
      <div class="br-note"><b>كيف تُقرأ:</b> الإدارة العامة (00) تحمل المصروفات المركزية للمجموعة كاملةً &mdash; الرواتب المركزية، الرسوم، القروض، الإهلاك &mdash; بينما تُسجَّل الإيرادات في مراكز تكلفة الفروع. لذلك يظهر مركز 00 بصافٍ سالب دائماً، وهذا لا يعني خسارة تشغيلية في الإدارة العامة بل أنها مركز تكلفة وليست مركز ربح. الحكم على ربحية أي فرع يتطلب توزيع مصروفات الإدارة العامة عليه، وهذا التوزيع غير مُعتمد حالياً في النظام.</div>`;

    /* ---------- department level ---------- */
    const d25 = DATA.dept.departments_2025, d26 = DATA.dept.departments_2026ytd;
    const by25 = Object.fromEntries(d25.map(r => [r.dept_no, r]));
    h += `<h3>ثالثاً: الأداء على مستوى الأقسام (فرع الرياض)</h3>
      <p class="br-lead">التفصيل حسب القسم متاح على مستوى السنة المالية فقط (2025 مقابل 2026 حتى تاريخه)، ولا يتأثر بمُرشِّح الفترة أعلاه. التفصيل على مستوى الطبيب/القسم موجود فعلياً لفرع الرياض فقط؛ الفروع الثلاثة الأخرى تظهر كمبلغ إداري إجمالي واحد.</p>
      <table class="br-t"><thead><tr><th>القسم</th><th>إيراد 2026 حتى تاريخه</th><th>إيراد 2025 (سنة كاملة)</th><th>نقدي 2026</th><th>آجل (تأمين) 2026</th><th>نسبة الآجل</th></tr></thead><tbody>`;
    d26.forEach(r => {
      const base = by25[r.dept_no];
      const share = r.revenue ? r.credit / r.revenue : null;
      h += `<tr><td>${DEPT_AR[r.name] || r.name}</td><td class="n">${arNum(r.revenue)}</td><td class="n">${base ? arNum(base.revenue) : '—'}</td><td class="n">${arNum(r.cash)}</td><td class="n">${arNum(r.credit)}</td><td class="n">${share === null ? '—' : arPct(share,0)}</td></tr>`;
    });
    const t26 = d26.reduce((s,r) => s + r.revenue, 0), t25 = d25.reduce((s,r) => s + r.revenue, 0);
    const c26 = d26.reduce((s,r) => s + r.credit, 0);
    h += `<tr class="tot"><td>إجمالي الأقسام (الرياض)</td><td class="n">${arNum(t26)}</td><td class="n">${arNum(t25)}</td><td class="n">${arNum(d26.reduce((s,r)=>s+r.cash,0))}</td><td class="n">${arNum(c26)}</td><td class="n">${arPct(c26/t26,0)}</td></tr></tbody></table>`;

    /* ---------- liquidity & financial position ---------- */
    const pr = (lab, c, p, up=true) => { const [d,pc] = chgCell(c,p,up);
      return `<tr><td>${lab}</td><td class="n">${arNum(c)}</td><td class="n">${p === null ? '—' : arNum(p)}</td><td class="n">${d}</td><td class="n">${pc}</td></tr>`; };
    h += `<h3>رابعاً: السيولة والمركز المالي</h3>
      <p class="br-lead">الأرصدة كما هي في نهاية الفترة المختارة (${mLabAR(b)})، مقارنةً بنفس التاريخ من العام السابق. الأرصدة تراكمية من افتتاحية 31 ديسمبر 2022 المطابقة للقوائم المالية المعتمدة.</p>
      <table class="br-t"><thead><tr><th>البند</th><th>نهاية الفترة</th><th>نفس التاريخ سابقاً</th><th>التغير</th><th>%</th></tr></thead><tbody>
      ${pr('النقد وما في حكمه', pos.cash, posPrev && posPrev.cash)}
      ${pr('ذمم مدينة (عملاء وتأمين)', pos.ar, posPrev && posPrev.ar, false)}
      ${pr('أرصدة أطراف ذات علاقة (مدينة)', pos.related, posPrev && posPrev.related, false)}
      ${pr('المخزون', pos.inv, posPrev && posPrev.inv)}
      ${pr('إجمالي الأصول المتداولة', pos.currentAssets, posPrev && posPrev.currentAssets)}
      ${pr('إجمالي الالتزامات المتداولة', pos.currentLiab, posPrev && posPrev.currentLiab, false)}
      ${pr('رأس المال العامل', pos.workingCap, posPrev && posPrev.workingCap)}
      ${pr('القروض طويلة الأجل', pos.debt, posPrev && posPrev.debt, false)}
      ${pr('صافي الدين (القروض ناقص النقد)', pos.netDebt, posPrev && posPrev.netDebt, false)}
      ${pr('مكافأة نهاية الخدمة (مخصص)', pos.eosb, posPrev && posPrev.eosb, false)}
      ${pr('الأصول الثابتة والمشاريع تحت التنفيذ', pos.fixed, posPrev && posPrev.fixed)}
      <tr class="tot"><td>نسبة التداول</td><td class="n">${fmtX(pos.currentRatio)}</td><td class="n">${posPrev ? fmtX(posPrev.currentRatio) : '—'}</td><td class="n" colspan="2">${posPrev && posPrev.currentRatio ? `<span class="${pos.currentRatio >= posPrev.currentRatio ? 'up':'dn'}">${pos.currentRatio >= posPrev.currentRatio ? '+':'−'}${Math.abs(pos.currentRatio-posPrev.currentRatio).toFixed(2)}x</span>` : '—'}</td></tr>
      <tr class="tot"><td>النسبة السريعة</td><td class="n">${fmtX(pos.quickRatio)}</td><td class="n">${posPrev ? fmtX(posPrev.quickRatio) : '—'}</td><td class="n" colspan="2">${posPrev && posPrev.quickRatio ? `<span class="${pos.quickRatio >= posPrev.quickRatio ? 'up':'dn'}">${pos.quickRatio >= posPrev.quickRatio ? '+':'−'}${Math.abs(pos.quickRatio-posPrev.quickRatio).toFixed(2)}x</span>` : '—'}</td></tr>
      </tbody></table>
      <div class="br-flag"><b>تنبيه محاسبي مهم بخصوص النقد:</b> الأرقام أعلاه على أساس القيود المُرحَّلة (Posted) فقط. المراجعة السابقة لحساب البنك 1224005 أظهرت رصيد قيود غير مُرحَّلة (Unposted) يقارب <b>8.1 مليون ريال</b> يخفض النقد الفعلي عن الرقم المُرحَّل. كما أن أرصدة النقد لا يمكن تفصيلها بشكل ذي معنى حسب مركز التكلفة لأن الحسابات البنكية مشتركة بين الفروع &mdash; الرقم الصحيح الوحيد هو إجمالي المجموعة.</div>`;

    /* ---------- narrative ---------- */
    const bullets = [];
    if(prv){
      const rd = cur.revenue - prv.revenue, rp = rd/Math.abs(prv.revenue);
      bullets.push(`الإيرادات ${rd >= 0 ? 'ارتفعت' : 'انخفضت'} بمقدار <b>${arNum(Math.abs(rd))} ريال</b> (${arPct(Math.abs(rp))}) مقارنةً بنفس الفترة من العام السابق، لتصل إلى <b>${arNum(cur.revenue)} ريال</b>.`);
      const ed = cur.expense - prv.expense, ep = ed/Math.abs(prv.expense);
      bullets.push(`المصروفات ${ed >= 0 ? 'ارتفعت' : 'انخفضت'} بمقدار <b>${arNum(Math.abs(ed))} ريال</b> (${arPct(Math.abs(ep))})، ${Math.abs(ep) > Math.abs(rp) ? 'أي بوتيرة أسرع من الإيرادات &mdash; وهذا ما يضغط على الهامش.' : 'أي بوتيرة أبطأ من الإيرادات &mdash; وهذا ما يدعم الهامش.'}`);
      bullets.push(`صافي النتيجة <b>${arNum(cur.net)} ريال</b> مقابل <b>${arNum(prv.net)} ريال</b>، بتغير قدره <b>${arNum(cur.net - prv.net)} ريال</b>.`);
    } else {
      bullets.push(`الإيرادات <b>${arNum(cur.revenue)} ريال</b> والمصروفات <b>${arNum(cur.expense)} ريال</b> وصافي النتيجة <b>${arNum(cur.net)} ريال</b>. لا تتوفر فترة مقارنة سابقة.`);
    }
    const salShare = cur.revenue ? cur.salaries/cur.revenue : null;
    bullets.push(`الرواتب والمزايا <b>${arNum(cur.salaries)} ريال</b>، أي <b>${arPct(salShare)}</b> من الإيرادات &mdash; وهي أكبر بند تكلفة منفرد في المجموعة.`);
    const credShare = cur.revenue ? cur.credRev/(cur.cashRev + cur.credRev) : null;
    bullets.push(`الإيرادات الآجلة (التأمين) تمثل <b>${arPct(credShare)}</b> من إيرادات المرضى، والباقي تحصيل نقدي مباشر &mdash; وهذا هو المحرك الأساسي لحركة الذمم المدينة والسيولة.`);
    bullets.push(`نسبة التداول <b>${fmtX(pos.currentRatio)}</b> والنسبة السريعة <b>${fmtX(pos.quickRatio)}</b>، ورأس المال العامل <b>${arNum(pos.workingCap)} ريال</b>${pos.workingCap < 0 ? ' &mdash; أي أن الالتزامات المتداولة تتجاوز الأصول المتداولة، وهو مؤشر ضغط على السيولة قصيرة الأجل.' : '.'}`);
    bullets.push(`صافي الدين <b>${arNum(pos.netDebt)} ريال</b>${pos.netDebt < 0 ? ' (مركز نقدي صافٍ).' : '.'}`);
    h += `<h3>خامساً: أبرز الملاحظات</h3><ul class="br-bul">${bullets.map(x => '<li>'+x+'</li>').join('')}</ul>`;

    /* ---------- audio ---------- */
    h += `<h3>سادساً: التقرير الصوتي</h3>
      <p class="br-lead">ملخص منطوق للتقرير يُولَّد من نفس أرقام الفترة المختارة أعلاه. اختر اللهجة ثم اضغط «تشغيل». الصوت يُنتَج من محرك النطق العربي المثبَّت على جهازك، فإن لم يوجد صوت عربي على الجهاز فالنص مكتوب بالكامل أدناه وجاهز للتسجيل.</p>
      <div class="au">
        <div class="au-tabs">
          <button class="au-tab on" data-d="nj">اللهجة النجدية</button>
          <button class="au-tab" data-d="eg">اللهجة المصرية</button>
        </div>
        <div class="au-row">
          <button class="au-btn" id="au-play">▶ تشغيل</button>
          <button class="au-btn sec" id="au-stop">■ إيقاف</button>
          <button class="au-btn sec" id="au-copy">نسخ النص</button>
          <span class="au-st" id="au-st"></span>
        </div>
        <div class="au-scr" id="au-scr"></div>
      </div>`;

    wrap.innerHTML = h;
    wireAudio(cur, prv, pos, posPrev, cw);
  }

  /* ---------- spoken scripts ---------- */
  function scripts(cur, prv, pos, cw){
    const per = periodLabel('ar');
    const scope = ccLabel('ar');
    const dir = cur.net >= 0 ? 'ربح' : 'خسارة';
    const rUp = prv ? (cur.revenue >= prv.revenue) : null;
    const nUp = prv ? (cur.net >= prv.net) : null;
    const salShare = cur.revenue ? arPct(cur.salaries/cur.revenue) : '—';
    const credShare = (cur.cashRev + cur.credRev) ? arPct(cur.credRev/(cur.cashRev + cur.credRev)) : '—';

    const nj = [
`السلام عليكم ورحمة الله. هذا تقرير مجلس الإدارة لمجموعة الفيحاء الطبية عن فترة ${per}، والنطاق ${scope}.`,
`نبدأ بالإيرادات. إجمالي الإيرادات في هالفترة ${say(cur.revenue)}. ${prv ? (rUp ? `وهذا أعلى من نفس الفترة من السنة اللي قبل بمقدار ${say(cur.revenue - prv.revenue)}.` : `وهذا أقل من نفس الفترة من السنة اللي قبل بمقدار ${say(prv.revenue - cur.revenue)}.`) : 'وما عندنا فترة مقارنة سابقة.'}`,
`أما المصروفات فوصلت ${say(cur.expense)}. ${prv ? (cur.expense >= prv.expense ? `يعني زادت ${say(cur.expense - prv.expense)} عن السنة اللي قبل.` : `يعني نزلت ${say(prv.expense - cur.expense)} عن السنة اللي قبل.`) : ''}`,
`والنتيجة النهائية: صافي ${dir} قدره ${say(Math.abs(cur.net))}، بهامش ${arPct(cur.margin)} من الإيراد. ${prv ? (nUp ? 'الوضع تحسّن عن السنة اللي قبل.' : 'الوضع تراجع عن السنة اللي قبل، ويحتاج وقفة.') : ''}`,
`أكبر بند تكلفة عندنا هو الرواتب والمزايا، ${say(cur.salaries)}، يعني ${salShare} من الإيراد. هذا البند هو اللي يحكم الهامش، وأي قرار على التكلفة لازم يبدأ من هنا.`,
`على مستوى الفروع، الإدارة العامة تحمل المصروفات المركزية كلها للمجموعة، والإيرادات تتسجّل عند الفروع. عشان كذا مركز الإدارة العامة يطلع بصافي سالب دايم، وهذا شي طبيعي محاسبياً مو خسارة تشغيلية.`,
`أما الأقسام، فالتفصيل موجود لفرع الرياض. الباطنة والطب العام والنساء والولادة هي الأعلى إيراداً، والطوارئ والأشعة والمختبر أقسام خدمية تحمل تكلفة أكثر من إيرادها المباشر، وهذا متوقع لأنها تخدم بقية العيادات.`,
`ننتقل للسيولة. النقد في نهاية الفترة ${say(pos.cash)}، ونسبة التداول ${fmtX(pos.currentRatio)}، والنسبة السريعة ${fmtX(pos.quickRatio)}، ورأس المال العامل ${say(pos.workingCap)}.`,
`وترى فيه ملاحظة مهمة لازم تنتبهون لها: هالأرقام على أساس القيود المرحّلة فقط. عندنا قيود غير مرحّلة تقارب ثمانية مليون ومية ألف ريال، وهي تخفض النقد الفعلي. يعني الرقم اللي قدامكم أعلى من الواقع بهالمقدار تقريباً.`,
`ونسبة الإيراد الآجل من التأمين ${credShare} من إيرادات المرضى. كل ما زادت هالنسبة، كل ما طالت دورة التحصيل وضغطت على السيولة، حتى لو الربح على الورق زين.`,
`صافي الدين ${say(pos.netDebt)}. وهذا كل اللي عندي، وشكراً لكم.`
    ].join('\n\n');

    const eg = [
`السلام عليكم ورحمة الله. ده تقرير مجلس الإدارة لمجموعة الفيحاء الطبية عن فترة ${per}، والنطاق ${scope}.`,
`نبتدي بالإيرادات. إجمالي الإيرادات في الفترة دي ${say(cur.revenue)}. ${prv ? (rUp ? `يعني أعلى من نفس الفترة السنة اللي فاتت بـ ${say(cur.revenue - prv.revenue)}.` : `يعني أقل من نفس الفترة السنة اللي فاتت بـ ${say(prv.revenue - cur.revenue)}.`) : 'ومفيش فترة مقارنة سابقة.'}`,
`أما المصروفات فوصلت ${say(cur.expense)}. ${prv ? (cur.expense >= prv.expense ? `يعني زادت ${say(cur.expense - prv.expense)} عن السنة اللي فاتت.` : `يعني قلّت ${say(prv.expense - cur.expense)} عن السنة اللي فاتت.`) : ''}`,
`والنتيجة في الآخر: صافي ${dir} قيمته ${say(Math.abs(cur.net))}، بهامش ${arPct(cur.margin)} من الإيراد. ${prv ? (nUp ? 'يعني الوضع اتحسّن عن السنة اللي فاتت.' : 'يعني الوضع اتراجع عن السنة اللي فاتت، ومحتاج وقفة.') : ''}`,
`أكبر بند تكلفة عندنا هو المرتبات والمزايا، ${say(cur.salaries)}، يعني ${salShare} من الإيراد. البند ده هو اللي بيتحكم في الهامش، وأي قرار على التكلفة لازم يبدأ من هنا.`,
`على مستوى الفروع، الإدارة العامة شايلة المصروفات المركزية كلها للمجموعة، والإيرادات بتتسجّل عند الفروع. عشان كده مركز الإدارة العامة بيطلع بصافي سالب على طول، وده طبيعي محاسبياً ومش خسارة تشغيلية.`,
`أما الأقسام، فالتفصيل موجود لفرع الرياض. الباطنة والطب العام والنسا والتوليد هي الأعلى إيراداً، والطوارئ والأشعة والمعمل أقسام خدمية شايلة تكلفة أكتر من إيرادها المباشر، وده متوقع لأنها بتخدم باقي العيادات.`,
`ننتقل للسيولة. الكاش في آخر الفترة ${say(pos.cash)}، ونسبة التداول ${fmtX(pos.currentRatio)}، والنسبة السريعة ${fmtX(pos.quickRatio)}، ورأس المال العامل ${say(pos.workingCap)}.`,
`وفيه ملاحظة مهمة لازم تاخدوا بالكوا منها: الأرقام دي على أساس القيود المرحّلة بس. عندنا قيود لسه مش مرحّلة حوالي تمن مليون ومية ألف جنيه... أقصد ريال، وهي بتقلّل الكاش الفعلي. يعني الرقم اللي قدامكوا أعلى من الواقع بالمقدار ده تقريباً.`,
`ونسبة الإيراد الآجل من التأمين ${credShare} من إيرادات المرضى. كل ما النسبة دي تزيد، كل ما دورة التحصيل تطوّل وتضغط على السيولة، حتى لو الربح على الورق كويس.`,
`صافي المديونية ${say(pos.netDebt)}. وده كل اللي عندي، وشكراً ليكوا.`
    ].join('\n\n');

    return {nj, eg};
  }

  /* ---------- audio wiring ---------- */
  let utter = null;
  function wireAudio(cur, prv, pos){
    const S = scripts(cur, prv, pos);
    let dialect = 'nj';
    const scr = wrap.querySelector('#au-scr');
    const st  = wrap.querySelector('#au-st');
    const show = () => { scr.textContent = S[dialect]; };
    show();

    const voices = () => (window.speechSynthesis ? window.speechSynthesis.getVoices() : []);
    function pickVoice(){
      const v = voices();
      const want = dialect === 'nj' ? ['ar-SA','ar_SA'] : ['ar-EG','ar_EG'];
      return v.find(x => want.some(w => (x.lang||'').replace('_','-').toLowerCase().startsWith(w.toLowerCase())))
          || v.find(x => (x.lang||'').toLowerCase().startsWith('ar'))
          || null;
    }
    function status(){
      if(!window.speechSynthesis){ st.textContent = 'متصفحك لا يدعم النطق الصوتي — النص متاح للنسخ.'; return; }
      const v = pickVoice();
      st.textContent = v ? `الصوت المستخدم: ${v.name} (${v.lang})`
        : 'لا يوجد صوت عربي مثبَّت على هذا الجهاز — النص جاهز أدناه للنسخ أو التسجيل.';
    }
    wrap.querySelectorAll('.au-tab').forEach(t => t.addEventListener('click', () => {
      dialect = t.dataset.d;
      wrap.querySelectorAll('.au-tab').forEach(x => x.classList.toggle('on', x === t));
      if(window.speechSynthesis) window.speechSynthesis.cancel();
      show(); status();
    }));
    wrap.querySelector('#au-play').addEventListener('click', () => {
      if(!window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      utter = new SpeechSynthesisUtterance(S[dialect]);
      const v = pickVoice(); if(v) utter.voice = v;
      utter.lang = v ? v.lang : (dialect === 'nj' ? 'ar-SA' : 'ar-EG');
      utter.rate = 0.95; utter.pitch = 1;
      utter.onend = () => { st.textContent = 'انتهى التشغيل.'; };
      utter.onerror = () => { st.textContent = 'تعذّر التشغيل على هذا الجهاز — النص متاح أدناه.'; };
      window.speechSynthesis.speak(utter);
      st.textContent = 'جارٍ التشغيل…';
    });
    wrap.querySelector('#au-stop').addEventListener('click', () => {
      if(window.speechSynthesis) window.speechSynthesis.cancel();
      st.textContent = 'تم الإيقاف.';
    });
    wrap.querySelector('#au-copy').addEventListener('click', () => {
      const t = S[dialect];
      if(navigator.clipboard) navigator.clipboard.writeText(t).then(() => st.textContent = 'تم نسخ النص.');
      else st.textContent = 'النسخ غير متاح — حدّد النص يدوياً.';
    });
    if(window.speechSynthesis){
      status();
      window.speechSynthesis.onvoiceschanged = status;
    } else status();
  }

  TI.on(render);
  render();
})();

renderStrips();
activate('cfo-exec');
