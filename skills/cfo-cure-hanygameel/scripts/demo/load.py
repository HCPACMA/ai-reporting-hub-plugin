import json,re
H='/home/claude/work/AlFaihaa_Modeling_Desk.html'
def load():
    lines=open(H,encoding='utf-8').read().split('\n')
    blobs={}
    for i,l in enumerate(lines):
        m=re.match(r'^(const DATA|DATA\.(\w+)) = (.*);\s*$',l)
        if m and len(l)>1000:
            key=m.group(2) or 'root'
            blobs[key]=(i,json.loads(m.group(3)))
    return lines,blobs
