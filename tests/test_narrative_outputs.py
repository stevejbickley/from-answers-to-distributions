from __future__ import annotations
import json
import numpy as np
import pandas as pd

from src.config import analysis, questions
from src.analyze import make_cultural_map_outputs


def _dist_rows(country, provider, condition, label, variant=None):
    qs=questions(); rows=[]
    for item in analysis()['primary_items']:
        code=str(qs[item]['human_codes'][0])
        row={'provider':provider,'condition':condition,'condition_label':label,
             'country':country,'item':item,'response':code,'p':1.0}
        if variant is not None: row['variant']=variant
        rows.append(row)
    return rows


def test_tao_style_map_outputs_are_reconstructed_without_new_calls(tmp_path):
    qs=questions(); items=analysis()['cultural_map_items']
    human=[]
    for country in ['A','B']:
        for item in analysis()['primary_items']:
            human.append({'country':country,'item':item,'response':str(qs[item]['human_codes'][0]),'p':1.0})
    human=pd.DataFrame(human)

    avg=[]; model=[]
    for country in ['__DEFAULT__','A','B']:
        avg += _dist_rows(country,'openai','gpt4o_anchor','GPT-4o anchor')
        for variant in [0,1]:
            model += _dist_rows(country,'openai','gpt4o_anchor','GPT-4o anchor',variant=variant)
    avg=pd.DataFrame(avg)
    avg['allowed_mass']=1.0; avg['missing_count']=0.0; avg['missing_mass_upper_bound']=0.0
    model=pd.DataFrame(model)
    model['allowed_mass']=1.0; model['missing_count']=0.0; model['missing_mass_upper_bound']=0.0

    qualities=list(qs['Y003']['constituents'])
    y3=[]
    for country in ['__DEFAULT__','A','B']:
        for variant in [0,1]:
            for q in qualities:
                y3.append({'provider':'openai','condition':'gpt4o_anchor','condition_label':'GPT-4o anchor',
                           'country':country,'variant':variant,'label_rep':0,'quality':q,'p_selected':0.6,
                           'allowed_mass':1.0,'missing_count':0,'missing_mass_upper_bound':0.0})
    y3=pd.DataFrame(y3)

    yh=[]
    for country in ['A','B']:
        for q in qualities:
            yh.append({'country':country,'quality':q,'p_selected':0.5})
    ypath=tmp_path/'human_y003_country_marginals.csv'; pd.DataFrame(yh).to_csv(ypath,index=False)

    # Minimal valid projection model. The exact coordinates are immaterial here;
    # the test verifies the reconstruction and prompting-distance pipeline.
    pca={'items':items,'means':{x:0.0 for x in items},'sds':{x:1.0 for x in items},
         'score_coef':np.zeros((len(items),2)).tolist()}
    ppath=tmp_path/'pca.json'; ppath.write_text(json.dumps(pca))

    make_cultural_map_outputs(human,avg,model,y3,ypath,ppath,tmp_path)
    coords=pd.read_csv(tmp_path/'cultural_map_coordinates.csv')
    assert 'tao_modal' in set(coords.representation)
    prompt=pd.read_csv(tmp_path/'cultural_map_prompting_summary.csv')
    exp=prompt[(prompt.condition=='gpt4o_anchor')&(prompt.representation=='expected')]
    assert len(exp)==1
    assert int(exp.n_countries.iloc[0])==2
    assert np.isfinite(float(exp.unconditioned_distance_mean.iloc[0]))
