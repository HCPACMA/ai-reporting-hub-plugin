# -*- coding: utf-8 -*-
"""Apply (or re-apply) the Cure skin to a dashboard HTML file. Idempotent.

usage: python3 apply_cure_skin.py <desk|hr|inv> <file.html> [<file2.html> ...]

The skin is the block between <!--CURE-SKIN:start ...--> and <!--CURE-SKIN:end -->.
If the file already has one it is replaced, otherwise it is inserted before the last </body>
(or appended at the end when the file is a body fragment, e.g. the HR template).
Edit base.css / base.js / app_<k>.css, run build.py, then re-run this.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RX = re.compile(r'<!--CURE-SKIN:start.*?<!--CURE-SKIN:end -->\n?', re.S)

def apply(html, snip):
    if RX.search(html):
        return RX.sub(lambda _: snip, html, count=1)
    i = html.rfind('</body>')
    return html[:i] + snip + html[i:] if i >= 0 else html.rstrip('\n') + '\n' + snip

if __name__ == '__main__':
    k, files = sys.argv[1], sys.argv[2:]
    snip = open(os.path.join(HERE, f'snippet_{k}.html'), encoding='utf-8').read()
    for f in files:
        h = open(f, encoding='utf-8').read()
        n = apply(h, snip)
        open(f, 'w', encoding='utf-8').write(n)
        print('skin', k, '->', f, len(h), '->', len(n))
