import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.analyze import compare
compare('data/processed/human_country_distributions.csv','data/processed/openai_probabilities.jsonl','data/processed/jev_probabilities.jsonl','results')
print('Analysis complete')
