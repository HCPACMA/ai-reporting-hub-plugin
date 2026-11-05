
/* ======================================================================
   COSTING  ·  service cost from the ER & Lab costing map refreshed with the
   warehouse cost at the last Stock Dispense, and profitability of every
   invoiced service against that cost
   ====================================================================== */
(function(){
  const C = DATA.cost; if(!C) return;
  const secs = ['cst-svc','cst-prof','cst-loss'].map(id => document.getElementById('sec-'+id));
  if(!secs[0]) return;
  secs.forEach(s => { if(s){ s.setAttribute('dir','rtl'); s.classList.add('cst-sec'); } });

  const B36 = s => parseInt(s, 36);
  const BRS = ['01','02','03','04'];
  const CT_LBL = {C:'نقدي', D:'نقدي بخصم', R:'آجل / تأمين'};
  const PAY = c => (c === 2 ? 'credit' : 'cash');
  const uc = s => (C.uc[s] ? C.uc[s][0] : 0);
  const ust = s => (C.uc[s] ? C.uc[s][1] : 'unmapped');
  const sname = s => (C.svn[s] ? C.svn[s][0] : s);
  const sspec = s => (C.svn[s] ? C.svn[s][1] : '0');
  const spn = n => C.spn[n] || n;
  const arDept = d => d;
  const ymLbl = ym => EN_MON[+String(ym).slice(4) - 1] + ' ' + String(ym).slice(0, 4);
  const pct = (v, d=1) => (v === null || !isFinite(v)) ? '—' : (v*100).toFixed(d) + '%';

  /* ---------------------------------------------------------------- data */
  let G = null;                        // {b, ym, sv, gr, ct, dc, sp, q, qg, val, ds, ps, iv, n}
  async function decode(){
    const bin = Uint8Array.from(atob(C.gz), ch => ch.charCodeAt(0));
    let txt;
    if(typeof DecompressionStream === 'function'){
      const ds = new DecompressionStream('gzip');
      const st = new Blob([bin]).stream().pipeThrough(ds);
      txt = await new Response(st).text();
    } else { throw new Error('no-gzip'); }
    const packed = JSON.parse(txt);
    let n = 0; const cols = {};
    for(const b of BRS){ cols[b] = packed[b].split('|').map(c => c.split(',')); n += cols[b][0].length; }
    const g = {n, b: new Uint8Array(n), ym: new Uint8Array(n), sv: new Uint16Array(n),
      gr: new Uint8Array(n), ct: new Uint8Array(n), dc: new Uint16Array(n), sp: new Uint8Array(n),
      q: new Float32Array(n), qg: new Float32Array(n), val: new Float32Array(n),
      ds: new Float32Array(n), ps: new Float32Array(n), iv: new Int32Array(n)};
    let i = 0;
    BRS.forEach((b, bi) => {
      const c = cols[b], m = c[0].length;
      for(let k = 0; k < m; k++, i++){
        g.b[i] = bi; g.ym[i] = B36(c[0][k]); g.sv[i] = B36(c[1][k]); g.gr[i] = B36(c[2][k]);
        g.ct[i] = +c[3][k]; g.dc[i] = B36(c[4][k]); g.sp[i] = B36(c[5][k]);
        g.q[i] = +c[6][k]; g.qg[i] = +c[7][k]; g.val[i] = +c[8][k];
        g.ds[i] = +c[9][k]; g.ps[i] = +c[10][k]; g.iv[i] = +c[11][k];
      }
    });
    return g;
  }

  /* ------------------------------------------------------------- filters */
  const F = {br:'ALL', grp:'ALL', pay:'ALL', ssp:'ALL', csp:'ALL', doc:'ALL', svc:'ALL',
             a:0, b:C.ym.length-1, cmp:'ok'};
  const subs = [];
  const onF = fn => subs.push(fn);
  const fire = () => subs.forEach(f => { try{ f(); }catch(e){ console.error(e); } });

  function opt(v, t, cur){ return `<option value="${esc(v)}"${String(v)===String(cur)?' selected':''}>${esc(t)}</option>`; }
  function filterBar(pfx){
    const svcOpts = C.sv.filter(s => C.uc[s]).sort((x,y)=> sname(x).localeCompare(sname(y)));
    const docOpts = C.dc.filter(d => F.br === 'ALL' || d.slice(0,2) === F.br);
    const sspecs = [...new Set(C.sv.map(sspec))].filter(x=>x&&x!=='0').sort((a,b)=>+a-+b);
    return `
    <div class="f"><label for="${pfx}-br">الفرع</label><select id="${pfx}-br">${opt('ALL','كل الفروع',F.br)}${BRS.map(b=>opt(b,C.brn[b],F.br)).join('')}</select></div>
    <div class="f"><label for="${pfx}-grp">مجموعة العملاء</label><select id="${pfx}-grp">${opt('ALL','كل المجموعات',F.grp)}${C.gr.map(g=>opt(g,C.grn[g]||g,F.grp)).join('')}</select></div>
    <div class="f"><label for="${pfx}-pay">طريقة الدفع</label><select id="${pfx}-pay">${opt('ALL','نقدي + آجل',F.pay)}${opt('cash','نقدي',F.pay)}${opt('credit','آجل / تأمين',F.pay)}</select></div>
    <div class="f"><label for="${pfx}-ssp">تخصص الخدمة</label><select id="${pfx}-ssp">${opt('ALL','كل التخصصات',F.ssp)}${sspecs.map(s=>opt(s,spn(s),F.ssp)).join('')}</select></div>
    <div class="f"><label for="${pfx}-csp">تخصص العيادة</label><select id="${pfx}-csp">${opt('ALL','كل العيادات',F.csp)}${C.sp.filter(x=>x!=='0').map(s=>opt(s,spn(s),F.csp)).join('')}</select></div>
    <div class="f"><label for="${pfx}-doc">الطبيب</label><select id="${pfx}-doc">${opt('ALL','كل الأطباء',F.doc)}${docOpts.map(d=>opt(d,(C.dcn[d.slice(0,2)]||{})[d.slice(3)]||d.slice(3),F.doc)).join('')}</select></div>
    <div class="f"><label for="${pfx}-svc">الخدمة</label><select id="${pfx}-svc">${opt('ALL','كل الخدمات المسعّرة',F.svc)}${svcOpts.map(s=>opt(s,sname(s)+' · '+s,F.svc)).join('')}</select></div>
    <div class="f"><label for="${pfx}-a">من شهر</label><select id="${pfx}-a">${C.ym.map((y,i)=>opt(i,ymLbl(y),F.a)).join('')}</select></div>
    <div class="f"><label for="${pfx}-b">إلى شهر</label><select id="${pfx}-b">${C.ym.map((y,i)=>opt(i,ymLbl(y),F.b)).join('')}</select></div>
    <div class="f"><label for="${pfx}-cmp">اكتمال التكلفة</label><select id="${pfx}-cmp">${opt('ok','الخدمات مكتملة التكلفة فقط',F.cmp)}${opt('any','تشمل الخدمات ناقصة التكلفة',F.cmp)}</select></div>`;
  }
  function wireBar(box, pfx){
    const on = (k, key, cast) => { const e = box.querySelector('#'+pfx+'-'+k); if(e) e.onchange = ev => { F[key] = cast ? cast(ev.target.value) : ev.target.value; if(key==='a'&&F.a>F.b) F.b=F.a; if(key==='b'&&F.b<F.a) F.a=F.b; if(key==='br') F.doc='ALL'; fire(); }; };
    on('br','br'); on('grp','grp'); on('pay','pay'); on('ssp','ssp'); on('csp','csp');
    on('doc','doc'); on('svc','svc'); on('a','a',Number); on('b','b',Number); on('cmp','cmp');
  }

  /* ---------------------------------------------------- aggregation core */
  // walk the grid once, bucketing by whatever key fn is given
  function scan(keyFn){
    const out = new Map(); const tot = [0,0,0,0,0,0,0];   // q,gross,disc,ps,cost,inv,qg
    if(!G) return {out, tot};
    const brI = F.br === 'ALL' ? -1 : BRS.indexOf(F.br);
    const grI = F.grp === 'ALL' ? -1 : C.gr.indexOf(F.grp);
    const cspI = F.csp === 'ALL' ? -1 : C.sp.indexOf(F.csp);
    const docI = F.doc === 'ALL' ? -1 : C.dc.indexOf(F.doc);
    const svI = F.svc === 'ALL' ? -1 : C.sv.indexOf(F.svc);
    for(let i = 0; i < G.n; i++){
      if(G.ym[i] < F.a || G.ym[i] > F.b) continue;
      if(brI >= 0 && G.b[i] !== brI) continue;
      if(grI >= 0 && G.gr[i] !== grI) continue;
      if(cspI >= 0 && G.sp[i] !== cspI) continue;
      if(docI >= 0 && G.dc[i] !== docI) continue;
      if(svI >= 0 && G.sv[i] !== svI) continue;
      if(F.pay !== 'ALL' && PAY(G.ct[i]) !== F.pay) continue;
      const code = C.sv[G.sv[i]];
      if(F.ssp !== 'ALL' && sspec(code) !== F.ssp) continue;
      const u = uc(code); if(!u) continue;                 // costed services only
      if(F.cmp === 'ok' && ust(code) !== 'ok') continue;    // drop partially-costed services
      const cost = G.q[i] * u;
      const k = keyFn(i, code);
      if(k === null) continue;
      let a = out.get(k); if(!a){ a = [0,0,0,0,0,0,0]; out.set(k, a); }
      a[0]+=G.q[i]; a[1]+=G.val[i]; a[2]+=G.ds[i]; a[3]+=G.ps[i]; a[4]+=cost; a[5]+=G.iv[i]; a[6]+=G.qg[i];
      tot[0]+=G.q[i]; tot[1]+=G.val[i]; tot[2]+=G.ds[i]; tot[3]+=G.ps[i]; tot[4]+=cost; tot[5]+=G.iv[i]; tot[6]+=G.qg[i];
    }
    return {out, tot};
  }
  const rev = a => a[1] - a[2] - a[3];
  const marg = a => rev(a) - a[4];

  /* ------------------------------------------------------------------ 1 */
  /* Service cost — the map, refreshed                                     */
  (function(){
    const sec = secs[0];
    audHead(sec, 'Costing', 'Service Cost', 'تكلفة الخدمة من خريطة المختبر والضماد',
      'كل خدمة مربوطة بأصناف المستودع التي تُصرف لتقديمها، ونسبة تحمّل الخدمة من كل صنف. تكلفة الصنف تُحدَّث من <b>آخر حركة صرف مخزني (Stock Dispense)</b> بدل العمود القديم في الملف. تكلفة تحليل المختبر = تكلفة الصنف ÷ (عدد التحاليل × نسبة التحمل)، وتكلفة خدمة الضماد = تكلفة الصنف × نسبة الاستهلاك، ثم تُجمع أصناف الخدمة كلها.');
    const bar = el('div','aud-bar'); sec.appendChild(bar);
    const kp = el('div','grid grid-4'); sec.appendChild(kp);
    const cTab = el('div','card'); cTab.style.marginTop='16px'; sec.appendChild(cTab);
    const cGap = el('div','card'); cGap.style.marginTop='16px'; sec.appendChild(cGap);
    sec.appendChild(el('div','note', `<b>المصدر.</b> ملف <code>ER &amp; Lab Costing Map.xlsx</code> (${C.map.length} سطر ربط بين ${new Set(C.map.map(m=>m[0])).size} خدمة و${new Set(C.map.map(m=>m[1])).size} صنف) + قاعدة بيانات الرياض عبر Cure MCP: <code>IM_STOCK_DISPENSING_M/D.COST_PRICE</code> عند آخر حركة صرف لكل صنف، و<code>IM_PRODUCT_MASTER</code> لأسماء الأصناف. المخازن كلها على قاعدة الرياض، فالتكلفة موحّدة على الفروع الأربعة. آخر تحديث ${esc(C.run)}.`));

    const st = {dept:'ALL', q:'', open:null, sort:'chg'};
    function render(){
      const svcs = Object.keys(C.uc);
      const rowsOf = s => C.map.filter(m => m[0] === s);
      const old = s => rowsOf(s).reduce((t,m)=> t + (m[5]||0)*0, 0);
      let list = svcs.map(s => {
        const rs = rowsOf(s);
        const u = C.uc[s];
        // old cost recomputed with the same formula but the sheet's stale item cost
        let o = 0, oOK = true;
        rs.forEach(m => {
          const share=m[3], tests=m[4], c0=m[5], stt=m[9];
          if(c0 == null){ oOK = false; return; }
          if(stt === 'no_item' || stt === 'no_dispense'){ oOK = false; return; }
          o += (m[10 /*placeholder*/] , (u[2]==='المختبر' && share >= 0.05) ? (tests ? c0/(tests*share) : (oOK=false, 0)) : c0*share);
        });
        return {s, name: sname(s), dept:u[2], unit:u[0], stt:u[1], n:u[3], bad:u[4], ld:u[5], chk:u[6]||0, old: oOK?o:null};
      });
      if(st.dept !== 'ALL') list = list.filter(x => x.dept === st.dept);
      if(st.q){ const q = st.q.toLowerCase(); list = list.filter(x => (x.name+' '+x.s).toLowerCase().includes(q)); }
      const okL = list.filter(x=>x.stt==='ok');
      const chg = okL.filter(x=>x.old!=null && x.old>0);
      const sumNew = chg.reduce((t,x)=>t+x.unit,0), sumOld = chg.reduce((t,x)=>t+x.old,0);
      bar.innerHTML = `
        <div class="f"><label for="cs-dept">القسم</label><select id="cs-dept">${opt('ALL','المختبر + الضماد',st.dept)}${opt('المختبر','المختبر',st.dept)}${opt('الضماد','الضماد / الطوارئ',st.dept)}</select></div>
        <div class="f"><label for="cs-q">بحث</label><input type="search" id="cs-q" placeholder="اسم الخدمة أو كودها" value="${esc(st.q)}"></div>
        <div class="f"><label for="cs-sort">ترتيب</label><select id="cs-sort">${opt('chg','أكبر تغير في التكلفة',st.sort)}${opt('cost','أعلى تكلفة',st.sort)}${opt('name','الاسم',st.sort)}${opt('code','الكود',st.sort)}</select></div>`;
      bar.querySelector('#cs-dept').onchange = e => { st.dept=e.target.value; render(); };
      bar.querySelector('#cs-sort').onchange = e => { st.sort=e.target.value; render(); };
      const qi = bar.querySelector('#cs-q'); qi.oninput = e => { st.q=e.target.value; render(); setTimeout(()=>{ const n=bar.querySelector('#cs-q'); n.focus(); n.setSelectionRange(n.value.length,n.value.length); },0); };

      kp.innerHTML = kpiTile('خدمات لها خريطة تكلفة', String(list.length), `${okL.length} مكتملة · ${list.filter(x=>x.stt==='partial').length} ناقصة · ${list.filter(x=>x.stt==='none').length} بدون تكلفة`)
        + kpiTile('أصناف مستودع مرتبطة', String(new Set(C.map.filter(m=>st.dept==='ALL'||C.uc[m[0]]&&C.uc[m[0]][2]===st.dept).map(m=>m[1])).size), 'من خريطة الربط')
        + kpiTile('متوسط التكلفة بعد التحديث', nfmt(okL.length? okL.reduce((t,x)=>t+x.unit,0)/okL.length : 0, 2), 'ريال للخدمة الواحدة')
        + kpiTile('أثر تحديث التكلفة', (sumOld? ((sumNew/sumOld-1)>=0?'+':'−')+Math.abs(sumNew/sumOld-1>0?(sumNew/sumOld-1)*100:(1-sumNew/sumOld)*100).toFixed(1)+'%' : '—'), `على ${chg.length} خدمة قابلة للمقارنة مع عمود Cost القديم`, sumNew>sumOld);

      const cmp = {chg:(a,b)=> Math.abs((b.old?b.unit/b.old-1:0)) - Math.abs((a.old?a.unit/a.old-1:0)),
                   cost:(a,b)=> b.unit-a.unit, name:(a,b)=> a.name.localeCompare(b.name), code:(a,b)=> a.s.localeCompare(b.s)};
      list.sort(cmp[st.sort]);
      let h = `<h3>تكلفة الخدمة بعد التحديث من المخازن</h3><p class="card-sub">اضغط على أي خدمة لعرض أصناف المستودع التي تتحمّلها · ${list.length} خدمة</p>
        <div class="aud-x"><table class="aud-t cst-t"><thead><tr><th>الكود</th><th>الخدمة</th><th>القسم</th><th class="n">أصناف</th><th class="n">التكلفة القديمة</th><th class="n">التكلفة المحدثة</th><th class="n">التغير</th><th>آخر صرف</th><th>الحالة</th></tr></thead><tbody>`;
      list.forEach(x => {
        const d = (x.old && x.old>0) ? x.unit/x.old-1 : null;
        const badge = x.stt==='ok' ? '<span class="pill ok">مكتملة</span>' : x.stt==='partial' ? '<span class="pill warn">ناقصة '+x.bad+'</span>' : '<span class="pill bad">بدون تكلفة</span>';
        h += `<tr class="cst-r" data-s="${x.s}"><td class="mono">${x.s}</td><td>${esc(x.name)}</td><td>${esc(x.dept)}</td><td class="n">${x.n}</td>
          <td class="n">${x.old!=null? nfmt(x.old,3):'—'}</td><td class="n"><b>${x.stt==='none'?'—':nfmt(x.unit,3)}</b></td>
          <td class="n ${d!=null&&d>0.02?'neg':d!=null&&d<-0.02?'pos':''}">${d!=null? ((d>=0?'+':'−')+Math.abs(d*100).toFixed(1)+'%') :'—'}</td>
          <td>${esc(x.ld||'—')}</td><td>${badge}${x.chk?' <span class="pill warn">راجع النسبة</span>':''}</td></tr>`;
        if(st.open === x.s){
          h += `<tr class="cst-d"><td colspan="9"><table class="aud-t cst-in"><thead><tr><th>الصنف</th><th>اسم الصنف</th><th class="n">نسبة التحمل</th><th class="n">عدد التحاليل</th><th class="n">تكلفة الصنف بالملف</th><th class="n">آخر صرف مخزني</th><th>تاريخه</th><th class="n">نصيب الخدمة</th><th>ملاحظة</th></tr></thead><tbody>`;
          rowsOf(x.s).forEach(m => {
            const LB = {ok:'', frac:'نسبة استهلاك — راجعها', no_item:'الصنف غير موجود في دليل الأصناف', no_dispense:'لا توجد حركة صرف لهذا الصنف', no_tests:'عدد التحاليل غير مذكور في الملف', no_share:'نسبة التحمل فارغة'};
            const stt = m[9], lbl = (stt in LB) ? LB[stt] : stt;
            const nt = [lbl, m[12]].filter(Boolean).join(' · ');
            h += `<tr><td class="mono">${m[1]}</td><td>${esc(m[2]||'—')}</td><td class="n">${m[3]!=null? (m[3]*100).toFixed(m[3]<0.01?2:0)+'%':'—'}</td><td class="n">${m[4]||'—'}</td>
              <td class="n">${m[5]!=null? nfmt(m[5],3):'—'}</td><td class="n">${m[6]!=null? nfmt(m[6],4):'—'}</td><td>${esc(m[7]||'—')}</td>
              <td class="n"><b>${m[8]!=null? nfmt(m[8],4):'—'}</b></td><td class="${stt==='ok'?'':'warnc'}">${esc(nt)||'—'}</td></tr>`;
          });
          h += `</tbody></table></td></tr>`;
        }
      });
      h += `</tbody></table></div>`;
      cTab.innerHTML = h;
      cTab.querySelectorAll('.cst-r').forEach(tr => tr.onclick = () => { st.open = (st.open === tr.dataset.s) ? null : tr.dataset.s; render(); });

      // gaps
      const gaps = [
        ['أصناف في الملف غير موجودة في دليل الأصناف', C.map.filter(m=>m[9]==='no_item')],
        ['أصناف لم تُصرف من المستودع إطلاقاً', C.map.filter(m=>m[9]==='no_dispense')],
        ['أسطر مختبر بدون عدد تحاليل في عمود الوصف', C.map.filter(m=>m[9]==='no_tests')],
        ['أسطر مختبر نسبتها أقل من 5% — عوملت كنسبة استهلاك', C.map.filter(m=>m[9]==='frac')],
      ];
      let g = `<h3>بنود تحتاج مراجعة في ملف الخريطة</h3><p class="card-sub">هذه ليست نتيجة — هي أسطر لا تكفي لحساب تكلفة سليمة، وكل خدمة فيها سطر منها تظهر «ناقصة» أعلاه</p><div class="cst-gaps">`;
      gaps.forEach(([t, arr]) => {
        const svc = new Set(arr.map(m=>m[0]));
        g += `<div class="cst-gap"><div class="cst-gn">${arr.length}</div><div class="cst-gt">${t}</div><div class="cst-gs">${svc.size} خدمة متأثرة${arr.length? ' · ' + [...new Set(arr.map(m=>m[1]))].slice(0,6).join('، ') + (new Set(arr.map(m=>m[1])).size>6?' …':'') : ''}</div></div>`;
      });
      g += `</div>`;
      cGap.innerHTML = g;
    }
    onF(()=>{}); render();
  })();

  /* ------------------------------------------------------------------ 2 */
  /* Profitability                                                         */
  (function(){
    const sec = secs[1];
    audHead(sec, 'Costing', 'Service Profitability', 'ربحية الخدمات على مستوى الفاتورة والعميل والخدمة',
      'سعر البيع من فواتير المرضى في الفروع الأربعة مقابل تكلفة الأصناف المحدّثة من المخازن. الإيراد = المبلغ قبل الضريبة − الخصم − حصة المريض المُفوترة على الشركة (نفس تعريف الإيراد في باقي اللوحة، حتى لا تُحتسب حصة المريض مرتين). التكلفة = الكمية × تكلفة الخدمة. الخدمات التي لا تكلفة لها مستبعدة من هذه الشاشة.');
    const bar = el('div','aud-bar cst-bar'); sec.appendChild(bar);
    const kp = el('div','grid grid-4'); sec.appendChild(kp);
    const cCh = el('div','card'); cCh.style.marginTop='16px'; sec.appendChild(cCh);
    const cTab = el('div','card'); cTab.style.marginTop='16px'; sec.appendChild(cTab);
    sec.appendChild(el('div','note', `<b>المصدر.</b> <code>RC_PATIENT_INVOICE_CHARGES</code> × <code>RC_PATIENT_INVOICES</code> × <code>RC_PATIENT_EPISODES</code> × <code>RC_CONTRACTS</code> في الفروع الأربعة عبر Cure MCP، من ${ymLbl(C.ym[0])} إلى ${ymLbl(C.ym[C.ym.length-1])}، الفواتير غير الملغاة فقط. أسطر حصة المريض في عقود التأمين (<code>BILL_TO='P'</code>) لا تُحتسب في الكمية حتى لا تتضاعف التكلفة. «العميل» هنا هو <b>مجموعة العملاء</b> (شركة التأمين / جهة التعاقد) — العقد في EXSYS مفتوح لكل مؤمَّن على حدة (أكثر من 29 ألف عقد) فلا يصلح بُعداً للتحليل.`));

    const gkeys = [['svc','الخدمة'],['grp','مجموعة العملاء'],['pay','طريقة الدفع'],['csp','تخصص العيادة'],['ssp','تخصص الخدمة'],['doc','الطبيب'],['br','الفرع'],['ym','الشهر']];
    const st = {by:'svc', sort:'marg', n:40};
    const keyer = {
      svc: (i,code)=>code, grp: i=>C.gr[G.gr[i]], pay: i=>PAY(G.ct[i]),
      csp: i=>C.sp[G.sp[i]], ssp: (i,code)=>sspec(code), doc: i=>C.dc[G.dc[i]],
      br: i=>BRS[G.b[i]], ym: i=>C.ym[G.ym[i]],
    };
    const label = {
      svc: k=>sname(k)+' · '+k, grp: k=>C.grn[k]||k, pay: k=>k==='cash'?'نقدي':'آجل / تأمين',
      csp: k=>spn(k), ssp: k=>spn(k), doc: k=>((C.dcn[k.slice(0,2)]||{})[k.slice(3)]||k.slice(3))+' · '+C.brn[k.slice(0,2)],
      br: k=>C.brn[k], ym: k=>ymLbl(k),
    };
    function render(){
      bar.innerHTML = filterBar('cp') + `<div class="f"><label for="cp-by">التجميع حسب</label><select id="cp-by">${gkeys.map(([v,t])=>opt(v,t,st.by)).join('')}</select></div>`;
      wireBar(bar,'cp');
      bar.querySelector('#cp-by').onchange = e => { st.by = e.target.value; render(); };
      if(!G){ kp.innerHTML=''; cTab.innerHTML = '<p class="card-sub">جارٍ فك ضغط بيانات الفواتير…</p>'; return; }
      const {out, tot} = scan(keyer[st.by]);
      const R = rev(tot), M = marg(tot);
      kp.innerHTML = kpiTile('الإيراد', nfmt(R), `${nfmt(tot[0])} خدمة · ${nfmt(tot[5])} سطر فاتورة`)
        + kpiTile('تكلفة الأصناف', nfmt(tot[4]), `خصم ممنوح ${nfmt(tot[2])} (${pct(tot[1]?tot[2]/tot[1]:0)})`)
        + kpiTile('مجمل الربح', nfmt(M), `هامش ${pct(R?M/R:0)}`, M<0)
        + kpiTile('الربح لكل سطر فاتورة', nfmt(tot[5]? M/tot[5] : 0, 2), `متوسط سعر الخدمة ${nfmt(tot[0]?R/tot[0]:0,2)} · التكلفة ${nfmt(tot[0]?tot[4]/tot[0]:0,2)}`, M<0);

      // monthly chart
      const mrows = scan(i=>C.ym[G.ym[i]]).out;
      const yms = C.ym.slice(F.a, F.b+1);
      const W=1100,H=260,L=70,Rp=60,T=14,Bm=32;
      let mx=0; yms.forEach(y=>{ const a=mrows.get(y); if(a) mx=Math.max(mx, rev(a)); });
      mx = mx*1.12 || 1;
      const bw = (W-L-Rp)/Math.max(yms.length,1);
      const Y = v => T+(H-T-Bm)*(1-v/mx);
      let g='', bars='', line='', lbls='';
      const step=Math.pow(10,Math.floor(Math.log10(mx/4))); const tick=[1,2,2.5,5,10].map(x=>x*step).find(t=>mx/t<=5)||step*10;
      for(let t=0;t<=mx;t+=tick) g+=`<line x1="${L}" x2="${W-Rp}" y1="${Y(t)}" y2="${Y(t)}" class="an-grid"/><text x="${L-6}" y="${Y(t)+4}" class="an-ax" text-anchor="end">${t>=1e6?(t/1e6).toFixed(1)+'M':(t/1000).toFixed(0)+'k'}</text>`;
      yms.forEach((y,i)=>{
        const a=mrows.get(y)||[0,0,0,0,0,0,0]; const r=rev(a), c=a[4];
        const x=L+i*bw+bw*0.18, w=bw*0.64;
        bars += `<rect x="${x}" y="${Y(r)}" width="${w}" height="${Math.max(0,H-Bm-Y(r))}" class="cst-bar-r"><title>${ymLbl(y)} · إيراد ${nfmt(r)}</title></rect>`;
        bars += `<rect x="${x}" y="${Y(c)}" width="${w}" height="${Math.max(0,H-Bm-Y(c))}" class="cst-bar-c"><title>تكلفة ${nfmt(c)}</title></rect>`;
        const gm = r? (r-c)/r : 0;
        line += `${i?'L':'M'}${(x+w/2).toFixed(1)},${(T+(H-T-Bm)*(1-gm)).toFixed(1)}`;
        if(yms.length<=14 || i%2===0) lbls += `<text x="${x+w/2}" y="${H-12}" class="an-ax" text-anchor="middle">${ymLbl(y).slice(0,3)}</text>`;
      });
      for(let p=0;p<=1.0001;p+=0.25) g+=`<text x="${W-Rp+8}" y="${T+(H-T-Bm)*(1-p)+4}" class="an-ax">${(p*100).toFixed(0)}%</text>`;
      cCh.innerHTML = `<h3>الإيراد والتكلفة شهرياً</h3><p class="card-sub">العمود الفاتح = الإيراد · الغامق = تكلفة الأصناف · الخط = هامش الربح %</p>
        <div class="an-wrap"><svg viewBox="0 0 ${W} ${H}" class="an-svg">${g}${bars}<path d="${line}" class="cst-gm"/>${lbls}</svg></div>`;

      // table
      const rowsA = [...out.entries()].map(([k,a])=>({k,a,r:rev(a),m:marg(a)}));
      const cmp = {marg:(x,y)=>y.m-x.m, loss:(x,y)=>x.m-y.m, rev:(x,y)=>y.r-x.r, gm:(x,y)=>(y.r?y.m/y.r:0)-(x.r?x.m/x.r:0), qty:(x,y)=>y.a[0]-x.a[0]};
      rowsA.sort(cmp[st.sort]);
      const show = rowsA.slice(0, st.n);
      let h = `<div class="cst-th"><h3>الربحية حسب ${gkeys.find(g=>g[0]===st.by)[1]}</h3>
        <div class="aud-bar" style="margin:0"><div class="f"><label for="cp-sort">ترتيب</label><select id="cp-sort">${[['marg','أعلى ربح'],['loss','أكبر خسارة'],['rev','أعلى إيراد'],['gm','أعلى هامش %'],['qty','أعلى كمية']].map(([v,t])=>opt(v,t,st.sort)).join('')}</select></div>
        <div class="f"><label for="cp-n">عدد الصفوف</label><select id="cp-n">${[20,40,80,200,1000].map(v=>opt(v,v===1000?'الكل':String(v),st.n)).join('')}</select></div></div></div>
        <div class="aud-x"><table class="aud-t cst-t"><thead><tr><th>${gkeys.find(g=>g[0]===st.by)[1]}</th><th class="n">الكمية</th><th class="n">مجاني</th><th class="n">إجمالي قبل الخصم</th><th class="n">الخصم</th><th class="n">الإيراد</th><th class="n">التكلفة</th><th class="n">الربح</th><th class="n">الهامش %</th><th class="n">أسطر الفواتير</th><th class="n">الربح للسطر</th></tr></thead><tbody>`;
      show.forEach(({k,a,r,m}) => {
        h += `<tr><td>${esc(label[st.by](k))}</td><td class="n">${nfmt(a[0])}</td><td class="n">${a[6]?nfmt(a[6]):'—'}</td><td class="n">${nfmt(a[1])}</td>
          <td class="n">${nfmt(a[2])}${a[1]?` <span class="cst-sub">${pct(a[2]/a[1],0)}</span>`:''}</td><td class="n">${nfmt(r)}</td><td class="n">${nfmt(a[4])}</td>
          <td class="n ${m<0?'neg':'pos'}"><b>${nfmt(m)}</b></td><td class="n ${m<0?'neg':''}">${pct(r?m/r:0)}</td><td class="n">${nfmt(a[5])}</td><td class="n">${nfmt(a[5]?m/a[5]:0,1)}</td></tr>`;
      });
      h += `</tbody></table></div>`;
      if(rowsA.length > show.length) h += `<p class="card-sub" style="margin-top:8px">معروض ${show.length} من ${rowsA.length}</p>`;
      cTab.innerHTML = h;
      cTab.querySelector('#cp-sort').onchange = e => { st.sort=e.target.value; render(); };
      cTab.querySelector('#cp-n').onchange = e => { st.n=+e.target.value; render(); };
    }
    onF(render); render();
  })();

  /* ------------------------------------------------------------------ 3 */
  /* Loss-making services and the maximum discount guard                   */
  (function(){
    const sec = secs[2];
    audHead(sec, 'Costing', 'Loss Makers & Discount Ceiling', 'الخدمات المُباعة بخسارة وأقصى خصم مسموح',
      'لكل خدمة: متوسط سعر البيع قبل الخصم من الفواتير الفعلية مقابل تكلفة الأصناف، ومنهما <b>أقصى خصم يصل بالسعر إلى التعادل</b> = 1 − (التكلفة ÷ السعر). أي خصم أكبر يبيع الخدمة بأقل من تكلفة الأصناف — وهذا قبل أي تحميل لأجور أو مصاريف غير مباشرة، فالحد الحقيقي أقل مما هو معروض.');
    const bar = el('div','aud-bar cst-bar'); sec.appendChild(bar);
    const kp = el('div','grid grid-4'); sec.appendChild(kp);
    const cTab = el('div','card'); cTab.style.marginTop='16px'; sec.appendChild(cTab);
    const cGrp = el('div','card'); cGrp.style.marginTop='16px'; sec.appendChild(cGrp);
    sec.appendChild(el('div','note', `<b>كيف تُقرأ.</b> «السعر» هو متوسط المبلغ قبل الخصم وقبل الضريبة لكل وحدة خدمة في الفترة والفلاتر المختارة، وقد يختلف عن التعريفة الرسمية إذا كانت العقود بأسعار متفاوتة. الخدمة تظهر خسرانة إذا كان الإيراد بعد الخصم وحصة المريض أقل من التكلفة. راجع دائماً أسطر الخريطة قبل اتخاذ قرار تسعير — خطأ في عدد التحاليل أو نسبة التحمل يقلب النتيجة. هذه الشاشة تعرض أيضاً الخدمات <b>ناقصة التكلفة</b>: تكلفتها المحسوبة أقل من الحقيقية، فإذا ظهرت خاسرة فهي خاسرة بيقين وبأكثر مما هو معروض.`));

    const st = {only:'loss', sort:'loss', sel:null};
    function render(){
      bar.innerHTML = filterBar('cl') + `<div class="f"><label for="cl-only">العرض</label><select id="cl-only">${[['loss','الخدمات الخاسرة فقط'],['risk','الخاسرة + القريبة من التعادل'],['all','كل الخدمات المسعّرة']].map(([v,t])=>opt(v,t,st.only)).join('')}</select></div>`;
      wireBar(bar,'cl');
      bar.querySelector('#cl-only').onchange = e => { st.only=e.target.value; render(); };
      if(!G){ cTab.innerHTML = '<p class="card-sub">جارٍ فك ضغط بيانات الفواتير…</p>'; return; }
      const keepC = F.cmp; F.cmp = 'any';        // a partly-costed service that already shows a loss is still a finding
      const {out, tot} = scan((i,code)=>code);
      F.cmp = keepC;
      let rowsA = [...out.entries()].map(([k,a])=>{
        const r = rev(a), m = r - a[4];
        const price = a[0] ? a[1]/a[0] : 0;
        const cost = uc(k);
        const maxD = price ? 1 - cost/price : null;
        const actD = a[1] ? a[2]/a[1] : 0;
        return {k, a, r, m, price, cost, maxD, actD, gm: r? m/r : 0};
      }).filter(x=>x.a[0] > 0);
      const lossA = rowsA.filter(x=>x.m<0);
      const risk = rowsA.filter(x=>x.m>=0 && x.gm<0.15);
      const over = rowsA.filter(x=>x.maxD!=null && x.actD > x.maxD);
      kp.innerHTML = kpiTile('خدمات تُباع بخسارة', String(lossA.length), `من ${rowsA.length} خدمة مسعّرة لها حركة`)
        + kpiTile('قيمة الخسارة', nfmt(lossA.reduce((t,x)=>t+x.m,0)), `على ${nfmt(lossA.reduce((t,x)=>t+x.a[0],0))} وحدة خدمة`, true)
        + kpiTile('خدمات تجاوز خصمها الحد', String(over.length), 'متوسط الخصم الفعلي أكبر من حد التعادل')
        + kpiTile('خدمات هامشها دون 15 بالمئة', String(risk.length), 'قريبة من التعادل — تحتاج سقف خصم');
      if(st.only==='loss') rowsA = lossA; else if(st.only==='risk') rowsA = lossA.concat(risk);
      rowsA.sort((x,y)=> st.sort==='loss' ? x.m-y.m : y.a[0]-x.a[0]);
      let h = `<h3>سقف الخصم لكل خدمة</h3><p class="card-sub">اضغط على خدمة لتفصيل ربحيتها حسب مجموعة العملاء · ${rowsA.length} خدمة</p>
        <div class="aud-x"><table class="aud-t cst-t"><thead><tr><th>الكود</th><th>الخدمة</th><th class="n">الكمية</th><th class="n">السعر قبل الخصم</th><th class="n">التكلفة</th><th>اكتمال التكلفة</th><th class="n">أقصى خصم للتعادل</th><th class="n">الخصم الفعلي</th><th class="n">الإيراد</th><th class="n">الربح</th><th class="n">الهامش %</th></tr></thead><tbody>`;
      rowsA.forEach(x => {
        const bust = x.maxD!=null && x.actD > x.maxD;
        h += `<tr class="cst-r2 ${st.sel===x.k?'on':''}" data-s="${x.k}"><td class="mono">${x.k}</td><td>${esc(sname(x.k))}</td><td class="n">${nfmt(x.a[0])}</td>
          <td class="n">${nfmt(x.price,2)}</td><td class="n">${nfmt(x.cost,3)}</td>
          <td>${ust(x.k)==='ok'?'<span class="pill ok">مكتملة</span>':'<span class="pill warn">ناقصة — التكلفة أقل من الحقيقة</span>'}</td>
          <td class="n"><b class="${x.maxD!=null&&x.maxD<=0?'neg':''}">${x.maxD==null?'—':(x.maxD<=0?'لا خصم':pct(x.maxD,0))}</b></td>
          <td class="n ${bust?'neg':''}">${pct(x.actD,0)}${bust?' ⚠':''}</td><td class="n">${nfmt(x.r)}</td>
          <td class="n ${x.m<0?'neg':'pos'}"><b>${nfmt(x.m)}</b></td><td class="n ${x.m<0?'neg':''}">${pct(x.gm)}</td></tr>`;
      });
      h += `</tbody></table></div>`;
      if(!rowsA.length) h += `<p class="card-sub">لا توجد خدمات مطابقة في هذه الفترة والفلاتر.</p>`;
      cTab.innerHTML = h;
      cTab.querySelectorAll('.cst-r2').forEach(tr => tr.onclick = () => { st.sel = (st.sel===tr.dataset.s)?null:tr.dataset.s; render(); });

      if(st.sel){
        const keep = F.svc, keepC2 = F.cmp; F.svc = st.sel; F.cmp = 'any';
        const g = scan(i=>C.gr[G.gr[i]]+'|'+PAY(G.ct[i])).out;
        F.svc = keep; F.cmp = keepC2;
        const cost = uc(st.sel);
        let gh = `<h3>${esc(sname(st.sel))} <span class="tag">${st.sel}</span></h3><p class="card-sub">ربحية الخدمة حسب مجموعة العملاء وطريقة الدفع · التكلفة ${nfmt(cost,3)} ريال للوحدة</p>
          <div class="aud-x"><table class="aud-t cst-t"><thead><tr><th>مجموعة العملاء</th><th>الدفع</th><th class="n">الكمية</th><th class="n">السعر</th><th class="n">الخصم %</th><th class="n">الإيراد للوحدة</th><th class="n">الربح للوحدة</th><th class="n">إجمالي الربح</th><th class="n">أقصى خصم</th></tr></thead><tbody>`;
        const arr = [...g.entries()].map(([k,a])=>({k,a,r:rev(a),m:marg(a)})).sort((x,y)=>x.m-y.m);
        arr.forEach(({k,a,r,m}) => {
          const [gk,pk]=k.split('|'); const price=a[0]?a[1]/a[0]:0; const md=price?1-cost/price:null;
          gh += `<tr><td>${esc(C.grn[gk]||gk)}</td><td>${pk==='cash'?'نقدي':'آجل'}</td><td class="n">${nfmt(a[0])}</td><td class="n">${nfmt(price,2)}</td>
            <td class="n">${pct(a[1]?a[2]/a[1]:0,0)}</td><td class="n">${nfmt(a[0]?r/a[0]:0,2)}</td>
            <td class="n ${m<0?'neg':'pos'}">${nfmt(a[0]?m/a[0]:0,2)}</td><td class="n ${m<0?'neg':'pos'}"><b>${nfmt(m)}</b></td>
            <td class="n">${md==null?'—':(md<=0?'لا خصم':pct(md,0))}</td></tr>`;
        });
        gh += `</tbody></table></div>`;
        cGrp.innerHTML = gh; cGrp.style.display='';
      } else { cGrp.style.display='none'; }
    }
    onF(render); render();
  })();

  /* ---------------------------------------------------------------- boot */
  decode().then(g => { G = g; fire(); })
          .catch(e => { console.error('cost decode', e);
            secs.slice(1).forEach(s => s && s.insertAdjacentHTML('beforeend',
              '<div class="note">تعذّر فك ضغط بيانات الفواتير في هذا المتصفح. افتح اللوحة في متصفح حديث (Chrome / Edge / Safari 16.4+).</div>')); });
})();
