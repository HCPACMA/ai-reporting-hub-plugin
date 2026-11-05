import json,sys,re
from parse import parse
J='/root/.claude/projects/-home-claude/bee4938b-749b-5170-9e80-fa9fe506607a.jsonl'
def find(marker, nth=1):
    hits=[]
    for line in open(J):
        try: o=json.loads(line)
        except: continue
        msg=o.get('message',{})
        c=msg.get('content') if isinstance(msg,dict) else None
        if not isinstance(c,list): continue
        for it in c:
            if isinstance(it,dict) and it.get('type')=='tool_result':
                cc=it.get('content')
                txt=cc if isinstance(cc,str) else ''.join(x.get('text','') for x in cc if isinstance(x,dict)) if isinstance(cc,list) else ''
                if marker in txt: hits.append(txt)
    return hits[-nth] if hits else None
if __name__=='__main__':
    t=find(sys.argv[1])
    if t is None: print('none'); sys.exit()
    open('/tmp/_r.json','w').write(t)
    rows=parse('/tmp/_r.json'); open(sys.argv[2],'w').write('\n'.join(rows)); print(len(rows), rows[0][:100])
