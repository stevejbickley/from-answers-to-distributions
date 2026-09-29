# Model conditions and interpretation

## Principal conditions

| Condition ID | Model/interface | Role | Default configuration |
|---|---|---|---|
| `gpt4o_anchor` | OpenAI GPT-4o next-token logprobs | Historical-generation anchor | `gpt-4o-2024-05-13`; no reasoning parameter |
| `gpt56_sol` | OpenAI GPT-5.6 Sol next-token logprobs | Primary contemporary OpenAI condition | `gpt-5.6-sol`; reasoning `none` |
| `jev` | TypeSafe Jev typed probabilities | Decision-native comparison | exact version pinned with `TYPESAFE_MODEL` |
| `gpt56_terra` | OpenAI GPT-5.6 Terra next-token logprobs | Optional robustness | `gpt-5.6-terra`; reasoning `none` |

## Identification logic

The design deliberately avoids treating every between-system difference as architectural evidence.

1. **Full vs argmax within the same model** changes representation while holding the model call fixed.
2. **GPT-4o vs GPT-5.6 Sol** changes model generation while holding the next-token probability extraction method approximately fixed.
3. **GPT-5.6 Sol vs Jev** changes complete model system and probability interface; it is an empirical benchmark, not a causal estimate of an output-head effect.

## Historical snapshot caveat

Pinned model snapshots are preferred for reproducibility. The live preflight checks the configured GPT-4o snapshot. If it is unavailable, use the current `gpt-4o` family alias only with an explicit manuscript note that the condition is a historical-generation anchor rather than an exact 2024 snapshot replication.


All OpenAI probability conditions use explicit `temperature=1.0`. GPT-5.6 conditions use reasoning effort `none`; GPT-4o receives no reasoning parameter. Temperature 0 is not used for the primary probability vectors because it would alter the uncertainty object being measured.
