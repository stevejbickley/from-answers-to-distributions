import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, os
from dotenv import load_dotenv
from src.analyze import compare
from src.cultural_revision import run_revision_analyses

load_dotenv()
p=argparse.ArgumentParser(description='Analyse archived model outputs; no provider calls.')
p.add_argument('--extensions-only',action='store_true',help='Reuse existing primary probability/metric CSVs.')
p.add_argument('--ivs',default=os.getenv('IVS_DATA_PATH'))
p.add_argument('--wvs',default=os.getenv('WVS_DATA_PATH'))
p.add_argument('--evs',default=os.getenv('EVS_DATA_PATH'))
p.add_argument('--skip-human-sampling',action='store_true',help='Explicitly skip respondent resampling, recording this in the manifest.')
a=p.parse_args()
if not a.extensions_only:
    compare('data/processed/human_country_distributions.csv','data/processed/openai_probabilities.jsonl','data/processed/jev_probabilities.jsonl','results')
run_revision_analyses(ivs=a.ivs,wvs=a.wvs,evs=a.evs,skip_human_sampling=a.skip_human_sampling,
                      progress=lambda message:print(message,flush=True))
print('Analysis complete')
