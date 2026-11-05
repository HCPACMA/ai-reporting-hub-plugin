# Idempotent: installs the heading/total row highlight (theme tokens + graduated steps for consecutive rows) into the Desk.
import re, os
P = os.environ.get('DESK', '/home/claude/work/AlFaihaa_Modeling_Desk.html')
s = open(P, encoding='utf8').read()
CSS = '''/* HL:css:begin */
:root{
  --hl-h:#3F5F8F; --hl-s:#146356; --hl-t:#0E5A6B; --hl-r:#B07A0A; --hl-base:#FFFFFF;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ --hl-h:#8DB1E6; --hl-s:#4FD1B3; --hl-t:#58C4DD; --hl-r:#E3B04B; --hl-base:#12211D; } }
:root[data-theme="dark"]{ --hl-h:#8DB1E6; --hl-s:#4FD1B3; --hl-t:#58C4DD; --hl-r:#E3B04B; --hl-base:#12211D; }
table tbody tr[data-hl][data-st] > td, table tbody tr[data-hl][data-st] > th{
  --hl-a: calc(var(--hl-a0) + var(--hl-k) * var(--hl-step));
  background: color-mix(in srgb, var(--hl-c) calc(var(--hl-a) * 1%), var(--surface));
  color: color-mix(in srgb, var(--hl-c) 38%, var(--ink));
  font-weight: 700;
  box-shadow: inset 0 1px 0 color-mix(in srgb, var(--hl-c) 38%, transparent), inset 0 -1px 0 color-mix(in srgb, var(--hl-c) 24%, transparent);
  border-top-color: transparent; text-shadow: none;
}
table tbody tr[data-hl="h"]{ --hl-c: var(--hl-h); --hl-a0: 9; --hl-k: 5; }
table tbody tr[data-hl="s"]{ --hl-c: var(--hl-s); --hl-a0: 11; --hl-k: 5; }
table tbody tr[data-hl="t"]{ --hl-c: var(--hl-t); --hl-a0: 15; --hl-k: 6; }
table tbody tr[data-hl="r"]{ --hl-c: var(--hl-r); --hl-a0: 20; --hl-k: 7; }
table tbody tr[data-st="0"]{ --hl-step: 0; } table tbody tr[data-st="1"]{ --hl-step: 1; } table tbody tr[data-st="2"]{ --hl-step: 2; }
table tbody tr[data-st="3"]{ --hl-step: 3; } table tbody tr[data-st="4"]{ --hl-step: 4; }
table tbody tr[data-hl][data-st] > td .bd-d, table tbody tr[data-hl][data-st] > td .i18-en{ color: color-mix(in srgb, var(--hl-c) 25%, var(--ink-muted)); }
table tbody tr[data-hl="r"] > td:first-child, table tbody tr[data-hl="t"] > td:first-child{ border-inline-start: 3px solid var(--hl-c); }
@media print{ table tbody tr[data-hl][data-st] > td{ -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
/* HL:css:end */
'''
JS = '''<script>/* HL:js:begin */
(function(){
  const CL = [['r',/(^|\\s)(res|vr-res|nph-res)(\\s|$)/],['t',/(^|\\s)(tot|bd-tot|cfa-tot|i18-sub)(\\s|$)/],['s',/(^|\\s)(sub|cfa-sub|aud-sub|vr-sub|bd-sub|pk-med|cst-sub|chk-sub)(\\s|$)/],['h',/(^|\\s)(i18-cat|cfa-h|pk-hd|bd-sep|cfa-s)(\\s|$)/]];
  function level(tr){
    if(tr.querySelector(':scope > th') && !tr.querySelector(':scope > td')) return null;
    const c = tr.className || ''; for(const [l,re] of CL) if(re.test(c)) return l;
    const c0 = tr.cells && tr.cells[0] ? tr.cells[0].textContent.trim() : '';
    if(/^(net income|net profit|net result|صافي الدخل|صافي الربح)(?!\\s*(before|قبل))/i.test(c0) && /font-weight:\\s*[67]00/.test(tr.getAttribute('style')||'')) return 'r';
    const st = tr.getAttribute('style') || '';
    if(/font-weight:\\s*700/.test(st)) return 't'; if(/font-weight:\\s*600/.test(st)) return 's';
    return null;
  }
  function pass(){
    document.querySelectorAll('table').forEach(tb => {
      if(tb.closest('.norm-bar')) return;
      tb.querySelectorAll(':scope > tbody').forEach(body => {
        let run = 0;
        for(const tr of body.children){
          if(tr.tagName !== 'TR') continue;
          const l = level(tr);
          if(l){ const st = String(Math.min(run, 4)); if(tr.dataset.hl !== l) tr.dataset.hl = l; if(tr.dataset.st !== st) tr.dataset.st = st; run++; }
          else { if(tr.dataset.hl) { delete tr.dataset.hl; delete tr.dataset.st; } run = 0; }
        }
      });
    });
  }
  let tm = 0; const sched = () => { clearTimeout(tm); tm = setTimeout(pass, 40); };
  new MutationObserver(sched).observe(document.body, {childList:true, subtree:true});
  pass();
})();
/* HL:js:end */</script>
'''
s = re.sub(r'/\* HL:css:begin \*/.*?/\* HL:css:end \*/\n', '', s, flags=re.S)
s = re.sub(r'<script>/\* HL:js:begin \*/.*?/\* HL:js:end \*/</script>\n', '', s, flags=re.S)
a = '/* NORM:css:end */\n'; assert a in s; s = s.replace(a, a + CSS, 1)
s = s.rstrip('\n') + '\n' + JS
open(P, 'w', encoding='utf8').write(s); print('hl installed', len(s))
