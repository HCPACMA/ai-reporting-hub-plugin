# Modeling Desk — Zakat section (Implementing Regulation 1445H)

Added 25 Sep 2026. It is one sidebar entry, **الزكاة · Zakat**, in Arabic (right-to-left). It opens on six tabs:
- the return
- equity & similar
- liabilities
- deductions
- net profit & expenses (with the fines list)
- zakat provision & accrual

Every line in these tabs shows its article number.

## Scope and decisions (owner, 25 Sep 2026)
- **Years:** 2024 onward. The open year 2026 is shown as an estimate with a monthly accrual.
- **Source:** EXSYS only, all four databases, posted and open vouchers. The owner's workbook is not used as a source.
- **Starting point:** net profit **before the year's zakat**.
- **Government fines and violations:** these are not an accepted expense. They are added to profit before zakat to reach adjusted profit.
  - They are read from the ledger lines in accounts 314xxxx whose description mentions مخالفة or غرامة.
  - These are netted against their reversal and reclassification entries.
  - Lawyers' fees, grievance-board fees and patient compensation are excluded from fines.
- **Zakat differences for earlier years** (assessments or corrections): these are an accepted expense or taxable income, so they stay inside profit.
- **Equity** includes retained earnings with the year's profit before zakat. The year's zakat provision is therefore not added again.
- **Leave provision 867,307 (2111003):** the owner says it is already included in liabilities. The ledger shows the end-of-service balance of 8,485,324 is account 2111001 alone, so the desk adds the leave provision under Art. 24 and flags the difference.

## Results
| Year | Profit before zakat | Fines added | Base | Zakat | Year's provision booked | Difference |
|---|---|---|---|---|---|---|
| 2024 | −3,692,793 | 16,175 | 6,736,968 | 174,134 | 212,487 (−38,771 corrected in Apr 2025) | −38,353 |
| 2025 | 1,961,653 | 129,650 | 8,228,809 | 212,113 | 186,414 | +25,698 |
| 2026 (estimate) | 4,505,967 | 96,500 | 11,032,666 | 284,387 | 0 | accrual due 208,031 |

- **Rate:** 2.5% ÷ 354 × days, which is 2.5777% (2024: 366 days).
- **2025 fines in the ledger total 129,650.** This is the 111,400 cases & violations provision plus 18,250 booked during the year. The workbook uses 111,400.
- **To confirm with the zakat adviser:** the 111,400 provision sits in equity (Art. 24), and the fines behind it are also added through the profit difference (Art. 23(3)).

## Files
- **Kit:** `scripts/zak/` (build_zakat.py, patch.py, exp_class.json), `templates/zak.js`, `templates/zak.css`, SPEC §14.
- **Refresh:** job `zak_lines` in batch A. `build` rebuilds `DATA.zak` last.

## Reconciliation 2025: owner's workbook vs the desk (25 Sep 2026)
| | Workbook | Desk (EXSYS) | Difference |
|---|---|---|---|
| Equity & similar | 56,071,807.40 | 56,069,607.38 | −2,200.02 |
| Liabilities added | 10,985,324.00 | 11,852,630.65 | +867,306.65 (leave provision 2111003) |
| Profit difference added (Art. 23(3)) | 0 (D24 blank) | 129,650.00 | +129,650.00 (fines) |
| Deductions | 59,825,279.00 | 59,823,079.53 | −2,199.47 |
| **Base** | **7,231,852.40** | **8,228,808.50** | **+996,956.10** |
| **Zakat** | **186,414.27** | **212,112.65** | **+25,698.38** |

Causes of the zakat difference:
- **Leave provision 867,306.65: +22,356.42.** Account 2111003 is separate from end-of-service (2111001 = 8,485,324 exactly). Art. 24 adds it as a liability.
- **Fines 129,650: +3,341.97.** The workbook adds 111,400 to profit but never carries it into the base (D24 is blank). Art. 23(3) requires it. The ledger's 2025 fines are 129,650, not 111,400.

No net effect on the base:
- **Depreciation of 2,199.96** (JV1-25/04126–04137, created 20 Jun 2026, 183.33 × 12 on account 1111008) lowers both profit and net fixed assets.
- **4,439.26:** retained earnings are lower and the owner account (2126001) is higher by the same amount. This is probably an audit reclassification that was not posted in EXSYS.

Other workbook vs ledger differences:
- Adjusted profit: workbook 2,079,691.74, desk 2,091,302.52. The minimum base does not apply, so this has no effect.
- Current assets are 131,569 higher and current liabilities 127,131 higher in the workbook (presentation). No effect, because current liabilities stay below current assets.
