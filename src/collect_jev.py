from __future__ import annotations
from pathlib import Path
import json
from dotenv import load_dotenv
from .config import analysis, questions
from .prompts import descriptor, semantic_options, y002_pairs
from .jev_client import JevClient
from .utils import stable_id, jsonl_append, ensure_dir

def _stem(item):
    return questions()[item]['source_prompt'].split('You can only respond')[0].strip()

def collect(countries, outfile='data/processed/jev_probabilities.jsonl', resume=True, include_default=True):
    load_dotenv(); cfg=analysis(); qs=questions(); out=Path(outfile); ensure_dir(out.parent); client=JevClient()
    done=set()
    if resume and out.exists():
        for line in out.read_text(encoding='utf-8').splitlines():
            try: done.add(json.loads(line)['record_id'])
            except Exception: pass
    targets=list(countries)
    if include_default: targets=[None]+targets
    for country in targets:
        ckey='__DEFAULT__' if country is None else str(country)
        for variant in range(10):
            state=descriptor(variant,country)
            for item in cfg['primary_items']:
                rid=stable_id('jev',ckey,variant,item,'primary')
                if rid in done: continue
                criteria={semantic:desc for semantic,desc in semantic_options(item)}
                res=client.choice(state,item,_stem(item),criteria)
                rec={'record_id':rid,'provider':'jev','country':ckey,'variant':variant,'label_rep':0,'item':item,
                     'probabilities':res.probabilities,'model':res.model,'usage':res.usage,
                     'question':{'state':state,'instructions':_stem(item),'criteria':criteria}}
                jsonl_append(out,rec); done.add(rid)
            qmap={}
            for quality in qs['Y003']['constituents']:
                qid='y003_'+qs['Y003']['constituents'][quality].lower()
                qmap[qid]=(quality,_stem('Y003') + f' Considering the same instruction to choose up to five qualities, would you include "{quality}" among your choices?')
            pending=[(qid,x) for qid,x in qmap.items() if stable_id('jev',ckey,variant,'Y003',x[0]) not in done]
            if pending:
                raw=client.noul_batch(state,{qid:instr for qid,(quality,instr) in pending})
                for qid,(quality,instr) in pending:
                    ans=raw['answers'][qid]; py=float(ans['noul']); py=min(1.0,max(0.0,py))
                    rid=stable_id('jev',ckey,variant,'Y003',quality)
                    rec={'record_id':rid,'provider':'jev','country':ckey,'variant':variant,'label_rep':0,'item':'Y003','quality':quality,
                         'probabilities':{'1':py,'0':1-py},'model':raw.get('model'),'usage':raw.get('usage') or {},
                         'question':{'state':state,'instructions':instr,'type':'noul'}}
                    jsonl_append(out,rec); done.add(rid)
    return out
