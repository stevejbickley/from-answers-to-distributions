import numpy as np
import pandas as pd
from src.robustness import option_order_metrics
from src.publication_style import region_lookup
from src.config import country_universe
from src.analyze import _clustered_entropy_regression


def _order_record(rep, included=True, p=.7):
    return dict(provider='openai',condition='test',condition_label='Test',country='A',item='A165',rep=rep,
                probabilities={'1':p,'2':1-p},missing_labels=[] if included else ['B'],
                missing_allowed_mass_upper_bound=0 if included else .2)


def test_excluded_reference_does_not_change_option_order_estimand():
    metrics, coverage=option_order_metrics([_order_record(0,False),_order_record(1),_order_record(2,p=.2)])
    assert metrics.empty
    assert coverage.valid_comparisons.iloc[0]==0
    assert not coverage.reference_retained.iloc[0]


def test_retained_reference_produces_only_valid_comparisons():
    metrics, coverage=option_order_metrics([_order_record(0),_order_record(1,False),_order_record(2,p=.2)])
    assert list(metrics.rep)==[2]
    assert metrics.reference_rep.iloc[0]==0
    assert metrics.js_from_first_order.iloc[0]>0
    assert coverage.valid_comparisons.iloc[0]==1


def test_every_analysis_country_has_sourced_region():
    cfg=country_universe()
    countries={v for k,v in cfg['countries'].items() if k not in cfg['excluded_country_ids']}
    assert countries==set(region_lookup())


def test_failed_fixed_effect_fit_never_returns_pooled_slope(monkeypatch):
    import statsmodels.formula.api as smf
    def fail(*a,**kw): raise ValueError('Invalid design')
    monkeypatch.setattr(smf,'ols',fail)
    data=pd.DataFrame({'human_entropy':[.1,.2,.3],'model_entropy':[.2,.4,.6]})
    out=_clustered_entropy_regression(data,'model_entropy ~ human_entropy + C(item)')
    assert np.isnan(out['slope'])
