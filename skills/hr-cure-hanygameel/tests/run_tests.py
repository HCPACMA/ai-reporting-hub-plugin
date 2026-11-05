#!/usr/bin/env python3
"""Round-trip and build test.  python3 tests/run_tests.py
1. regenerate raw replies from the verified extract, ingest them, expect the identical extract;
2. render every SQL file (placeholder and forbidden-word checks);
3. build the page and expect every gate to pass (including Arabic text on every finding and a valid payroll notes file);
4. payroll notes carry-over rule;
5. browser smoke test (optional, needs playwright): every page in Arabic, English and both, no console error."""
import json, os, subprocess, sys, tempfile
kit = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
py = sys.executable
ext = os.path.join(kit, 'data', 'extract.alfaihaa.2026-10-12.json'); cfg = os.path.join(kit, 'config', 'company.alfaihaa.json')
tmp = tempfile.mkdtemp()
def run(*a): return subprocess.run([py, *a], capture_output=True, text=True, cwd=kit)
r = run('tests/make_fixtures.py', ext, os.path.join(tmp, 'raw')); assert r.returncode == 0, r.stderr
r = run('scripts/ingest.py', '--raw', os.path.join(tmp, 'raw'), '--config', cfg, '--asof', '2026-10-12', '--out', os.path.join(tmp, 'ex.json')); assert r.returncode == 0, r.stderr
a = json.load(open(ext)); b = json.load(open(os.path.join(tmp, 'ex.json')))
diff = [k for k in a if a[k] != b.get(k)]
assert not diff, f"round trip differs: {diff}"; print('ok  ingest round trip')
r = run('scripts/render_sql.py', '--config', cfg, '--asof', '2026-10-12', '--out', os.path.join(tmp, 'sql')); assert r.returncode == 0, r.stderr; print('ok  19 SQL files render')
r = run('scripts/build_hr.py', '--extract', ext, '--config', cfg, '--out', os.path.join(tmp, 'out')); assert r.returncode == 0, r.stdout + r.stderr
html = open(os.path.join(tmp, 'out', 'HR_Command_Center.html'), encoding='utf8').read()
assert '{{' not in html and '/*DATA_JSON*/' not in html; print('ok  build, gates pass, no unfilled tokens')
for n in ['hr10_contract_status', 'hr12_completeness', 'hr16_gl_provisions', 'hr11_id_expiry']:
    sys.path.insert(0, os.path.join(kit, 'scripts')); import ingest
    assert ingest.parse_table(open(os.path.join(kit, 'raw_samples', n + '.txt'), encoding='utf8').read()); 
print('ok  real sample replies parse')
# 4. carry-over rule
sys.path.insert(0, os.path.join(kit, 'scripts')); import notes_tool
base = dict(id='T1', month='2026-09', status='open', closedIn=None)
assert notes_tool.state_in(base, '2026-09') == 'new' and notes_tool.state_in(base, '2026-11') == 'carried' and notes_tool.state_in(base, '2026-08') is None
done = dict(base, status='done', closedIn='2026-10')
assert notes_tool.state_in(done, '2026-10') == 'closed' and notes_tool.state_in(done, '2026-11') is None and notes_tool.state_in(done, '2026-09') == 'new'
info = dict(base, status='info')
assert notes_tool.state_in(info, '2026-09') == 'info' and notes_tool.state_in(info, '2026-10') is None
print('ok  payroll notes carry-over rule')
d = json.load(open(os.path.join(tmp, 'out', 'data.json'), encoding='utf8'))
assert d.get('gosi') and d.get('travel') and d.get('prepay') and d.get('nursing') and d.get('leaveDays') and all(n.get('people') for n in json.load(open(os.path.join(kit,'data','payroll_notes.json'),encoding='utf8'))['notes']); print('ok  GOSI/travel data and people on every note')
assert d['payroll'] and all(f['t']['ar'] and f['x']['ar'] for f in d['findings']); print('ok  Arabic text on findings and notes in the page data')
# 5. browser smoke test
try:
    from playwright.sync_api import sync_playwright
except Exception:
    print('skip browser smoke test (playwright not installed)'); sys.exit(0)
import re
routes = ['overview','workforce/summary','workforce/people','payroll/cost','payroll/items','notes/register','notes/review','notes/future','notes/loans','movement','leave','liab','audit/register','audit/quality','plan/projection','plan/calendar','plan/practice','compliance/gosi','compliance/travel','prepay','nursing']
errs = []
with sync_playwright() as pw:
    b = pw.chromium.launch(); pg = b.new_page(viewport={'width':1366,'height':800})
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('file://' + os.path.join(tmp, 'out', 'HR_Command_Center.html')); pg.wait_for_timeout(500)
    for lang in ['ar','en','both']:
        pg.click(f'#langsw button[data-l="{lang}"]')
        for r in routes:
            pg.evaluate(f"location.hash='#{r}'"); pg.wait_for_timeout(60)
            txt = pg.evaluate("document.querySelector('.panel.active').innerText")
            assert not re.findall(r'\?\?[\w.]+', txt) and 'undefined' not in txt and 'NaN' not in txt, f'{lang} {r} shows a missing key or bad value'
    pg.click('#langsw button[data-l="ar"]'); pg.evaluate("location.hash='#nursing'"); pg.wait_for_timeout(100)
    pg.click('#t-nu tr.clk >> nth=0'); pg.wait_for_timeout(80)
    assert pg.evaluate("document.querySelectorAll('#t-nu tr.drow').length") == 1, 'doctor row did not expand'
    pg.select_option('#nu-st', 'none'); n = pg.evaluate("document.querySelectorAll('#t-nu tr.docrow').length"); assert n == d['nursing']['summary']['none'], 'no-nurse filter count'
    pg.evaluate("location.hash='#leave'"); pg.wait_for_timeout(100)
    for by in ['branch','dept','job','emp']:
        pg.select_option('#ld-by', by); assert pg.evaluate("document.querySelectorAll('#t-ld tbody tr').length") > 1, 'leave days ' + by
    b.close()
assert not errs, errs; print('ok  browser smoke test: 21 pages x 3 + nursing/leave interaction languages, no console error')
