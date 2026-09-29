import math
from src.openai_logprobs import classify_topk_censoring
from src.config import models, analysis


def test_complete_vector_is_complete():
    d=classify_topk_censoring(allowed_mass=.91,missing_count=0,top_probs=[.5,.2,.1],top_logprobs_requested=3)
    assert d['censoring_status']=='COMPLETE'
    assert d['missing_allowed_mass_upper_bound']==0


def test_missing_tail_uses_conservative_residual_mass_bound():
    # The residual vocabulary mass is always a valid semantic-label upper bound.
    # The Kth-token probability is diagnostic only because whitespace-normalized
    # semantic labels can have multiple raw token surface forms.
    d=classify_topk_censoring(allowed_mass=.80,missing_count=2,top_probs=[.5,.2,.09,.01],top_logprobs_requested=4,negligible_mass_threshold=.001)
    assert math.isclose(d['missing_allowed_mass_upper_bound'],.20,rel_tol=1e-12)
    assert math.isclose(d['top_logprob_cutoff_probability'],.01,rel_tol=1e-12)
    assert d['censoring_status']=='TAIL_CENSORED_NONNEGLIGIBLE'


def test_decisive_missing_label_can_be_negligible_from_residual_mass():
    d=classify_topk_censoring(allowed_mass=.99995,missing_count=1,top_probs=[.99995],top_logprobs_requested=20,negligible_mass_threshold=.001)
    assert d['missing_allowed_mass_upper_bound'] <= .000051
    assert d['censoring_status']=='TAIL_CENSORED_NEGLIGIBLE'


def test_incomplete_topk_without_small_residual_is_flagged():
    d=classify_topk_censoring(allowed_mass=.8,missing_count=1,top_probs=[.7,.1],top_logprobs_requested=20,negligible_mass_threshold=.001)
    assert d['censoring_status']=='INCOMPLETE_NO_TOPK_CUTOFF'


def test_probability_extraction_temperature_is_explicitly_one():
    assert float(models()['openai']['temperature']) == 1.0
    c=analysis()['openai_censoring']
    assert float(c['primary_missing_mass_upper_bound']) == .001
    assert float(c['strict_missing_mass_upper_bound']) == .0001

class _FakeResponses:
    def __init__(self):
        self.kwargs=None
    def create(self, **kwargs):
        self.kwargs=kwargs
        class R:
            def model_dump(self_non):
                return {
                    'id':'resp_test','model':'fake-model','temperature':kwargs.get('temperature'),
                    'usage':{'input_tokens':10,'output_tokens':1,'total_tokens':11},
                    'output':[{'type':'message','content':[{'type':'output_text','text':'A','logprobs':[
                        {'token':'A','logprob':math.log(.60),'top_logprobs':[
                            {'token':'A','logprob':math.log(.60)},
                            {'token':' A','logprob':math.log(.20)},
                            {'token':'X','logprob':math.log(.10)},
                        ]}
                    ]}]}]
                }
        return R()

class _FakeClient:
    def __init__(self): self.responses=_FakeResponses()


def test_get_choice_distribution_sums_surface_forms_and_passes_temperature():
    from src.openai_logprobs import get_choice_distribution
    c=_FakeClient()
    r=get_choice_distribution('sys','user',{'A':'yes','B':'no'},model='fake-model',client=c,
                              top_logprobs=3,temperature=1.0,retries=1)
    assert c.responses.kwargs['temperature']==1.0
    assert c.responses.kwargs['max_output_tokens']>=16
    assert math.isclose(r.raw_allowed_probabilities['yes'],.80,rel_tol=1e-12)
    assert r.raw_allowed_probabilities['no']==0
    assert math.isclose(r.allowed_mass,.80,rel_tol=1e-12)
    assert math.isclose(r.missing_allowed_mass_upper_bound,.20,rel_tol=1e-12)


class _OvershootResponses:
    def create(self, **kwargs):
        class R:
            def model_dump(self_non):
                return {
                    "id":"resp_overshoot","model":"fake-model","temperature":kwargs.get("temperature"),
                    "usage":{"input_tokens":10,"output_tokens":1,"total_tokens":11},
                    "output":[{"type":"message","content":[{"type":"output_text","text":"A","logprobs":[
                        {"token":"A","logprob":math.log(.600006),"top_logprobs":[
                            {"token":"A","logprob":math.log(.600006)},
                            {"token":"B","logprob":math.log(.400006)},
                        ]}
                    ]}]}]
                }
        return R()


class _OvershootClient:
    def __init__(self):
        self.responses=_OvershootResponses()


def test_allowed_mass_is_clamped_but_raw_overshoot_is_preserved():
    from src.openai_logprobs import get_choice_distribution
    r=get_choice_distribution(
        "sys","user",{"A":"yes","B":"no"},model="fake-model",
        client=_OvershootClient(),top_logprobs=2,temperature=1.0,retries=1
    )
    assert r.allowed_mass == 1.0
    assert r.allowed_mass_raw > 1.0
    assert math.isclose(r.allowed_mass_raw,1.000012,rel_tol=1e-12)
    assert r.residual_probability_mass == 0.0
    assert r.missing_allowed_mass_upper_bound == 0.0
    assert math.isclose(sum(r.probabilities.values()),1.0,rel_tol=1e-12)
