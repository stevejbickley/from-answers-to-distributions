from __future__ import annotations
from pathlib import Path
import json, pandas as pd
from .analyze import crossed_bootstrap_contrast
from .utils import ensure_dir

PRIMARY_CONTRASTS=[('gpt56_sol','jev'),('gpt4o_anchor','jev'),('gpt4o_anchor','gpt56_sol')]

def make_tables(results='results'):
    results=Path(results); out=ensure_dir(results/'tables'); m=pd.read_csv(results/'country_item_metrics.csv')
    full=m[m.representation=='full'].copy()
    summary=(m.groupby(['condition','condition_label','representation']).agg(
        n=('js','size'),js_mean=('js','mean'),js_median=('js','median'),tv_mean=('tv','mean'),
        wasserstein_mean=('wasserstein','mean'),expected_abs_error_mean=('expected_abs_error','mean'),
        human_entropy_mean=('human_entropy','mean'),model_entropy_mean=('model_entropy','mean'),
        entropy_abs_error_mean=('entropy_abs_error','mean'),entropy_signed_error_mean=('entropy_signed_error','mean'),
        allowed_mass_mean=('allowed_mass','mean'),missing_labels_mean=('missing_count','mean')).reset_index())
    summary.to_csv(out/'table2_primary_summary.csv',index=False)
    item=(full.groupby(['item','condition','condition_label']).agg(js_mean=('js','mean'),tv_mean=('tv','mean'),
          wasserstein_mean=('wasserstein','mean'),expected_error=('expected_abs_error','mean'),
          entropy_error=('entropy_abs_error','mean'),n=('js','size')).reset_index())
    item.to_csv(out/'table_s6_item_summary.csv',index=False)
    country=(full.groupby(['country','condition','condition_label']).agg(js_mean=('js','mean'),tv_mean=('tv','mean'),entropy_error=('entropy_abs_error','mean'),n=('js','size')).reset_index())
    country.to_csv(out/'table_s7_country_summary.csv',index=False)
    boot={}
    for a,b in PRIMARY_CONTRASTS:
        key=f'{a}_vs_{b}'; boot[key]={}
        for metric in ['js','tv','wasserstein','expected_abs_error','entropy_abs_error']:
            x=full.dropna(subset=[metric]); boot[key][metric]=crossed_bootstrap_contrast(x,a,b,metric=metric)
    # Same-model representation contrast is deterministic paired difference; summarize directly.
    rep=[]
    for cond,g in m.groupby('condition'):
        piv=g.pivot_table(index=['country','item'],columns='representation',values='js').dropna()
        if {'full','argmax'}.issubset(piv.columns):
            rep.append({'condition':cond,'n':len(piv),'mean_js_full':piv['full'].mean(),'mean_js_argmax':piv['argmax'].mean(),
                        'mean_argmax_minus_full':(piv['argmax']-piv['full']).mean()})
    pd.DataFrame(rep).to_csv(out/'table_s5_full_vs_argmax.csv',index=False)
    (out/'paired_contrasts.json').write_text(json.dumps(boot,indent=2),encoding='utf-8')
    dpath=results/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath)
        diag=(d.groupby(['condition','condition_label']).agg(calls=('item','size'),complete_calls=('missing_count',lambda x:int((x==0).sum())),
              incomplete_percent=('missing_count',lambda x:100*float((x>0).mean())),allowed_mass_mean=('allowed_mass','mean'),
              allowed_mass_median=('allowed_mass','median'),missing_mass_upper_bound_max=('missing_allowed_mass_upper_bound','max'),
              primary_retained_percent=('primary_included',lambda x:100*float(x.astype(bool).mean())),
              strict_retained_percent=('strict_included',lambda x:100*float(x.astype(bool).mean())),
              complete_only_percent=('complete_only_included',lambda x:100*float(x.astype(bool).mean())),
              invalid_generated_percent=('valid_generated',lambda x:100*float((~x.astype(bool)).mean()))).reset_index())
        diag.to_csv(out/'table_s3_openai_diagnostics.csv',index=False)
        sp=results/'openai_censoring_sensitivity_summary.csv'
        if sp.exists(): pd.read_csv(sp).to_csv(out/'table_s4_openai_censoring_sensitivity.csv',index=False)
    cpath=results/'cultural_map_distances.csv'
    if cpath.exists():
        c=pd.read_csv(cpath); cmap=c.groupby(['condition','condition_label','representation'],as_index=False).agg(mean_distance=('distance','mean'),median_distance=('distance','median'),n=('distance','size'))
        cmap.to_csv(out/'table3_cultural_map.csv',index=False)
    ypath=results/'y003_marginal_metrics.csv'
    if ypath.exists():
        y=pd.read_csv(ypath); ys=y.groupby(['condition','condition_label','quality'],as_index=False).agg(mae=('abs_error','mean'),mse=('sq_error','mean'),n=('abs_error','size'))
        ys.to_csv(out/'table_s9_y003.csv',index=False)
    return summary,item,boot
