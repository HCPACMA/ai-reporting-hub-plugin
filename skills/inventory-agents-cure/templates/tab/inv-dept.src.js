/* «إدارة المخازن · AI Agents» — tab for the Inventory Audit dashboard.
   Adds one sidebar entry right under Overview and its own panel; uses the dashboard's .tab-btn / .panel switching.
   Data: window.INV_DATA (built by build_inv_tab.py). 3D: window.INV_OFFICE_HTML (inlined) or inv-office.html beside the page. */
(function(){
  const D = window.INV_DATA; if(!D || !D.roles) return;
  const ID = 'invdept', tabs = document.getElementById('tabs');
  if(!tabs || document.getElementById('panel-'+ID)) return;
  const css = `
#panel-${ID}{direction:rtl;text-align:right;font-family:'IBM Plex Sans Arabic',system-ui,sans-serif}
#panel-${ID} .iv-head{display:flex;justify-content:space-between;align-items:flex-end;gap:14px;flex-wrap:wrap;margin-bottom:10px}
#panel-${ID} .iv-head h2{margin:4px 0;font-size:22px}
#panel-${ID} .iv-mute{color:var(--cu-mute,#64748b);font-size:13px}
#panel-${ID} .iv-sub{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 14px;border-bottom:1px solid var(--cu-line,#d6dde6)}
#panel-${ID} .iv-sub button{font:inherit;font-size:14px;padding:8px 14px;border:0;background:none;color:var(--cu-mute,#64748b);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}
#panel-${ID} .iv-sub button.on{color:var(--cu-blue,#0b6fbf);border-color:var(--cu-blue,#0b6fbf);font-weight:600}
#panel-${ID} .iv-card{background:var(--cu-surf,#fff);border:1px solid var(--cu-line,#d6dde6);border-radius:12px;padding:14px 16px;margin-bottom:12px;box-shadow:var(--cu-shadow,none);line-height:1.75}
#panel-${ID} .iv-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
#panel-${ID} .iv-role h3{margin:0;font-size:16px;display:flex;align-items:center;gap:8px}
#panel-${ID} .iv-role .en{font-size:12px;color:var(--cu-mute,#64748b);font-weight:400}
#panel-${ID} .dot{display:inline-block;width:10px;height:10px;border-radius:50%}
#panel-${ID} .chip{display:inline-block;font-size:11.5px;padding:2px 9px;border-radius:999px;border:1px solid var(--cu-line,#d6dde6);margin:2px 0 2px 4px;background:var(--cu-surf2,#f4f6f9)}
#panel-${ID} .chip.lnk{cursor:pointer;color:var(--cu-blue,#0b6fbf)}
#panel-${ID} table.iv-t{width:100%;border-collapse:collapse;font-size:13px;margin-top:6px}
#panel-${ID} .iv-t th{background:var(--cu-th,#0b6fbf);color:#fff;text-align:right;padding:7px 9px;font-weight:600;white-space:nowrap}
#panel-${ID} .iv-t td{padding:7px 9px;border-top:1px solid var(--cu-line,#e3e8ef);vertical-align:top}
#panel-${ID} .iv-tw{overflow-x:auto}
#panel-${ID} .org{display:flex;flex-direction:column;align-items:center;gap:0}
#panel-${ID} .org .lvl{display:flex;justify-content:center;gap:10px;flex-wrap:wrap}
#panel-${ID} .org .n{border:1px solid var(--cu-line,#d6dde6);border-top:4px solid var(--c);border-radius:10px;padding:8px 12px;background:var(--cu-surf,#fff);min-width:150px;text-align:center;cursor:pointer}
#panel-${ID} .org .n small{display:block;color:var(--cu-mute,#64748b);font-size:11px}
#panel-${ID} .org .v{width:2px;height:18px;background:#94a3b8}
#panel-${ID} select{font:inherit;padding:6px 10px;border-radius:8px;border:1px solid var(--cu-line,#d6dde6);background:var(--cu-surf,#fff);color:inherit}
#panel-${ID} iframe{width:100%;height:calc(100vh - 220px);min-height:520px;border:1px solid var(--cu-line,#d6dde6);border-radius:12px;background:#111}
#panel-${ID} .sev{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600;color:#fff}
#panel-${ID} .sev.high{background:#d7261e}#panel-${ID} .sev.medium{background:#f5a623}#panel-${ID} .sev.low{background:#3aa0f0}#panel-${ID} .sev.info{background:#8794a8}`;
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  // sidebar entry under Overview
  const ov = tabs.querySelector('.tab-btn[data-tab="overview"]');
  const lab = document.createElement('div'); lab.className = 'sidebar-label'; lab.textContent = 'AI Inventory Department';
  const btn = document.createElement('button'); btn.className = 'tab-btn'; btn.setAttribute('role','tab'); btn.setAttribute('aria-selected','false'); btn.dataset.tab = ID;
  btn.innerHTML = '🤖 إدارة المخازن · AI Agents';
  if(ov){ ov.after(lab); lab.after(btn); } else { tabs.appendChild(lab); tabs.appendChild(btn); }
  const ref = document.getElementById('panel-overview');
  const panel = document.createElement('section'); panel.className = 'panel'; panel.id = 'panel-'+ID;
  (ref ? ref.parentNode : document.querySelector('main') || document.body).appendChild(panel);
  btn.addEventListener('click', ()=>{
    document.querySelectorAll('.tab-btn').forEach(b=>b.setAttribute('aria-selected', b===btn));
    document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
    panel.classList.add('active'); render();
  });
  const goTab = id => { const b = tabs.querySelector('.tab-btn[data-tab="'+id+'"]'); if(b) b.click(); };

  const esc = s => String(s==null?'':s).replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const R = Object.fromEntries(D.roles.map(r=>[r.id,r]));
  const SEVN = {high:'عالية',medium:'متوسطة',low:'منخفضة',info:'للعلم'};
  let sub = 'duties', who = '';
  function tabChips(r){ return (r.tabs||[]).map(t=>`<span class="chip lnk" data-go="${esc(t)}">${esc(D.tab_labels[t]||t)}</span>`).join(''); }
  function node(id){ const r=R[id]; return r?`<div class="n" style="--c:${r.color}" data-who="${id}"><b>${esc(r.name_ar)}</b><small>${esc(r.name_en)}</small></div>`:''; }
  function render(){
    const P = D.periods && D.periods.length ? D.periods[D.periods.length-1] : null;
    const findings = P ? P.roles.flatMap(r=>r.findings.map(f=>Object.assign({role_ar:R[r.id]?R[r.id].name_ar:r.id,color:(R[r.id]||{}).color},f))) : [];
    const subs = [['ov','نظرة عامة'],['duties','المهام الوظيفية'],['fi','الملاحظات ('+findings.length+')'],['sm','الملخص'],['wh','المستودع 3D']];
    panel.innerHTML = `<div class="iv-head"><div><div class="iv-mute">AI Inventory Department · ${esc(D.site)}</div>
      <h2>إدارة المخازن بالذكاء الاصطناعي</h2>
      <div class="iv-mute">9 وكلاء بوصف وظيفي ومهام ومؤشرات أداء · قراءة فقط من Cure · ${P?'آخر تشغيل '+esc(P.period):'لم يتم أول تشغيل بعد'}</div></div></div>
      <div class="iv-sub">${subs.map(([k,t])=>`<button data-s="${k}" class="${sub===k?'on':''}">${t}</button>`).join('')}</div><div id="iv-body"></div>`;
    panel.querySelectorAll('.iv-sub button').forEach(b=>b.onclick=()=>{sub=b.dataset.s;render()});
    const body = panel.querySelector('#iv-body');
    const makers = D.roles.filter(r=>r.kind==='maker');
    if(sub==='ov'){
      body.innerHTML = `<div class="iv-card"><div class="org">
        <div class="lvl"><div class="n" style="--c:#64748b"><b>المدير المالي</b><small>الإدارة المالية</small></div></div><div class="v"></div>
        <div class="lvl">${node('inv-manager')}${node('inv-auditor')}</div><div class="v"></div>
        <div class="lvl">${node('inv-controller')}</div><div class="v"></div>
        <div class="lvl">${makers.map(r=>node(r.id)).join('')}</div></div>
        <p class="iv-mute" style="text-align:center;margin:10px 0 0">اضغط على أي وظيفة لعرض مهامها الوظيفية</p></div>
        <div class="iv-card iv-tw"><table class="iv-t"><thead><tr><th>الموظف</th><th>يرفع إلى</th><th>الموديل</th><th>التابات اللي بيشتغل عليها</th><th>مؤشرات الأداء</th><th>الحالة</th></tr></thead><tbody>
        ${D.roles.map(r=>{const pr=P&&P.roles.find(x=>x.id===r.id);return `<tr><td><span class="dot" style="background:${r.color}"></span> ${esc(r.name_ar)}</td>
          <td>${esc(r.reports_to_ar)}</td><td>${esc(r.model)}</td><td>${tabChips(r)||'—'}</td><td>${(r.kpis_ar||[]).map(esc).join('، ')}</td>
          <td>${pr?(pr.decision==='approved'?'معتمد':esc(pr.decision||'قيد المراجعة')):'<span class="iv-mute">لم يُشغَّل بعد</span>'}</td></tr>`}).join('')}</tbody></table></div>`;
      body.querySelectorAll('[data-who]').forEach(n=>n.onclick=()=>{who=n.dataset.who;sub='duties';render()});
    }
    else if(sub==='duties'){
      const list = who ? D.roles.filter(r=>r.id===who) : D.roles;
      body.innerHTML = `<div style="margin-bottom:10px"><label class="iv-mute">الموظف <select id="iv-who"><option value="">كل الموظفين</option>${D.roles.map(r=>`<option value="${r.id}" ${who===r.id?'selected':''}>${esc(r.name_ar)}</option>`).join('')}</select></label></div>
        <div class="iv-grid">${list.map(r=>`<div class="iv-card iv-role" style="border-top:4px solid ${r.color}">
          <h3><span class="dot" style="background:${r.color}"></span>${esc(r.name_ar)} <span class="en">${esc(r.name_en)}</span></h3>
          <div class="iv-mute">يرفع إلى: ${esc(r.reports_to_ar)} · الدورية: ${esc(r.cadence)} · الموديل: ${esc(r.model)}</div>
          <p style="margin:8px 0">${esc(r.summary_ar)}</p>
          <b>المسؤوليات</b><ul style="margin:4px 0 8px;padding-inline-start:18px">${r.responsibilities_ar.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>
          <b>المهام الوظيفية</b><div class="iv-tw"><table class="iv-t"><thead><tr><th>الدورية</th><th>المهمة</th><th>المصدر</th><th>المخرج</th></tr></thead><tbody>
          ${r.duties.map(d=>`<tr><td style="white-space:nowrap">${esc(d.freq)}</td><td>${esc(d.task_ar)}</td><td>${esc(d.source)}</td><td><code>${esc(d.output)}</code></td></tr>`).join('')}</tbody></table></div>
          <div style="margin-top:8px"><b>مؤشرات الأداء:</b> ${(r.kpis_ar||[]).map(k=>`<span class="chip">${esc(k)}</span>`).join('')}</div>
          ${r.tabs&&r.tabs.length?`<div style="margin-top:4px"><b>افتح التاب:</b> ${tabChips(r)}</div>`:''}</div>`).join('')}</div>`;
      body.querySelector('#iv-who').onchange=e=>{who=e.target.value;render()};
    }
    else if(sub==='fi'){
      body.innerHTML = findings.length ? `<div class="iv-card iv-tw"><table class="iv-t"><thead><tr><th>الدرجة</th><th>الموظف</th><th>الملاحظة</th><th>المبلغ</th><th>المعرّف</th></tr></thead><tbody>
        ${findings.map(f=>`<tr><td><span class="sev ${f.severity}">${SEVN[f.severity]||esc(f.severity)}</span></td><td>${esc(f.role_ar)}</td><td><b>${esc(f.title_ar)}</b><div class="iv-mute">${esc(f.detail_ar||'')}</div></td><td>${f.amount!=null?Number(f.amount).toLocaleString('en-US'):''}</td><td><code>${esc(f.id)}</code></td></tr>`).join('')}</tbody></table></div>`
        : `<div class="iv-card iv-mute">لا توجد ملاحظات بعد — تظهر هنا بعد أول تشغيل لإدارة المخازن (مثلاً: «شغّل إدارة المخازن لشهر أكتوبر»).</div>`;
    }
    else if(sub==='sm') body.innerHTML = `<div class="iv-card">${P&&P.summary_html?P.summary_html:'<span class="iv-mute">لا يوجد ملخص بعد.</span>'}</div>`;
    else if(sub==='wh'){ body.innerHTML = `<iframe ${window.INV_OFFICE_HTML?'':'src="inv-office.html"'} title="المستودع 3D" loading="lazy"></iframe>
      <div class="iv-mute" style="margin-top:6px">أزرار التكبير والتحريك أسفل يمين المشهد، و⤢ لملاءمة الشاشة · اضغط على أي موظف لعرض وصفه.</div>`;
      if(window.INV_OFFICE_HTML){ const fr=body.querySelector('iframe'); if(fr) fr.srcdoc = window.INV_OFFICE_HTML; } }
    body.querySelectorAll('[data-go]').forEach(c=>c.onclick=()=>goTab(c.dataset.go));
  }
  render();
})();
