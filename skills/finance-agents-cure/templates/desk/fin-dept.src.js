/* «الإدارة المالية» — AI Finance Department tab for the Modeling Desk.
   Self-contained: adds its own sidebar group + section, uses the Desk's activate() and Cure-skin variables.
   Data: window.FIN_DATA (built by build_desk_fin.py). 3D office: fin-office.html beside index.html. */
(function(){
  const D = window.FIN_DATA; if(!D || !D.periods || !D.periods.length) return;
  const ID = 'fin-dept';
  const css = `
#sec-${ID}{direction:rtl;text-align:right;font-family:'IBM Plex Sans Arabic',var(--font,system-ui),sans-serif}
#sec-${ID} .fd-head{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:14px}
#sec-${ID} .fd-head h2{margin:4px 0;font-size:24px}
#sec-${ID} .fd-mute{color:var(--cu-mute,#64748b);font-size:13px}
#sec-${ID} select,#sec-${ID} input{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--cu-line,#d6dde6);background:var(--cu-surf,#fff);color:inherit}
#sec-${ID} .fd-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 16px;border-bottom:1px solid var(--cu-line,#d6dde6)}
#sec-${ID} .fd-tabs button{font:inherit;font-size:14px;padding:8px 14px;border:0;background:none;color:var(--cu-mute,#64748b);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
#sec-${ID} .fd-tabs button.on{color:var(--cu-blue,#0b6fbf);border-color:var(--cu-blue,#0b6fbf);font-weight:600}
#sec-${ID} .fd-kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:16px}
#sec-${ID} .fd-k{background:var(--cu-surf,#fff);border:1px solid var(--cu-line,#d6dde6);border-radius:12px;padding:14px 16px;box-shadow:var(--cu-shadow,none)}
#sec-${ID} .fd-k b{display:block;font-size:26px;line-height:1.2}
#sec-${ID} .fd-k span{font-size:12px;color:var(--cu-mute,#64748b)}
#sec-${ID} .fd-card{background:var(--cu-surf,#fff);border:1px solid var(--cu-line,#d6dde6);border-radius:12px;padding:16px 18px;margin-bottom:14px;box-shadow:var(--cu-shadow,none);line-height:1.75}
#sec-${ID} .fd-card h2{font-size:17px;margin:18px 0 8px}#sec-${ID} .fd-card h3{font-size:15px;margin:14px 0 6px}
#sec-${ID} .fd-tw{overflow-x:auto}
#sec-${ID} table.fd-t{width:100%;border-collapse:collapse;font-size:13px}
#sec-${ID} .fd-t th{background:var(--cu-th,#0b6fbf);color:#fff;text-align:right;padding:8px 10px;font-weight:600;white-space:nowrap}
#sec-${ID} .fd-t td{padding:8px 10px;border-top:1px solid var(--cu-line,#e3e8ef);vertical-align:top}
#sec-${ID} .fd-t tr.fd-row{cursor:pointer}#sec-${ID} .fd-t tr.fd-row:hover td{background:var(--cu-soft,#eef5fd)}
#sec-${ID} .fd-ev td{background:var(--cu-surf2,#f4f6f9)}
#sec-${ID} .sev{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600;color:#fff;white-space:nowrap}
#sec-${ID} .sev.high{background:var(--cu-red,#d7261e)}#sec-${ID} .sev.medium{background:var(--cu-orange,#f5a623)}
#sec-${ID} .sev.low{background:var(--cu-blue2,#3aa0f0)}#sec-${ID} .sev.info{background:#8794a8}
#sec-${ID} .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-inline-end:6px;vertical-align:middle}
#sec-${ID} .ok{color:var(--cu-green,#1e9e5a);font-weight:600}#sec-${ID} .bad{color:var(--cu-red,#d7261e);font-weight:600}
#sec-${ID} .fd-filters{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
#sec-${ID} .cp{font:inherit;font-size:11px;padding:1px 7px;border-radius:6px;border:1px solid var(--cu-line,#d6dde6);background:var(--cu-surf,#fff);cursor:pointer;margin-inline-start:6px}
#sec-${ID} iframe{width:100%;height:calc(100vh - 230px);min-height:520px;border:1px solid var(--cu-line,#d6dde6);border-radius:12px;background:#111}
#sec-${ID} code{background:var(--cu-soft,#eef2ff);padding:1px 5px;border-radius:5px;font-size:12px;direction:ltr;unicode-bidi:embed}
#sec-${ID} blockquote{margin:8px 0;padding:8px 12px;border-inline-start:3px solid var(--cu-blue,#0b6fbf);background:var(--cu-soft,#eef5fd);border-radius:6px}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  // sidebar entry + section (appended after the existing groups; nothing existing is changed)
  const nav = document.getElementById('nav'), main = document.getElementById('main');
  if(!nav || !main || document.getElementById('sec-'+ID)) return;
  const g = document.createElement('div'); g.className = 'nav-group'; g.textContent = 'AI Finance Department';
  const b = document.createElement('button'); b.className = 'nav-item'; b.dataset.target = ID;
  b.innerHTML = '<span class="ic">⚙</span>الإدارة المالية · AI Agents'; b.addEventListener('click', ()=> window.activate ? activate(ID) : null);
  // placed right under CFO Command Center (its single sidebar entry); falls back to the end of the sidebar
  const cfo = nav.querySelector('.nav-item[data-target="cfo-exec"]');
  if(cfo && cfo.parentNode === nav){ cfo.after(g); g.after(b); } else { nav.appendChild(g); nav.appendChild(b); }
  const sec = document.createElement('section'); sec.className = 'section'; sec.id = 'sec-'+ID; main.appendChild(sec);

  const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const num = v => (typeof v==='number') ? v.toLocaleString('en-US',{maximumFractionDigits:2}) : esc(v);
  const SEVN = {high:'عالية',medium:'متوسطة',low:'منخفضة',info:'للعلم'};
  const STN = {new:'جديدة',still_open:'مفتوحة',partly_fixed:'صُححت جزئياً',fixed:'صُححت',unverified:'غير مؤكدة'};
  let per = D.periods[D.periods.length-1].period, tab = 'ov', flt = {role:'',sev:'',q:''}, open = {};

  function P(){ return D.periods.find(p=>p.period===per); }
  function render(){
    const p = P(), all = p.roles.flatMap(r=>r.findings.map(f=>Object.assign({role:r.id,role_ar:r.name_ar,color:r.color},f)));
    const approved = p.roles.filter(r=>r.decision==='approved').length, high = all.filter(f=>f.severity==='high').length;
    sec.innerHTML = `
      <div class="fd-head"><div><div class="eyebrow">AI Finance Department · ${esc(D.site)}</div>
        <h2>الإدارة المالية بالذكاء الاصطناعي</h2>
        <div class="fd-mute">مخرجات الوكلاء بعد مراجعة رئيس الحسابات والمراجع الداخلي · قراءة فقط من Cure · آخر بناء ${esc(D.built)}</div></div>
        <label class="fd-mute">الفترة <select id="fd-per">${D.periods.map(x=>`<option ${x.period===per?'selected':''}>${x.period}</option>`).join('')}</select></label></div>
      <div class="fd-tabs">${[['ov','نظرة عامة'],['fi','الملاحظات ('+all.length+')'],['sm','الملخص الإداري'],['au','المراجعة الداخلية'],['lg','سجل التشغيل'],['of','المكتب 3D']]
        .map(([k,t])=>`<button data-t="${k}" class="${tab===k?'on':''}">${t}</button>`).join('')}</div>
      <div id="fd-body"></div>`;
    sec.querySelector('#fd-per').onchange = e=>{ per = e.target.value; render(); };
    sec.querySelectorAll('.fd-tabs button').forEach(x=>x.onclick=()=>{ tab = x.dataset.t; render(); });
    const body = sec.querySelector('#fd-body');
    if(tab==='ov'){
      body.innerHTML = `
      <div class="fd-kpis">
        <div class="fd-k"><b class="${approved===p.roles.length?'ok':''}">${approved} / ${p.roles.length}</b><span>ملفات معتمدة من رئيس الحسابات</span></div>
        <div class="fd-k"><b class="${p.blockers.length>1?'bad':''}">${Math.max(0,p.blockers.length-1)}</b><span>موانع إقفال</span></div>
        <div class="fd-k"><b class="${high?'bad':''}">${high}</b><span>ملاحظات عالية</span></div>
        <div class="fd-k"><b>${esc(p.audit_rating||'—')}</b><span>تقييم المراجع الداخلي</span></div></div>
      ${p.headline?`<div class="fd-card"><b>الخلاصة: </b>${p.headline}</div>`:''}
      ${p.blockers.length>1?`<div class="fd-card"><h3 style="margin-top:0">موانع الإقفال</h3>${tbl(p.blockers)}</div>`:''}
      <div class="fd-card"><h3 style="margin-top:0">حالة الموظفين</h3><div class="fd-tw"><table class="fd-t"><thead><tr>
        <th>الموظف</th><th>القرار</th><th>الموديل</th><th>عالية</th><th>متوسطة</th><th>منخفضة</th><th>للعلم</th><th>الملخص</th></tr></thead><tbody>
        ${p.roles.map(r=>{const c=s=>r.findings.filter(f=>f.severity===s).length;
          return `<tr><td><span class="dot" style="background:${r.color}"></span>${esc(r.name_ar)}</td>
          <td>${r.decision==='approved'?'<span class="ok">معتمد</span>':'<span class="bad">'+esc(r.decision||'قيد المراجعة')+'</span>'}${r.returned_before?' <span class="fd-mute">(بعد إرجاع)</span>':''}</td>
          <td>${esc(r.model_used||(D.roles_def.find(x=>x.id===r.id)||{}).model||'—')}</td><td>${c('high')}</td><td>${c('medium')}</td><td>${c('low')}</td><td>${c('info')}</td>
          <td style="min-width:280px">${esc(r.summary_ar).slice(0,260)}${(r.summary_ar||'').length>260?'…':''}</td></tr>`}).join('')}
        </tbody></table></div></div>`;
    }
    else if(tab==='fi'){
      const rows = all.filter(f=>(!flt.role||f.role===flt.role)&&(!flt.sev||f.severity===flt.sev)&&
        (!flt.q||JSON.stringify(f).toLowerCase().includes(flt.q.toLowerCase())));
      const order = {high:0,medium:1,low:2,info:3}; rows.sort((a,b)=>(order[a.severity]-order[b.severity])||((b.amount||0)-(a.amount||0)));
      body.innerHTML = `<div class="fd-filters">
        <select id="fd-r"><option value="">كل الموظفين</option>${p.roles.map(r=>`<option value="${r.id}" ${flt.role===r.id?'selected':''}>${esc(r.name_ar)}</option>`).join('')}</select>
        <select id="fd-s"><option value="">كل الدرجات</option>${Object.keys(SEVN).map(s=>`<option value="${s}" ${flt.sev===s?'selected':''}>${SEVN[s]}</option>`).join('')}</select>
        <input id="fd-q" placeholder="بحث: رقم قيد، حساب، كلمة…" value="${esc(flt.q)}" style="min-width:240px">
        <span class="fd-mute" style="align-self:center">${rows.length} ملاحظة · اضغط على الصف لعرض الأدلة</span></div>
        <div class="fd-tw"><table class="fd-t"><thead><tr><th>الدرجة</th><th>الموظف</th><th>الملاحظة</th><th>المبلغ</th><th>الحالة</th><th>المعرّف</th></tr></thead><tbody>
        ${rows.map(f=>{const k=f.role+'|'+f.id;return `<tr class="fd-row" data-k="${esc(k)}"><td><span class="sev ${f.severity}">${SEVN[f.severity]||esc(f.severity)}</span>${f.blocks_close?' <span class="bad">⛔</span>':''}</td>
          <td><span class="dot" style="background:${f.color}"></span>${esc(f.role_ar)}</td><td><b>${esc(f.title_ar)}</b></td>
          <td style="white-space:nowrap">${f.amount!=null?num(f.amount):''}</td><td>${STN[f.status]||esc(f.status||'')}</td><td><code>${esc(f.id)}</code></td></tr>
          ${open[k]?`<tr class="fd-ev"><td colspan="6">${f.detail_ar?`<p style="margin:0 0 8px">${esc(f.detail_ar)}</p>`:''}${f.rule?`<div class="fd-mute">القاعدة: ${esc(f.rule)}</div>`:''}
            <div class="fd-tw"><table class="fd-t"><thead><tr><th>الفرع</th><th>المرجع</th><th>الحساب</th><th>التاريخ</th><th>المبلغ</th><th>البيان</th></tr></thead><tbody>
            ${(f.evidence||[]).map(e=>`<tr><td>${esc(e.branch)}</td><td style="white-space:nowrap"><code>${esc(e.ref)}</code><button class="cp" data-c="${esc(e.ref)}">نسخ</button></td>
              <td>${esc(e.account)}</td><td style="white-space:nowrap">${esc(e.date)}</td><td>${e.amount!=null?num(e.amount):''}</td><td>${esc(e.narration)}</td></tr>`).join('')}
            </tbody></table></div></td></tr>`:''}`}).join('')}</tbody></table></div>`;
      body.querySelector('#fd-r').onchange=e=>{flt.role=e.target.value;render()};
      body.querySelector('#fd-s').onchange=e=>{flt.sev=e.target.value;render()};
      const q=body.querySelector('#fd-q'); q.onchange=e=>{flt.q=e.target.value;render()};
      body.querySelectorAll('tr.fd-row').forEach(tr=>tr.onclick=()=>{open[tr.dataset.k]=!open[tr.dataset.k];render()});
      body.querySelectorAll('.cp').forEach(c=>c.onclick=ev=>{ev.stopPropagation();try{navigator.clipboard.writeText(c.dataset.c).then(()=>{c.textContent='✓'},()=>{c.textContent='—'})}catch(e){c.textContent='—'}});
    }
    else if(tab==='sm') body.innerHTML = `<div class="fd-card">${p.summary_html||'<p class="fd-mute">لا يوجد ملخص لهذه الفترة.</p>'}</div>`;
    else if(tab==='au') body.innerHTML = `<div class="fd-card">${p.audit_html||'<p class="fd-mute">لم تتم المراجعة الداخلية لهذه الفترة.</p>'}</div>`;
    else if(tab==='lg') body.innerHTML = `<div class="fd-card">${p.log_html||''}</div>`;
    else if(tab==='of') body.innerHTML = `<iframe ${window.FIN_OFFICE_HTML?'':'src="fin-office.html"'} title="المكتب 3D" loading="lazy"></iframe>
      <div class="fd-mute" style="margin-top:6px">نفس المكتب المنشور كصفحة مستقلة: أزرار التكبير والتحريك أسفل يمين المشهد، و⤢ لملاءمة الشاشة.</div>`;
    if(tab==='of' && window.FIN_OFFICE_HTML){ const fr=body.querySelector('iframe'); if(fr) fr.srcdoc = window.FIN_OFFICE_HTML; }
  }
  function tbl(rows){ if(!rows.length) return ''; return `<div class="fd-tw"><table class="fd-t"><thead><tr>${rows[0].map(c=>`<th>${esc(c)}</th>`).join('')}</tr></thead><tbody>${
    rows.slice(1).map(r=>`<tr>${r.map(c=>`<td>${esc(c).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>')}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`; }
  render();
})();
