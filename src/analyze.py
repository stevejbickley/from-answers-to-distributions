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

def model_long(records):
    rows=[]; y3=[]
    for r in records:
        label_rep=int(r.get('label_rep',0))
        if r['item']=='Y003':
            y3.append({'provider':r['provider'],'country':r['country'],'variant':int(r['variant']),'label_rep':label_rep,
                       'quality':r['quality'],'p_selected':float(r['probabilities']['1']),
                       'allowed_mass':float(r.get('allowed_mass',1.0)),'missing_count':len(r.get('missing_labels',[]))})
            continue
        probs=r['probabilities']
        if r['item']=='Y002': probs=aggregate_y002(probs)
        for response,p in probs.items():
            rows.append({'provider':r['provider'],'country':r['country'],'variant':int(r['variant']),'label_rep':label_rep,'item':r['item'],
                         'response':str(response),'p':float(p),'allowed_mass':float(r.get('allowed_mass',1.0)),
                         'missing_count':len(r.get('missing_labels',[]))})
    return pd.DataFrame(rows),pd.DataFrame(y3)

def _vector(df, levels):
    if df.empty: return np.zeros(len(levels),float)
    # Average duplicated semantic responses (e.g. label replications) before vectorization.
    gg=df.groupby('response',as_index=False)['p'].mean()
    m={str(r.response):float(r.p) for r in gg.itertuples()}
    x=np.array([m.get(str(k),0.0) for k in levels],float); s=x.sum()
    return x/s if s>0 else x

def average_model(model):
    return (model.groupby(['provider','country','item','response'],as_index=False)
            .agg(p=('p','mean'),allowed_mass=('allowed_mass','mean'),missing_count=('missing_count','mean')))

def compare(human_csv, openai_jsonl, jev_jsonl, outdir='results', pca_json='data/processed/pca_model.json'):
    cfg=analysis(); qs=questions(); outdir=ensure_dir(outdir)
    human=pd.read_csv(human_csv); human['response']=human['response'].astype(str)
    openai_records=load_jsonl(openai_jsonl); jev_records=load_jsonl(jev_jsonl)
    # Primary OpenAI analysis uses only request records for which every allowed label was returned.
    # Diagnostics retain all requests; incomplete requests are never silently treated as exact zeros.
    complete_openai=[r for r in openai_records if len(r.get('missing_labels',[]))==0]
    recs=complete_openai+jev_records
    model,y3=model_long(recs); avg=average_model(model)
    # Save analysis-ready mean probability vectors.
    avg.to_csv(outdir/'model_mean_probabilities.csv',index=False)
    if not y3.empty:
        y3avg=y3.groupby(['provider','country','quality'],as_index=False).agg(p_selected=('p_selected','mean'),allowed_mass=('allowed_mass','mean'),missing_count=('missing_count','mean'))
        y3avg.to_csv(outdir/'model_y003_mean_marginals.csv',index=False)
    metric_rows=[]
    countries=sorted(set(human.country).intersection(set(avg.country)) - {DEFAULT_KEY})
    for country in countries:
        for item in cfg['primary_items']:
            levels=[str(x) for x in qs[item]['human_codes']]
            hg=human[(human.country==country)&(human.item==item)]
            if hg.empty: continue
            hp=_vector(hg,levels); vals=np.asarray(qs[item]['response_values'],float)
            for provider in ['openai','jev']:
                mg=avg[(avg.provider==provider)&(avg.country==country)&(avg.item==item)]
                if mg.empty: continue
                mp=_vector(mg,levels)
                row={'country':country,'item':item,'provider':provider,
                     'js':js_divergence(hp,mp),'tv':total_variation(hp,mp),
                     'expected_abs_error':abs(expected_value(vals,hp)-expected_value(vals,mp)),
                     'human_entropy':entropy(hp),'model_entropy':entropy(mp),
                     'entropy_signed_error':entropy(mp)-entropy(hp),
                     'entropy_abs_error':abs(entropy(hp)-entropy(mp)),
                     'human_effective_categories':effective_categories(hp),'model_effective_categories':effective_categories(mp),
                     'allowed_mass':float(mg.allowed_mass.mean()),'missing_count':float(mg.missing_count.mean())}
                row['wasserstein']=normalized_wasserstein(vals,hp,mp) if qs[item].get('ordered',False) else np.nan
                metric_rows.append(row)
    metrics=pd.DataFrame(metric_rows); metrics.to_csv(outdir/'country_item_metrics.csv',index=False)
    # Prompt sensitivity after averaging OpenAI label reps within descriptor.
    desc=(model.groupby(['provider','country','variant','item','response'],as_index=False)['p'].mean())
    sens=[]
    for (provider,country,item),g in desc.groupby(['provider','country','item']):
        levels=[str(x) for x in qs[item]['human_codes']]
        target=_vector(avg[(avg.provider==provider)&(avg.country==country)&(avg.item==item)],levels)
        for variant,vg in g.groupby('variant'):
            sens.append({'provider':provider,'country':country,'item':item,'variant':variant,
                         'js_to_provider_mean':js_divergence(_vector(vg,levels),target)})
    sensitivity=pd.DataFrame(sens); sensitivity.to_csv(outdir/'prompt_sensitivity.csv',index=False)
    # Label sensitivity for OpenAI: compare each label rep with descriptor-specific average.
    lab=[]
    om=model[model.provider=='openai']
    for (country,item,variant),g in om.groupby(['country','item','variant']):
        levels=[str(x) for x in qs[item]['human_codes']]
        target=_vector(g,levels)
        for rep,rg in g.groupby('label_rep'):
            lab.append({'country':country,'item':item,'variant':variant,'label_rep':rep,'js_to_label_mean':js_divergence(_vector(rg,levels),target)})
    pd.DataFrame(lab).to_csv(outdir/'openai_label_sensitivity.csv',index=False)
    # OpenAI request-level completeness diagnostics.
    diag=[]
    for r in openai_records:
        diag.append({'country':r['country'],'item':r['item'],'variant':r['variant'],'label_rep':r.get('label_rep',0),
                     'allowed_mass':float(r.get('allowed_mass',1.0)),'missing_count':len(r.get('missing_labels',[])),
                     'generated_token':r.get('generated_token'),'valid_generated':(str(r.get('generated_token','')).strip() in (r.get('prompt',{}).get('allowed_labels') or []))})
    pd.DataFrame(diag).to_csv(outdir/'openai_logprob_diagnostics.csv',index=False)
    # Y003 marginal comparisons.
    y3human_path=Path(human_csv).with_name('human_y003_country_marginals.csv')
    if y3human_path.exists() and not y3.empty:
        yh=pd.read_csv(y3human_path); ya=y3[y3.country!=DEFAULT_KEY].groupby(['provider','country','quality'],as_index=False)['p_selected'].mean()
        ym=ya.merge(yh,on=['country','quality'],suffixes=('_model','_human'))
        ym['abs_error']=(ym.p_selected_model-ym.p_selected_human).abs(); ym['sq_error']=(ym.p_selected_model-ym.p_selected_human)**2
        ym.to_csv(outdir/'y003_marginal_metrics.csv',index=False)
    # Cultural map expected and argmax coordinates.
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
    # Human expected vectors from empirical distributions plus exact Y003 expected index from marginals.
    hrows=[]
    for country in sorted(human.country.unique()):
        exp={}
        ok=True
        for item in cfg['primary_items']:
            g=human[(human.country==country)&(human.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item)
        yg=yh[yh.country==country]
        if ok and not yg.empty:
            mp={r.quality:float(r.p_selected) for r in yg.itertuples()}
            need=list(qs['Y003']['constituents'])
            if all(k in mp for k in need):
                exp['Y003']=mp['Independence']+mp['Determination, perseverance']-mp['Religious faith']-mp['Obedience']
                coord=project_expected_scores(exp,pca); hrows.append({'country':country,'provider':'human','representation':'expected',**coord})
    hcoord=pd.DataFrame(hrows)
    mrows=[]
    for (provider,country),_ in avg.groupby(['provider','country']):
        exp={}; arg={}; ok=True
        for item in cfg['primary_items']:
            g=avg[(avg.provider==provider)&(avg.country==country)&(avg.item==item)]
            if g.empty: ok=False; break
            exp[item]=_expected_from_dist(g,item); arg[item]=_argmax_from_dist(g,item)
        yg=y3[(y3.provider==provider)&(y3.country==country)]
        if ok and not yg.empty:
            yy=yg.groupby('quality')['p_selected'].mean().to_dict(); need=list(qs['Y003']['constituents'])
            if all(k in yy for k in need):
                exp['Y003']=yy['Independence']+yy['Determination, perseverance']-yy['Religious faith']-yy['Obedience']
                arg['Y003']=(1 if yy['Independence']>=.5 else 0)+(1 if yy['Determination, perseverance']>=.5 else 0)-(1 if yy['Religious faith']>=.5 else 0)-(1 if yy['Obedience']>=.5 else 0)
                mrows.append({'country':country,'provider':provider,'representation':'expected',**project_expected_scores(exp,pca)})
                mrows.append({'country':country,'provider':provider,'representation':'argmax',**project_expected_scores(arg,pca)})
    coords=pd.concat([hcoord,pd.DataFrame(mrows)],ignore_index=True); coords.to_csv(outdir/'cultural_map_coordinates.csv',index=False)
    humanxy=hcoord.set_index('country')[['survival_self_expression','traditional_secular']]
    drows=[]
    for r in pd.DataFrame(mrows).itertuples():
        if r.country==DEFAULT_KEY or r.country not in humanxy.index: continue
        hx,hy=humanxy.loc[r.country]
        d=float(np.hypot(r.survival_self_expression-hx,r.traditional_secular-hy))
        drows.append({'country':r.country,'provider':r.provider,'representation':r.representation,'distance':d})
    pd.DataFrame(drows).to_csv(outdir/'cultural_map_distances.csv',index=False)

def crossed_bootstrap_difference(metrics, metric='js', reps=5000, seed=20260923):
    """OpenAI minus Jev; positive means Jev has lower error."""
    piv=metrics.pivot_table(index=['country','item'],columns='provider',values=metric).dropna()
    if not {'openai','jev'}.issubset(piv.columns): return None
    diff=(piv['openai']-piv['jev']).rename('diff').reset_index(); point=float(diff['diff'].mean()); rng=np.random.default_rng(seed)
    mat=diff.pivot(index='country',columns='item',values='diff').to_numpy(float); nc,ni=mat.shape; draws=np.empty(reps,float)
    for b in range(reps):
        rr=rng.integers(0,nc,nc); cc=rng.integers(0,ni,ni); draws[b]=np.nanmean(mat[np.ix_(rr,cc)])
    good=draws[np.isfinite(draws)]; lo,hi=np.quantile(good,[.025,.975])
    try: _,p=wilcoxon(piv['openai'],piv['jev'],zero_method='wilcox',alternative='two-sided')
    except Exception: p=np.nan
    return {'metric':metric,'mean_openai_minus_jev':point,'ci95_low':float(lo),'ci95_high':float(hi),'wilcoxon_p':float(p),'n_country_item':int(len(piv))}
