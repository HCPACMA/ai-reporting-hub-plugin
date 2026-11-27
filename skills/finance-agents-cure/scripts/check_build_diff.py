#!/usr/bin/env python3
"""Do-not-break check for plugin builds.
Compares two manifest.txt files from .plugin-sync (before / after a build change):
every file packaged before must still be packaged with the same hash, except the
wrapper files that are regenerated on every build.
Usage: python check_build_diff.py <manifest_before.txt> <manifest_after.txt>"""
import sys
WRAPPERS = {'.claude-plugin/plugin.json', '.claude-plugin/marketplace.json', 'README.md'}
def load(p):
    d = {}
    for line in open(p, encoding='utf-8'):
        parts = line.split(None, 2)
        if len(parts) == 3 and not line.startswith('built'): d[parts[2].strip()] = parts[0]
    return d
a, b = load(sys.argv[1]), load(sys.argv[2])
missing = [n for n in a if n not in b]
changed = [n for n in a if n in b and a[n] != b[n] and n not in WRAPPERS]
added = [n for n in b if n not in a]
print(f'before {len(a)} · after {len(b)} · added {len(added)} · changed {len(changed)} · missing {len(missing)}')
for n in missing: print('MISSING', n)
for n in changed: print('CHANGED', n)
for n in added: print('ADDED  ', n)
sys.exit(1 if (missing or changed) else 0)
