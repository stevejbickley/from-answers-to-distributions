# Changelog

## Multi-model design update — 2026-09-25

- Changed primary contemporary OpenAI condition from GPT-5.6 Terra to **GPT-5.6 Sol**.
- Added **GPT-4o historical-generation anchor** as a principal model condition.
- Kept **GPT-5.6 Terra** as optional robustness only.
- Added explicit model-condition metadata to every OpenAI and Jev record.
- Added requested-versus-served OpenAI model identifiers.
- Prevented GPT-4o from inheriting GPT-5.6 reasoning parameters.
- Added full-distribution versus deterministic argmax evaluation for every model condition.
- Added pairwise crossed-bootstrap contrasts: Sol vs Jev, GPT-4o vs Sol, GPT-4o vs Jev.
- Updated prompt/label/order robustness to be condition-specific.
- Updated figures, tables, manuscript framing, README, analysis plan, API notes, and tests.
- GPT-5.6 Terra can be enabled with `--include-terra`.

### 2026-09-25 — usage and cost accounting
- Preserve provider-returned usage for OpenAI and Jev and add flattened token fields.
- Add dated, auditable list-price estimates in `config/pricing.yaml`.
- Record request IDs so batched Jev answers are not double-counted.
- Add request-level and aggregate token/cost summary outputs.
- Add tests for OpenAI cached/cache-write token accounting and Jev input-only billing.


## 2026-09-25 — final OpenAI probability/censoring patch
- Set OpenAI probability extraction explicitly to `temperature=1.0`; retained GPT-5.6 reasoning effort `none`.
- Added conservative top-K censoring bounds based on residual vocabulary mass, with the Kth-token probability retained as a diagnostic.
- Primary policy now retains complete calls plus negligible censored tails (`upper bound <= 0.001`) instead of dropping every incomplete call.
- Added stricter (`1e-4`) and complete-only sensitivity outputs.
- Added balanced and deliberately lopsided live preflight checks with censoring diagnostics.
- Added request-level top-K/censoring metadata and tests.
