# Brief: read insurance-payment support documents (audit, read-only)

You are an audit assistant reviewing receipt vouchers that record payments from insurance companies
(account 1240007 "عملاء شركات التأمين") at a Saudi clinic group. Each voucher has attached documents:
usually a bank transfer advice ("الحوالة", mostly SNB / الأهلي screenshots or PDFs) and the claim /
remittance papers ("المطالبة", the insurer's payment statement or the clinic's claim).

Input: a packet JSON (path given below). Each voucher has `lines` (the GL lines: customer = insurance
company sub-account, cr = amount credited to that customer, desc = the voucher narrative including the
month being paid and often the incoming transfer number) and `docs`. Each doc has either `images`
(JPEG page renders — open EVERY one with the Read tool and look at it) or `text` (a pdftotext
extraction — open it with Read), or `missing_on_disk` (the file the system points to does not exist).

For EVERY doc, read it and record exactly what it says. Never guess or fill in from the voucher: if a
field is not on the document, use null. Transcribe names/refs as written. Amounts as numbers.

Return by WRITING a JSON file (path given below) = a list with one object per doc:
{
 "voucher": "...", "file": "...",
 "kind": "transfer" | "claim" | "remittance_advice" | "refund_proof" | "credit_note" | "other" | "unreadable" | "missing",
 "bank": str|null,                 // e.g. SNB
 "value_date": "YYYY-MM-DD"|null,
 "amount": number|null,            // transfer amount, or the claim / remittance total actually paid
 "direction": "incoming"|"outgoing"|null,   // for transfers: حوالة واردة = incoming, صادرة = outgoing
 "payer_name": str|null,           // remitter / sender as printed (English or Arabic)
 "beneficiary_name": str|null,
 "transfer_ref": str|null,         // any reference: UTI, EXTN..., حوالة رقم, payment ref
 "bank_details_text": str|null,    // the free-text details / وصف line, verbatim (short)
 "period_in_transfer": str|null,   // any month/period written in the bank details (not handwriting)
 "handwritten_note": str|null,     // handwriting on the page, e.g. "Riyadh - Jun 2026"
 "doc_insurer": str|null,          // insurer / TPA named on a claim or remittance document
 "doc_period": str|null,           // service month(s) the claim / remittance covers, e.g. "2026-06"
 "doc_branch": str|null,           // clinic / branch named on the claim (Riyadh, Buraydah 1/2, Rafha) if any
 "doc_amount_paid": number|null,   // on claim/remittance: net paid / approved amount if shown
 "doc_amount_claimed": number|null,
 "legible": true|false,
 "notes": str|null                 // anything odd: wrong company, wrong month, different branch, amount
                                   // differs, a document that belongs to a different voucher, duplicate, etc.
}
Then, per VOUCHER, add one more object {"voucher": "...", "kind": "voucher_verdict", ...} with:
 "payer_matches_customer": "yes"|"no"|"partial"|"unknown"  (compare transfer payer to the voucher's customer;
    note TPAs: e.g. NEXtCARE pays for Al Jazira Takaful, GlobeMed for Mutakamela, "العناية الشاملة" /
    Comprehensive Care pays for Al Sagr and Arabian Shield — treat a known TPA/insurer pairing as "partial"
    with the reason, not "no"),
 "amount_matches": "yes"|"no"|"part_of_transfer"|"unknown",   // voucher bank debit vs transfer amount;
    one transfer split across branches/months is "part_of_transfer" when the parts are shown
 "period_voucher": month(s) in the voucher narrative, "period_transfer": month(s) in transfer (details or
    handwriting, say which), "period_docs": month(s) on claim/remittance,
 "period_consistent": "yes"|"no"|"unknown",
 "right_file": "yes"|"no"|"unknown"  (is the attachment really this payment — same company, amount, date),
 "issues": [short strings], "confidence": "high"|"medium"|"low"

Do not modify any other file. When done, reply with at most 10 lines: count of docs read, and the list of
vouchers with any issue (one line each). Be precise and literal — this is audit evidence.
