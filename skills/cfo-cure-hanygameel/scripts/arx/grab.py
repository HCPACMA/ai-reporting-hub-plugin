import json,sys
J='/root/.claude/projects/-home-claude/bee4938b-749b-5170-9e80-fa9fe506607a.jsonl'
def grab(marker, out):
    hit=None
    for line in open(J):
        if marker in line:
            o=json.loads(line)
            if o.get('type')!='user': continue
            for it in o['message']['content']:
                if isinstance(it,dict) and it.get('type')=='tool_result':
                    cc=it['content']; txt=cc if isinstance(cc,str) else ''.join(x.get('text','') for x in cc if isinstance(x,dict))
                    if marker in txt: hit=txt
    open(out,'w').write(hit); return hit
if __name__=='__main__': grab(sys.argv[1],sys.argv[2]); print('ok')
