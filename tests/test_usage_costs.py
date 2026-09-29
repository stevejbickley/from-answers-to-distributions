from src.usage_costs import flatten_usage, estimate_cost


def test_openai_usage_and_sol_cost_with_cache_components():
    usage={
        'input_tokens':1000,
        'input_tokens_details':{'cached_tokens':200,'cache_write_tokens':100},
        'output_tokens':50,
        'output_tokens_details':{'reasoning_tokens':10},
        'total_tokens':1050,
    }
    f=flatten_usage('openai',usage)
    assert f['ordinary_input_tokens']==700
    assert f['cached_input_tokens']==200
    assert f['cache_write_input_tokens']==100
    assert f['reasoning_output_tokens']==10
    c=estimate_cost('openai','gpt-5.6-sol',usage)
    expected=(700*4 + 200*0.4 + 100*5 + 50*20)/1_000_000
    assert abs(c['estimated_total_cost_usd']-expected)<1e-12


def test_jev_cost_is_input_only():
    usage={'input_tokens':1000,'output_tokens':500}
    c=estimate_cost('jev','jev-1.13.0',usage)
    assert abs(c['estimated_total_cost_usd']-0.000042)<1e-12
    assert c['estimated_output_cost_usd']==0


def test_gpt4o_pricing_match_snapshot():
    c=estimate_cost('openai','gpt-4o-2024-05-13',{'input_tokens':1_000_000,'output_tokens':1_000_000})
    assert abs(c['estimated_total_cost_usd']-12.5)<1e-12
