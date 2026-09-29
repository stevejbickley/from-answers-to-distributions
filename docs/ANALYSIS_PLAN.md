# Preregistered analysis plan

## Core design

The human benchmark is compared with three principal probabilistic model conditions: GPT-4o historical-generation anchor (`gpt4o_anchor`), GPT-5.6 Sol (`gpt56_sol`), and Jev (`jev`). GPT-5.6 Terra (`gpt56_terra`) is supplementary robustness only.

The GPT-4o anchor is included to distinguish a **change in probability representation** from a **change in model generation**. Within each model we derive both its full probability vector and its argmax point representation from the same API call. Between GPT-4o and GPT-5.6 Sol we hold the extraction method constant while changing model generation. Between GPT-5.6 Sol and Jev we compare distinct probability interfaces on a contemporary benchmark.

## Probability semantics

- Human: between-person response frequency within a country/territory.
- GPT-4o / GPT-5.6: conditional next-token probability over controlled single-token labels, renormalized over permitted labels.
- Jev: direct probability over declared choices returned by a typed decision interface.

Numerical similarity is empirical; semantic equivalence is not assumed.

## Primary sample and estimator

Use all countries/territories retained by the source cultural-map replication with valid human distributions. Primary full-distribution items are A008, A165, E018, E025, F063, F118, F120, G006, and Y002. Y003 is evaluated through the four constituent marginals needed for its expected autonomy index.

Within each country-year and item, estimate survey-weighted response proportions using `S017`, then average country-year vectors equally within country. For each model condition, average the ten respondent-descriptor variants at the probability-vector level after label-rotation replications.

## Primary metrics

Primary: Jensen-Shannon divergence (base 2; bounded 0–1).

Secondary: total variation distance; normalized 1-Wasserstein distance for ordered scales; absolute expected-score error; normalized entropy error; effective-number-of-categories error.

Every metric is computed for:

1. the full machine probability vector; and
2. an argmax one-hot vector derived from that exact same vector.

## Planned contrasts

The principal full-distribution contrast is `error_GPT5.6Sol - error_Jev`; positive values indicate lower error for Jev.

Additional planned contrasts:

- `error_GPT4o - error_GPT5.6Sol` — temporal/model-generation change;
- `error_GPT4o - error_Jev` — historical-generation versus decision-native comparison;
- `error_argmax - error_full` within each condition — incremental fidelity from retaining uncertainty.

Pairwise model contrasts use a crossed bootstrap that independently resamples countries and items with replacement. Paired Wilcoxon tests are secondary robustness statistics.

## Prompt, label, and order robustness

For each country × item × model condition, compare each of the ten wording variants with that condition's across-variant mean distribution using JSD. OpenAI label assignments rotate systematically across variants. A supplementary option-order experiment randomly permutes alternatives for a stratified country subset and is run for GPT-4o, GPT-5.6 Sol, Jev, and optional Terra when requested.

## OpenAI completeness diagnostics

Request `top_logprobs=20`, explicitly include output-text logprobs, and set `temperature=1.0` for probability extraction. The original point-response study used temperature 0; this extension uses T=1 because its estimand is the unsharpened next-token probability vector, with the point response defined by the vector argmax. Report by model condition:

- missing permitted labels;
- pre-renormalization permitted-label probability mass;
- generated token and whether it is a permitted label;
- requested and served model IDs.

Missing alternatives are never silently interpreted as exact zero. For each incomplete OpenAI call, bound the total omitted permitted-label mass by the residual vocabulary probability mass, `1 - allowed_mass`. Record the 20th-token probability as an additional diagnostic, but do not use `missing_count × p_20` as the semantic-label bound because a normalized label can have multiple raw token surface forms. Primary estimates retain complete records plus tail-censored records with an upper bound <= 0.001. Prespecified sensitivities use <= 0.0001 and complete-only records.

## GPT-4o historical anchor availability

The default historical anchor is `gpt-4o-2024-05-13`, because pinned snapshots are preferable when available. API availability is checked during live preflight. If that snapshot is unavailable, the analyst may set `OPENAI_HISTORICAL_MODEL=gpt-4o`; this must be reported as a historical-generation anchor rather than an exact historical model replication. Requested and served model identifiers are archived in every record.

## Reasoning configuration

GPT-5.6 Sol and Terra use reasoning effort `none` in the primary probability-elicitation design. This better matches immediate survey-response elicitation and Jev's System One framing than introducing additional hidden deliberative computation. A reasoning-effort extension may be added later as a supplementary experiment but is not part of the primary design.

## Y002 and Y003

Y002 is elicited over 12 ordered pairs and aggregated to the three IVS index categories. Y003's full subset space is not included in primary JSD analysis; instead compare the four constituent marginal selection probabilities and compute expected Y003 exactly as `p(Independence)+p(Determination)-p(Religious faith)-p(Obedience)`.

## Cultural-map analysis

Project both expected-score and argmax representations into the human-fitted 10-variable cultural-map space. Compare country-prompted model coordinates with human country coordinates using Euclidean distance. The expected-versus-argmax comparison directly quantifies how much cultural-alignment conclusions change when uncertainty is retained.

## Data governance

WVS/EVS/IVS respondent microdata remain outside the public repository. The repository contains only acquisition/version instructions, code, prompts, aggregate/generated outputs permitted for sharing, and path-free provenance/checksums. Tables and figures are always regenerated from the analyst-supplied external human data.
