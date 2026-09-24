import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse,json,pandas as pd,numpy as np
from src.config import questions
from src.analyze import aggregate_y002
from src.metrics import js_divergence

def vec(probs,item):
    if item=='Y002': probs=aggregate_y002(probs)
    levels=[str(x) for x in questions()[item]['human_codes']]
    x=np.array([float(probs.get(k,0)) for k in levels]); return x/x.sum()

p=argparse.ArgumentParser(); p.add_argument('--order',default='data/processed/option_order_robustness.jsonl'); p.add_argument('--out',default='results/option_order_metrics.csv'); a=p.parse_args()
if Path(a.order).exists():
    rows=[json.loads(x) for x in Path(a.order).read_text().splitlines() if x.strip()]
    out=[]
    for (provider,country,item),gdf in pd.DataFrame([{'provider':r['provider'],'country':r['country'],'item':r['item'],'rep':r['rep'],'raw':r} for r in rows]).groupby(['provider','country','item']):
        gs=list(gdf.sort_values('rep').raw); ref=vec(gs[0]['probabilities'],item)
        for r in gs[1:]: out.append({'provider':provider,'country':country,'item':item,'rep':r['rep'],'js_from_first_order':js_divergence(ref,vec(r['probabilities'],item))})
    pd.DataFrame(out).to_csv(a.out,index=False); print('Wrote',a.out)
else: print('No order robustness file found; skipped')
