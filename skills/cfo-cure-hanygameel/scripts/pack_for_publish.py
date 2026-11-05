# Publish-time packer: gzip+base64 every big DATA.<key> payload and inflate it at load (inline pako). Source Desk stays uncompressed for refresh.py.
# usage: python3 pack_for_publish.py Desk.html Desk_publish.html [min_bytes]
import re, sys, gzip, base64, json
src, dst = sys.argv[1], sys.argv[2]; MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 120000
PAKO = open('/opt/npm-tools/node_modules/pako/dist/pako_inflate.min.js', encoding='utf8').read()
t = open(src, encoding='utf8').read()
n = 0
def rep(m):
    global n
    body = m.group(2)
    if len(body.encode()) < MIN: return m.group(0)
    z = base64.b64encode(gzip.compress(body.encode('utf8'), 9, mtime=0)).decode()
    n += 1
    return f'{m.group(1)}JSON.parse(__inf("{z}"));'
t2 = re.sub(r'^(DATA\.\w+ = )(.*);[ \t]*$', rep, t, flags=re.M)
helper = ('\n' + PAKO + '\nfunction __inf(b){var s=atob(b),u=new Uint8Array(s.length);for(var i=0;i<s.length;i++)u[i]=s.charCodeAt(i);return pako.inflate(u,{to:"string"});}\n')
i = t2.index('\nconst DATA = ')
t2 = t2[:i] + helper + t2[i:]
open(dst, 'w', encoding='utf8').write(t2)
print('packed', n, 'payloads;', len(t.encode()), '->', len(t2.encode()), 'bytes')
