from playwright.sync_api import sync_playwright
import json, re
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
src = open(f"{SCR}/feedback/verify_feedback.py", encoding="utf-8").read()
m = re.search(r"def init_script\(.*?\n\"\"\" % \(.*?\)\n", src, re.S); exec(m.group(0))
h = open(WORK, encoding="utf-8").read()
i = h.index('<script id="audit-data" type="application/json">') + 48
A = json.loads(h[i:h.index('</script>', i)])
K = A['price_changes']['kpi']
def run(vp, shot):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        page = b.new_page(viewport=vp); page.add_init_script(init_script(True, True))
        errs = []; page.on("pageerror", lambda e: errs.append(str(e))); page.on("console", lambda c: errs.append(c.text) if c.type=='error' and 'ERR_TUNNEL' not in c.text else None)
        page.goto(f"file://{WORK}"); page.wait_for_timeout(900)
        page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(500)
        assert page.locator('#rv-kpi .kpi').count() == 5
        assert page.locator('#tbl-rv tbody tr').count() == 34, page.locator('#tbl-rv tbody tr').count()
        assert page.locator('#tbl-rv .rvsel').count() == 34
        assert page.locator('#tbl-rv-ex tbody tr').count() == 18
        assert page.locator('#tbl-pc tbody tr').count() == K['events_window'] == 254
        t = page.locator('#rv-kpi').inner_text(); assert '4,257,207' in t and '68,866' in t, t
        assert 'SYNFLORIX' not in page.locator('#tbl-wl-alerts').inner_text().upper()
        assert 'Net of purchase returns' in page.locator('#wl-returns-note').inner_text()
        # status save + persisted + filter
        first = page.locator('#tbl-rv .rvsel').first
        fid = first.get_attribute('data-fid')
        first.select_option('mismatch'); page.wait_for_timeout(300)
        assert 'mismatch' in page.evaluate("JSON.stringify([...window.__store.entries()])"), 'not stored'
        page.select_option('#rv-state', 'mismatch'); page.wait_for_timeout(300)
        assert page.locator('#tbl-rv tbody tr').count() == 1
        page.select_option('#rv-state', ''); page.select_option('#rv-level', 'high'); page.wait_for_timeout(300)
        assert page.locator('#tbl-rv tbody tr').count() == 2, page.locator('#tbl-rv tbody tr').count()
        page.fill('#rv-search', 'synflorix'); page.wait_for_timeout(300)
        assert page.locator('#tbl-rv tbody tr').count() == 1
        page.fill('#rv-search', ''); page.select_option('#rv-level', '')
        # export
        page.click('#rv-export'); page.wait_for_timeout(300)
        dl = page.evaluate("window.__dl && window.__dl.filename"); assert dl and 'purchase_returns' in dl, dl
        # digest has the new key
        assert 'purchase_returns_review' in page.content()
        page.locator('#rv-kpi').scroll_into_view_if_needed(); page.screenshot(path=shot, full_page=False)
        assert not errs, errs
        b.close()
run({'width':1360,'height':900}, f"{SCR}/returns/rv_desktop.png")
run({'width':390,'height':844}, f"{SCR}/returns/rv_mobile.png")
print('OK')
