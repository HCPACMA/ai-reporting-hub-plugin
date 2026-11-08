/* AR Reconciliation › Tawuniya review (مراجعة مخالصة التعاونية) — added 7 Nov 2026.
   Data: window.TAW_DATA (ar-tawuniya-data.js), built by CFO-Cure-Kit/scripts/taw_settlement/build_data.py.
   Adds a sub-tab to #sec-ar-rec .arr-tabs; works with any number of existing sub-tabs. */
(function(){
  'use strict';
  var BRN = {Riyadh:'Riyadh', BUR1:'Buraydah 1', BUR2:'Buraydah 2', Rafha:'Rafha'};
  var BRA = {Riyadh:'الرياض', BUR1:'بريدة 1', BUR2:'بريدة 2', Rafha:'رفحاء'};
  var MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DT = [['early','Early payment discount','خصم تعجيل دفع'],['vol','Volume discount','خصم حجم عمل'],['mt','Medical & technical rejections','مرفوضات طبية وفنية'],['other','Other discount','خصومات أخرى'],['drg','DRG rejections','مرفوضات DRG']];
  var r2 = function(x){ return Math.round((x + 0) * 100) / 100; };
  var sum = function(a){ return r2(a.reduce(function(s, x){ return s + x; }, 0)); };
  var esc = function(s){ return String(s == null ? '' : s).replace(/[&<>"]/g, function(m){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]; }); };
  var n2 = function(v){ if(v == null || isNaN(v)) return '—'; v = r2(v); return (v < 0 ? '−' : '') + Math.abs(v).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2}); };
  var pc = function(v){ return isFinite(v) ? (v * 100).toFixed(2) + '%' : '—'; };
  var ml = function(ym){ return /^\d{4}-\d{2}$/.test(ym) ? MON[+ym.slice(5,7) - 1] + ' ' + ym.slice(0,4) : ym; };

  /* ---------------- model ---------------- */
  function model(D){
    var M = {br:{}, order:Object.keys(D.br)};
    M.order.forEach(function(b){
      var x = D.br[b], inP = function(m){ return m >= D.p0 && m <= D.p1; };
      var claims = x.claims.map(function(c){ return {mon:c[0], vno:c[1], dr:c[2], ret:c[3], oth:c[4], net:r2(c[2] - c[3] - c[4])}; });
      var pays = x.pays.map(function(p){ return {vno:p[0], dt:p[1], kind:p[2], mon:p[3], amt:p[4], inp:inP(p[3])}; });
      var lc = sum(claims.map(function(c){ return c.net; }));
      var pn = sum(pays.filter(function(p){ return p.inp && p.kind === 'net'; }).map(function(p){ return p.amt; }));
      var pv = sum(pays.filter(function(p){ return p.inp && p.kind === 'vat'; }).map(function(p){ return p.amt; }));
      var gross = r2(x.net[0] + x.net[1]), discT = r2(x.disc[0] + x.disc[1]), booked = sum((x.cns || []).map(function(c){ return c.amt; }));
      var unpaidMon = []; for(var i = 0; i < claims.length; i++){ var m = claims[i].mon;
        var hasN = pays.some(function(p){ return p.mon === m && p.kind === 'net'; }), hasV = pays.some(function(p){ return p.mon === m && p.kind === 'vat'; });
        if(!hasN || !hasV) unpaidMon.push(m + (!hasN ? ' (claim)' : '') + (!hasV ? ' (VAT)' : '')); }
      M.br[b] = {b:b, x:x, claims:claims, pays:pays, lc:lc, gross:gross, cdiff:r2(lc - gross), pn:pn, pv:pv, pdn:r2(pn - x.paid[0]), pdv:r2(pv - x.paid[1]),
        discT:discT, booked:booked, toBook:r2(discT - booked), lbal:x.lbal, after:r2(x.lbal - (discT - booked)), balT:r2(x.bal[0] + x.bal[1]),
        bdiff:r2(x.lbal - (discT - booked) - (x.bal[0] + x.bal[1])), mtPct:x.mt[0] / x.net[0], unpaid:unpaidMon};
    });
    var keys = ['lc','gross','cdiff','pn','pv','pdn','pdv','discT','booked','toBook','lbal','after','balT','bdiff'];
    M.tot = {}; keys.forEach(function(k){ M.tot[k] = sum(M.order.map(function(b){ return M.br[b][k]; })); });
    ['net','early','vol','other','mt','drg','disc','paid','appr','bal'].forEach(function(k){ M.tot[k] = [0,1].map(function(i){ return sum(M.order.map(function(b){ return D.br[b][k][i]; })); }); });
    M.flags = flags(D, M);
    return M;
  }
  function flags(D, M){
    var F = [];
    var mts = M.order.map(function(b){ return M.br[b].mtPct; }), flat = mts.every(function(v){ return Math.abs(v - mts[0]) < 0.0001; });
    if(flat) F.push(['high','Flat-rate rejection', 'Medical & technical rejection is ' + pc(mts[0]) + ' of net (excl. VAT) in every branch, the same rate everywhere. That points to an estimated percentage, not a rejection list. Ask for the claim-level rejection detail before signing.', 'نسبة المرفوضات ثابتة ' + pc(mts[0]) + ' في جميع الفروع — نطلب كشف المرفوضات التفصيلي قبل التوقيع']);
    if(M.tot.vol[0] > 0) F.push(['med','Volume discount taken already', 'Volume discount of ' + n2(M.tot.vol[0]) + ' (excl. VAT) is deducted, but the letter\'s own note says volume discount is calculated at year end.', 'خصم حجم العمل مخصوم رغم أن الخطاب ينص على احتسابه نهاية العام']);
    M.order.forEach(function(b){ var x = D.br[b];
      if(x.vat_no && D.letter.tawuniya_vat && x.vat_no === D.letter.tawuniya_vat) F.push(['high', BRN[b] + ': wrong VAT number', 'The second party (Al Faihaa) VAT number in the ' + BRN[b] + ' letter is ' + x.vat_no + ', which is Tawuniya\'s own number. It should be ' + D.letter.faihaa_vat + '. Ask for a corrected copy.', 'الرقم الضريبي للفيحاء في خطاب ' + BRA[b] + ' خاطئ (رقم التعاونية)']);
    });
    M.order.forEach(function(b){ var r = M.br[b];
      if(Math.abs(r.cdiff) >= 1) F.push([Math.abs(r.cdiff) > 1000 ? 'med' : 'low', BRN[b] + ': claims differ by ' + n2(r.cdiff), 'Ledger claims (net of returns, incl. VAT) are ' + (r.cdiff > 0 ? 'higher' : 'lower') + ' than the letter by ' + n2(Math.abs(r.cdiff)) + '. After the discount credit notes are posted the ledger will ' + (r.bdiff > 0 ? 'exceed' : 'fall short of') + ' the letter balance by ' + n2(Math.abs(r.bdiff)) + '. Trace to claims not submitted / re-submitted or returns.', 'فرق مطالبات ' + BRA[b]]);
      if(Math.abs(r.pdn) >= 0.01 || Math.abs(r.pdv) >= 0.01) F.push(['high', BRN[b] + ': payments differ', 'Ledger receipts for the period differ from the letter: claims ' + n2(r.pdn) + ', VAT ' + n2(r.pdv) + '.', 'فرق سداد ' + BRA[b]]);
    });
    if(!D.letter.signed) F.push(['low','Not signed yet', 'This is the initial letter: the signature page is blank. Reply with the points above before it is signed and stamped.', 'خطاب مبدئي غير موقّع']);
    return F;
  }

  /* ---------------- xlsx ---------------- */
  var XL = (function(){
    var crcT = (function(){ var t = new Uint32Array(256); for(var n = 0; n < 256; n++){ var c = n; for(var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
    var crc32 = function(u){ var c = 0xFFFFFFFF; for(var i = 0; i < u.length; i++) c = crcT[(c ^ u[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; };
    var xe = function(v){ return String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); };
    var col = function(i){ var s = ''; i++; while(i){ var m = (i - 1) % 26; s = String.fromCharCode(65 + m) + s; i = Math.floor((i - 1) / 26); } return s; };
    function cell(ref, v){
      if(v == null || v === '') return '';
      if(typeof v === 'object' && v.f) return '<c r="' + ref + '"' + (v.s ? ' s="' + v.s + '"' : '') + (typeof v.v === 'string' ? ' t="str"' : '') + '><f>' + xe(v.f) + '</f>' + (v.v != null ? '<v>' + xe(v.v) + '</v>' : '') + '</c>';
      if(typeof v === 'object') { var s = v.s ? ' s="' + v.s + '"' : ''; v = v.v; if(v == null || v === '') return s ? '<c r="' + ref + '"' + s + '/>' : '';
        return typeof v === 'number' ? '<c r="' + ref + '"' + s + '><v>' + v + '</v></c>' : '<c r="' + ref + '"' + s + ' t="inlineStr"><is><t xml:space="preserve">' + xe(v) + '</t></is></c>'; }
      return typeof v === 'number' ? '<c r="' + ref + '" s="2"><v>' + v + '</v></c>' : '<c r="' + ref + '" t="inlineStr"><is><t xml:space="preserve">' + xe(v) + '</t></is></c>';
    }
    function sheet(sh){
      var rows = sh.rows, w = sh.widths || [];
      var x = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">';
      x += '<sheetViews><sheetView workbookViewId="0"' + (sh.rtl ? ' rightToLeft="1"' : '') + '>' + (sh.freeze ? '<pane ySplit="' + sh.freeze + '" topLeftCell="A' + (sh.freeze + 1) + '" activePane="bottomLeft" state="frozen"/>' : '') + '</sheetView></sheetViews>';
      if(w.length) x += '<cols>' + w.map(function(v, i){ return '<col min="' + (i + 1) + '" max="' + (i + 1) + '" width="' + v + '" customWidth="1"/>'; }).join('') + '</cols>';
      x += '<sheetData>' + rows.map(function(r, i){ return '<row r="' + (i + 1) + '">' + (r || []).map(function(v, j){ return cell(col(j) + (i + 1), v); }).join('') + '</row>'; }).join('') + '</sheetData>';
      if(sh.merges && sh.merges.length) x += '<mergeCells count="' + sh.merges.length + '">' + sh.merges.map(function(m){ return '<mergeCell ref="' + m + '"/>'; }).join('') + '</mergeCells>';
      if(sh.af) x += '<autoFilter ref="' + sh.af + '"/>';
      return x + '<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/><pageSetup orientation="landscape" fitToWidth="1" fitToHeight="0"/></worksheet>';
    }
    var STY = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">' +
      '<numFmts count="3"><numFmt numFmtId="164" formatCode="#,##0.00;[Red]\\-#,##0.00"/><numFmt numFmtId="165" formatCode="yyyy-mm-dd"/><numFmt numFmtId="166" formatCode="0.00%"/></numFmts>' +
      '<fonts count="5"><font><sz val="10"/><name val="Arial"/></font><font><b/><sz val="10"/><color rgb="FFFFFFFF"/><name val="Arial"/></font><font><b/><sz val="10"/><name val="Arial"/></font><font><b/><sz val="13"/><color rgb="FF0B6FBF"/><name val="Arial"/></font><font><b/><sz val="10"/><color rgb="FFD7261E"/><name val="Arial"/></font></fonts>' +
      '<fills count="5"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF0B6FBF"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFE7F1FC"/><bgColor indexed="64"/></patternFill></fill><fill><patternFill patternType="solid"><fgColor rgb="FFFDECEA"/><bgColor indexed="64"/></patternFill></fill></fills>' +
      '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left/><right/><top style="thin"><color rgb="FF0B6FBF"/></top><bottom style="double"><color rgb="FF0B6FBF"/></bottom><diagonal/></border></borders>' +
      '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="11">' +
      '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>' +                                                                              /*0 text*/
      '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment wrapText="1" vertical="center"/></xf>' + /*1 header*/
      '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +                                                     /*2 money*/
      '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +                                                     /*3 date*/
      '<xf numFmtId="166" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>' +                                                     /*4 pct*/
      '<xf numFmtId="164" fontId="2" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1"/>' +        /*5 total money*/
      '<xf numFmtId="0" fontId="2" fillId="3" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>' +                                 /*6 total text*/
      '<xf numFmtId="0" fontId="3" fillId="0" borderId="0" xfId="0" applyFont="1"/>' +                                                              /*7 title*/
      '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>' +            /*8 wrap*/
      '<xf numFmtId="0" fontId="4" fillId="4" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="top"/></xf>' + /*9 flag high*/
      '<xf numFmtId="166" fontId="2" fillId="3" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyFill="1" applyBorder="1"/>' +        /*10 total pct*/
      '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';
    function zip(files){
      var te = new TextEncoder(), parts = [], cen = [], off = 0;
      files.forEach(function(f){
        var nb = te.encode(f.name), data = typeof f.data === 'string' ? te.encode(f.data) : f.data, crc = crc32(data);
        var h = new DataView(new ArrayBuffer(30)); h.setUint32(0,0x04034b50,true); h.setUint16(4,20,true); h.setUint16(6,0x800,true); h.setUint16(8,0,true);
        h.setUint16(10,0,true); h.setUint16(12,0x21,true); h.setUint32(14,crc,true); h.setUint32(18,data.length,true); h.setUint32(22,data.length,true); h.setUint16(26,nb.length,true);
        var c = new DataView(new ArrayBuffer(46)); c.setUint32(0,0x02014b50,true); c.setUint16(4,20,true); c.setUint16(6,20,true); c.setUint16(8,0x800,true); c.setUint16(10,0,true);
        c.setUint16(14,0x21,true); c.setUint32(16,crc,true); c.setUint32(20,data.length,true); c.setUint32(24,data.length,true); c.setUint16(28,nb.length,true); c.setUint32(42,off,true);
        parts.push(new Uint8Array(h.buffer), nb, data); cen.push(new Uint8Array(c.buffer), nb); off += 30 + nb.length + data.length;
      });
      var cd = cen.reduce(function(a, b){ return a + b.length; }, 0), e = new DataView(new ArrayBuffer(22));
      e.setUint32(0,0x06054b50,true); e.setUint16(8,files.length,true); e.setUint16(10,files.length,true); e.setUint32(12,cd,true); e.setUint32(16,off,true);
      var all = parts.concat(cen, [new Uint8Array(e.buffer)]), n = all.reduce(function(a, b){ return a + b.length; }, 0), out = new Uint8Array(n), p = 0;
      all.forEach(function(a){ out.set(a, p); p += a.length; }); return out;
    }
    function book(sheets){
      var ns = 'http://schemas.openxmlformats.org/', files = [];
      files.push({name:'[Content_Types].xml', data:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="' + ns + 'package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>' +
        sheets.map(function(s, i){ return '<Override PartName="/xl/worksheets/sheet' + (i + 1) + '.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'; }).join('') + '</Types>'});
      files.push({name:'_rels/.rels', data:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="' + ns + 'package/2006/relationships"><Relationship Id="rId1" Type="' + ns + 'officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'});
      var df = []; sheets.forEach(function(s, i){ if(s.af) df.push('<definedName name="_xlnm._FilterDatabase" localSheetId="' + i + '" hidden="1">\'' + s.name.replace(/'/g, "''") + '\'!' + s.af.replace(/([A-Z]+)(\d+)/g, '$$$1$$$2') + '</definedName>'); });
      files.push({name:'xl/workbook.xml', data:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="' + ns + 'spreadsheetml/2006/main" xmlns:r="' + ns + 'officeDocument/2006/relationships"><bookViews><workbookView/></bookViews><sheets>' +
        sheets.map(function(s, i){ return '<sheet name="' + xe(s.name) + '" sheetId="' + (i + 1) + '" r:id="rId' + (i + 1) + '"/>'; }).join('') + '</sheets>' + (df.length ? '<definedNames>' + df.join('') + '</definedNames>' : '') + '<calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>'});
      files.push({name:'xl/_rels/workbook.xml.rels', data:'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="' + ns + 'package/2006/relationships">' +
        sheets.map(function(s, i){ return '<Relationship Id="rId' + (i + 1) + '" Type="' + ns + 'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet' + (i + 1) + '.xml"/>'; }).join('') +
        '<Relationship Id="rId' + (sheets.length + 1) + '" Type="' + ns + 'officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'});
      files.push({name:'xl/styles.xml', data:STY});
      sheets.forEach(function(s, i){ files.push({name:'xl/worksheets/sheet' + (i + 1) + '.xml', data:sheet(s)}); });
      return zip(files);
    }
    return {book:book, col:col};
  })();

  function serial(d){ var a = d.split('-').map(Number); return Math.round(Date.UTC(a[0], a[1] - 1, a[2]) / 86400000) + 25569; }
  function workbook(D, M){
    var H = function(t){ return {v:t, s:1}; }, T = function(t){ return {v:t, s:6}; }, TM = function(f, v){ return {f:f, v:v, s:5}; }, F = function(f, v, s){ return {f:f, v:v, s:s || 2}; };
    var O = M.order, nb = O.length, last = nb + 3, title = 'Tawuniya settlement review · ' + ml(D.p0) + ' – ' + ml(D.p1) + ' · letter ' + D.letter.date + ' · ledger ' + D.acct + '/' + D.sub + ' as of ' + D.asof;
    /* Summary */
    var s1 = [[{v:'مراجعة مخالصة التعاونية — ' + title, s:7}], [],
      [H('Branch / الفرع'), H('Provider ID'), H('Letter: net claims incl. VAT / صافي المطالبات'), H('Ledger: claims net of returns / المطالبات في الدفاتر'), H('Claims difference / فرق المطالبات'),
       H('Letter: paid incl. VAT / المسدد'), H('Ledger: receipts for the period / المقبوضات'), H('Payment difference / فرق السداد'),
       H('Letter: total discounts incl. VAT / الخصومات'), H('Discounts already booked / المسجل'), H('Discounts to book / المطلوب تسجيله'),
       H('Letter: balance due incl. VAT / الرصيد المستحق'), H('Ledger balance today / رصيد الدفاتر'), H('Ledger after booking discounts / الرصيد بعد القيد'), H('Difference vs letter / الفرق')]];
    O.forEach(function(b, i){ var r = M.br[b], n = i + 4;
      s1.push([BRN[b] + ' / ' + BRA[b], r.x.prov, r.gross, r.lc, F('D' + n + '-C' + n, r.cdiff), r2(r.x.paid[0] + r.x.paid[1]), r2(r.pn + r.pv), F('G' + n + '-F' + n, r2(r.pn + r.pv - r.x.paid[0] - r.x.paid[1])),
        r.discT, r.booked, F('I' + n + '-J' + n, r.toBook), r.balT, r.lbal, F('M' + n + '-K' + n, r.after), F('N' + n + '-L' + n, r.bdiff)]); });
    var tr = [T('Total / الإجمالي'), T('')]; for(var c = 2; c < 15; c++){ var L = XL.col(c); tr.push(TM('SUM(' + L + '4:' + L + last + ')', null)); } s1.push(tr);
    s1.push([], [{v:'Ledger claims = month-end claim JVs Jan–Sep minus returns (مرتجع) and other credits. Receipts = claim and VAT receipts whose narration names a month in the period. Ledger after booking = balance today − discounts still to book; the remaining difference equals the claims difference.', s:8}]);
    /* Payment match */
    var s2 = [[{v:'مطابقة السداد — Payment match', s:7}], [], [H('Branch / الفرع'), H('Letter: paid excl. VAT'), H('Ledger: claim receipts'), H('Difference'), H('Letter: VAT paid'), H('Ledger: VAT receipts'), H('Difference'), H('Letter: total paid'), H('Ledger: total'), H('Difference')]];
    O.forEach(function(b, i){ var r = M.br[b], n = i + 4, k = BRN[b];
      s2.push([BRN[b] + ' / ' + BRA[b], r.x.paid[0], F('SUMIFS(Payments!G:G,Payments!A:A,"' + k + '",Payments!E:E,"Claim",Payments!H:H,"Yes")', r.pn), F('C' + n + '-B' + n, r.pdn),
        r.x.paid[1], F('SUMIFS(Payments!G:G,Payments!A:A,"' + k + '",Payments!E:E,"VAT",Payments!H:H,"Yes")', r.pv), F('F' + n + '-E' + n, r.pdv),
        F('B' + n + '+E' + n, r2(r.x.paid[0] + r.x.paid[1])), F('C' + n + '+F' + n, r2(r.pn + r.pv)), F('I' + n + '-H' + n, r2(r.pdn + r.pdv))]); });
    var t2 = [T('Total / الإجمالي')]; for(c = 1; c < 10; c++){ L = XL.col(c); t2.push(TM('SUM(' + L + '4:' + L + last + ')', null)); } s2.push(t2);
    /* Claims */
    var s3 = [[H('Branch / الفرع'), H('Month / الشهر'), H('Voucher / القيد'), H('Claims Dr / مدين'), H('Returns / مرتجع'), H('Other credits / دائن آخر'), H('Net claims / الصافي')]];
    O.forEach(function(b){ M.br[b].claims.forEach(function(c){ var n = s3.length + 1; s3.push([BRN[b], ml(c.mon), c.vno, c.dr, c.ret, c.oth, F('D' + n + '-E' + n + '-F' + n, c.net)]); }); });
    var cl = s3.length; s3.push([T('Total'), T(''), T(''), TM('SUBTOTAL(9,D2:D' + cl + ')'), TM('SUBTOTAL(9,E2:E' + cl + ')'), TM('SUBTOTAL(9,F2:F' + cl + ')'), TM('SUBTOTAL(9,G2:G' + cl + ')')]);
    /* Payments */
    var s4 = [[H('Branch / الفرع'), H('Voucher / السند'), H('Date / التاريخ'), H('Month paid / الشهر المسدد'), H('Type / النوع'), H('Period key'), H('Amount / المبلغ'), H('In this settlement? / ضمن المخالصة')]];
    O.forEach(function(b){ M.br[b].pays.slice().sort(function(a, c){ return a.mon < c.mon ? -1 : a.mon > c.mon ? 1 : a.kind < c.kind ? 1 : -1; }).forEach(function(p){
      s4.push([BRN[b], p.vno, {v:serial(p.dt), s:3}, D.periods[p.mon] || ml(p.mon), p.kind === 'vat' ? 'VAT' : 'Claim', p.mon, p.amt, p.inp ? 'Yes' : 'No']); }); });
    var pl = s4.length; s4.push([T('Total shown'), T(''), T(''), T(''), T(''), T(''), TM('SUBTOTAL(9,G2:G' + pl + ')'), T('')]);
    /* Discounts */
    var s5 = [[H('Branch / الفرع'), H('Discount / الخصم'), H('البيان'), H('Excl. VAT / قبل الضريبة'), H('VAT / الضريبة'), H('Incl. VAT / شامل الضريبة'), H('% of net claims excl. VAT / النسبة'), H('Booked in ledger / المسجل'), H('To book (credit note) / المطلوب قيده')]];
    O.forEach(function(b){ var x = D.br[b]; DT.forEach(function(t){ var n = s5.length + 1, v = x[t[0]], bk = 0;
      s5.push([BRN[b], t[1], t[2], v[0], v[1], F('D' + n + '+E' + n, r2(v[0] + v[1])), F('IFERROR(D' + n + '/' + x.net[0] + ',0)', v[0] / x.net[0], 4), bk, F('F' + n + '-H' + n, r2(v[0] + v[1] - bk))]); }); });
    var dl = s5.length; s5.push([T('Total'), T(''), T(''), TM('SUBTOTAL(9,D2:D' + dl + ')'), TM('SUBTOTAL(9,E2:E' + dl + ')'), TM('SUBTOTAL(9,F2:F' + dl + ')'), {f:'IFERROR(D' + (dl + 1) + '/' + M.tot.net[0] + ',0)', s:10}, TM('SUBTOTAL(9,H2:H' + dl + ')'), TM('SUBTOTAL(9,I2:I' + dl + ')')]);
    s5.push([], [T('By type, all branches / حسب النوع'), T(''), T(''), T('Excl. VAT'), T('VAT'), T('Incl. VAT'), T('% of net')]);
    DT.forEach(function(t){ var n = s5.length + 1; s5.push([t[1], '', t[2], F('SUMIFS(D2:D' + dl + ',B2:B' + dl + ',"' + t[1] + '")', M.tot[t[0]][0]), F('SUMIFS(E2:E' + dl + ',B2:B' + dl + ',"' + t[1] + '")', M.tot[t[0]][1]), F('D' + n + '+E' + n, r2(M.tot[t[0]][0] + M.tot[t[0]][1])), F('IFERROR(D' + n + '/' + M.tot.net[0] + ',0)', M.tot[t[0]][0] / M.tot.net[0], 4)]); });
    /* Letter figures */
    var s6 = [[H('Line (as printed in the letter)'), H('البند')].concat(O.map(function(b){ return H(BRN[b]); })).concat([H('Total')])];
    var LL = [['Total net amount without VAT','صافي المطالبات قبل الضريبة','net',0],['Total net VAT amount','ضريبة المطالبات','net',1],['Early payment discount','خصم تعجيل دفع','early',0],['VAT on early payment discount','ضريبة خصم التعجيل','early',1],
      ['Volume discount','خصم حجم عمل','vol',0],['VAT on volume discount','ضريبة خصم الحجم','vol',1],['Other discount','خصومات أخرى','other',0],['Medical & technical discount','مرفوضات طبية وفنية','mt',0],['VAT on medical & technical','ضريبة المرفوضات','mt',1],
      ['DRG rejection','مرفوضات DRG','drg',0],['Total discount','إجمالي الخصومات','disc',0],['Total VAT on discount','ضريبة الخصومات','disc',1],['Actual paid amount without VAT','المسدد قبل الضريبة','paid',0],['Actual paid amount of VAT','ضريبة مسددة','paid',1],
      ['Approved to be paid without VAT','المعتمد قبل الضريبة','appr',0],['Approved to be paid of VAT','ضريبة معتمدة','appr',1],['Balance amount to be paid without VAT','الرصيد قبل الضريبة','bal',0],['Balance amount to be paid of VAT','ضريبة الرصيد','bal',1]];
    LL.forEach(function(l){ var n = s6.length + 1, last6 = XL.col(1 + nb); s6.push([l[0], l[1]].concat(O.map(function(b){ return D.br[b][l[2]][l[3]]; })).concat([F('SUM(C' + n + ':' + last6 + n + ')', M.tot[l[2]][l[3]])])); });
    s6.push([], ['Provider ID', 'رقم المزود'].concat(O.map(function(b){ return D.br[b].prov; })), ['Credit note no.', 'رقم الإشعار الدائن'].concat(O.map(function(b){ return D.br[b].cn; })), ['Second-party VAT no. in letter', 'الرقم الضريبي للطرف الثاني'].concat(O.map(function(b){ return D.br[b].vat_no; })));
    /* Points */
    var s7 = [[H('Priority / الأولوية'), H('Point / الملاحظة'), H('Detail'), H('بالعربي')]];
    M.flags.forEach(function(f){ s7.push([{v:f[0] === 'high' ? 'High' : f[0] === 'med' ? 'Medium' : 'Low', s:f[0] === 'high' ? 9 : 8}, {v:f[1], s:8}, {v:f[2], s:8}, {v:f[3], s:8}]); });
    return XL.book([
      {name:'Summary', rows:s1, widths:[22,11,17,17,14,17,17,14,17,15,17,17,17,17,14], freeze:3},
      {name:'Payment match', rows:s2, widths:[22,17,17,13,16,16,13,17,17,13], freeze:3},
      {name:'Claims', rows:s3, widths:[13,11,15,15,13,13,15], freeze:1, af:'A1:G' + cl},
      {name:'Payments', rows:s4, widths:[13,15,12,26,8,12,15,12], freeze:1, af:'A1:H' + pl},
      {name:'Discounts', rows:s5, widths:[30,30,22,15,13,15,13,14,15], freeze:1, af:'A1:I' + dl},
      {name:'Letter figures', rows:s6, widths:[36,24].concat(O.map(function(){ return 16; })).concat([17]), freeze:1},
      {name:'Points', rows:s7, widths:[10,34,90,48], freeze:1}
    ]);
  }

  /* ---------------- view ---------------- */
  var CSS = '.taw-p .taw-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:4px 0 14px}.taw-p .taw-bar button.f{border:1px solid var(--border);background:var(--surface);color:var(--ink);border-radius:16px;padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer}' +
    '.taw-p .taw-bar button.f.on{background:var(--accent);border-color:var(--accent);color:#fff}.taw-p .taw-x{margin-inline-start:auto;display:flex;gap:8px;align-items:center}.taw-p .taw-x button{border:0;border-radius:8px;padding:7px 14px;font:inherit;font-weight:600;font-size:12.5px;cursor:pointer;background:var(--accent);color:#fff}' +
    '.taw-p .taw-x span{font-size:12px;color:var(--ink-muted)}.taw-p .taw-k{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-bottom:14px}.taw-p .taw-k>div{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}' +
    '.taw-p .taw-k b{display:block;font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:var(--ink-faint);font-weight:600}.taw-p .taw-k .v{font-size:21px;font-weight:700;margin:4px 0 2px;font-variant-numeric:tabular-nums}.taw-p .taw-k small{color:var(--ink-muted);font-size:12px}' +
    '.taw-p .ok{color:var(--good)}.taw-p .bad{color:var(--critical)}.taw-p .wr{color:var(--warning)}.taw-p table td.n,.taw-p table th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.taw-p tr.tot td{font-weight:700;border-top:2px solid var(--accent-line)}' +
    '.taw-p tr.out td{color:var(--ink-faint)}.taw-p .ar{font-family:Cairo,"IBM Plex Sans",sans-serif;color:var(--ink-muted);font-size:12px}.taw-p .flg{display:grid;gap:8px}.taw-p .flg>div{border:1px solid var(--border);border-inline-start:4px solid var(--warning);border-radius:8px;padding:9px 12px;background:var(--surface)}' +
    '.taw-p .flg>div.high{border-inline-start-color:var(--critical);background:var(--flag-bg)}.taw-p .flg>div.low{border-inline-start-color:var(--ink-faint)}.taw-p .flg b{display:block;margin-bottom:2px}.taw-p details{margin-top:10px}.taw-p details summary{cursor:pointer;color:var(--accent);font-weight:600;font-size:13px}' +
    '.taw-p .meta{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12.5px;color:var(--ink-muted);margin:-4px 0 12px}.taw-p .meta b{color:var(--ink)}';
  function render(D){
    var M = model(D), st = {b:'ALL'};
    var p = document.createElement('div'); p.className = 'taw-p arr-ptaw'; p.hidden = true;
    var css = document.createElement('style'); css.textContent = CSS; p.appendChild(css);
    var body = document.createElement('div'); p.appendChild(body);
    var cls = function(v, t){ return Math.abs(v) < (t || 0.01) ? 'ok' : 'bad'; };
    function draw(){
      var O = st.b === 'ALL' ? M.order : [st.b], one = st.b !== 'ALL';
      var g = function(k){ return one ? M.br[st.b][k] : M.tot[k]; }, gx = function(k){ return one ? D.br[st.b][k] : M.tot[k]; };
      var h = '';
      h += '<div class="meta"><span>Letter: <b>' + esc(D.letter.kind) + '</b> dated <b>' + D.letter.date + '</b></span><span>Period <b>' + ml(D.p0) + ' – ' + ml(D.p1) + '</b></span><span>Ledger <b>' + D.acct + ' / ' + D.sub + '</b> to <b>' + D.asof + '</b></span><span>' + (D.letter.signed ? '<b class="ok">Signed</b>' : '<b class="wr">Initial — not signed yet</b>') + '</span></div>';
      h += '<div class="taw-bar">' + ['ALL'].concat(M.order).map(function(b){ return '<button type="button" class="f' + (st.b === b ? ' on' : '') + '" data-b="' + b + '">' + (b === 'ALL' ? 'All branches' : BRN[b]) + '</button>'; }).join('') +
        '<div class="taw-x"><span class="m"></span><button type="button" class="dl">⤓ Download Excel (.xlsx)</button></div></div>';
      var gross = g('gross'), lc = g('lc'), cd = g('cdiff');
      h += '<div class="taw-k">' +
        '<div><b>Claims · مطابقة المطالبات</b><div class="v ' + cls(cd, 1) + '">' + n2(cd) + '</div><small>letter ' + n2(gross) + ' · ledger ' + n2(lc) + '</small></div>' +
        '<div><b>Payments · مطابقة السداد</b><div class="v ' + cls(g('pdn') + g('pdv')) + '">' + n2(r2(g('pdn') + g('pdv'))) + '</div><small>letter ' + n2(r2(gx('paid')[0] + gx('paid')[1])) + ' · ledger ' + n2(r2(g('pn') + g('pv'))) + '</small></div>' +
        '<div><b>Discounts · الخصومات</b><div class="v">' + n2(g('discT')) + '</div><small>' + pc(gx('disc')[0] / gx('net')[0]) + ' of net · booked ' + n2(g('booked')) + '</small></div>' +
        '<div><b>Balance due · الرصيد المستحق</b><div class="v">' + n2(g('balT')) + '</div><small>ledger after booking ' + n2(g('after')) + ' · <span class="' + cls(g('bdiff'), 1) + '">diff ' + n2(g('bdiff')) + '</span></small></div></div>';
      /* 1 claims */
      h += '<div class="card"><h3>1 · Claims balance reconciliation <span class="ar">مطابقة رصيد المطالبات</span></h3><p class="card-sub">Net claims in the letter (incl. VAT) against the month-end claim JVs on ' + D.acct + '/' + D.sub + ' for ' + ml(D.p0) + ' – ' + ml(D.p1) + ', net of patient returns (مرتجع)</p>' +
        '<div class="aud-scroll" style="max-height:none"><table class="aud-t"><thead><tr><th>Branch</th><th>Provider</th><th class="n">Letter excl. VAT</th><th class="n">Letter VAT</th><th class="n">Letter incl. VAT</th><th class="n">Ledger claims</th><th class="n">Difference</th><th class="n">Diff %</th></tr></thead><tbody>' +
        O.map(function(b){ var r = M.br[b]; return '<tr><td>' + BRN[b] + ' <span class="ar">' + BRA[b] + '</span></td><td>' + r.x.prov + '</td><td class="n">' + n2(r.x.net[0]) + '</td><td class="n">' + n2(r.x.net[1]) + '</td><td class="n">' + n2(r.gross) + '</td><td class="n">' + n2(r.lc) + '</td><td class="n ' + cls(r.cdiff, 1) + '">' + n2(r.cdiff) + '</td><td class="n">' + pc(r.cdiff / r.gross) + '</td></tr>'; }).join('') +
        (one ? '' : '<tr class="tot"><td>Total</td><td></td><td class="n">' + n2(M.tot.net[0]) + '</td><td class="n">' + n2(M.tot.net[1]) + '</td><td class="n">' + n2(M.tot.gross) + '</td><td class="n">' + n2(M.tot.lc) + '</td><td class="n ' + cls(M.tot.cdiff, 1) + '">' + n2(M.tot.cdiff) + '</td><td class="n">' + pc(M.tot.cdiff / M.tot.gross) + '</td></tr>') +
        '</tbody></table></div><details><summary>Ledger claims by month</summary><div class="aud-scroll" style="max-height:420px"><table class="aud-t"><thead><tr><th>Branch</th><th>Month</th><th>Voucher</th><th class="n">Claims Dr</th><th class="n">Returns</th><th class="n">Other credits</th><th class="n">Net</th><th>Paid?</th></tr></thead><tbody>' +
        O.map(function(b){ var r = M.br[b]; return r.claims.map(function(c){ var pn = r.pays.some(function(p){ return p.mon === c.mon && p.kind === 'net'; }), pv = r.pays.some(function(p){ return p.mon === c.mon && p.kind === 'vat'; });
          return '<tr><td>' + BRN[b] + '</td><td>' + ml(c.mon) + '</td><td>' + c.vno + '</td><td class="n">' + n2(c.dr) + '</td><td class="n">' + n2(c.ret) + '</td><td class="n">' + n2(c.oth) + '</td><td class="n">' + n2(c.net) + '</td><td>' + (pn ? 'claim ✓' : '<span class="wr">claim —</span>') + ' · ' + (pv ? 'VAT ✓' : '<span class="wr">VAT —</span>') + '</td></tr>'; }).join(''); }).join('') +
        '</tbody></table></div></details></div>';
      /* 2 payments */
      h += '<div class="card"><h3>2 · Payment reconciliation <span class="ar">مطابقة السداد</span></h3><p class="card-sub">“Actual paid” in the letter against receipts on ' + D.sub + ' whose narration names a month inside the settlement period (claim and VAT receipts separately)</p>' +
        '<div class="aud-scroll" style="max-height:none"><table class="aud-t"><thead><tr><th>Branch</th><th class="n">Letter paid excl. VAT</th><th class="n">Ledger claim receipts</th><th class="n">Diff</th><th class="n">Letter VAT paid</th><th class="n">Ledger VAT receipts</th><th class="n">Diff</th><th>Result</th></tr></thead><tbody>' +
        O.map(function(b){ var r = M.br[b], okk = Math.abs(r.pdn) < 0.01 && Math.abs(r.pdv) < 0.01; return '<tr><td>' + BRN[b] + '</td><td class="n">' + n2(r.x.paid[0]) + '</td><td class="n">' + n2(r.pn) + '</td><td class="n ' + cls(r.pdn) + '">' + n2(r.pdn) + '</td><td class="n">' + n2(r.x.paid[1]) + '</td><td class="n">' + n2(r.pv) + '</td><td class="n ' + cls(r.pdv) + '">' + n2(r.pdv) + '</td><td>' + (okk ? '<span class="pill ok">Matches</span>' : '<span class="pill bad">Check</span>') + (r.unpaid.length ? ' <span class="ar">not yet received: ' + r.unpaid.map(function(u){ return esc(ml(u.slice(0,7)) + u.slice(7)); }).join(', ') + '</span>' : '') + '</td></tr>'; }).join('') +
        (one ? '' : '<tr class="tot"><td>Total</td><td class="n">' + n2(M.tot.paid[0]) + '</td><td class="n">' + n2(M.tot.pn) + '</td><td class="n">' + n2(M.tot.pdn) + '</td><td class="n">' + n2(M.tot.paid[1]) + '</td><td class="n">' + n2(M.tot.pv) + '</td><td class="n">' + n2(M.tot.pdv) + '</td><td></td></tr>') +
        '</tbody></table></div><details><summary>Receipts on ' + D.sub + ' in ' + D.asof.slice(0,4) + ' (greyed = belongs to another period)</summary><div class="aud-scroll" style="max-height:420px"><table class="aud-t"><thead><tr><th>Branch</th><th>Voucher</th><th>Date</th><th>Month paid</th><th>Type</th><th class="n">Amount</th></tr></thead><tbody>' +
        O.map(function(b){ return M.br[b].pays.slice().sort(function(a, c){ return a.mon < c.mon ? -1 : a.mon > c.mon ? 1 : a.kind < c.kind ? 1 : -1; }).map(function(q){ return '<tr' + (q.inp ? '' : ' class="out"') + '><td>' + BRN[b] + '</td><td>' + q.vno + '</td><td>' + q.dt + '</td><td>' + esc(D.periods[q.mon] || ml(q.mon)) + '</td><td>' + (q.kind === 'vat' ? 'VAT' : 'Claim') + '</td><td class="n">' + n2(q.amt) + '</td></tr>'; }).join(''); }).join('') +
        '</tbody></table></div></details></div>';
      /* 3 discounts */
      h += '<div class="card"><h3>3 · Discount details <span class="ar">تفاصيل الخصومات — مرفوضات · حجم عمل · خصم تعجيل دفع</span></h3><p class="card-sub">As stated in the letter; % is of net claims excl. VAT. “To book” = the credit notes still to be entered on the Exsys Credit Note screen once the settlement is signed</p>' +
        '<div class="aud-scroll" style="max-height:none"><table class="aud-t"><thead><tr><th>Discount</th>' + O.map(function(b){ return '<th class="n">' + BRN[b] + '</th>'; }).join('') + (one ? '' : '<th class="n">Total</th>') + '<th class="n">VAT</th><th class="n">Incl. VAT</th><th class="n">% of net</th></tr></thead><tbody>' +
        DT.map(function(t){ var tot = one ? D.br[st.b][t[0]] : M.tot[t[0]], net0 = one ? D.br[st.b].net[0] : M.tot.net[0]; if(!tot[0] && !tot[1]) return '';
          return '<tr><td>' + t[1] + ' <span class="ar">' + t[2] + '</span></td>' + O.map(function(b){ return '<td class="n">' + n2(D.br[b][t[0]][0]) + '<br><span class="ar">' + pc(D.br[b][t[0]][0] / D.br[b].net[0]) + '</span></td>'; }).join('') + (one ? '' : '<td class="n">' + n2(tot[0]) + '</td>') + '<td class="n">' + n2(tot[1]) + '</td><td class="n">' + n2(tot[0] + tot[1]) + '</td><td class="n">' + pc(tot[0] / net0) + '</td></tr>'; }).join('') +
        (function(){ var tot = one ? D.br[st.b].disc : M.tot.disc, net0 = one ? D.br[st.b].net[0] : M.tot.net[0]; return '<tr class="tot"><td>Total discounts</td>' + O.map(function(b){ return '<td class="n">' + n2(D.br[b].disc[0]) + '</td>'; }).join('') + (one ? '' : '<td class="n">' + n2(tot[0]) + '</td>') + '<td class="n">' + n2(tot[1]) + '</td><td class="n">' + n2(tot[0] + tot[1]) + '</td><td class="n">' + pc(tot[0] / net0) + '</td></tr>'; })() +
        '</tbody></table></div><p class="card-sub" style="margin-top:10px">Booked so far for this period: <b>' + n2(g('booked')) + '</b> · still to book: <b>' + n2(g('toBook')) + '</b> (credit-note no. in the letter: ' + O.map(function(b){ return BRN[b] + ' ' + D.br[b].cn; }).join(', ') + ')</p></div>';
      /* 4 balance */
      h += '<div class="card"><h3>4 · Balance after the settlement <span class="ar">الرصيد بعد المخالصة</span></h3><p class="card-sub">Ledger balance today − discounts still to book = what the ledger will show; it should equal the letter’s balance due. Today’s balance holds only ' + ml(D.p0) + ' – ' + ml(D.p1) + ' items (earlier settlements are closed)</p>' +
        '<div class="aud-scroll" style="max-height:none"><table class="aud-t"><thead><tr><th>Branch</th><th class="n">Ledger balance today</th><th class="n">− Discounts to book</th><th class="n">= Ledger after booking</th><th class="n">Letter balance due</th><th class="n">Difference</th><th>Explained by</th></tr></thead><tbody>' +
        O.map(function(b){ var r = M.br[b]; return '<tr><td>' + BRN[b] + '</td><td class="n">' + n2(r.lbal) + '</td><td class="n">' + n2(r.toBook) + '</td><td class="n">' + n2(r.after) + '</td><td class="n">' + n2(r.balT) + '</td><td class="n ' + cls(r.bdiff, 1) + '">' + n2(r.bdiff) + '</td><td>' + (Math.abs(r.bdiff - r.cdiff) < 0.05 ? 'claims difference' : 'claims ' + n2(r.cdiff) + ' + payments ' + n2(r.pdn + r.pdv)) + '</td></tr>'; }).join('') +
        (one ? '' : '<tr class="tot"><td>Total</td><td class="n">' + n2(M.tot.lbal) + '</td><td class="n">' + n2(M.tot.toBook) + '</td><td class="n">' + n2(M.tot.after) + '</td><td class="n">' + n2(M.tot.balT) + '</td><td class="n">' + n2(M.tot.bdiff) + '</td><td></td></tr>') + '</tbody></table></div></div>';
      /* 5 flags */
      h += '<div class="card"><h3>5 · Points to raise before signing <span class="ar">ملاحظات قبل التوقيع</span></h3><div class="flg">' +
        M.flags.map(function(f){ return '<div class="' + f[0] + '"><b>' + esc(f[1]) + '</b>' + esc(f[2]) + '<div class="ar" dir="rtl">' + esc(f[3]) + '</div></div>'; }).join('') + '</div></div>';
      body.innerHTML = h;
      body.querySelectorAll('button.f').forEach(function(bt){ bt.onclick = function(){ st.b = bt.dataset.b; draw(); }; });
      var dlb = body.querySelector('button.dl'), msg = body.querySelector('.taw-x .m');
      dlb.onclick = async function(){
        dlb.disabled = true; msg.textContent = 'Preparing…';
        var fn = 'Tawuniya_Settlement_Review_' + D.p0 + '_to_' + D.p1 + '_' + D.asof + '.xlsx', blob;
        try { blob = new Blob([workbook(D, M)], {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}); }
        catch(e){ console.error(e); msg.textContent = 'The Excel file could not be built.'; dlb.disabled = false; return; }
        try {
          var dl = window.claude && window.claude.use ? await window.claude.use('downloads') : null;
          if(dl){ await dl.save({filename:fn, data:blob}); msg.textContent = 'Saved.'; }
          else { var a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = fn; document.body.appendChild(a); a.click(); a.remove(); msg.textContent = 'Download started.'; }
        } catch(e){ msg.textContent = e && e.code === 'declined' ? 'Download cancelled.' : 'The file could not be downloaded here.'; }
        dlb.disabled = false;
      };
    }
    draw();
    return p;
  }

  function mount(){
    var D = window.TAW_DATA, sec = document.getElementById('sec-ar-rec');
    var tabs = sec && sec.querySelector('.arr-tabs');
    if(!D || !tabs) return false;
    if(tabs.querySelector('[data-t="taw"]')) return true;
    var btn = document.createElement('button'); btn.type = 'button'; btn.setAttribute('role','tab'); btn.dataset.t = 'taw';
    btn.innerHTML = 'Tawuniya review <small>مراجعة مخالصة التعاونية</small>';
    tabs.appendChild(btn);
    var panel = render(D); sec.appendChild(panel);
    tabs.addEventListener('click', function(e){
      var b = e.target.closest('button'); if(!b || !tabs.contains(b)) return;
      if(b === btn){
        tabs.querySelectorAll('button').forEach(function(x){ x.classList.toggle('on', x === btn); x.setAttribute('aria-selected', x === btn ? 'true' : 'false'); });
        Array.prototype.forEach.call(sec.children, function(ch){ if(ch !== tabs && ch !== panel && /(^|\s)arr-p/.test(ch.className)) ch.hidden = true; });
        panel.hidden = false;
      } else panel.hidden = true;
    });
    return true;
  }
  window.__tawMount = mount; window.__tawWorkbook = function(){ var D = window.TAW_DATA; return workbook(D, model(D)); };
  if(typeof document !== 'undefined'){
    if(!mount()){ var n = 0, t = setInterval(function(){ if(mount() || ++n > 120) clearInterval(t); }, 500); }
  }
})();
