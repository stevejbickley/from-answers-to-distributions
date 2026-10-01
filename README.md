# Cultural alignment in AI does not imply population fidelity

**Replication and extension materials for:**  
*Cultural alignment in AI does not imply population fidelity.*

This repository provides the complete reproducibility workflow for a cross-national comparison of **human population response distributions**, **OpenAI next-token probability distributions**, and **Jev probability vectors over declared alternatives**.

The central question is whether **within-model uncertainty can recover between-person population heterogeneity**, and whether that correspondence is population-specific rather than merely generic uncertainty.

The study builds on the cultural-values benchmark introduced in the 2024 *PNAS Nexus* study *Cultural bias and cultural alignment of large language models*, but changes the main unit of evaluation from a single generated answer to the **full probability distribution over permitted responses**.

The primary design contains three model conditions:

1. **GPT-4o historical-generation anchor** — OpenAI next-token probability distributions from the earliest GPT-4o snapshot available to the researcher (`gpt-4o-2024-05-13` by default);
2. **GPT-5.6 Sol** — the primary contemporary OpenAI condition (`gpt-5.6-sol`, reasoning effort `none`); and
3. **TypeSafe Jev** — direct typed decision probability distributions from the System One API.

**GPT-5.6 Terra** is configured as an optional cost-balanced robustness condition and is not part of the primary design unless `--include-terra` is supplied.

The human benchmark is reconstructed from the **Integrated Values Surveys (IVS)** by harmonising the World Values Survey (WVS) and European Values Study (EVS), retaining the survey window and cultural-map variables used in the source study.

---

## October 2026 revision

All additions reuse the archived model outputs; no new API collection is required. The current publication set contains three main figures, three main tables, 24 supplementary tables and 16 supplementary figures. The manuscript and supplementary information are assembled and edited separately in Word, using the audited outputs from this repository.

```bash
python scripts/04_analyze.py --extensions-only  # new analyses against unchanged primary outputs
python scripts/05_make_outputs.py
python scripts/11_audit_publication.py
```

`python scripts/run_all.py --analysis-only --robustness` reruns all analysis stages, generates tables and figures, and audits the outputs. `--skip-human-sampling` explicitly skips the respondent bootstrap; missing external microdata explicitly skips all microdata-dependent sensitivities. Reproducing the full reported analysis requires those sensitivities to be completed.

## Scientific question

The study asks whether **uncertainty within one artificial system can recover heterogeneity across many humans**. This is the study's **uncertainty-substitution hypothesis**: a model probability distribution may contain population-level signal, but its statistical meaning is not assumed to be the same as a survey frequency.

The study distinguishes three probability objects that have the same mathematical form but different meanings:

- **human population heterogeneity:** the survey-weighted fraction of people in a country/territory selecting each response;
- **autoregressive token uncertainty:** the probability that an OpenAI model assigns to controlled response-label tokens; and
- **declared-alternative uncertainty:** the probability that Jev assigns directly to declared response alternatives.

For country/territory `c`, survey item `j`, and permitted response `k`, the principal estimands are:

- `H[c,j,k]` — survey-weighted human response frequency;
- `O4[c,j,k]` — GPT-4o next-token probability, renormalised over permitted labels;
- `O56[c,j,k]` — GPT-5.6 Sol next-token probability, renormalised over permitted labels; and
- `J[c,j,k]` — Jev direct decision probability.

For every machine distribution, the pipeline also derives an **argmax one-hot representation from the same aggregated probability vector**. This makes the full-distribution versus point-response comparison deterministic and avoids making a second model call merely to recover the modal answer.

The design separates three sources of change:

- **representation change:** full probability distribution versus argmax within the same model;
- **model-generation change:** GPT-4o versus GPT-5.6 Sol while holding the logprob extraction procedure approximately constant; and
- **probability-interface/system change:** GPT-5.6 Sol next-token probabilities versus Jev decision probabilities.

The empirical analysis is organised around four questions:

1. **Cultural location:** does country prompting reproduce the location improvement in Tao et al.?
2. **Country-specific signal:** does prompting move probability in the human country-specific direction, and recover distributions relative to the model default and LOCO human benchmark?
3. **Disagreement:** does model uncertainty recover both the level and adjusted structure of human entropy?
4. **Robustness:** do results persist across temporal targets, human respondent sampling, effective sample sizes, item omissions and elicitation diagnostics?

The cultural-map projection is retained as a secondary replication/extension of the Tao et al. benchmark rather than as the sole or primary test of population fidelity.

The GPT-5.6 Sol versus Jev comparison is an empirical comparison of complete model systems, **not** a causal estimate of the effect of a particular architecture or output head.

---

# Repository status

Empirical tables are generated from saved analysis outputs. Authors update the manuscript and supplementary information separately and cross-check their numerical claims, tables and figure captions against the audited outputs.

The repository is designed so that:

- WVS, EVS, and IVS respondent-level microdata remain outside the public repository;
- API keys remain in a local `.env` file and are never committed;
- raw provider-returned usage metadata are archived with model records;
- all human aggregate distributions, PCA coordinates, model-comparison statistics, tables, and figures are generated by code;
- model-collection files are append-only and resumable; and
- provenance/checksum files allow an independent researcher to verify which external human-data releases were used without redistributing those releases.

---

## Repository structure

```text
.
├── README.md
├── CITATION.cff
├── LICENSE
├── CHANGELOG.md
├── requirements.txt
├── pytest.ini
├── .env.example
├── .gitignore
│
├── config/
│   ├── analysis.yaml
│   ├── countries.yaml
│   ├── models.yaml
│   ├── pricing.yaml
│   ├── prompt_variants.yaml
│   └── questions.yaml
│
├── data/
│   ├── README.md
│   ├── raw/
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
│
├── docs/
│   ├── ANALYSIS_PLAN.md
│   ├── API_NOTES.md
│   ├── DATA_README.md
│   ├── IVS_MERGER.md
│   └── MODEL_CONDITIONS.md
│
├── scripts/
│   ├── 00_build_ivs.py
│   ├── 00_validate_environment.py
│   ├── 01_prepare_human.py
│   ├── 02_collect_openai.py
│   ├── 03_collect_jev.py
│   ├── 04_analyze.py
│   ├── 05_make_outputs.py
│   ├── 06_autofill_manuscript.py
│   ├── 07_option_order_robustness.py
│   ├── 08_jev_native_score.py
│   ├── 09_analyze_robustness.py
│   ├── 10_summarize_api_usage.py
│   └── run_all.py
│
├── src/
│   ├── analyze.py
│   ├── collect_jev.py
│   ├── collect_openai.py
│   ├── config.py
│   ├── cultural_map.py
│   ├── figures.py
│   ├── human.py
│   ├── jev_client.py
│   ├── manuscript_autofill.py
│   ├── metrics.py
│   ├── openai_logprobs.py
│   ├── prompts.py
│   ├── tables.py
│   ├── usage_costs.py
│   └── utils.py
│
├── results/
│   └── .gitkeep
│
├── figures/
│   └── .gitkeep
│
├── manuscript/
│   ├── Main_manuscript.md
│   ├── Main_manuscript_RESULTS_PENDING.docx
│   ├── Supplementary_Information.md
│   └── Supplementary_Information.docx
│
└── tests/
    ├── fixtures/
    └── test_*.py
```

The repository itself should contain **code, configuration, documentation, prompts, generated aggregate outputs, and reproducibility metadata**. Licensed WVS/EVS/IVS respondent microdata should remain in a separate local or restricted-access folder. Main and supplementary figures are generated from empirical outputs; the earlier conceptual probability-semantics figure is no longer part of the final figure set.

---

# Reproducing the study

## 1. Obtain the human survey data

The public repository does **not** redistribute WVS or EVS microdata.

The **reported empirical analysis** uses:

- **World Values Survey Trend File (1981–2022), version 4.1.0** — the WVS release used for the final release-updated benchmark; and
- **European Values Study Trend File 1981–2017, ZA7503, version 3.0.0** — DOI `10.4232/1.14021`.

The source Tao et al. study used an earlier WVS Trend release. If an independent researcher has access to that source-study release, it can be run as an additional historical replication benchmark, but it should not silently replace the v4.1 dataset used for the reported results.

The IVS construction also uses the official/common merge materials when available:

- `EVS_WVS_Merge Syntax_stata.do`
- `F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx`
- `F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx`

### Recommended private-data layout

A convenient arrangement is:

```text
/path/to/private/values-data/
├── ZA7503_v3-0-0.dta
├── Trends_VS_1981_2022_Stata_v4_1.dta        # reported-study WVS release
├── Trends_VS_1981_2022_Stata_v3_0.dta        # optional earlier-release replication, if available
├── EVS_WVS_Merge Syntax_stata.do
├── F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx
├── F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx
└── Integrated_values_surveys_1981-2022.csv.gz # created locally
```

This folder can be anywhere on the local machine and should **not** be committed to the public repository.

The repository `.gitignore` excludes `.env` and common WVS/EVS/IVS raw and processed filenames, but the safest practice is still to keep the licensed data physically outside the repository.

---

## 2. Create the Python environment

Python 3.10+ is recommended.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows — Command Prompt

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows — PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 3. Build the merged EVS + WVS → IVS dataset

If you already have the required harmonised IVS file, skip to **Step 4**.

If starting from the separate EVS and WVS Trend files, run `scripts/00_build_ivs.py`.

### Reported-study IVS build

Example using the WVS v4.1 release used for the reported empirical analysis:

```bash
python scripts/00_build_ivs.py \
  --evs "/path/to/private/values-data/ZA7503_v3-0-0.dta" \
  --wvs "/path/to/private/values-data/Trends_VS_1981_2022_Stata_v4_1.dta" \
  --merge-syntax "/path/to/private/values-data/EVS_WVS_Merge Syntax_stata.do" \
  --dictionary "/path/to/private/values-data/F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx" \
  --countries "/path/to/private/values-data/F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx" \
  --output "/path/to/private/values-data/Integrated_values_surveys_1981-2022.csv.gz"
```

If an earlier WVS Trend release matching the source study is available, substitute that file deliberately and write the result to a differently named output. Treat it as a historical replication benchmark rather than as the dataset underlying the reported results.

The merger is intentionally **fail-loud**. It:

1. classifies the EVS/WVS source files from their actual structure;
2. parses the official Stata merge syntax;
3. materialises the official 838-variable IVS schema;
4. applies the structural missing-value rules from the supplied merge syntax;
5. validates against the common EVS/WVS dictionary;
6. checks participating-country information when supplied;
7. preserves source missing-reason codes `-1` to `-5`;
8. prevents accidental WVS7 duplication when a joint EVS/WVS file is supplied;
9. supports memory-efficient `.csv.gz` output; and
10. writes provenance and QC files alongside the merged dataset.

The following files are produced next to the IVS output:

```text
Integrated_values_surveys_1981-2022.csv.gz
Integrated_values_surveys_1981-2022.csv.gz.manifest.json
Integrated_values_surveys_1981-2022.csv.gz.qc_wave_year_counts.csv
Integrated_values_surveys_1981-2022.csv.gz.qc_core_missing.csv
```

### Paper-core IVS only

If a smaller file containing only the variables required for this paper is preferred, add:

```text
--core-only
```

The complete schema is preferable for a reusable IVS build; `--core-only` is sufficient for this study.

### Important: use ZA7503, not ZA7505, for the full historical EVS component

`ZA7503_v3-0-0.dta` is the EVS Trend File covering the historical EVS waves required by the canonical merge.

`ZA7505_v5-0-0.dta` is instead the Joint EVS/WVS 2017–2022 file and contains EVS5 plus WVS7. Appending the full ZA7505 file to the WVS Trend File would duplicate WVS7 while omitting EVS1–4.

The merger therefore refuses to treat ZA7505 as a complete historical EVS source unless `--allow-partial-joint` is explicitly supplied. That mode is for diagnostics only and produces an explicitly partial WVS1–7 + EVS5 dataset.

### Important: do not preprocess ZA7503 with the Stata missing-value `.do` file

Use the original `ZA7503_v3-0-0.dta` file as input.

The Python merger intentionally retains the source `-1` through `-5` missing-reason codes and applies the required structural `-3`/`-4` rules itself. The accompanying Stata missing-value conversion file is therefore not required for this workflow.

---

## 4. Configure API keys, model versions, and external data paths

Copy the example environment file:

```bash
cp .env.example .env
```

On Windows, copy `.env.example` to `.env` manually or use:

```bat
copy .env.example .env
```

Populate `.env` with your own credentials and paths:

```dotenv
# Secrets
OPENAI_API_KEY=...
TYPESAFE_API_KEY=...
# JEV_API_KEY=...   # accepted alias if preferred

# Historical OpenAI anchor
OPENAI_HISTORICAL_MODEL=gpt-4o-2024-05-13

# Primary contemporary OpenAI model
OPENAI_PRIMARY_MODEL=gpt-5.6-sol
OPENAI_PRIMARY_REASONING_EFFORT=none

# Optional robustness model
OPENAI_TERRA_MODEL=gpt-5.6-terra
OPENAI_TERRA_REASONING_EFFORT=none

# TypeSafe / Jev
TYPESAFE_BASE_URL=https\://api.typesafe.ai
TYPESAFE_MODEL=jev-1.13.0

# External human-data paths
IVS_DATA_PATH=/absolute/path/to/private/values-data/Integrated_values_surveys_1981-2022.csv.gz

# Optional if working directly with separate files in another workflow
WVS_DATA_PATH=/absolute/path/to/private/values-data/Trends_VS_1981_2022_Stata_v4_1.dta
EVS_DATA_PATH=/absolute/path/to/private/values-data/ZA7503_v3-0-0.dta
```

`.env` is excluded from Git and must never be committed.

Pinned model versions are preferable for the archived final run. If `gpt-4o-2024-05-13` is unavailable to the API account, set:

```dotenv
OPENAI_HISTORICAL_MODEL=gpt-4o
```

and report this explicitly as a **historical-generation anchor rather than an exact historical snapshot replication**.

The package records both the requested and served model identifiers, so a model substitution cannot occur silently.

---

## 5. Validate the local configuration before making paid calls

Run:

```bash
python scripts/00_validate_environment.py
```

This checks:

- Python;
- required configuration files;
- whether API keys are present;
- whether configured external-data paths exist;
- selected OpenAI model conditions; and
- the configured Jev model.

This command makes **no paid API calls**.

---

## 6. Run the automated tests

Before the empirical run:

```bash
pytest -q
```

The automated test suite covers configuration safety, country-universe integrity, probability metrics, OpenAI censoring, multi-model analysis/configuration, Y003 reconstruction, the additional population-specificity and entropy-structure analyses, pipeline smoke tests, prompts, and API usage/cost accounting. The exact test count may increase as the replication package evolves; `pytest -q` is the authoritative check.

---

## 7. Run a minimal live API preflight

Before committing to the full model collection:

```bash
python scripts/00_validate_environment.py --live
```

This makes only minimal live requests and verifies:

- OpenAI authentication;
- GPT-4o availability;
- GPT-5.6 Sol availability;
- output logprob availability;
- permitted-label recovery;
- Jev authentication;
- Jev model discovery; and
- a minimal System One choice request.

To include the optional GPT-5.6 Terra condition in the preflight:

```bash
python scripts/00_validate_environment.py --live --include-terra
```

Run this immediately before the archived empirical collection so API/model availability is checked at the time of data generation.

---

# Full end-to-end run

Once the IVS file exists and `.env` is configured, the principal study can be executed with:

```bash
python scripts/run_all.py --robustness
```

This performs, in order:

1. human-data preparation;
2. GPT-4o and GPT-5.6 Sol probability collection;
3. Jev probability collection;
4. primary statistical analysis, including **population specificity** and **heterogeneity-structure** analyses;
5. option-order robustness collection;
6. Jev native-Score robustness collection;
7. robustness summarisation;
8. API token/cost accounting;
9. final main/SI table and figure generation **after all requested analyses are available**; and
10. publication-output auditing.

To include GPT-5.6 Terra as an additional supplementary robustness condition:

```bash
python scripts/run_all.py --include-terra --robustness
```

If the human benchmark and all model-response files are already present, rerun the complete local analysis without any new OpenAI or Jev calls using:

```bash
python scripts/run_all.py --analysis-only --robustness
```

Update the manuscript and supplementary information manually after reviewing the generated outputs.

`run_all.py` **does not construct IVS from raw EVS/WVS files**. The EVS/WVS → IVS build is deliberately a separate preliminary step because the licensed source files are external to the repository.

---

# Running the workflow step by step

The individual stages can also be run separately. This is useful for auditing, resuming API collection, or rerunning only analysis/output stages.

## A. Prepare the human benchmark

With `IVS_DATA_PATH` configured:

```bash
python scripts/01_prepare_human.py \\
  --ivs "/path/to/private/values-data/Integrated_values_surveys_1981-2022.csv.gz" \\
  --csv \\
  --outdir data/processed
```

This:

- restricts observations to common waves 5–7 and calendar years 2005–2022;
- applies substantive-value validity rules;
- reconstructs Y003 where necessary from its constituent items;
- computes survey-weighted country-year response distributions;
- averages country-year distributions equally within country;
- fits the human PCA/cultural-map model; and
- writes a path-free provenance/checksum manifest.

The required paper variables are:

```text
S001, S002VS, S003, S009, S017, S020,
A008, A165, E018, E025, F063, F118, F120, G006,
Y002, Y003, A029, A039, A040, A042
```

When necessary:

```text
Y003 = A029 + A039 - A040 - A042
```

The principal prepared outputs are:

```text
data/processed/human_country_year_distributions.csv
data/processed/human_country_distributions.csv
data/processed/human_y003_country_year_marginals.csv
data/processed/human_y003_country_marginals.csv
data/processed/pca_model.json
data/processed/human_input_provenance.json
```

`human_input_provenance.json` records filenames, byte sizes, SHA-256 checksums, the analysis window, and prepared-record count, but deliberately omits local filesystem paths.

---

## B. Collect OpenAI probability distributions

Run the two principal OpenAI conditions:

```bash
python scripts/02_collect_openai.py
```

Or run them separately:

```bash
python scripts/02_collect_openai.py --condition gpt4o_anchor
python scripts/02_collect_openai.py --condition gpt56_sol
```

Optional Terra robustness:

```bash
python scripts/02_collect_openai.py --condition gpt56_terra
```

or:

```bash
python scripts/02_collect_openai.py --include-terra
```

Output:

```text
data/processed/openai_probabilities.jsonl
```

The collector is **append-only and resumable**. Stable record IDs include model condition, country/territory, prompt variant, item, and label replication, so an interrupted run can resume without intentionally duplicating completed cells.

### Why OpenAI temperature is 1.0

The original 2024 point-response study set temperature to zero so a single generated answer would be as deterministic as possible. This replication-extension has a different primary estimand: the **full next-token probability distribution**. The OpenAI probability calls therefore explicitly set **`temperature=1.0`** for GPT-4o, GPT-5.6 Sol, and optional GPT-5.6 Terra. This avoids deliberately sharpening the distribution being measured. GPT-5.6 uses `reasoning.effort=none`, which is also compatible with temperature and logprob extraction.

The point-response comparison does not require a separate temperature-zero call: it is defined as the **argmax of the same temperature-1 probability vector**. For any positive temperature, temperature scaling preserves the ordering of logits, so this isolates the representation change (full distribution versus modal category) without introducing a second API draw. This should be described as continuity with, rather than byte-for-byte regeneration of, the original temperature-zero API run.

### OpenAI logprob safeguards

The OpenAI collector:

- uses controlled response labels;
- sets `max_output_tokens=16`, the current Responses API minimum; the prompt still requires a single response label, so this is a ceiling rather than an instruction to emit 16 tokens;
- requests `top_logprobs=20`;
- explicitly requests output-text logprob records;
- stores the generated token;
- stores every permitted label returned by the API;
- records labels absent from the top-logprob set;
- records pre-renormalisation probability mass assigned to permitted labels;
- records the residual vocabulary mass, number of top-logprob alternatives returned, and Kth-token cutoff where available;
- computes a conservative upper bound on total omitted permitted-label probability mass;
- classifies each call as complete, negligible tail-censoring, non-negligible tail-censoring, or incomplete without a full top-K cutoff;
- records requested and served model identifiers and explicit temperature; and
- never silently interprets an unreturned permitted label as exact probability zero.

Missing labels are treated as top-K censoring rather than automatic failures. The package conservatively upper-bounds their total omitted probability mass. The primary policy retains complete records plus records whose omitted permitted-label mass is bounded above by 0.001; a stricter 0.0001 policy and complete-only policy are generated as sensitivity analyses.

---

## C. Collect Jev probability distributions

Run:

```bash
python scripts/03_collect_jev.py
```

Output:

```text
data/processed/jev_probabilities.jsonl
```

Jev returns probabilities directly over the declared response alternatives. Where multiple answers are returned from one API request, the common request identifier is retained so request-level usage and costs are not double-counted.

The final archived empirical run should pin the exact Jev version in `.env` where possible.

---

## D. Run the primary analysis

```bash
python scripts/04_analyze.py
```

The primary analysis now includes the original distributional comparisons plus two additional analyses that require **no additional API calls**:

1. **Population specificity:** compares each country-conditioned model distribution with (a) the same model's unconditioned `__DEFAULT__` distribution and (b) an equal-country leave-one-country-out human baseline.
2. **Heterogeneity structure:** tests whether model entropy tracks where human disagreement occurs using overall, within-item, within-country, fixed-effect/residualized, Pearson/Spearman, slope, and variance-ratio diagnostics.

The analysis produces, among other files:

```text
results/model_mean_probabilities.csv
results/model_y003_mean_marginals.csv
results/country_item_metrics.csv
results/prompt_sensitivity.csv
results/openai_label_sensitivity.csv
results/openai_logprob_diagnostics.csv
results/openai_censoring_policy_counts.csv
results/country_item_metrics_censoring_sensitivity.csv
results/openai_censoring_sensitivity_summary.csv
results/y003_marginal_metrics.csv
results/population_specificity_metrics.csv
results/entropy_structure_summary.csv
results/entropy_structure_by_item.csv
results/entropy_structure_by_country.csv
results/cultural_map_coordinates.csv
results/cultural_map_distances.csv
results/cultural_map_prompting_distances.csv
results/cultural_map_prompting_summary.csv
results/cultural_map_tao_style_variant_coordinates.csv  # when reconstructable
```

For population specificity, a positive gain means the country-conditioned model is closer to that country's human response distribution than the stated baseline.

The cultural-map analysis now explicitly separates the **replication checkpoint** from the distributional extension. It compares each model's unconditioned/default cultural position with its country-conditioned positions, reproducing the logic of Tao et al.'s cultural-prompting analysis. The manuscript can therefore report whether the original mean-location result replicates before asking the harder question of whether the full national response distributions are recovered.

---

## E. Generate tables and figures

```bash
python scripts/05_make_outputs.py
```

This regenerates the final analysis-derived main and supplementary tables and figures from the saved empirical outputs. When `run_all.py --robustness` is used, this step runs **after** robustness analysis so option-order results can be incorporated into the final SI outputs.

### Main-text outputs

```text
results/tables/table2_primary_summary.csv
results/tables/table3_country_conditioning.csv
results/tables/table3_population_specificity.csv  # retained for detailed/backward-compatible reporting

figures/figure1_tao_replication.png
figures/figure2_country_specific_signal.png
figures/figure3_heterogeneity_structure.png
```

The main figures now follow the paper's narrative rather than displaying raw point clouds:

1. **Figure 1:** a direct replication/extension checkpoint against Tao et al. — the release-updated human cultural map with only unconditioned model positions, plus unconditioned-versus-country-conditioned cultural distance;
2. **Figure 2:** country-deviation direction and pooled projection, gains relative to the model default, and the LOCO human benchmark;
3. **Figure 3:** mean entropy and pooled/fixed-effect associations with human disagreement.

The full-versus-argmax comparison is now **Figure S15**. Figures S12–S16 add direction, temporal targets, leave-one-item-out entropy and conditional respondent-bootstrap diagnostics. The complete canonical set has 3 main and 16 supplementary figures.

The analysis additionally reconstructs a **Tao-style modal cultural-map representation** from the frozen probability records. Within each prompt variant, arbitrary OpenAI label rotations are averaged, each survey item is collapsed to its modal substantive response, the resulting ten-construct profile is projected into the human cultural-map space, and coordinates are averaged across prompt variants. This requires **no new API calls**. Because the present Y003 design uses four collected marginals rather than Tao et al.'s original direct joint selection task, this output is described as *Tao-style* rather than an exact point-response reproduction.

### Supplementary outputs

```text
results/tables/table_s3_openai_diagnostics.csv
results/tables/table_s4_openai_censoring_sensitivity.csv
results/tables/table_s5_full_vs_argmax.csv
results/tables/table_s6_item_summary.csv
results/tables/table_s7_country_summary.csv
results/tables/table_s8_prompt_sensitivity.csv
results/tables/table_s9_y003.csv
results/tables/table_s10_entropy_structure.csv
results/tables/table_s11_entropy_by_item.csv
results/tables/table_s12_population_specificity_by_item.csv
results/tables/table_s13_label_sensitivity.csv
results/tables/table_s14_option_order_sensitivity.csv
results/tables/table_s15_cultural_map.csv
results/tables/table_s16_tao_replication.csv
results/tables/paired_contrasts.json

figures/figure_s1_sol_vs_jev_fidelity.png
figures/figure_s2_prompt_sensitivity.png
figures/figure_s3_label_sensitivity_heatmap.png
figures/figure_s4_option_order_heatmap.png
figures/figure_s5_item_error_heatmap.png
figures/figure_s6_topk_retention.png
figures/figure_s7_y003_mae.png
figures/figure_s8_cultural_map_representations.png
figures/figure_s9_entropy_by_item_heatmap.png
figures/figure_s10_population_specificity_by_item_heatmap.png
figures/figure_s11_entropy_scatter_diagnostic.png
```

Some SI figures/tables are generated only when their corresponding robustness/input file exists.

---

## F. Run robustness analyses

### Option-order robustness

```bash
python scripts/07_option_order_robustness.py
```

The default robustness design samples the configured number of countries and randomly permutes response alternatives across repeated runs for GPT-4o, GPT-5.6 Sol, and Jev.

To add Terra:

```bash
python scripts/07_option_order_robustness.py --include-terra
```

Raw output:

```text
data/processed/option_order_robustness.jsonl
```

### Jev native-Score robustness

```bash
python scripts/08_jev_native_score.py
```

This evaluates the Jev ordered `Score` interface as a supplementary check where applicable.

### Summarise robustness results

```bash
python scripts/09_analyze_robustness.py
```

---

## G. Summarise API token usage and costs

```bash
python scripts/10_summarize_api_usage.py
```

The package retains the provider-returned `usage` payload on each empirical OpenAI and Jev record and also derives explicit fields for:

- input tokens;
- cached input tokens where returned;
- cache-write input tokens where returned;
- output tokens;
- reasoning output tokens where returned;
- total tokens;
- request ID;
- requested/served model;
- provider-reported cost where available; and
- a dated list-price cost estimate.

The pricing snapshot is stored in:

```text
config/pricing.yaml
```

The generated summaries are:

```text
results/api_request_usage.csv
results/api_usage_summary.csv
results/api_usage_totals.json
```

These are reproducibility metadata rather than invoices. Provider prices, processing tiers, credits, regional uplifts, and account-specific arrangements can change. The raw usage payload is retained so costs can be recalculated later.

---

## H. Update the manuscript and supplementary information

After analysis and the publication audit, copy the required tables from `results/tables/` and use the corresponding figure files in `figures/`. Edit the text and captions in Word, checking numerical claims, rounding, sample sizes and figure/table references against the saved outputs.

The pipeline does not assemble publication documents. `results/manuscript_tokens.json` remains a numerical lookup generated alongside the tables and figures. The separate legacy `scripts/06_autofill_manuscript.py` utility only replaces numerical placeholders in a user-supplied template and is not part of the current publication workflow.

---

# Human-data construction and version sensitivity

## Analysis window

The human-data preparation step enforces:

- common IVS wave codes **5, 6, and 7**; and
- calendar years **2005–2022**.

The calendar-year restriction is applied in addition to common-wave codes because newer WVS Trend releases can include a small number of observations outside 2005–2022 within those wave classifications.

## Survey weighting and aggregation

Within each country-year and item, response proportions are estimated using survey weight:

```text
S017
```

Country-level response distributions are then produced by **equally averaging the available country-year distributions**, matching the intended longitudinal treatment of countries participating in more than one wave.

## Cultural-map construction

The ten cultural-map constructs are:

```text
A008  Feeling of Happiness
A165  Trust on People
E018  Respect for Authority
E025  Petition Signing Experience
F063  Importance of God
F118  Justifiability of Homosexuality
F120  Justifiability of Abortion
G006  Pride of Nationality
Y002  Post-Materialist Index
Y003  Autonomy Index
```

The human PCA is fitted using the IVS benchmark and the paper's rescaling constants:

```text
PC1' = 1.81 × PC1 + 0.38
PC2' = 1.61 × PC2 − 0.01
```

The five source-study exclusions are:

```text
Egypt
Kuwait
Qatar
Tajikistan
Uzbekistan
```

because at least one required cultural-map variable lacks valid observations.

## WVS release sensitivity

The **reported analysis** uses **EVS ZA7503 v3.0.0 + WVS Trend v4.1**. This yields a slightly different 2005–2022 benchmark from the original Tao et al. paper because the WVS release itself has changed.

Accordingly, the paper describes the human benchmark as a **release-updated replication and extension**, not an exact numerical reproduction of the source-study dataset. If an earlier WVS release is additionally analysed, preserve its version in provenance and report it as a separate historical-replication sensitivity rather than mixing results across releases.

The merge code exposes release differences in QC/provenance outputs rather than concealing them.

---

# Y002 and Y003 handling

## Y002 — Post-Materialist Index

Y002 asks for the first- and second-ranked choice among four goals. The model experiment therefore elicits the **12 possible ordered pairs**, then maps those pairs to the three IVS categories:

- materialist;
- mixed; and
- post-materialist.

This preserves the original index logic while permitting a full probability distribution over the valid ordered response space.

## Y003 — Autonomy Index

Y003 is a multi-select item whose complete response space is too large for the common one-of-\\(K\\) probability-vector design.

The primary analysis therefore compares the four constituent marginals required by the index:

- Independence (`A029`);
- Determination/perseverance (`A039`);
- Religious faith (`A040`); and
- Obedience (`A042`).

Expected Y003 is calculated by linearity of expectation:

```text
E[Y003] =
P(Independence)
+ P(Determination)
- P(Religious faith)
- P(Obedience)
```

For EVS observations where merged Y003 is structurally unavailable, the human pipeline reconstructs it row-by-row when all four constituent items are valid.

---

# Primary analysis

## Primary full-distribution items

The primary common probability-distribution analysis includes:

```text
A008, A165, E018, E025, F063, F118, F120, G006, Y002
```

Y003 is analysed through its four constituent marginals as described above.

## Primary metric

The primary distributional metric is **Jensen–Shannon divergence**, base 2 and bounded between 0 and 1.

Secondary metrics include:

- total variation distance;
- normalised 1-Wasserstein distance for ordered scales;
- absolute expected-score error;
- normalised entropy error; and
- effective-number-of-categories diagnostics.

Every applicable distributional metric is calculated for:

1. the full machine probability distribution; and
2. the argmax one-hot distribution derived from exactly the same **aggregated** model probability vector.

This isolates the information lost by collapsing an already-estimated probability distribution to its modal response; it is not a comparison with a second stochastic API draw.

## Primary model contrasts

The principal model comparisons are:

- **GPT-5.6 Sol vs Jev** — contemporary probability-system/interface comparison;
- **GPT-4o vs GPT-5.6 Sol** — model-generation/temporal comparison;
- **GPT-4o vs Jev** — historical-generation versus declared-alternative interface comparison; and
- **full distribution vs argmax within each model** — incremental population-level information from retaining uncertainty.

Pairwise full-distribution contrasts use a crossed bootstrap that independently resamples countries and items with replacement. Paired Wilcoxon tests are reported as secondary robustness statistics.

## Population specificity

For each country `c` and item `j`, the analysis asks whether country conditioning contributes information beyond two baselines.

### Same-model unconditioned baseline

```text
country-conditioning gain
= JSD(human[c,j], model[DEFAULT,j])
- JSD(human[c,j], model[c,j])
```

A positive value means the country-conditioned distribution is closer to the corresponding human population than the same model's unconditioned distribution.

### Leave-one-country-out human baseline

For each target country, the pipeline also constructs an equal-country mean response distribution using all other countries for the same item. It then compares the model's country-specific JSD with this naive cross-national human benchmark.

Outputs include mean and median gains, percentage of cells improved, crossed-bootstrap confidence intervals, and item-level summaries.

## Heterogeneity structure

Matching average entropy is distinguished from tracking **where disagreement occurs**. In addition to mean entropy error, the pipeline reports:

- overall Pearson and Spearman human-model entropy association;
- the original entropy-on-entropy OLS slope and clustered confidence interval;
- item-fixed-effect, country-fixed-effect, and two-way-fixed-effect slopes;
- within-item association across countries;
- within-country association across items;
- two-way-residualized Pearson and Spearman association; and
- human/model entropy standard deviations and variance-compression ratios.

These diagnostics distinguish a model that merely has the right average amount of uncertainty from one whose uncertainty changes across populations and questions in the same places as observed human heterogeneity.

The default bootstrap configuration is stored in `config/analysis.yaml`.

---

# Prompt, label, and order robustness

The source benchmark uses ten semantically similar respondent descriptors. These are preserved so probability estimates are not identified from one wording alone.

For each model condition, the analysis assesses:

- dispersion across respondent-descriptor variants;
- OpenAI label-assignment sensitivity;
- OpenAI permitted-label probability mass and completeness;
- answer-option order sensitivity; and
- Jev native ordered-Score behavior where applicable.

The OpenAI label mapping is systematically rotated across prompt variants so response labels are not permanently tied to substantive answer categories.

---

# Model conditions

| Condition | Interface | Role | Default |
|---|---|---|---|
| `gpt4o_anchor` | OpenAI next-token logprobs | Historical-generation anchor | `gpt-4o-2024-05-13` |
| `gpt56_sol` | OpenAI next-token logprobs | Primary contemporary OpenAI model | `gpt-5.6-sol`, reasoning `none` |
| `jev` | Jev typed decision probabilities | Declared-alternative interface comparison | exact version pinned via `TYPESAFE_MODEL` |
| `gpt56_terra` | OpenAI next-token logprobs | Optional robustness | `gpt-5.6-terra`, reasoning `none` |

The model and analysis configuration are stored in:

```text
config/models.yaml
config/analysis.yaml
```

For the final archived empirical run, preserve:

- collection date/time;
- requested model;
- served model;
- model version where available;
- prompt/configuration files;
- API response IDs;
- raw usage metadata; and
- the repository commit/tag used for collection.

---

# Reproducing analyses without making new API calls

Once the processed human benchmark and model-response JSONL files have been archived, the preferred way to rerun the complete analysis is:

```bash
python scripts/run_all.py --analysis-only --robustness
```

This makes **no OpenAI or Jev API calls**. It:

1. reuses the existing `data/processed/` human/model outputs;
2. reruns primary analysis, including population specificity and entropy structure;
3. reanalyses existing robustness JSONL files when `--robustness` is supplied;
4. rebuilds API usage/cost summaries;
5. regenerates the correctly numbered final tables and figures; and
6. audits the publication outputs.

The same stages can also be run manually:

```bash
python scripts/04_analyze.py
python scripts/09_analyze_robustness.py   # if robustness outputs exist
python scripts/10_summarize_api_usage.py
python scripts/05_make_outputs.py
python scripts/11_audit_publication.py
```

`--skip-openai` and `--skip-jev` remain useful for partial workflows, but `--analysis-only` is the clearest option when all provider collection has already been completed.

---

# Licensed data and repository policy

The WVS, EVS, and constructed IVS respondent-level files are **not redistributed** in this repository.

For public end-to-end replication, an independent researcher should:

1. obtain the cited WVS and EVS releases from their official repositories;
2. place them in a local/restricted directory;
3. run `scripts/00_build_ivs.py`;
4. verify the generated provenance/QC outputs;
5. run the human-data preparation step; and
6. continue through the API and analysis pipeline.

The public repository can contain:

- dataset citations and acquisition instructions;
- release identifiers;
- merge/harmonisation code;
- checksums and provenance;
- configuration files;
- all prompts;
- API collection code;
- archived provider outputs where redistribution is permitted;
- aggregate human benchmarks where permitted;
- statistical-analysis code;
- generated tables/figures; and
- manuscript/SI source files.

It should not contain the restricted raw survey microdata.

---

# Reproducibility and audit trail

The package is designed to retain the information required to audit the complete workflow.

## Human-data provenance

`scripts/00_build_ivs.py` writes:

- source-file classification;
- source hashes;
- merge/schema information;
- warnings;
- wave/year counts; and
- missing-code diagnostics.

`scripts/01_prepare_human.py` writes:

```text
data/processed/human_input_provenance.json
```

with source filename, byte size, SHA-256 checksum, analysis window, and prepared-record count, while intentionally excluding private local paths.

## Model-call provenance

Each empirical OpenAI/Jev record stores, where available:

- stable study record ID;
- unique provider/request ID;
- provider;
- study condition;
- country/territory;
- survey item;
- prompt variant;
- exact response mapping;
- probabilities;
- requested model;
- served model;
- provider usage metadata;
- flattened token counts; and
- cost metadata.

## Configuration provenance

The frozen study configuration is defined in:

```text
config/questions.yaml
config/prompt_variants.yaml
config/models.yaml
config/analysis.yaml
config/pricing.yaml
```

Archive these files with the final study release.

---

# Interpretation

A lower divergence from human survey frequencies does **not** mean that a model “is” a culture or that its internal uncertainty is definitionally population heterogeneity.

Country/territory labels are coarse descriptions of internally heterogeneous populations. Human survey frequencies describe variation **between people**; OpenAI logprobs describe conditional **next-token uncertainty within one model**; Jev probabilities describe **decision uncertainty over declared alternatives**.

The central empirical question is therefore whether uncertainty within one model can serve as a useful statistical proxy for variation across many people. The study tests that **uncertainty-substitution hypothesis** rather than assuming equivalence.

The additional population-specificity analysis asks whether a country-conditioned model contains information about that country's response distribution beyond an unconditioned model distribution and a naive leave-one-country-out human baseline. The heterogeneity-structure analysis separately asks whether model uncertainty changes across countries and questions in the same places that human disagreement changes.

Similarly, differences between GPT-5.6 Sol and Jev should not be interpreted as identifying a single architectural mechanism, because the systems differ in many unobserved aspects of pretraining, post-training, capacity, objectives, and serving.

---

# Citation

If you use this repository, its code, or its generated materials, please cite the associated study and the software archive.

Machine-readable citation metadata are provided in:

```text
CITATION.cff
```

The associated manuscript is currently:

\> *Can AI uncertainty recover human population variation? Token uncertainty, decision uncertainty, and cross-cultural survey responses.*

Before the final archival release, update `CITATION.cff` with the final author list, repository/archive DOI, journal citation, and article DOI where applicable.

The WVS and EVS source datasets should also be cited separately using the citations required by their respective data providers.

---

# Licence

Analysis and replication code are released under the licence specified in `LICENSE`.

The repository licence does **not** override:

- WVS or EVS data-access/licensing terms;
- OpenAI, TypeSafe/Jev, or other provider terms;
- publisher rights in manuscript versions; or
- third-party rights in any external material.

Licensed survey microdata remain governed by their original providers and are not redistributed here.

---

# Recommended archival checklist

Before creating the final GitHub/Zenodo/OSF release:

- [ ] confirm the final WVS and EVS release/version used;
- [ ] archive `human_input_provenance.json`;
- [ ] archive the IVS build manifest and QC outputs;
- [ ] run `pytest -q`;
- [ ] run the live API preflight;
- [ ] pin and record model versions;
- [ ] complete the primary and robustness API collections;
- [ ] verify OpenAI permitted-label completeness diagnostics;
- [ ] verify Jev response/model metadata;
- [ ] generate `api_request_usage.csv`, `api_usage_summary.csv`, and `api_usage_totals.json`;
- [ ] rerun and verify the population-specificity and entropy-structure analyses;
- [ ] regenerate all tables and figures from the archived inputs;
- [ ] update the manuscript and supplementary information in Word and cross-check all reported numbers against the audited outputs;
- [ ] ensure `.env` and licensed microdata are absent from Git history;
- [ ] update `CITATION.cff` with the final author list and DOI(s);
- [ ] tag the exact repository commit used for the submitted/final manuscript; and
- [ ] archive the release in the selected long-term repository.

For implementation details beyond this README, see:

```text
docs/ANALYSIS_PLAN.md
docs/API_NOTES.md
docs/DATA_README.md
docs/IVS_MERGER.md
docs/MODEL_CONDITIONS.md
```
## Publication outputs

The current canonical set contains three main and sixteen supplementary figures,
with PNG, PDF and SVG exports listed in `figures/manifest.json`. Tables are saved
in `results/tables/`, and `results/publication_audit.json` records numerical checks.
The manuscript and supplementary information are assembled and edited separately
in Word after the analysis outputs have been audited.

[The September publication review](docs/PUBLICATION_REVIEW.md) records an earlier
revision, including corrections to sensitivity denominators and order-reference
selection. Its historical output counts do not describe the current figure set.
