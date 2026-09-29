from __future__ import annotations
from pathlib import Path
import json
from dotenv import load_dotenv
from .config import analysis, questions, models
from .prompts import probability_prompt, y003_constituent_prompt
from .openai_logprobs import get_choice_distribution
from .utils import jsonl_append, stable_id, ensure_dir
from .usage_costs import usage_and_cost


def configured_conditions(include_optional: bool = False, condition_names: list[str] | None = None):
    cfg = models()['openai']
    out = []
    wanted = set(condition_names or [])
    for name, mc in cfg.get('conditions', {}).items():
        if wanted:
            use = name in wanted
        else:
            use = bool(mc.get('enabled', False)) or (include_optional and mc.get('role') == 'contemporary_robustness')
        if use:
            out.append((name, mc))
    if not out:
        raise ValueError('No OpenAI model conditions selected.')
    return out


def _diagnostic_fields(res):
    return {
        'raw_allowed_probabilities': res.raw_allowed_probabilities,
        'allowed_mass': res.allowed_mass,
        'allowed_mass_raw': res.allowed_mass_raw,
        'residual_probability_mass': res.residual_probability_mass,
        'missing_labels': res.missing_labels,
        'missing_allowed_mass_upper_bound': res.missing_allowed_mass_upper_bound,
        'missing_mass_bound_method': res.missing_mass_bound_method,
        'censoring_status': res.censoring_status,
        'top_logprobs_requested': res.top_logprobs_requested,
        'top_logprobs_returned': res.top_logprobs_returned,
        'top_logprob_cutoff_probability': res.top_logprob_cutoff_probability,
        'top_logprob_cutoff_logprob': res.top_logprob_cutoff_logprob,
        'temperature': res.temperature,
        'generated_token': res.generated_token,
    }


def collect(countries, outfile='data/processed/openai_probabilities.jsonl', resume=True,
            include_default=True, include_optional=False, condition_names=None):
    load_dotenv(); cfg=analysis(); qs=questions(); ocfg=models()['openai']; outfile=Path(outfile); ensure_dir(outfile.parent)
    censor_cfg=cfg.get('openai_censoring',{})
    threshold=float(censor_cfg.get('primary_missing_mass_upper_bound',0.001))
    temperature=float(ocfg.get('temperature',1.0))
    done=set()
    if resume and outfile.exists():
        for line in outfile.read_text(encoding='utf-8').splitlines():
            try: done.add(json.loads(line)['record_id'])
            except Exception: pass
    targets=list(countries)
    if include_default: targets=[None]+targets
    conditions=configured_conditions(include_optional=include_optional, condition_names=condition_names)
    for condition, mcfg in conditions:
        model_id=mcfg['model']; reasoning=mcfg.get('reasoning_effort') or None
        model_temperature=float(mcfg.get('temperature',temperature))
        print(f'Collecting OpenAI condition={condition} model={model_id} temperature={model_temperature}')
        for country in targets:
            ckey='__DEFAULT__' if country is None else str(country)
            for variant in range(10):
                for item in cfg['primary_items']:
                    for label_rep in range(int(cfg.get('openai_label_repetitions',1))):
                        prm=probability_prompt(item,variant,country,permutation_id=label_rep)
                        rid=stable_id('openai',condition,ckey,variant,item,'primary',label_rep)
                        if rid in done: continue
                        res=get_choice_distribution(
                            prm['system'],prm['user'],prm['label_to_semantic'],
                            model=model_id,reasoning_effort=reasoning,
                            top_logprobs=ocfg['top_logprobs'],max_output_tokens=ocfg['max_output_tokens'],
                            temperature=model_temperature,negligible_mass_threshold=threshold,retries=ocfg['retries'])
                        usage_flat,cost=usage_and_cost('openai',res.model,res.usage,raw=res.raw)
                        reqid=res.response_id or rid
                        rec={'record_id':rid,'request_id':reqid,'provider':'openai','condition':condition,'condition_label':mcfg.get('label',condition),
                             'condition_role':mcfg.get('role'),'requested_model':model_id,'country':ckey,'variant':variant,
                             'label_rep':label_rep,'item':item,'probabilities':res.probabilities,
                             **_diagnostic_fields(res),'model':res.model,
                             'usage':res.usage,'usage_flat':usage_flat,'cost':cost,'prompt':prm,'response_id':res.response_id}
                        jsonl_append(outfile,rec); done.add(rid)
                for quality in qs['Y003']['constituents']:
                    for label_rep in range(min(2,int(cfg.get('openai_label_repetitions',1)))):
                        yes,no=('A','B') if label_rep%2==0 else ('B','A')
                        prm=y003_constituent_prompt(quality,variant,country,label_yes=yes,label_no=no)
                        rid=stable_id('openai',condition,ckey,variant,'Y003',quality,label_rep)
                        if rid in done: continue
                        res=get_choice_distribution(
                            prm['system'],prm['user'],prm['label_to_semantic'],
                            model=model_id,reasoning_effort=reasoning,
                            top_logprobs=ocfg['top_logprobs'],max_output_tokens=ocfg['max_output_tokens'],
                            temperature=model_temperature,negligible_mass_threshold=threshold,retries=ocfg['retries'])
                        usage_flat,cost=usage_and_cost('openai',res.model,res.usage,raw=res.raw)
                        reqid=res.response_id or rid
                        rec={'record_id':rid,'request_id':reqid,'provider':'openai','condition':condition,'condition_label':mcfg.get('label',condition),
                             'condition_role':mcfg.get('role'),'requested_model':model_id,'country':ckey,'variant':variant,
                             'label_rep':label_rep,'item':'Y003','quality':quality,'probabilities':res.probabilities,
                             **_diagnostic_fields(res),'model':res.model,
                             'usage':res.usage,'usage_flat':usage_flat,'cost':cost,'prompt':prm,'response_id':res.response_id}
                        jsonl_append(outfile,rec); done.add(rid)
    return outfile
