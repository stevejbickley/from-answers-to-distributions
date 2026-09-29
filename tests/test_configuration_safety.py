from pathlib import Path

def test_openai_requests_explicitly_include_logprobs():
    s=Path('src/openai_logprobs.py').read_text()
    assert "include=['message.output_text.logprobs']" in s

def test_repo_ignores_secrets_and_human_microdata():
    s=Path('.gitignore').read_text()
    assert '.env' in s
    assert 'data/raw/**' in s
    assert 'data/processed/**' in s

def test_external_data_env_is_documented():
    s=Path('.env').read_text()
    assert 'IVS_DATA_PATH=' in s


def test_human_preparation_writes_path_free_provenance():
    s=Path('scripts/01_prepare_human.py').read_text()
    assert 'human_input_provenance.json' in s
    assert "'filename':p.name" in s
    assert "'sha256':h.hexdigest()" in s

def test_explicit_older_model_does_not_inherit_reasoning_setting():
    s=Path('src/openai_logprobs.py').read_text()
    assert 'if model is None:' in s
    assert "OPENAI_PRIMARY_REASONING_EFFORT" in s
