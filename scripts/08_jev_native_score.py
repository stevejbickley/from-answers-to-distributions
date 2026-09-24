import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse,json,pandas as pd
from dotenv import load_dotenv
from src.config import analysis,questions
from src.prompts import descriptor,semantic_options
from src.jev_client import JevClient
from src.utils import jsonl_append,stable_id

p=argparse.ArgumentParser(); p.add_argument('--human',default='data/processed/human_country_distributions.csv'); p.add_argument('--out',default='data/processed/jev_native_score.jsonl'); a=p.parse_args(); load_dotenv()
ordered=['A008','E018','E025','F063','F118','F120','G006']
countries=sorted(pd.read_csv(a.human).country.unique()); qs=questions(); client=JevClient()
for country in countries:
  for variant in range(10):
    state=descriptor(variant,country)
    for item in ordered:
      opts=semantic_options(item); criteria=[desc for _,desc in opts]
      res=client.score(state,item,qs[item]['source_prompt'].split('You can only respond')[0].strip(),criteria)
      # Score levels are zero-indexed positions; map back to substantive response keys.
      probs={str(opts[int(k)][0]):v for k,v in res.probabilities.items()}
      jsonl_append(a.out,{'record_id':stable_id('jevscore',country,variant,item),'provider':'jev_score','country':country,'variant':variant,'item':item,'probabilities':probs,'model':res.model,'usage':res.usage})
print('Wrote',a.out)
