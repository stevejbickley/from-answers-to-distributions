from __future__ import annotations
from pathlib import Path
import json, os, pandas as pd
from dotenv import load_dotenv
from .config import analysis, questions, models
from .prompts import probability_prompt, y003_constituent_prompt
from .openai_logprobs import get_choice_distribution
from .utils import jsonl_append, stable_id, ensure_dir

def collect(countries, outfile='data/processed/openai_probabilities.jsonl', resume=True, include_default=True):
    load_dotenv(); cfg=analysis(); qs=questions(); mcfg=models()['openai']; outfile=Path(outfile); ensure_dir(outfile.parent)
    done=set()
    if resume and outfile.exists():
        for line in outfile.read_text(encoding='utf-8').splitlines():
            try: done.add(json.loads(line)['record_id'])
            except Exception: pass
    targets=list(countries)
    if include_default: targets=[None]+targets
    for country in targets:
        ckey='__DEFAULT__' if country is None else str(country)
        for variant in range(10):
            for item in cfg['primary_items']:
                for label_rep in range(int(cfg.get('openai_label_repetitions',1))):
                    prm=probability_prompt(item,variant,country,permutation_id=label_rep)
                    rid=stable_id('openai',ckey,variant,item,'primary',label_rep)
                    if rid in done: continue
                    res=get_choice_distribution(prm['system'],prm['user'],prm['label_to_semantic'],
                        model=mcfg['model'],reasoning_effort=mcfg['reasoning_effort'],top_logprobs=mcfg['top_logprobs'],
                        max_output_tokens=mcfg['max_output_tokens'],retries=mcfg['retries'])
                    rec={'record_id':rid,'provider':'openai','country':ckey,'variant':variant,'label_rep':label_rep,'item':item,
                         'probabilities':res.probabilities,'raw_allowed_probabilities':res.raw_allowed_probabilities,
                         'allowed_mass':res.allowed_mass,'missing_labels':res.missing_labels,
                         'generated_token':res.generated_token,'model':res.model,'usage':res.usage,
                         'prompt':prm,'response_id':res.response_id}
                    jsonl_append(outfile,rec); done.add(rid)
            for quality in qs['Y003']['constituents']:
                # Binary labels are also rotated (A/B then B/A) across two reps to diagnose label bias.
                for label_rep in range(min(2,int(cfg.get('openai_label_repetitions',1)))):
                    yes,no=('A','B') if label_rep%2==0 else ('B','A')
                    prm=y003_constituent_prompt(quality,variant,country,label_yes=yes,label_no=no)
                    rid=stable_id('openai',ckey,variant,'Y003',quality,label_rep)
                    if rid in done: continue
                    res=get_choice_distribution(prm['system'],prm['user'],prm['label_to_semantic'],
                        model=mcfg['model'],reasoning_effort=mcfg['reasoning_effort'],top_logprobs=mcfg['top_logprobs'],
                        max_output_tokens=mcfg['max_output_tokens'],retries=mcfg['retries'])
                    rec={'record_id':rid,'provider':'openai','country':ckey,'variant':variant,'label_rep':label_rep,'item':'Y003',
                         'quality':quality,'probabilities':res.probabilities,'allowed_mass':res.allowed_mass,
                         'missing_labels':res.missing_labels,'generated_token':res.generated_token,'model':res.model,
                         'usage':res.usage,'prompt':prm,'response_id':res.response_id}
                    jsonl_append(outfile,rec); done.add(rid)
    return outfile
