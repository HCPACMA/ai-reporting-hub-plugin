from playwright.sync_api import sync_playwright
import json, re
SCR="/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"; WORK=f"{SCR}/dashboard_askai.html"
src=open(f"{SCR}/feedback/verify_feedback.py",encoding="utf-8").read()
m=re.search(r"def init_script\(.*?\n\"\"\" % \(.*?\)\n",src,re.S); exec(m.group(0))
def run(vp,tag):
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        page=b.new_page(viewport=vp); page.add_init_script(init_script(True,True))
        errs=[]; page.on("pageerror",lambda e:errs.append(str(e))); page.on("console",lambda c:errs.append(c.text) if c.type=='error' and 'ERR_TUNNEL' not in c.text else None)
        page.goto(f"file://{WORK}"); page.wait_for_timeout(1200)
        tabs=page.eval_on_selector_all('.tab-btn[data-tab]','els=>els.map(e=>e.dataset.tab)')
        def counts():
            out={}
            for t in tabs:
                page.locator(f'.tab-btn[data-tab="{t}"]').click(); page.wait_for_timeout(150)
                out[t]=page.locator(f'#panel-{t} tbody tr').count()
            return out
        base=counts()
        print(tag,'columns overstock:',page.eval_on_selector('#tbl-overstock thead','e=>e.innerText.replace(/\\s+/g," ")')[:300])
        for sel,val in (('#gf-st','10'),('#gf-ig','39'),('#gf-pc','6')):
            page.select_option(sel,val); page.wait_for_timeout(300)
            c=counts(); ch={t:(base[t],c[t]) for t in tabs if base[t]!=c[t]}
            print(tag,sel,val,'changed tabs:',ch)
            page.screenshot(path=f"{SCR}/ver28/{tag}_{sel[1:]}.png")
            page.click('#gf-reset'); page.wait_for_timeout(300)
        c=counts(); assert c==base,'reset mismatch'
        # combined + supplier table
        page.select_option('#gf-st','F'); page.wait_for_timeout(300)
        page.locator('.tab-btn[data-tab="vendor"]').click(); page.wait_for_timeout(200)
        print(tag,'vendor top rows (type F):',page.locator('#tbl-vendor-top tbody tr').count(), page.eval_on_selector('#tbl-vendor-top tbody tr','e=>e.innerText.replace(/\\s+/g," ")')[:300])
        print('ERRS',errs[:5]); assert not errs
        b.close()
run({'width':1360,'height':900},'desk'); run({'width':390,'height':844},'mob'); print('OK')
