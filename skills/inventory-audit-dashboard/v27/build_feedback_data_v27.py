"""Assemble AUDIT.transfer_workflow + the patched fraud_detection.sod values (item 5, 2026-10-01).
Inputs: fraud_workflow.json (device script build_fraud_workflow.py, full 2026 transaction extract) and ERP query
results from IM_STOCK_SND_TRANSFER_M / IM_STOCK_RCV_TRANSFER_M / *_D (read-only Cure queries run 2026-10-01)."""
import json
D = json.load(open('fraud_workflow.json', encoding='utf-8'))

ORG = {'01011301': 'Riyadh', '02011301': 'Buraydah 1', '03011301': 'Buraydah 2',
       '04011301': 'Rafha', '01011302': 'Riyadh (org 01011302)'}
# (from, to, docs sent+received both posted, avg days to receipt, max days, distinct GL JVs, same person sent & received, sender ids, receiver ids)
R = [
 ('01011301','04011301',135,0.92, 7.3,12,  0,'6381','6362'),
 ('01011301','03011301',115,0.31, 5.8,12,  0,'2030 / 6381','6265'),
 ('01011301','02011301',105,0.29, 5.8,12,  0,'6381','6265'),
 ('02011301','03011301', 47,0.95, 4.0,16, 47,'6265','6265'),
 ('03011301','02011301', 32,0.54, 5.0,13, 32,'6265','6265'),
 ('04011301','01011301', 23,5.78,24.7, 8,  0,'6362','6381'),
 ('03011301','01011301', 21,4.47,17.8,11,  0,'6265','6381'),
 ('02011301','01011301', 15,4.57,14.7,11,  0,'6265','6381'),
 ('01011301','01011302',  8,0.32, 1.8, 6,  6,'2030 / 6381','6381'),
 ('01011302','01011301',  3,3.61,10.8, 3,  1,'2030 / 6381','6381'),
]
routes = [dict(from_org=a, to_org=b, route=f"{ORG[a]} → {ORG[b]}", docs=n, avg_days=avg, max_days=mx, gl_vouchers=jv,
               same_person=sp, sender_staff=s, receiver_staff=r) for a,b,n,avg,mx,jv,sp,s,r in R]
docs = sum(r['docs'] for r in routes)
same_docs = sum(r['same_person'] for r in routes)
bur_docs = sum(r['same_person'] for r in routes if r['from_org'] in ('02011301','03011301') and r['to_org'] in ('02011301','03011301'))
assert docs == 504, docs

su = D['same_user_by_type']
tw = {
 "as_of": "2026-10-05",
 "steps": [
  {"n": 1, "who": "Sending storekeeper", "doc": "Send Transfer (TS / SND…)", "does": "Posts the send so the receiving branch can see the movement and receive it."},
  {"n": 2, "who": "Receiving storekeeper", "doc": "Receive Transfer (TR / RCV…)", "does": "Creates and posts the receipt himself — this post is the acceptance that makes him responsible for the stock."},
  {"n": 3, "who": "Store accountant", "doc": "Consolidated GL posting (one JV1-26/… per batch)", "does": "Reviews the documents, confirms receipt, then posts the sends to the GL in one consolidated posting (monthly in practice)."},
 ],
 "kpi": {
   "docs_sent_posted": docs, "docs_received_posted": docs, "gl_consolidated": 500, "gl_pending": 4,
   "cancelled_sends": 8, "cancelled_receipts_reposted": 1,
   "qty_lines_checked": 3704, "qty_mismatch_lines": 0,
   "same_person_docs": same_docs, "same_person_bur_docs": bur_docs,
   "tr_same_user_lines": su['TR'], "same_user_total": D['same_user_total'], "same_user_excl_tr": D['same_user_excl_tr'],
   "same_user_excl_tr_pct": D['same_user_excl_tr_pct'], "posted_excl_tr": D['posted_excl_tr'],
   "tr_share_pct": round(100*su['TR']/D['same_user_total'],1),
 },
 "routes": routes,
 "ts_lag": D['ts_consolidation_lag'],
 "same_user_by_type": su,
 "user_summary_excl_tr": D['user_summary_excl_tr'],
}
json.dump(tw, open('transfer_workflow.json','w',encoding='utf-8'), ensure_ascii=False)
json.dump(D['sod_rows_excl_tr'], open('sod_rows_excl_tr.json','w',encoding='utf-8'), ensure_ascii=False)
print(tw['kpi']); print(len(D['sod_rows_excl_tr']), 'same-person docs', same_docs, 'bur', bur_docs)
