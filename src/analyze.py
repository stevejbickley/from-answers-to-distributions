from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
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
        for variant,vg in g.groupby('variant'):
            sens.append({'provider':provider,'condition':cond,'condition_label':label,'country':country,'item':item,'variant':variant,
                         'js_to_condition_mean':js_divergence(_vector(vg,levels),target)})
    sensitivity=pd.DataFrame(sens); sensitivity.to_csv(outdir/'prompt_sensitivity.csv',index=False)

    # OpenAI label sensitivity separately by model condition.
    lab=[]; om=model[model.provider=='openai']
    for (cond,country,item,variant),g in om.groupby(['condition','country','item','variant']):
        levels=[str(x) for x in qs[item]['human_codes']]; target=_vector(g,levels)
        for rep,rg in g.groupby('label_rep'):
            lab.append({'condition':cond,'country':country,'item':item,'variant':variant,'label_rep':rep,
                        'js_to_label_mean':js_divergence(_vector(rg,levels),target)})
    pd.DataFrame(lab).to_csv(outdir/'openai_label_sensitivity.csv',index=False)

    # Request-level OpenAI censoring/completeness diagnostics.
    diag=[]
    for r in openai_records:
        bound=_missing_bound(r)
        diag.append({'condition':_condition(r),'condition_label':r.get('condition_label',_condition(r)),
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
        make_cultural_map_outputs(human,avg,y3,Path(y3human_path),pca_json,outdir)
    return metrics,sensitivity

def _expected_from_dist(g, item):
    qs=questions(); levels=[str(x) for x in qs[item]['human_codes']]; vals=np.asarray(qs[item]['response_values'],float)
    return expected_value(vals,_vector(g,levels))

def _argmax_from_dist(g,item):
    qs=questions(); levels=[str(x) for x in qs[item]['human_codes']]; p=_vector(g,levels); vals=np.asarray(qs[item]['response_values'],float)
    return float(vals[int(np.argmax(p))])

def make_cultural_map_outputs(human,avg,y3,y3human_path,pca_json,outdir):
    cfg=analysis(); qs=questions(); outdir=Path(outdir)
    pca=json.loads(Path(pca_json).read_text())
    for k in ['R','eigenvalues','loadings','score_coef']:
        if k in pca: pca[k]=np.asarray(pca[k],float)
    yh=pd.read_csv(y3human_path)
    hrows=[]
    for country in sorted(human.country.unique()):
        exp={}; ok=True
        for item in cfg['primary_items']:
            g=human[(human.country==country)&(human.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item)
        yg=yh[yh.country==country]
        if ok and not yg.empty:
            mp={r.quality:float(r.p_selected) for r in yg.itertuples()}; need=list(qs['Y003']['constituents'])
            if all(k in mp for k in need):
                exp['Y003']=mp['Independence']+mp['Determination, perseverance']-mp['Religious faith']-mp['Obedience']
                hrows.append({'country':country,'provider':'human','condition':'human','condition_label':'Human IVS','representation':'expected',**project_expected_scores(exp,pca)})
    hcoord=pd.DataFrame(hrows); mrows=[]
    for (provider,cond,label,country),_ in avg.groupby(['provider','condition','condition_label','country']):
        exp={}; arg={}; ok=True
        for item in cfg['primary_items']:
            g=avg[(avg.condition==cond)&(avg.country==country)&(avg.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item); arg[item]=_argmax_from_dist(g,item)
        yg=y3[(y3.condition==cond)&(y3.country==country)]
        if ok and not yg.empty:
            yy=yg.groupby('quality')['p_selected'].mean().to_dict(); need=list(qs['Y003']['constituents'])
            if all(k in yy for k in need):
                exp['Y003']=yy['Independence']+yy['Determination, perseverance']-yy['Religious faith']-yy['Obedience']
                arg['Y003']=(1 if yy['Independence']>=.5 else 0)+(1 if yy['Determination, perseverance']>=.5 else 0)-(1 if yy['Religious faith']>=.5 else 0)-(1 if yy['Obedience']>=.5 else 0)
                mrows.append({'country':country,'provider':provider,'condition':cond,'condition_label':label,'representation':'expected',**project_expected_scores(exp,pca)})
                mrows.append({'country':country,'provider':provider,'condition':cond,'condition_label':label,'representation':'argmax',**project_expected_scores(arg,pca)})
    coords=pd.concat([hcoord,pd.DataFrame(mrows)],ignore_index=True); coords.to_csv(outdir/'cultural_map_coordinates.csv',index=False)
    humanxy=hcoord.set_index('country')[['survival_self_expression','traditional_secular']]; drows=[]
    for r in pd.DataFrame(mrows).itertuples():
        if r.country==DEFAULT_KEY or r.country not in humanxy.index: continue
        hx,hy=humanxy.loc[r.country]; d=float(np.hypot(r.survival_self_expression-hx,r.traditional_secular-hy))
        drows.append({'country':r.country,'provider':r.provider,'condition':r.condition,'condition_label':r.condition_label,'representation':r.representation,'distance':d})
    pd.DataFrame(drows).to_csv(outdir/'cultural_map_distances.csv',index=False)

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
