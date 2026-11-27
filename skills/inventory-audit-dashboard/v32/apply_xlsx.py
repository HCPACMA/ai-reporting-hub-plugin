import sys,re
SRC,OUT=sys.argv[1],sys.argv[2]
h=open(SRC,encoding='utf-8').read()
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
JS=r'''window.__xlsxBytes = function(headers, rows, sheetName){
  const enc=new TextEncoder(); const esc=s=>String(s).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g,'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const col=n=>{let s='';n++;while(n>0){const m=(n-1)%26;s=String.fromCharCode(65+m)+s;n=Math.floor((n-1)/26);}return s;};
  const all=[headers].concat(rows), widths=headers.map((_,j)=>Math.min(60,Math.max(8,...all.slice(0,400).map(r=>String(r[j]==null?'':r[j]).length+2))));
  let sd='';
  all.forEach((r,i)=>{ sd+=`<row r="${i+1}">`; r.forEach((v,j)=>{ const ref=col(j)+(i+1);
    if(v==null||v==='') return;
    if(i>0&&typeof v==='number'&&isFinite(v)) sd+=`<c r="${ref}"><v>${v}</v></c>`;
    else sd+=`<c r="${ref}" t="inlineStr"${i===0?' s="1"':''}><is><t xml:space="preserve">${esc(v)}</t></is></c>`; }); sd+='</row>'; });
  const last=col(headers.length-1)+all.length;
  const sheet=`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>${widths.map((w,j)=>`<col min="${j+1}" max="${j+1}" width="${w}" customWidth="1"/>`).join('')}</cols><sheetData>${sd}</sheetData><autoFilter ref="A1:${last}"/></worksheet>`;
  const nm=esc((sheetName||'Data').replace(/[\[\]\*\?\/\\:]/g,' ').slice(0,31));
  const files=[['[Content_Types].xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'],
   ['_rels/.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'],
   ['xl/workbook.xml',`<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="${nm}" sheetId="1" r:id="rId1"/></sheets></workbook>`],
   ['xl/_rels/workbook.xml.rels','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'],
   ['xl/styles.xml','<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="10"/><name val="Arial"/></font><font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF0F6E5C"/></patternFill></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'],
   ['xl/worksheets/sheet1.xml',sheet]];
  const T=new Uint32Array(256); for(let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xEDB88320^(c>>>1):c>>>1;T[n]=c>>>0;}
  const crc=b=>{let c=0xFFFFFFFF;for(let i=0;i<b.length;i++)c=T[(c^b[i])&255]^(c>>>8);return (c^0xFFFFFFFF)>>>0;};
  const parts=[],cen=[];let off=0; const u16=n=>[n&255,(n>>8)&255], u32=n=>[n&255,(n>>>8)&255,(n>>>16)&255,(n>>>24)&255];
  files.forEach(([name,txt])=>{ const nb=enc.encode(name), d=enc.encode(txt), c=crc(d);
    const lh=new Uint8Array([0x50,0x4B,3,4,...u16(20),...u16(0x0800),...u16(0),...u16(0),...u16(0x21),...u32(c),...u32(d.length),...u32(d.length),...u16(nb.length),...u16(0)]);
    parts.push(lh,nb,d);
    cen.push(new Uint8Array([0x50,0x4B,1,2,...u16(20),...u16(20),...u16(0x0800),...u16(0),...u16(0),...u16(0x21),...u32(c),...u32(d.length),...u32(d.length),...u16(nb.length),...u16(0),...u16(0),...u16(0),...u16(0),...u32(0),...u32(off)]),nb);
    off+=lh.length+nb.length+d.length; });
  const cs=cen.reduce((a,b)=>a+b.length,0);
  const eocd=new Uint8Array([0x50,0x4B,5,6,...u16(0),...u16(0),...u16(files.length),...u16(files.length),...u32(cs),...u32(off),...u16(0)]);
  return new Blob(parts.concat(cen,[eocd]),{type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
};
window.__saveXlsx = async function(filename, headers, rows, sheetName){
  let cap=null; try{ cap=await window.claude.use('downloads'); }catch(e){}
  if(!cap){ alert('Downloads are not available in this view.'); return; }
  try{ await cap.save({filename:filename, data:window.__xlsxBytes(headers,rows,sheetName)}); }
  catch(e){ if(!e||e.code!=='declined') alert('The download could not be saved ('+((e&&e.code)||'error')+').'); }
};
window.__csvTextToXlsx = async function(filename, csvText, sheetName){
  const t=csvText.replace(/^﻿/,''), rows=[]; let row=[],f='',q=false;
  for(let i=0;i<t.length;i++){const c=t[i];
    if(q){ if(c==='"'){ if(t[i+1]==='"'){f+='"';i++;} else q=false; } else f+=c; }
    else if(c==='"') q=true; else if(c===',') {row.push(f);f='';} else if(c==='\n'||c==='\r'){ if(c==='\r'&&t[i+1]==='\n') i++; row.push(f);f='';rows.push(row);row=[]; } else f+=c; }
  if(f!==''||row.length){row.push(f);rows.push(row);}
  const conv=v=>(/^-?\d+(\.\d+)?$/.test(v)&&!/^-?0\d/.test(v)&&v.length<16)?parseFloat(v):v;
  await window.__saveXlsx(filename, rows[0]||[], rows.slice(1).map(r=>r.map(conv)), sheetName);
};
window.__csv = function(rows, cols, name){
  window.__saveXlsx(name.replace(/\.csv$/i,'.xlsx'), cols.map(c=>c[1]), rows.map(r=>cols.map(c=>{const v=r[c[0]]; return Array.isArray(v)?v.join(' '):(typeof v==='boolean'?(v?'yes':''):(v==null?'':v));})), name.replace(/\.csv$/i,'').replace(/_/g,' '));
};'''
# replace the earlier __csv definition
a=h.index('window.__csv = window.__csv || function(rows, cols, name){')
b=h.index('\n};\n',a)+4
h=h[:a]+JS+'\n'+h[b:]
# valerr local csv -> delegate
a=h.index('  function csv(rows, cols, name){')
b=h.index('\n  }\n',a)+5
h=h[:a]+"  function csv(rows, cols, name){ window.__csv(rows, cols, name); }\n"+h[b:]
# existing csv-string exports -> xlsx
n=0
def sub(m):
    global n; n+=1
    return f"await window.__csvTextToXlsx({m.group(1)}'.xlsx', lines.join('\\r\\n'), {m.group(1)}'');"
pat=re.compile(r"await dlCap\.save\(\{filename:('[^']*'(?:\+[^+]*?)?)\+'\.csv', data:'﻿'\+lines\.join\('\\r\\n'\)\}\);")
h2=pat.sub(lambda m:f"await window.__csvTextToXlsx({m.group(1)}+'.xlsx', lines.join('\\r\\n'), 'Export');",h); 
cnt=len(pat.findall(h)); h=h2
print('replaced existing',cnt)
h=h.replace('Download (CSV)','Download (Excel)').replace('Download reviews (CSV)','Download reviews (Excel)')
open(OUT,'w',encoding='utf-8').write(h); print(len(h))
