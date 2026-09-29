from pathlib import Path
import pandas as pd
import pytest
from src.config import country_universe
from src.human import build_country_universe, load_analysis_country_targets


def test_frozen_country_universe_counts_and_exclusions():
    cfg = country_universe()
    countries = {int(k): v for k, v in cfg['countries'].items()}
    excluded = {int(x) for x in cfg['excluded_country_ids']}
    assert len(countries) == 112
    assert cfg['expected_pre_exclusion_count'] == 112
    assert cfg['expected_post_exclusion_count'] == 107
    assert excluded == {414, 634, 762, 818, 860}
    assert len(set(countries.values())) == 112


def test_s003_is_canonical_and_s009_aliases_do_not_split_targets():
    df = pd.DataFrame({
        'S003': [826, 826, 909, 909, 818],
        'S009': ['GB', 'GB-GBN', 'NIR', 'GB-NIR', 'EG'],
    })
    u = build_country_universe(df, strict=False)
    assert len(u) == 3
    assert u.loc[u.country_id.eq(826), 'country'].item() == 'United Kingdom'
    assert u.loc[u.country_id.eq(909), 'country'].item() == 'Northern Ireland'
    assert u.loc[u.country_id.eq(826), 'alpha_codes_observed'].item() == 'GB;GB-GBN'
    assert u.loc[u.country_id.eq(909), 'alpha_codes_observed'].item() == 'GB-NIR;NIR'
    assert not bool(u.loc[u.country_id.eq(818), 'included_for_analysis'].item())


def test_target_loader_uses_only_included_rows_and_validates_count(tmp_path):
    p = tmp_path / 'human_country_universe.csv'
    pd.DataFrame({
        'country_id': [1, 2, 3],
        'country': ['A', 'B', 'C'],
        'included_for_analysis': [True, True, False],
    }).to_csv(p, index=False)
    assert load_analysis_country_targets(p, expected_count=2) == ['A', 'B']
    with pytest.raises(ValueError):
        load_analysis_country_targets(p, expected_count=3)


def test_collectors_use_validated_country_universe_not_distribution_name_uniques():
    for rel in [
        'scripts/02_collect_openai.py',
        'scripts/03_collect_jev.py',
        'scripts/07_option_order_robustness.py',
        'scripts/08_jev_native_score.py',
    ]:
        s = Path(rel).read_text(encoding='utf-8')
        assert 'load_analysis_country_targets' in s
        assert 'human_country_universe.csv' in s
