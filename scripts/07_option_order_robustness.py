import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, json, random, pandas as pd
from dotenv import load_dotenv
from src.config import analysis, questions, models
from src.prompts import probability_prompt, descriptor, semantic_options
from src.openai_logprobs import get_choice_distribution
from src.jev_client import JevClient
from src.utils import jsonl_append, stable_id

p=argparse.ArgumentParser()
p.add_argument('--human',default='data/processed/human_country_distributions.csv')
p.add_argument('--out',default='data/processed/option_order_robustness.jsonl')
p.add_argument('--n-countries',type=int,default=None)
p.add_argument('--reps',type=int,default=None)
a=p.parse_args(); load_dotenv(); cfg=analysis(); qs=questions(); mcfg=models()['openai']
countries=sorted(pd.read_csv(a.human).country.unique())
rng=random.Random(cfg['random_seed']); n=a.n_countries or cfg.get('option_order_country_sample',12); reps=a.reps or cfg.get('option_order_repetitions',4)
countries=rng.sample(countries,min(n,len(countries)))
jev=JevClient()
for country in countries:
  for item in cfg['primary_items']:
    base=[k for k,_ in semantic_options(item)]
    for rep in range(reps):
      order=base[:]; rng.shuffle(order)
      prm=probability_prompt(item,0,country,permutation_id=rep,option_order=order)
      ores=get_choice_distribution(prm['system'],prm['user'],prm['label_to_semantic'],model=mcfg['model'],reasoning_effort=mcfg['reasoning_effort'],top_logprobs=mcfg['top_logprobs'],max_output_tokens=mcfg['max_output_tokens'])
      jsonl_append(a.out,{'record_id':stable_id('order','openai',country,item,rep),'provider':'openai','country':country,'item':item,'rep':rep,'order':order,'probabilities':ores.probabilities,'allowed_mass':ores.allowed_mass,'missing_labels':ores.missing_labels})
      by=dict(semantic_options(item)); criteria={k:by[k] for k in order}
      jres=jev.choice(descriptor(0,country),item,qs[item]['source_prompt'].split('You can only respond')[0].strip(),criteria)
      jsonl_append(a.out,{'record_id':stable_id('order','jev',country,item,rep),'provider':'jev','country':country,'item':item,'rep':rep,'order':order,'probabilities':jres.probabilities})
print('Wrote',a.out)
