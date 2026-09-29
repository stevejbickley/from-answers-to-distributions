import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from src.collect_openai import collect
from src.human import load_analysis_country_targets

p = argparse.ArgumentParser(description='Collect full next-token distributions for configured OpenAI model conditions.')
p.add_argument('--universe', default='data/processed/human_country_universe.csv',
               help='Validated country-universe file produced by scripts/01_prepare_human.py.')
p.add_argument('--out', default='data/processed/openai_probabilities.jsonl')
p.add_argument('--include-terra', action='store_true', help='Also collect the optional GPT-5.6 Terra robustness condition.')
p.add_argument('--condition', action='append', dest='conditions', help='Run only a named OpenAI condition; repeat as needed.')
a = p.parse_args()

countries = load_analysis_country_targets(a.universe)
print('Countries:', len(countries))
collect(countries, a.out, include_optional=a.include_terra, condition_names=a.conditions)
