"""Country-specific signal and robustness analyses using frozen model outputs.

Human-target sampling and crossed country/item resampling answer different
questions; their intervals are deliberately kept in separate output tables.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.linalg import qr
from scipy.special import xlogy
from scipy.stats import rankdata

from .config import analysis, questions
from .human import (load_ivsd, clean, build_country_universe, human_target_diagnostics,
                    bootstrap_human_probabilities)

DEFAULT = '__DEFAULT__'


def distribution_array(frame, countries, items):
    qs = questions()
    out = np.full((len(countries), len(items), max(len(qs[j]['human_codes']) for j in items)), np.nan)
    ci, ji = {c:i for i,c in enumerate(countries)}, {j:i for i,j in enumerate(items)}
    for (country, item), g in frame.groupby(['country', 'item']):
        if country not in ci or item not in ji:
            continue
        if g.response.astype(str).duplicated().any():
            raise ValueError(f'Duplicate response probabilities: {country}, {item}')
        values = dict(zip(g.response.astype(str), g.p.astype(float)))
        v = np.array([values.get(str(k), 0.) for k in qs[item]['human_codes']])
        if not np.isfinite(v).all() or np.any(v < 0) or not np.isclose(v.sum(), 1., atol=1e-8):
            raise ValueError(f'Invalid probability vector: {country}, {item}')
        out[ci[country], ji[item]] = 0.
        out[ci[country], ji[item], :len(v)] = v / v.sum()
    return out


def js_array(a, b):
    """JSD on the last axis, including zero probabilities and padded categories."""
    m = (a + b) / 2
    with np.errstate(invalid='ignore', divide='ignore'):
        return .5 * np.sum(xlogy(a, a) + xlogy(b, b) - xlogy(a + b, m), axis=-1) / np.log(2)


def entropy_array(p, items):
    counts = np.array([len(questions()[j]['human_codes']) for j in items])
    return -np.sum(xlogy(p, p), axis=-1) / np.log(counts)


def loco_array(h):
    """Equal-country item distribution excluding the target, for arrays or draws."""
    n = np.sum(np.isfinite(h[..., 0]), axis=-2, keepdims=True)
    total = np.nansum(h, axis=-3, keepdims=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        return np.where(n[..., None] > 1, (total - h) / (n[..., None] - 1), np.nan)


def direction_components(h, p, default, loco, *, min_human=1e-8, min_model=1e-12):
    dh, dp = h - loco, p - default
    hn, pn = np.linalg.norm(dh, axis=-1), np.linalg.norm(dp, axis=-1)
    usable = np.isfinite(hn) & np.isfinite(pn) & (hn > min_human)
    moving = pn > min_model
    dot = np.sum(dh * dp, axis=-1)
    dot = np.where(np.isfinite(pn) & ~moving, 0., dot)
    with np.errstate(invalid='ignore', divide='ignore'):
        return {'human_shift_norm':hn, 'model_shift_norm':pn,
                'dot_product':dot, 'human_shift_sq':hn ** 2,
                'direction_correct':np.where(usable, (dot > 0).astype(float), np.nan),
                'cosine_similarity':np.where(usable & moving, np.clip(dot / (hn * pn), -1., 1.), np.nan),
                'projection_coefficient':np.where(usable, dot / hn ** 2, np.nan),
                'magnitude_ratio':np.where(usable, pn / hn, np.nan)}


def compute_cultural_deviation_alignment(human, model, cfg=None):
    cfg = cfg or analysis()
    items = cfg['primary_items']
    countries = sorted(set(human.country) - {DEFAULT})
    h = distribution_array(human, countries, items)
    l = loco_array(h)
    rows = []
    tol = cfg.get('cultural_direction', {})
    for condition, g in model.groupby('condition'):
        p = distribution_array(g, countries, items)
        default = distribution_array(g, [DEFAULT], items)
        components = direction_components(h, p, default, l,
            min_human=float(tol.get('min_human_shift_norm', 1e-8)),
            min_model=float(tol.get('min_model_shift_norm', 1e-12)))
        for c, country in enumerate(countries):
            for j, item in enumerate(items):
                if not np.isfinite(p[c,j]).all() or not np.isfinite(h[c,j]).all():
                    continue
                rows.append({'condition':condition, 'country':country, 'item':item,
                             **{key:float(value[c,j]) for key,value in components.items()}})
    return pd.DataFrame(rows)


def direction_summary(frame, *, reps=5000, seed=20260930):
    """Pooled projection uses sums, never a mean of unstable cellwise ratios."""
    valid = frame.direction_correct.notna()
    g = frame.loc[valid]
    cosine = g.cosine_similarity.dropna()
    row = {'n_cells':len(frame), 'n_direction_cells':len(g), 'n_cosine_cells':len(cosine),
           'n_tiny_or_unavailable_human_shift':int((~valid).sum()),
           'n_zero_model_shift':int(g.cosine_similarity.isna().sum()),
           'direction_correct_percent':100 * g.direction_correct.mean(),
           'cosine_mean':cosine.mean(),
           'projection_pooled':g.dot_product.sum() / g.human_shift_sq.sum() if len(g) else np.nan,
           'human_shift_norm_mean':g.human_shift_norm.mean(),
           'model_shift_norm_mean':g.model_shift_norm.mean(),
           'magnitude_ratio_median':g.magnitude_ratio.median()}
    if not len(g) or not reps:
        return row
    countries, items = sorted(frame.country.unique()), sorted(frame.item.unique())
    def mat(col):
        return g.pivot(index='country', columns='item', values=col).reindex(index=countries, columns=items).to_numpy(float)
    mats = {key:mat(key) for key in ['direction_correct', 'cosine_similarity', 'dot_product', 'human_shift_sq']}
    rng = np.random.default_rng(seed)
    nc, nj = len(countries), len(items)
    wc = rng.multinomial(nc, np.full(nc, 1/nc), size=reps)
    wj = rng.multinomial(nj, np.full(nj, 1/nj), size=reps)
    def total(m):
        return np.einsum('bc,cj,bj->b', wc, np.nan_to_num(m, nan=0.), wj, optimize=True)
    with np.errstate(invalid='ignore', divide='ignore'):
        draws = {'direction_correct_percent':100 * total(mats['direction_correct']) / total(np.isfinite(mats['direction_correct'])),
                 'cosine_mean':total(mats['cosine_similarity']) / total(np.isfinite(mats['cosine_similarity'])),
                 'projection_pooled':total(mats['dot_product']) / total(mats['human_shift_sq'])}
    for key, values in draws.items():
        values = values[np.isfinite(values)]
        row[key + '_ci_low'], row[key + '_ci_high'] = np.quantile(values, [.025, .975]) if len(values) else (np.nan,np.nan)
        row[key + '_valid_bootstrap_draws'] = len(values)
    return row


def direction_tables(frame, cfg=None):
    opts = (cfg or analysis()).get('cultural_direction', {})
    kwargs = {'reps':int(opts.get('bootstrap_reps',5000)), 'seed':int(opts.get('seed',20260930))}
    overall = pd.DataFrame([{'condition':c, **direction_summary(g, **kwargs)} for c,g in frame.groupby('condition')])
    by_item = pd.DataFrame([{'condition':c, 'item':j, **direction_summary(g, **kwargs)} for (c,j),g in frame.groupby(['condition','item'])])
    return overall, by_item


def fixed_effect_basis(countries, items):
    design = np.column_stack([np.ones(len(countries)),
        pd.get_dummies(pd.Series(countries), drop_first=True, dtype=float).to_numpy(),
        pd.get_dummies(pd.Series(items), drop_first=True, dtype=float).to_numpy()])
    q, r, _ = qr(design, mode='economic', pivoting=True)
    diagonal = np.abs(np.diag(r))
    rank = int(np.sum(diagonal > np.max(design.shape) * np.finfo(float).eps * diagonal.max()))
    return q[:, :rank]


def residual_association(x, y, q=None):
    x, y = np.asarray(x,float), np.asarray(y,float)
    if q is not None:
        x, y = x - q @ (q.T @ x), y - q @ (q.T @ y)
    else:
        x, y = x - x.mean(axis=0), y - y.mean(axis=0)
    den = np.sum(x*x,axis=0)
    other = np.sum(y*y,axis=0)
    dot = np.sum(x*y,axis=0)
    with np.errstate(invalid='ignore',divide='ignore'):
        slope = np.where(den > 1e-15, dot/den, np.nan)
        pearson = np.where((den>1e-15)&(other>1e-15), dot/np.sqrt(den*other), np.nan)
    rx, ry = rankdata(x,axis=0), rankdata(y,axis=0)
    rx, ry = rx-rx.mean(axis=0), ry-ry.mean(axis=0)
    with np.errstate(invalid='ignore',divide='ignore'):
        spearman = np.where((den>1e-15)&(other>1e-15),
            np.sum(rx*ry,axis=0)/np.sqrt(np.sum(rx*rx,axis=0)*np.sum(ry*ry,axis=0)),np.nan)
    return {'slope':slope, 'pearson':pearson, 'spearman':spearman}


def compute_entropy_leave_one_item_out(metrics):
    full = metrics.loc[metrics.representation.eq('full')].copy() if 'representation' in metrics else metrics.copy()
    rows = []
    for condition,g in full.groupby('condition'):
        for omitted in [None, *sorted(g.item.unique())]:
            use = g if omitted is None else g.loc[g.item.ne(omitted)]
            use = use.dropna(subset=['human_entropy','model_entropy'])
            q = fixed_effect_basis(use.country, use.item)
            result = residual_association(use.human_entropy, use.model_entropy, q)
            rows.append({'condition':condition, 'omitted_item':'none' if omitted is None else omitted,
                         'n_cells':len(use), 'n_countries':use.country.nunique(), 'n_items':use.item.nunique(),
                         **{'two_way_'+key:float(value) for key,value in result.items()}})
    details = pd.DataFrame(rows)
    summaries = []
    for condition,g in details.groupby('condition'):
        base = g.loc[g.omitted_item.eq('none')].iloc[0]
        lo = g.loc[g.omitted_item.ne('none')]
        row = {'condition':condition, 'n_omissions':len(lo)}
        for key in ['slope','pearson','spearman']:
            col = 'two_way_'+key
            changes = (lo[col]-base[col]).abs()
            row.update({col+'_full':base[col], col+'_min':lo[col].min(), col+'_median':lo[col].median(),
                        col+'_max':lo[col].max(), col+'_most_influential_item':
                        lo.loc[changes.idxmax(),'omitted_item'] if changes.notna().any() else None})
        summaries.append(row)
    return details, pd.DataFrame(summaries)


def core_target_metrics(human, model, target='pooled_equal_year', cfg=None):
    cfg = cfg or analysis()
    items = cfg['primary_items']; countries = sorted(set(human.country)-{DEFAULT})
    h = distribution_array(human,countries,items); loco=loco_array(h)
    he = entropy_array(h,items); rows=[]
    for condition,g in model.groupby('condition'):
        p=distribution_array(g,countries,items); default=distribution_array(g,[DEFAULT],items)
        pe=entropy_array(p,items)
        vals={'js':js_array(h,p), 'default_js':js_array(h,default), 'loco_js':js_array(h,loco),
              'human_entropy':he, 'model_entropy':pe}
        for ci,country in enumerate(countries):
            for ji,item in enumerate(items):
                if not np.isfinite(vals['js'][ci,ji]):continue
                r={'target':target,'condition':condition,'country':country,'item':item,
                   **{k:float(v[ci,ji]) for k,v in vals.items()}}
                r['gain_vs_default']=r['default_js']-r['js'];r['gain_vs_loco']=r['loco_js']-r['js']
                r['entropy_abs_error']=abs(r['human_entropy']-r['model_entropy'])
                rows.append(r)
    frame=pd.DataFrame(rows)
    direction=compute_cultural_deviation_alignment(human,model,cfg)
    frame=frame.merge(direction,on=['condition','country','item'],validate='one_to_one')
    return frame


def core_summary(frame, *, crossed_intervals=False, cfg=None):
    cfg=cfg or analysis(); rows=[]
    for (target,condition),g in frame.groupby(['target','condition']):
        d=direction_summary(g,reps=int(cfg['cultural_direction']['bootstrap_reps']) if crossed_intervals else 0,
                            seed=int(cfg['cultural_direction']['seed']))
        q=fixed_effect_basis(g.country,g.item)
        adjusted=residual_association(g.human_entropy,g.model_entropy,q)
        pooled=residual_association(g.human_entropy,g.model_entropy)
        rows.append({'target':target,'condition':condition,'n_countries':g.country.nunique(),'n_items':g.item.nunique(),
                     'js_mean':g.js.mean(),'default_js_mean':g.default_js.mean(),'gain_vs_default_mean':g.gain_vs_default.mean(),
                     'pct_default_improved':100*g.gain_vs_default.gt(0).sum()/g.gain_vs_default.notna().sum(),
                     'loco_js_mean':g.loco_js.mean(),'gain_vs_loco_mean':g.gain_vs_loco.mean(),
                     'pct_model_beats_loco':100*g.gain_vs_loco.gt(0).sum()/g.gain_vs_loco.notna().sum(),
                     'human_entropy_mean':g.human_entropy.mean(),'model_entropy_mean':g.model_entropy.mean(),
                     'entropy_abs_error_mean':g.entropy_abs_error.mean(), **d,
                     **{'pooled_'+k:float(v) for k,v in pooled.items()},
                     **{'two_way_'+k:float(v) for k,v in adjusted.items()}})
    return pd.DataFrame(rows)


def compute_human_sampling_sensitivity(draws, countries, items, model, point_frame, cfg=None):
    """Propagate respondent-bootstrap references through fixed model predictions.

    Percentile intervals are conditional on countries/items, released weights,
    and the frozen models. They are not substitutes for crossed intervals and
    do not correct errors-in-variables attenuation in entropy regressions.
    """
    cfg=cfg or analysis(); tol=cfg['cultural_direction']; rows=[]
    h_entropy=entropy_array(draws,items)
    country_grid=np.repeat(countries,len(items));item_grid=np.tile(items,len(countries))
    for condition,g in model.groupby('condition'):
        p=distribution_array(g,countries,items);default=distribution_array(g,[DEFAULT],items)
        pe=entropy_array(p,items)
        base=point_frame.loc[point_frame.condition.eq(condition)]
        observed=set(zip(base.country,base.item))
        mask=np.array([(c,j) in observed for c,j in zip(country_grid,item_grid)])
        x=h_entropy.reshape(len(draws),-1)[:,mask].T
        y=pe.reshape(-1)[mask,None]
        q=fixed_effect_basis(country_grid[mask],item_grid[mask])
        adjusted=residual_association(x,y,q);pooled=residual_association(x,y)
        for start in range(0,len(draws),100):
            stop=min(start+100,len(draws));h=draws[start:stop];l=loco_array(h)
            js=js_array(h,p);dj=js_array(h,default);lj=js_array(h,l)
            valid=np.isfinite(js);dg=dj-js
            d=direction_components(h,p,default,l,
                min_human=float(tol['min_human_shift_norm']),min_model=float(tol['min_model_shift_norm']))
            dvalid=np.isfinite(d['direction_correct'])
            def mean(v):
                return np.nanmean(np.where(valid,v,np.nan),axis=(1,2))
            with np.errstate(invalid='ignore',divide='ignore'):
                values={'js_mean':mean(js),'gain_vs_default_mean':mean(dg),'loco_js_mean':mean(lj),
                        'gain_vs_loco_mean':mean(lj-js),
                        'pct_default_improved':100*np.sum(valid&(dg>0),axis=(1,2))/valid.sum(axis=(1,2)),
                        'pct_model_beats_loco':100*np.sum(valid&(lj>js),axis=(1,2))/valid.sum(axis=(1,2)),
                        'human_entropy_mean':mean(h_entropy[start:stop]),
                        'entropy_abs_error_mean':mean(np.abs(h_entropy[start:stop]-pe)),
                        'direction_correct_percent':100*np.nansum(d['direction_correct'],axis=(1,2))/dvalid.sum(axis=(1,2)),
                        'cosine_mean':np.nanmean(d['cosine_similarity'],axis=(1,2)),
                        'projection_pooled':np.nansum(np.where(dvalid,d['dot_product'],np.nan),axis=(1,2))/
                                            np.nansum(np.where(dvalid,d['human_shift_sq'],np.nan),axis=(1,2))}
            for b in range(start,stop):
                rows.append({'condition':condition,'replicate':b,'n_cells':int(valid[b-start].sum()),
                             **{key:float(value[b-start]) for key,value in values.items()},
                             **{'two_way_'+key:float(value[b]) for key,value in adjusted.items()},
                             **{'pooled_'+key:float(value[b]) for key,value in pooled.items()}})
    draw_frame=pd.DataFrame(rows)
    points=core_summary(point_frame,cfg=cfg).set_index('condition')
    intervals=[]
    for condition,g in draw_frame.groupby('condition'):
        for metric in g.columns.difference(['condition','replicate','n_cells']):
            values=g[metric].dropna()
            lo,hi=np.quantile(values,[.025,.975]) if len(values) else (np.nan,np.nan)
            intervals.append({'condition':condition,'metric':metric,'point_estimate':points.loc[condition,metric],
                              'bootstrap_mean':values.mean(),'ci_low':lo,'ci_high':hi,'valid_replicates':len(values),
                              'replicates':len(g),'min_cells':int(g.n_cells.min()),'max_cells':int(g.n_cells.max())})
    return draw_frame,pd.DataFrame(intervals)


def file_hash(path):
    h=sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def run_revision_analyses(*, ivs=None, wvs=None, evs=None, outdir='results', processed='data/processed',
                          cfg=None, skip_human_sampling=False, progress=print):
    """Run all additions without importing or invoking a provider client."""
    cfg=cfg or analysis();outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    processed=Path(processed)
    human=pd.read_csv(processed/'human_country_distributions.csv',float_precision='round_trip')
    human['response']=human.response.astype(str)
    model=pd.read_csv(outdir/'model_mean_probabilities.csv',float_precision='round_trip')
    model['response']=model.response.astype(str)
    models=cfg['primary_model_conditions'];model=model.loc[model.condition.isin(models)].copy()
    metrics=pd.read_csv(outdir/'country_item_metrics.csv',float_precision='round_trip')
    metrics=metrics.loc[metrics.condition.isin(models)]
    manifest={'configuration':{k:cfg[k] for k in ['human_target','human_sampling','cultural_direction','entropy_robustness']},
              'frozen_model_probabilities_sha256':file_hash(outdir/'model_mean_probabilities.csv'),
              'human_primary_sha256':file_hash(processed/'human_country_distributions.csv'),
              'provider_calls':0,'completed':False}
    # Invalidate an earlier successful run before writing any new outputs.
    (outdir/'revision_analysis_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    progress('Computing country-deviation alignment and crossed intervals')
    direction=compute_cultural_deviation_alignment(human,model,cfg)
    direction.to_csv(outdir/'cultural_deviation_alignment.csv',index=False)
    overall,by_item=direction_tables(direction,cfg)
    overall.to_csv(outdir/'cultural_deviation_summary.csv',index=False)
    by_item.to_csv(outdir/'cultural_deviation_by_item.csv',index=False)
    progress('Computing leave-one-item-out entropy diagnostics')
    loio,loio_summary=compute_entropy_leave_one_item_out(metrics)
    loio.to_csv(outdir/'entropy_leave_one_item_out.csv',index=False)
    loio_summary.to_csv(outdir/'entropy_leave_one_item_out_summary.csv',index=False)
    primary=core_target_metrics(human,model,cfg=cfg)
    primary.to_csv(outdir/'revision_primary_core_metrics.csv',index=False)
    reference=metrics.loc[metrics.representation.eq('full'),['condition','country','item','js']]
    check=primary.merge(reference,on=['condition','country','item'],suffixes=('','_archived'),validate='one_to_one')
    if len(check)!=len(reference) or not np.allclose(check.js,check.js_archived,atol=1e-12,rtol=0):
        raise AssertionError('Revision core does not reproduce archived primary JSD')
    sources=[ivs] if ivs else [wvs,evs]
    available=all(s and Path(s).expanduser().is_file() for s in sources)
    manifest['external_human_data_available']=available
    temporal=[core_summary(primary,crossed_intervals=True,cfg=cfg)]
    if available:
        progress('Loading licensed human microdata and constructing temporal targets')
        raw,_=load_ivsd(ivs=ivs,wvs=wvs,evs=evs);df=clean(raw)
        raw_weights=pd.to_numeric(raw.loc[df.index,cfg['weight_variable']],errors='coerce')
        manifest['weight_handling']={'missing_or_nonnumeric_imputed_to_one':int(raw_weights.isna().sum()),
                                     'nonpositive_excluded':int(raw_weights.le(0).sum())}
        del raw
        universe=build_country_universe(df)
        manifest['external_inputs']=[{'filename':Path(s).name,'sha256':file_hash(Path(s).expanduser())} for s in sources]
        manifest['prepared_records']=len(df)
        all_cy,all_diag=[],[]
        for target in [cfg['human_target']['primary'],*cfg['human_target']['sensitivities']]:
            probabilities,cy,diagnostics=human_target_diagnostics(df,target,universe)
            all_cy.append(cy);all_diag.append(diagnostics)
            probabilities.to_csv(outdir/f'human_target_{target}_probabilities.csv',index=False)
            if target==cfg['human_target']['primary']:
                a=probabilities.merge(human,on=['country','item','response'],suffixes=('','_old'),validate='one_to_one')
                if len(a)!=len(human) or not np.allclose(a.p,a.p_old,atol=1e-12,rtol=0):
                    raise AssertionError('Microdata primary target differs from archived benchmark')
            else:
                frame=core_target_metrics(probabilities,model,target,cfg)
                frame.to_csv(outdir/f'temporal_{target}_core_metrics.csv',index=False)
                temporal.append(core_summary(frame,crossed_intervals=True,cfg=cfg))
                # Re-evaluate the pooled target on identical retained cells to
                # separate a target-date change from a coverage change.
                paired=primary.merge(frame[['condition','country','item']],on=['condition','country','item'],validate='one_to_one')
                paired['target']='pooled_matched_'+target
                temporal.append(core_summary(paired,crossed_intervals=True,cfg=cfg))
        pd.concat(all_cy).to_csv(outdir/'human_country_year_sample_sizes.csv',index=False)
        diag=pd.concat(all_diag);diag.to_csv(outdir/'human_sample_size_diagnostics.csv',index=False)
        effective=[]
        base_diag=diag.loc[diag.target.eq(cfg['human_target']['primary'])]
        for cutoff in [0,*cfg['human_sampling']['effective_n_thresholds']]:
            selected=base_diag.loc[base_diag.aggregate_n_eff.ge(cutoff),['country','item']]
            use=primary.merge(selected,on=['country','item'],validate='many_to_one')
            if len(use):
                summary=core_summary(use,cfg=cfg);summary.insert(0,'minimum_aggregate_n_eff',cutoff);effective.append(summary)
        pd.concat(effective).to_csv(outdir/'effective_sample_size_sensitivity.csv',index=False)
        manifest['temporal_targets']='completed';manifest['sample_diagnostics']='completed'
        if not skip_human_sampling:
            opts=cfg['human_sampling'];cache=processed/'human_sampling_bootstrap.npz';meta=cache.with_suffix('.json')
            identity={'inputs':manifest['external_inputs'],'sampling':opts,
                      'human_code_sha256':file_hash(Path(__file__).with_name('human.py')),
                      'analysis_configuration':cfg,
                      'country_configuration_sha256':file_hash('config/countries.yaml'),
                      'questions_sha256':file_hash('config/questions.yaml')}
            if cache.exists() and meta.exists() and json.loads(meta.read_text())==identity:
                progress('Reusing verified aggregate respondent-bootstrap cache')
                with np.load(cache) as saved:
                    draws=saved['probabilities'];countries=saved['countries'].tolist();items=saved['items'].tolist()
            else:
                progress(f"Drawing {opts['bootstrap_reps']} respondent replicates within each country-year")
                draws,countries,items=bootstrap_human_probabilities(df,universe=universe,
                    reps=int(opts['bootstrap_reps']),seed=int(opts['seed']),batch_size=int(opts['batch_size']),progress=progress)
                np.savez_compressed(cache,probabilities=draws,countries=np.array(countries),items=np.array(items))
                meta.write_text(json.dumps(identity,indent=2)+'\n')
            progress('Propagating human sampling variability through JSD, direction, LOCO and entropy')
            draw_frame,intervals=compute_human_sampling_sensitivity(draws,countries,items,model,primary,cfg)
            draw_frame.to_csv(outdir/'human_sampling_bootstrap_draws.csv',index=False)
            intervals.to_csv(outdir/'human_sampling_sensitivity.csv',index=False)
            manifest['human_sampling']='completed'
        else:
            manifest['human_sampling']='skipped_explicitly'
    else:
        manifest['temporal_targets']='skipped_external_microdata_unavailable'
        manifest['sample_diagnostics']='skipped_external_microdata_unavailable'
        manifest['human_sampling']='skipped_external_microdata_unavailable'
        progress('External IVS microdata unavailable: temporal, effective-n and respondent-bootstrap analyses explicitly skipped')
    pd.concat(temporal).to_csv(outdir/'temporal_target_sensitivity.csv',index=False)
    manifest['completed']=True
    (outdir/'revision_analysis_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest
