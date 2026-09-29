import numpy as np
import pandas as pd

from src.analyze import population_specificity_metrics, entropy_structure_analysis


def test_population_specificity_positive_when_country_prompt_is_closer(tmp_path):
    cfg={'primary_items':['Q']}
    qs={'Q':{'human_codes':[1,2,3],'response_values':[1,2,3],'ordered':True}}
    human=pd.DataFrame([
        {'country':'A','item':'Q','response':'1','p':.8},{'country':'A','item':'Q','response':'2','p':.1},{'country':'A','item':'Q','response':'3','p':.1},
        {'country':'B','item':'Q','response':'1','p':.1},{'country':'B','item':'Q','response':'2','p':.1},{'country':'B','item':'Q','response':'3','p':.8},
    ])
    rows=[]
    for cond,label in [('gpt4o_anchor','GPT-4o anchor'),('jev','Jev')]:
        for country,p in [('A',[.75,.15,.10]),('B',[.10,.15,.75]),('__DEFAULT__',[.33,.34,.33])]:
            for response,v in zip(['1','2','3'],p):
                rows.append({'provider':'jev' if cond=='jev' else 'openai','condition':cond,'condition_label':label,
                             'country':country,'item':'Q','response':response,'p':v,
                             'allowed_mass':1.0,'missing_count':0,'missing_mass_upper_bound':0.0})
    out=population_specificity_metrics(human,pd.DataFrame(rows),cfg,qs)
    assert (out['gain_vs_default_js']>0).all()


def test_entropy_structure_writes_fixed_effect_diagnostics(tmp_path):
    rows=[]
    for condition,mult in [('gpt4o_anchor',.6),('jev',.05)]:
        for c in range(8):
            for i in range(4):
                h=.2+.05*c+.03*i
                rows.append({'country':f'C{c}','item':f'I{i}','condition':condition,'condition_label':condition,
                             'representation':'full','human_entropy':h,'model_entropy':mult*h+.02*i})
    metrics=pd.DataFrame(rows)
    summary,by_item,by_country=entropy_structure_analysis(metrics,tmp_path)
    assert {'ols_slope','two_way_fe_slope','within_item_pearson_fisher_mean','two_way_resid_sd_ratio'}.issubset(summary.columns)
    assert len(by_item)==8
    assert len(by_country)==16
