from playwright.sync_api import sync_playwright
import json, re
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
src = open(f"{SCR}/feedback/verify_feedback.py", encoding="utf-8").read()
m = re.search(r"def init_script\(.*?\n\"\"\" % \(.*?\)\n", src, re.S); exec(m.group(0))
h = open(WORK, encoding="utf-8").read()
i = h.index('<script id="audit-data" type="application/json">') + 48
A = json.loads(h[i:h.index('</script>', i)])
L = A['live_check']; K = A['price_changes']['kpi']
def run(vp, shot):
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        page = b.new_page(viewport=vp); page.add_init_script(init_script(True, True))
        errs = []; page.on("pageerror", lambda e: errs.append(str(e))); page.on("console", lambda c: errs.append(c.text) if c.type=='error' and 'ERR_TUNNEL' not in c.text else None)
        page.goto(f"file://{WORK}"); page.wait_for_timeout(900)
        assert page.locator('#lc-kpi .kpi').count() == 5
        assert page.locator('#tbl-lc tbody tr').count() == 5
        assert page.locator('#tbl-lc-down tbody tr').count() == 10 and page.locator('#tbl-lc-up tbody tr').count() == 10
        txt = page.locator('#lc-kpi').inner_text(); assert '1,515,833' in txt and '1,632,434' in txt, txt
        page.locator('#lc-kpi').scroll_into_view_if_needed(); page.screenshot(path=shot, full_page=False)
        page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(500)
        assert page.locator('#pc-kpi-row .kpi').count() == 5
        assert page.locator('#tbl-pc tbody tr').count() == K['events_window']
        assert page.locator('#tbl-wl-alerts tbody tr').count() >= 20
        assert '2026-10-03' in page.content()
        assert not errs, errs
        b.close()
run({'width':1360,'height':900}, f"{SCR}/refresh/lc_desktop.png")
run({'width':390,'height':844}, f"{SCR}/refresh/lc_mobile.png")
print('OK')
