import pandas as pd
from src.analyze import crossed_bootstrap_contrast

def test_pairwise_contrast_uses_condition_not_provider():
    rows=[]
    for c in ['A','B','C']:
        for item in ['x','y']:
            rows += [
                {'country':c,'item':item,'condition':'gpt56_sol','representation':'full','js':0.30},
                {'country':c,'item':item,'condition':'jev','representation':'full','js':0.20},
                {'country':c,'item':item,'condition':'gpt4o_anchor','representation':'full','js':0.40},
            ]
    out=crossed_bootstrap_contrast(pd.DataFrame(rows),'gpt56_sol','jev',reps=100,seed=1)
    assert out is not None
    assert abs(out['mean_error_a_minus_b']-0.10)<1e-9
