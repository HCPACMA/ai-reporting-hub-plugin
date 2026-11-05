import sys, json
sys.path.insert(0,'/home/claude/work/kit/refresh'); import refresh
for name, mk in [('gl_oth','104/26000011|JV4-26/00072'), ('gls','JV4-25/00109 | P | 2025-12-31'), ('twin','| JV1-26/02206 | 101/26000401 | JV1-26/02199'), ('fp','1263000:-:149.25:0')]:
    s = refresh.transcript_find(mk); json.dump(json.loads(s), open(name+'.json','w'), ensure_ascii=False); print(name, len(s))
