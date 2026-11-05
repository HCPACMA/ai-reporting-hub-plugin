/* ======================================================================
   Zakat · الزكاة — Implementing Regulation for Zakat Collection 1445H
   (years starting on or after 1 Jan 2024), computed from the four EXSYS ledgers
   ====================================================================== */
(function(){
  const Z = DATA.zak, sec = document.getElementById('sec-zakat');
  if(!Z || !sec) return;
  sec.setAttribute('dir', 'rtl'); sec.classList.add('zk-sec');
  const YS = Z.years, OY = Z.openYear;
  const st = {y: YS.filter(y => y < OY).slice(-1)[0] || YS[YS.length-1], tab: 'ret'};
  const nf = v => (v === null || v === undefined || !isFinite(v)) ? '—' : (v < -0.5 ? '−' : '') + Math.abs(Math.round(v)).toLocaleString('en-US');
  const nf2 = v => (v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
  const pc = v => (v*100).toFixed(4) + '%';
  const rateOf = o => 0.025 / 354 * o.days;                      // Art. 15(2), unrounded
  const AR_MON = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
  const asOf = new Date(Z.asOf + 'T00:00:00');
  const asOfAr = `${asOf.getDate()} ${AR_MON[asOf.getMonth()]} ${asOf.getFullYear()}`;
  const art = a => `<span class="zk-art">م ${a}</span>`;
  const yLab = y => y === OY ? `${y} (تقديري)` : String(y);

  const head = el('div', 'section-head', `
    <div class="eyebrow">Zakat · الزكاة</div>
    <h2>الزكاة الشرعية</h2>
    <p>الوعاء والزكاة المستحقة وفق اللائحة التنفيذية لجباية الزكاة 1445هـ (قرار وزير المالية رقم 1007 وتعديله رقم 1248)، التي تسري على السنوات المالية التي تبدأ في <bdi>1 يناير 2024</bdi> أو بعدها. كل رقم محسوب من قيود دفتر الأستاذ في قواعد بيانات EXSYS الأربع (القيود المرحلة والمفتوحة، دون الملغاة وقيود الإقفال) حتى <bdi>${asOfAr}</bdi>. الزكاة على مستوى المكلف ككل، فلا يطبق عليها فلتر الفرع أو مركز التكلفة.</p>`);
  sec.appendChild(head);
  const bar = el('div', 'zk-top'); sec.appendChild(bar);
  const kpi = el('div', 'zk-kpi'); sec.appendChild(kpi);
  const tabs = el('div', 'zk-tabs'); sec.appendChild(tabs);
  const body = el('div'); sec.appendChild(body);

  const TABS = [['ret','الإقرار الزكوي'],['eq','حقوق الملكية وما في حكمها'],['li','الالتزامات'],['ded','الحسميات'],['pl','صافي الربح والمصروفات'],['prov','مخصص الزكاة والاستحقاق']];
  function drawBar(){
    bar.innerHTML = `<div class="zk-seg" role="group" aria-label="العام الزكوي">${YS.map(y => `<button data-y="${y}" class="${y===st.y?'on':''}">${yLab(y)}</button>`).join('')}</div>
      <span class="zk-note" style="margin:0">العام الزكوي = السنة المالية <bdi>${st.y}</bdi> · ${Z.y[st.y].days} يوماً${st.y === OY ? ` · محسوب كأن السنة أقفلت في <bdi>${asOfAr}</bdi>` : ''}</span>`;
    bar.querySelectorAll('button').forEach(b => b.onclick = () => { st.y = +b.dataset.y; render(); });
    tabs.innerHTML = TABS.map(([k, l]) => `<button data-t="${k}" class="${k===st.tab?'on':''}">${l}</button>`).join('');
    tabs.querySelectorAll('button').forEach(b => b.onclick = () => { st.tab = b.dataset.t; render(); });
  }
  function drawKpi(o){
    const diff = o.zakat - o.booked;
    const book = o.open ? o.accrualToDate - o.booked : diff;
    kpi.innerHTML = `
      <div><span>الوعاء الزكوي</span><b>${nf(o.finalBase)}</b><em>${o.rule==='min'?'الحد الأدنى (م 27)':o.rule==='max'?'الحد الأعلى (م 28)':o.rule==='none'?'لا وعاء (م 27(3))':'الإضافات − الحسميات (م 21)'}</em></div>
      <div><span>الزكاة المستحقة${o.open?' — تقدير السنة كاملة':''}</span><b>${nf(o.zakat)}</b><em>${pc(rateOf(o))} = <bdi>2.5% ÷ 354 × ${o.days}</bdi> (م 15)</em></div>
      <div><span>${o.open?'المحمل في الدفاتر حتى الآن':'مخصص زكاة العام في الدفاتر'}</span><b>${nf(o.booked)}</b><em>${o.open?`الاستحقاق الواجب حتى ${asOfAr}: ${nf(o.accrualToDate)}`:'قيد إثبات مخصص الزكاة عن العام (3280005)'}</em></div>
      <div><span>${o.open?'قيد استحقاق مطلوب حتى اليوم':'الفرق المطلوب قيده'}</span><b>${nf(book)}</b>${Math.abs(book) < 1 ? '<span class="pill ok">مطابق</span>' : book > 0 ? '<span class="pill bad">نقص في المخصص</span>' : '<span class="pill warn">زيادة في المخصص</span>'}</div>`;
  }

  /* --------------------------------------------------------- waterfall (ltr svg) */
  function waterfall(o){
    const it = [['حقوق الملكية وما في حكمها', o.eqTot, 'tot'], ['+ الالتزامات المضافة', o.liAdd, 'up']];
    if(Math.abs(o.adjTot) >= 1) it.push(['+ غرامات غير جائزة الحسم', o.adjTot, 'up']);
    it.push(['− الحسميات', -o.dedTot, 'dn'], ['الوعاء قبل الحدود', o.base, 'tot']);
    if(Math.abs(o.finalBase - o.base) >= 1) it.push(['الوعاء المعتمد', o.finalBase, 'tot']);
    const W = 470, L = 160, R = 64, rowH = 32, H = it.length*rowH + 30;
    let run = 0; const segs = it.map(([l, v, k]) => { let a, b; if(k === 'tot'){ a = 0; b = v; run = v; } else { a = run; b = run + v; run = b; } return {l, v, k, a, b}; });
    const mx = Math.max(...segs.map(s => Math.max(s.a, s.b))), mn = Math.min(0, ...segs.map(s => Math.min(s.a, s.b)));
    const x = v => L + (v - mn) / (mx - mn) * (W - L - R);
    let s = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="من حقوق الملكية إلى الوعاء الزكوي">`;
    segs.forEach((g, i) => {
      const y = 8 + i*rowH, x0 = x(Math.min(g.a, g.b)), x1 = x(Math.max(g.a, g.b));
      s += `<text class="lbl" x="${L-10}" y="${y+15}" text-anchor="end">${g.l}</text>`;
      s += `<rect class="b-${g.k}" x="${x0}" y="${y+3}" width="${Math.max(2, x1-x0)}" height="${rowH-12}" rx="3"><title>${g.l}: ${nf(g.v)}</title></rect>`;
      s += `<text class="val" x="${x1+6}" y="${y+15}">${g.k==='tot'?'':(g.v>=0?'+':'−')}${(Math.abs(g.v)/1e6).toFixed(2)}M</text>`;
      if(i < segs.length-1){ const nx = x(g.k==='tot' ? g.b : g.b); s += `<line class="conn" x1="${nx}" x2="${nx}" y1="${y+rowH-9}" y2="${y+rowH+3}"/>`; }
    });
    s += `</svg>`;
    return `<div class="zk-wf">${s}</div><div class="zk-lg"><span><i style="background:var(--dv-tot,#7C8E89)"></i>مجموع</span><span><i style="background:var(--dv-unf,#C9502A)"></i>يزيد الوعاء</span><span><i style="background:var(--dv-fav,#1A7FA8)"></i>يخفض الوعاء</span></div>`;
  }

  /* --------------------------------------------------------- tabs */
  function tRet(o){
    const row = (l, v, a, cls='') => `<tr class="${cls}"><td>${l}</td><td class="n">${nf(v)}</td><td class="art">${a ? art(a) : ''}</td></tr>`;
    let h = '';
    if(o.open) h += `<div class="zk-warn">السنة <bdi>${OY}</bdi> مفتوحة: الأرصدة حتى <bdi>${asOfAr}</bdi> وتشمل صافي ربح الفترة؛ الوعاء هنا تقدير لما سيكون عليه لو أقفلت السنة اليوم، ويستخدم لحساب الاستحقاق الشهري لا للإقرار.</div>`;
    h += `<div class="zk-2"><div class="card"><h3>الإقرار الزكوي — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">وفق ترتيب نموذج الإقرار؛ كل بند مع مادته في اللائحة</p><div class="zk-x"><table class="zk-t"><thead><tr><th>البند</th><th class="n">المبلغ (ريال)</th><th>المادة</th></tr></thead><tbody>`;
    h += `<tr class="sub"><td colspan="3">صافي الربح</td></tr>`;
    h += row('صافي الربح الدفتري قبل الزكاة', o.np.book, '23(3)', 'ind');
    o.adj.forEach(a => h += row('يضاف: ' + a[1], a[2], a[3], 'ind'));
    h += row('صافي الربح المعدل', o.npAdj, '', 'tot');
    h += `<tr class="sub"><td colspan="3">عناصر الإضافة</td></tr>`;
    h += row('حقوق الملكية وما في حكمها', o.eqTot, '23(1), 24, 30, 36', 'ind');
    h += row(`الالتزامات (${nf(o.liRaw)}) بحدود الأصول المحسومة`, o.liAdd, '23(2), 29', 'ind');
    h += row('الفرق بين صافي الربح المعدل والدفتري', o.adjTot, '23(3)', 'ind');
    h += row('إجمالي الإضافات', o.eqTot + o.liAdd + o.adjTot, '', 'tot');
    h += `<tr class="sub"><td colspan="3">عناصر الحسم</td></tr>`;
    o.ded.forEach(d => { if(Math.abs(d[2]) >= 1) h += row(d[1], d[2], d[3], 'ind'); });
    h += row('الاستثمارات', 0, '26(1)–(3)', 'ind muted');
    h += row('إجمالي الحسميات', o.dedTot, '', 'tot');
    h += row('الوعاء الزكوي قبل الحدين', o.base, '21', 'tot');
    h += `<tr class="sub"><td colspan="3">الحد الأدنى والأعلى</td></tr>`;
    h += row('الأصول غير المحسومة + الفرق', o.undeducted + o.adjTot, '27(2)(أ)', 'ind');
    h += row('صافي الربح المعدل', o.npAdj, '27(2)(ب)', 'ind');
    h += row(`الحد الأدنى — ${o.npAdj > 0 && o.base < o.npAdj ? 'ينطبق' : 'لا ينطبق (الوعاء أكبر من صافي الربح المعدل أو لا يوجد ربح)'}`, o.minBase, '27', 'ind');
    h += row(`الحد الأعلى — ${o.rule === 'max' ? 'ينطبق' : 'لا ينطبق'}`, o.maxBase, '28', 'ind');
    h += row('الوعاء الزكوي المعتمد', o.finalBase, '', 'res');
    h += `<tr><td>نسبة الزكاة <bdi>2.5% ÷ 354 × ${o.days}</bdi></td><td class="n">${pc(rateOf(o))}</td><td class="art">${art('15')}</td></tr>`;
    h += row(o.open ? 'الزكاة التقديرية للسنة كاملة' : 'الزكاة المستحقة', o.zakat, '', 'res');
    h += row('مخصص زكاة العام في الدفاتر', o.booked, '', 'ind');
    if(o.open) h += row(`الاستحقاق الواجب حتى ${asOfAr} (${o.elapsed} يوماً)`, o.accrualToDate, '', 'ind');
    h += `</tbody></table></div></div>`;
    h += `<div class="card"><h3>من حقوق الملكية إلى الوعاء</h3><p class="card-sub">مليون ريال</p>${waterfall(o)}`;
    // three-year comparison
    h += `<h3 style="margin-top:22px">مقارنة الأعوام</h3><div class="zk-x"><table class="zk-t"><thead><tr><th>البند</th>${YS.map(y => `<th class="n">${yLab(y)}</th>`).join('')}</tr></thead><tbody>`;
    const rr = (l, f, cls='') => `<tr class="${cls}"><td>${l}</td>${YS.map(y => `<td class="n">${nf(f(Z.y[y]))}</td>`).join('')}</tr>`;
    h += rr('حقوق الملكية وما في حكمها', o => o.eqTot) + rr('الالتزامات المضافة', o => o.liAdd) + rr('الحسميات', o => -o.dedTot) + rr('الوعاء المعتمد', o => o.finalBase, 'tot');
    h += rr('صافي الربح قبل الزكاة', o => o.np.book) + rr('صافي الربح المعدل', o => o.npAdj) + rr('الزكاة المستحقة', o => o.zakat, 'tot') + rr('مخصص زكاة العام في الدفاتر', o => o.booked) + rr('الفرق', o => o.zakat - o.booked, 'tot');
    h += `</tbody></table></div><p class="zk-note">عام <bdi>${OY}</bdi> تقدير للسنة كاملة بأرصدة اليوم. عام 2024 سنة كبيسة (366 يوماً).</p></div></div>`;
    return h;
  }
  const KIND = {cap:'رأس المال', res:'الاحتياطيات', re:'الأرباح المبقاة', oci:'احتياطي إعادة القياس (الدخل الشامل الآخر)', prov:'مخصصات تعامل كحقوق ملكية', div:'أرباح تحت التوزيع', own:'جاري المالك / الشركاء'};
  function tEq(o){
    let h = `<div class="card"><h3>حقوق الملكية وما في حكمها — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">برصيد آخر المدة كما يظهر في قائمة المركز المالي (م 17)، مع البنود المعاد تصنيفها إلى حقوق الملكية (م 28(2))</p><div class="zk-x"><table class="zk-t"><thead><tr><th>البند</th><th>الحساب</th><th class="n">المبلغ</th><th>المادة</th></tr></thead><tbody>`;
    let last = null;
    o.eq.forEach(r => { if(r[0] !== last){ h += `<tr class="sub"><td colspan="4">${KIND[r[0]]}</td></tr>`; last = r[0]; } h += `<tr class="ind"><td>${r[2]}</td><td class="acc">${r[1]}</td><td class="n">${nf(r[3])}</td><td class="art">${art(r[4])}</td></tr>`; });
    h += `<tr class="tot"><td>حقوق الملكية وفق الدفاتر</td><td></td><td class="n">${nf(o.eqBook)}</td><td></td></tr>`;
    h += `<tr class="res"><td>حقوق الملكية وما في حكمها</td><td></td><td class="n">${nf(o.eqTot)}</td><td></td></tr></tbody></table></div>`;
    h += `<p class="zk-note">• المخصصات تعامل معاملة حقوق الملكية برصيد آخر المدة، عدا مكافأة نهاية الخدمة والإجازات فتعامل كالتزامات غير متداولة (م 24؛ الدليل الإرشادي مثال 13: مخصص القضايا ومخصص الزكاة من حقوق الملكية).<br>• الأرباح التي صدر قرار بتوزيعها ولم تودع في حسابات المساهمين تضاف كحقوق ملكية أياً كان الحساب المودعة فيه (م 36).<br>• جاري المالك الدائن: لا عقد تمويل ولا مدة سداد ولا عائد، فلا تتحقق شروط معاملته كالتزام، فيعامل كحقوق ملكية (م 30(2)). الأرصدة المدينة في حسابات المالك لا تحسم ولا يقاص بها (م 31، 34).<br>• مجمع مخصص الخصم الإضافي لشركات التأمين (1240008) مخصص مخفض للأصل، فلا يضاف للوعاء (الأسئلة الشائعة، س 22).</p></div>`;
    return h;
  }
  function tLi(o){
    const L = o.loan;
    let h = `<div class="zk-2"><div class="card"><h3>الالتزامات المضافة — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">تضاف الالتزامات غير المتداولة بحدود الأصول المحسومة (م 23(2)، 29(1))</p><table class="zk-t"><thead><tr><th>البند</th><th>الحساب</th><th class="n">المبلغ</th><th>المادة</th></tr></thead><tbody>`;
    o.li.forEach(r => h += `<tr><td>${r[2]}</td><td class="acc">${r[1]}</td><td class="n">${nf(r[3])}</td><td class="art">${art(r[4])}</td></tr>`);
    h += `<tr class="tot"><td>إجمالي الالتزامات</td><td></td><td class="n">${nf(o.liRaw)}</td><td></td></tr>`;
    h += `<tr><td>الأصول المحسومة (الحد الأقصى للإضافة)</td><td></td><td class="n">${nf(o.dedTot)}</td><td class="art">${art('23(2)')}</td></tr>`;
    h += `<tr class="res"><td>الالتزامات المضافة للوعاء</td><td></td><td class="n">${nf(o.liAdd)}</td><td></td></tr></tbody></table>`;
    h += `<h3 style="margin-top:20px">القرض طويل الأجل</h3><table class="zk-t"><tbody>
      <tr><td>رصيد القرض (2113002)</td><td class="n">${nf(L.gross)}</td></tr>
      <tr><td>ناقصاً: فوائد مدينة مؤجلة (1262000)</td><td class="n">${nf(-L.dint)}</td></tr>
      <tr class="tot"><td>القيمة الدفترية</td><td class="n">${nf(L.carry)}</td></tr>
      <tr><td>الجزء المتداول (أقساط الاثني عشر شهراً التالية)</td><td class="n">${nf(-L.current)}</td></tr>
      <tr class="res"><td>الجزء غير المتداول — يضاف</td><td class="n">${nf(L.noncurrent)}</td></tr></tbody></table>
      <p class="zk-note">لا يفصل دفتر الأستاذ الجزء المتداول؛ يقدر بصافي ما سدد من القرض خلال آخر سنة مقفلة (أقساط متساوية)، ولا يتجاوز القيمة الدفترية.</p></div>`;
    h += `<div class="card"><h3>اختبار الالتزامات المتداولة</h3><p class="card-sub">لا تضاف الالتزامات المتداولة إلا إذا زادت عن الأصول المتداولة، أو حسم أصل متداول (م 29(2)، 25)</p><table class="zk-t"><tbody>
      <tr><td>الأصول المتداولة</td><td class="n">${nf(o.caTot)}</td></tr>
      <tr><td>الالتزامات المتداولة (بعد إعادة تصنيف ما في حكم حقوق الملكية)</td><td class="n">${nf(o.clTot)}</td></tr>
      <tr class="res"><td>الزيادة المضافة للوعاء</td><td class="n">${nf(o.clExcess)}</td></tr>
      <tr class="muted"><td>تنسيب الالتزامات (م 25): لا يوجد أصل متداول محسوم ولا أصل غير متداول غير محسوم</td><td class="n">0</td></tr></tbody></table>
      <details><summary>تفاصيل الأصول المتداولة (${o.ca.length})</summary><table class="zk-t"><tbody>${o.ca.map(r => `<tr><td>${r[1]}</td><td class="acc">${r[0]}</td><td class="n">${nf(r[2])}</td></tr>`).join('')}</tbody></table></details>
      <details><summary>تفاصيل الالتزامات المتداولة (${o.cl.length})</summary><table class="zk-t"><tbody>${o.cl.map(r => `<tr><td>${r[1]}</td><td class="acc">${r[0]}</td><td class="n">${nf(r[2])}</td></tr>`).join('')}</tbody></table></details></div></div>`;
    return h;
  }
  function tDed(o){
    let h = `<div class="card"><h3>عناصر الحسم — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">تحسم بصافي قيمتها الظاهرة في القوائم المالية، إذا اقتنيت للاستخدام لا للبيع (م 48)</p><div class="zk-x"><table class="zk-t"><thead><tr><th>البند</th><th>الحساب</th><th class="n">المبلغ</th></tr></thead><tbody>`;
    o.ded.forEach(d => {
      h += `<tr class="sub"><td colspan="2">${d[1]} ${art(d[3])}</td><td class="n">${nf(d[2])}</td></tr>`;
      d[4].forEach(r => h += `<tr class="ind"><td>${r[1]}</td><td class="acc">${r[0]}</td><td class="n">${nf(r[2])}</td></tr>`);
    });
    h += `<tr class="res"><td>إجمالي الحسميات</td><td></td><td class="n">${nf(o.dedTot)}</td></tr>`;
    h += `<tr><td>إجمالي الأصول</td><td></td><td class="n">${nf(o.totalAssets)}</td></tr><tr><td>الأصول غير المحسومة</td><td></td><td class="n">${nf(o.undeducted)}</td></tr></tbody></table></div>`;
    h += `<p class="zk-note">• لا توجد استثمارات أو صناديق أو أصول حق استخدام أو قطع غيار غير معدة للبيع في الدفاتر. المخزون (أدوية ومستلزمات تستهلك في تقديم الخدمة) لا يحسم (م 52).<br>• الأصول غير المسجلة باسم المنشأة تحسم فقط في الحالات الواردة في المادة <bdi>48(2)</bdi> — تحقق من صكوك الأراضي والمباني.<br>• لا تحسم الذمم المدينة على الأطراف ذات العلاقة (منازلنا) ولا الأرصدة المدينة للمالك (م 31، 33، 34).</p></div>`;
    return h;
  }
  function tPl(o){
    const yi = YS.indexOf(o.y);
    const N = o.np, prov = o.eq.find(r => r[1] === '2111004');
    let h = `<div class="zk-2"><div class="card"><h3>صافي الربح — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">نقطة البداية صافي الربح قبل زكاة العام؛ الفرق بينه وبين الربح المعدل يضاف للوعاء (م 23(3))</p><table class="zk-t"><tbody>
      <tr><td>صافي الربح بعد الزكاة (الدفاتر)</td><td class="n">${nf(N.afterZakat)}</td></tr>
      <tr><td>يضاف: مخصص زكاة العام</td><td class="n">${nf(N.currentCharge)}</td></tr>
      <tr class="tot"><td>صافي الربح قبل الزكاة</td><td class="n">${nf(N.book)}</td></tr>
      ${Math.abs(N.priorAdj) >= 1 ? `<tr class="muted"><td>منه: فروق زكاة سنوات سابقة (${N.priorAdj < 0 ? 'إيراد خاضع' : 'مصروف جائز الحسم'}) — تبقى ضمن الربح</td><td class="n">${nf(-N.priorAdj)}</td></tr>` : ''}
      ${o.adj.map(a => `<tr><td>يضاف: ${a[1]} ${art(a[3])}</td><td class="n">${nf(a[2])}</td></tr>`).join('')}
      <tr class="res"><td>صافي الربح المعدل</td><td class="n">${nf(o.npAdj)}</td></tr></tbody></table>
      <p class="zk-note">• الغرامات والمخالفات الحكومية مصروف غير جائز الحسم يضاف لصافي الربح قبل الزكاة. تستخرج من قيود حسابات الرسوم الحكومية (<bdi>314xxxx</bdi>) التي يذكر بيانها مخالفة أو غرامة، بعد صافي قيود العكس وإعادة التبويب، وتستبعد أتعاب المحامين ورسوم التظلم والتعويضات.<br>• فروق الزكاة الناتجة عن الربط أو التعديل عن سنوات سابقة مصروف جائز الحسم أو إيراد خاضع، فتبقى ضمن صافي الربح${Math.abs(N.priorAdj) >= 1 ? ` (<bdi>${nf(-N.priorAdj)}</bdi> هذا العام)` : ''}.${prov ? `<br>• مخصص القضايا والمخالفات (<bdi>${nf(prov[3])}</bdi>) مضاف أيضاً ضمن حقوق الملكية وما في حكمها (م 24)، وجزء الغرامات المكوّن به المخصص يضاف كذلك عبر فرق صافي الربح (م 23(3)) — راجع هذا التداخل مع مستشار الزكاة.` : ''}</p></div>`;
    // review list
    const rv = Z.exp.filter(r => Z.review[r[0]] && Math.abs(r[4][yi]) >= 1);
    const byA = {}; rv.forEach(r => { byA[r[0]] = (byA[r[0]] || 0) + r[4][yi]; });
    h += `<div class="card"><h3>مصروفات للمراجعة</h3><p class="card-sub">شروط القبول في المواد 62–65</p><table class="zk-t"><thead><tr><th>الحساب</th><th class="n">المبلغ</th><th>الملاحظة</th></tr></thead><tbody>${Object.keys(byA).map(a => `<tr><td class="acc">${a}</td><td class="n">${nf(byA[a])}</td><td>${Z.review[a]}</td></tr>`).join('')}</tbody></table></div></div>`;
    h += `<div class="card" style="margin-top:16px"><h3>الغرامات والمخالفات — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">قيود دفتر الأستاذ (بعد صافي العكس وإعادة التبويب بين الحسابين 3140004 و3140001)</p><div class="zk-x"><table class="zk-t"><thead><tr><th>المخالفة (صافي القيود)</th><th class="n">عدد القيود</th><th class="n">المبلغ</th></tr></thead><tbody>${o.finesG.map(r => `<tr><td>${r[0]}</td><td class="n">${r[2]}</td><td class="n">${nf(r[1])}</td></tr>`).join('')}<tr class="res"><td colspan="2">صافي الغرامات غير جائزة الحسم</td><td class="n">${nf(o.adjTot)}</td></tr></tbody></table></div>
      <details><summary>كل القيود (${o.fines.length})</summary><table class="zk-t"><tbody>${o.fines.map(r => `<tr><td class="acc">${r[0]}</td><td class="acc">${r[1]}</td><td class="acc">${r[2]}</td><td>${r[4]}</td><td class="n">${nf(r[3])}</td></tr>`).join('')}</tbody></table></details>
      ${o.fineReview.length ? `<details><summary>بنود تذكر مخالفة لكنها ليست غرامة — مقبولة (${o.fineReview.length})</summary><table class="zk-t"><tbody>${o.fineReview.map(r => `<tr><td class="acc">${r[0]}</td><td class="acc">${r[1]}</td><td>${r[4]}</td><td class="n">${nf(r[3])}</td></tr>`).join('')}</tbody></table></details>` : ''}</div>`;
    // classification pivot
    const cats = {}; let tc = 0, tg = 0;
    Z.exp.forEach(r => { const v = r[4][yi]; if(Math.abs(v) < 0.5) return; const c = cats[r[3]] = cats[r[3]] || {COR:0, GA:0, rows:[]}; c[r[2]] += v; c.rows.push(r); if(r[2]==='COR') tc += v; else tg += v; });
    const order = Object.keys(cats).sort((a, b) => (cats[b].COR + cats[b].GA) - (cats[a].COR + cats[a].GA));
    h += `<div class="card" style="margin-top:16px"><h3>تبويب المصروفات لأغراض الإقرار — <bdi>${yLab(o.y)}</bdi></h3><p class="card-sub">تكلفة الإيرادات = مراكز التكلفة الطبية؛ العمومية والإدارية = الإدارة والتأمين والمركز الرئيسي. التصنيف وفق ملف تبويب المصاريف 2025م. اضغط على البند لعرض الحسابات.</p><div class="zk-x"><table class="zk-t"><thead><tr><th>التصنيف</th><th class="n">تكلفة الإيرادات</th><th class="n">عمومية وإدارية</th><th class="n">الإجمالي</th></tr></thead><tbody>`;
    order.forEach(c => {
      const x = cats[c];
      h += `<tr><td><details><summary>${c}</summary><table class="zk-t">${x.rows.sort((a,b)=>Math.abs(b[4][yi])-Math.abs(a[4][yi])).map(r => `<tr><td class="acc">${r[0]}</td><td>${r[1]}</td><td>${r[2]==='COR'?'تكلفة':'عمومية'}</td><td class="n">${nf(r[4][yi])}</td></tr>`).join('')}</table></details></td><td class="n">${nf(x.COR)}</td><td class="n">${nf(x.GA)}</td><td class="n">${nf(x.COR + x.GA)}</td></tr>`;
    });
    h += `<tr class="tot"><td>الإجمالي</td><td class="n">${nf(tc)}</td><td class="n">${nf(tg)}</td><td class="n">${nf(tc + tg)}</td></tr></tbody></table></div>
      <p class="zk-note">حسابات خارج ملف التبويب صنفت بأسمائها: الخصم الإضافي لشركات التأمين (3280004)، الخسائر الرأسمالية (3380000)، فوائد القروض (3290001)، تكلفة فائدة منافع الموظفين (3390000)، والزكاة (3280005).</p></div>`;
    return h;
  }
  function tProv(o){
    let h = `<div class="zk-2"><div class="card"><h3>حركة مخصص الزكاة (2123003)</h3><p class="card-sub">المسدد = الرصيد الافتتاحي + المحمل − الرصيد الختامي</p><table class="zk-t"><thead><tr><th>البند</th>${YS.map(y => `<th class="n">${yLab(y)}</th>`).join('')}</tr></thead><tbody>`;
    const rr = (l, f, cls='') => `<tr class="${cls}"><td>${l}</td>${YS.map(y => `<td class="n">${nf(f(Z.y[y]))}</td>`).join('')}</tr>`;
    h += rr('الرصيد الافتتاحي', o => o.provRoll.open) + rr('مخصص زكاة العام', o => o.np.currentCharge) + rr('فروق زكاة سنوات سابقة', o => o.np.priorAdj) + rr('المسدد / المستخدم', o => -o.provRoll.paid) + rr('الرصيد الختامي', o => o.provRoll.close, 'tot');
    h += rr('الزكاة المحسوبة وفق اللائحة', o => o.zakat, 'res') + rr('الفرق (محسوب − مخصص العام)', o => o.zakat - o.np.currentCharge, 'tot');
    h += `</tbody></table><p class="zk-note">فرق سنة مقفلة يعالج بقيد تسوية على مصروف الزكاة ومخصصها، ويظهر أثره في إقرار تلك السنة عند تعديله (م 103–104).</p></div>`;
    const O = Z.y[OY];
    if(O){
      const monthly = O.zakat / 12;
      h += `<div class="card"><h3>الاستحقاق الشهري لعام <bdi>${OY}</bdi></h3><p class="card-sub">الزكاة التقديرية للسنة موزعة بالأيام حتى ${asOfAr}</p><table class="zk-t"><tbody>
        <tr><td>الزكاة التقديرية للسنة كاملة</td><td class="n">${nf(O.zakat)}</td></tr>
        <tr><td>الأيام المنقضية</td><td class="n">${O.elapsed} / ${O.days}</td></tr>
        <tr class="tot"><td>الاستحقاق الواجب حتى اليوم</td><td class="n">${nf(O.accrualToDate)}</td></tr>
        <tr><td>المحمل في الدفاتر حتى اليوم</td><td class="n">${nf(O.booked)}</td></tr>
        <tr class="res"><td>قيد مطلوب: من ح/ مصروف الزكاة (3280005) إلى ح/ مخصص الزكاة (2123003)</td><td class="n">${nf(O.accrualToDate - O.booked)}</td></tr>
        <tr><td>قسط شهري مقترح لبقية السنة</td><td class="n">${nf(monthly)}</td></tr></tbody></table>
        <table class="zk-t" style="margin-top:14px"><thead><tr><th>الشهر</th><th class="n">المحمل</th><th class="n">المستحق (1/12)</th></tr></thead><tbody>${Z.openMonthlyBooked.map(([ym, v]) => `<tr><td>${AR_MON[+ym.slice(4)-1]}</td><td class="n">${nf(v)}</td><td class="n">${nf(monthly)}</td></tr>`).join('')}</tbody></table>
        <p class="zk-note">التقدير يعاد حسابه مع كل تحديث للبيانات: يتغير بتغير حقوق الملكية وصافي الربح والأصول الثابتة خلال السنة.</p></div>`;
    }
    h += `</div>`;
    return h;
  }
  function render(){
    drawBar();
    const o = Z.y[st.y]; drawKpi(o);
    body.innerHTML = ({ret:tRet, eq:tEq, li:tLi, ded:tDed, pl:tPl, prov:tProv})[st.tab](o) +
      `<p class="zk-note">المصدر: ${Z.src}. المراجع: اللائحة التنفيذية لجباية الزكاة 1445هـ، الدليل الإرشادي لجباية الزكاة، الأسئلة الشائعة. هذه الصفحة أداة احتساب ومراجعة، والإقرار المقدم هو المرجع.</p>`;
  }
  render();
})();
