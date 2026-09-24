from __future__ import annotations
from pathlib import Path
import json, pandas as pd, numpy as np
from .analyze import crossed_bootstrap_difference
from .utils import ensure_dir

def make_tables(results='results'):
    results=Path(results); out=ensure_dir(results/'tables'); m=pd.read_csv(results/'country_item_metrics.csv')
    summary=(m.groupby('provider').agg(
        n=('js','size'),js_mean=('js','mean'),js_median=('js','median'),tv_mean=('tv','mean'),
        wasserstein_mean=('wasserstein','mean'),expected_abs_error_mean=('expected_abs_error','mean'),
        human_entropy_mean=('human_entropy','mean'),model_entropy_mean=('model_entropy','mean'),
        entropy_abs_error_mean=('entropy_abs_error','mean'),entropy_signed_error_mean=('entropy_signed_error','mean'),
        allowed_mass_mean=('allowed_mass','mean'),missing_labels_mean=('missing_count','mean')).reset_index())
    summary.to_csv(out/'table2_primary_summary.csv',index=False)
    item=(m.groupby(['item','provider']).agg(js_mean=('js','mean'),tv_mean=('tv','mean'),
          wasserstein_mean=('wasserstein','mean'),expected_error=('expected_abs_error','mean'),
          entropy_error=('entropy_abs_error','mean'),n=('js','size')).reset_index())
    item.to_csv(out/'table_s6_item_summary.csv',index=False)
    country=(m.groupby(['country','provider']).agg(js_mean=('js','mean'),tv_mean=('tv','mean'),entropy_error=('entropy_abs_error','mean'),n=('js','size')).reset_index())
    country.to_csv(out/'table_s7_country_summary.csv',index=False)
    boot={}
    for metric in ['js','tv','wasserstein','expected_abs_error','entropy_abs_error']:
        if metric in m.columns:
            x=m.dropna(subset=[metric]); boot[metric]=crossed_bootstrap_difference(x,metric=metric)
    (out/'paired_contrasts.json').write_text(json.dumps(boot,indent=2),encoding='utf-8')
    # Diagnostics
    dpath=results/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath)
        diag=pd.DataFrame([{
            'calls':len(d),'complete_calls':int((d.missing_count==0).sum()),
            'incomplete_percent':100*float((d.missing_count>0).mean()),
            'allowed_mass_mean':float(d.allowed_mass.mean()),'allowed_mass_median':float(d.allowed_mass.median()),
            'invalid_generated_percent':100*float((~d.valid_generated.astype(bool)).mean())
        }])
        diag.to_csv(out/'table_s3_openai_diagnostics.csv',index=False)
    # Cultural map summary
    cpath=results/'cultural_map_distances.csv'
    if cpath.exists():
        c=pd.read_csv(cpath)
        cmap=c.groupby(['provider','representation'],as_index=False).agg(mean_distance=('distance','mean'),median_distance=('distance','median'),n=('distance','size'))
        cmap.to_csv(out/'table3_cultural_map.csv',index=False)
    # Y003
    ypath=results/'y003_marginal_metrics.csv'
    if ypath.exists():
        y=pd.read_csv(ypath)
        ys=y.groupby(['provider','quality'],as_index=False).agg(mae=('abs_error','mean'),mse=('sq_error','mean'),n=('abs_error','size'))
        ys.to_csv(out/'table_s9_y003.csv',index=False)
    return summary,item,boot
