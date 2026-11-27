import json
AUD='/home/claude/inventory_build/pipeline_run/Inventory/alfaihaa/alfaihaa_inventory_audit.json'
F=json.load(open('forecast_results_v27.json'))
res=F if isinstance(F,dict) else {r['code']:r for r in F}
d=json.load(open(AUD)); abc={i['product']:i for i in d['abc_analysis']['company_wide']['items']}
top50=json.load(open('../inv/top50_new.json'))
def flag(c): return None if c is None else ("overstock" if c>6 else ("watch" if c>4 else "ok"))
items=[]
for p in top50:
    r=res[p]; a=abc[p]
    nc=a['qty']/r['avg_last3'] if r['avg_last3'] else None
    f3=r['forecast_total_3mo']/3
    fc=a['qty']/f3 if f3>0 else None
    nf,ff=flag(nc),flag(fc)
    items.append({"product":p,"product_name":a['product_name'],"on_hand_qty":a['qty'],"on_hand_value":a['value'],"model":r['model'],
      "confidence":r['confidence'],"backtest_mape_pct":r['backtest_mape_pct'],"trend_pct":r['trend_pct_yoy_window'],"n_months_history":r['n_months'],
      "avg_last3":r['avg_last3'],"forecast_months":r['forecast_months'],"forecast":r['forecast'],"forecast_total_3mo":r['forecast_total_3mo'],
      "ci_low_3mo":r['ci_low_3mo'],"ci_high_3mo":r['ci_high_3mo'],"naive_cover_months":None if nc is None else round(nc,1),
      "forecast_cover_months":None if fc is None else round(fc,1),"naive_flag":nf,"forecast_flag":ff,"reclassified":nf!=ff})
json.dump({"items":items},open('demand_forecast_items_v27.json','w'),ensure_ascii=False,indent=1)
# validate vs old on retained SKUs
old={i['product']:i for i in json.load(open('demand_forecast_items.json'))['items']}
diff=0
for i in items:
    o=old.get(i['product'])
    if not o: continue
    for k in ('model','confidence','backtest_mape_pct','trend_pct','n_months_history','avg_last3','forecast','forecast_total_3mo','ci_low_3mo','ci_high_3mo'):
        if o[k]!=i[k]: diff+=1; print('DIFF',i['product'],k,o[k],i[k])
print('retained',sum(1 for i in items if i['product'] in old),'field diffs',diff)
print('reclassified',sum(i['reclassified'] for i in items))
