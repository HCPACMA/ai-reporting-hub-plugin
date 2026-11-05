/* ---- Branches & Departments (bilingual EN / عربي, RTL) ---- */
(function(){
  const sec = document.getElementById('sec-dept');
  const DB = DATA.bd, MO = DB.months, N = MO.length, LASTC = DB.last, LAST_I = N-1;
  const EXT = DATA.ext;
  const BR = ['01','02','03','04'];              // the four branches
  const ALLC = ['01','02','03','04','00'];       // + head office
  const NAME = {}; ALLC.forEach(c => NAME[c] = DB.br[c]);
  NAME['00'] = ['Head Office / Unallocated','الإدارة العامة / غير موزع'];
  NAME['ALL'] = ['Group','المجموعة'];
  const COL = {'01':'#146356','02':'#3D6FB5','03':'#C97B3E','04':'#7C6FC9','00':'#7C8E89','ALL':'#10231F'};
  const ARM = ['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
  const ENM = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const yOf = i => +MO[i].slice(0,4), mOf = i => +MO[i].slice(5,7)-1;
  const labEN = i => ENM[mOf(i)]+' '+yOf(i), labAR = i => ARM[mOf(i)]+' '+yOf(i);

  /* ------------------------------ state + language ------------------------------ */
  const ST = {lang:'both', tab:'is', grain:'Y', a:0, b:LASTC, cc:'ALL', cmp:true, alloc:false, view:'branch', mode:'amt'};
  const t  = (en,ar) => ST.lang==='en' ? en : ST.lang==='ar' ? ar : `${en}<span class="bd-ar" dir="rtl">${ar}</span>`;   // block (two lines)
  const ti = (en,ar) => ST.lang==='en' ? en : ST.lang==='ar' ? ar : `${en} · ${ar}`;                                   // inline
  const T  = o => t(o[0],o[1]), TL = o => ti(o[0],o[1]);
  const pick = o => ST.lang==='ar' ? o[1] : o[0];
  const fm = n => (n===null||n===undefined||isNaN(n)) ? '—' : (Math.round(n)===0 ? '0' : Math.round(n).toLocaleString('en-US'));
  const fp = (n,d=1) => (n===null||n===undefined||!isFinite(n)) ? '—' : (n*100).toFixed(d)+'%';
  const fs = (n,d=1) => (n===null||n===undefined||!isFinite(n)) ? '—' : (n>=0?'+':'−')+Math.abs(n*100).toFixed(d)+'%';
  const fx = (n,d=2) => (n===null||n===undefined||!isFinite(n)) ? '—' : n.toFixed(d)+'x';
  const fd = n => (n===null||n===undefined||!isFinite(n)) ? '—' : '\u200E'+(n>=0?'+':'−')+(Math.abs(n)>=1e6 ? (Math.abs(n)/1e6).toFixed(2)+'M' : Math.abs(n)>=1e3 ? (Math.abs(n)/1e3).toFixed(0)+'K' : Math.round(Math.abs(n))+'');
  const fdp = (n,p) => fd(n)+' · '+fs(p);
  const fM = n => (n===null||isNaN(n)) ? '—' : (Math.abs(n)>=1e6 ? (n/1e6).toFixed(2)+'M' : Math.abs(n)>=1e3 ? (n/1e3).toFixed(0)+'K' : Math.round(n)+'');
  const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');

  /* ------------------------------ data access ------------------------------ */
  const LNS = ['cash','cred','oth','cor','ins','ga','ho','zak','dep'];
  const sumLn = (cc,k,a,b) => { const s = DB.ln[cc][k]; let r = 0; for(let i=a;i<=b;i++) r += s[i]; return r; };
  const raw = (cc,a,b) => { const o = {}; LNS.forEach(k => o[k] = sumLn(cc,k,a,b)); return o; };
  const zero = () => { const o = {}; LNS.forEach(k => o[k] = 0); return o; };
  const addTo = (o,p,f=1) => { LNS.forEach(k => o[k] += p[k]*f); return o; };
  function derive(o){
    o.rev = o.cash + o.cred; o.gm = o.rev - o.cor; o.tga = o.ga + o.ins + o.ho;
    o.op = o.gm - o.tga; o.nibz = o.op + o.oth; o.net = o.nibz - o.zak; o.ebitda = o.net + o.dep;
    o.contrib = o.rev - o.cor - o.ins - o.ga;          // branch contribution before head-office costs (G&A is branch-specific)
    return o;
  }
  const revShare = (cc,a,b) => {
    const tot = BR.reduce((s,c) => s + sumLn(c,'cash',a,b) + sumLn(c,'cred',a,b), 0);
    return tot ? (sumLn(cc,'cash',a,b) + sumLn(cc,'cred',a,b)) / tot : 0;
  };
  /* stat(cc, a, b, alloc): window totals for a branch / head office / the group */
  function stat(cc,a,b,alloc){
    let o;
    if(cc === 'ALL'){ o = zero(); ALLC.forEach(c => addTo(o, raw(c,a,b))); }
    else if(cc === '00'){ o = alloc ? zero() : raw('00',a,b); }
    else { o = raw(cc,a,b); if(alloc) addTo(o, raw('00',a,b), revShare(cc,a,b)); }
    return derive(o);
  }
  const winPrev = w => (w.a-12 >= 0) ? {a:w.a-12, b:w.b-12} : null;
  const months = w => w.b - w.a + 1;
  const natSum = (cc,code,a,b) => { const s = DB.nat[cc][code]; if(!s) return 0; let r = 0; for(let i=a;i<=b;i++) r += s[i]; return r; };
  const natCodes = Object.keys(DB.natLab);
  const natOf = (cc,code,a,b) => cc==='ALL' ? ALLC.reduce((s,c)=>s+natSum(c,code,a,b),0) : natSum(cc,code,a,b);

  /* ------------------------------ periods (same grains as the other statements) ------------------------------ */
  function periodOptions(grain){
    const out = [];
    if(grain === 'M') MO.forEach((m,i) => out.push({v:i+':'+i, en:labEN(i)+(i>LASTC?' (open)':''), ar:labAR(i)+(i>LASTC?' (مفتوح)':'')}));
    else if(grain === 'Q'){
      for(let i = 0; i <= LAST_I; i += 3){
        const b = Math.min(i+2, LAST_I), q = Math.floor(mOf(i)/3)+1;
        out.push({v:i+':'+b, en:'Q'+q+' '+yOf(i)+(b>LASTC?' (open)':''), ar:'الربع '+q+' '+yOf(i)+(b>LASTC?' (مفتوح)':'')});
      }
    } else {
      for(let y = 2023; y <= 2026; y++){
        const a = MO.indexOf(y+'-01'); if(a < 0) continue;
        let b = a; while(b+1 <= LASTC && yOf(b+1) === y) b++;
        const partial = mOf(b) < 11;
        out.push({v:a+':'+b, en:(partial ? y+' YTD (Jan–'+ENM[mOf(b)]+')' : 'FY'+y), ar:(partial ? y+' حتى تاريخه (يناير–'+ARM[mOf(b)]+')' : 'السنة المالية '+y)});
        if(yOf(LAST_I) === y && LAST_I > b)
          out.push({v:a+':'+LAST_I, en:y+' YTD incl. '+ENM[mOf(LAST_I)]+' (open, partial)', ar:y+' حتى تاريخه شاملاً '+ARM[mOf(LAST_I)]+' (شهر مفتوح)'});
      }
    }
    return out;
  }
  const winLabel = (a,b) => a===b ? [labEN(a),labAR(a)] : [labEN(a)+' – '+labEN(b), labAR(a)+' – '+labAR(b)];
  const W = () => ({a:ST.a, b:ST.b});

  /* ------------------------------ income-statement rows ------------------------------ */
  /* [key, EN, AR, value(o), weight]  — costs are shown negative, like the statements above */
  const ISR = [
    ['cash','Cash Revenue','الإيرادات النقدية',o=>o.cash,0],
    ['cred','Credit Revenue','الإيرادات الآجلة (تأمين)',o=>o.cred,0],
    ['rev','TOTAL REVENUE','إجمالي الإيرادات',o=>o.rev,2],
    ['cor','Cost of Revenue','تكلفة الإيرادات',o=>-o.cor,0],
    ['gm','Gross Margin','مجمل الربح',o=>o.gm,1],
    ['ga','G&A Expenses','المصروفات العمومية والإدارية',o=>-o.ga,0],
    ['ins','Insurance Co Expenses','مصروفات شركات التأمين',o=>-o.ins,0],
    ['ho','Head Office Expenses','مصروفات الإدارة العامة',o=>-o.ho,0],
    ['tga','Total G&A Expenses (rollup)','إجمالي المصروفات العمومية والإدارية',o=>-o.tga,1],
    ['op','PROFIT FROM OPERATION','الربح من التشغيل',o=>o.op,2],
    ['oth','Total Other Revenue','إجمالي الإيرادات الأخرى',o=>o.oth,0],
    ['nibz','Net Income Before Zakat & TAX','صافي الدخل قبل الزكاة والضريبة',o=>o.nibz,1],
    ['zak','Zakat Expenses','مصروف الزكاة',o=>-o.zak,0],
    ['net','NET INCOME','صافي الدخل',o=>o.net,2],
    ['dep','Memo: Depreciation (add-back)','مذكرة: الإهلاك (إضافة)',o=>o.dep,0],
    ['ebitda','EBITDA','الأرباح قبل الفوائد والضرائب والإهلاك',o=>o.ebitda,1],
  ];
  const rowV = (key,o) => ISR.find(r => r[0]===key)[3](o);
  const delta = (cur,prev) => (prev===null||prev===undefined||!prev) ? null : (cur-prev)/Math.abs(prev);
  const favCls = d => d===null ? '' : d>=0 ? 'bd-up' : 'bd-dn';
