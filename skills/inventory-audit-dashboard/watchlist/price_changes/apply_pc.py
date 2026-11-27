import json, shutil
SCR = "/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad"
WORK = f"{SCR}/dashboard_askai.html"
PD = f"{SCR}/pc"
html = open(WORK, "r", encoding="utf-8").read()
orig_len = len(html)
shutil.copyfile(WORK, f"{SCR}/dashboard_askai.pre_pc.html")

def rep(old, new, label, count=1):
    global html
    assert html.count(old) == count, f"{label}: anchor count={html.count(old)}"
    html = html.replace(old, new)

# 1. data
start_tag = '<script id="audit-data" type="application/json">'
si = html.index(start_tag) + len(start_tag)
ei = html.index("</script>", si)
A = json.loads(html[si:ei])
A["price_changes"] = json.load(open(f"{PD}/price_changes.json", encoding="utf-8"))
js = json.dumps(A, ensure_ascii=False, separators=(",", ":"))
assert "</" not in js
html = html[:si] + js + html[ei:]

# 2. css
css = """
/* ---------- price changes between invoices ---------- */
#panel-watch .pc-inv{display:inline-flex; flex-direction:column; gap:2px; align-items:flex-start; white-space:normal; min-width:190px;}
#panel-watch .pc-invno{display:inline-flex; align-items:center; gap:4px; font-family:"IBM Plex Mono",monospace; font-size:12px;}
#panel-watch .pc-meta{display:block; font-size:12px; color:var(--ink-2); line-height:1.35;}
#panel-watch .pc-px{font-family:"IBM Plex Mono",monospace; color:var(--ink);}
#panel-watch .pc-attrow{display:flex; flex-wrap:wrap; gap:4px; margin-top:2px;}
#panel-watch .pc-att{display:inline-flex; align-items:center; gap:2px; font-size:12px;}
#panel-watch .pc-att a{color:var(--accent); text-decoration:underline; text-underline-offset:2px;}
#panel-watch .pc-nolink{color:var(--ink-2);}
#panel-watch .pc-copy{appearance:none; border:0; background:none; color:var(--ink-mute); cursor:pointer; font-size:13px; padding:1px 3px; border-radius:4px;}
#panel-watch .pc-copy:hover{color:var(--accent); background:var(--surface-2);}
#panel-watch #pc-base{flex:1 1 280px; min-width:200px; font:inherit; font-size:12.5px; padding:7px 9px; border-radius:7px; border:1px solid var(--border); background:var(--surface); color:var(--ink);}
#panel-watch .pc-chk{display:inline-flex; align-items:center; gap:6px; font-size:12.5px; color:var(--ink-2);}
"""
rep("</style>\n\n<div class=\"app\">", css + "</style>\n\n<div class=\"app\">", "css")

# 3. section inside the watch panel, right after the alerts table
anchor = '<div class="tablewrap"><div class="scrollbody"><table id="tbl-wl-alerts"></table></div></div>\n'
sect = anchor + """        <div class="section-head" style="margin-top:22px;"><h2 style="font-size:14px;">Price changes between invoices — same product, same supplier</h2><span class="section-note" id="pc-note-text"></span></div>
        <div class="callout">Every time a supplier invoices the same product at a different net price from its previous invoice — any size of change, up or down. Each row opens both invoices side by side: the purchase-invoice number, the supplier's own invoice number, and the scanned copy attached to it in the ERP. Use it to confirm a rise was agreed, or that a drop is not a unit-of-measure slip.</div>
        <section class="kpirow" id="pc-kpi-row"></section>
        <div class="filterbar">
          <input type="search" id="pc-search" placeholder="Search product / code / supplier / invoice no…" aria-label="Search price changes">
          <select id="pc-dir" aria-label="Direction"><option value="">All changes</option><option value="up">Increases</option><option value="down">Decreases</option><option value="x">Possible entry errors (3× or more)</option></select>
          <select id="pc-period" aria-label="Period"><option value="90">Newer invoice in the last 90 days</option><option value="all">All of 2026</option></select>
          <select id="pc-minpct" aria-label="Minimum change"><option value="0">Any size</option><option value="2">2% or more</option><option value="5">5% or more</option><option value="10">10% or more</option></select>
          <select id="pc-scan" aria-label="Scans"><option value="">Scanned or not</option><option value="both">Both invoices scanned</option><option value="missing">A scan is missing</option></select>
          <label class="pc-chk"><input type="checkbox" id="pc-latest"> Latest change per product only</label>
          <span class="count" id="pc-count"></span>
          <button type="button" id="pc-export">Download (CSV)</button>
        </div>
        <div class="filterbar">
          <input type="text" id="pc-base" placeholder="Folder of the scanned invoices, e.g. \\\\server\\share\\PI  or  https://…  (saved in this browser only)" aria-label="Folder of scanned invoices" autocomplete="off" spellcheck="false">
          <span class="section-note" id="pc-status"></span>
        </div>
        <p class="wl-fine" id="pc-base-note"></p>
        <div class="tablewrap"><div class="scrollbody"><table id="tbl-pc"></table></div></div>
        <p class="wl-fine">Prices are net per primary unit (unit-of-measure differences between invoices are already normalised) and volume-weighted when one invoice carries the product on several lines. SAR effect = (newer price − earlier price) × units on the newer invoice. “Check entry” marks moves of 3× or more, which are usually a keying or unit slip rather than a real price change. “Superseded” means a later invoice exists for the same product and supplier. Scans exist only from 31 March 2026, so older invoices show “no scan attached”.</p>
"""
rep(anchor, sect, "section")

# 4. js block after the watch-list block, digest
rep("WL.build(); WL.init();\n", "WL.build(); WL.init();\n" + open(f"{PD}/pc_block.js", encoding="utf-8").read() + "\n", "js block")
rep("      price_vendor_watchlist: WL.summary(),\n", "      price_vendor_watchlist: WL.summary(),\n      price_changes_between_invoices: PC.summary(),\n", "digest")

open(WORK, "w", encoding="utf-8").write(html)
print(f"orig_len={orig_len} new_len={len(html)} delta={len(html)-orig_len}")
