import json, shutil, re
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
RF = f"{SCR}/refresh"
html = open(WORK, "r", encoding="utf-8").read()
orig_len = len(html)
shutil.copyfile(WORK, f"{SCR}/dashboard_askai.pre_refresh.html")

def rep(old, new, label, count=1):
    global html
    assert html.count(old) == count, f"{label}: anchor count={html.count(old)}"
    html = html.replace(old, new)

tag = '<script id="audit-data" type="application/json">'
si = html.index(tag) + len(tag); ei = html.index("</script>", si)
A = json.loads(html[si:ei])
A["watchlist"] = json.load(open(f"{SCR}/watch/live_result.json", encoding="utf-8"))["watchlist"]
A["price_changes"] = json.load(open(f"{SCR}/pc/price_changes.json", encoding="utf-8"))
A["live_check"] = json.load(open(f"{RF}/live_check.json", encoding="utf-8"))
js = json.dumps(A, ensure_ascii=False, separators=(",", ":"))
assert "</" not in js
html = html[:si] + js + html[ei:]

css = """
/* ---------- live check vs snapshot ---------- */
#panel-overview .lc-grid{display:grid; grid-template-columns:1fr 1fr; gap:14px;}
@media (max-width:900px){ #panel-overview .lc-grid{grid-template-columns:1fr;} }
#panel-overview .lc-fine{font-size:12px; color:var(--ink-mute); margin-top:8px; line-height:1.5;}
"""
rep("</style>\n\n<div class=\"app\">", css + "</style>\n\n<div class=\"app\">", "css")

anchor = '<div class="tablewrap"><div class="scrollbody"><table id="tbl-valuation"></table></div></div>\n'
sect = anchor + """        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Live check — stock today against the 8 September snapshot</h2><span class="section-note">Re-priced from the live ERP balances; the other tabs still run on the snapshot.</span></div>
        <section class="kpirow" id="lc-kpi"></section>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-lc"></table></div></div>
        <div class="lc-grid" style="margin-top:14px;">
          <div><h3 style="font-size:13px; margin:0 0 6px;">Biggest value decreases</h3><div class="tablewrap"><div class="scrollbody"><table id="tbl-lc-down"></table></div></div></div>
          <div><h3 style="font-size:13px; margin:0 0 6px;">Biggest value increases</h3><div class="tablewrap"><div class="scrollbody"><table id="tbl-lc-up"></table></div></div></div>
        </div>
        <p class="lc-fine" id="lc-basis"></p>
"""
rep(anchor, sect, "section")
rep("WL.build(); WL.init();\n", "WL.build(); WL.init();\n" + open(f"{RF}/live_block.js", encoding="utf-8").read() + "\n", "js")
rep("      price_vendor_watchlist: WL.summary(),\n", "      price_vendor_watchlist: WL.summary(),\n      live_stock_check: LC.summary(),\n", "digest")
open(WORK, "w", encoding="utf-8").write(html)
print(orig_len, len(html))
