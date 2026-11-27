import json,shutil
W='/home/claude/w'
raw=open(f'{W}/dash_v28_live.html',encoding='utf-8').read()
shutil.copyfile(f'{W}/dash_v28_live.html',f'{W}/dashboard_askai.pre_v29.html')
i=raw.index('<body>')+len('<body>'); j=raw.rindex('</body></html>')
h=raw[i:j].lstrip('\n')
assert h.startswith('<title>'),h[:60]
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
tag='<script id="audit-data" type="application/json">'
si=h.index(tag)+len(tag); ei=h.index('</script>',si)
A=json.load(open(f'{W}/audit_v29.json',encoding='utf-8')); A['dims']=json.load(open(f'{W}/dims_v29.json',encoding='utf-8'))
js=json.dumps(A,ensure_ascii=False,separators=(',',':')); assert '</' not in js
h=h[:si]+js+h[ei:]
rep('<h2 style="font-size:14px;">What changed since the 8 September snapshot</h2><span class="section-note">Every tab now runs on the full live re-extract of 5 October; this compares it with the previous snapshot.</span>',
    '<h2 style="font-size:14px;" id="lc-title">What changed since the previous snapshot</h2><span class="section-note" id="lc-sub">Every tab runs on the full live re-extract; this compares it with the previous snapshot.</span>','lc head')
rep("Overview: live check vs the 8 Sep snapshot","Overview: live check vs the previous snapshot",'lc cmt')
rep("  const sgn = n => (n>0?'+':n<0?'−':'') + fmt0(Math.abs(n));",
"""  const sgn = n => (n>0?'+':n<0?'−':'') + fmt0(Math.abs(n));
  const MON=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const dm = s => (+s.slice(8,10))+' '+MON[+s.slice(5,7)-1];
  const dS = dm(L.snapshot_as_of), dL = dm(L.as_of);
  document.getElementById('lc-title').textContent = 'What changed since the '+dS+' snapshot';
  document.getElementById('lc-sub').textContent = 'Every tab runs on the full live re-extract of '+dL+'; this compares it with the '+dS+' snapshot.';""",'lc dm')
rep("card('Stock value ('+L.as_of.slice(8,10).replace(/^0/,'')+' Oct)'","card('Stock value ('+dL+')'",'c1')
rep("card('Snapshot (8 Sep)'","card('Snapshot ('+dS+')'",'c2')
rep("card('Movement since 8 Sep'","card('Movement since '+dS",'c5')
rep("label:'SKUs (8 Sep)'","label:'SKUs ('+dS+')'",'s1'); rep("label:'SKUs (5 Oct)'","label:'SKUs ('+dL+')'",'s2')
rep("label:'Value 8 Sep'","label:'Value '+dS",'v1',2); rep("label:'Value 5 Oct'","label:'Value '+dL",'v2',2)
rep('All 637 ranked SKUs','All 704 ranked SKUs','xyz title')
open(f'{W}/dashboard_v29.html','w',encoding='utf-8').write(h); print(len(h))
