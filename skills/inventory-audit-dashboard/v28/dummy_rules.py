import re
G=1.318
MONEY=re.compile(r'(sar|value|^val|_val$|cost|price|spend|savings|impact|paid|annualized)',re.I)
NOT=re.compile(r'(pct|share|count|skus?$|^n_|_n$|lines|events$|docs|flags|ratio|hhi|qty|days|^high$|^medium$|backtest|mape|^sku|alerts$|window_days|_lines$)',re.I)
EXPLICIT={('watchlist','trend/[]','supplier_gap'),('watchlist','trend/[]','entry_outlier'),
 ('watchlist','alerts/[]','from'),('watchlist','alerts/[]','to'),('watchlist','alerts/[]','best'),
 ('returns_review','lines/[]','med'),('scan_review','invoices/[]','tot'),('scan_review','invoices/[]/ai','tot'),
 ('live_check','top_down/[]','delta'),('live_check','top_up/[]','delta'),('price_changes','events/[]/from','px'),('price_changes','events/[]/to','px'),
 ('returns_review','events_returned/[]/from','px'),('returns_review','events_returned/[]/to','px')}
NEVER={('abc_analysis','company_wide','zero_or_unpriced_value_skus_excluded'),('watchlist','kpi','alerts'),('watchlist','kpi','lines_90d'),('abc_xyz','cells/[]','at_risk'),('abc_xyz','kpi','excess_skus')}
def is_money(top,path,key):
    t=(top,path,key)
    if t in NEVER: return False
    if t in EXPLICIT: return True
    if key in('on_hand','cv','mean_m','sd_m','score','ratio','hhi'): return False
    if re.fullmatch(r'(price_gap_savings_identified)',key): return True
    # watchlist alerts price (sole-source single price) / ref_price
    if NOT.search(key) and not re.search(r'(sar|value|cost|price|spend)',key): return False
    if NOT.search(key) and re.search(r'(pct|share|count|skus?$|lines|events$|qty|days)',key) : return False
    return bool(MONEY.search(key))
