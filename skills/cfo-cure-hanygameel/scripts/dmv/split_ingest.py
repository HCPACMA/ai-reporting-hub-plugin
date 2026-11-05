import sys, json, subprocess, os
sys.path.insert(0,'/home/claude/work/kit/refresh')
import refresh
BRN={'الرياض':'01','بريدة 1':'02','بريدة 2':'03','رفحاء':'04'}
job, marker = sys.argv[1], sys.argv[2]
s=json.load(open(marker))['result'] if marker.startswith('/') else json.loads(refresh.transcript_find(marker))['result']
L=s.split('\n'); head=[l for l in L[:3]]
parts={b:[] for b in BRN.values()}
for l in L[3:]:
    if l.startswith('| '):
        br=l.strip().strip('|').rsplit('|',1)[1].strip()
        parts[BRN[br]].append(l)
for b,ls in parts.items():
    f=f'/home/claude/work/dmv/stage_{job}_{b}.json'
    json.dump({'result':'\n'.join(head+ls)},open(f,'w'),ensure_ascii=False)
    print(subprocess.run(['python3','refresh.py','ingest',job,b,'--file',f],capture_output=True,text=True,cwd='/home/claude/work/kit/refresh').stdout.strip())
