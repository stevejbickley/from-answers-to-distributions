import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, pandas as pd
from src.collect_openai import collect
p=argparse.ArgumentParser(); p.add_argument('--human',default='data/processed/human_country_distributions.csv'); p.add_argument('--out',default='data/processed/openai_probabilities.jsonl'); a=p.parse_args()
countries=sorted(pd.read_csv(a.human).country.unique()); print('Countries:',len(countries)); collect(countries,a.out)
