import pickle,json,sys
def build(statefile, top):
    st=pickle.load(open(statefile,'rb'))
    bn={'01':'Riyadh','02':'Buraydah 1','03':'Buraydah 2','04':'Rafha'}
    out=[]
    for b in st['balances']:
        if b['product'] not in top: continue
        k=(b['org'],b['store'],b['product'])
        ds=st['ds_qty_6mo'].get(k,0.0); ts=st['ts_qty_6mo'].get(k,0.0)
        lr=st['last_receipt_date'].get(k)
        out.append({'org':b['org'],'branch':bn[b['org']],'store':b['store'],'store_name':b['store_name'],'product':b['product'],'product_name':b['product_name'],
          'on_hand_qty':b['on_hand'],'on_hand_value':b['on_hand_cost'],'unit_cost':b['unit_cost'],'dispensed_qty_6mo':ds,'transferred_out_qty_6mo':ts,'qty_out_6mo':ds+ts,
          'last_received':str(lr) if lr else None,'last_received_type':st['last_receipt_type'].get(k)})
    return out
if __name__=='__main__':
    top=set(json.load(open(sys.argv[2])))
    json.dump(build(sys.argv[1],top),open(sys.argv[3],'w'),ensure_ascii=False)
