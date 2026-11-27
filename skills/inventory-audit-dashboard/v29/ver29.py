from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
    for vp in ({'width':1360,'height':900},{'width':390,'height':844}):
        page=b.new_page(viewport=vp); errs=[]
        page.on("pageerror",lambda e:errs.append(str(e))); page.on("console",lambda c:errs.append(c.text) if c.type=='error' and 'ERR_' not in c.text and 'Failed to load' not in c.text else None)
        page.goto("file:///home/claude/w/test_v29.html"); page.wait_for_timeout(1500)
        tabs=page.eval_on_selector_all('.tab-btn[data-tab]','els=>els.map(e=>e.dataset.tab)')
        out={}
        for t in tabs:
            page.locator(f'.tab-btn[data-tab="{t}"]').click(); page.wait_for_timeout(120)
            out[t]=page.locator(f'#panel-{t} tbody tr').count()
        print(vp['width'],out)
        page.locator('.tab-btn[data-tab="overview"]').click()
        print(page.inner_text('#lc-kpi')[:400].replace('\n',' | '))
        print(page.inner_text('#lc-title'), '||', page.inner_text('#kpi-row')[:300].replace('\n',' | '))
        page.locator('.tab-btn[data-tab="abcxyz"]').click(); print(page.inner_text('#xyz-kpi-row')[:300].replace('\n',' | '))
        page.select_option('#gf-st','F'); page.wait_for_timeout(300); print('filtered vendor rows')
        print('ERRS',errs[:6])
    b.close()
