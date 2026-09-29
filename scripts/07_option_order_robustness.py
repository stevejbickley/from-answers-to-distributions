import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, random
from dotenv import load_dotenv
from src.config import analysis, questions, models
from src.collect_openai import configured_conditions
from src.prompts import probability_prompt, descriptor, semantic_options
from src.openai_logprobs import get_choice_distribution
from src.jev_client import JevClient
from src.utils import jsonl_append, stable_id
from src.usage_costs import usage_and_cost
from src.human import load_analysis_country_targets
p=argparse.ArgumentParser(); p.add_argument('--universe',default='data/processed/human_country_universe.csv'); p.add_argument('--out',default='data/processed/option_order_robustness.jsonl'); p.add_argument('--n-countries',type=int,default=None); p.add_argument('--reps',type=int,default=None); p.add_argument('--include-terra',action='store_true'); a=p.parse_args()
load_dotenv(); cfg=analysis(); qs=questions(); ocfg=models()['openai']; conditions=configured_conditions(include_optional=a.include_terra)
countries=load_analysis_country_targets(a.universe); rng=random.Random(cfg['random_seed']); n=a.n_countries or cfg.get('option_order_country_sample',12); reps=a.reps or cfg.get('option_order_repetitions',4); countries=rng.sample(countries,min(n,len(countries))); jev=JevClient(); threshold=float(cfg.get('openai_censoring',{}).get('primary_missing_mass_upper_bound',0.001)); temperature=float(ocfg.get('temperature',1.0))
for country in countries:
  for item in cfg['primary_items']:
    base=[k for k,_ in semantic_options(item)]
    for rep in range(reps):
      order=base[:]; rng.shuffle(order)
      for cond,mcfg in conditions:
        prm=probability_prompt(item,0,country,permutation_id=rep,option_order=order)
        ores=get_choice_distribution(prm['system'],prm['user'],prm['label_to_semantic'],model=mcfg['model'],reasoning_effort=mcfg.get('reasoning_effort') or None,top_logprobs=ocfg['top_logprobs'],max_output_tokens=ocfg['max_output_tokens'],temperature=float(mcfg.get('temperature',temperature)),negligible_mass_threshold=threshold)
        orid=stable_id('order',cond,country,item,rep); ouf,ocost=usage_and_cost('openai',ores.model,ores.usage,raw=ores.raw)
        jsonl_append(a.out,{'record_id':orid,'request_id':ores.response_id or orid,'provider':'openai','condition':cond,'condition_label':mcfg.get('label',cond),'country':country,'item':item,'rep':rep,'order':order,'probabilities':ores.probabilities,'allowed_mass':ores.allowed_mass,'allowed_mass_raw':ores.allowed_mass_raw,'residual_probability_mass':ores.residual_probability_mass,'missing_labels':ores.missing_labels,'missing_allowed_mass_upper_bound':ores.missing_allowed_mass_upper_bound,'missing_mass_bound_method':ores.missing_mass_bound_method,'censoring_status':ores.censoring_status,'top_logprobs_requested':ores.top_logprobs_requested,'top_logprobs_returned':ores.top_logprobs_returned,'top_logprob_cutoff_probability':ores.top_logprob_cutoff_probability,'temperature':ores.temperature,'model':ores.model,'usage':ores.usage,'usage_flat':ouf,'cost':ocost,'response_id':ores.response_id})
      by=dict(semantic_options(item)); criteria={k:by[k] for k in order}; jres=jev.choice(descriptor(0,country),item,qs[item]['source_prompt'].split('You can only respond')[0].strip(),criteria)
      jrid=stable_id('order','jev',country,item,rep); juf,jcost=usage_and_cost('jev',jres.model,jres.usage,raw=jres.raw)
      jsonl_append(a.out,{'record_id':jrid,'request_id':(jres.raw.get('id') if isinstance(jres.raw,dict) else None) or jrid,'provider':'jev','condition':'jev','condition_label':'Jev','country':country,'item':item,'rep':rep,'order':order,'probabilities':jres.probabilities,'model':jres.model,'usage':jres.usage,'usage_flat':juf,'cost':jcost})
print('Wrote',a.out)
