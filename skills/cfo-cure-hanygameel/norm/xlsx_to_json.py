# Reads Financial\\Normalization.xlsx (columns VOUCHER_NO, Normalization, Note, Date) -> norm/vouchers.json
# Usage: python3 xlsx_to_json.py <Normalization.xlsx> <out vouchers.json>   (rows with an empty Normalization column are skipped)
import sys, json, openpyxl
ws = openpyxl.load_workbook(sys.argv[1], data_only=True).worksheets[0]
rows = list(ws.iter_rows(values_only=True)); h = [str(c).strip().lower() if c else '' for c in rows[0]]
ix = lambda n: h.index(n)
out = [{"v": str(r[ix('voucher_no')]).strip(), "tag": str(r[ix('normalization')]).strip(), "note": str(r[ix('note')] or ''),
        "date": (r[ix('date')].strftime('%Y-%m-%d') if hasattr(r[ix('date')], 'strftime') else str(r[ix('date')] or ''))}
       for r in rows[1:] if r[ix('voucher_no')] and r[ix('normalization')]]
json.dump(out, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1); print(len(out), 'vouchers')
