import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, os
from dotenv import load_dotenv
from src.config import models, analysis
from src.collect_openai import configured_conditions

load_dotenv()
p=argparse.ArgumentParser(description='Validate configuration; --live makes minimal capability requests to each selected API model condition.')
p.add_argument('--live', action='store_true')
p.add_argument('--include-terra', action='store_true')
a=p.parse_args()

print('Python:',sys.version)
openai_key=os.getenv('OPENAI_API_KEY')
jev_key=os.getenv('TYPESAFE_API_KEY') or os.getenv('JEV_API_KEY')
print('OPENAI_API_KEY', 'set' if openai_key else 'NOT SET')
print('TYPESAFE_API_KEY/JEV_API_KEY', 'set' if jev_key else 'NOT SET')
for name in ['IVS_DATA_PATH','WVS_DATA_PATH','EVS_DATA_PATH']:
    v=os.getenv(name)
    if v:
        path=Path(v).expanduser(); print(name, str(path), 'OK' if path.exists() else 'NOT FOUND')
for path in ['config/questions.yaml','config/prompt_variants.yaml','config/analysis.yaml','config/models.yaml']:
    assert Path(path).exists(),path
print('Configuration files OK')
mcfg=models(); ocfg=mcfg['openai']; acfg=analysis(); threshold=float(acfg.get('openai_censoring',{}).get('primary_missing_mass_upper_bound',0.001))
conds=configured_conditions(include_optional=a.include_terra)
for name,cfg in conds:
    print('OpenAI condition:',name,'model=',cfg['model'],'reasoning=',cfg.get('reasoning_effort') or 'n/a','temperature=',cfg.get('temperature',ocfg.get('temperature',1.0)))
print('Jev model:',mcfg['jev'].get('model') or '(discover at runtime)')

if a.live:
    if not openai_key or not jev_key: raise SystemExit('Both API keys are required for --live.')
    from src.openai_logprobs import get_choice_distribution
    from src.jev_client import JevClient

    balanced_user=(
        'A fair coin has been flipped once, but the outcome is hidden and no information about it is available.\n'
        'A = Heads\nB = Tails\n'
        'Both outcomes are equally plausible before observing the result. Return exactly A or B.'
    )
    lopsided_user='Choose the first option.\nA = first\nB = second\nReturn exactly A or B.'

    for name,cfg in conds:
        temp=float(cfg.get('temperature',ocfg.get('temperature',1.0)))
        print(f'Testing OpenAI {name} ({cfg["model"]}) logprobs at temperature={temp}...')
        for test_name,user in [('balanced',balanced_user),('lopsided-tail',lopsided_user)]:
            r=get_choice_distribution(
                'Return the requested label only.',user,{'A':'first','B':'second'},
                model=cfg['model'],reasoning_effort=cfg.get('reasoning_effort') or None,
                top_logprobs=ocfg.get('top_logprobs',20),max_output_tokens=ocfg.get('max_output_tokens',16),
                temperature=temp,negligible_mass_threshold=threshold,retries=1)
            print(' ',test_name,
                  'served_model=',r.model,
                  'allowed_mass=',f'{r.allowed_mass:.12g}',
                  'allowed_mass_raw=',f'{r.allowed_mass_raw:.12g}',
                  'missing=',r.missing_labels,
                  'missing_mass_ub=',f'{r.missing_allowed_mass_upper_bound:.3g}',
                  'status=',r.censoring_status,
                  'topk=',f'{r.top_logprobs_returned}/{r.top_logprobs_requested}')
            if r.censoring_status in {'TAIL_CENSORED_NONNEGLIGIBLE','INCOMPLETE_NO_TOPK_CUTOFF'}:
                print('   WARNING: this test would be excluded from the primary analysis under the configured censoring threshold.')

    print('Testing Jev model access...')
    jc=JevClient(retries=1); jm=jc.models(); print('  Jev models:',[x.get('name') for x in jm.get('models',[])])
    jr=jc.choice('A simple test state.','q','Which option best matches the state?',{'match':'Matches','other':'Does not match'})
    print('  Jev systemone OK:',jr.model,jr.probabilities)
