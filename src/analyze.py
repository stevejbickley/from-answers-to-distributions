from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, pearsonr, spearmanr, norm
from .config import analysis, questions
from .prompts import y002_pairs
from .metrics import js_divergence,total_variation,normalized_wasserstein,expected_value,entropy,effective_categories
from .cultural_map import project_expected_scores
from .utils import ensure_dir

DEFAULT_KEY='__DEFAULT__'


def load_jsonl(path):
    rows=[]
    with open(path,encoding='utf-8') as f:
        for line in f:
            if line.strip(): rows.append(json.loads(line))
    return rows


def aggregate_y002(probs):
    pair_to_idx={x['pair']:str(x['index']) for x in y002_pairs()}
    out={'1':0.0,'2':0.0,'3':0.0}
    for pair,p in probs.items():
        if pair in pair_to_idx: out[pair_to_idx[pair]] += float(p)
    s=sum(out.values()); return {k:v/s for k,v in out.items()} if s else out


def _condition(r):
    if r.get('condition'): return str(r['condition'])
    return 'jev' if r.get('provider')=='jev' else 'openai_legacy'


def _missing_bound(r):
    if len(r.get('missing_labels',[])) == 0:
        return 0.0
    if r.get('missing_allowed_mass_upper_bound') is not None:
        return float(r['missing_allowed_mass_upper_bound'])
    # Backward-compatible conservative bound for old records.
    return max(0.0, 1.0-float(r.get('allowed_mass',0.0)))


def openai_record_included(r, policy='primary', cfg=None):
    cfg = cfg or analysis()
    c=cfg.get('openai_censoring',{})
    if len(r.get('missing_labels',[])) == 0:
        return True
    if policy == 'complete_only':
        return False
    threshold=float(c.get('strict_missing_mass_upper_bound',0.0001) if policy=='strict'
                    else c.get('primary_missing_mass_upper_bound',0.001))
    return _missing_bound(r) <= threshold


def model_long(records):
    rows=[]; y3=[]
    for r in records:
        cond=_condition(r); label_rep=int(r.get('label_rep',0))
        base={'provider':r['provider'],'condition':cond,'condition_label':r.get('condition_label',cond),
              'country':r['country'],'variant':int(r['variant']),'label_rep':label_rep,
              'model':r.get('model'),'requested_model':r.get('requested_model')}
        bound=_missing_bound(r) if r.get('provider')=='openai' else 0.0
        if r['item']=='Y003':
            y3.append({**base,'quality':r['quality'],'p_selected':float(r['probabilities']['1']),
                       'allowed_mass':float(r.get('allowed_mass',1.0)),'missing_count':len(r.get('missing_labels',[])),
                       'missing_mass_upper_bound':bound})
            continue
        probs=r['probabilities']
        if r['item']=='Y002': probs=aggregate_y002(probs)
        for response,p in probs.items():
            rows.append({**base,'item':r['item'],'response':str(response),'p':float(p),
                         'allowed_mass':float(r.get('allowed_mass',1.0)),
                         'missing_count':len(r.get('missing_labels',[])),
                         'missing_mass_upper_bound':bound})
    return pd.DataFrame(rows),pd.DataFrame(y3)


def _vector(df, levels):
    if df.empty: return np.zeros(len(levels),float)
    gg=df.groupby('response',as_index=False)['p'].mean()
    m={str(r.response):float(r.p) for r in gg.itertuples()}
    x=np.array([m.get(str(k),0.0) for k in levels],float); s=x.sum()
    return x/s if s>0 else x


def _argmax_vector(x):
    out=np.zeros_like(x,float)
    if len(x) and np.sum(x)>0: out[int(np.argmax(x))]=1.0
    return out


def average_model(model):
    return (model.groupby(['provider','condition','condition_label','country','item','response'],as_index=False)
            .agg(p=('p','mean'),allowed_mass=('allowed_mass','mean'),missing_count=('missing_count','mean'),
                 missing_mass_upper_bound=('missing_mass_upper_bound','mean')))


def _metric_table(human, avg, cfg, qs):
    metric_rows=[]
    countries=sorted(set(human.country).intersection(set(avg.country)) - {DEFAULT_KEY})
    for country in countries:
        for item in cfg['primary_items']:
            levels=[str(x) for x in qs[item]['human_codes']]
            hg=human[(human.country==country)&(human.item==item)]
            if hg.empty: continue
            hp=_vector(hg,levels); vals=np.asarray(qs[item]['response_values'],float)
            for cond in sorted(avg.condition.unique()):
                mg=avg[(avg.condition==cond)&(avg.country==country)&(avg.item==item)]
                if mg.empty: continue
                full=_vector(mg,levels)
                provider=str(mg.provider.iloc[0]); label=str(mg.condition_label.iloc[0])
                for representation,mp in [('full',full),('argmax',_argmax_vector(full))]:
                    row={'country':country,'item':item,'provider':provider,'condition':cond,'condition_label':label,
                         'representation':representation,'js':js_divergence(hp,mp),'tv':total_variation(hp,mp),
                         'expected_abs_error':abs(expected_value(vals,hp)-expected_value(vals,mp)),
                         'human_entropy':entropy(hp),'model_entropy':entropy(mp),
                         'entropy_signed_error':entropy(mp)-entropy(hp),'entropy_abs_error':abs(entropy(hp)-entropy(mp)),
                         'human_effective_categories':effective_categories(hp),'model_effective_categories':effective_categories(mp),
                         'allowed_mass':float(mg.allowed_mass.mean()),'missing_count':float(mg.missing_count.mean()),
                         'missing_mass_upper_bound':float(mg.missing_mass_upper_bound.mean())}
                    row['wasserstein']=normalized_wasserstein(vals,hp,mp) if qs[item].get('ordered',False) else np.nan
                    metric_rows.append(row)
    return pd.DataFrame(metric_rows)



def _safe_corr(x, y, method='pearson'):
    x=np.asarray(x,float); y=np.asarray(y,float)
    m=np.isfinite(x)&np.isfinite(y)
    x=x[m]; y=y[m]
    if len(x)<3 or np.nanstd(x,ddof=1)==0 or np.nanstd(y,ddof=1)==0:
        return np.nan
    try:
        if method=='spearman':
            return float(spearmanr(x,y).statistic)
        return float(pearsonr(x,y).statistic)
    except Exception:
        return np.nan


def _fisher_mean(values):
    x=np.asarray([v for v in values if np.isfinite(v)],float)
    if len(x)==0: return np.nan
    x=np.clip(x,-0.999999,0.999999)
    return float(np.tanh(np.mean(np.arctanh(x))))


def _clustered_entropy_regression(g, formula):
    """OLS slope on human_entropy with two-way clustered covariance by country and item."""
    try:
        import statsmodels.formula.api as smf
        from statsmodels.stats.sandwich_covariance import cov_cluster_2groups
        fit=smf.ols(formula,data=g).fit()
        if 'human_entropy' not in fit.model.exog_names:
            return {'slope':np.nan,'se':np.nan,'ci_low':np.nan,'ci_high':np.nan,'p':np.nan,'r2':float(fit.rsquared)}
        idx=fit.model.exog_names.index('human_entropy')
        c1=pd.Categorical(g['country']).codes
        c2=pd.Categorical(g['item']).codes
        cov=cov_cluster_2groups(fit,c1,c2)[0]
        # A negative clustered variance is undefined, not evidence of certainty.
        variance=float(cov[idx,idx])
        se=float(np.sqrt(variance)) if variance>=0 else np.nan
        slope=float(fit.params['human_entropy'])
        z=slope/se if se>0 else np.nan
        p=float(2*norm.sf(abs(z))) if np.isfinite(z) else np.nan
        return {'slope':slope,'se':se,'ci_low':slope-1.96*se if np.isfinite(se) else np.nan,
                'ci_high':slope+1.96*se if np.isfinite(se) else np.nan,'p':p,'r2':float(fit.rsquared)}
    except (ValueError, np.linalg.LinAlgError, ZeroDivisionError):
        # Never substitute pooled OLS under a fixed-effect label.
        return dict.fromkeys(['slope','se','ci_low','ci_high','p','r2'],np.nan)


def _two_way_residuals(g, column):
    import statsmodels.formula.api as smf
    fit=smf.ols(f'{column} ~ C(country) + C(item)',data=g).fit()
    return np.asarray(fit.resid,float)


def entropy_structure_analysis(metrics, outdir='results'):
    """Separate average entropy fidelity from the structure of entropy across countries/items."""
    outdir=ensure_dir(outdir)
    full=metrics[metrics.representation=='full'].copy() if 'representation' in metrics.columns else metrics.copy()
    summaries=[]; item_rows=[]; country_rows=[]
    for cond,g in full.groupby('condition'):
        g=g.dropna(subset=['human_entropy','model_entropy']).copy()
        if g.empty: continue
        label=str(g['condition_label'].iloc[0]) if 'condition_label' in g else cond
        overall_p=_safe_corr(g.human_entropy,g.model_entropy,'pearson')
        overall_s=_safe_corr(g.human_entropy,g.model_entropy,'spearman')
        reg0=_clustered_entropy_regression(g,'model_entropy ~ human_entropy')
        regi=_clustered_entropy_regression(g,'model_entropy ~ human_entropy + C(item)')
        regc=_clustered_entropy_regression(g,'model_entropy ~ human_entropy + C(country)')
        reg2=_clustered_entropy_regression(g,'model_entropy ~ human_entropy + C(country) + C(item)')
        rh=_two_way_residuals(g,'human_entropy'); rm=_two_way_residuals(g,'model_entropy')
        resid_p=_safe_corr(rh,rm,'pearson'); resid_s=_safe_corr(rh,rm,'spearman')
        hsd=float(np.nanstd(g.human_entropy,ddof=1)); msd=float(np.nanstd(g.model_entropy,ddof=1))
        rhsd=float(np.nanstd(rh,ddof=1)); rmsd=float(np.nanstd(rm,ddof=1))
        item_p=[]; item_s=[]; country_p=[]; country_s=[]
        for item,ig in g.groupby('item'):
            pr=_safe_corr(ig.human_entropy,ig.model_entropy,'pearson'); sr=_safe_corr(ig.human_entropy,ig.model_entropy,'spearman')
            slope=float(np.polyfit(ig.human_entropy,ig.model_entropy,1)[0]) if len(ig)>=3 and np.nanstd(ig.human_entropy)>0 else np.nan
            item_rows.append({'condition':cond,'condition_label':label,'item':item,'n':len(ig),'pearson':pr,'spearman':sr,'slope':slope,
                              'human_entropy_mean':ig.human_entropy.mean(),'model_entropy_mean':ig.model_entropy.mean()})
            if np.isfinite(pr): item_p.append(pr)
            if np.isfinite(sr): item_s.append(sr)
        for country,cg in g.groupby('country'):
            pr=_safe_corr(cg.human_entropy,cg.model_entropy,'pearson'); sr=_safe_corr(cg.human_entropy,cg.model_entropy,'spearman')
            slope=float(np.polyfit(cg.human_entropy,cg.model_entropy,1)[0]) if len(cg)>=3 and np.nanstd(cg.human_entropy)>0 else np.nan
            country_rows.append({'condition':cond,'condition_label':label,'country':country,'n':len(cg),'pearson':pr,'spearman':sr,'slope':slope})
            if np.isfinite(pr): country_p.append(pr)
            if np.isfinite(sr): country_s.append(sr)
        row={'condition':cond,'condition_label':label,'n':len(g),
             'pearson_overall':overall_p,'spearman_overall':overall_s,
             'human_entropy_sd':hsd,'model_entropy_sd':msd,'sd_ratio_model_to_human':msd/hsd if hsd>0 else np.nan,
             'two_way_resid_pearson':resid_p,'two_way_resid_spearman':resid_s,
             'two_way_resid_human_sd':rhsd,'two_way_resid_model_sd':rmsd,
             'two_way_resid_sd_ratio':rmsd/rhsd if rhsd>0 else np.nan,
             'within_item_pearson_fisher_mean':_fisher_mean(item_p),'within_item_spearman_fisher_mean':_fisher_mean(item_s),
             'within_item_pearson_median':float(np.nanmedian(item_p)) if item_p else np.nan,
             'within_item_spearman_median':float(np.nanmedian(item_s)) if item_s else np.nan,
             'within_country_pearson_fisher_mean':_fisher_mean(country_p),'within_country_spearman_fisher_mean':_fisher_mean(country_s),
             'within_country_pearson_median':float(np.nanmedian(country_p)) if country_p else np.nan,
             'within_country_spearman_median':float(np.nanmedian(country_s)) if country_s else np.nan}
        for prefix,res in [('ols',reg0),('item_fe',regi),('country_fe',regc),('two_way_fe',reg2)]:
            for key,val in res.items(): row[f'{prefix}_{key}']=val
        summaries.append(row)
    summary=pd.DataFrame(summaries); items=pd.DataFrame(item_rows); countries=pd.DataFrame(country_rows)
    summary.to_csv(Path(outdir)/'entropy_structure_summary.csv',index=False)
    items.to_csv(Path(outdir)/'entropy_structure_by_item.csv',index=False)
    countries.to_csv(Path(outdir)/'entropy_structure_by_country.csv',index=False)
    return summary,items,countries


def population_specificity_metrics(human, avg, cfg=None, qs=None):
    """Compare country-conditioned distributions with two no-new-API baselines.

    Baseline 1 is the same model condition under the unconditioned __DEFAULT__ prompt.
    Baseline 2 is the leave-one-country-out, equal-country human distribution for the item.
    Positive gain means the country-conditioned model is closer to that country's human distribution.
    """
    cfg=cfg or analysis(); qs=qs or questions(); rows=[]
    countries=sorted(set(human.country)-{DEFAULT_KEY})
    conditions=sorted(set(avg.condition))
    for cond in conditions:
        cg=avg[avg.condition==cond]
        if cg.empty: continue
        provider=str(cg.provider.iloc[0]); label=str(cg.condition_label.iloc[0])
        for country in countries:
            for item in cfg['primary_items']:
                levels=[str(x) for x in qs[item]['human_codes']]
                hg=human[(human.country==country)&(human.item==item)]
                mg=cg[(cg.country==country)&(cg.item==item)]
                if hg.empty or mg.empty: continue
                hp=_vector(hg,levels); mp=_vector(mg,levels)
                country_js=js_divergence(hp,mp)
                # Same model with country information removed.
                dg=cg[(cg.country==DEFAULT_KEY)&(cg.item==item)]
                default_js=np.nan; shift=np.nan
                if not dg.empty:
                    dp=_vector(dg,levels); default_js=js_divergence(hp,dp); shift=js_divergence(mp,dp)
                # Leave-one-country-out equal-country human baseline. This uses only
                # other countries, so the target country's empirical distribution cannot leak into its baseline.
                others=human[(human.country!=country)&(human.country!=DEFAULT_KEY)&(human.item==item)]
                loco_js=np.nan
                if not others.empty:
                    by_country=(others.groupby(['country','response'],as_index=False)['p'].mean()
                                .groupby('response',as_index=False)['p'].mean())
                    lp=_vector(by_country,levels); loco_js=js_divergence(hp,lp)
                rows.append({'provider':provider,'condition':cond,'condition_label':label,'country':country,'item':item,
                             'country_model_js':country_js,'default_model_js':default_js,
                             'gain_vs_default_js':default_js-country_js if np.isfinite(default_js) else np.nan,
                             'model_shift_from_default_js':shift,
                             'loco_human_js':loco_js,
                             'gain_vs_loco_human_js':loco_js-country_js if np.isfinite(loco_js) else np.nan})
    return pd.DataFrame(rows)


def crossed_bootstrap_mean(frame, value_col, reps=5000, seed=20260923):
    """Crossed country × item bootstrap for one mean quantity (e.g., a baseline gain)."""
    x=frame[['country','item',value_col]].dropna().copy()
    if x.empty: return None
    mat=x.pivot_table(index='country',columns='item',values=value_col,aggfunc='mean').to_numpy(float)
    point=float(x[value_col].mean()); rng=np.random.default_rng(seed); nc,ni=mat.shape; draws=np.empty(reps,float)
    for b in range(reps):
        rr=rng.integers(0,nc,nc); cc=rng.integers(0,ni,ni); draws[b]=np.nanmean(mat[np.ix_(rr,cc)])
    good=draws[np.isfinite(draws)]
    lo,hi=(np.quantile(good,[.025,.975]) if len(good) else (np.nan,np.nan))
    return {'mean':point,'ci95_low':float(lo),'ci95_high':float(hi),'n_country_item':int(len(x)),
            'n_countries':int(x.country.nunique()),'n_items':int(x.item.nunique())}

def compare(human_csv, openai_jsonl, jev_jsonl, outdir='results', pca_json='data/processed/pca_model.json'):
    cfg=analysis(); qs=questions(); outdir=ensure_dir(outdir)
    human=pd.read_csv(human_csv); human['response']=human['response'].astype(str)
    openai_records=load_jsonl(openai_jsonl); jev_records=load_jsonl(jev_jsonl)

    # Primary OpenAI policy: retain complete records plus tail-censored records
    # whose *upper bound* on omitted permitted-label mass is <= 0.001 by default.
    primary_openai=[r for r in openai_records if openai_record_included(r,'primary',cfg)]
    recs=primary_openai+jev_records
    model,y3=model_long(recs); avg=average_model(model)
    avg.to_csv(outdir/'model_mean_probabilities.csv',index=False)
    if not y3.empty:
        y3avg=y3.groupby(['provider','condition','condition_label','country','quality'],as_index=False).agg(
            p_selected=('p_selected','mean'),allowed_mass=('allowed_mass','mean'),missing_count=('missing_count','mean'),
            missing_mass_upper_bound=('missing_mass_upper_bound','mean'))
        y3avg.to_csv(outdir/'model_y003_mean_marginals.csv',index=False)

    metrics=_metric_table(human,avg,cfg,qs); metrics.to_csv(outdir/'country_item_metrics.csv',index=False)

    # Additional analyses that use only already-collected model outputs.
    # (1) Does country conditioning add population-specific distributional information?
    specificity=population_specificity_metrics(human,avg,cfg,qs)
    specificity.to_csv(outdir/'population_specificity_metrics.csv',index=False)
    # (2) Does model uncertainty track where human disagreement occurs after separating
    #     item- and country-level structure?
    entropy_structure_analysis(metrics,outdir)

    # Prespecified censoring sensitivity: primary threshold, stricter 1e-4, complete-only.
    sens_metrics=[]; policy_counts=[]
    for policy in ['primary','strict','complete_only']:
        selected=[r for r in openai_records if openai_record_included(r,policy,cfg)]
        pmodel,_=model_long(selected)
        pavg=average_model(pmodel) if not pmodel.empty else pd.DataFrame()
        pm=_metric_table(human,pavg,cfg,qs) if not pavg.empty else pd.DataFrame()
        if not pm.empty:
            pm=pm[pm.provider=='openai'].copy(); pm['censoring_policy']=policy; sens_metrics.append(pm)
        for cond in sorted({_condition(r) for r in openai_records}):
            allc=[r for r in openai_records if _condition(r)==cond]
            selc=[r for r in selected if _condition(r)==cond]
            policy_counts.append({'condition':cond,'censoring_policy':policy,'records_total':len(allc),'records_included':len(selc),
                                  'records_excluded':len(allc)-len(selc),'included_percent':100*len(selc)/len(allc) if allc else np.nan})
    if sens_metrics:
        sm=pd.concat(sens_metrics,ignore_index=True); sm.to_csv(outdir/'country_item_metrics_censoring_sensitivity.csv',index=False)
        ss=(sm[sm.representation=='full'].groupby(['condition','condition_label','censoring_policy'],as_index=False)
            .agg(n_country_item=('js','size'),js_mean=('js','mean'),tv_mean=('tv','mean'),
                 expected_abs_error_mean=('expected_abs_error','mean'),entropy_abs_error_mean=('entropy_abs_error','mean')))
        ss.to_csv(outdir/'openai_censoring_sensitivity_summary.csv',index=False)
    pd.DataFrame(policy_counts).to_csv(outdir/'openai_censoring_policy_counts.csv',index=False)

    # Prompt sensitivity after primary censoring policy and averaging label rotations.
    desc=(model.groupby(['provider','condition','condition_label','country','variant','item','response'],as_index=False)['p'].mean())
    sens=[]
    for (provider,cond,label,country,item),g in desc.groupby(['provider','condition','condition_label','country','item']):
        levels=[str(x) for x in qs[item]['human_codes']]
        target=_vector(avg[(avg.condition==cond)&(avg.country==country)&(avg.item==item)],levels)
        n_variants=int(g.variant.nunique())
        for variant,vg in g.groupby('variant'):
            sens.append({'provider':provider,'condition':cond,'condition_label':label,'country':country,'item':item,'variant':variant,
                         'n_variants_retained':n_variants,
                         'js_to_condition_mean':js_divergence(_vector(vg,levels),target) if n_variants>=2 else np.nan})
    sensitivity=pd.DataFrame(sens); sensitivity.to_csv(outdir/'prompt_sensitivity.csv',index=False)

    # OpenAI label sensitivity separately by model condition.
    lab=[]; om=model[model.provider=='openai']
    for (cond,country,item,variant),g in om.groupby(['condition','country','item','variant']):
        levels=[str(x) for x in qs[item]['human_codes']]; target=_vector(g,levels)
        n_labels=int(g.label_rep.nunique())
        for rep,rg in g.groupby('label_rep'):
            lab.append({'condition':cond,'country':country,'item':item,'variant':variant,'label_rep':rep,
                        'n_label_repetitions_retained':n_labels,
                        'js_to_label_mean':js_divergence(_vector(rg,levels),target) if n_labels>=2 else np.nan})
    pd.DataFrame(lab).to_csv(outdir/'openai_label_sensitivity.csv',index=False)

    # Request-level OpenAI censoring/completeness diagnostics.
    diag=[]
    for r in openai_records:
        bound=_missing_bound(r)
        diag.append({'condition':_condition(r),'condition_label':r.get('condition_label',_condition(r)),
                     'quality':r.get('quality'), 'request_id':r.get('response_id') or r.get('request_id') or r.get('id'),
                     'requested_model':r.get('requested_model'),'served_model':r.get('model'),
                     'country':r['country'],'item':r['item'],'variant':r['variant'],'label_rep':r.get('label_rep',0),
                     'temperature':r.get('temperature'),
                     'allowed_mass':float(r.get('allowed_mass',1.0)),
                     'residual_probability_mass':float(r.get('residual_probability_mass',max(0,1-float(r.get('allowed_mass',1.0))))),
                     'missing_count':len(r.get('missing_labels',[])),
                     'missing_allowed_mass_upper_bound':bound,
                     'missing_mass_bound_method':r.get('missing_mass_bound_method'),
                     'censoring_status':r.get('censoring_status','COMPLETE' if len(r.get('missing_labels',[]))==0 else 'LEGACY_INCOMPLETE'),
                     'top_logprobs_requested':r.get('top_logprobs_requested'),
                     'top_logprobs_returned':r.get('top_logprobs_returned'),
                     'top_logprob_cutoff_probability':r.get('top_logprob_cutoff_probability'),
                     'primary_included':openai_record_included(r,'primary',cfg),
                     'strict_included':openai_record_included(r,'strict',cfg),
                     'complete_only_included':openai_record_included(r,'complete_only',cfg),
                     'generated_token':r.get('generated_token'),
                     'valid_generated':(str(r.get('generated_token','')).strip() in (r.get('prompt',{}).get('allowed_labels') or []))})
    pd.DataFrame(diag).to_csv(outdir/'openai_logprob_diagnostics.csv',index=False)

    # Y003 marginal comparisons under the primary censoring policy.
    y3human_path=Path(human_csv).with_name('human_y003_country_marginals.csv')
    if y3human_path.exists() and not y3.empty:
        yh=pd.read_csv(y3human_path); ya=y3[y3.country!=DEFAULT_KEY].groupby(['provider','condition','condition_label','country','quality'],as_index=False)['p_selected'].mean()
        ym=ya.merge(yh,on=['country','quality'],suffixes=('_model','_human'))
        ym['abs_error']=(ym.p_selected_model-ym.p_selected_human).abs(); ym['sq_error']=(ym.p_selected_model-ym.p_selected_human)**2
        ym.to_csv(outdir/'y003_marginal_metrics.csv',index=False)
    if Path(pca_json).exists() and y3human_path.exists():
        make_cultural_map_outputs(human,avg,model,y3,Path(y3human_path),pca_json,outdir)
    return metrics,sensitivity

def _expected_from_dist(g, item):
    qs=questions(); levels=[str(x) for x in qs[item]['human_codes']]; vals=np.asarray(qs[item]['response_values'],float)
    return expected_value(vals,_vector(g,levels))

def _argmax_from_dist(g,item):
    qs=questions(); levels=[str(x) for x in qs[item]['human_codes']]; p=_vector(g,levels); vals=np.asarray(qs[item]['response_values'],float)
    return float(vals[int(np.argmax(p))])

def _y003_from_marginals(values, threshold=False):
    """Construct expected or modal Y003 from its four required marginals."""
    need=['Independence','Determination, perseverance','Religious faith','Obedience']
    if not all(k in values for k in need):
        return np.nan
    if threshold:
        v={k:(1.0 if float(values[k])>=0.5 else 0.0) for k in need}
    else:
        v={k:float(values[k]) for k in need}
    return v['Independence']+v['Determination, perseverance']-v['Religious faith']-v['Obedience']


def _map_distance(x1,y1,x2,y2):
    return float(np.hypot(float(x1)-float(x2),float(y1)-float(y2)))


def make_cultural_map_outputs(human,avg,model,y3,y3human_path,pca_json,outdir):
    """Create cultural-map coordinates plus Tao-style prompting diagnostics.

    Three machine representations are produced where the data permit:
      * expected: expected item scores from the final averaged probability vector;
      * argmax: argmax of that same final averaged probability vector;
      * tao_modal: a close reconstruction of Tao et al.'s point-response logic.
        For each prompt variant we first average OpenAI label rotations, collapse
        each item to its modal substantive response, project that complete
        ten-item point profile into the human PCA space, and then average the
        resulting coordinates across prompt variants. Y003 is reconstructed
        from the four collected marginals, so this is deliberately described as
        Tao-style rather than an exact reproduction of Tao et al.'s direct Y003
        joint-choice elicitation.

    No additional provider calls are made: all outputs are reconstructed from
    the already-collected probability records.
    """
    cfg=analysis(); qs=questions(); outdir=Path(outdir)
    pca=json.loads(Path(pca_json).read_text())
    for k in ['R','eigenvalues','loadings','score_coef']:
        if k in pca: pca[k]=np.asarray(pca[k],float)
    yh=pd.read_csv(y3human_path)

    # Human release-updated cultural-map coordinates.
    hrows=[]
    for country in sorted(human.country.unique()):
        exp={}; ok=True
        for item in cfg['primary_items']:
            g=human[(human.country==country)&(human.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item)
        yg=yh[yh.country==country]
        if ok and not yg.empty:
            mp={r.quality:float(r.p_selected) for r in yg.itertuples()}
            exp['Y003']=_y003_from_marginals(mp,threshold=False)
            if np.isfinite(exp['Y003']):
                hrows.append({'country':country,'provider':'human','condition':'human',
                              'condition_label':'Human IVS','representation':'expected',
                              **project_expected_scores(exp,pca)})
    hcoord=pd.DataFrame(hrows)

    # Final averaged expected-score and argmax representations.
    mrows=[]
    for (provider,cond,label,country),_ in avg.groupby(['provider','condition','condition_label','country']):
        exp={}; arg={}; ok=True
        for item in cfg['primary_items']:
            g=avg[(avg.condition==cond)&(avg.country==country)&(avg.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item); arg[item]=_argmax_from_dist(g,item)
        yg=y3[(y3.condition==cond)&(y3.country==country)]
        if ok and not yg.empty:
            yy=yg.groupby('quality')['p_selected'].mean().to_dict()
            exp['Y003']=_y003_from_marginals(yy,threshold=False)
            arg['Y003']=_y003_from_marginals(yy,threshold=True)
            if np.isfinite(exp['Y003']) and np.isfinite(arg['Y003']):
                mrows.append({'country':country,'provider':provider,'condition':cond,
                              'condition_label':label,'representation':'expected',
                              **project_expected_scores(exp,pca)})
                mrows.append({'country':country,'provider':provider,'condition':cond,
                              'condition_label':label,'representation':'argmax',
                              **project_expected_scores(arg,pca)})

    # Close Tao-style point-response reconstruction from frozen probability records.
    # Label rotations are averaged within prompt variant before the modal response
    # is chosen so the arbitrary A/B/C/... mapping does not decide the result.
    variant_rows=[]
    if model is not None and not model.empty and y3 is not None and not y3.empty:
        vm=(model.groupby(['provider','condition','condition_label','country','variant','item','response'],as_index=False)
                  .agg(p=('p','mean')))
        vy=(y3.groupby(['provider','condition','condition_label','country','variant','quality'],as_index=False)
                .agg(p_selected=('p_selected','mean')))
        keys=vm[['provider','condition','condition_label','country','variant']].drop_duplicates()
        for rr in keys.itertuples(index=False):
            provider,cond,label,country,variant=rr
            point={}; ok=True
            for item in cfg['primary_items']:
                g=vm[(vm.condition==cond)&(vm.country==country)&(vm.variant==variant)&(vm.item==item)]
                if g.empty: ok=False; break
                point[item]=_argmax_from_dist(g,item)
            yg=vy[(vy.condition==cond)&(vy.country==country)&(vy.variant==variant)]
            if ok and not yg.empty:
                yy=yg.set_index('quality').p_selected.to_dict()
                point['Y003']=_y003_from_marginals(yy,threshold=True)
                if np.isfinite(point['Y003']):
                    xy=project_expected_scores(point,pca)
                    variant_rows.append({'country':country,'provider':provider,'condition':cond,
                                         'condition_label':label,'variant':int(variant),
                                         'representation':'tao_modal_variant',**xy})
    variant_df=pd.DataFrame(variant_rows)
    if not variant_df.empty:
        variant_df.to_csv(outdir/'cultural_map_tao_style_variant_coordinates.csv',index=False)
        tao=(variant_df.groupby(['country','provider','condition','condition_label'],as_index=False)
                    .agg(survival_self_expression=('survival_self_expression','mean'),
                         traditional_secular=('traditional_secular','mean'),
                         n_variants_used=('variant','nunique')))
        tao['representation']='tao_modal'
        mrows.extend(tao.to_dict('records'))

    model_coords=pd.DataFrame(mrows)
    coords=pd.concat([hcoord,model_coords],ignore_index=True,sort=False)
    coords.to_csv(outdir/'cultural_map_coordinates.csv',index=False)

    # Country-conditioned distances to the corresponding human country.
    humanxy=hcoord.set_index('country')[['survival_self_expression','traditional_secular']]
    drows=[]
    for r in model_coords.itertuples():
        if r.country==DEFAULT_KEY or r.country not in humanxy.index: continue
        hx,hy=humanxy.loc[r.country]
        drows.append({'country':r.country,'provider':r.provider,'condition':r.condition,
                      'condition_label':r.condition_label,'representation':r.representation,
                      'distance':_map_distance(r.survival_self_expression,r.traditional_secular,hx,hy)})
    dist=pd.DataFrame(drows)
    dist.to_csv(outdir/'cultural_map_distances.csv',index=False)

    # Direct analogue of Tao et al.'s cultural-prompting comparison: for every
    # target country, compare distance from the same model's unconditioned
    # (__DEFAULT__) cultural position with distance from its country-conditioned
    # position. This is the clean replication/extension output used by Fig. 1.
    prows=[]
    for (cond,rep),g in model_coords.groupby(['condition','representation']):
        default=g[g.country==DEFAULT_KEY]
        if default.empty: continue
        d0=default.iloc[0]
        for r in g[g.country!=DEFAULT_KEY].itertuples():
            if r.country not in humanxy.index: continue
            hx,hy=humanxy.loc[r.country]
            uncond=_map_distance(d0.survival_self_expression,d0.traditional_secular,hx,hy)
            prompted=_map_distance(r.survival_self_expression,r.traditional_secular,hx,hy)
            prows.append({'country':r.country,'provider':r.provider,'condition':r.condition,
                          'condition_label':r.condition_label,'representation':rep,
                          'unconditioned_distance':uncond,'country_conditioned_distance':prompted,
                          'distance_improvement':uncond-prompted,
                          'improved':bool(prompted<uncond)})
    prompting=pd.DataFrame(prows)
    prompting.to_csv(outdir/'cultural_map_prompting_distances.csv',index=False)
    if not prompting.empty:
        summ=(prompting.groupby(['provider','condition','condition_label','representation'],as_index=False)
              .agg(n_countries=('country','size'),
                   unconditioned_distance_mean=('unconditioned_distance','mean'),
                   unconditioned_distance_median=('unconditioned_distance','median'),
                   country_conditioned_distance_mean=('country_conditioned_distance','mean'),
                   country_conditioned_distance_median=('country_conditioned_distance','median'),
                   mean_distance_improvement=('distance_improvement','mean'),
                   median_distance_improvement=('distance_improvement','median'),
                   pct_countries_improved=('improved',lambda x:100*float(pd.Series(x).astype(bool).mean()))))
        summ.to_csv(outdir/'cultural_map_prompting_summary.csv',index=False)

def crossed_bootstrap_contrast(metrics, condition_a, condition_b, metric='js', representation='full', reps=5000, seed=20260923):
    """Mean error(A)-error(B); positive means B has lower error."""
    mm=metrics[metrics.representation==representation] if 'representation' in metrics.columns else metrics
    piv=mm.pivot_table(index=['country','item'],columns='condition',values=metric)
    if not {condition_a,condition_b}.issubset(piv.columns): return None
    piv=piv.dropna(subset=[condition_a,condition_b])
    diff=(piv[condition_a]-piv[condition_b]).rename('diff').reset_index(); point=float(diff['diff'].mean()); rng=np.random.default_rng(seed)
    mat=diff.pivot(index='country',columns='item',values='diff').to_numpy(float); nc,ni=mat.shape; draws=np.empty(reps,float)
    for b in range(reps):
        rr=rng.integers(0,nc,nc); cc=rng.integers(0,ni,ni); draws[b]=np.nanmean(mat[np.ix_(rr,cc)])
    good=draws[np.isfinite(draws)]; lo,hi=np.quantile(good,[.025,.975])
    try: _,p=wilcoxon(piv[condition_a],piv[condition_b],zero_method='wilcox',alternative='two-sided')
    except Exception: p=np.nan
    return {'metric':metric,'representation':representation,'condition_a':condition_a,'condition_b':condition_b,
            'mean_error_a_minus_b':point,'ci95_low':float(lo),'ci95_high':float(hi),'wilcoxon_p':float(p),'n_country_item':int(len(piv))}

def crossed_bootstrap_difference(metrics, metric='js', reps=5000, seed=20260923):
    """Backward-compatible primary contrast: GPT-5.6 Sol minus Jev."""
    return crossed_bootstrap_contrast(metrics,'gpt56_sol','jev',metric=metric,reps=reps,seed=seed)
