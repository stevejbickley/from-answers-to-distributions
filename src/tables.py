from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .analyze import crossed_bootstrap_contrast, crossed_bootstrap_mean
from .utils import ensure_dir
from .config import analysis, questions, variants

PRIMARY_CONTRASTS=[('gpt56_sol','jev'),('gpt4o_anchor','jev'),('gpt4o_anchor','gpt56_sol')]
TAO_GPT4O={'unconditioned_distance_mean':2.42,'country_conditioned_distance_mean':1.57,'pct_countries_improved':71.0}


def _pct_positive(x):
    x=pd.to_numeric(x,errors='coerce').dropna()
    return 100*float((x>0).mean()) if len(x) else np.nan


def make_tables(results='results'):
    results=Path(results); out=ensure_dir(results/'tables'); m=pd.read_csv(results/'country_item_metrics.csv')
    full=m[m.representation=='full'].copy()
    cfg=analysis(); bootstrap={'reps':cfg['bootstrap_replicates'],'seed':cfg['random_seed']}
    # Previously absent SI tables are generated from the same configuration as collection.
    pd.DataFrame([{'item':k,'construct':v['title'],
                   'human_support':', '.join(map(str,v.get('human_codes',[-2,-1,0,1,2]))),
                   'probability_representation':('Four binary marginals' if k=='Y003' else
                       '12 ordered pairs aggregated to 3 categories' if k=='Y002' else f"{len(v['human_codes'])} categories"),
                   'source_prompt':v['source_prompt']} for k,v in questions().items()])\
        .to_csv(out/'table_s1_survey_constructs.csv',index=False)
    pd.DataFrame(variants()).to_csv(out/'table_s2_prompt_variants.csv',index=False)

    # Main Table 2: primary distributional fidelity summary.
    summary=(m.groupby(['condition','condition_label','representation']).agg(
        n=('js','size'),js_mean=('js','mean'),js_median=('js','median'),tv_mean=('tv','mean'),
        wasserstein_mean=('wasserstein','mean'),expected_abs_error_mean=('expected_abs_error','mean'),
        human_entropy_mean=('human_entropy','mean'),model_entropy_mean=('model_entropy','mean'),
        entropy_abs_error_mean=('entropy_abs_error','mean'),entropy_signed_error_mean=('entropy_signed_error','mean'),
        allowed_mass_mean=('allowed_mass','mean'),missing_labels_mean=('missing_count','mean')).reset_index())
    summary.to_csv(out/'table2_primary_summary.csv',index=False)

    # Main Table 3: population specificity. Positive gain means country conditioning
    # beats the corresponding baseline for the target country's human distribution.
    pspath=results/'population_specificity_metrics.csv'
    if pspath.exists():
        ps=pd.read_csv(pspath); rows=[]
        for (cond,label),g in ps.groupby(['condition','condition_label']):
            d=crossed_bootstrap_mean(g,'gain_vs_default_js',**bootstrap)
            l=crossed_bootstrap_mean(g,'gain_vs_loco_human_js',**bootstrap)
            rows.append({
                'condition':cond,'condition_label':label,'n_country_item':len(g),
                'country_model_js_mean':g.country_model_js.mean(),
                'default_model_js_mean':g.default_model_js.mean(),
                'gain_vs_default_mean':d['mean'] if d else np.nan,
                'gain_vs_default_ci95_low':d['ci95_low'] if d else np.nan,
                'gain_vs_default_ci95_high':d['ci95_high'] if d else np.nan,
                'gain_vs_default_median':g.gain_vs_default_js.median(),
                'pct_country_conditioning_improves':_pct_positive(g.gain_vs_default_js),
                'loco_human_js_mean':g.loco_human_js.mean(),
                'gain_vs_loco_human_mean':l['mean'] if l else np.nan,
                'gain_vs_loco_human_ci95_low':l['ci95_low'] if l else np.nan,
                'gain_vs_loco_human_ci95_high':l['ci95_high'] if l else np.nan,
                'gain_vs_loco_human_median':g.gain_vs_loco_human_js.median(),
                'pct_model_beats_loco_human':_pct_positive(g.gain_vs_loco_human_js),
                'model_shift_from_default_js_mean':g.model_shift_from_default_js.mean(),
            })
        ps_summary=pd.DataFrame(rows)
        ps_summary.to_csv(out/'table3_population_specificity.csv',index=False)

        # Main Table 3: country conditioning at two levels. This directly contrasts
        # Tao-style cultural-location alignment with full response-distribution fidelity.
        cmap_path=results/'cultural_map_prompting_summary.csv'
        if cmap_path.exists():
            cmap=pd.read_csv(cmap_path)
            cmap=cmap[cmap.representation=='expected'].copy()
            cols=['condition','unconditioned_distance_mean','country_conditioned_distance_mean',
                  'pct_countries_improved','n_countries']
            merged=ps_summary.merge(cmap[cols],on='condition',how='left',suffixes=('','_map'))
            merged=merged.rename(columns={
                'unconditioned_distance_mean':'map_unconditioned_distance_mean',
                'country_conditioned_distance_mean':'map_country_conditioned_distance_mean',
                'pct_countries_improved':'map_pct_countries_improved',
                'n_countries':'map_n_countries',
                'country_model_js_mean':'distribution_country_conditioned_js_mean',
                'default_model_js_mean':'distribution_unconditioned_js_mean',
                'pct_country_conditioning_improves':'distribution_pct_cells_improved',
                'loco_human_js_mean':'loco_human_js_mean',
                'pct_model_beats_loco_human':'distribution_pct_model_beats_loco_human'})
            keep=['condition','condition_label','map_unconditioned_distance_mean','map_country_conditioned_distance_mean',
                  'map_pct_countries_improved','distribution_unconditioned_js_mean','distribution_country_conditioned_js_mean',
                  'gain_vs_default_mean','gain_vs_default_ci95_low','gain_vs_default_ci95_high',
                  'distribution_pct_cells_improved','loco_human_js_mean','distribution_pct_model_beats_loco_human',
                  'n_country_item','map_n_countries']
            merged[[c for c in keep if c in merged.columns]].to_csv(out/'table3_country_conditioning.csv',index=False)

        byitem=(ps.groupby(['item','condition','condition_label'],as_index=False).agg(
            n=('country','size'),country_model_js_mean=('country_model_js','mean'),
            default_model_js_mean=('default_model_js','mean'),gain_vs_default_mean=('gain_vs_default_js','mean'),
            loco_human_js_mean=('loco_human_js','mean'),gain_vs_loco_human_mean=('gain_vs_loco_human_js','mean'),
            model_shift_from_default_js_mean=('model_shift_from_default_js','mean')))
        byitem.to_csv(out/'table_s12_population_specificity_by_item.csv',index=False)

    # Existing supplementary distribution summaries.
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
            x=full.dropna(subset=[metric]); boot[key][metric]=crossed_bootstrap_contrast(x,a,b,metric=metric,**bootstrap)
    (out/'paired_contrasts.json').write_text(json.dumps(boot,indent=2),encoding='utf-8')

    # Same-model representation contrast is deterministic paired difference; summarize directly.
    rep=[]
    for cond,g in m.groupby('condition'):
        piv=g.pivot_table(index=['country','item'],columns='representation',values='js').dropna()
        if {'full','argmax'}.issubset(piv.columns):
            rep.append({'condition':cond,'condition_label':str(g.condition_label.iloc[0]),'n':len(piv),
                        'mean_js_full':piv['full'].mean(),'mean_js_argmax':piv['argmax'].mean(),
                        'mean_argmax_minus_full':(piv['argmax']-piv['full']).mean(),
                        'median_argmax_minus_full':(piv['argmax']-piv['full']).median(),
                        'pct_full_better':100*float(((piv['argmax']-piv['full'])>0).mean())})
    pd.DataFrame(rep).to_csv(out/'table_s5_full_vs_argmax.csv',index=False)

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

    # Prompt, entropy, and interface summaries used in the expanded SI.
    ppath=results/'prompt_sensitivity.csv'
    if ppath.exists():
        p=pd.read_csv(ppath); p=p[p.country!='__DEFAULT__']
        (p.groupby(['item','condition','condition_label'],as_index=False).agg(
            n=('js_to_condition_mean','count'),n_retained=('js_to_condition_mean','size'),
            n_countries=('country','nunique'),mean_js=('js_to_condition_mean','mean'),median_js=('js_to_condition_mean','median'))
         .to_csv(out/'table_s8_prompt_sensitivity.csv',index=False))

    ypath=results/'y003_marginal_metrics.csv'
    if ypath.exists():
        y=pd.read_csv(ypath); ys=y.groupby(['condition','condition_label','quality'],as_index=False).agg(mae=('abs_error','mean'),mse=('sq_error','mean'),n=('abs_error','size'))
        ys.to_csv(out/'table_s9_y003.csv',index=False)

    epath=results/'entropy_structure_summary.csv'
    if epath.exists():
        pd.read_csv(epath).to_csv(out/'table_s10_entropy_structure.csv',index=False)
    eipath=results/'entropy_structure_by_item.csv'
    if eipath.exists():
        pd.read_csv(eipath).to_csv(out/'table_s11_entropy_by_item.csv',index=False)

    lpath=results/'openai_label_sensitivity.csv'
    if lpath.exists():
        l=pd.read_csv(lpath); l=l[l.country!='__DEFAULT__']
        (l.groupby(['condition','item'],as_index=False).agg(
            n=('js_to_label_mean','count'),n_retained=('js_to_label_mean','size'),
            n_countries=('country','nunique'),mean_js=('js_to_label_mean','mean'),median_js=('js_to_label_mean','median'))
         .to_csv(out/'table_s13_label_sensitivity.csv',index=False))

    opath=results/'option_order_metrics.csv'
    if opath.exists():
        o=pd.read_csv(opath)
        (o.groupby(['condition','condition_label','item'],as_index=False).agg(n=('js_from_first_order','size'),mean_js=('js_from_first_order','mean'),median_js=('js_from_first_order','median'))
         .to_csv(out/'table_s14_option_order_sensitivity.csv',index=False))

    # Cultural-map alignment and the explicit Tao replication checkpoint are SI outputs.
    stale=out/'table3_cultural_map.csv'
    if stale.exists(): stale.unlink()
    cpath=results/'cultural_map_distances.csv'
    if cpath.exists():
        c=pd.read_csv(cpath)
        cmap=(c.groupby(['condition','condition_label','representation'],as_index=False)
               .agg(mean_distance=('distance','mean'),median_distance=('distance','median'),n=('distance','size')))
        cmap.to_csv(out/'table_s15_cultural_map.csv',index=False)
        # Pair all representations and models on the same countries when comparing means.
        expected=c[c.representation=='expected']
        common=set.intersection(*(set(g.country) for _,g in expected.groupby('condition')))
        matched=c[c.country.isin(common)]
        (matched.groupby(['condition','condition_label','representation'],as_index=False)
         .agg(mean_distance=('distance','mean'),median_distance=('distance','median'),n=('distance','size'))
         .to_csv(results/'cultural_map_common_country_summary.csv',index=False))

    pmpath=results/'cultural_map_prompting_summary.csv'
    if pmpath.exists():
        pm=pd.read_csv(pmpath)
        rows=[]
        # Published benchmark from Tao et al. (2024), kept as a clearly identified external row.
        rows.append({'source':'Tao et al. (2024)','condition':'gpt4o_published','condition_label':'Tao GPT-4o',
                     'representation':'published point responses','n_countries':107,
                     'unconditioned_distance_mean':TAO_GPT4O['unconditioned_distance_mean'],
                     'country_conditioned_distance_mean':TAO_GPT4O['country_conditioned_distance_mean'],
                     'mean_distance_improvement':TAO_GPT4O['unconditioned_distance_mean']-TAO_GPT4O['country_conditioned_distance_mean'],
                     'pct_countries_improved':TAO_GPT4O['pct_countries_improved']})
        for r in pm.itertuples():
            rows.append({'source':'Current study','condition':r.condition,'condition_label':r.condition_label,
                         'representation':r.representation,'n_countries':r.n_countries,
                         'unconditioned_distance_mean':r.unconditioned_distance_mean,
                         'country_conditioned_distance_mean':r.country_conditioned_distance_mean,
                         'mean_distance_improvement':r.mean_distance_improvement,
                         'pct_countries_improved':r.pct_countries_improved})
        pd.DataFrame(rows).to_csv(out/'table_s16_tao_replication.csv',index=False)

    from .revision_outputs import make_revision_tables
    make_revision_tables(results)
    return summary,item,boot
