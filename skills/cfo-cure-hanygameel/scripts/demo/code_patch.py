PATCHES = [
 ('<title>Al Faihaa Group — Modeling Desk</title>', '<title>Demo Care · Modeling Desk</title>\n<style>.demo-flag{margin-top:10px;padding:7px 9px;border:1px dashed var(--warning);border-radius:8px;background:var(--warning-soft);color:var(--ink);font-size:11.5px;line-height:1.5}.demo-flag b{color:var(--warning)}.demo-badge{position:fixed;right:14px;bottom:12px;z-index:50;padding:5px 11px;border-radius:99px;background:var(--warning);color:#fff;font-size:11.5px;font-weight:700;letter-spacing:.04em;box-shadow:0 2px 8px rgba(0,0,0,.18);pointer-events:none}</style>'),
 ('<div class="eyebrow">Al Faihaa Group</div>', '<div class="eyebrow">Demo Care Group</div>'),
 ('<div class="sub">Consolidated · Riyadh + BUR1 + BUR2 + Rafha</div>\n    </div>',
  '<div class="sub">Consolidated · Riyadh + BUR1 + BUR2 + Rafha</div>\n      <div class="demo-flag"><b>Demo data</b> — all names are fictional and all amounts are scaled; not real figures.<div dir="rtl" lang="ar">بيانات تجريبية — الأسماء وهمية والمبالغ معدّلة؛ ليست أرقامًا حقيقية</div></div>\n    </div>'),
 ('  <main id="main"></main>', '  <main id="main"></main>\n  <div class="demo-badge" aria-hidden="true">DEMO DATA</div>'),
 # prose money
 ('roughly SAR 718K versus SAR 49–58M', 'roughly SAR 4.49M versus SAR 306–363M'),
 ('FY2025 ~SAR&nbsp;3.8M', 'FY2025 ~SAR&nbsp;23.9M'),
 ('fmtSAR(11500000)', 'fmtSAR(71875000)'), ('fmtSAR(16000000)', 'fmtSAR(100000000)'),
 ('pkSAR(564292)', 'pkSAR(3526825)'), ('pkSAR(3653273)', 'pkSAR(22832956)'),
 ('output VAT 422,547.77 vs 422,564.45 (−16.68), input VAT 89,879.00 ties, sales after adjustments 6,207,595.38',
  'output VAT 2,640,923.56 vs 2,641,027.81 (−104.25), input VAT 561,743.75 ties, sales after adjustments 38,797,471.13'),
 ('moved to deferred, 450,000), so live July revenue is 450,000 lower', 'moved to deferred, 2,812,500), so live July revenue is 2,812,500 lower'),
 ('(2025: 73,579,425 vs 73,580,303)', '(2025: 459,871,406 vs 459,876,894)'),
 ('gap ≥ 5,000)', 'gap ≥ 31,250)'),
 ('Debit of 1,000+ that is an exact multiple of 500', 'Debit of 6,250+ that is an exact multiple of 3,125'),
 ('above 3 × average (1,000+)', 'above 3 × average (6,250+)'),
 ('Manual journal of 1,000+ with no attached document', 'Manual journal of 6,250+ with no attached document'),
 ('placeholder="e.g. 4723.75"', 'placeholder="e.g. 29523.44"'),
 ('<option value="2">± 2 SAR</option><option value="10">± 10 SAR</option><option value="100">± 100 SAR</option>',
  '<option value="12.5">± 12.50 SAR</option><option value="62.5">± 62.50 SAR</option><option value="625">± 625 SAR</option>'),
 ('± 2 SAR catches transfers', '± 12.50 SAR catches transfers'),
 ('(± 2 SAR, same company)', '(± 12.50 SAR, same company)'),
 # money thresholds in logic
 ('(tol||1000)', '(tol||6250)'),
 ('resPill(cur.salesRes, 1000)', 'resPill(cur.salesRes, 6250)'),
 ('Math.abs(c.salesRes)/1000, Math.abs(c.outRes)/100, Math.abs(c.inRes)/100', 'Math.abs(c.salesRes)/6250, Math.abs(c.outRes)/625, Math.abs(c.inRes)/625'),
 ('Math.abs(c.salesRes)>1000?', 'Math.abs(c.salesRes)>6250?'),
 ('Math.abs(o.m[ym]-m) >= 5000)', 'Math.abs(o.m[ym]-m) >= 31250)'),
 ('o.cg >= 5000 &&', 'o.cg >= 31250 &&'),
 ('Math.max(1000, 0.01*Math.abs(o.inv))', 'Math.max(6250, 0.01*Math.abs(o.inv))'),
 ('Math.abs(C.eq[y]) > 100)', 'Math.abs(C.eq[y]) > 625)'),
 ('r.r1 > 10000 &&', 'r.r1 > 62500 &&'),
]
import sys; sys.path.insert(0, '/home/claude/work/demo')
from anon import A
PATCHES.append(("'7000911508'", "'" + A.digits('7000911508') + "'"))
PATCHES.append(('  window.__arExportBar(sec);', '  /* AR workbook export disabled in the demo */'))
