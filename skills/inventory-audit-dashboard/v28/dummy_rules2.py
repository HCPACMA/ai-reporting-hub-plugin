import re
from dummy_rules import is_money, G
Q=3
U=G/Q
UNIT_KEYS={'unit_cost','group_median_cost','min_price','max_price','avg_price','cheapest_price','priciest_price','paid','best','price','ref_price','price_now','price_before','px','pi_price','med'}
UNIT_EXPLICIT={('watchlist','alerts/[]','from'),('watchlist','alerts/[]','to'),('receiving_flags','[]','cost'),('returns_review','lines/[]','cost')}
QTY_SET={'on_hand','q','of','avg_last3','forecast_total_3mo','ci_low_3mo','ci_high_3mo','mean_m','sd_m','to_branch_forecast_3mo','company_forecast_3mo','total_qty'}
QTY_NOT={'min_qty','max_qty','reorder_qty','qty_lines_checked','qty_mismatch_lines'}
def kind(top,path,key):
    t=(top,path,key)
    if t in UNIT_EXPLICIT or (key in UNIT_KEYS and is_money(top,path,key)): return 'U'
    if is_money(top,path,key): return 'G'
    if key in QTY_NOT: return None
    if 'qty' in key or key in QTY_SET: return 'Q'
    return None
