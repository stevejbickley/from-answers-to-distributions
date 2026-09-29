from __future__ import annotations
from pathlib import Path
from typing import Any
import math
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _num(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        y = float(x)
        return y if math.isfinite(y) else default
    except Exception:
        return default


def _int(x: Any, default: int = 0) -> int:
    return int(round(_num(x, default)))


def pricing_config(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path) if path else ROOT / 'config' / 'pricing.yaml'
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def flatten_usage(provider: str, usage: dict[str, Any] | None) -> dict[str, int]:
    """Normalize provider-returned usage without discarding the original usage object.

    OpenAI Responses currently reports input_tokens/output_tokens with nested
    input_tokens_details and output_tokens_details. Jev reports input_tokens and
    output_tokens. Unknown/missing fields are left at zero; raw usage remains in
    the source record for forward compatibility.
    """
    usage = usage or {}
    provider = str(provider or '').lower()
    ind = usage.get('input_tokens_details') or usage.get('prompt_tokens_details') or {}
    outd = usage.get('output_tokens_details') or usage.get('completion_tokens_details') or {}

    input_tokens = _int(usage.get('input_tokens', usage.get('prompt_tokens', 0)))
    output_tokens = _int(usage.get('output_tokens', usage.get('completion_tokens', 0)))
    cached = _int(ind.get('cached_tokens', usage.get('cached_input_tokens', 0)))
    cache_write = _int(ind.get('cache_write_tokens', usage.get('cache_write_input_tokens', 0)))
    reasoning = _int(outd.get('reasoning_tokens', usage.get('reasoning_output_tokens', 0)))
    total = _int(usage.get('total_tokens', input_tokens + output_tokens))

    # Defensive bounds. These fields are components of input/output totals when
    # providers expose them. Do not allow malformed future fields to create
    # negative ordinary-token counts downstream.
    cached = max(0, min(cached, input_tokens))
    cache_write = max(0, min(cache_write, max(0, input_tokens - cached)))
    reasoning = max(0, min(reasoning, output_tokens))
    total = max(total, input_tokens + output_tokens)

    return {
        'input_tokens': input_tokens,
        'cached_input_tokens': cached,
        'cache_write_input_tokens': cache_write,
        'ordinary_input_tokens': max(0, input_tokens - cached - cache_write),
        'output_tokens': output_tokens,
        'reasoning_output_tokens': reasoning,
        'total_tokens': total,
    }


def _find_rate(provider: str, model: str | None, cfg: dict[str, Any]) -> tuple[str | None, dict[str, Any] | None]:
    provider = str(provider or '').lower()
    model = str(model or '').lower()
    section = cfg.get('openai' if provider.startswith('openai') else 'jev' if provider.startswith('jev') else provider, {}) or {}
    # Prefer longest prefix to avoid gpt-5.6 matching before gpt-5.6-terra.
    candidates = []
    for key, rate in section.items():
        for pref in rate.get('model_match_prefixes', [key]):
            pref = str(pref).lower()
            if model == pref or model.startswith(pref):
                candidates.append((len(pref), key, rate))
    if not candidates:
        return None, None
    _, key, rate = sorted(candidates, reverse=True)[0]
    return key, rate


def _provider_reported_cost(usage: dict[str, Any] | None, raw: dict[str, Any] | None) -> float | None:
    usage = usage or {}; raw = raw or {}
    for obj in (usage, raw):
        for key in ('cost_usd', 'total_cost_usd', 'cost'):
            if key in obj and obj[key] is not None:
                try:
                    v = float(obj[key])
                    if math.isfinite(v):
                        return v
                except Exception:
                    pass
    return None


def estimate_cost(provider: str, model: str | None, usage: dict[str, Any] | None,
                  raw: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or pricing_config()
    flat = flatten_usage(provider, usage)
    key, rate = _find_rate(provider, model, cfg)
    reported = _provider_reported_cost(usage, raw)
    base = {
        'currency': cfg.get('currency', 'USD'),
        'pricing_snapshot_date': cfg.get('snapshot_date'),
        'processing_tier_assumed': cfg.get('processing_tier', 'standard'),
        'pricing_model_key': key,
        'pricing_source_url': rate.get('source_url') if rate else None,
        'provider_reported_cost_usd': reported,
        'estimated_input_cost_usd': None,
        'estimated_output_cost_usd': None,
        'estimated_total_cost_usd': None,
        'estimate_available': bool(rate),
        'estimate_basis': 'provider_usage_x_dated_list_price' if rate else 'no_matching_pricing_rule',
    }
    if not rate:
        return base

    input_mult = 1.0; output_mult = 1.0
    threshold = rate.get('long_context_threshold_tokens')
    if threshold is not None and flat['input_tokens'] > int(threshold):
        input_mult = float(rate.get('long_context_input_multiplier', 1.0))
        output_mult = float(rate.get('long_context_output_multiplier', 1.0))

    ordinary_rate = _num(rate.get('input_per_million')) * input_mult
    cached_rate = _num(rate.get('cached_input_per_million', rate.get('input_per_million'))) * input_mult
    cache_write_rate = _num(rate.get('cache_write_per_million', rate.get('input_per_million'))) * input_mult
    output_rate = _num(rate.get('output_per_million')) * output_mult

    input_cost = (
        flat['ordinary_input_tokens'] * ordinary_rate
        + flat['cached_input_tokens'] * cached_rate
        + flat['cache_write_input_tokens'] * cache_write_rate
    ) / 1_000_000.0
    output_cost = flat['output_tokens'] * output_rate / 1_000_000.0
    total = input_cost + output_cost
    base.update({
        'input_rate_usd_per_million': ordinary_rate,
        'cached_input_rate_usd_per_million': cached_rate,
        'cache_write_rate_usd_per_million': cache_write_rate,
        'output_rate_usd_per_million': output_rate,
        'long_context_multiplier_applied': bool(threshold is not None and flat['input_tokens'] > int(threshold)),
        'estimated_input_cost_usd': input_cost,
        'estimated_output_cost_usd': output_cost,
        'estimated_total_cost_usd': total,
    })
    return base


def usage_and_cost(provider: str, model: str | None, usage: dict[str, Any] | None,
                   raw: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None) -> tuple[dict[str, int], dict[str, Any]]:
    return flatten_usage(provider, usage), estimate_cost(provider, model, usage, raw=raw, cfg=cfg)
