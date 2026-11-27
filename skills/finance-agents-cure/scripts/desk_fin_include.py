#!/usr/bin/env python3
"""Make sure a Modeling Desk index.html loads the «الإدارة المالية» tab (idempotent).
Adds  <!--FIN-DEPT:start --><script src="fin-dept.js"></script><!--FIN-DEPT:end -->
after <!--TAW-REVIEW:end --> (or before </body>, or at the end). Run it on any local Desk copy before republishing it.
Usage: python desk_fin_include.py <path to index.html>"""
import sys
p = sys.argv[1]; s = open(p, encoding='utf-8').read()
TAG = '<!--FIN-DEPT:start --><script src="fin-dept.js"></script><!--FIN-DEPT:end -->'
if '<!--FIN-DEPT:start -->' in s: print('already included'); sys.exit(0)
for anchor in ('<!--TAW-REVIEW:end -->',):
    if anchor in s: s = s.replace(anchor, anchor + '\n' + TAG, 1); break
else:
    i = s.rfind('</body>'); s = (s[:i] + TAG + '\n' + s[i:]) if i >= 0 else (s + '\n' + TAG + '\n')
open(p, 'w', encoding='utf-8').write(s); print('include added')
