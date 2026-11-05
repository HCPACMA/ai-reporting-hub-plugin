#!/usr/bin/env python3
"""Attach employee code, name and letter path(s) to every payroll note.

    python3 scripts/notes_people.py --notes data/payroll_notes.json --index data/letters_index.json \
        --names raw/hr19_names.txt [--admin Admin_Decisions_Review_Sep2026_v2.xlsx] [--settle Settlement_Letters_Review_Sep2026.xlsx]

The letters index (data/letters_index.json) is made on the PC that can see the letters folder:
    {"base_windows": "R:\\\\...\\\\2026", "files": {"<staff no>": ["09-2026/12-09-2026/3002.pdf", ...]}}
Each note gets  people: [{code, name, paths: [{rel, win, lbl}]}]  (first path = the letter the note is about).
Selection: the review workbook row of that employee (folder + file) when it exists, then the newest other letters.
"""
import argparse, json, os, re
import openpyxl


def nz(s):
    return ' '.join(str(s or '').split())


def load_names(*files):
    d = {}
    for f in files:
        if f and os.path.exists(f):
            for line in open(f, encoding='utf8'):
                m = re.search(r'(\d{3,6})\|([^|]+)', line)
                if m:
                    d[m.group(1)] = nz(m.group(2))
    return d


def rows_of(path, sheet):
    if not path or not os.path.exists(path):
        return []
    wb = openpyxl.load_workbook(path, data_only=True)
    return [r for r in wb[sheet].iter_rows(values_only=True) if any(x not in (None, '') for x in r)] if sheet in wb.sheetnames else []


def sort_key(rel):
    m = re.match(r'(\d\d)-(\d{4})/(\d\d)-(\d\d)', rel)
    if not m:
        return (0, 0, 0)
    return (int(m.group(2)), int(m.group(1)), int(m.group(3)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--notes', required=True); ap.add_argument('--index', required=True); ap.add_argument('--names', nargs='*', default=[]); ap.add_argument('--names-json')
    ap.add_argument('--admin'); ap.add_argument('--settle')
    a = ap.parse_args()
    N = json.load(open(a.notes, encoding='utf8')); IX = json.load(open(a.index, encoding='utf8')); files = IX['files']; base = IX['base_windows']
    names = load_names(*a.names)
    if a.names_json and os.path.exists(a.names_json):
        for k, v in json.load(open(a.names_json, encoding='utf8')).items():
            names.setdefault(k, v)
    named = IX.get('named', {})
    # review-workbook hints: (code) -> [(folder, file)]
    hints = {}
    for r in rows_of(a.admin, 'نتائج الخطابات')[1:]:
        if r[2]:
            hints.setdefault(str(r[2]).strip(), []).append((nz(r[0]), nz(r[1])))
    for r in rows_of(a.settle, 'نتائج الخطابات')[1:]:
        if r[1]:
            hints.setdefault(str(r[1]).strip(), []).append((nz(r[3]), str(r[1]).strip() + '.pdf'))
    miss = []
    for n in N['notes']:
        people = []
        for h in n.get('ppl') or []:
            # explicit hint: {code, name?, file?, folder?, none?}  (letters without a staff number, groups, records without a letter)
            c = h.get('code') or '—'; nm = h.get('name') or names.get(c, '')
            paths = []
            if not h.get('none'):
                cand = named.get(h['file'], []) if h.get('file') else sorted(files.get(c, []), key=sort_key, reverse=True)
                if h.get('folder'):
                    cand = [x for x in cand if x.rsplit('/', 1)[0].split('/')[-1].startswith(h['folder'])] or cand
                if h.get('file') and not named.get(h['file']):
                    cand = [x for x in files.get(c, []) if x.rsplit('/', 1)[-1] == h['file']] or cand
                paths = [dict(rel=x, win=base + '\\' + x.replace('/', '\\'), lbl=x.rsplit('/', 1)[-1]) for x in cand[:1 if h.get('file') or h.get('folder') else 3]]
            if not paths:
                miss.append((n['id'], c))
            people.append(dict(code=c, name=nm, paths=paths, **({} if paths else {'nopath': True})))
        if people:
            n['people'] = people
            continue
        codes = re.findall(r'\d{4}', str(n.get('emp') or ''))
        for c in dict.fromkeys(codes):
            cand = sorted(files.get(c, []), key=sort_key, reverse=True)
            cand = [x for x in cand if sort_key(x)[0:2] >= (2026, 8)] or cand
            first = []
            for folder, fn in hints.get(c, []):
                for x in cand:
                    d, b = x.rsplit('/', 1)
                    if b.lower() == fn.lower() and d.split('/')[-1].startswith(folder) and x not in first:
                        first.append(x)
            ordered = first[:1] + [x for x in cand if x not in first[:1]]
            paths = [dict(rel=x, win=base + '\\' + x.replace('/', '\\'), lbl=x.rsplit('/', 1)[-1]) for x in ordered[:3]]
            if not paths:
                miss.append((n['id'], c))
            people.append(dict(code=c, name=names.get(c, ''), paths=paths, **({} if paths else {'nopath': True})))
        n['people'] = people
    N['letters_base'] = base
    json.dump(N, open(a.notes, 'w', encoding='utf8'), ensure_ascii=False, indent=1)
    print('notes', len(N['notes']), 'people', sum(len(n['people']) for n in N['notes']), 'no-path', miss, 'no-name', [(n['id'], p['code']) for n in N['notes'] for p in n['people'] if not p['name']])


if __name__ == '__main__':
    main()
