import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from src.collect_jev import collect
from src.human import load_analysis_country_targets

p = argparse.ArgumentParser(description='Collect Jev decision distributions for the validated source-study country universe.')
p.add_argument('--universe', default='data/processed/human_country_universe.csv',
               help='Validated country-universe file produced by scripts/01_prepare_human.py.')
p.add_argument('--out', default='data/processed/jev_probabilities.jsonl')
a = p.parse_args()

countries = load_analysis_country_targets(a.universe)
print('Countries:', len(countries))
collect(countries, a.out)
