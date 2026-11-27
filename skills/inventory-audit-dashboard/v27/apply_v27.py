import json,shutil
SCR='/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad'
W=f'{SCR}/dashboard_askai.html'
shutil.copyfile(W,f'{SCR}/dashboard_askai.pre_v27.html')
h=open(W,encoding='utf-8').read()
def rep(old,new,label,count=1):
    global h
    assert h.count(old)==count,(label,h.count(old)); h=h.replace(old,new)
tag='<script id="audit-data" type="application/json">'
si=h.index(tag)+len(tag); ei=h.index('</script>',si)
js=open(f'{SCR}/refresh/audit_v27.json',encoding='utf-8').read(); assert '</' not in js
h=h[:si]+js+h[ei:]
rep('Live check — stock today against the 8 September snapshot','What changed since the 8 September snapshot','lc title')
rep('Re-priced from the live ERP balances; the other tabs still run on the snapshot.','Every tab now runs on the full live re-extract of 5 October; this compares it with the previous snapshot.','lc note')
rep("card('Stock value today', fmtSAR(T.val_live), 'live on-hand × last cost · '+L.as_of)","card('Stock value ('+L.as_of.slice(8,10).replace(/^0/,'')+' Oct)', fmtSAR(T.val_live), 'on-hand × last cost · live extract '+L.as_of)",'lc card1')
rep("card('Snapshot (8 Sep)', fmtSAR(T.val_snap), 'what the other tabs are built on')","card('Snapshot (8 Sep)', fmtSAR(T.val_snap), 'what the previous version was built on')",'lc card2')
rep("'Movement since 9 Sep'","'Movement since 8 Sep'",'lc card5')
rep("label:'SKUs (today)'","label:'SKUs (5 Oct)'",'lc c1'); rep("label:'Value today'","label:'Value 5 Oct'",'lc c2',2)
rep('All 697 ranked SKUs','All 637 ranked SKUs','xyz title')
rep("' pending — dated 1 Oct, inside the monthly cycle'","' pending — current month, inside the monthly cycle'",'tw pending')
open(W,'w',encoding='utf-8').write(h); print(len(h))
