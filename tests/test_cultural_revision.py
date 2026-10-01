import numpy as np
import pandas as pd
import pytest
from src.cultural_revision import (direction_components, direction_summary, loco_array,
    js_array, compute_entropy_leave_one_item_out, residual_association, fixed_effect_basis)
from src.human import select_human_target, human_target_diagnostics, bootstrap_human_probabilities
from src.config import questions, analysis


@pytest.mark.parametrize('scale',[1.,-1.,.4])
def test_cultural_direction_known_projection(scale):
    h=np.array([[[.6,.3,.1]]]);loco=np.array([[[.4,.3,.3]]]);default=np.array([[[.4,.3,.3]]])
    p=default+scale*(h-loco)
    d=direction_components(h,p,default,loco)
    assert d['projection_coefficient'].item()==pytest.approx(scale)
    assert d['cosine_similarity'].item()==pytest.approx(np.sign(scale))
    assert d['direction_correct'].item()==float(scale>0)


def test_zero_shift_and_tiny_human_shift_are_not_false_cosines():
    h=np.array([[[.6,.4]]]);loco=np.array([[[.5,.5]]]);p=np.array([[[.4,.6]]])
    d=direction_components(h,p,p,loco)
    assert d['direction_correct'].item()==0
    assert d['projection_coefficient'].item()==0
    assert np.isnan(d['cosine_similarity'].item())
    tiny=direction_components(loco+1e-10,p,p+.1,loco)
    assert np.isnan(tiny['direction_correct'].item())
    assert np.isnan(tiny['projection_coefficient'].item())


def test_binary_cosine_and_loco_exclusion():
    h=np.array([[[.2,.8]],[[.4,.6]],[[.9,.1]]])
    loco=loco_array(h)
    assert np.allclose(loco[0,0],[.65,.35])
    d=direction_components(h,h,np.array([[[.5,.5]]]),loco)
    assert np.allclose(np.abs(d['cosine_similarity']),1)
    assert np.allclose(loco_array(np.stack([h,h])),np.stack([loco,loco]))
    assert np.allclose(js_array(h,h),0)


def test_pooled_projection_is_ratio_of_sums_and_bootstrap_reproducible():
    frame=pd.DataFrame({'country':['a','a','b','b'],'item':['x','y','x','y'],
        'direction_correct':[1.,1.,0.,1.],'dot_product':[1.,.01,-.02,2.],
        'human_shift_sq':[1.,.001,.01,2.],'cosine_similarity':[1.,.5,-1.,.7],
        'human_shift_norm':[1.,.03,.1,1.4],'model_shift_norm':[1.,.2,.2,1.5],
        'magnitude_ratio':[1.,6.,2.,1.1]})
    a=direction_summary(frame,reps=50);b=direction_summary(frame,reps=50)
    assert a==b
    assert a['projection_pooled']==pytest.approx(2.99/3.011)
    assert a['direction_correct_percent']==75


def small_human():
    rows=[]
    for cid,country in [(1,'a'),(2,'b')]:
        for year,wave in [(2010,5),(2020,7)]:
            for i in range(8):
                row={'S003':cid,'S020':year,'S002VS':wave,'S017':float(i+1)}
                for item in analysis()['primary_items']:
                    codes=questions()[item]['human_codes'];row[item]=codes[i%len(codes)]
                rows.append(row)
    return pd.DataFrame(rows),pd.DataFrame({'country_id':[1,2],'country':['a','b'],'included_for_analysis':[True,True]})


def test_temporal_selection_and_kish_equal_year_formula():
    frame,u=small_human()
    assert set(select_human_target(frame,'latest_available',u).S020)=={2020}
    assert set(select_human_target(frame,'wave7',u).S002VS)=={7}
    # No fallback to earlier nonmissing items at the latest country year.
    frame.loc[(frame.S003==1)&(frame.S020==2020),'A008']=np.nan
    probs,cy,agg=human_target_diagnostics(frame,'latest_available',u)
    assert probs.loc[(probs.country=='a')&(probs.item=='A008')].empty
    _,cy,agg=human_target_diagnostics(frame,'pooled_equal_year',u)
    expected=36**2/204
    assert np.allclose(cy.kish_n_eff,expected)
    r=agg.loc[(agg.country=='b')&(agg.item=='A008')].iloc[0]
    assert r.aggregate_n_eff==pytest.approx(2*expected)
    assert r.raw_n==16


def test_respondent_bootstrap_preserves_cross_item_dependence():
    frame,u=small_human()
    # Identical binary responses must receive the same draw multiplicities.
    frame['E018']=frame.A165
    a,countries,items=bootstrap_human_probabilities(frame,universe=u,reps=20,seed=42,batch_size=5)
    b,_,_=bootstrap_human_probabilities(frame,universe=u,reps=20,seed=42,batch_size=5)
    assert np.array_equal(a,b)
    assert np.allclose(a.sum(axis=-1),1)
    assert np.allclose(a[:,:,items.index('A165'),:2],a[:,:,items.index('E018'),:2])
    assert np.std(a[:,:,0,0])>0


def test_leave_one_item_out_omits_exactly_one_and_fwl_is_correct():
    rng=np.random.default_rng(8);rows=[]
    for c in range(8):
        for j in range(4):
            x=rng.uniform(.1,.9)
            rows.append({'condition':'test','country':str(c),'item':str(j),'human_entropy':x,
                         'model_entropy':.3*x+.01*c+.02*j,'representation':'full'})
    frame=pd.DataFrame(rows)
    details,summary=compute_entropy_leave_one_item_out(frame)
    assert len(details)==5
    assert set(details.loc[details.omitted_item!='none','n_items'])=={3}
    assert set(details.loc[details.omitted_item!='none','n_cells'])=={24}
    assert np.allclose(details.two_way_slope,.3)
    assert summary.n_omissions.item()==4
    q=fixed_effect_basis(frame.country,frame.item)
    result=residual_association(np.column_stack([frame.human_entropy]*3),frame.model_entropy.to_numpy()[:,None],q)
    assert np.allclose(result['slope'],.3)


def test_missing_microdata_is_explicit_and_new_figures_do_not_use_stale_outputs(tmp_path):
    from src.revision_outputs import completed_manifest
    import json
    with pytest.raises(ValueError,match='Run scripts'):
        completed_manifest(tmp_path)
    p=tmp_path/'revision_analysis_manifest.json'
    p.write_text(json.dumps({'completed':False}))
    with pytest.raises(ValueError,match='not completed'):
        completed_manifest(tmp_path)
    p.write_text(json.dumps({'completed':True,'human_sampling':'skipped_external_microdata_unavailable'}))
    assert completed_manifest(tmp_path)['human_sampling'].startswith('skipped')


def test_array_metrics_match_independent_scalar_implementations():
    from src.metrics import js_divergence
    from src.cultural_revision import entropy_array
    rng=np.random.default_rng(19)
    a=rng.dirichlet(np.ones(4),size=7)[:,None,:]
    b=rng.dirichlet(np.ones(4),size=7)[:,None,:]
    assert np.allclose(js_array(a,b).ravel(),[js_divergence(x[0],y[0]) for x,y in zip(a,b)])
    assert np.allclose(entropy_array(a,['A008']).ravel(),[-np.sum(x*np.log(x))/np.log(4) for x in a[:,0]])


def test_revision_runner_without_licensed_microdata(tmp_path):
    from src.cultural_revision import run_revision_analyses, core_target_metrics
    import copy
    cfg=copy.deepcopy(analysis());cfg['primary_model_conditions']=['test'];cfg['cultural_direction']['bootstrap_reps']=12
    out=tmp_path/'results';out.mkdir();processed=tmp_path/'processed';processed.mkdir()
    rows=[]
    for country in ['a','b','c']:
        for item in cfg['primary_items']:
            codes=questions()[item]['human_codes']
            for k in codes:rows.append({'country':country,'item':item,'response':str(k),'p':1/len(codes)})
    h=pd.DataFrame(rows);h.to_csv(processed/'human_country_distributions.csv',index=False)
    model=pd.concat([h,h[h.country.eq('a')].assign(country='__DEFAULT__')],ignore_index=True).assign(condition='test')
    model.to_csv(out/'model_mean_probabilities.csv',index=False)
    metrics=core_target_metrics(h,model,cfg=cfg).assign(representation='full')
    metrics.to_csv(out/'country_item_metrics.csv',index=False)
    manifest=run_revision_analyses(ivs=tmp_path/'unavailable.csv',outdir=out,processed=processed,cfg=cfg,progress=lambda x:None)
    assert manifest['completed'] and manifest['provider_calls']==0
    assert manifest['human_sampling']=='skipped_external_microdata_unavailable'
    assert manifest['temporal_targets']=='skipped_external_microdata_unavailable'
    assert (out/'entropy_leave_one_item_out.csv').exists()
    assert not (out/'human_sampling_sensitivity.csv').exists()


def test_uniform_respondent_resampling_does_not_apply_weights_twice():
    # Two respondents have weights 1 and 3 and distinct binary responses.
    # Uniform resampling gives probabilities 0, .75, 1 with frequencies .25,
    # .50, .25, hence mean .625. Weight-proportional resampling followed by
    # weighting again would instead yield .84375.
    frame,u=small_human()
    frame=frame.loc[(frame.S003==1)&(frame.S020==2010)].iloc[:2].copy()
    frame['S017']=[1.,3.]
    draws,_,items=bootstrap_human_probabilities(frame,universe=u.iloc[:1],reps=5000,seed=17)
    values=draws[:,0,items.index('A165'),1]
    assert values.mean()==pytest.approx(.625,abs=.02)
    assert set(np.unique(values))=={0.,.75,1.}


def test_completed_manifest_rejects_changed_model_vectors(tmp_path):
    from src.revision_outputs import completed_manifest
    import hashlib,json
    model=tmp_path/'model_mean_probabilities.csv';model.write_text('original')
    manifest={'completed':True,'frozen_model_probabilities_sha256':hashlib.sha256(model.read_bytes()).hexdigest()}
    (tmp_path/'revision_analysis_manifest.json').write_text(json.dumps(manifest))
    model.write_text('changed')
    with pytest.raises(ValueError,match='Model probabilities changed'):
        completed_manifest(tmp_path)
