# API notes and frozen-model policy

## OpenAI

The primary contemporary OpenAI condition is `gpt-5.6-sol` with reasoning effort `none`. GPT-5.6 Terra is optional robustness.

The historical-generation anchor defaults to `gpt-4o-2024-05-13`. Pinned snapshots are preferred because model-family aliases can change behavior over time. Run `python scripts/00_validate_environment.py --live` before the full experiment. If the pinned GPT-4o snapshot is unavailable, set `OPENAI_HISTORICAL_MODEL=gpt-4o` and explicitly report that this is a generation-level anchor rather than an exact 2024 snapshot replication.

The collector requests `top_logprobs=20` and `include=['message.output_text.logprobs']`. The code stores both the model requested and the model returned in the API response, plus response ID, usage, generated token, complete permitted-label diagnostics, and exact prompt mapping.

## Jev / TypeSafe

Pin `TYPESAFE_MODEL` to the exact Jev model version used in the archived empirical run when possible. The live preflight validates `/v1/models` and one minimal System One choice request.

## Cost control and resumability

All collection files are append-only JSONL with stable IDs containing model condition, country, prompt variant, item, and label replication. Interrupted experiments can resume safely. The optional Terra model is disabled by default and is activated only with `--include-terra` or `--condition gpt56_terra`.

## Token and cost accounting

Every empirical OpenAI and Jev record retains the provider-returned `usage` object verbatim and additionally stores:

- `request_id` (used to identify one billable API call);
- `usage_flat.input_tokens`;
- `usage_flat.cached_input_tokens` and `cache_write_input_tokens` when reported by OpenAI;
- `usage_flat.output_tokens` and `reasoning_output_tokens` when reported;
- `usage_flat.total_tokens`;
- a `cost` object containing any provider-reported cost if present and a dated list-price estimate.

The dated rates live in `config/pricing.yaml`. Costs are explicitly labelled estimates, because provider prices, processing tiers, credits, regional uplifts and gateway markups can change. Raw usage remains authoritative for recomputing costs under another price schedule.

Run `python scripts/10_summarize_api_usage.py` to create:

- `results/api_request_usage.csv` — one row per unique API request;
- `results/api_usage_summary.csv` — requests, token totals and estimated USD cost by provider/model condition;
- `results/api_usage_totals.json` — whole-study totals.

Jev Y003 uses one batched Noul request for four constituent questions. The same request usage is attached to each answer record for provenance, but `request_id` is shared and the summarizer bills/counts the API request only once.


## Temperature and top-K censoring

Primary OpenAI probability extraction explicitly uses `temperature=1.0` for GPT-4o, GPT-5.6 Sol, and optional GPT-5.6 Terra. This is deliberate: the study measures the model's next-token probability distribution, so temperature 0 would sharpen/collapse the sampling distribution toward its modal token. The 2024 source study used temperature 0 because its outcome was a single point response. Our point-response representation is instead the deterministic argmax of the temperature-1 probability vector. GPT-5.6 conditions use `reasoning.effort=none`, which is required for logprob/temperature compatibility.

If one or more permitted labels are absent from the returned top-K set, the code does not assign them exact zero probability without qualification. It stores the residual vocabulary mass and the Kth-token cutoff when available. The conservative semantic-label upper bound used for inclusion is the residual vocabulary mass, `1 - allowed_mass`. The Kth-token cutoff is retained as a diagnostic only, because one whitespace-normalized semantic label can correspond to multiple raw token surface forms. Primary analyses retain complete calls and tail-censored calls whose omitted permitted-label mass upper bound is at most `0.001`. Sensitivity analyses use `0.0001` and complete-only records.
