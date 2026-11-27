
/* ---------- salary setup per employee (Cure screen HRSTFSAL) ---------- */
var SS=D.sset||null,ssS={act:'all',on:'all',nat:'all',job:'all',br:'all',q:'',open:{}};
var SSBR={'00':{en:'HQ and administration',ar:'الإدارة العامة والمقر'},'01':{en:'Riyadh clinic',ar:'مجمع الرياض'},'02':{en:'BUR1',ar:'بريدة 1'},'03':{en:'BUR2',ar:'بريدة 2'},'04':{en:'Rafha',ar:'رفحاء'},'??':{en:'Not recorded',ar:'غير مسجل'}};
function ssNatOk(n,f){return f==='all'||(f==='S'?n===SS.saudi:f==='N'?n!==SS.saudi:n===f)}
function ssNatName(c){var o=SS.nats[c];return o?o:{en:'Code '+c,ar:'رمز '+c}}
function ssJobName(c){var o=SS.jobs[c];return o?o:{en:'Code '+c,ar:'رمز '+c}}
function ssItemName(c){var o=SS.items[String(c)];return o?{en:o.en,ar:o.ar}:{en:'Item '+c,ar:'بند '+c}}
function ssAllow(its){var s=0;its.forEach(function(x){var o=SS.items[String(x[0])];s+=(o&&o.sign==='-')?-x[1]:x[1]});return s}
function ssRows(){var q=(ssS.q||'').toLowerCase();return SS.rows.filter(function(r){
  if(ssS.act==='a'&&!r[5])return false;if(ssS.act==='i'&&r[5])return false;if(ssS.on==='y'&&!r[6])return false;if(ssS.on==='n'&&r[6])return false;
  if(!ssNatOk(r[2],ssS.nat))return false;if(ssS.job!=='all'&&r[3]!==ssS.job)return false;if(ssS.br!=='all'&&r[4]!==ssS.br)return false;
  if(q&&(r[0]+' '+r[1]).toLowerCase().indexOf(q)<0)return false;return true})}
function ssM(v){return Number(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2})}
function ssPill(on,yes,no){return '<span class="pill '+(on?'L':'I')+'">'+TI(on?yes:no)+'</span>'}
function ssDetail(r){var h='<div class="ss-d"><div><b>'+TI({en:'Allowances in the current record',ar:'مفردات المرتب في السجل الحالي'})+'</b>';
  h+=r[18].length?'<table class="cmp">'+r[18].map(function(x){return '<tr><td>'+TI(ssItemName(x[0]))+'</td><td class="num">'+ssM(x[1])+'</td></tr>'}).join('')+'</table>':'<div class="hint">—</div>';
  h+='</div><div><b>'+TI({en:'Earlier salary periods',ar:'مفردات مرتب سابقة'})+'</b>';
  h+=r[19].length?'<table class="cmp"><thead><tr><th>'+TI({en:'From',ar:'من'})+'</th><th>'+TI({en:'To',ar:'إلى'})+'</th><th class="num">'+TI({en:'Basic',ar:'الأساسي'})+'</th><th class="num">'+TI({en:'Daily',ar:'اليومي'})+'</th><th class="num">'+TI({en:'Hourly',ar:'الساعة'})+'</th><th>'+TI({en:'Allowances',ar:'البدلات'})+'</th></tr></thead><tbody>'+r[19].map(function(x){return '<tr><td class="mono">'+esc(x[0])+'</td><td class="mono">'+esc(x[1]||'—')+'</td><td class="num">'+ssM(x[2])+'</td><td class="num">'+ssM(x[3])+'</td><td class="num">'+ssM(x[4])+'</td><td class="hint">'+x[5].map(function(y){return TI(ssItemName(y[0]))+' '+ssM(y[1])}).join(' · ')+'</td></tr>'}).join('')+'</tbody></table>':'<div class="hint">'+TI({en:'No earlier periods in the program',ar:'لا توجد فترات سابقة في البرنامج'})+'</div>';
  return h+'</div></div>'}
function buildSS(){if(!SS)return;
  $('#ss-h').innerHTML=TI({en:'Salary setup per employee',ar:'إعداد مرتبات الموظفين'});
  $('#ss-lead').innerHTML=TI({en:'The current record of the Cure screen Employee Salary Setup (HRSTFSAL) for every employee: basic, daily and hourly rate, insurance basis, allowances, the GOSI shares of the last payroll, entry notes and the earlier salary periods (click a row).',ar:'السجل الحالي من شاشة إعداد مرتبات الموظفين في Cure (HRSTFSAL) لكل موظف: الأساسي والراتب اليومي وراتب الساعة والأساسي التأميني والبدلات وحصص التأمينات في آخر مسير وملاحظات الدخول والفترات السابقة للمرتب (اضغط على الصف).'});
  [['ss-fa',{en:'Status',ar:'الحالة'}],['ss-fo',{en:'On the job',ar:'على رأس العمل'}],['ss-fn',{en:'Nationality',ar:'الجنسية'}],['ss-fj',{en:'Profession',ar:'المهنة'}],['ss-fb',{en:'Branch',ar:'الفرع'}],['ss-fq',{en:'Code or name',ar:'كود أو اسم'}]].forEach(function(x){$('#'+x[0]).innerHTML=TI(x[1])});
  var rr=ssRows(),on=rr.filter(function(r){return r[6]}).length,act=rr.filter(function(r){return r[5]}).length;
  var avg=rr.length?rr.reduce(function(a,r){return a+r[10]},0)/rr.length:0,pk=rr.reduce(function(a,r){return a+r[10]+ssAllow(r[18])},0);
  kpi('#kpi-ss',[{l:{en:'Employees shown',ar:'الموظفون المعروضون'},v:rr.length},{l:{en:'Active record',ar:'نشط'},v:act},{l:{en:'On the job',ar:'على رأس العمل'},v:on},{l:{en:'Average basic (SAR)',ar:'متوسط الأساسي (ريال)'},v:Math.round(avg)},{l:{en:'Total package (SAR)',ar:'إجمالي الحزمة (ريال)'},v:Math.round(pk)}]);
  fillSelect('#ss-act',[['all',uo('mva.all')],['a',{en:'Active',ar:'نشط'}],['i',{en:'Inactive',ar:'غير نشط'}]],ssS.act);
  fillSelect('#ss-on',[['all',uo('mva.all')],['y',{en:'On the job',ar:'على رأس العمل'}],['n',{en:'Not on the job',ar:'ليس على رأس العمل'}]],ssS.on);
  var nm=Object.keys(SS.nats).sort(function(a,b){return TI(ssNatName(a))<TI(ssNatName(b))?-1:1});
  fillSelect('#ss-nat',[['all',uo('mva.all')],['S',{en:'Saudi',ar:'سعودي'}],['N',{en:'Non-Saudi',ar:'غير سعودي'}]].concat(nm.map(function(k){return [k,ssNatName(k)]})),ssS.nat);
  var jb=Object.keys(SS.jobs).sort(function(a,b){return TI(ssJobName(a))<TI(ssJobName(b))?-1:1});
  fillSelect('#ss-job',[['all',uo('mva.all')]].concat(jb.map(function(k){return [k,ssJobName(k)]})),ssS.job);
  fillSelect('#ss-br',[['all',uo('mva.all')]].concat(SS.brs.map(function(k){return [k,SSBR[k]||{en:'Branch '+k,ar:'فرع '+k}]})),ssS.br);
  renderSS()}
function renderSS(){if(!SS)return;var rr=ssRows();
  var th=[['Code','الكود'],['Name','الاسم'],['Nationality','الجنسية'],['Profession','المهنة'],['Branch','الفرع'],['Status','الحالة'],['On the job','على رأس العمل'],['Contract end','نهاية العقد'],['Record from','بداية السجل'],['Basic','الأساسي'],['Insurance basic','الأساسي التأميني'],['Daily','اليومي'],['Hourly','الساعة'],['Allowances','البدلات'],['Package','الحزمة'],['Company share','حصة الشركة'],['Staff share','حصة الموظف'],['Entry notes','ملاحظات الدخول']].map(function(x){return '<th>'+TI({en:x[0],ar:x[1]})+'</th>'}).join('');
  var h='<thead><tr>'+th+'</tr></thead><tbody>'+rr.map(function(r){var al=ssAllow(r[18]),k=r[0],open=ssS.open[k];
    return '<tr class="ss-r" data-k="'+esc(k)+'" style="cursor:pointer"><td class="mono">'+esc(k)+'</td><td>'+esc(r[1])+'</td><td>'+TI(ssNatName(r[2]))+'</td><td>'+TI(ssJobName(r[3]))+'</td><td>'+TI(SSBR[r[4]]||{en:r[4],ar:r[4]})+'</td><td>'+ssPill(r[5],{en:'Active',ar:'نشط'},{en:'Inactive',ar:'غير نشط'})+'</td><td>'+ssPill(r[6],{en:'Yes',ar:'نعم'},{en:'No',ar:'لا'})+(r[7]?'<div class="hint">'+TI({en:'Separated',ar:'منتهي'})+'</div>':'')+'</td><td class="mono">'+esc(r[8]||'—')+'</td><td class="mono">'+esc(r[9])+'</td><td class="num">'+ssM(r[10])+'</td><td class="num">'+ssM(r[11])+'</td><td class="num">'+ssM(r[12])+'</td><td class="num">'+ssM(r[13])+'</td><td class="num">'+ssM(al)+'</td><td class="num"><b>'+ssM(r[10]+al)+'</b></td><td class="num">'+ssM(r[15])+'</td><td class="num">'+ssM(r[16])+'</td><td class="cc">'+esc(r[17]||'')+'</td></tr>'+(open?'<tr class="ss-x"><td colspan="18">'+ssDetail(r)+'</td></tr>':'')}).join('')+'</tbody>';
  $('#t-ss').innerHTML=rr.length?h:'<tbody><tr><td><div class="empty">—</div></td></tr></tbody>';
  $('#ss-count').textContent=rr.length+' / '+SS.rows.length;
  $('#ss-note').innerHTML=TI({en:'Active = the employee has a contract with status A. On the job = current contract with status A and not separated. Allowances are those saved on the salary record; the company and staff shares come from the latest payroll of the employee. Data to '+SS.asof+'.',ar:'نشط = للموظف عقد حالته A. على رأس العمل = العقد الحالي بحالة A وغير منتهي الخدمة. البدلات هي المسجلة على سجل المرتب، وحصتا الشركة والموظف من آخر مسير للموظف. البيانات حتى '+SS.asof+'.'})}
function exportSS(){var rr=ssRows(),ic={};rr.forEach(function(r){r[18].forEach(function(x){ic[x[0]]=1})});var codes=Object.keys(ic).map(Number).sort(function(a,b){return a-b});
  var H=[XL('Code','الكود'),XL('Name','الاسم'),XL('Nationality','الجنسية'),XL('Profession','المهنة'),XL('Branch','الفرع'),XL('Status','الحالة'),XL('On the job','على رأس العمل'),XL('Contract end','نهاية العقد'),XL('Record from','بداية السجل'),XL('Basic','الأساسي'),XL('Insurance basic','الأساسي التأميني'),XL('Daily','اليومي'),XL('Hourly','الساعة')].concat(codes.map(function(c){return pickL(ssItemName(c))})).concat([XL('Allowances','البدلات'),XL('Package','الحزمة'),XL('Company share','حصة الشركة'),XL('Staff share','حصة الموظف'),XL('Entry notes','ملاحظات الدخول')]);
  var A=[H].concat(rr.map(function(r){var m={};r[18].forEach(function(x){m[x[0]]=x[1]});var al=ssAllow(r[18]);return [r[0],r[1],pickL(ssNatName(r[2])),pickL(ssJobName(r[3])),pickL(SSBR[r[4]]||{en:r[4],ar:r[4]}),r[5]?XL('Active','نشط'):XL('Inactive','غير نشط'),r[6]?XL('Yes','نعم'):XL('No','لا'),r[8]||'',r[9],{v:r[10],s:'amt'},{v:r[11],s:'amt'},{v:r[12],s:'amt'},{v:r[13],s:'amt'}].concat(codes.map(function(c){return m[c]==null?'':{v:m[c],s:'amt'}})).concat([{v:al,s:'amt'},{v:r[10]+al,s:'amt'},{v:r[15],s:'amt'},{v:r[16],s:'amt'},r[17]||''])}));
  var Bh=[[XL('Code','الكود'),XL('Name','الاسم'),XL('From','من'),XL('To','إلى'),XL('Basic','الأساسي'),XL('Daily','اليومي'),XL('Hourly','الساعة'),XL('Allowances','البدلات')]];
  rr.forEach(function(r){r[19].forEach(function(x){Bh.push([r[0],r[1],x[0],x[1]||'',{v:x[2],s:'amt'},{v:x[3],s:'amt'},{v:x[4],s:'amt'},x[5].map(function(y){return pickL(ssItemName(y[0]))+' '+y[1]}).join(' · ')])})});
  var w=[9,26,14,24,16,10,10,12,12,12,12,10,10].concat(codes.map(function(){return 13})).concat([12,12,12,12,50]);
  saveXlsx('Salary_Setup_'+SS.asof+'.xlsx',[{name:XL('Salary setup','إعداد المرتبات'),rows:A,w:w},{name:XL('Earlier periods','الفترات السابقة'),rows:Bh,w:[9,26,12,12,12,10,10,60]}])}
function wireSS(){if(!SS)return;[['#ss-act','act'],['#ss-on','on'],['#ss-nat','nat'],['#ss-job','job'],['#ss-br','br']].forEach(function(x){$(x[0]).addEventListener('change',function(e){ssS[x[1]]=e.target.value;buildSS()})});
  $('#ss-q').addEventListener('input',function(e){ssS.q=e.target.value;renderSS()});$('#ss-xl').addEventListener('click',exportSS);
  $('#t-ss').addEventListener('click',function(e){var tr=e.target.closest&&e.target.closest('tr.ss-r');if(!tr)return;var k=tr.dataset.k;ssS.open[k]=!ssS.open[k];renderSS()})}
