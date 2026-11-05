import re
P='/home/claude/work/AlFaihaa_Modeling_Desk.html'
import shutil; shutil.copy('/tmp/claude-0/-home-claude/bee4938b-749b-5170-9e80-fa9fe506607a/scratchpad/desk_v39_backup.html',P)
s=open(P,encoding='utf8').read()
blob=open('/home/claude/work/bd/data_bd.json',encoding='utf8').read().strip()
# 1 data
line='DATA.bd = '+blob+';'
if '\nDATA.bd = ' in s:
    s=re.sub(r'\nDATA\.bd = .*;\n','\n'+line.replace('\\','\\\\')+'\n',s,count=1)
else:
    i=s.index('\nDATA.ujv = '); j=s.index('\n',i+1)
    s=s[:j+1]+line+'\n'+s[j+1:]
# 2 css
css=open('/home/claude/work/bd/bd.css').read()
a='/* ---- Branches & Departments (bilingual, RTL) ---- */'
if a in s:
    i=s.index(a); j=s.index('@media (max-width:760px){ #sec-dept .bd-t{min-width:560px} }',i)+len('@media (max-width:760px){ #sec-dept .bd-t{min-width:560px} }')
    s=s[:i]+css.strip()+s[j:]
else:
    m='#sec-costcenter td.num,#sec-dept td.num{white-space:nowrap}'
    s=s.replace(m,m+'\n'+css,1)
# 3 js
js=''.join(open('/home/claude/work/bd/'+f,encoding='utf8').read() for f in ['bd_core.js','bd_ui.js','bd_tabs1.js','bd_tabs2.js','bd_whatif.js','bd_end.js'])
d0='/* ---- Department Assessment ---- */'
o="const sec = document.getElementById('sec-dept');"
n="const sec = document.createElement('div'); sec.id = 'bd-pane-dept'; document.getElementById('sec-dept').appendChild(sec);"
k=s.index(d0); seg_end=s.index('\n/* ',k+20)
seg=s[k:seg_end]; assert o in seg
s=s[:k]+seg.replace(o,n,1)+s[seg_end:]
m0='/* ---------- per-page period strip ---------- */'
assert m0 in s
s=s.replace(m0,js.strip()+'\n\n'+m0,1)
# 5 nav
s=s.replace("{id:'dept', label:'Department Assessment', icon:'⌗', group:'Departments'}","{id:'dept', label:'Branches & Departments · الفروع والأقسام', icon:'⌗', group:'Departments'}")
open(P,'w',encoding='utf8').write(s)
print(len(s))
import subprocess; subprocess.run(['python3','/home/claude/work/norm/apply_ui.py'],check=True)
