# AP / supplier rules (Al Faihaa)

- Suppliers send statements monthly (days 1–15) by email; reconcile each against the Cure balance up to the previous month-end. If there is a difference, reconcile the whole statement.
- Supplier balance = vouchers of ALL branches, cancelled excluded.
- Due date: last day of (target month − credit days), all months treated as 30 days (October dues, 90-day credit → due up to 31/07).
- Due amount = balance at the cut-off date − every later payment (including transfers whose text has no «سداد», e.g. «تحويل لشركة…», «دفعة…»). Only returns / credit notes are "other". A payment can appear twice (transfer + «سداد باقي المستحق») — count both.
- A due amount can never exceed the supplier's Cure balance. If it does, the method is wrong — stop and fix.
- Suppliers flagged `prior_approval` in the site config need approval before payment: show a hint, never include silently.
- The bank file (bulk transfer CSV) is prepared for a human to upload. Agents never send it.

## Added after the 2026-10 run
- A supplier whose credit term is a Cure default (`ap.default_credit_term_codes`, or the 30-day creation default) is ON HOLD — never in the bank file — until the term is confirmed from the contract. Show 60/90-day alternatives for information only.
- The bank file carries a DRAFT header and a status column; only suppliers with a confirmed (non-default) term go in it.
- Due method: balance at cut-off − later payments − later non-cash reductions (e.g. water deductions, fee reversals). Never clip a due to the balance; if a due exceeds the balance the method is wrong — stop.
- Prior-approval suppliers are matched by supplier CODE from the site config, never by name.
- Negative branch balances from old inter-branch payments (liability booked in another branch) are explained as info, not payables.
