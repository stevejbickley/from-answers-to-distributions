from src.config import models, analysis

def test_primary_model_conditions_are_anchor_sol_and_jev():
    m=models()['openai']['conditions']
    assert m['gpt4o_anchor']['model']
    assert m['gpt56_sol']['model'] == 'gpt-5.6-sol'
    assert m['gpt56_sol']['reasoning_effort'] == 'none'
    assert m['gpt56_terra']['enabled'] is False
    assert analysis()['primary_model_conditions'] == ['gpt4o_anchor','gpt56_sol','jev']

def test_default_flags_select_anchor_and_sol_not_terra():
    m=models()['openai']['conditions']
    enabled=[k for k,v in m.items() if v.get('enabled')]
    assert enabled == ['gpt4o_anchor','gpt56_sol']

def test_openai_probability_temperature_is_native_scale():
    assert float(models()['openai']['temperature']) == 1.0
