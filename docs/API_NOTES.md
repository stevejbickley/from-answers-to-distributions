# API implementation notes (23 September 2026)

## OpenAI

The current Responses API supports `top_logprobs` from 0 to 20. Each output-text token can include its own log probability and a list of the most likely alternative tokens. The default comparator is `gpt-5.6-terra`, chosen because it balances intelligence and cost and because TypeSafe publicly used GPT-5.6 Terra as a comparison point for Jev. Pin the exact model snapshot/model identifier returned by the API in the final paper.

The package deliberately uses short single-token labels (A-L), strips incidental whitespace when matching tokens, records all returned top-logprobs, and renormalizes only across allowed labels. `allowed_mass` is retained as a diagnostic because the conditional distribution over allowed labels is not the same as the model's full vocabulary distribution.

## Jev

The TypeSafe API endpoint is `POST /v1/systemone`, authenticated with `Authorization: Bearer <API_KEY>`. Choice questions define instructions and a criteria dictionary; responses include a `probabilities` dictionary over choices. Noul questions are used for Y003 constituent marginals. Run `GET /v1/models` before the study and record the returned Jev model name/version.

The study compares observable probability interfaces. It does not attempt to reverse-engineer hidden architecture, weights, attention masks, or proprietary training procedures.
