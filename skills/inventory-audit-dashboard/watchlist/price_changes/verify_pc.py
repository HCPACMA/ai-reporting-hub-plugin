from playwright.sync_api import sync_playwright
import json, re
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
src = open(f"{SCR}/feedback/verify_feedback.py", encoding="utf-8").read()
m = re.search(r"def init_script\(.*?\n\"\"\" % \(.*?\)\n", src, re.S)
exec(m.group(0))
h = open(WORK, encoding="utf-8").read()
i = h.index('<script id="audit-data" type="application/json">') + len('<script id="audit-data" type="application/json">')
A = json.loads(h[i:h.index('</script>', i)])
P = A['price_changes']; K = P['kpi']; EV = P['events']
N90 = K['events_window']; NALL = len(EV)

def run(viewport, shot=None):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        page = b.new_page(viewport=viewport)
        page.add_init_script(init_script(True, True))
        errs = []
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(f"file://{WORK}"); page.wait_for_timeout(900)
        page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(500)
        assert page.locator('#pc-kpi-row .kpi').count() == 5
        n = page.locator('#tbl-pc tbody tr').count()
        assert n == N90, (n, N90)
        assert page.locator('#pc-count').inner_text().startswith(f'{N90} of {NALL}'), page.locator('#pc-count').inner_text()
        page.select_option('#pc-period', 'all'); page.wait_for_timeout(250)
        assert page.locator('#tbl-pc tbody tr').count() == NALL
        page.select_option('#pc-period', '90')
        page.select_option('#pc-dir', 'up'); page.wait_for_timeout(200)
        assert page.locator('#tbl-pc tbody tr').count() == K['up_window']
        page.select_option('#pc-dir', 'x'); page.wait_for_timeout(200)
        assert page.locator('#tbl-pc tbody tr').count() == K['extreme_window']
        page.select_option('#pc-dir', ''); page.select_option('#pc-minpct', '10'); page.wait_for_timeout(200)
        n10 = sum(1 for e in EV if e['to']['d'] >= K['window_start'] and abs(e['pct']) >= 10)
        assert page.locator('#tbl-pc tbody tr').count() == n10, (page.locator('#tbl-pc tbody tr').count(), n10)
        page.select_option('#pc-minpct', '0')
        page.check('#pc-latest'); page.wait_for_timeout(200)
        nl = sum(1 for e in EV if e['to']['d'] >= K['window_start'] and e['latest'])
        assert page.locator('#tbl-pc tbody tr').count() == nl
        page.uncheck('#pc-latest')
        page.fill('#pc-search', 'PUR01-26-000524'); page.wait_for_timeout(250)
        ns = sum(1 for e in EV if e['to']['d'] >= K['window_start'] and 'pur01-26-000524' in (e['from']['inv']+e['to']['inv']).lower())
        assert page.locator('#tbl-pc tbody tr').count() == ns >= 1, ns
        page.fill('#pc-search', '')
        page.wait_for_timeout(200)
        # default folder: X:\\VOUCHERS_DOCUMENTS\\PI -> links exist out of the box
        assert page.input_value('#pc-base') == 'X:\\VOUCHERS_DOCUMENTS\\PI', page.input_value('#pc-base')
        a0 = page.locator('#tbl-pc a[href^="file:"]').first
        h0 = a0.get_attribute('href'); t0 = a0.get_attribute('title')
        assert h0.startswith('file:///X:/VOUCHERS_DOCUMENTS/PI/PI'), h0
        assert a0.locator('xpath=following-sibling::button').get_attribute('data-copy') == 'X:\\VOUCHERS_DOCUMENTS\\PI\\' + t0
        # clearing the folder -> no anchors, copy-name only
        page.fill('#pc-base', ''); page.press('#pc-base', 'Tab'); page.wait_for_timeout(300)
        assert page.locator('#tbl-pc a[href^="file:"]').count() == 0
        assert page.locator('#tbl-pc .pc-nolink').count() > 0
        assert 'No folder set' in page.locator('#pc-base-note').inner_text()
        # set a UNC folder -> links appear with correct URL
        page.fill('#pc-base', '\\\\fileserver\\scans\\PI'); page.press('#pc-base', 'Tab'); page.wait_for_timeout(400)
        a = page.locator('#tbl-pc a[href^="file:"]').first
        href = a.get_attribute('href'); title = a.get_attribute('title')
        assert href.startswith('file://fileserver/scans/PI/'), href
        assert href.endswith(re.sub(r"^", "", __import__('urllib.parse').parse.quote(title, safe="()-_.!~*'")) ), (href, title)
        c = a.locator('xpath=following-sibling::button').get_attribute('data-copy')
        assert c == '\\\\fileserver\\scans\\PI\\' + title, c
        # web url base
        page.fill('#pc-base', 'https://files.example.org/pi/'); page.press('#pc-base', 'Tab'); page.wait_for_timeout(300)
        h2 = page.locator('#tbl-pc a[target="_blank"]').first.get_attribute('href')
        assert h2.startswith('https://files.example.org/pi/PI-'), h2
        # drive letter
        page.fill('#pc-base', 'D:\\Scans\\PI'); page.press('#pc-base', 'Tab'); page.wait_for_timeout(300)
        h3 = page.locator('#tbl-pc a[target="_blank"]').first.get_attribute('href')
        assert h3.startswith('file:///D:/Scans/PI/'), h3
        # persisted across reload
        page.reload(); page.wait_for_timeout(800)
        page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(400)
        assert page.input_value('#pc-base') == 'D:\\Scans\\PI'
        # copy invoice number
        page.evaluate("navigator.clipboard && (navigator.clipboard.writeText = async t => { window.__clip = t; })")
        page.locator('#tbl-pc .pc-invno .pc-copy').first.click(); page.wait_for_timeout(200)
        assert page.evaluate("window.__clip").startswith('PUR01-26-'), page.evaluate("window.__clip")
        assert 'Copied' in page.locator('#pc-status').inner_text()
        # sort by change
        page.locator('#tbl-pc thead th').nth(4).click(); page.wait_for_timeout(200)
        # existing watch-list intact
        assert page.locator('#wl-kpi-row .kpi').count() == 6
        assert page.locator('#tbl-wl-alerts tbody tr').count() > 0
        # no-scan badge & scan rows
        assert page.locator('#tbl-pc .badge', has_text='no scan attached').count() > 0
        # digest has it
        d = page.evaluate("typeof PC !== 'undefined' ? JSON.stringify(PC.summary()).length : 0")
        assert d > 500
        # csv export
        if shot: page.locator('#pc-kpi-row').scroll_into_view_if_needed(); page.wait_for_timeout(200); page.screenshot(path=shot)
        # other tabs still render
        for t in ('askai','fraud','overview'):
            page.locator(f'.tab-btn[data-tab="{t}"]').click(); page.wait_for_timeout(250)
        real = [e for e in errs if 'font' not in e.lower()]
        assert not real, real
        b.close()
    print('PC OK', viewport)

run({'width':1440,'height':1000}, f"{SCR}/pc/pc_desktop.png")
run({'width':390,'height':844}, f"{SCR}/pc/pc_mobile.png")
