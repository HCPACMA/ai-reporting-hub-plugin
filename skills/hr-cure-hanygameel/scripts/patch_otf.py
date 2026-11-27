import os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p=os.path.join(root,'scripts','build_hr.py'); s=open(p,encoding='utf-8').read()
if "D['otf']" not in s:
    a="    except Exception as _e: print('overtime review not attached:', _e)\n"
    assert a in s
    s=s.replace(a,a+"""    try:
        _of = sorted(_g.glob(os.path.join(KIT, 'data', 'overtime_feas.*.json')))
        if _of: D['otf'] = json.load(open(_of[-1], encoding='utf8'))
    except Exception as _e: print('overtime feasibility not attached:', _e)
""",1)
    open(p,'w',encoding='utf-8').write(s)
p=os.path.join(root,'templates','hr_command_center.template.html'); t=open(p,encoding='utf-8').read()
if 'id="p-notes-otf"' in t: print('already patched'); sys.exit(0)
panel='''<section class="panel" id="p-notes-otf">
  <h2 id="otf-h"></h2>
  <p class="lead" id="otf-lead"></p>
  <div class="grid kpis" id="kpi-otf"></div>
  <div class="card mt">
    <div class="nctl">
      <label><span id="otf-fb"></span><select id="otf-br"></select></label>
      <label><span id="otf-fv"></span><select id="otf-v"></select></label>
      <label><span id="otf-fd"></span><input type="number" id="otf-d" min="0" max="100" step="1" value="35" style="width:70px"></label>
      <label><span id="otf-fl"></span><input type="checkbox" id="otf-l"></label>
      <label><span id="otf-fs"></span><input type="checkbox" id="otf-s"></label>
      <label><span id="otf-fq"></span><input type="search" id="otf-q"></label>
      <button class="btn sm" id="otf-xl" type="button" data-ui="xl.btn"></button>
      <button class="btn sm" id="otf-pdf" type="button">PDF</button>
    </div>
    <div class="scroll v"><table class="cmp" id="t-otf"></table></div>
    <div class="note" id="otf-un"></div>
  </div>
  <div class="card mt" id="otf-reco"></div>
  <div class="note" id="otf-note"></div>
</section>

'''
def rep(a,b):
    global t
    assert a in t, a[:60]
    t=t.replace(a,b,1)
rep('<section class="panel" id="p-notes-ot">',panel+'<section class="panel" id="p-notes-ot">')
rep("['ot','nav.nt.ot'],","['ot','nav.nt.ot'],['otf','nav.nt.otf'],")
rep("d('nav.nt.ot','Overtime review','مراجعة الإضافي');","d('nav.nt.ot','Overtime review','مراجعة الإضافي');d('nav.nt.otf','Overtime feasibility','جدوى الإضافي');")
rep("if(!D.sset)NAV.forEach(","if(!D.otf)NAV.forEach(function(g){if(g.id==='notes')g.s=g.s.filter(function(x){return x[0]!=='otf'})});\nif(!D.sset)NAV.forEach(")
js=open(os.path.join(root,'scripts','otf_block.js'),encoding='utf-8').read()
i=t.index("function buildAll(){"); t=t[:i]+js+t[i:]
rep("buildSS();buildPrepay();","buildSS();buildOTF();buildPrepay();")
rep("wireSS();\n","wireSS();wireOTF();\n")
open(p,'w',encoding='utf-8').write(t); print('patched')
