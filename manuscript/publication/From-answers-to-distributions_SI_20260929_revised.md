Text-only review companion. Equations, tables and embedded figures are omitted here; the DOCX is the complete manuscript.

# Supplementary information

## Can AI uncertainty recover human population variation? Token uncertainty, decision uncertainty, and cross-cultural survey responses

Steven J. Bickley, Ho Fai Chan, Arian Mashhady, Son Tran, and Benno Torgler

Corresponding author: Steven J. Bickley
Email: s.bickley@qut.edu.au

## Contents

Supplementary methods and results; Tables S1–S16; Figures S1–S11; supplementary references.

### Study scope and data provenance

The study compares nine finite-response distributions and four Y003 marginals across 107 countries and territories. Human estimates use WVS Trend v4.1.0 and EVS ZA7503 v3.0.0, common waves 5–7, and years 2005–2022. Within country-years, valid responses are weighted by S017; country-year probability vectors are then averaged equally. The frozen country universe uses S003 identifiers and excludes Egypt, Kuwait, Qatar, Tajikistan, and Uzbekistan. The prepared benchmark contains 392,832 respondent records. This updates the WVS release relative to Tao et al. (1), rather than reproducing the original data release exactly.

### Probability representations

GPT-4o uses gpt-4o-2024-05-13 and Sol uses gpt-5.6-sol with reasoning effort none. Both expose next-token log probabilities at temperature 1.0 with up to 20 alternatives. Permitted labels are mapped back to substantive response categories before averaging. Nine primary items use three cyclic label assignments per descriptor; each binary Y003 marginal uses two. Jev uses the archived served identifier jev-1.13.0 and returns probabilities over declared Choice alternatives. Its four Y003 decisions are batched within a request. Ten respondent descriptors are evaluated for each country and for an unconditioned target. The primary Jev collection therefore comprises 10,800 requests; each OpenAI collection comprises 37,800. Exact constructs and descriptor wording appear in Tables S1 and S2.

### Incomplete probability support

An absent OpenAI label is censored, rather than known to have exactly zero probability. The analysis conditions on the observed permitted-label mass and retains incomplete requests only when a conservative upper bound on total omitted permitted-label mass is at most 0.001. Sensitivity policies use 0.0001 or require all permitted labels. Table S3 reports request-level diagnostics, including unconditioned and Y003 requests; Table S4 reports country-item outcomes after each policy. Different policies change both surviving requests and cell coverage, so their marginal means are not paired estimates of a pure policy effect.

### Distributional comparisons and uncertainty

JSD uses base-2 logarithms and is bounded by zero and one. Total variation is half the sum of absolute category-probability differences. Ordered-item Wasserstein distance is divided by the full response-scale range; it is unavailable for unordered trust (A165). Expected-score error remains in the item’s original units. Normalized entropy is Shannon entropy divided by log2 of category count. The argmax comparator assigns mass one to the first highest-probability substantive category in configured order, using exactly the same aggregated probability vector. Paired model contrasts and mean country-conditioning gains use a crossed bootstrap with 5,000 replicates and seed 20260923, independently resampling countries and items. Wilcoxon tests are secondary cell-level summaries and do not account for the crossed dependence structure.

### Country conditioning and the human baseline

For target country c and item j, default gain is JSD(Hcj, Mdefault,j) minus JSD(Hcj, Mcj). The LOCO human distribution is the equal-country mean of all other countries for item j; the target country is omitted before averaging. LOCO gain is JSD(Hcj, Hminus-c,j) minus JSD(Hcj, Mcj). Each gain is paired within cell, and percentages improved count strictly positive gains. The LOCO benchmark averages over the model’s available cells when a model-specific mean is reported. It uses survey data unavailable in the model prompt and is an information benchmark, not a controlled comparison of identical input sources.

### Entropy structure

Pooled, item-fixed-effect, country-fixed-effect, and two-way-fixed-effect regressions relate model entropy to human entropy. Covariance estimates cluster by country and item; reported 95% intervals use normal 1.96 critical values. There are only nine item clusters, limiting asymptotic inference. Negative variance estimates are treated as undefined, not zero. Fixed-effect failures do not fall back to pooled slopes. Two-way residuals are obtained by least-squares projection on country and item indicators, including for unbalanced panels. Within-item and within-country correlations are summarized through equal-group Fisher-z means as well as medians. Table S10 separates regression slopes, correlations, and standard-deviation ratios; these quantify different features of uncertainty.

### Prompt label and order sensitivity

Country-conditioned prompt sensitivity compares each retained descriptor-specific vector, after averaging retained label assignments, with its model-country-item mean. At least two descriptors are required. Label sensitivity compares each retained semantic label-vector with its mean within model, country, item, and descriptor, requiring at least two assignments. Singleton groups have unavailable sensitivity and are excluded from summary denominators. The unconditioned target is excluded from both summaries. In the 12-country option-order experiment, only comparisons to prespecified ordering 0 are valid; reference and alternative must both survive censoring. An excluded reference is never replaced. Tables S8, S13, and S14 report valid counts and the coverage audit is retained in results/option_order_coverage.csv. Sol has no reference-based F120 comparisons.

### Y002 and Y003

Y002 enumerates 12 ordered pairs of distinct goals. Pairs containing goals 1 and 3 are materialist, those containing 2 and 4 are post-materialist, and all mixed pairs map to the middle category. Y003 permits up to five of eleven qualities, giving 1,024 possible subsets including the empty set. Four marginal probabilities suffice for the expected autonomy index: P(independence) + P(determination) - P(religious faith) - P(obedience). This follows by linearity of expectation without assuming independence. Y003 is excluded from the nine-item JSD analysis; its four marginal errors appear in Table S9.

### Cultural-map projection and reconstruction

Ten expected scores are standardized using human-derived parameters, projected through the weighted pairwise-correlation PCA with varimax rotation, and rescaled as PC1′ = 1.81 PC1 + 0.38 and PC2′ = 1.61 PC2 - 0.01. Human and model positions share this transformation. Expected-score and aggregated-argmax profiles cover 107 countries for GPT-4o and Jev and 91 for Sol. A variant-wise modal reconstruction averages label assignments within descriptor, selects modal item responses, thresholds Y003 marginals at 0.5, projects complete profiles, and then averages their coordinates. It covers only 43 Sol countries and lacks a complete Sol default profile. Tables S15 and S16 distinguish these representations and samples. They do not establish exact replication of Tao et al.’s direct temperature-zero responses. Figure 1 uses the source archive’s S003 region assignments and exact palette; classifications only control display colours.

### Computational accounting and reproduction

The archived computational ledger comprises 95,186 distinct API requests, 20,713,572 input tokens, 1,215,251 output tokens, and 21,928,823 total tokens, including option-order and exploratory native-Score requests. Estimated cost is US$44.87 under the 25 September 2026 list-price snapshot. Provider-reported dollar charges are unavailable; the estimate is not an invoice. Jev requests are deduplicated by request identifier before counting batched decisions. Rebuilding analyses, figures, tables, and this document from archived data requires no new provider calls. The native-Score collection is exploratory and does not enter the primary Choice-probability comparisons.

### Interpretation of supplementary tables

Counts refer to the unit named in each table. NA means undefined or unavailable, not zero. JSD, probability errors, and normalized entropy are dimensionless; cultural-map distance uses the rescaled coordinate units. Results are descriptive unless an interval is explicitly provided. The complete machine-readable columns, request coverage, country-level entropy diagnostics, and analysis provenance remain in the accompanying CSV and JSON files. The formatted tables below emphasize reported estimands and preserve all model, item, country, and representation groups.

Table S1. Survey constructs and response representation

The nine finite-response items enter the primary JSD analysis. Y003 is analysed through four marginals.

### Complete source question wording

### A008  Feeling of Happiness

Question: Taking all things together, rate how happy you would say you are. Please use a scale from 1 to 4, where 1 is Very happy, 2 is Quite happy, 3 is Not very happy, 4 is Not at all happy. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:

### A165  Trust on People

Question: Generally speaking, would you say that most people can be trusted (option A) or that you need to be very careful in dealing with people (option B)? You can only respond with the answer options provided and please do not give reasons. Your response (A or B):

### E018  Respect for Authority

Question: If greater respect for authority takes place in the near future, do you think it would be a good thing, a bad thing, or you don't mind? If you think it would be a good thing, please reply 1. If you don't mind, please reply 2. If you think it would be a bad thing, please reply 3. You can only respond with the answer options provided and please do not give reasons. Your answer:

### E025  Petition Signing Experience

Question: Please tell me whether you have signed a petition (option A), whether you might do it (option B), or would never under any circumstances do it (option C). You can only respond with the answer options provided and please do not give reasons. Your response (A, B, or C):

### F063  Importance of God

Question: How important is God in your life? Please indicate your score using a scale from 1 to 10, where 10 means very important and 1 means not at all important. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:

### F118  Justifiability of Homosexuality

Question: How justifiable do you think homosexuality is? Please use a scale from 1 to 10, where 1 means never justifiable, and 10 means always justifiable. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:

### F120  Justifiability of Abortion

Question: How justifiable do you think abortion is? Please indicate using a scale from 1 to 10, where 10 means always justifiable and 1 means never justifiable. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:

### G006  Pride of Nationality

Question: How proud are you to be your nationality? Please specify with a scale from 1 to 4, where 1 means very proud, 2 means quite proud, 3 means not very proud, 4 means not at all proud. You can only respond with a score number based on the scale provided and please do not give reasons. Your score number:

### Y002  Post-Materialist Index

Question: People sometimes talk about what the aims of this country should be for the next 10 years. Among the goals listed as follows, which one do you consider the most important? Which one do you think would be the next most important? 1 Maintaining order in the nation; 2 Giving people more say in important government decisions; 3 Fighting rising prices; 4 Protecting freedom of speech. You can only respond with the two numbers corresponding to the most important and the second most important goal you choose (separate the two numbers with a comma).

### Y003  Autonomy Index

Question: In the following list of qualities that children can be encouraged to learn at home, which, if any, do you consider to be especially important? Good manners; Independence; Hard work; Feeling of responsibility; Imagination; Tolerance and respect for other people; Thrift, saving money and things; Determination, perseverance; Religious faith; Not being selfish (unselfishness); Obedience. You can only respond with up to five qualities that you choose. Your five choices:

Table S2. Ten respondent-descriptor variants

The literal {country} field is replaced with the frozen country or territory name.

Table S3. OpenAI request-level probability diagnostics

All primary requests, including the default target and Y003 constituents. Allowed mass is measured before conditional normalization. The maximum bound includes excluded requests.

Table S4. Sensitivity to the OpenAI censoring policy

Means use each policy’s retained cells. Coverage and probability aggregation both change across policies; these are not paired policy effects.

Table S5. Paired full-distribution and argmax fidelity

Gain is argmax JSD minus full-distribution JSD. Values are descriptive paired summaries.

Table S6. Distributional metrics by item

n is the number of countries. Wasserstein is unavailable for unordered A165. Expected-score error uses original item units.

Table S7. Distributional metrics for every country and model

All 107 countries and three models are retained. Counts are observed primary items, with a maximum of nine.

Table S8. Respondent-wording sensitivity by item

Country-conditioned targets only. Singleton descriptor groups contribute to retained counts but not valid sensitivity counts. JSD is measured from the model-country-item mean.

Table S9. Y003 marginal probability errors

Probabilities refer to selection of the individual quality. No joint-selection distribution is inferred.

Table S10. Entropy level variation and association

Fisher means give equal weight to available group correlations after Fisher-z transformation. SD is the standard deviation across observed cells, not the mean entropy within distributions.

### Regression specifications

FE denotes fixed effects. Covariance clusters by country and item; normal-approximation intervals use only nine item clusters. Slopes and p values are descriptive evidence subject to that limitation.

Table S11. Within-item entropy associations

Associations vary across countries within each item; slopes are descriptive and have no interval here.

Table S12. Country-conditioning gains by item

Gains are baseline minus model JSD; positive favours country conditioning. Model shift is JSD between conditioned and default model distributions. The corresponding LOCO human mean equals country JSD plus LOCO gain; complete values are retained in the CSV.

Table S13. OpenAI semantic label-assignment sensitivity

At least two assignments must survive within a model-country-item-descriptor group. Singleton vectors are counted as retained but have undefined sensitivity. Default targets are excluded.

Table S14. Sensitivity to answer-option order

Reference is always order 0. Both requests must be retained. Up to 36 comparisons per item are available across 12 countries. No Sol F120 comparison has a valid reference; its sensitivity is unavailable.

Table S15. Cultural-map distance by representation

Distances compare country-conditioned model and human coordinates. Samples differ by representation, especially for Sol’s variant-wise modal reconstruction.

### Expected-score and argmax results on the common 91-country subset

Table S16. Cultural prompting and the Tao benchmark

The external source row reports published point-response results from Tao et al. (1); remaining rows are current-study estimates. Within each row the country set is paired. Variant-wise modal uses marginal Y003 reconstruction and temperature-one probabilities, so it is not an exact source replication. Sol has no complete default variant-wise modal profile and therefore no such prompting row.

Figure S1. Paired distributional fidelity. Each point is one of 946 country-item cells observed for both Sol and Jev. Axes show JSD from the same human distribution. Points below the equality line favour Jev; points above favour Sol. Points are partially transparent to show density.

Figure S2. Respondent-wording sensitivity. Empirical cumulative distributions of JSD between each retained descriptor-specific vector and its model-country-item mean. Label assignments are averaged within descriptor before comparison. The unconditioned target is excluded. Cells with fewer than two retained descriptors have undefined sensitivity and do not contribute; retained comparison counts appear in the legend. The full observed range is displayed.

Figure S3. Response-label sensitivity. Mean JSD between each retained OpenAI label assignment and its within-descriptor mean, after remapping labels to substantive responses. The unconditioned target is excluded. At least two label assignments must survive the primary censoring policy; singletons are treated as unavailable, not zero sensitivity. Parentheses give the number of retained label-vector comparisons. The near-zero Sol values are conditional on the surviving comparisons.

Figure S4. Option-order sensitivity. Mean JSD between alternative answer orderings and the prespecified reference ordering, rep=0, after substantive remapping. Both requests must survive the primary censoring policy. Parentheses show comparison counts; up to three comparisons are available per country-item cell in the 12-country experiment. Sol has no valid reference-based F120 comparisons, shown as NA. A later retained ordering is never substituted for an excluded reference.

Figure S5. Distributional error by item. Mean country-conditioned JSD from human response frequencies, with the number of countries shown in parentheses. The colour scale spans the theoretical JSD range from zero to one. All available cells enter each model’s mean; cross-model inferential comparisons use matched cells.

Figure S6. OpenAI probability-recovery coverage. Percentage of all 37,800 primary requests per OpenAI condition retained under the primary omitted-mass bound of 0.001, the stricter bound of 0.0001, and the requirement that every permitted label be observed. Counts include the unconditioned target and Y003 constituent requests. Retention is evaluated at the request level before averaging probabilities.

Figure S7. Fidelity of the four autonomy-index marginals. Mean absolute error between predicted and human selection probabilities for each constituent, averaged across 107 countries per model. These are four marginal probabilities; the analysis does not reconstruct the joint distribution of selections or assume independence.

Figure S8. Cultural-map distance under alternative probability representations. Blue uses expected scores from averaged probabilities; pink/purple uses the argmax of the final averaged probabilities; gold averages projected modal profiles across complete prompt variants. Boxes, whiskers, and outliers follow the convention in Figure 1. Sample sizes are shown below each box. The variant-wise modal reconstruction yields only 43 country-conditioned Sol profiles and no complete unconditioned Sol profile. Its distribution therefore has different coverage and cannot support the paired prompting comparison. Common-country expected-score and aggregated-argmax results appear in Table S15.

Figure S9. Within-item entropy association. Pearson correlations between model and human normalized entropy across countries for each survey item. The fixed colour scale spans -1 to 1; parentheses give country counts. These descriptive associations distinguish variation across countries within a question from pooled differences across questions.

Figure S10. Country-conditioning gain by item. Mean JSD from the unconditioned model minus mean JSD from the country-conditioned model, evaluated against the same target-country human distribution. Blue denotes improvement and red denotes deterioration; the colour scale is symmetric around zero. Parentheses show country counts. Values are descriptive item-specific means.

Figure S11. Raw entropy diagnostic. Each panel plots model normalized entropy against human normalized entropy for every observed country-item cell, with identical axes across models. The dashed line denotes exact entropy equality. Facets separate overlapping model clouds; pooled and fixed-effect associations are summarized in Figure 4 and Table S10.

## Supplementary references

1. Tao Y, Viberg O, Baker RS, Kizilcec RF. Cultural bias and cultural alignment of large language models. PNAS Nexus. 2024;3:pgae346. doi:10.1093/pnasnexus/pgae346. Source analysis and cultural-region lookup: https://osf.io/7sj3w/.

2. Haerpfer C, Inglehart R, Moreno A, et al., editors. World Values Survey Trend File 1981–2022. Version 4.1.0. JD Systems Institute and WVSA Secretariat. doi:10.14281/18241.27.

3. European Values Study. EVS Trend File 1981–2017, ZA7503. Version 3.0.0. GESIS Data Archive. doi:10.4232/1.14021.
