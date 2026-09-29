from __future__ import annotations
import math, os, json
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from openai import OpenAI
from .utils import retry_call


@dataclass
class OpenAIProbResult:
    probabilities: dict[str, float]
    raw_allowed_probabilities: dict[str, float]
    allowed_mass: float
    allowed_mass_raw: float
    residual_probability_mass: float
    missing_labels: list[str]
    missing_allowed_mass_upper_bound: float
    missing_mass_bound_method: str
    censoring_status: str
    top_logprobs_requested: int
    top_logprobs_returned: int
    top_logprob_cutoff_probability: float | None
    top_logprob_cutoff_logprob: float | None
    temperature: float
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
    """Tolerant extractor for the first Responses API output-text logprob record."""
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


def classify_topk_censoring(*, allowed_mass: float, missing_count: int,
                            top_probs: list[float], top_logprobs_requested: int,
                            negligible_mass_threshold: float = 1e-3):
    """Conservatively bound omitted permitted-label probability mass.

    A missing allowed label is *not* assigned probability zero.  The total
    omitted permitted-label probability mass is always bounded above by the
    residual vocabulary mass, ``1 - observed_allowed_mass``.  This bound remains
    valid even when the API returns fewer than the requested top-K alternatives.

    The Kth returned token probability is retained as a diagnostic but is *not*
    multiplied by the number of missing semantic labels to form the primary
    bound.  After whitespace normalization, one semantic label can in principle
    correspond to more than one raw token surface form, so that multiplication
    would not be universally conservative.

    The primary analysis uses a prespecified threshold on the residual-mass upper
    bound while keeping complete-only and a stricter threshold as sensitivities.
    """
    allowed_mass = float(max(0.0, min(1.0, allowed_mass)))
    residual = float(max(0.0, 1.0 - allowed_mass))
    missing_count = int(missing_count)
    returned = len(top_probs)

    if missing_count == 0:
        cutoff_p = min(top_probs) if top_probs else None
        cutoff_lp = math.log(cutoff_p) if cutoff_p and cutoff_p > 0 else None
        return {
            'residual_probability_mass': residual,
            'missing_allowed_mass_upper_bound': 0.0,
            'missing_mass_bound_method': 'complete',
            'censoring_status': 'COMPLETE',
            'top_logprobs_returned': returned,
            'top_logprob_cutoff_probability': cutoff_p,
            'top_logprob_cutoff_logprob': cutoff_lp,
        }

    upper = residual
    method = 'residual_vocabulary_mass'
    cutoff_p = None
    cutoff_lp = None
    full_topk = returned >= int(top_logprobs_requested) and returned > 0
    if full_topk:
        cutoff_p = float(min(top_probs))
        cutoff_lp = float(math.log(cutoff_p)) if cutoff_p > 0 else float('-inf')

    if upper <= float(negligible_mass_threshold):
        status = 'TAIL_CENSORED_NEGLIGIBLE'
    elif full_topk:
        status = 'TAIL_CENSORED_NONNEGLIGIBLE'
    else:
        # There is still a valid residual-mass upper bound, but no Kth-token
        # cutoff because the API returned fewer alternatives than requested.
        status = 'INCOMPLETE_NO_TOPK_CUTOFF'

    return {
        'residual_probability_mass': residual,
        'missing_allowed_mass_upper_bound': float(upper),
        'missing_mass_bound_method': method,
        'censoring_status': status,
        'top_logprobs_returned': returned,
        'top_logprob_cutoff_probability': cutoff_p,
        'top_logprob_cutoff_logprob': cutoff_lp,
    }


def get_choice_distribution(system: str, user: str, label_to_semantic: dict[str, str],
                            model: str | None = None, reasoning_effort: str | None = None,
                            top_logprobs: int = 20, max_output_tokens: int = 16,
                            temperature: float = 1.0,
                            negligible_mass_threshold: float = 1e-3,
                            client: 'OpenAI | None' = None, retries: int = 6):
    """Return a controlled next-token distribution over substantive alternatives.

    ``temperature=1`` is deliberate for the probability experiment: it preserves
    the model's unsharpened sampling distribution.  The original point-response
    study used temperature 0 to make a single generated answer deterministic;
    applying temperature 0 here would change/collapse the probability object we
    are trying to measure.  The point representation is therefore derived as the
    argmax of the temperature-1 probability vector, rather than by a second
    stochastic call.
    """
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    if model is None:
        model = os.getenv('OPENAI_PRIMARY_MODEL', 'gpt-5.6-sol')
        if reasoning_effort is None:
            reasoning_effort = os.getenv('OPENAI_PRIMARY_REASONING_EFFORT', 'none')

    def call():
        kwargs = dict(
            model=model,
            input=[
                {'role':'system','content':system},
                {'role':'user','content':user},
            ],
            top_logprobs=int(top_logprobs),
            include=['message.output_text.logprobs'],
            max_output_tokens=max(16, int(max_output_tokens)),
            temperature=float(temperature),
        )
        if reasoning_effort:
            kwargs['reasoning'] = {'effort': reasoning_effort}
        return client.responses.create(**kwargs)

    response = retry_call(call, retries=retries)
    raw = response.model_dump() if hasattr(response, 'model_dump') else _dump(response)
    rec = _find_first_logprob_record(raw)
    if rec is None:
        raise RuntimeError('Could not locate token logprobs in OpenAI response. Save raw response and check API schema/model support.')

    top_candidates = list(rec.get('top_logprobs') or [])
    top_probs = []
    for c in top_candidates:
        try:
            top_probs.append(float(math.exp(float(c['logprob']))))
        except Exception:
            pass

    # For matching labels, also include the emitted token itself in case the API
    # schema did not duplicate it inside top_logprobs.
    candidates = list(top_candidates)
    emitted_raw = str(rec.get('token')) if rec.get('token') is not None else None
    top_raw = {str(c.get('token')) for c in top_candidates if c.get('token') is not None}
    if emitted_raw is not None and rec.get('logprob') is not None and emitted_raw not in top_raw:
        candidates.append({'token':rec['token'], 'logprob':rec['logprob']})

    # Sum distinct raw token surface forms that normalize to the same semantic
    # label (e.g. 'A' and ' A'), rather than taking only the largest one.
    by_label = {}
    seen_raw = set()
    for c in candidates:
        raw_tok = str(c.get('token',''))
        key = (raw_tok, float(c.get('logprob'))) if c.get('logprob') is not None else (raw_tok, None)
        if key in seen_raw:
            continue
        seen_raw.add(key)
        tok = raw_tok.strip()
        if tok in label_to_semantic:
            prob = math.exp(float(c['logprob']))
            by_label[tok] = by_label.get(tok, 0.0) + prob

    missing = [lab for lab in label_to_semantic if lab not in by_label]
    raw_semantic = {label_to_semantic[lab]: by_label.get(lab, 0.0) for lab in label_to_semantic}
    mass_raw = float(sum(raw_semantic.values()))
    if mass_raw <= 0:
        raise RuntimeError('None of the allowed response labels appeared in top_logprobs.')

    # Provider logprobs are finite-precision values. Summing multiple raw token
    # surface forms that normalize to the same semantic labels can therefore
    # produce a tiny numerical overshoot above 1. Preserve the unmodified sum
    # for auditability, but clamp the diagnostic mass used by downstream QC to
    # the probability interval [0, 1]. The conditional semantic distribution is
    # normalized by the raw sum so it still sums to one exactly (up to floating
    # point precision).
    mass = float(max(0.0, min(1.0, mass_raw)))

    # The stored probability vector is the observed allowed-label vector
    # conditional on its observed raw mass. Missing labels remain explicitly
    # recorded and are governed by the conservative tail-mass bound below.
    probs = {k: float(v/mass_raw) for k,v in raw_semantic.items()}

    censor = classify_topk_censoring(
        allowed_mass=mass,
        missing_count=len(missing),
        top_probs=top_probs,
        top_logprobs_requested=int(top_logprobs),
        negligible_mass_threshold=float(negligible_mass_threshold),
    )

    usage = raw.get('usage') or {}
    served_temperature = raw.get('temperature')
    try:
        served_temperature = float(served_temperature)
    except Exception:
        served_temperature = float(temperature)

    return OpenAIProbResult(
        probabilities=probs,
        raw_allowed_probabilities=raw_semantic,
        allowed_mass=mass,
        allowed_mass_raw=mass_raw,
        residual_probability_mass=censor['residual_probability_mass'],
        missing_labels=missing,
        missing_allowed_mass_upper_bound=censor['missing_allowed_mass_upper_bound'],
        missing_mass_bound_method=censor['missing_mass_bound_method'],
        censoring_status=censor['censoring_status'],
        top_logprobs_requested=int(top_logprobs),
        top_logprobs_returned=censor['top_logprobs_returned'],
        top_logprob_cutoff_probability=censor['top_logprob_cutoff_probability'],
        top_logprob_cutoff_logprob=censor['top_logprob_cutoff_logprob'],
        temperature=served_temperature,
        generated_token=str(rec.get('token')).strip() if rec.get('token') is not None else None,
        generated_logprob=float(rec['logprob']) if rec.get('logprob') is not None else None,
        model=str(raw.get('model') or model),
        response_id=raw.get('id'),
        usage=usage,
        raw=raw,
    )
