import json, copy, re
W='/home/claude/w'
N=json.load(open(f'{W}/pipe/Inventory/alfaihaa/alfaihaa_inventory_audit.json')); V27=json.load(open(f'{W}/audit_v27.json'))
A=copy.deepcopy(N)
AS_OF_D='2026-10-20'; DATA_TO='2026-10-20'
LR=json.load(open(f'{W}/watch/live_result.json')); B,WL,BR=LR['blocks'],LR['watchlist'],LR['returns']
PCD=json.load(open(f'{W}/watch/price_changes/price_changes.json'))
for k in ('purchases_by_supplier','product_supplier_price_matrix','supplier_savings_opportunities','price_outliers_flagged'): A[k]=B[k]
A['kpi']['price_gap_savings_identified']=B['price_gap_savings_identified']
V=copy.deepcopy(V27['vendor_concentration'])
for k in ('kpi','top_suppliers','by_branch','single_source_products'): V[k]=B['vendor'][k]
A['vendor_concentration']=V
f6n=N['meta']['findings'][6]; f6o=V27['meta']['findings'][6]; assert f6o.startswith(f6n)
A['meta']['findings'][6]=f6n+f6o[len(f6n):]
nl=3229
A['meta']['purchase_invoice_lines']=nl
pr=copy.deepcopy(V27['meta']['purchasing_refresh'])
pr.update({'refreshed_on':AS_OF_D,'checked_through':DATA_TO,'lines':nl,'previous_snapshot_lines':V27['meta']['purchasing_refresh']['lines'],
 'previous_snapshot_spend':V27['meta']['purchasing_refresh']['net_spend'],'gross_lines':BR['lines_gross'],'returns_lines':BR['returns_lines'],
 'returns_value':BR['returns_value'],'net_spend':BR['spend_net'],'gross_spend':BR['spend_gross'],
 'source':'IM_PRODUCTS_TRANSACTIONS, T_TYPE = PI, STATUS = P, 2026-01-01 to 2026-10-20',
 'note':pr['note']+' Refreshed on 20 Oct against the full re-extract: 130 new posted purchase-invoice lines since 5 Oct; the 2026 purchase returns are unchanged (34 lines).'})
A['meta']['purchasing_refresh']=pr
A['meta']['scan_review_refresh']=V27['meta']['scan_review_refresh']
A['watchlist']=WL
ev_ret=PCD.pop('events_returned'); A['price_changes']=PCD
RE=WL['returns_effect']; RR=copy.deepcopy(V27['returns_review'])
RR.update({'as_of':AS_OF_D,'bridge':BR,'events_returned':ev_ret,
  'kpi':{k:PCD['kpi'][k] for k in ('events_returned_total','events_returned_window','events_returned_sar_window','invoice_lines_returned_full','invoice_lines_returned_partial')},
  'watch':{'cleared':len(RE['cleared_by_return']),'cleared_sar':RE['cleared_sar'],'unique_sar_gross':RE['unique_sar_gross'],'unique_sar_net':RE['unique_sar_net'],
           'cleared_list':[f"{a['product_name']} at {a['supplier_name']} (SAR {a['impact']:,.0f})" for a in RE['cleared_by_return']]}})
A['returns_review']=RR
A['scan_review']=V27['scan_review']

# ---- 'not linked in ERP' flag (nl) + share-derived scan paths, carried from V27 (invoices before 31 Mar have no ERP attachment record; their scans are on the share)
_nl={}
for _e in V27['price_changes']['events']+V27['returns_review']['events_returned']:
    for _s in ('from','to'):
        if _e[_s].get('nl'): _nl[_e[_s]['inv']]=_e[_s]['att']
for _r in V27['scan_review']['invoices']:
    if _r['nl']: _nl.setdefault(_r['inv'],None)
def _fix(_e):
    for _s in ('from','to'):
        _x=_e[_s]
        if _x['inv'] in _nl and _nl[_x['inv']] is not None: _x['att']=_nl[_x['inv']]; _x['nl']=True
        else: _x['nl']=False
for _e in A['price_changes']['events']+A['returns_review']['events_returned']: _fix(_e)
_K=A['price_changes']['kpi']; _ev=A['price_changes']['events']; _win=[e for e in _ev if e['to']['d']>=_K['window_start']]
_K['events_both_linked_window']=sum(1 for e in _win if not e['from']['nl'] and not e['to']['nl'])
_K['events_unlinked_window']=len(_win)-_K['events_both_linked_window']
_pi=json.load(open(f'{W}/watch/price_changes/pi_rows_with_inv.json'))
_K['invoices_not_linked_erp']=len({r[2] for r in _pi if r[2] in _nl})
print('nl kpis',_K['events_both_linked_window'],_K['events_unlinked_window'],_K['invoices_not_linked_erp'])
assert set(V27['price_changes']['kpi'])<=set(_K)|{'x'}, set(V27['price_changes']['kpi'])-set(_K)
# forecast
items=json.load(open(f'{W}/fc/demand_forecast_items_v29.json'))['items']
tierA=[i for i in N['abc_analysis']['company_wide']['items'] if i['tier']=='A']
tA=sum(i['value'] for i in tierA); tot=N['kpi']['total_inventory_value']; v50=sum(i['on_hand_value'] for i in items)
meth=V27['demand_forecast']['methodology']
meth=re.sub(r'\(\d+\.\d+% of Tier-A value, \d+\.\d+% of total inventory value\)', f'({100*v50/tA:.1f}% of Tier-A value, {100*v50/tot:.1f}% of total inventory value)', meth)
meth=meth.replace('the 50 SKUs re-ranked on 5 Oct stock','the 50 SKUs re-ranked on 20 Oct stock')
assert '20 Oct stock' in meth
reclassed=[i for i in items if i['reclassified']]; mapes=sorted(i['backtest_mape_pct'] for i in items if i['backtest_mape_pct'] is not None)
mc={}
for i in items: mc[i['model']]=mc.get(i['model'],0)+1
A['demand_forecast']={'methodology':meth,'kpi':{'skus_forecasted':len(items),'total_value_forecasted':round(v50,2),'reclassified_count':len(reclassed),
  'sar_moved_out_of_overstock':round(sum(i['on_hand_value'] for i in reclassed if i['naive_flag']=='overstock' and i['forecast_flag']!='overstock'),2),
  'sar_newly_flagged':round(sum(i['on_hand_value'] for i in reclassed if i['naive_flag']!='overstock' and i['forecast_flag']=='overstock'),2),
  'median_backtest_mape_pct':mapes[len(mapes)//2] if mapes else None,'backtested_sku_count':len(mapes),'model_counts':mc,'as_of':DATA_TO},'items':items}
# rebalancing
RB=json.load(open(f'{W}/fc/rebalancing_recommendations_v29.json'))
exp={}
for r in N['expiry_risk']+N['past_expiry_on_hand']:
    if r['org']=='01': exp.setdefault(r['product'],[]).append(r)
for rec in RB['recommendations']:
    e=exp.get(rec['product'])
    rec['riyadh_expiry_batches']=len(e) if e else 0
    rec['riyadh_expiry_qty']=round(sum(x['qty_on_hand'] for x in e),1) if e else 0
    rec['riyadh_earliest_expiry']=min(str(x['expiry_date'])[:10] for x in e) if e else None
rb_meth=V27['rebalancing']['methodology']
i0=rb_meth.index('Expiry check (FEFO)'); old_sent=rb_meth[i0:]
flagged=sorted({r['product_name'] for r in RB['recommendations'] if r['riyadh_expiry_batches']})
new_sent=("Expiry check (FEFO): "+(f"{len(flagged)} suggested SKU(s) have near-expiry or past-expiry batches at Riyadh today ("+'; '.join(flagged)+") - the quantity shown can include those batches, so ship the earliest-expiry stock first and confirm the batch before sending."
  if flagged else "no suggested SKU has a near-expiry or past-expiry batch at Riyadh today, so no FEFO conflict applies to these recommendations; the check is still run per SKU."))
RB['kpi']['skus_with_riyadh_expiry_batches']=len(flagged)
A['rebalancing']={'methodology':rb_meth.replace(old_sent,new_sent),'kpi':RB['kpi'],'recommendations':RB['recommendations']}
# ABC x XYZ
XZ=json.load(open(f'{W}/xyz/abc_xyz.json'))
xm=V27['abc_xyz']['methodology'].replace('every one of the 637 ranked SKUs',f"every one of the {XZ['kpi']['skus_ranked']} ranked SKUs")
assert str(XZ['kpi']['skus_ranked']) in xm
A['abc_xyz']={'methodology':xm,**XZ}
tw=json.load(open(f'{W}/pipe/Inventory/alfaihaa/transfer_workflow.json')); tw['sod_rows_excl_tr']=json.load(open(f'{W}/pipe/Inventory/alfaihaa/sod_rows_excl_tr.json')); A['transfer_workflow']=tw
A['live_check']=json.load(open(f'{W}/live_check_v29.json'))
A['meta']['findings'].append("Refresh 2026-10-20 (V29): every table was re-extracted from the ERP in full on 20 Oct 2026 (all 2026 transactions to 20 Oct, active products, stock balances, batches, manufacturer batches) with the packed-query method; transaction counts tie to the ERP row count and the creator of every document was recovered. Overstock, Slow-Moving, Expiry, Aging, ABC, Purchasing, Watch-list, Price changes, Returns, Forecast, Rebalancing, ABC x XYZ and Fraud tabs are all rebuilt on this extract; the Overview 'change since 5 Oct' section compares it with the previous snapshot. The Forecast uses history to 30 Sep (October dropped as a partial month); SKUs first seen in October have no history and are excluded.")
VE=json.load(open(f'{W}/valerr/valuation_errors.json')); A['valuation_errors']=VE
A['meta']['findings'].append("Rules added 21 Oct 2026: (1) an item needs about three months of consumption history before it can be called slow-moving or overstocked - items first bought less than three months before the as-of date (%s new SKUs, SAR %s on hand) are left out of Overstock and Slow-Moving; (2) any purchase invoice that has a purchase return is left out of the price-change, supplier-gap, savings and price-outlier analyses (spend totals stay net of returns); (3) a new Valuation Errors tab lists cost mismatches that inflate or deflate stock value: inter-branch transfers received at a cost far from the cost they were sent at, consecutive purchases at a price 3x or more away from the previous one, and on-hand cost far from the latest purchase cost." % (N['kpi'].get('new_items_excluded'), format(round(N['kpi'].get('new_items_excluded_value',0)),',')))
json.dump(A,open(f'{W}/audit_v29.json','w'),ensure_ascii=False,separators=(',',':'))
print('keys',len(A),'size',len(json.dumps(A))//1024,'KB'); print(set(A)^set(V27))
print(A['rebalancing']['kpi']); print(A['abc_xyz']['kpi']['skus_ranked'], A['demand_forecast']['kpi'])
