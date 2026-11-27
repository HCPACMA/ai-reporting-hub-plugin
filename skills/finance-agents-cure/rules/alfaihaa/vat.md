# VAT rules (Al Faihaa)

- From Sept 2026 insurers get one monthly summary invoice; it is what goes to ZATCA and must equal the insurer share booked on its GL account. Patient share is reported in detail.
- A summary invoice can be issued up to 15 days after month end; its supply period is the month, so it belongs to that month's return.
- Months before Sept 2026 stay at invoice level.
- Patient share never gets a credit note. Credit notes against detailed insurer invoices cover the insurer share only.
- Insurer-settlement credit notes reduce credit revenue and the drug-sales margin revenue (4200027).

## Accounts and monthly cycle (confirmed 2026-11-19)
- Input VAT `vat_input` (Dr), output VAT `vat_output` (Cr), settlement `vat_settlement`, all under the VAT parent account.
- After month end and before payment, the accountant closes input and output into the settlement account (JV text contains `monthly_closing_jv_text`); the VAT payment is made from the settlement account (its debit).
- Return ↔ trial balance reconciliation follows the CFO-Cure method (`vat.reconciliation_method`): output = output account (Cr − Dr) vs return VAT; input = input account (Dr − Cr) + settlement-account effect vs return input, less the prior-month VAT payment; sales = TB revenue adjusted as in that spec. Exclude the monthly VAT closing JV and year-end closing when reading movements.
- A month where adjusted TB sales fall more than 10 % below the return is flagged "revenue not posted yet", not as an error.
- After the payment, the settlement account should net to zero for that month; a residual is a finding.

## Added after the 2026-10 run
- ZATCA status = `SEND_STATUS` and `REPORTING_OR_CLEARANCE_STATUS` (not `SEND_FLAG` alone). Scan unsent / unanswered / rejected documents for every open month, not only the current one.
- Any line of the monthly VAT closing JV on a non-VAT account is a finding.
- Check invoice type vs customer type (simplified invoice issued to a business customer).
