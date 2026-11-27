# AR & insurance receivables rules (Al Faihaa)

Control account: `accounts.ar_insurance_control` (1240007). Each insurer is a sub-account with its own customer groups.

## Identity
- Every insurer account/code is its own company, never paired with another of the same name (e.g. 100013 / 100184 are separate customers under separate groups).
- An insurer may work alone, then move to a TPA, then another TPA: each account may sit under a different customer group. A wrong attachment is not a wrong posting.
- A claim's branch comes from its cost centre (prefix 01 Riyadh, 02 Buraydah 1, 03 Buraydah 2, 04 Rafha). A payment's branch and the months it settles come from its journal narration.

## Payment review
- Verify the claim from Cure on the sub-account the payment was posted to — not from the attached claim file. Payment must not exceed the customer's claims.
- A month's claim excludes credit-note lines (`CREDIT_NOTE_FROM`). Returns reduce the month of the ORIGINAL invoice.
- A voucher paying several months is allocated line by line to each month named in its narration — never all on the first month, no surplus carry-forward.
- Do not flag "registered later than the payment month": insurers always send details late.
- A transfer covering several branches is checked against the attachment's per-branch rows.
- Mistaken transfers that were returned reduce the paid amount of their month (not an overpayment).
- Check any "payments exceed claim" flag against the Accounts Statement before reporting it.
- Incomplete or missing claim attachments are ignored; rely on the customer account in Cure.
- Rejections, provision closures, credit notes, special discounts, volume (حجم عمل) and early-payment discounts, penalties and violations all count as payments.
- Amounts covering more than one month are spread pro rata: each month's share = its remaining claim ÷ total remaining over the period. A provision applies to the whole company, spread across branches the same way.

## TPA specifics
- GlobeMed volume rebate on a remittance needs a separate credit note on the insurer's account — check every GlobeMed payment.
- GlobeMed "Chq #" is the transfer date (ddmmyy); rows with the same Chq # are one transfer, possibly across several monthly reports. Use the Billing Month column, not the transfer date.
- GlobeMed "approved" counts only after the settlement is signed; until then the months stay at gross claim.

## Settlements (مخالصات)
- Settlement payments cover a period and are not matched to individual claims.
- Each insurer has one last signed settlement date, applied across all branches. That date's balance is the opening balance; later receipts covering the settled period are subtracted from it. After payment the balance should be zero; if not, rejections were probably not closed properly.
- Which period a post-settlement payment belongs to is read from the narration, not assumed oldest-first.
- Some insurers confirm with an electronic stamp only; for those, only our own signature is checked.
- Rafha is the only branch that sends claims and receives payment details directly through NPHIES.

## Added after the 2026-10 pilot (chief-accountant review)
- A credit note or rejection closing is deducted with ALL its lines, including its VAT line (`VAT_CREDIT_NOTE_FROM`), never the net line alone.
- Pro-rata formula, exactly: share(month m) = amount × remaining_claim(m) ÷ Σ remaining_claim(all months of the period), where remaining_claim = claim − payments − credit notes already allocated to that month. Never weight by gross claim.
- Before raising "payment exceeds claim", list as context the open claims of the same insurer's OTHER sub-accounts on that branch (a likely wrong-sub-account posting) — but never merge the accounts.
