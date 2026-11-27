import json, re, pathlib
D=pathlib.Path('.')
for k in ['desk','hr','inv']:
    s=(D/f'snippet_{k}.html').read_text()
    css=re.search(r'<style id="cure-skin">\n(.*)\n</style>',s,re.S).group(1)
    js=re.search(r'<script id="cure-skin-js">\n(.*)\n</script>',s,re.S).group(1)
    out="/* Cure skin v1 — AI Reporting HUB (%s) */\n(function(){if(document.getElementById('cure-skin'))return;var s=document.createElement('style');s.id='cure-skin';s.textContent=%s;document.body.appendChild(s);})();\n%s\n"%(k,json.dumps(css),js)
    (D/f'cure-skin-{k}.js').write_text(out); print(k,len(out))
