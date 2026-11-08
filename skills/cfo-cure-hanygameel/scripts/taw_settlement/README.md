# AR Reconciliation › Tawuniya review (sub-tab) — 7 Nov 2026

Live Desk artifact: `ar-tawuniya.js` (data + code), loaded from index.html between `<!--TAW-REVIEW:start -->` and `<!--TAW-REVIEW:end -->`.
It appends a "Tawuniya review" button to `#sec-ar-rec .arr-tabs` and its own panel (works whatever sub-tabs exist).

Sections: 1 claims balance reconciliation · 2 payment reconciliation (claim + VAT receipts by month named in the narration)
· 3 discount details (early payment / volume / medical-technical rejections / other / DRG, % of net, booked vs to book)
· 4 balance after the settlement · 5 points to raise. Excel button → 7 sheets (Summary, Payment match [SUMIFS on Payments],
Claims, Payments, Discounts, Letter figures, Points), formulas with cached values.

Refresh: run `taw_settlement.sql` (P0/P1 = settlement period) on Cure; update C / P / LBAL (and `cns` = credit notes booked
for the period, list of {amt}) in `build_data.py`; letter figures (L) come from the PDFs. `python3 build_data.py` asserts
payments = letter and claims − receipts = ledger balance; then `python3 build_js.py` and republish `ar-tawuniya.js`.
A new settlement letter = new L block + period P0/P1.
