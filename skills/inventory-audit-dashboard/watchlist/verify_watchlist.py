from playwright.sync_api import sync_playwright
import json, re
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
src = open(f"{SCR}/feedback/verify_feedback.py", encoding="utf-8").read()
m = re.search(r"def init_script\(.*?\n\"\"\" % \(.*?\)\n", src, re.S)
exec(m.group(0))   # reuse the mocked claude.use() (db, user, downloads, sample)

h = open(WORK, encoding="utf-8").read()
i = h.index('<script id="audit-data" type="application/json">') + len('<script id="audit-data" type="application/json">')
A = json.loads(h[i:h.index('</script>', i)])
WLD = A['watchlist']; NAL = len(WLD['alerts']); NSUP = len(WLD['suppliers']); NSOLE = len(WLD['sole_source'])
GAP = round(WLD['kpi']['by_type']['supplier_gap']['sar'])

def run(viewport, with_db=True, can_write=True, full=True, shot=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/opt/pw-browsers/chromium')
        page = browser.new_page(viewport=viewport)
        page.add_init_script(init_script(with_db, can_write))
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(f"file://{WORK}")
        page.wait_for_timeout(900)

        # ---- overview KPI relabel ----
        ov = page.locator('#kpi-row').inner_text()
        assert f"{GAP:,}" in ov, f"overview gap kpi: {ov[-200:]}"
        assert '2,258' not in ov and '2,243' not in ov

        page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(400)
        assert page.locator('#wl-kpi-row .kpi').count() == 6, "wl kpis"
        assert page.locator('#wl-trend svg circle').count() == len(WLD['trend']), "trend points"
        assert page.locator('#tbl-wl-alerts tbody tr').count() == NAL, f"alert rows {page.locator('#tbl-wl-alerts tbody tr').count()} != {NAL}"
        assert page.locator('#tbl-wl-alerts .wlsel').count() == NAL
        assert page.locator('#tbl-wl-suppliers tbody tr').count() == NSUP
        assert page.locator('#tbl-wl-sole tbody tr').count() == NSOLE
        fids = page.eval_on_selector_all('.wlsel', 'els => els.map(e=>e.dataset.fid)')
        assert len(fids) == len(set(fids)) == NAL and all(len(f) <= 200 and all(c.isalnum() or c in '_-.~:@+' for c in f) for f in fids), "fids"
        txt = page.locator('#wl-kpi-row').inner_text()
        assert 'open sar impact' in txt.lower() and 'reviewed' in txt.lower(), txt
        status = page.locator('#wl-status').inner_text()
        if with_db: assert 'saved to this dashboard' in status or 'view-only' in status, status
        else: assert 'not available' in status, status

        if can_write:
            sel = page.locator('#tbl-wl-alerts .wlsel').first
            fid = sel.get_attribute('data-fid')
            sel.select_option('negotiating'); page.wait_for_timeout(300)
            assert sel.get_attribute('data-v') == 'negotiating'
            if with_db:
                d = page.evaluate("(f)=>window.__store.get(f)", fid)
                assert d and d['status'] == 'negotiating' and d['by'] == 'u_me' and d['impact_at'] > 0, d
            assert '1 of' in page.locator('#wl-kpi-row .kpi').nth(5).inner_text(), page.locator('#wl-kpi-row .kpi').nth(5).inner_text()
            # survives re-sort
            page.locator('#tbl-wl-alerts thead th').nth(3).click(); page.wait_for_timeout(200)
            assert page.eval_on_selector(f'.wlsel[data-fid="{fid}"]', 'e=>e.value') == 'negotiating'
            # note
            page.locator(f'.wlnote[data-fid="{fid}"]').click(); page.wait_for_timeout(150)
            assert page.locator('#wl-note-pop').is_visible()
            page.fill('#wl-note-pop textarea', 'Asked supplier for the contract price'); page.click('#wl-note-pop .wl-pop-save'); page.wait_for_timeout(250)
            assert not page.locator('#wl-note-pop').is_visible()
            assert 'has' in page.locator(f'.wlnote[data-fid="{fid}"]').get_attribute('class')
            if with_db: assert page.evaluate("(f)=>window.__store.get(f).note", fid) == 'Asked supplier for the contract price'
            # resolved row leaves the default "open" view; reappears under All
            s2 = page.locator('#tbl-wl-alerts .wlsel').nth(1)
            s2.select_option('resolved'); page.wait_for_timeout(450)
            assert page.locator('#tbl-wl-alerts tbody tr').count() == NAL - 1, "resolved should leave open view"
            page.select_option('#wl-state', 'all'); page.wait_for_timeout(200)
            assert page.locator('#tbl-wl-alerts tbody tr').count() == NAL
            page.select_option('#wl-state', 'closed'); page.wait_for_timeout(200)
            assert page.locator('#tbl-wl-alerts tbody tr').count() == 1
            page.select_option('#wl-state', 'open'); page.wait_for_timeout(200)
            page.select_option('#wl-type', 'price_up'); page.wait_for_timeout(200)
            n_pu = page.locator('#tbl-wl-alerts tbody tr').count()
            assert 0 < n_pu < NAL
            page.select_option('#wl-type', ''); page.fill('#wl-search', 'saline'); page.wait_for_timeout(250)
            assert page.locator('#tbl-wl-alerts tbody tr').count() >= 1
            page.fill('#wl-search', ''); page.wait_for_timeout(200)
            # clearing the status deletes the doc
            page.locator(f'.wlsel[data-fid="{fid}"]').first.select_option(''); page.wait_for_timeout(250)
            if with_db: assert page.evaluate("(f)=>window.__store.has(f)", fid) is False
            if with_db:
                # "still occurring": a resolved review dated before the alert's latest purchase
                al = WLD['alerts'][2]; f3 = re.sub(r'[^A-Za-z0-9_\-.~:@+]', '_', al['id'])[:190]
                page.evaluate("([f,a])=>window.__remote(f,{aid:a,status:'resolved',note:'',by:'u_other',at:'2026-07-01T10:00:00Z',impact_at:1})", [f3, al['id']])
                page.select_option('#wl-state', 'all'); page.wait_for_timeout(300)
                assert 'still occurring' in page.locator('#tbl-wl-alerts').inner_text(), "still occurring badge"
                # "worse since review"
                al4 = WLD['alerts'][3]; f4 = re.sub(r'[^A-Za-z0-9_\-.~:@+]', '_', al4['id'])[:190]
                page.evaluate("([f,a])=>window.__remote(f,{aid:a,status:'ack',note:'',by:'u_other',at:'2026-09-01T10:00:00Z',impact_at:100})", [f4, al4['id']])
                page.wait_for_timeout(300)
                assert 'worse since review' in page.locator('#tbl-wl-alerts').inner_text(), "worse badge"
                page.select_option('#wl-state', 'open'); page.wait_for_timeout(200)
                # export
                page.click('#wl-export'); page.wait_for_timeout(400)
                dl = page.evaluate("window.__dl")
                assert dl and dl['filename'].startswith('price_vendor_watchlist_') and dl['filename'].endswith('.csv'), dl
                assert dl['data'].startswith('﻿alert_id,type') and dl['data'].count('\r\n') == NAL, (dl['data'][:120], dl['data'].count('\r\n'))
                assert 'Hany' in dl['data'] or 'Colleague' in dl['data']
                # failed write reverts
                page.evaluate("window.__failWrites = true")
                s5 = page.locator('#tbl-wl-alerts .wlsel').nth(6)
                s5.select_option('accepted'); page.wait_for_timeout(400)
                assert 'Could not save' in page.locator('#wl-status').inner_text()
                page.evaluate("window.__failWrites = false")
        else:
            assert page.locator('#tbl-wl-alerts .wlsel').first.is_disabled(), "view-only disabled"

        if full:
            # ---- vendor tab reflects the live pull ----
            page.locator('.tab-btn[data-tab="vendor"]').click(); page.wait_for_timeout(250)
            vt = page.locator('#vendor-kpi-row').inner_text()
            assert '4,257,207' in vt and '64 active' in vt, vt
            # ---- fraud tab: Buraydah arrangement is shown as accepted ----
            page.locator('.tab-btn[data-tab="fraud"]').click(); page.wait_for_timeout(300)
            wf = page.locator('#wf-kpi-row').inner_text()
            assert '7 docs' in wf and 'accepted arrangement' in wf, wf
            rt = page.locator('#tbl-wf-routes').inner_text()
            assert rt.count('accepted') == 2, rt
            assert page.locator('#tbl-fraud-sod tbody tr').count() == 498
            for tab, sel_, n in [('rebalance', '#tbl-rebalance tbody tr', 12), ('forecast', '#tbl-forecast-all tbody tr', 50), ('abcxyz', '#tbl-xyz-all tbody tr', 697)]:
                page.locator(f'.tab-btn[data-tab="{tab}"]').click(); page.wait_for_timeout(250)
                assert page.locator(sel_).count() == n, f"{tab} regressed"
            page.locator('.tab-btn[data-tab="purchases"]').click(); page.wait_for_timeout(250)
            assert page.locator('#tbl-matrix tbody tr').count() == len(A['product_supplier_price_matrix'])
            page.locator('.tab-btn[data-tab="board"]').click(); page.wait_for_timeout(300)
            assert f"{GAP:,}" in page.locator('#panel-board').inner_text(), "board gap number"
            page.locator('.tab-btn[data-tab="askai"]').click(); page.wait_for_timeout(250)
            chips = page.locator('.askai-chip')
            if chips.count() > 0:
                chips.first.click(); page.wait_for_timeout(600)
                s = page.evaluate("window.__lastSample") or ''
                assert 'price_vendor_watchlist' in s and 'fraud_review' in s and 'same_person_is_accepted_arrangement' in s, "digest fields"
        if viewport['width'] < 500:
            page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(300)
            sw = page.evaluate("document.documentElement.scrollWidth"); iw = page.evaluate("window.innerWidth")
            assert sw <= 417, f"new horizontal overflow {sw} (baseline from earlier versions: 415, tab strip)"
        if shot:
            page.locator('.tab-btn[data-tab="watch"]').click(); page.wait_for_timeout(300)
            page.locator('#panel-watch').scroll_into_view_if_needed()
            page.screenshot(path=shot.replace('.png', '_top.png'))
            page.locator('#tbl-wl-alerts').scroll_into_view_if_needed(); page.wait_for_timeout(200)
            page.screenshot(path=shot.replace('.png', '_alerts.png'))
        fatal = [e for e in errors if 'net::' not in e and 'ERR_TUNNEL' not in e]
        assert not fatal, f"page errors: {fatal}"
        browser.close()
        print(f"[{viewport} db={with_db} write={can_write}] ALL CHECKS PASSED")

run({"width": 1440, "height": 1000}, shot=f"{SCR}/watch/wl_desktop.png")
run({"width": 390, "height": 844}, shot=f"{SCR}/watch/wl_mobile.png")
run({"width": 1440, "height": 1000}, with_db=False, full=False)
run({"width": 1440, "height": 1000}, with_db=True, can_write=False, full=False)
print("DONE")
