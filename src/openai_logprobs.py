from __future__ import annotations
import math, os, json
from dataclasses import dataclass, asdict
from typing import Any
from openai import OpenAI
from .utils import normalize, retry_call

@dataclass
class OpenAIProbResult:
    probabilities: dict[str, float]
    raw_allowed_probabilities: dict[str, float]
    allowed_mass: float
    missing_labels: list[str]
    generated_token: str | None
    generated_logprob: float | None
    model: str
    response_id: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]


def _dump(x):
    if hasattr(x, 'model_dump'):
        return x.model_dump()
    if isinstance(x, dict):
        return x
    return json.loads(json.dumps(x, default=lambda o: getattr(o, '__dict__', str(o))))


def _find_first_logprob_record(obj):
    """Tolerant extractor for Responses API output text logprobs."""
    if isinstance(obj, dict):
        if 'logprob' in obj and 'token' in obj and 'top_logprobs' in obj:
            return obj
        for v in obj.values():
            r = _find_first_logprob_record(v)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_first_logprob_record(v)
            if r is not None:
                return r
    return None


def get_choice_distribution(system: str, user: str, label_to_semantic: dict[str, str],
                            model: str | None = None, reasoning_effort: str | None = None,
                            top_logprobs: int = 20, max_output_tokens: int = 2,
                            client: OpenAI | None = None, retries: int = 6):
    client = client or OpenAI()
    model = model or os.getenv('OPENAI_MODEL', 'gpt-5.6-terra')
    reasoning_effort = reasoning_effort or os.getenv('OPENAI_REASONING_EFFORT', 'none')
    def call():
        kwargs = dict(
            model=model,
            input=[
                {'role':'system','content':system},
                {'role':'user','content':user},
            ],
            top_logprobs=int(top_logprobs),
            max_output_tokens=int(max_output_tokens),
        )
        # Current GPT-5.6 models support reasoning effort; omit if blank.
        if reasoning_effort:
            kwargs['reasoning'] = {'effort': reasoning_effort}
        return client.responses.create(**kwargs)
    response = retry_call(call, retries=retries)
    raw = response.model_dump() if hasattr(response, 'model_dump') else _dump(response)
    rec = _find_first_logprob_record(raw)
    if rec is None:
        raise RuntimeError('Could not locate token logprobs in OpenAI response. Save raw response and check API schema/model support.')
    candidates = list(rec.get('top_logprobs') or [])
    # Ensure the emitted token itself is represented.
    if rec.get('token') is not None and rec.get('logprob') is not None:
        candidates.append({'token':rec['token'], 'logprob':rec['logprob']})
    by_label = {}
    for c in candidates:
        tok = str(c.get('token','')).strip()
        if tok in label_to_semantic:
            p = math.exp(float(c['logprob']))
            by_label[tok] = max(by_label.get(tok, 0.0), p)
    missing = [lab for lab in label_to_semantic if lab not in by_label]
    raw_semantic = {label_to_semantic[lab]: by_label.get(lab, 0.0) for lab in label_to_semantic}
    mass = float(sum(raw_semantic.values()))
    if mass <= 0:
        raise RuntimeError('None of the allowed response labels appeared in top_logprobs.')
    probs = {k: float(v/mass) for k,v in raw_semantic.items()}
    usage = raw.get('usage') or {}
    return OpenAIProbResult(
        probabilities=probs,
        raw_allowed_probabilities=raw_semantic,
        allowed_mass=mass,
        missing_labels=missing,
        generated_token=str(rec.get('token')).strip() if rec.get('token') is not None else None,
        generated_logprob=float(rec['logprob']) if rec.get('logprob') is not None else None,
        model=str(raw.get('model') or model),
        response_id=raw.get('id'),
        usage=usage,
        raw=raw,
    )
