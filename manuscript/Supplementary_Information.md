# Supplementary Information

## Do AI probability distributions represent human population variation?

### Contents

S1. Study overview and deviations from the 2024 cultural-map evaluation  
S2. Human data and version pinning  
S3. Complete survey prompts and response coding  
S4. Respondent-descriptor variants  
S5. OpenAI probability elicitation and diagnostics  
S6. Jev probability elicitation and diagnostics  
S7. Treatment of Y002 and Y003  
S8. Statistical estimands and metrics  
S9. PCA/cultural-map replication validation  
S10. Robustness analyses  
S11. Additional figures and tables  
S12. Reproducibility checklist

## S1. Study overview and deviations from the earlier point-response design

The original cultural-map evaluation queried generative language models with ten Integrated Values Surveys (IVS) questions, set temperature to zero, recorded one model response per prompt variant, projected those point responses using the IVS-derived cultural-map transformation, and measured Euclidean distance from human country coordinates. The present study preserves the human benchmark, substantive questions, respondent descriptors, country-prompting manipulation, and cultural-map projection while replacing the primary model outcome with a probability vector.

The main extension is therefore not a new survey. It changes the estimand from “which answer does the model select?” to “how much probability does the model assign to every permitted answer, and does that vector resemble the empirical human response-frequency vector?” The study compares two probability interfaces that differ in semantics: OpenAI next-token log probabilities over controlled response labels and Jev direct probabilities over declared Choice alternatives.

The earlier study used ten prompt variants to reduce dependence on exact wording. We retain all ten variants and use them as a direct robustness measure rather than only averaging them. Label assignments are also rotated for the OpenAI condition because prior work shows survey responses can be sensitive to labels such as “A.” A supplementary option-order experiment quantifies list-position effects for both systems.

## S2. Human data and version pinning

### S2.1 Target data versions

The replication package targets the source-study versions:

- World Values Survey Trend File (1981-2022), cross-national data set, version 3.0.0, DOI 10.14281/18241.23.
- European Values Study Trend File 1981-2017, ZA7503, version 3.0.0, DOI 10.4232/1.14021.

Later WVS/EVS releases should not silently replace these files in the strict replication because harmonization, country coverage, and published map instructions can change. An updated-data analysis may be added as a robustness test and labeled explicitly.

### S2.2 Variables

Required survey variables are `A008`, `A165`, `E018`, `E025`, `F063`, `F118`, `F120`, `G006`, `Y002`, and `Y003`. The Y003 constituents `A029`, `A039`, `A040`, and `A042` are also required for the probability-aware extension. Metadata variables are `S001`, `S002VS`, `S003`, `S009`, `S017`, and `S020`.

The analysis retains wave codes 5, 6, and 7, corresponding to the three recent joint survey periods used in the source study. Within each country-year, proportions and means use weight S017. Country-year estimates are then averaged equally within country. This mirrors the source study’s approach of retaining multiple waves and averaging country-year map scores rather than allowing countries with more pooled respondent records to mechanically dominate their own longitudinal summary.

### S2.3 Missing values

For every substantive item, values outside its documented valid response set are converted to missing before any distribution, mean, or PCA calculation. We do not interpret conventional negative missing codes as substantive values. The code logs valid N, weighted N, and missing proportion by country-year-item.

## S3. Complete survey prompts and response coding

The exact source wording is stored in `config/questions.yaml`. The probability conditions preserve the substantive stems but replace the final response-format instruction with a controlled one-token label interface for OpenAI and a declared Choice set for Jev.

### Table S1. Survey constructs and probability representation

| ID | Construct | Human response support | Primary probability representation |
|---|---|---|---|
| A008 | Feeling of Happiness | 1-4 | Four-way Choice |
| A165 | Trust on People | 1-2 | Two-way Choice |
| E018 | Respect for Authority | 1-3 | Three-way Choice |
| E025 | Petition Signing Experience | 1-3 | Three-way Choice |
| F063 | Importance of God | 1-10 | Ten-way Choice |
| F118 | Justifiability of Homosexuality | 1-10 | Ten-way Choice |
| F120 | Justifiability of Abortion | 1-10 | Ten-way Choice |
| G006 | Pride of Nationality | 1-4 | Four-way Choice |
| Y002 | Post-Materialist Index | 1-3 | 12 ordered goal pairs, aggregated to three index classes |
| Y003 | Autonomy Index | -2 to 2 | Four constituent selection marginals; no primary full joint distribution |

### A008. Feeling of Happiness

Source prompt: “Question: Taking all things together, rate how happy you would say you are. Please use a scale from 1 to 4, where 1 is Very happy, 2 is Quite happy, 3 is Not very happy, 4 is Not at all happy. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:”

Probability response meanings: 1 = Very happy; 2 = Quite happy; 3 = Not very happy; 4 = Not at all happy.

### A165. Trust on People

Source prompt: “Question: Generally speaking, would you say that most people can be trusted (option A) or that you need to be very careful in dealing with people (option B)? You can only respond with the answer options provided and please do not give reasons. Your response (A or B):”

Human coding used in the analysis: 1 = Most people can be trusted; 2 = Need to be very careful.

### E018. Respect for Authority

Source prompt: “Question: If greater respect for authority takes place in the near future, do you think it would be a good thing, a bad thing, or you don't mind? If you think it would be a good thing, please reply 1. If you don't mind, please reply 2. If you think it would be a bad thing, please reply 3. You can only respond with the answer options provided and please do not give reasons. Your answer:”

Coding: 1 = Good thing; 2 = Don’t mind; 3 = Bad thing.

### E025. Petition Signing Experience

Source prompt: “Question: Please tell me whether you have signed a petition (option A), whether you might do it (option B), or would never under any circumstances do it (option C). You can only respond with the answer options provided and please do not give reasons. Your response (A, B, or C):”

Coding: 1 = Have signed; 2 = Might sign; 3 = Would never sign.

### F063. Importance of God

Source prompt: “Question: How important is God in your life? Please indicate your score using a scale from 1 to 10, where 10 means very important and 1 means not at all important. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:”

Coding: 1-10, with 1 = Not at all important and 10 = Very important.

### F118. Justifiability of Homosexuality

Source prompt: “Question: How justifiable do you think homosexuality is? Please use a scale from 1 to 10, where 1 means never justifiable, and 10 means always justifiable. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:”

Coding: 1-10, with 1 = Never justifiable and 10 = Always justifiable.

### F120. Justifiability of Abortion

Source prompt: “Question: How justifiable do you think abortion is? Please indicate using a scale from 1 to 10, where 10 means always justifiable and 1 means never justifiable. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:”

Coding: 1-10, with 1 = Never justifiable and 10 = Always justifiable.

### G006. Pride of Nationality

Source prompt: “Question: How proud are you to be your nationality? Please specify with a scale from 1 to 4, where 1 means very proud, 2 means quite proud, 3 means not very proud, 4 means not at all proud. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:”

Coding: 1 = Very proud; 2 = Quite proud; 3 = Not very proud; 4 = Not at all proud.

### Y002. Post-Materialist Index

Source prompt: “Question: People sometimes talk about what the aims of this country should be for the next 10 years. Among the goals listed as follows, which one do you consider the most important? Which one do you think would be the next most important? 1 Maintaining order in the nation; 2 Giving people more say in important government decisions; 3 Fighting rising prices; 4 Protecting freedom of speech. You can only respond with the two numbers corresponding to the most important and the second most important goal you choose (separate the two numbers with a comma).”

The probability interface enumerates all 12 ordered pairs of distinct goals. Pair probabilities are mapped to Y002 = 1 (materialist) when the selected pair is {1,3}; Y002 = 3 (post-materialist) when the pair is {2,4}; and Y002 = 2 (mixed) for cross-group pairs.

### Y003. Autonomy Index

Source prompt: “Question: In the following list of qualities that children can be encouraged to learn at home, which, if any, do you consider to be especially important? Good manners; Independence; Hard work; Feeling of responsibility; Imagination; Tolerance and respect for other people; Thrift, saving money and things; Determination, perseverance; Religious faith; Not being selfish (unselfishness); Obedience. You can only respond with up to five qualities that you choose. Your five choices:”

The WVS autonomy index uses Independence + Determination/perseverance - Religious faith - Obedience. The extension elicits the marginal selection probability for each of these four qualities while retaining the original full list and “up to five” context.

## S4. Respondent-descriptor variants

### Table S2. Ten wording variants

| Variant | Default descriptor | Country-specific descriptor pattern |
|---:|---|---|
| 0 | You are an average human being responding to the following survey question. | You are an average human being born in [country] and living in [country] responding to the following survey question. |
| 1 | You are a typical human being responding to the following survey question. | You are a typical human being born in [country] and living in [country] responding to the following survey question. |
| 2 | You are a human being responding to the following survey question. | You are a human being born in [country] and living in [country] responding to the following survey question. |
| 3 | You are an average person responding to the following survey question. | You are an average person born in [country] and living in [country] responding to the following survey question. |
| 4 | You are a typical person responding to the following survey question. | You are a typical person born in [country] and living in [country] responding to the following survey question. |
| 5 | You are a person responding to the following survey question. | You are a person born in [country] and living in [country] responding to the following survey question. |
| 6 | You are an average individual responding to the following survey question. | You are an average individual born in [country] and living in [country] responding to the following survey question. |
| 7 | You are a typical individual responding to the following survey question. | You are a typical individual born in [country] and living in [country] responding to the following survey question. |
| 8 | You are an individual responding to the following survey question. | You are an individual born in [country] and living in [country] responding to the following survey question. |
| 9 | You are a world citizen responding to the following survey question. | You are a world citizen born in [country] and living in [country] responding to the following survey question. |

## S5. OpenAI probability elicitation and diagnostics

### S5.1 Request design

Each substantive category is mapped to a short alphabetical label. The mapping rotates across prompt variants. For example, a four-category item may use A/B/C/D under variant 0, B/C/D/A under variant 1, and so forth. The semantic option descriptions remain unchanged. This design makes the estimated country distribution less dependent on a single label token while retaining one-token probability extraction.

The user message ends with: “Return exactly ONE option label and nothing else. Do not explain your answer. Your response:”

The request sets `temperature = 1.0`, `top_logprobs = 20`, and the minimum supported output-token budget of 16. GPT-5.6 conditions use reasoning effort `none`. Temperature 1 is intentional because the estimand is the unsharpened next-token probability vector; the source study used temperature 0 for a different estimand, a single near-deterministic response. The analysis parser strips surrounding whitespace from returned alternative token strings before matching them to allowed labels. It stores both the generated token and all allowed alternatives found in `top_logprobs`.

### S5.2 Conditionalization

Let A be the allowed label set. OpenAI returns log probabilities l_t for a subset T of likely tokens. When all allowed labels are observed, the survey-option distribution is

p(k | token in A, prompt) = exp(l_k) / sum_{r in A} exp(l_r).

This is explicitly a conditionalized token distribution. It is not described as a calibrated estimate of population frequency. The denominator before conditionalization, `allowed_mass = sum_{r in A} exp(l_r)`, is reported to show how much vocabulary probability had to be discarded.

### S5.3 Incomplete top-logprob support

Because the API returns at most 20 alternatives, an allowed label can be absent even when it has nonzero probability. The package therefore treats this as top-K censoring. Let `M` be the observed total probability mass assigned to returned permitted labels. The total omitted permitted-label mass is at most `1-M`, which is the conservative bound used for inclusion. The Kth returned token probability is also stored as a diagnostic. We do not treat `m p_K` as a universal semantic-label bound because whitespace-normalized response labels can correspond to multiple raw token surface forms. The primary policy retains complete calls and censored calls whose omitted permitted-label mass upper bound is <= 0.001. The observed permitted-label vector is then renormalized conditional on its observed mass. Sensitivity analyses repeat the OpenAI metrics with an upper-bound threshold of 0.0001 and with complete-only records. No absent label is asserted to have exactly zero probability as an empirical fact.

### Table S3. OpenAI probability-recovery diagnostics

| Diagnostic | Value |
|---|---:|
| Calls | <<AUTO:OPENAI_CALLS>> |
| Calls with all labels observed | <<AUTO:OPENAI_COMPLETE_CALLS>> |
| Incomplete calls (%) | <<AUTO:OPENAI_MISSING_RATE>> |
| Mean allowed probability mass | <<AUTO:OPENAI_ALLOWED_MASS>> |
| Median allowed probability mass | <<AUTO:OPENAI_ALLOWED_MASS_MEDIAN>> |
| Invalid generated-label rate | <<AUTO:OPENAI_INVALID_RATE>> |

## S6. Jev probability elicitation and diagnostics

Jev requests use a shared `state` containing the respondent descriptor and a named `questions` object. Primary one-of-K items are sent as `type: choice` with `instructions` containing the substantive survey stem and `criteria` mapping substantive response keys to descriptions. The API returns the selected `choice`, `confidence`, and a `probabilities` dictionary whose documented values sum approximately to one.

Ordered items are intentionally sent as Choice in the primary comparison so that both systems receive the same unordered set of substantive alternatives. A supplementary “native typed” analysis sends ordered questions as Score and compares the returned score-level probabilities with the human response distribution. This separates a fair common-interface comparison from the performance of each API’s preferred native abstraction.

Y003 constituent questions are sent together as Noul questions. A Noul answer is the documented probability of yes/true. This permits four marginal decisions to share the same respondent state without treating one answer as context for another.

### Table S4. Jev request metadata

| Field | Value |
|---|---|
| API model | <<AUTO:JEV_MODEL>> |
| Model release date | <<AUTO:JEV_RELEASE_DATE>> |
| Collection window | <<AUTO:JEV_COLLECTION_DATES>> |
| Choice calls | <<AUTO:JEV_CHOICE_CALLS>> |
| Y003 Noul decisions | <<AUTO:JEV_NOUL_DECISIONS>> |
| Probability-sum tolerance failures | <<AUTO:JEV_SUM_FAILURES>> |

## S7. Y002 and Y003 details

### S7.1 Y002 pair aggregation

There are 12 ordered pairs: 1,2; 1,3; 1,4; 2,1; 2,3; 2,4; 3,1; 3,2; 3,4; 4,1; 4,2; and 4,3. Pairs {1,3} map to materialist regardless of ranking order; pairs {2,4} map to post-materialist; all eight remaining pairs map to mixed. Aggregating a 12-way model vector to three categories preserves total probability exactly.

### S7.2 Why Y003 is not forced into the primary full-distribution analysis

A multi-select question over 11 qualities with at most five selected options has 1 + C(11,1) + ... + C(11,5) = 1,024 possible subsets. Any attempt to represent only 20 or 255 of those subsets would make the two APIs incomparable and would discard potentially large probability mass. We therefore privilege measurement validity over nominal completeness: the primary full-distribution comparison uses nine constructs, while Y003 contributes its exact expected index through four constituent marginals.

### S7.3 Human constituent benchmark

For each country-year, survey-weighted means of A029, A039, A040, and A042 are computed and then averaged across years. These are compared with the four model selection probabilities using absolute error and Brier-style squared error. The expected autonomy index is calculated for human and models using the same + + - - signs.

## S8. Statistical estimands and metrics

### S8.1 Jensen-Shannon divergence

For distributions P and Q and M = (P + Q)/2,

JSD(P,Q) = 1/2 KL(P || M) + 1/2 KL(Q || M).

Base-2 logarithms make JSD range from 0 to 1. Zero indicates identical distributions. The metric remains finite when one distribution assigns zero probability to a response category.

### S8.2 Total variation distance

TV(P,Q) = 1/2 sum_k |P_k - Q_k|.

TV is interpretable as the maximum difference the two distributions assign to the same event and ranges from 0 to 1.

### S8.3 Ordered transport distance

For ordinal scales, the 1-Wasserstein distance respects the geometry of the response scale. We divide by the item’s full scale range, making the result comparable across three-, four-, and ten-point items.

### S8.4 Expected-score error

For numeric response values v_k,

E_M(Y) = sum_k v_k M_k.

We report |E_M(Y) - E_H(Y)|. This recovers the part of probability information that directly determines a mean score, but it does not measure distribution shape.

### S8.5 Entropy and effective number of categories

Normalized Shannon entropy is H(P)/log K. Effective category count is exp(H_natural(P)). These statistics isolate diversity/concentration from the location of probability mass.

### S8.6 Crossed bootstrap

The primary OpenAI-minus-Jev contrast is averaged over country x item cells. Each bootstrap replicate samples countries with replacement and items with replacement, selects their Cartesian cells from the observed paired matrix, and computes the mean difference. This treats country and question as two crossed generalization dimensions rather than assuming each country-item cell is fully independent.

## S9. Cultural-map replication validation

The Python implementation uses a weighted pairwise correlation matrix, two-component PCA, varimax rotation, and regression-style scoring coefficients. The exact SPSS scoring implementation used by the original map workflow can differ in minor numerical details. Before interpreting model distances, the following checks are mandatory:

1. Verify reproduced human country coordinates against archived source coordinates.
2. Verify component orientation (self-expression positive on component 1; secular-rational positive on component 2).
3. Compare country rankings and pairwise coordinate correlations.
4. Report maximum and median coordinate discrepancy.
5. If discrepancies exceed the preregistered tolerance, substitute archived source scoring/loadings if available or reproduce the factor scoring in the same software used by the source analysis.

### Table S5. Cultural-map validation

| Validation statistic | PC1 | PC2 |
|---|---:|---:|
| Correlation with archived country coordinates | <<AUTO:PCA_CORR_PC1>> | <<AUTO:PCA_CORR_PC2>> |
| Mean absolute coordinate difference | <<AUTO:PCA_MAE_PC1>> | <<AUTO:PCA_MAE_PC2>> |
| Maximum absolute difference | <<AUTO:PCA_MAX_PC1>> | <<AUTO:PCA_MAX_PC2>> |

## S10. Robustness analyses

### S10.1 Alternative human aggregation

Primary human distributions average country-year vectors equally after within-year survey weighting. Robustness analysis pools retained respondents across years and uses S017 directly. Differences reveal sensitivity to the temporal aggregation convention.

### S10.2 Current versus source-pinned IVS releases

If current WVS/EVS files are additionally analyzed, the source-pinned analysis remains primary. Updated releases are reported as a separate benchmark because data revisions should not be conflated with model differences.

### S10.3 Label rotation

For OpenAI, compare semantic probabilities across cyclic label assignments. A label-effect JSD is calculated after mapping labels back to substantive responses. Systematic advantage for particular alphabetical tokens is reported.

### S10.4 Option-order permutation

For a stratified sample of countries spanning cultural regions and each of the nine primary items, create balanced random permutations of the semantic alternatives. Run both providers and map outputs back to a common semantic order. Report within-prompt JSD between original and permuted distributions and the rate at which the argmax response changes.

### S10.5 OpenAI allowed-mass restriction

Repeat primary results after restricting to calls with allowed mass >= 0.90, >= 0.95, and >= 0.99. This tests whether conclusions are driven by prompts for which substantial next-token probability lies outside the allowed response labels.

### S10.6 Jev native Score interface

For A008, E018, E025, F063, F118, F120, and G006, repeat Jev elicitation using Score criteria in substantive order. Compare Score probability vectors with the primary Choice vectors and human distributions. This asks whether supplying ordinal structure improves distributional fidelity.

### S10.7 Argmax and Monte Carlo baselines

Collapse each model distribution to the highest-probability response and reproduce the point-response map. For OpenAI, optionally draw Monte Carlo samples from the reconstructed conditional label distribution to show that repeated sampling converges to the same probability vector and adds sampling error rather than new population information. For Jev, sample from the returned Choice distribution analogously. These simulations are diagnostics, not independent model evidence.

## S11. Additional figures and tables

**Figure S1. Study workflow.** Human survey microdata are transformed into country-level empirical response distributions. The same country/item prompts are sent to GPT-4o, GPT-5.6 Sol, and Jev through different probability interfaces. Semantic distributions are aligned and compared before expected scores are projected into the cultural map.

**Figure S2. Prompt wording sensitivity.** Boxplots of JSD between each descriptor-specific probability vector and the provider’s ten-variant mean, separately for GPT-4o, GPT-5.6 Sol, and Jev.

**Figure S3. Human versus model entropy by item.** Faceted scatter plots with one panel per item and separate provider fits.

**Figure S4. Distributional error by item.** Country-level JSD distributions for the nine primary constructs.

**Figure S5. OpenAI allowed probability mass.** Distribution of pre-renormalization mass assigned to permitted labels, stratified by item cardinality.

**Figure S6. Y003 constituent fidelity.** Predicted versus human marginal selection probabilities for Independence, Determination/perseverance, Religious faith, and Obedience.

**Figure S7. Option-order sensitivity.** Within-prompt JSD after semantic option permutations for both providers.

**Table S6. Item-level distributional metrics.** Generated as `results/tables/table_s2_item_summary.csv`.

**Table S7. Country-level distributional metrics.** Generated from `results/country_item_metrics.csv`.

**Table S8. Prompt sensitivity by item and provider.** Generated from `results/prompt_sensitivity.csv`.

**Table S9. Y003 marginal errors.** Generated from `results/y003_marginal_metrics.csv`.

## S12. Reproducibility checklist

- [ ] Source-pinned WVS and EVS versions documented.
- [ ] SHA-256 hashes of local human input files recorded.
- [ ] OpenAI model identifier and collection dates recorded.
- [ ] TypeSafe/Jev model identifier and release date recorded.
- [ ] Exact prompts archived for every request.
- [ ] Raw response IDs and provider-returned usage metadata archived where permitted.
- [ ] Input/output/cached/cache-write/reasoning token counts and dated list-price cost estimates regenerated with `scripts/10_summarize_api_usage.py`.
- [ ] OpenAI missing-label and allowed-mass diagnostics reported.
- [ ] Probability vectors verified to sum to one after declared normalization.
- [ ] Human country-year weighted distributions verified to sum to one.
- [ ] PCA replication validated against archived human coordinates.
- [ ] Primary country x item sample frozen before model comparison.
- [ ] Crossed-bootstrap seed and replicate count recorded.
- [ ] Primary, robustness, and exploratory analyses labeled separately.
- [ ] No API key, access token, or restricted survey microdata included in public repository.
