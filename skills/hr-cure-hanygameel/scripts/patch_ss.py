import os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p=os.path.join(root,'scripts','build_hr.py'); s=open(p,encoding='utf-8').read()
if "D['sset']" not in s:
    assert "    if salary: D['salary'] = salary\n" in s
    s=s.replace("    if salary: D['salary'] = salary\n","""    if salary: D['salary'] = salary
    try:
        _ss = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'salary_setup.json')
        if os.path.exists(_ss): D['sset'] = json.load(open(_ss, encoding='utf8'))
    except Exception as _e: print('salary setup not attached:', _e)
""",1)
    open(p,'w',encoding='utf-8').write(s)
p=os.path.join(root,'templates','hr_command_center.template.html'); t=open(p,encoding='utf-8').read()
if 'id="p-payroll-setup"' in t: print('already patched'); sys.exit(0)
panel='''<section class="panel" id="p-payroll-setup">
  <h2 id="ss-h"></h2>
  <p class="lead" id="ss-lead"></p>
  <div class="grid kpis" id="kpi-ss"></div>
  <div class="card mt">
    <div class="nctl">
      <label><span id="ss-fa"></span><select id="ss-act"></select></label>
      <label><span id="ss-fo"></span><select id="ss-on"></select></label>
      <label><span id="ss-fn"></span><select id="ss-nat"></select></label>
      <label><span id="ss-fj"></span><select id="ss-job"></select></label>
      <label><span id="ss-fb"></span><select id="ss-br"></select></label>
      <label><span id="ss-fq"></span><input type="search" id="ss-q"></label>
      <button class="btn sm" id="ss-xl" type="button" data-ui="xl.btn"></button>
    </div>
    <div class="scroll v"><table class="cmp" id="t-ss"></table></div>
    <div class="note" id="ss-count"></div>
  </div>
  <div class="note" id="ss-note"></div>
</section>

<section class="panel" id="p-payroll-items">'''
def rep(a,b):
    global t
    assert a in t, a[:60]
    t=t.replace(a,b,1)
rep('<section class="panel" id="p-payroll-items">',panel)
rep("['salaries','nav.pay.sal']]","['salaries','nav.pay.sal'],['setup','nav.pay.setup']]")
rep("d('nav.pay.sal',","d('nav.pay.setup','Salary setup (per employee)','إعداد مرتبات الموظفين');d('nav.pay.sal',")
rep("if(!D.salary)NAV.forEach(","if(!D.sset)NAV.forEach(function(g){if(g.id==='payroll')g.s=g.s.filter(function(x){return x[0]!=='setup'})});\nif(!D.salary)NAV.forEach(")
js=open(os.path.join(root,'scripts','ss_block.js'),encoding='utf-8').read()
i=t.index("function buildAll(){"); t=t[:i]+js+t[i:]
rep("buildSalaries();buildPrepay();","buildSalaries();buildSS();buildPrepay();")
rep("if(SL){[['#sl-br','br']","wireSS();\nif(SL){[['#sl-br','br']")
open(p,'w',encoding='utf-8').write(t); print('patched')
