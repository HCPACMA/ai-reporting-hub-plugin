import json, copy, re
SCR='/tmp/claude-0/-home-claude/945d3a47-697d-5024-a1b0-26cae0e7ec05/scratchpad'
PIPE='/home/claude/inventory_build/pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json'
N=json.load(open(PIPE)); V26=json.load(open(f'{SCR}/refresh/audit_v26.json')); PREV=json.load(open(f'{SCR}/inv/audit_prev.json'))
A=copy.deepcopy(N)
AS_OF_D='2026-10-06'; DATA_TO='2026-10-05'
# ---------------- purchasing blocks (net of returns) + watch-list
LR=json.load(open(f'{SCR}/watch/live_result.json')); B,WL,BR=LR['blocks'],LR['watchlist'],LR['returns']
PCD=json.load(open(f'{SCR}/pc/price_changes.json'))
for k in ('purchases_by_supplier','product_supplier_price_matrix','supplier_savings_opportunities','price_outliers_flagged'): A[k]=B[k]
A['kpi']['price_gap_savings_identified']=B['price_gap_savings_identified']
V=copy.deepcopy(V26['vendor_concentration'])
V['kpi']=B['vendor']['kpi']; V['top_suppliers']=B['vendor']['top_suppliers']; V['by_branch']=B['vendor']['by_branch']; V['single_source_products']=B['vendor']['single_source_products']
A['vendor_concentration']=V
# meta: purchase text updates carried from V26 on top of the fresh base text
f6_prev=PREV['meta']['findings'][6]; f6_v26=V26['meta']['findings'][6]; assert f6_v26.startswith(f6_prev)
A['meta']['findings'][6]=N['meta']['findings'][6]+f6_v26[len(f6_prev):]
A['meta']['purchase_invoice_lines']=V26['meta']['purchase_invoice_lines']
pr=copy.deepcopy(V26['meta']['purchasing_refresh']); pr.update({'refreshed_on':AS_OF_D,'checked_through':DATA_TO,'note':pr['note']+' Re-checked on 6 Oct against the full re-extract: no purchase invoice was posted after 29 Sep (the 37 newer purchase lines are still open drafts), so the posted-line set is unchanged.'})
A['meta']['purchasing_refresh']=pr
A['meta']['scan_review_refresh']=V26['meta']['scan_review_refresh']
A['watchlist']=WL
ev_ret=PCD.pop('events_returned'); A['price_changes']=PCD
RE=WL['returns_effect']; RR=copy.deepcopy(V26['returns_review'])
RR.update({'as_of':AS_OF_D,'bridge':BR,'events_returned':ev_ret,
  'kpi':{k:PCD['kpi'][k] for k in ('events_returned_total','events_returned_window','events_returned_sar_window','invoice_lines_returned_full','invoice_lines_returned_partial')},
  'watch':{'cleared':len(RE['cleared_by_return']),'cleared_sar':RE['cleared_sar'],'unique_sar_gross':RE['unique_sar_gross'],'unique_sar_net':RE['unique_sar_net'],
           'cleared_list':[f"{a['product_name']} at {a['supplier_name']} (SAR {a['impact']:,.0f})" for a in RE['cleared_by_return']]}})
A['returns_review']=RR
A['scan_review']=V26['scan_review']
# ---------------- forecast
items=json.load(open(f'{SCR}/forecast/demand_forecast_items_v27.json'))['items']
tierA=[i for i in N['abc_analysis']['company_wide']['items'] if i['tier']=='A']
tA=sum(i['value'] for i in tierA); tot=N['kpi']['total_inventory_value']; v50=sum(i['on_hand_value'] for i in items)
meth=V26['demand_forecast']['methodology']
meth=re.sub(r'\(\d+\.\d+% of Tier-A value, \d+\.\d+% of total inventory value\)', f'({100*v50/tA:.1f}% of Tier-A value, {100*v50/tot:.1f}% of total inventory value)', meth)
meth=meth.replace('pulled live from EXSYS.IM_PRODUCTS_TRANSACTIONS on 2026-10-01','pulled live from EXSYS.IM_PRODUCTS_TRANSACTIONS (history to 30 Sep 2026; the 50 SKUs re-ranked on 5 Oct stock)')
assert '2026-10-05' not in meth
reclassed=[i for i in items if i['reclassified']]; mapes=sorted(i['backtest_mape_pct'] for i in items if i['backtest_mape_pct'] is not None)
mc={}
for i in items: mc[i['model']]=mc.get(i['model'],0)+1
A['demand_forecast']={'methodology':meth,'kpi':{'skus_forecasted':len(items),'total_value_forecasted':round(v50,2),'reclassified_count':len(reclassed),
  'sar_moved_out_of_overstock':round(sum(i['on_hand_value'] for i in reclassed if i['naive_flag']=='overstock' and i['forecast_flag']!='overstock'),2),
  'sar_newly_flagged':round(sum(i['on_hand_value'] for i in reclassed if i['naive_flag']!='overstock' and i['forecast_flag']=='overstock'),2),
  'median_backtest_mape_pct':mapes[len(mapes)//2] if mapes else None,'backtested_sku_count':len(mapes),'model_counts':mc,'as_of':DATA_TO},'items':items}
# ---------------- rebalancing (+ expiry awareness)
RB=json.load(open(f'{SCR}/rebalance/rebalancing_recommendations_v27.json'))
exp={}
for r in N['expiry_risk']+N['past_expiry_on_hand']:
    if r['org']=='01': exp.setdefault(r['product'],[]).append(r)
for rec in RB['recommendations']:
    e=exp.get(rec['product'])
    rec['riyadh_expiry_batches']=len(e) if e else 0
    rec['riyadh_expiry_qty']=round(sum(x['qty_on_hand'] for x in e),1) if e else 0
    rec['riyadh_earliest_expiry']=min(str(x['expiry_date'])[:10] for x in e) if e else None
rb_meth=V26['rebalancing']['methodology']
old_sent=rb_meth[rb_meth.index('No batch in this top-50 scope'):]
flagged=sorted({r['product_name'] for r in RB['recommendations'] if r['riyadh_expiry_batches']})
new_sent=("Expiry check (FEFO): "+(f"{len(flagged)} suggested SKU(s) have near-expiry or past-expiry batches at Riyadh today ("+'; '.join(flagged)+") - the quantity shown can include those batches, so ship the earliest-expiry stock first and confirm the batch before sending."
  if flagged else "no suggested SKU has a near-expiry or past-expiry batch at Riyadh today, so no FEFO conflict applies to these recommendations; the check is still run per SKU."))
RB['kpi']['skus_with_riyadh_expiry_batches']=len(flagged)
A['rebalancing']={'methodology':rb_meth.replace(old_sent,new_sent),'kpi':RB['kpi'],'recommendations':RB['recommendations']}
# ---------------- ABC x XYZ
XZ=json.load(open(f'{SCR}/xyz/abc_xyz.json'))
xm=V26['abc_xyz']['methodology'].replace('every one of the 697 ranked SKUs',f"every one of the {XZ['kpi']['skus_ranked']} ranked SKUs")
assert str(XZ['kpi']['skus_ranked']) in xm
A['abc_xyz']={'methodology':xm,**XZ}
# ---------------- transfer workflow, live check
tw=json.load(open(f'{SCR}/feedback/transfer_workflow.json')); tw['sod_rows_excl_tr']=json.load(open(f'{SCR}/feedback/sod_rows_excl_tr.json')); A['transfer_workflow']=tw
A['live_check']=json.load(open(f'{SCR}/refresh/live_check_v27.json'))
# ---------------- meta finding for the refresh
A['meta']['source']=A['meta']['source']
A['meta']['findings'].append("Refresh 2026-10-06 (V27): every table was re-extracted from the ERP in full on 6 Oct 2026 (all 2026 transactions to 5 Oct, active products, stock balances, batches, manufacturer batches) with a packed-query method that bypasses the 200-row-per-call limit; the transaction count (61,675 lines after removing the view's exact duplicate Credit-Receipt lines) matches the ERP row count exactly, and the creator of every document was recovered. The column-shift defect described in the two earlier correction notes does not occur in this extract (0 rows affected). Overstock, Slow-Moving, Expiry, Aging, ABC, Forecast, Rebalancing, ABC x XYZ and Fraud tabs are all rebuilt on this extract; the Overview 'change since 8 Sep' section compares it with the previous snapshot.")
json.dump(A,open(f'{SCR}/refresh/audit_v27.json','w'),ensure_ascii=False,separators=(',',':'))
print('keys',len(A),'size',len(json.dumps(A))//1024,'KB'); print('new vs v26 keys',set(A)^set(V26))
print(A['rebalancing']['kpi']); print(A['abc_xyz']['kpi']['skus_ranked'], A['demand_forecast']['kpi'])
