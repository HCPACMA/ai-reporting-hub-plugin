/* ======================================================================
   Deep Analysis · Drivers — what moved revenue, departments, cost and net
   income, year on year or against the previous period. DATA.drv only.
   ====================================================================== */
(function(){
  const sec = document.getElementById('sec-deep'); if(!sec || !DATA.drv) return;
  const X = DATA.drv, M = X.m, N = M.length, OPEN = X.open;
  const BRN = X.br, BRS = ['01','02','03','04'];
  const ACC = X.acc, NAT = X.nat;
  const nat_of = {}; NAT.forEach(g => g[3].forEach(a => nat_of[a] = g[0]));
  const NATL = Object.fromEntries(NAT.map(g => [g[0], g[2]]));
  NATL.other = 'Other expenses';
  const FNL = {COR:'Cost of revenue (clinics)', GA:'General & administrative', INS:'Insurance-company cost', HO:'Head office', X:'Unassigned cost centre'};
  const FNO = ['COR','GA','INS','HO','X'];
  const ZAKAT = '3280005';
  const L = Object.keys(X.ser).map(k => { const [a,cc,f] = k.split('|'); return {a, cc, f, v:X.ser[k]}; });
  const MONL = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const mlab = i => MONL[+M[i].slice(5,7)-1] + ' ' + M[i].slice(0,4);
  const fm = v => (v < 0 ? '−' : '') + fmtM(Math.abs(v)).replace('-','');
  const fmS = v => (v > 0 ? '+' : v < 0 ? '−' : '') + fmtM(Math.abs(v));
  const pct = (c,p) => p ? ((c-p)/Math.abs(p)*100) : null;
  const pctS = v => v === null ? '—' : (v >= 0 ? '+' : '−') + Math.abs(v).toFixed(1) + '%';
  const PP = v => (v*100).toFixed(1) + '%'; PP.pp = true;
  const st = {tab:'rev', cmp:'yoy', cview:'nat', np:false, lfl:true};

  /* ---------------- windows ---------------- */
  function win(){
    let a = M.indexOf(TIMONTHS[TI.a]), b = M.indexOf(TIMONTHS[TI.b]);
    const clipped = a < 0; if(a < 0) a = 0; if(b < 0) b = N-1;
    const len = b - a + 1;
    let c = st.cmp === 'yoy' ? {a:a-12, b:b-12} : {a:a-len, b:b-len};
    if(c.a < 0) c = null;
    return {a, b, c, clipped, open: OPEN !== null && b === OPEN};
  }
  const brOK = cc => TI.cc === 'ALL' || cc === TI.cc;
  const sumR = (arr, a, b) => { let s = 0; for(let i = a; i <= b; i++) s += arr[i] || 0; return s; };

  /* ---------------- ledger lines ---------------- */
  function ledger(a, b){
    const o = {rev:0, orev:0, zak:0, fn:{}, nat:{}, acc:{}, brRev:{}, brFn:{}, mat:{}};
    FNO.forEach(f => o.fn[f] = 0);
    for(const r of L){
      if(!brOK(r.cc)) continue;
      const v = sumR(r.v, a, b); if(!v) continue;
      if(r.a[0] === '4'){
        const isRev = (r.a.startsWith('41') || r.a.startsWith('42')) && r.a !== '4200027';
        if(isRev){ o.rev -= v; o.brRev[r.cc] = (o.brRev[r.cc]||0) - v; } else o.orev -= v;
        o.acc[r.a] = (o.acc[r.a]||0) - v;
      } else if(r.a === ZAKAT){ o.zak += v; }
      else {
        const f = FNO.includes(r.f) ? r.f : 'X', n = nat_of[r.a] || 'other';
        o.fn[f] += v; o.nat[n] = (o.nat[n]||0) + v; o.acc[r.a] = (o.acc[r.a]||0) + v;
        const k = n + '|' + f; o.mat[k] = (o.mat[k]||0) + v;
        const kb = r.cc + '|' + f; o.brFn[kb] = (o.brFn[kb]||0) + v;
      }
    }
    o.cost = FNO.reduce((s,f) => s + o.fn[f], 0);
    o.ni = o.rev + o.orev - o.cost - o.zak;
    return o;
  }
  function accRows(a, b, pred){          // account-level cost rows with nature/function
    const out = {};
    for(const r of L){
      if(!brOK(r.cc) || r.a[0] !== '3' || r.a === ZAKAT || !pred(r)) continue;
      out[r.a] = (out[r.a]||0) + sumR(r.v, a, b);
    }
    return out;
  }
  const accName = a => { const x = ACC[a]; return x ? (x[1] || x[0]) : a; };

  /* ---------------- invoice visits (with like-for-like for the open month) ---------------- */
  function lflFactors(ci){                // per branch|pt|sp: share of the comparison month earned in days 1..openDay
    const A = DATA.anom; if(!A) return null;
    const d0 = new Date(A.d0 + 'T00:00:00Z'), [y,m] = M[ci].split('-').map(Number);
    const first = Math.round((Date.UTC(y, m-1, 1) - d0) / 864e5), dim = new Date(Date.UTC(y, m, 0)).getUTCDate();
    const upto = Math.min(X.openDay, dim), f = {};
    const src = st.np ? A.dailyNP : A.daily;
    for(const k in src){
      const s = src[k]; let part = 0, all = 0;
      for(let d = 0; d < dim; d++){ const v = s[first + d] || 0; all += v; if(d < upto) part += v; }
      f[k] = all ? part / all : upto / dim;
    }
    return {f, upto, dim};
  }
  function visits(a, b, isCmp, W){
    const seg = {}; let lf = null;
    if(isCmp && W.open && st.lfl) lf = lflFactors(b);
    for(const r of X.vis){
      const [br, pt, sp, doc, eps, rev, revNP] = r;
      if(!brOK(br)) continue;
      const R = st.np ? revNP : rev;
      let v = sumR(eps, a, b), x = sumR(R, a, b);
      if(lf){                      // scale the comparison window's last month to the same days
        const k = br + '|' + pt + '|' + sp, fac = lf.f[k] !== undefined ? lf.f[k] : lf.upto / lf.dim;
        v -= eps[b] * (1 - fac); x -= R[b] * (1 - fac);
      }
      if(!v && !x) continue;
      const key = br + '|' + pt + '|' + sp;
      const s = seg[key] || (seg[key] = {br, pt, sp, v:0, r:0, doc:{}});
      s.v += v; s.r += x;
      const d = s.doc[doc] || (s.doc[doc] = {v:0, r:0}); d.v += v; d.r += x;
    }
    return {seg, lf};
  }
  function pvm(cur, cmp){
    let V0 = 0, R0 = 0, V1 = 0, other = 0, mixA = 0, price = 0, R1 = 0, R0all = 0;
    const keys = new Set([...Object.keys(cur), ...Object.keys(cmp)]);
    const cont = [];
    keys.forEach(k => {
      const c = cur[k] || {v:0, r:0}, p = cmp[k] || {v:0, r:0};
      R1 += c.r; R0all += p.r;
      if(c.v > 0 && p.v > 0){ V0 += p.v; R0 += p.r; V1 += c.v; cont.push([c, p]); }
      else other += c.r - p.r;
    });
    const p0 = V0 ? R0 / V0 : 0;
    cont.forEach(([c, p]) => { const p0s = p.r / p.v, p1s = c.r / c.v; mixA += c.v * p0s; price += c.v * (p1s - p0s); });
    const volume = (V1 - V0) * p0, mix = mixA - V1 * p0;
    return {R0:R0all, R1, volume, price, mix, other};
  }

  /* ---------------- chart primitives ---------------- */
  // horizontal waterfall: items [{label, v, kind:'total'|'delta', fav}]
  function waterfall(items, opts={}){
    const rowH = 30, left = opts.left || 280, right = 96, W = opts.W || 860, top = 8, H = top + items.length * rowH + 22;
    let run = 0; const segs = [];
    items.forEach(it => {
      if(it.kind === 'total'){ segs.push({...it, x0:0, x1:it.v}); run = it.v; }
      else { segs.push({...it, x0:run, x1:run + it.v}); run += it.v; }
    });
    let lo = Math.min(0, ...segs.map(s => Math.min(s.x0, s.x1))), hi = Math.max(0, ...segs.map(s => Math.max(s.x0, s.x1)));
    if(opts.zoom && lo >= 0){         // zoom the axis so small deltas are visible between two big totals
      const deltas = segs.filter(s => s.kind !== 'total');
      const dlo = Math.min(...segs.map(s => Math.min(s.x0, s.x1)).filter((_,i) => segs[i].kind !== 'total'), ...deltas.map(s => s.x0));
      lo = Math.max(0, Math.min(dlo, ...segs.filter(s => s.kind === 'total').map(s => s.x1)) * 0.85);
    }
    if(hi === lo) hi = lo + 1;
    const sx = v => left + (v - lo) / (hi - lo) * (W - left - right);
    const ticks = niceTicks(lo, hi, 5);
    let g = ticks.map(t => `<line class="grid" x1="${sx(t)}" x2="${sx(t)}" y1="${top}" y2="${H-18}"/><text x="${sx(t)}" y="${H-4}" font-size="10.5" text-anchor="middle">${fmtM(t)}</text>`).join('');
    if(lo < 0 && hi > 0) g += `<line class="ax" x1="${sx(0)}" x2="${sx(0)}" y1="${top}" y2="${H-18}"/>`;
    segs.forEach((s, i) => {
      const y = top + i * rowH, a = Math.min(s.x0, s.x1), b = Math.max(s.x0, s.x1);
      const xa = sx(Math.max(a, lo)), w = Math.max(2, sx(b) - xa);
      const cls = s.kind === 'total' ? 'b-tot' : (s.fav ? 'b-fav' : 'b-unf');
      const val = s.kind === 'total' ? fm(s.v) : fmS(s.v);
      const tip = `${s.label}: ${s.kind === 'total' ? fmtSARFull(s.v) : (s.v >= 0 ? '+' : '−') + 'SAR ' + Math.round(Math.abs(s.v)).toLocaleString('en-US')}${s.tip ? ' · ' + s.tip : ''}`;
      g += `<g><title>${esc(tip)}</title><rect class="hit" x="0" y="${y}" width="${W}" height="${rowH}"/>` +
           `<text class="lbl" x="${left - 10}" y="${y + rowH/2 + 4}" text-anchor="end">${esc(trunc(s.label, opts.chars || 38))}</text>` +
           `<rect class="${cls}" x="${xa}" y="${y + 6}" width="${w}" height="${rowH - 12}" rx="3"/>` +
           `<text class="val" x="${sx(b) + 6}" y="${y + rowH/2 + 4}">${val}</text></g>`;
      if(i < segs.length - 1){
        const nx = s.kind === 'total' ? s.x1 : s.x1;
        g += `<line class="conn" x1="${sx(nx)}" x2="${sx(nx)}" y1="${y + rowH - 6}" y2="${y + rowH + 6}"/>`;
      }
    });
    return `<div class="dv-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria || 'Waterfall')}">${g}</svg></div>` +
      `<div class="dv-legend"><span><i class="tot"></i>Period total</span><span><i class="fav"></i>Raises net income</span><span><i class="unf"></i>Lowers net income</span>${lo > 0 ? '<span>Axis starts at ' + fmtM(lo) + '</span>' : ''}</div>`;
  }
  function niceTicks(lo, hi, n){
    const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0))), r = step0 / mag;
    const step = (r < 1.5 ? 1 : r < 3 ? 2 : r < 7 ? 5 : 10) * mag, out = [];
    for(let t = Math.ceil(lo / step) * step; t <= hi + 1e-9; t += step) out.push(t);
    return out;
  }
  const trunc = (s, n) => { s = String(s); return s.length > n ? s.slice(0, n - 1) + '…' : s; };
  // treemap: items [{label, size, delta, fav}] — size = current value, colour = change (favourable blue / unfavourable orange)
  function treemap(items, opts={}){
    items = items.filter(i => i.size > 0).sort((a,b) => b.size - a.size);
    if(!items.length) return '<p class="card-sub">Nothing to show for this selection.</p>';
    const W = 1000, H = 340, rects = [];
    squarify(items, 0, 0, W, H, rects);
    const maxp = Math.max(0.05, ...items.map(i => Math.abs(i.dp || 0)));
    const cells = rects.map(r => {
      const it = r.it, a = Math.min(1, Math.abs(it.dp || 0) / maxp), fav = it.fav;
      const bg = it.dp === null ? 'var(--surface-3)' : `color-mix(in srgb, ${fav ? 'var(--dv-fav)' : 'var(--dv-unf)'} ${Math.round(12 + a * 58)}%, var(--surface))`;
      const small = r.w < 90 || r.h < 44;
      return `<div style="left:${r.x/W*100}%;top:${r.y/H*100}%;width:${r.w/W*100}%;height:${r.h/H*100}%;background:${bg}" title="${esc(it.label + ' · ' + fmtSARFull(it.size) + ' · change ' + fmS(it.delta) + (it.dp !== null ? ' (' + pctS(it.dp*100) + ')' : ''))}">${small ? '' : `<b>${esc(it.label)}</b><span>${fm(it.size)} · ${fmS(it.delta)}</span>`}</div>`;
    }).join('');
    return `<div class="dv-tm" role="img" aria-label="${esc(opts.aria || 'Treemap')}">${cells}</div>` +
      `<div class="dv-scale"><span>${opts.unfLab || 'Worse'}</span><span class="bar"></span><span>${opts.favLab || 'Better'}</span><span>· box size = current ${opts.what || 'value'}, colour = change vs comparison</span></div>`;
  }
  function squarify(items, x, y, w, h, out){
    const total = items.reduce((s, i) => s + i.size, 0); if(!total) return;
    const scale = w * h / total; let row = [], rest = items.slice();
    const worst = (row, len) => { const s = row.reduce((a,i) => a + i.size*scale, 0), mx = Math.max(...row.map(i => i.size*scale)), mn = Math.min(...row.map(i => i.size*scale)); return Math.max(len*len*mx/(s*s), s*s/(len*len*mn)); };
    while(rest.length){
      const len = Math.min(w, h), it = rest[0];
      if(!row.length || worst(row.concat([it]), len) <= worst(row, len)){ row.push(it); rest.shift(); continue; }
      [x, y, w, h] = layRow(row, x, y, w, h, scale, out); row = [];
    }
    if(row.length) layRow(row, x, y, w, h, scale, out);
  }
  function layRow(row, x, y, w, h, scale, out){
    const s = row.reduce((a,i) => a + i.size*scale, 0);
    if(w >= h){ const cw = s / h; let yy = y; row.forEach(it => { const ch = it.size*scale / cw; out.push({x, y:yy, w:cw, h:ch, it}); yy += ch; }); return [x + cw, y, w - cw, h]; }
    const rh = s / w; let xx = x; row.forEach(it => { const cw = it.size*scale / rh; out.push({x:xx, y, w:cw, h:rh, it}); xx += cw; }); return [x, y + rh, w, h - rh];
  }
  // line chart: current window months vs same months a year earlier
  function trend(series, opts={}){
    const W = opts.W || 860, H = opts.H || 230, l = 62, r = 16, t = 12, bt = 28, n = series.cur.length;
    const vals = series.cur.concat(series.ly).filter(v => v !== null);
    let lo = Math.min(0, ...vals), hi = Math.max(...vals, 1);
    const ticks = niceTicks(lo, hi, 4); lo = Math.min(lo, ticks[0]); hi = Math.max(hi, ticks[ticks.length-1]);
    const sx = i => l + (n === 1 ? (W-l-r)/2 : i * (W - l - r) / (n - 1)), sy = v => t + (1 - (v - lo)/(hi - lo)) * (H - t - bt);
    let g = ticks.map(v => `<line class="grid" x1="${l}" x2="${W-r}" y1="${sy(v)}" y2="${sy(v)}"/><text x="${l-8}" y="${sy(v)+4}" font-size="10.5" text-anchor="end">${opts.fmt ? opts.fmt(v) : fmtM(v)}</text>`).join('');
    const path = arr => arr.map((v,i) => v === null ? null : `${sx(i)},${sy(v)}`).filter(Boolean).join(' ');
    g += `<polyline class="ln-ly" points="${path(series.ly)}"/><polyline class="ln-cur" points="${path(series.cur)}"/>`;
    const step = Math.max(1, Math.ceil(n / 12));
    series.lab.forEach((lb, i) => { if(i % step === 0 || i === n-1) g += `<text x="${sx(i)}" y="${H-8}" font-size="10.5" text-anchor="middle">${lb}</text>`; });
    series.cur.forEach((v, i) => {
      const ly = series.ly[i], f = opts.fmt || (x => fmtSARFull(x));
      const tip = `${series.lab[i]}: ${v === null ? '—' : f(v)}${ly !== null ? ' · a year earlier ' + f(ly) : ''}${series.partial && i === n-1 ? ' · open month, partial' : ''}`;
      g += `<g><title>${esc(tip)}</title><rect class="hit" x="${sx(i) - (W-l-r)/(2*Math.max(1,n-1))}" y="${t}" width="${(W-l-r)/Math.max(1,n-1)}" height="${H-t-bt}"/>` +
           (v !== null ? `<circle class="pt-cur" cx="${sx(i)}" cy="${sy(v)}" r="${i === n-1 ? 5 : 3.5}"/>` : '') + `</g>`;
    });
    return `<div class="dv-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria || 'Trend')}">${g}</svg></div>` +
      `<div class="dv-legend"><span><i class="cur"></i>${opts.curLab || 'This period'}</span><span><i class="ly"></i>Same month a year earlier</span>${series.partial ? '<span>Last point: open month, partial</span>' : ''}</div>`;
  }
  // decomposition tree: node {label, cur, prev, fav(sign), kids:[]}
  function tree(root, opts={}){
    const mx = n => Math.max(1, ...((n.kids||[]).map(k => Math.abs(k.cur - k.prev))));
    const node = (n, scale, depth) => {
      const d = n.cur - n.prev, kids = (n.kids||[]).filter(k => Math.abs(k.cur) + Math.abs(k.prev) >= 1)
        .sort((a,b) => Math.abs(b.cur-b.prev) - Math.abs(a.cur-a.prev));
      const good = n.costLike ? d <= 0 : d >= 0, w = Math.min(50, Math.abs(d) / scale * 50);
      const bar = `<span class="db"><i style="${d >= 0 ? 'left:50%' : 'right:50%'};width:${w}%;background:${good ? 'var(--dv-fav)' : 'var(--dv-unf)'}"></i></span>`;
      const sum = `<summary><span class="nm" title="${esc(n.label)}">${esc(n.label)}</span><span class="n">${fm(n.cur)}</span><span class="n">${fmS(d)}</span>${bar}</summary>`;
      const sc = mx({kids});
      return `<details${kids.length ? '' : ' class="leaf"'}${depth < (opts.open || 1) ? ' open' : ''}>${sum}${kids.slice(0, opts.limit || 25).map(k => node(k, sc, depth + 1)).join('')}</details>`;
    };
    return `<div class="dv-tree"><div class="hd"><span>${opts.head || 'Driver'}</span><span>Current</span><span>Change</span><span>Change (bar)</span></div>${node(root, Math.max(1, Math.abs(root.cur - root.prev)), 0)}</div>`;
  }
  function movers(list, costLike){
    return `<ul class="dv-movers">${list.map(m => {
      const good = costLike ? m.d <= 0 : m.d >= 0;
      return `<li><span class="ic ${good ? 'fav' : 'unf'}">${m.d >= 0 ? '▲' : '▼'}</span><span>${m.text}</span><span class="n">${fmS(m.d)}</span></li>`;
    }).join('')}</ul>`;
  }
  const tile = (label, cur, prev, costLike, fmtF) => {
    if(fmtF && fmtF.pp){
      if(cur === null) return `<div class="card kpi"><div class="label">${label}</div><div class="value num" style="font-size:22px">—</div><div class="delta flat">not meaningful: revenue not posted yet</div></div>`;
      const d = prev === null ? null : (cur - prev) * 100, good = d === null ? null : (costLike ? d <= 0 : d >= 0);
      return `<div class="card kpi"><div class="label">${label}</div><div class="value num" style="font-size:22px">${(cur*100).toFixed(1)}%</div><div class="delta" style="${d === null ? '' : 'color:' + (good ? 'var(--dv-fav)' : 'var(--dv-unf)')}">${d === null ? 'no comparison' : (d >= 0 ? '▲ ' : '▼ ') + Math.abs(d).toFixed(1) + ' pp vs ' + (prev*100).toFixed(1) + '%'}</div></div>`;
    }
    const f = fmtF || fmtSARFull, d = prev === null ? null : cur - prev, p = prev === null ? null : pct(cur, prev);
    const good = d === null ? null : (costLike ? d <= 0 : d >= 0);
    return `<div class="card kpi"><div class="label">${label}</div><div class="value num" style="font-size:22px">${f(cur)}</div>` +
      `<div class="delta ${d === null ? 'flat' : good ? 'up' : 'down'}" style="${d === null ? '' : 'color:' + (good ? 'var(--dv-fav)' : 'var(--dv-unf)')}">${d === null ? 'no comparison' : (d >= 0 ? '▲ ' : '▼ ') + (fmtF ? fmtF(Math.abs(d)).replace(/^SAR /,'') : fmtM(Math.abs(d))) + ' (' + pctS(p) + ') vs ' + f(prev)}</div></div>`;
  };

  /* ---------------- shell ---------------- */
  const box = el('div', 'dv');
  const head = sec.querySelector('.section-head'); head.after(box);
  const top = el('div', 'dv-top'), warn = el('div'), body = el('div');
  box.appendChild(el('div', 'section-head', `<div class="eyebrow">Deep Analysis · Drivers</div><h2 style="font-size:22px">What moved the result <span style="font-family:'IBM Plex Sans',sans-serif;font-size:15px;color:var(--ink-muted);font-weight:500">· محركات الإيراد والتكلفة وصافي الربح</span></h2><p>Every change split into the things that caused it — volume, price and mix for revenue; department contribution; cost by nature and by function; and the full bridge to net income. The period and branch come from the filter bar at the top of the page; pick the comparison here.</p>`));
  box.appendChild(top); box.appendChild(warn); box.appendChild(body);

  function drawTop(W){
    const cmpLab = W.c ? (W.c.a === W.c.b ? mlab(W.c.a) : mlab(W.c.a) + ' – ' + mlab(W.c.b)) : 'not available';
    top.innerHTML = `<div class="dv-tabs" role="tablist">${[['rev','Revenue driver'],['dept','Department driver'],['cost','Cost driver'],['ni','Net income driver']].map(([k,t]) => `<button role="tab" aria-selected="${st.tab===k}" data-t="${k}" class="${st.tab===k?'on':''}">${t}</button>`).join('')}</div>` +
      `<div class="dv-seg" aria-label="Comparison">${[['yoy','vs same period last year'],['prev','vs previous period']].map(([k,t]) => `<button data-c="${k}" class="${st.cmp===k?'on':''}">${t}</button>`).join('')}</div>` +
      `<div class="dv-read">Period <b>${W.a === W.b ? mlab(W.a) : mlab(W.a) + ' – ' + mlab(W.b)}</b> · compared with <b>${cmpLab}</b> · <b>${TI.cc === 'ALL' ? 'All branches' : (BRN[TI.cc] || TI.cc)}</b></div>`;
    top.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { st.tab = b.dataset.t; render(); });
    top.querySelectorAll('[data-c]').forEach(b => b.onclick = () => { st.cmp = b.dataset.c; render(); });
    const notes = [];
    if(W.clipped) notes.push('The driver data starts in January 2024; the period has been cut to start there.');
    if(W.open) notes.push(`<b>${mlab(OPEN)} is the open month</b> (${X.openDay} days so far). Ledger figures include every posted and open entry to date — September sales invoices are not in the ledger yet, so ledger-based comparisons for this month are not like-for-like. The revenue driver uses the invoice tables and compares the same days of the comparison month.`);
    warn.innerHTML = notes.length ? `<div class="dv-warn">${notes.join(' ')}</div>` : '';
  }

  /* ---------------- Revenue driver ---------------- */
  function renderRev(W){
    if(!W.c) return '<p class="card-sub">No comparison period available for this selection.</p>';
    const C = visits(W.a, W.b, false, W), P = visits(W.c.a, W.c.b, true, W);
    const b = pvm(C.seg, P.seg);
    const V1 = Object.values(C.seg).reduce((s,x) => s + x.v, 0), V0 = Object.values(P.seg).reduce((s,x) => s + x.v, 0);
    const gl = ledger(W.a, W.b), glp = ledger(W.c.a, W.c.b);
    let h = `<div class="grid grid-4">${tile('Invoice revenue', b.R1, b.R0)}${tile('Visits (episodes)', V1, V0, false, v => Math.round(v).toLocaleString('en-US'))}${tile('Revenue per visit', V1 ? b.R1/V1 : 0, V0 ? b.R0/V0 : null, false, v => 'SAR ' + Math.round(v).toLocaleString('en-US'))}${tile('Ledger revenue (41x + 42x)', gl.rev, glp.rev)}</div>`;
    h += `<div class="dv-seg" style="margin-top:12px">${[[false,'All invoice lines'],[true,'Exclude pharmacy lines']].map(([k,t]) => `<button data-np="${k}" class="${st.np===k?'on':''}">${t}</button>`).join('')}</div>`;
    if(W.open) h += ` <div class="dv-seg" style="margin-top:12px">${[[true,'Same days of the comparison month'],[false,'Full comparison month']].map(([k,t]) => `<button data-lfl="${k}" class="${st.lfl===k?'on':''}">${t}</button>`).join('')}</div>`;
    const items = [{label:'Comparison period', v:b.R0, kind:'total'},
      {label:'Volume — more / fewer visits', v:b.volume, kind:'delta', fav:b.volume >= 0, tip:`${Math.round(V1-V0).toLocaleString('en-US')} visits at the old average price`},
      {label:'Price — revenue per visit', v:b.price, kind:'delta', fav:b.price >= 0, tip:'same visits, change in revenue per visit within each segment'},
      {label:'Mix — shift between segments', v:b.mix, kind:'delta', fav:b.mix >= 0, tip:'visits moving between higher- and lower-value segments (branch × payment × specialty)'},
      {label:'New / lost segments & refunds', v:b.other, kind:'delta', fav:b.other >= 0, tip:'segments with visits in only one of the two periods, and refund-only lines'},
      {label:'This period', v:b.R1, kind:'total'}];
    h += `<div class="card" style="margin-top:16px"><h3>Revenue bridge — volume, price and mix</h3><p class="card-sub">Invoice revenue (net of discount, insurer share and VAT, less refunds). Segment = branch × payment type × doctor speciality; visits = distinct patient episodes.</p>${waterfall(items, {zoom:true, aria:'Revenue bridge'})}</div>`;
    // by branch & payment type
    const agg = (seg, key) => { const o = {}; Object.values(seg).forEach(s => { const k = key(s); o[k] = (o[k]||0) + s.r; }); return o; };
    const bc = agg(C.seg, s => BRN[s.br] + ' · ' + s.pt), bp = agg(P.seg, s => BRN[s.br] + ' · ' + s.pt);
    const bk = [...new Set([...Object.keys(bc), ...Object.keys(bp)])].map(k => ({k, d:(bc[k]||0) - (bp[k]||0)})).sort((a,b) => b.d - a.d);
    const bItems = [{label:'Comparison period', v:b.R0, kind:'total'}, ...bk.map(x => ({label:x.k, v:x.d, kind:'delta', fav:x.d >= 0})), {label:'This period', v:b.R1, kind:'total'}];
    // treemap by speciality
    const sc = agg(C.seg, s => s.sp), sp_ = agg(P.seg, s => s.sp);
    const tm = [...new Set([...Object.keys(sc), ...Object.keys(sp_)])].map(k => { const c = sc[k]||0, p = sp_[k]||0; return {label:k, size:c, delta:c-p, dp:p ? (c-p)/Math.abs(p) : null, fav:c >= p}; });
    h += `<div class="dv-grid"><div class="card"><h3>By branch and payment type</h3><p class="card-sub">Change in invoice revenue, largest increase first.</p>${waterfall(bItems, {zoom:true, left:170, W:560, chars:24, aria:'Revenue change by branch and payment type'})}</div>` +
         `<div class="card"><h3>By doctor speciality</h3><p class="card-sub">Where the revenue is, and which way each speciality moved.</p>${treemap(tm, {what:'revenue', aria:'Revenue by speciality'})}</div></div>`;
    // decomposition tree branch → payment → speciality → doctor
    const root = {label:'Invoice revenue', cur:b.R1, prev:b.R0, kids:[]};
    const add = (arr, label) => { let n = arr.find(k => k.label === label); if(!n){ n = {label, cur:0, prev:0, kids:[]}; arr.push(n); } return n; };
    [[C.seg,'cur'],[P.seg,'prev']].forEach(([seg, f]) => Object.values(seg).forEach(s => {
      const nb = add(root.kids, BRN[s.br]), np = add(nb.kids, s.pt), ns = add(np.kids, s.sp);
      nb[f] += s.r; np[f] += s.r; ns[f] += s.r;
      for(const d in s.doc){ const nd = add(ns.kids, d); nd[f] += s.doc[d].r; }
    }));
    h += `<div class="card" style="margin-top:16px"><h3>Decomposition tree</h3><p class="card-sub">Branch → payment type → speciality → doctor. Click a row to open it; rows are sorted by the size of their change.</p>${tree(root, {head:'Revenue', open:1})}</div>`;
    // movers: doctors
    const docs = [];
    Object.values(C.seg).concat(Object.values(P.seg)).forEach(() => {});
    const dm = {};
    [[C.seg,1],[P.seg,-1]].forEach(([seg, s]) => Object.values(seg).forEach(x => { for(const d in x.doc){ const k = BRN[x.br] + ' · ' + x.sp + ' · ' + d; const o = dm[k] || (dm[k] = {r:0, v:0}); o.r += s * x.doc[d].r; o.v += s * x.doc[d].v; } }));
    Object.entries(dm).forEach(([k, o]) => docs.push({text:`${esc(k)} — ${o.v >= 0 ? '+' : '−'}${Math.abs(Math.round(o.v)).toLocaleString('en-US')} visits`, d:o.r}));
    docs.sort((a,b) => Math.abs(b.d) - Math.abs(a.d));
    h += `<div class="dv-grid"><div class="card"><h3>Biggest movers — doctors</h3><p class="card-sub">Change in invoice revenue and visits.</p>${movers(docs.slice(0, 8))}</div>`;
    // trend: monthly invoice revenue, 12 months ending at the period end, vs a year earlier
    const e = W.b, s0 = Math.max(0, e - 11), idx = []; for(let i = s0; i <= e; i++) idx.push(i);
    const monthRev = i => X.vis.reduce((t, r) => brOK(r[0]) ? t + (st.np ? r[6] : r[5])[i] : t, 0);
    const monthVis = i => X.vis.reduce((t, r) => brOK(r[0]) ? t + r[4][i] : t, 0);
    h += `<div class="card"><h3>Monthly invoice revenue</h3><p class="card-sub">12 months to ${mlab(e)} against the same months a year earlier.</p>${trend({cur:idx.map(monthRev), ly:idx.map(i => i >= 12 ? monthRev(i-12) : null), lab:idx.map(i => mlab(i).replace(' 20',' ’')), partial:W.open}, {W:560, H:300, aria:'Monthly invoice revenue'})}</div></div>`;
    h += `<div class="card" style="margin-top:16px"><h3>Monthly visits</h3><p class="card-sub">Monthly visits (episodes), 12 months to ${mlab(e)}.</p>${trend({cur:idx.map(monthVis), ly:idx.map(i => i >= 12 ? monthVis(i-12) : null), lab:idx.map(i => mlab(i).replace(' 20',' ’')), partial:W.open}, {fmt:v => Math.round(v).toLocaleString('en-US'), curLab:'Visits', H:200, aria:'Monthly visits'})}</div>`;
    // invoice → ledger reconciliation for the period
    const V = DATA.vatr, med = (a0, b0) => { let t = 0; for(let i = a0; i <= b0; i++){ const ym = M[i].replace('-',''); BRS.filter(brOK).forEach(br => { t += (((V||{}).adj||{})[br]||{})[ym] ? (V.adj[br][ym].MED||0) : 0; }); } return t; };
    const x27 = (a0, b0) => { let t = 0; L.forEach(r => { if(r.a === '4200027' && brOK(r.cc)) t -= sumR(r.v, a0, b0); }); return t; };
    const invAll = (a0, b0) => X.vis.reduce((t, r) => brOK(r[0]) ? t + sumR(r[5], a0, b0) : t, 0);
    const recRow = (lab, a0, b0, glr) => { const inv = invAll(a0, b0), md = med(a0, b0), dx = x27(a0, b0), oth = inv - md - dx - glr; const sg = v => Math.round(v) === 0 ? '0' : (v < 0 ? '−' : '+') + nfmt(Math.abs(v)); return `<tr><td>${lab}</td><td>${nfmt(inv)}</td><td>${sg(-md)}</td><td>${sg(-dx)}</td><td>${sg(-oth)}</td><td>${sg(glr).replace(/^\+/,'')}</td></tr>`; };
    h += `<div class="card" style="margin-top:16px"><h3>From invoice revenue to ledger revenue</h3><p class="card-sub">Why the two revenue figures differ (all invoice lines, including pharmacy).</p><div class="dv-wrap"><table class="dv-tbl"><tr><th>Period</th><th>Invoice revenue</th><th>Medicine cost booked against revenue</th><th>Insurance drug sales (4200027, other revenue)</th><th>Timing & other</th><th>Ledger revenue (41x + 42x)</th></tr>` +
      recRow('This period', W.a, W.b, gl.rev) + recRow('Comparison', W.c.a, W.c.b, glp.rev) + `</table></div>` +
      `<p class="dv-note">Every month the Riyadh ledger debits revenue with the cost of medicines dispensed (journal "ادوية عن شهر"), so ledger revenue is net of it while the invoices are not; the amounts come from the same entries the VAT reconciliation uses (from January 2025). Insurance drug sales are posted to 4200027, which the statements show as other revenue. "Timing & other" is mainly invoices not yet posted${W.open ? ' — for the open month, the ${mlab(OPEN)} sales that are not in the ledger yet' : ''}, credit notes and discounts posted in a different month.${C.lf || P.lf ? ` The comparison month is limited to days 1–${X.openDay} using each segment's daily invoice revenue; visits are scaled in the same proportion.` : ''}</p></div>`;
    return h;
  }

  /* ---------------- Department driver ---------------- */
  function renderDept(W){
    if(!W.c) return '<p class="card-sub">No comparison period available for this selection.</p>';
    const rows = [];
    for(const k in X.dser){
      const [br, en, ar] = X.dept[k]; if(!brOK(br)) continue;
      const [ca, cr, co] = X.dser[k];
      const r1 = sumR(ca, W.a, W.b) + sumR(cr, W.a, W.b), r0 = sumR(ca, W.c.a, W.c.b) + sumR(cr, W.c.a, W.c.b);
      const c1 = sumR(co, W.a, W.b), c0 = sumR(co, W.c.a, W.c.b);
      if(!r1 && !r0 && !c1 && !c0) continue;
      rows.push({k, br, label:(TI.cc === 'ALL' ? BRN[br] + ' · ' : '') + en + (ar && ar !== en ? ' ' : ''), ar, r1, r0, c1, c0, m1:r1 - c1, m0:r0 - c0});
    }
    const T = f => rows.reduce((s, r) => s + r[f], 0);
    let h = `<div class="grid grid-4">${tile('Department revenue', T('r1'), T('r0'))}${tile('Direct cost', T('c1'), T('c0'), true)}${tile('Contribution', T('m1'), T('m0'))}${tile('Contribution margin', T('r1') > 0 ? T('m1')/T('r1') : null, T('r0') > 0 ? T('m0')/T('r0') : null, false, PP)}</div>`;
    const byD = rows.map(r => ({label:r.label, v:r.m1 - r.m0, kind:'delta', fav:r.m1 >= r.m0, tip:`revenue ${fmS(r.r1 - r.r0)}, direct cost ${fmS(r.c1 - r.c0)}`})).sort((a,b) => Math.abs(b.v) - Math.abs(a.v));
    const topN = byD.slice(0, 12), rest = byD.slice(12).reduce((s, x) => s + x.v, 0);
    const items = [{label:'Comparison contribution', v:T('m0'), kind:'total'}, ...topN.sort((a,b) => b.v - a.v), ...(byD.length > 12 ? [{label:`${byD.length - 12} other departments`, v:rest, kind:'delta', fav:rest >= 0}] : []), {label:'This period', v:T('m1'), kind:'total'}];
    h += `<div class="card" style="margin-top:16px"><h3>Contribution bridge by department</h3><p class="card-sub">Contribution = department revenue − direct cost tagged to the department (before shared overhead). The 12 largest changes, then the rest together.</p>${waterfall(items, {aria:'Contribution by department', left:300, chars:42})}</div>`;
    const tm = rows.map(r => ({label:r.label, size:r.r1, delta:r.r1 - r.r0, dp:r.r0 ? (r.r1 - r.r0)/Math.abs(r.r0) : null, fav:r.r1 >= r.r0}));
    h += `<div class="dv-grid"><div class="card"><h3>Revenue by department</h3><p class="card-sub">Box size = revenue this period; colour = change.</p>${treemap(tm, {what:'revenue', aria:'Revenue by department'})}</div>`;
    const rev = rows.map(r => ({text:`${esc(r.label)} — revenue ${fmS(r.r1 - r.r0)}, direct cost ${fmS(r.c1 - r.c0)}`, d:r.m1 - r.m0})).sort((a,b) => Math.abs(b.d) - Math.abs(a.d));
    h += `<div class="card"><h3>What moved contribution</h3><p class="card-sub">Largest changes first.</p>${movers(rev.slice(0, 10))}</div></div>`;
    rows.sort((a,b) => b.r1 - a.r1);
    h += `<div class="card" style="margin-top:16px"><h3>Department table</h3><div class="dv-wrap"><table class="dv-tbl"><tr><th>Department</th><th>Revenue</th><th>Δ revenue</th><th>Direct cost</th><th>Δ cost</th><th>Contribution</th><th>Δ contribution</th><th>Margin</th></tr>` +
      rows.map(r => `<tr><td title="${esc(r.ar)}">${esc(r.label)}</td><td>${nfmt(r.r1)}</td><td class="${r.r1 >= r.r0 ? 'pos' : 'neg'}">${fmS(r.r1 - r.r0)}</td><td>${nfmt(r.c1)}</td><td class="${r.c1 <= r.c0 ? 'pos' : 'neg'}">${fmS(r.c1 - r.c0)}</td><td>${nfmt(r.m1)}</td><td class="${r.m1 >= r.m0 ? 'pos' : 'neg'}">${fmS(r.m1 - r.m0)}</td><td>${r.r1 > 10000 && Math.abs(r.m1/r.r1) < 5 ? (r.m1/r.r1*100).toFixed(1) + '%' : '—'}</td></tr>`).join('') + `</table></div>` +
      `<p class="dv-note">From the ledger by cost centre (posted and open vouchers). Revenue is cash 41x + credit 42x (insurance drug sales 4200027 excluded); direct cost is every expense account tagged to the department, zakat excluded. "Non-clinical & shared" holds each branch's cost centres outside the clinics. Salaries and supplies booked centrally in Riyadh on behalf of a branch stay with the cost centre they were tagged to.</p></div>`;
    return h;
  }

  /* ---------------- Cost driver (by nature / by function) ---------------- */
  function renderCost(W){
    if(!W.c) return '<p class="card-sub">No comparison period available for this selection.</p>';
    const C = ledger(W.a, W.b), P = ledger(W.c.a, W.c.b), byNat = st.cview === 'nat';
    const keys = byNat ? [...NAT.map(g => g[0]), 'other'] : FNO;
    const lab = k => byNat ? NATL[k] : FNL[k];
    const cur = k => byNat ? (C.nat[k]||0) : C.fn[k], prv = k => byNat ? (P.nat[k]||0) : P.fn[k];
    let h = `<div class="dv-seg" style="margin-bottom:12px">${[['nat','By nature'],['fn','By function']].map(([k,t]) => `<button data-cv="${k}" class="${st.cview===k?'on':''}">${t}</button>`).join('')}</div>`;
    h += `<div class="grid grid-4">${tile('Operating cost (ex. zakat)', C.cost, P.cost, true)}${tile('Cost as % of revenue', C.rev > 0 ? C.cost/C.rev : null, P.rev > 0 ? P.cost/P.rev : null, true, PP)}${tile('Revenue (ledger)', C.rev, P.rev)}${tile(byNat ? 'Employee benefits' : 'Cost of revenue', byNat ? (C.nat.emp||0) : C.fn.COR, byNat ? (P.nat.emp||0) : P.fn.COR, true)}</div>`;
    const ds = keys.map(k => ({k, label:lab(k), v:cur(k) - prv(k)})).filter(x => Math.abs(x.v) >= 1).sort((a,b) => a.v - b.v);
    const items = [{label:'Comparison cost', v:P.cost, kind:'total'}, ...ds.map(x => ({label:x.label, v:x.v, kind:'delta', fav:x.v <= 0})), {label:'This period', v:C.cost, kind:'total'}];
    h += `<div class="card" style="margin-top:16px"><h3>Cost bridge ${byNat ? 'by nature' : 'by function'}</h3><p class="card-sub">${byNat ? 'Expenses grouped by what they are (IFRS 18 nature groups).' : 'Expenses grouped by where they are incurred — the organisation-function rules the income statement uses.'} Orange = cost went up (lowers net income).</p>${waterfall(items, {zoom:true, aria:'Cost bridge'})}</div>`;
    const tm = keys.map(k => ({label:lab(k), size:cur(k), delta:cur(k) - prv(k), dp:prv(k) ? (cur(k)-prv(k))/Math.abs(prv(k)) : null, fav:cur(k) <= prv(k)}));
    h += `<div class="dv-grid"><div class="card"><h3>Where the cost is</h3><p class="card-sub">Box size = cost this period; colour = change (orange = up).</p>${treemap(tm, {what:'cost', unfLab:'Cost up', favLab:'Cost down', aria:'Cost composition'})}</div>`;
    // matrix nature x function (change)
    const mx = Math.max(1, ...Object.keys({...C.mat, ...P.mat}).map(k => Math.abs((C.mat[k]||0) - (P.mat[k]||0))));
    const natK = [...NAT.map(g => g[0]), 'other'].filter(n => FNO.some(f => (C.mat[n+'|'+f]||0) || (P.mat[n+'|'+f]||0)));
    const cell = v => { const a = Math.min(1, Math.abs(v)/mx); return `<td style="background:color-mix(in srgb, ${v > 0 ? 'var(--dv-unf)' : 'var(--dv-fav)'} ${Math.round(a*60)}%, var(--surface))" title="${fmtSARFull(v)}">${Math.abs(v) >= 1 ? fmS(v) : '·'}</td>`; };
    const accM = [];
    { const ac = accRows(W.a, W.b, () => true), ap = accRows(W.c.a, W.c.b, () => true);
      new Set([...Object.keys(ac), ...Object.keys(ap)]).forEach(a0 => accM.push({text:`${a0} · ${esc(accName(a0))}`, d:(ac[a0]||0) - (ap[a0]||0)})); }
    accM.sort((x,y) => Math.abs(y.d) - Math.abs(x.d));
    h += `<div class="card"><h3>Biggest movers — accounts</h3><p class="card-sub">Change in cost; blue = cost went down.</p>${movers(accM.slice(0, 10), true)}</div></div>`;
    h += `<div class="card" style="margin-top:16px"><h3>Nature × function — change</h3><p class="card-sub">Each cell is the change in that nature of cost inside that function.</p><div class="dv-wrap"><table class="dv-hm"><tr><th>Nature</th>${FNO.map(f => `<th title="${FNL[f]}">${f}</th>`).join('')}<th>Total</th></tr>` +
      natK.map(n => `<tr><td>${esc(NATL[n])}</td>${FNO.map(f => cell((C.mat[n+'|'+f]||0) - (P.mat[n+'|'+f]||0))).join('')}${cell((C.nat[n]||0) - (P.nat[n]||0))}</tr>`).join('') +
      `</table></div><p class="card-sub" style="margin-top:8px">COR cost of revenue · GA general & administrative · INS insurance-company cost · HO head office · X unassigned.</p></div>`;
    // drill tree: group → account
    const root = {label:'Operating cost', cur:C.cost, prev:P.cost, costLike:true, kids:[]};
    keys.forEach(k => {
      const pred = byNat ? (r => (nat_of[r.a] || 'other') === k) : (r => (FNO.includes(r.f) ? r.f : 'X') === k);
      const ac = accRows(W.a, W.b, pred), ap = accRows(W.c.a, W.c.b, pred);
      const kids = [...new Set([...Object.keys(ac), ...Object.keys(ap)])].map(a => ({label:a + ' · ' + accName(a), cur:ac[a]||0, prev:ap[a]||0, costLike:true}));
      root.kids.push({label:lab(k), cur:cur(k), prev:prv(k), costLike:true, kids});
    });
    h += `<div class="card" style="margin-top:16px"><h3>Drill down to the account</h3><p class="card-sub">${byNat ? 'Nature' : 'Function'} → account. Click to open.</p>${tree(root, {head:'Cost', open:1})}</div>`;
    // trend: cost % of revenue
    const e = W.b, s0 = Math.max(0, e - 11), idx = []; for(let i = s0; i <= e; i++) idx.push(i);
    const ratio = i => { const o = ledger(i, i); return o.rev > 0 && !(W.open && i === OPEN) ? o.cost / o.rev * 100 : null; };
    h += `<div class="card" style="margin-top:16px"><h3>Cost as % of revenue, month by month</h3><p class="card-sub">12 months to ${mlab(e)}; ledger basis.${W.open ? ' The open month has costs posted but no September sales yet, so its ratio is not meaningful.' : ''}</p>${trend({cur:idx.map(ratio), ly:idx.map(i => i >= 12 ? ratio(i-12) : null), lab:idx.map(i => mlab(i).replace(' 20',' ’')), partial:W.open}, {fmt:v => v.toFixed(0) + '%', aria:'Cost as percent of revenue'})}</div>`;
    return h;
  }

  /* ---------------- Net income driver ---------------- */
  function niItems(C, P){
    const d = (x, y) => x - y;
    return [
      {k:'rev', label:'Revenue (cash + credit)', v:d(C.rev, P.rev)},
      {k:'orev', label:'Other revenue', v:d(C.orev, P.orev)},
      ...FNO.map(f => ({k:f, label:FNL[f], v:-d(C.fn[f], P.fn[f])})),
      {k:'zak', label:'Zakat', v:-d(C.zak, P.zak)}];
  }
  function renderNI(W){
    if(!W.c) return '<p class="card-sub">No comparison period available for this selection.</p>';
    const C = ledger(W.a, W.b), P = ledger(W.c.a, W.c.b);
    let h = `<div class="grid grid-4">${tile('Net income', C.ni, P.ni)}${tile('Net margin', C.rev > 0 ? C.ni/C.rev : null, P.rev > 0 ? P.ni/P.rev : null, false, PP)}${tile('Revenue', C.rev, P.rev)}${tile('Operating cost + zakat', C.cost + C.zak, P.cost + P.zak, true)}</div>`;
    const its = niItems(C, P).filter(x => Math.abs(x.v) >= 1);
    const items = [{label:'Comparison net income', v:P.ni, kind:'total'}, ...its.map(x => ({label:x.label, v:x.v, kind:'delta', fav:x.v >= 0})), {label:'This period', v:C.ni, kind:'total'}];
    h += `<div class="card" style="margin-top:16px"><h3>Net income bridge</h3><p class="card-sub">Each bar is how much that line moved net income: blue raised it, orange lowered it. Costs are by function, as in the income statement.</p>${waterfall(items, {aria:'Net income bridge'})}</div>`;
    // heatmap: each month in the window (max 12, ending at b) vs a year earlier
    const e = W.b, s0 = Math.max(12, e - 11), idx = []; for(let i = s0; i <= e; i++) idx.push(i);
    const rowsK = [['rev','Revenue'],['orev','Other revenue'],...FNO.map(f => [f, FNL[f]]),['zak','Zakat'],['ni','Net income']];
    const vals = idx.map(i => { const c = ledger(i, i), p = ledger(i-12, i-12), it = Object.fromEntries(niItems(c, p).map(x => [x.k, x.v])); it.ni = c.ni - p.ni; return it; });
    const mxv = Math.max(1, ...vals.flatMap(o => rowsK.filter(r => r[0] !== 'ni').map(r => Math.abs(o[r[0]]||0))));
    const cell = v => { const a = Math.min(1, Math.abs(v)/mxv); return `<td style="background:color-mix(in srgb, ${v >= 0 ? 'var(--dv-fav)' : 'var(--dv-unf)'} ${Math.round(a*60)}%, var(--surface))" title="${fmtSARFull(v)}">${Math.abs(v) >= 1 ? fmS(v) : '·'}</td>`; };
    h += `<div class="card" style="margin-top:16px"><h3>Month by month — what moved net income against the same month last year</h3><p class="card-sub">Blue = raised net income, orange = lowered it. Hover a cell for the exact amount.${W.open ? ' The last column is the open month (partial).' : ''}</p><div class="dv-wrap"><table class="dv-hm"><tr><th>Driver</th>${idx.map(i => `<th>${mlab(i).replace(' 20',' ’')}</th>`).join('')}</tr>` +
      rowsK.filter(([k]) => k === 'ni' || vals.some(o => Math.abs(o[k]||0) >= 1)).map(([k, l]) => `<tr${k === 'ni' ? ' style="font-weight:700"' : ''}><td>${l}</td>${vals.map(o => cell(o[k]||0)).join('')}</tr>`).join('') + `</table></div></div>`;
    // decomposition tree
    const brKids = lg => Object.keys(BRN).filter(brOK).map(b => ({label:BRN[b], cur:lg(b)[0], prev:lg(b)[1]}));
    const root = {label:'Net income', cur:C.ni, prev:P.ni, kids:[
      {label:'Revenue (cash + credit)', cur:C.rev, prev:P.rev, kids:brKids(b => [C.brRev[b]||0, P.brRev[b]||0])},
      {label:'Other revenue', cur:C.orev, prev:P.orev, kids:[]},
      ...FNO.map(f => {
        const nk = {}; [[C,'cur'],[P,'prev']].forEach(([o, s]) => { for(const k in o.mat){ const [n, ff] = k.split('|'); if(ff !== f) continue; (nk[n] = nk[n] || {label:NATL[n], cur:0, prev:0, costLike:true, kids:[]})[s] += o.mat[k]; } });
        const kids = Object.values(nk).map(x => ({...x, cur:-x.cur, prev:-x.prev, costLike:false}));
        return {label:FNL[f] + ' (as a reduction)', cur:-C.fn[f], prev:-P.fn[f], kids};
      }),
      {label:'Zakat (as a reduction)', cur:-C.zak, prev:-P.zak, kids:[]}]};
    h += `<div class="card" style="margin-top:16px"><h3>Decomposition tree</h3><p class="card-sub">Net income → revenue by branch and each cost function by nature. Costs are shown as negative numbers, so every row reads the same way: a positive change raises net income.</p>${tree(root, {head:'Net income', open:1})}</div>`;
    const e2 = W.b, s2 = Math.max(0, e2 - 11), id2 = []; for(let i = s2; i <= e2; i++) id2.push(i);
    const niM = i => ledger(i, i).ni;
    h += `<div class="card" style="margin-top:16px"><h3>Monthly net income</h3><p class="card-sub">12 months to ${mlab(e2)} against the same months a year earlier.</p>${trend({cur:id2.map(niM), ly:id2.map(i => i >= 12 ? niM(i-12) : null), lab:id2.map(i => mlab(i).replace(' 20',' ’')), partial:W.open}, {aria:'Monthly net income'})}</div>`;
    h += `<p class="dv-note">Ledger basis: every posted and open journal entry in the four EXSYS databases; cancelled vouchers, year-end closing vouchers and JV1-24/04043 are excluded, so the full years rebuild the income statement${TI.cc !== 'ALL' ? '' : ` (FY2024 net ${ledger(0, 11).ni < 0 ? 'loss' : 'income'} ${nfmt(Math.abs(ledger(0, 11).ni))}; FY2025 net ${ledger(12, 23).ni < 0 ? 'loss' : 'income'} ${nfmt(Math.abs(ledger(12, 23).ni))})`}. Revenue excludes insurance drug sales 4200027, which the statements show in other revenue.</p>`;
    return h;
  }

  /* ---------------- render ---------------- */
  function render(){
    const W = win(); drawTop(W);
    body.innerHTML = st.tab === 'rev' ? renderRev(W) : st.tab === 'dept' ? renderDept(W) : st.tab === 'cost' ? renderCost(W) : renderNI(W);
    body.querySelectorAll('[data-np]').forEach(b => b.onclick = () => { st.np = b.dataset.np === 'true'; render(); });
    body.querySelectorAll('[data-lfl]').forEach(b => b.onclick = () => { st.lfl = b.dataset.lfl === 'true'; render(); });
    body.querySelectorAll('[data-cv]').forEach(b => b.onclick = () => { st.cview = b.dataset.cv; render(); });
  }
  TI.on(render); render();
})();
