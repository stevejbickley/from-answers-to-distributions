# From answers to distributions: replication and extension package

This package reproduces the cultural-values survey design in the attached PNAS Nexus study and extends it to compare:

1. **Human population response distributions** from the Integrated Values Surveys (IVS; WVS + EVS),
2. **OpenAI next-token probability distributions** reconstructed from `top_logprobs`, and
3. **TypeSafe Jev direct decision probability distributions** returned by the System One API.

The core scientific question is not whether one newly released model is "better." It is whether three different statistical objects — population heterogeneity, lexical next-token uncertainty, and decision uncertainty — coincide closely enough that model probabilities can be interpreted as synthetic population distributions.

## Important status

The package is complete and executable, but **no empirical model results are fabricated here**. To produce the numerical Results section, you must provide:

- the IVS/WVS+EVS data used by the original study (the data are licensed/distributed by WVS/EVS and are not bundled here),
- `OPENAI_API_KEY`, and
- `TYPESAFE_API_KEY` / Jev early-access credentials.

Once those are supplied, `python scripts/run_all.py ...` produces the processed human distributions, model probability records, all main/SI tables, figures, diagnostics, and a JSON dictionary that can auto-fill the manuscript result placeholders.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env with API keys; never commit it

# Option A: already merged IVS trend file
python scripts/run_all.py --ivs /path/to/IVS_trend_file.sav

# Option B: separate harmonized WVS and EVS trend files
python scripts/run_all.py --wvs /path/to/WVS_TimeSeries_3_0.sav --evs /path/to/EVS_Trend_3_0.sav
```

For a dry run without paid API calls:

```bash
python tests/fixtures/create_synthetic_ivsd.py
python scripts/01_prepare_human.py --ivs tests/fixtures/synthetic_ivsd.csv --csv
python -m pytest -q
```

## Reproducibility target

The source article reports using the three most recent survey waves (2005–2022), the ten IVS variables underlying the Inglehart–Welzel map, survey weight `S017`, PCA with pairwise deletion and varimax rotation, and the published rescaling equations. The Python implementation here mirrors those steps as closely as possible. Because the original analysis used software-specific factor scoring, the package also writes diagnostics and includes a reference SPSS syntax file. The paper's published rescaling constants are treated as authoritative for replication.

## Primary estimands

For each country/territory `c`, item `j`, and permitted response `k`:

- `H[c,j,k]`: survey-weighted human response probability,
- `O[c,j,k]`: OpenAI probability reconstructed from next-token log probabilities and renormalized over allowed single-token labels,
- `J[c,j,k]`: Jev direct choice probability.

Primary distributional metrics are Jensen-Shannon divergence, total variation distance, normalized Wasserstein distance for ordered items, expected-score error, and entropy/effective-category error. The primary model contrast is paired at the country × item level with a crossed country/item bootstrap.

## Y002 and Y003

- **Y002** is elicited as one of the 12 possible ordered pairs of two distinct goals, then aggregated into the WVS materialist/mixed/post-materialist index distribution.
- **Y003** cannot be represented exactly as a single small choice distribution because the original question allows up to five selections from 11 qualities (1,024 possible subsets including the empty set). It is therefore retained in the 10-item cultural-map replication using the four constituent marginals needed for its expected index, while the primary full-distribution benchmark is conducted on the other nine constructs. The SI reports the four Y003 constituent probabilities separately. No independence assumption is required for the expected Y003 index because expectation is linear.

## Main directories

- `config/` — exact survey prompts, response coding, prompt variants, model/API settings
- `src/` — reusable implementation
- `scripts/` — numbered end-to-end pipeline
- `tests/` — unit and smoke tests
- `docs/` — analysis plan and data notes
- `manuscript/` — manuscript/SI source text and result-token dictionary
- `results/`, `figures/` — generated outputs

## Ethics / interpretation

These are population-level benchmark comparisons. A lower distributional distance does not mean the model "is" a culture, nor does a model probability automatically estimate a human frequency. Country labels are coarse proxies for heterogeneous populations, and country prompting may reproduce stereotypes rather than within-country variation. The analysis is designed to measure those limitations rather than assume them away.
