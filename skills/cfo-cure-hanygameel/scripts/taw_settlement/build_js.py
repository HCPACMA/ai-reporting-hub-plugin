import json,sys
d=open('taw_data.json',encoding='utf-8').read()
s=open('ar-tawuniya.src.js',encoding='utf-8').read()
open('ar-tawuniya.js','w',encoding='utf-8').write('/* data: Tawuniya settlement review (built by build_data.py) */\nwindow.TAW_DATA='+d+';\n'+s)
print('ok')
