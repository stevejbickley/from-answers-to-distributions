import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, json
import pandas as pd
from src.usage_costs import usage_and_cost
from src.utils import ensure_dir, atomic_json

p=argparse.ArgumentParser(description='Create request-level and aggregated API token/cost accounting tables from saved JSONL records.')
p.add_argument('--data-dir',default='data/processed')
p.add_argument('--out-requests',default='results/api_request_usage.csv')
p.add_argument('--out-summary',default='results/api_usage_summary.csv')
p.add_argument('--out-json',default='results/api_usage_totals.json')
a=p.parse_args()

rows=[]
for path in sorted(Path(a.data_dir).glob('*.jsonl')):
    for lineno,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: r=json.loads(line)
        except Exception: continue
        provider=str(r.get('provider','')).lower()
        if provider.startswith('openai'): family='openai'
        elif provider.startswith('jev'): family='jev'
        else: continue
        usage=r.get('usage') or {}
        if not usage: continue
        model=r.get('model') or r.get('requested_model')
        uf=r.get('usage_flat'); cost=r.get('cost')
        if not isinstance(uf,dict) or not isinstance(cost,dict):
            uf,cost=usage_and_cost(family,model,usage,raw=r)
        request_id=r.get('request_id') or r.get('response_id') or r.get('record_id') or f'{path.name}:{lineno}'
        rows.append({
            'source_file':path.name,'provider':family,'provider_record_type':provider,
            'condition':r.get('condition') or provider,'condition_label':r.get('condition_label') or r.get('condition') or provider,
            'model':model,'request_id':request_id,'country':r.get('country'),'variant':r.get('variant'),'item':r.get('item'),
            **uf,
            'provider_reported_cost_usd':cost.get('provider_reported_cost_usd'),
            'estimated_input_cost_usd':cost.get('estimated_input_cost_usd'),
            'estimated_output_cost_usd':cost.get('estimated_output_cost_usd'),
            'estimated_total_cost_usd':cost.get('estimated_total_cost_usd'),
            'pricing_snapshot_date':cost.get('pricing_snapshot_date'),
            'pricing_model_key':cost.get('pricing_model_key'),
            'pricing_source_url':cost.get('pricing_source_url'),
            'estimate_basis':cost.get('estimate_basis'),
        })

ensure_dir(Path(a.out_requests).parent)
if not rows:
    pd.DataFrame().to_csv(a.out_requests,index=False); pd.DataFrame().to_csv(a.out_summary,index=False)
    atomic_json(a.out_json,{'requests':0,'note':'No provider usage records found.'}); print('No API usage records found.'); raise SystemExit(0)

frame=pd.DataFrame(rows)
# One Jev request can yield several saved answer records (e.g., batched Y003 Noul questions).
# Count/bill that request once. Verify duplicates agree on usage/cost before collapsing.
key=['source_file','provider','request_id']
conflicts=[]
for k,g in frame.groupby(key,dropna=False):
    cols=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','total_tokens','estimated_total_cost_usd']
    for c in cols:
        vals=g[c].dropna().astype(str).unique()
        if len(vals)>1: conflicts.append({'key':k,'field':c,'values':vals.tolist()})
if conflicts:
    raise RuntimeError(f'Conflicting usage for duplicated API request IDs: {conflicts[:5]}')

counts=frame.groupby(key,dropna=False).size().rename('saved_records_for_request').reset_index()
request=frame.drop_duplicates(key,keep='first').merge(counts,on=key,how='left')
request.to_csv(a.out_requests,index=False)

sumcols=['input_tokens','cached_input_tokens','cache_write_input_tokens','ordinary_input_tokens','output_tokens','reasoning_output_tokens','total_tokens',
         'provider_reported_cost_usd','estimated_input_cost_usd','estimated_output_cost_usd','estimated_total_cost_usd']
for c in sumcols: request[c]=pd.to_numeric(request[c],errors='coerce')
group=['provider','condition','condition_label','model']
agg={c:'sum' for c in sumcols}; agg['provider_reported_cost_usd']=lambda x: x.sum(min_count=1); agg['request_id']='count'
summary=request.groupby(group,dropna=False).agg(agg).reset_index().rename(columns={'request_id':'requests'})
summary.to_csv(a.out_summary,index=False)

totals={
    'requests':int(len(request)),
    'input_tokens':int(request.input_tokens.fillna(0).sum()),
    'cached_input_tokens':int(request.cached_input_tokens.fillna(0).sum()),
    'cache_write_input_tokens':int(request.cache_write_input_tokens.fillna(0).sum()),
    'output_tokens':int(request.output_tokens.fillna(0).sum()),
    'reasoning_output_tokens':int(request.reasoning_output_tokens.fillna(0).sum()),
    'total_tokens':int(request.total_tokens.fillna(0).sum()),
    'estimated_total_cost_usd':float(request.estimated_total_cost_usd.fillna(0).sum()),
    'provider_reported_cost_usd':(float(request.provider_reported_cost_usd.sum()) if request.provider_reported_cost_usd.notna().any() else None),
    'pricing_snapshot_dates':sorted(set(str(x) for x in request.pricing_snapshot_date.dropna().unique())),
    'note':'Estimated cost uses the dated standard list-price snapshot in config/pricing.yaml; provider invoices are authoritative. Batched Jev answer records are deduplicated by request_id.'
}
atomic_json(a.out_json,totals)
print('Wrote',a.out_requests,a.out_summary,a.out_json)
