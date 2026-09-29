Text-only review companion. Equations, tables and embedded figures are omitted here; the DOCX is the complete manuscript.

# Can AI uncertainty recover human population variation? Token uncertainty, decision uncertainty, and cross-cultural survey responses

Steven J. Bickley1,2,3, Ho Fai Chan1,2,3, Arian Mashhady1,2, Son Tran3, & Benno Torgler1,2,3,4,5

1 School of Economics and Finance, Queensland University of Technology, Gardens Point, 2 George Street, Brisbane, QLD 4001, Australia

2 ARC Industrial Transformation Training Centre for Behavioural Insights for Technology Adoption, Queensland University of Technology, Brisbane, Australia

3 Panalogy Lab Pty Ltd, Brisbane, Australia

4 Institut für Schweizer Wirtschaftspolitik an der Universität Luzern (IWP), Switzerland

5 CREMA—Centre for Research in Economics, Management, and the Arts, Zürich, Switzerland

Corresponding author: Steven J. Bickley

Email: s.bickley@qut.edu.au 

Author Contributions: SJB, HFC and AM conceived the study. SJB developed the conceptual framework and study methodology. SJB conducted computational analyses, statistical modelling, validation, and reproducibility checks. SJB curated and harmonized the survey and model-generated data. SJB developed visualizations. SJB, HFC, AM and BT interpreted the findings and developed the theoretical implications. SJB wrote the original manuscript. All authors contributed to critical revision of the manuscript and approved the final version.

Competing Interest Statement: SJB, HFC and BT hold dual roles in Queensland University of Technology and Panalogy Lab Pty Ltd. This relationship is managed under QUT’s approved Conflict of Interest Management Plan. The authors declare no other competing interests.

Classification: Social Sciences — Psychological and Cognitive Sciences

Keywords: human values; artificial intelligence; cultural alignment; synthetic respondents; survey research

## Abstract

Human populations contain disagreement, yet a single artificial model is increasingly used to simulate them. Can uncertainty within one model recover variation across many people? Building on Tao et al.’s cross-cultural benchmark, we compare survey-weighted response distributions across 107 countries and territories with GPT-4o and GPT-5.6 Sol next-token probabilities and TypeSafe Jev decision probabilities. Mean Jensen-Shannon divergence is 0.214, 0.290, and 0.193, respectively. Retaining full probabilities substantially improves fidelity relative to the same vectors collapsed to modal answers. Country prompting also improves mean cultural-map location, but improves full response distributions in only 48.9%, 56.9%, and 69.9% of cells. All three models rarely outperform a leave-one-country-out human baseline. Jev most closely matches average human entropy, yet its entropy scarcely covaries with human disagreement. The GPT models have lower mean entropy and positive pooled associations with human entropy, but all country-and-item fixed-effect slope intervals include zero. Model uncertainty therefore contains population-level information without reproducing population heterogeneity. Cultural location, distributional fidelity, and the structure of disagreement are distinct evaluation targets.

## Significance Statement

A model probability describes uncertainty within one artificial system; a survey distribution describes differences among people. Across 107 countries and nine cultural-value constructs, retaining full AI probabilities preserves more information than selecting only modal answers. Yet improved cultural-map location does not guarantee better response distributions, and country-conditioned models rarely beat a simple average of other countries’ human responses. Matching the average amount of disagreement also fails to establish that a model identifies where people disagree. Synthetic-population research should assess cultural location, complete response distributions, and the pattern of disagreement separately.

## Introduction

Populations disagree. People who share a country, institution, demographic category, or cultural environment can nevertheless give different answers to the same question. For social research, this variation is not simply noise to be averaged away. The amount and structure of disagreement can reveal contested norms, minority positions, polarized judgments, and differences in the experiences and commitments that people bring to collective life.

Artificial intelligence is increasingly used to simulate those populations. Researchers ask large language models (LLMs) to answer surveys, emulate experimental participants, approximate subgroup attitudes, and anticipate aggregate behavioral outcomes (2–5,15). Much of this work begins with a single artificial system and asks it to stand in for many heterogeneous humans. That creates a basic statistical question: when one model is uncertain between several answers, can that uncertainty substitute for disagreement across many people?

The temptation is understandable. A human survey distribution and a model probability distribution can have exactly the same mathematical form. If 20%, 50%, and 30% of respondents choose three alternatives, the population can be represented by the vector . If a model assigns probabilities 0.20, 0.50, and 0.30 to the same alternatives, the two vectors are numerically identical. But identical numbers need not describe identical processes. Survey frequencies arise because different people select different responses. A language-model distribution arises because one model assigns different probabilities to possible textual continuations. A decision model may instead express uncertainty directly over a predefined set of alternatives.

The distinction matters because most synthetic respondent research has historically observed point answers. A model receives a persona or population descriptor, generates one response, and repeated generations are treated analogously to repeated observations from people. Yet variation over repeated model generations is not automatically variation across humans. Human disagreement reflects differences in biography, institutions, beliefs, values, information, and interpretation, together with within-person uncertainty and measurement processes. Sampling the same artificial system repeatedly instead samples a generative mechanism whose stochasticity need not preserve those sources of human variation (2,3,15).

Recent research has therefore begun to move from answers to distributions. First-token probabilities can be compared directly with empirical response frequencies, models can be specialized to predict group-level survey distributions, and model probabilities can be evaluated against distributions of human disagreement (5,6). This shift is promising because a complete probability vector retains information discarded by a modal prediction. It also introduces a deeper measurement problem. A vector of model probabilities may look like a population distribution without having the same interpretation.

Several adjacent literatures address pieces of this problem. Lee et al. (6) compare sampling- and log-probability-based model distributions with human disagreement in natural-language inference. Cao et al. (5) specialize LLMs using first-token probabilities to reproduce country-level survey response distributions. Xie et al. (3) evaluate population-level statistical realism more broadly and show that synthetic data often collapse toward overly typical profiles. Survey-method studies additionally show that model responses can change substantially with response-generation procedure, wording, labels, and option order (7,16–18). What remains less clear is whether uncertainty within a single model can be interpreted as between-person heterogeneity, whether this correspondence differs between lexical and explicitly typed decision probabilities, and whether matching average dispersion implies tracking where human disagreement actually occurs. We test those distinctions directly.

We call the implicit assumption behind such use the uncertainty substitution hypothesis: uncertainty within one model can serve as a statistical proxy for heterogeneity across people. The hypothesis does not require the two probability objects to arise from the same mechanism. It requires only that they coincide closely enough, across populations and questions, for model uncertainty to recover substantively important properties of the human distribution. This is ultimately an empirical proposition.

Formally, let a human population in country or territory  contain heterogeneous latent states  distributed according to . For survey item  and response , the population distribution is

This probability integrates variation across people. An autoregressive language model instead exposes a conditional distribution over textual continuations,

which can be mapped to substantive survey responses through controlled output labels. A decision-native model exposes a probability directly over declared alternatives,

These three objects can be placed on the same response support and compared numerically. Their semantics nevertheless remain distinct:  is between-person population heterogeneity,  is generative or lexical uncertainty within a language model, and  is decision uncertainty within a structured choice interface. Whether  or  approximates  is the empirical question.

This problem is related to, but distinct from, conventional probability calibration. Calibration asks whether events assigned a given probability occur with the corresponding long-run frequency (13,14). Here the target is not repeated realization of one uncertain event. It is the distribution of responses across different people. A model can therefore be well behaved as a probabilistic predictor while still failing to reproduce the social distribution it is being used to simulate.

The distinction also changes how synthetic populations should be evaluated. Matching a population mean is only one criterion. Two distributions can share the same expected response while differing markedly in concentration, tails, minority support, or multimodality. Likewise, a model could reproduce the average amount of disagreement across a dataset without identifying which particular populations and questions are consensual and which are divided. We therefore distinguish three increasingly demanding targets: (i) location, whether the model places expected responses appropriately; (ii) distributional shape, whether its full response probabilities resemble population frequencies; and (iii) heterogeneity structure, whether its uncertainty rises and falls across populations and questions in the same places that human disagreement does.

We test these distinctions using the cross-cultural benchmark developed by Tao et al. (1). Their study projected responses from several GPT generations into the Inglehart–Welzel World Cultural Map using ten constructs from the Integrated Values Surveys (IVS). Country-specific prompting often moved GPT point responses toward the corresponding national survey coordinates, demonstrating that model responses contain culturally patterned information. The source study evaluated 107 countries/territories and repeated each question under ten semantically similar respondent descriptors to reduce dependence on exact wording (1). We preserve that basic design but change the principal unit of analysis from which response the model selects to how probability is distributed over all permitted responses.

The cultural-values setting provides a demanding test. The benchmark spans happiness, interpersonal trust, authority, political participation, religion, moral judgments, national pride, materialist/post-materialist priorities, and child-rearing autonomy (1,10). Countries differ systematically on these measures, while substantial variation also remains within countries. The same model must therefore recover both geographic structure and population disagreement across questions that vary greatly in response cardinality and substantive content.

We compare three principal model conditions. GPT-4o provides a historical-generation anchor close to the most recent OpenAI model in Tao et al. (1). GPT-5.6 Sol provides a contemporary autoregressive comparison using the same probability-extraction procedure. TypeSafe Jev provides a contrasting decision interface in which probabilities are returned over explicitly declared alternatives rather than reconstructed from next-token probabilities (8,9). The comparison is not intended as an architectural horse race: training data, post-training, capacity, objectives, and serving infrastructure differ across systems. Instead, the three conditions let us observe how the uncertainty-substitution hypothesis behaves across model generations and probability interfaces.

The study makes three contributions. First, it distinguishes between-person heterogeneity, next-token uncertainty, and decision uncertainty, three mathematically comparable but generatively different probability objects that synthetic population research can easily conflate. Second, it measures the information gained by retaining uncertainty rather than reducing each model to its modal response. Third, it separates matching the average amount of human disagreement from recovering the social structure of disagreement across countries and questions. This latter distinction is especially important: knowing how uncertain a population is on average is not the same as knowing where disagreement actually occurs.

We organize the analysis around four questions. RQ1, distributional substitution: how closely do machine probability distributions reproduce survey-weighted human response distributions? RQ2, heterogeneity recovery: do machine probabilities reproduce not only the average level but also the cross-population structure of human disagreement? RQ3, population specificity: does conditioning a model on a country improve distributional fidelity relative to its unconditioned distribution and simple population-level baselines? RQ4, measurement robustness: how sensitive are inferred distributions to respondent wording, arbitrary response labels, option ordering, and incomplete top- probability support? As a secondary extension of Tao et al. (1), we also test whether retaining complete probability information changes cultural-map alignment. Together, these analyses ask whether uncertainty inside one artificial system can recover variation across many humans—and whether that uncertainty is genuinely population-specific rather than merely generically diffuse.

## Results

### Analysis coverage and probability recovery

The merged EVS/WVS file contained 666,907 historical observations. Restricting the benchmark to common waves 5–7 and calendar years 2005–2022 retained 392,832 respondent records. Harmonization identified 112 countries and territories before the five source-study exclusions, leaving 107 analysis targets and 963 possible country-item cells across the nine primary constructs. The run used WVS Trend v4.1 and EVS ZA7503 v3.0.0. It is a release-updated replication and extension of Tao et al. (1), whose earlier release yielded 393,536 observations.

GPT-4o returned every permitted label in 35,754 of 37,800 primary requests (94.6%); Sol did so in 1,922 requests (5.1%). The primary rule retained complete vectors and incomplete vectors whose unseen permitted-label mass was bounded above by 0.001. This retained 37,800 GPT-4o requests and 24,723 Sol requests (65.4%), yielding 963 and 946 country-item distributions, respectively. Jev supplied probabilities for every declared alternative; its 10,800 primary requests covered all 963 country-item cells and the autonomy marginals. Coverage and censoring diagnostics are reported in Tables S3 and S4.

### Cultural prompting improves mean cultural location

The unconditioned models occupy distinct positions in the human cultural map (Fig. 1a). Country prompting reduces mean expected-score distance from 2.558 to 1.562 for GPT-4o, from 4.040 to 1.786 for Sol, and from 2.731 to 1.628 for Jev (Fig. 1b). Distances improve for 75.7%, 82.4%, and 86.9% of observed countries, respectively. GPT-4o and Jev use 107 countries; Sol uses the 91 countries with complete ten-construct inputs. Within-model prompting comparisons use the same countries on both sides.

Tao et al. reported a GPT-4o mean distance reduction from 2.42 to 1.57 and improvement in 71.0% of countries (1). The current expected-score analysis changes both the response representation and the human-data release, so numerical proximity does not establish exact reproduction. A closer reconstruction that averages projected modal responses across prompt variants yields 2.380 to 1.603 for GPT-4o, with improvement in 74.8% of countries (Table S16). It still differs from the original temperature-zero, direct-response protocol, including its treatment of Y003. Sol lacks a complete unconditioned profile for this variant-wise modal reconstruction; its available country-conditioned modal profiles are reported only as a coverage-limited diagnostic (Fig. S8).

Retaining probabilities also improves mean cultural alignment relative to taking the argmax of the final averaged vector: country-conditioned mean distance falls from 1.690 to 1.562 for GPT-4o, from 1.884 to 1.786 for Sol, and from 1.845 to 1.628 for Jev. On the common 91-country subset, expected-score distances are 1.545, 1.786, and 1.631, respectively (Table S15). These comparisons concern compressed cultural coordinates; they do not establish recovery of the underlying response distributions.

### Full probabilities preserve information lost by modal answers

Mean JSD from human response frequencies is 0.214 for GPT-4o, 0.290 for Sol, and 0.193 for Jev (Table 2). On the 946 cells shared by Sol and Jev, the mean Sol-minus-Jev difference is 0.099 (95% crossed-bootstrap CI 0.057 to 0.145). Mean total variation differs by 0.063 (0.008 to 0.117). The normalized Wasserstein contrast is 0.055, with an interval narrowly including zero (-0.0004 to 0.113). The paired diagnostic appears in Figure S1.

GPT-4o and Jev are less clearly separated. Their mean JSD difference is 0.020 across 963 matched cells (95% CI -0.016 to 0.053), and GPT-4o has lower mean total variation (0.379 versus 0.391). On the 946 cells shared by GPT-4o and Sol, GPT-4o has lower JSD by 0.079 on average (GPT-4o-minus-Sol 95% CI -0.113 to -0.045). These results describe the evaluated model snapshots and do not establish a general ordering of providers or interfaces.

Collapsing each aggregated vector to its argmax increases mean JSD to 0.382, 0.392, and 0.470, respectively. The paired mean reductions from retaining the full distribution are 0.169, 0.102, and 0.277; the full distribution is closer in 99.1%, 61.2%, and 95.5% of cells (Fig. 2; Table S5). This is a comparison of two representations of the same vector, without an additional API request. Nonmodal probability mass therefore contributes information about human response frequencies, although the gain is not uniform across cells.

Fidelity varies substantially by item (Fig. S5; Table S6). For justifiability of homosexuality (F118), mean JSD is 0.407 for GPT-4o, 0.518 for Sol, and 0.306 for Jev; for the post-materialist index (Y002), the values are 0.109, 0.244, and 0.068. Respect for authority (E018) shows smaller differences, at 0.175, 0.170, and 0.143. Country-level summaries are reported in Table S7.

### Country information adds uneven population-specific information

Improvement in cultural-map location does not imply improvement in every response distribution. Relative to the same model’s unconditioned distribution, mean country-conditioning JSD gain is 0.043 for GPT-4o (95% CI -0.029 to 0.139), 0.144 for Sol (0.016 to 0.285), and 0.093 for Jev (0.032 to 0.161). Country conditioning improves 48.9%, 56.9%, and 69.9% of cells, respectively (Fig. 3a; Table 3). The GPT-4o interval includes zero, and fewer than half its cells improve despite a positive mean gain.

A simple human benchmark remains substantially closer to the target distributions. The equal-country average of all other countries for the same item, excluding the target country, has mean JSD approximately 0.052 on each model’s observed cells. The country-conditioned models beat this leave-one-country-out benchmark in only 15.2%, 10.9%, and 15.1% of cells (Fig. 3b). Country prompts therefore add useful information relative to a model’s own default without recovering most of the distributional information already contained in this cross-national human baseline.

The item pattern further qualifies the mean gains (Fig. S10; Table S12). Country prompting worsens happiness-distribution fidelity for all three systems. Gains are particularly large for Sol on importance of God (0.524 JSD units) and for GPT-4o on justifiability of homosexuality (0.365). Such differences explain why a positive overall gain can coexist with deterioration across many country-item cells.

### Average entropy and the pattern of disagreement remain distinct

Across the full human benchmark, mean normalized entropy is 0.721. Model means are 0.378 for GPT-4o, 0.215 for Sol, and 0.657 for Jev; the human mean on Sol’s 946 observed cells is 0.718 (Fig. 4a). Mean absolute entropy errors are 0.372, 0.512, and 0.230, respectively. Jev thus comes closest to the average amount of human disagreement, while both GPT models produce more concentrated response distributions.

The pooled slopes of model entropy on human entropy are 0.596 for GPT-4o (two-way cluster-robust 95% CI 0.235 to 0.958), 0.361 for Sol (0.150 to 0.571), and -0.010 for Jev (-0.177 to 0.156). With item fixed effects, the slopes are 0.456 (0.106 to 0.807), 0.297 (0.028 to 0.566), and -0.002 (-0.084 to 0.079). With both country and item fixed effects, they are 0.295 (-0.100 to 0.690), 0.258 (-0.020 to 0.536), and 0.013 (-0.119 to 0.144); all three intervals include zero (Fig. 4b; Table S10). The GPT models’ pooled positive associations therefore provide weaker evidence of tracking disagreement once both sources of structure are removed. Inference is approximate because the covariance estimator has only nine item clusters.

Within-item correlations vary in sign and magnitude (Fig. S9; Table S11). For example, both GPT models show correlations near 0.78 for importance of God, while their correlations are negative for justifiability of homosexuality. Jev has a correlation of approximately -0.50 for abortion. Lower mean entropy and a slope below one should not be conflated with smaller cross-cell entropy variance: the model-to-human standard-deviation ratios are 1.446 for GPT-4o, 1.267 for Sol, and 1.013 for Jev (Table S10). These diagnostics distinguish the level, association, and variability of model uncertainty.

### Sensitivity to elicitation and probability recovery

Among country-conditioned cells with at least two retained descriptor variants, mean JSD from the model-country-item mean is 0.038 for GPT-4o, 0.043 for Sol, and 0.014 for Jev (Fig. S2; Table S8). Among descriptor groups with at least two retained label assignments, mean semantic label sensitivity is 0.032 and 0.008, respectively (Fig. S3; Table S13). Groups with only one retained repetition cannot identify sensitivity and are treated as unavailable.

Comparing alternative option orders only with the prespecified reference order gives mean JSD 0.141 for GPT-4o across 324 comparisons, 0.045 for Sol across 157, and 0.010 for Jev across 324 (Fig. S4; Table S14). Sol has no valid reference-based F120 comparisons after censoring. Its smaller sensitivity estimate is conditional on selective retention and should not be interpreted as evidence of general invariance to order.

Tightening the unseen-mass bound from 0.001 to 0.0001 changes Sol’s mean JSD from 0.290 on 946 cells to 0.283 on 875 cells. Requiring every permitted label to be observed leaves only 101 cells, with mean JSD 0.161 (Fig. S6; Table S4). Because both retained requests and cell coverage change, this contrast cannot distinguish a censoring-policy effect from selection into the retained sample.

Y003 was evaluated separately through the four marginal selection probabilities that determine the autonomy index. Mean absolute error across these marginals is 0.416 for GPT-4o, 0.384 for Sol, and 0.223 for Jev. Jev has the lowest mean error for each constituent (Fig. S7; Table S9). These results concern marginal probabilities and do not establish recovery of the joint pattern of child-rearing values.

## Discussion 

Can uncertainty inside one artificial system recover variation across a population of humans? Our results suggest a qualified answer. Machine probability distributions contain substantial information about population responses, and retaining that information is consistently better than discarding it in favor of a modal answer. Yet the correspondence is incomplete, model-dependent, and multidimensional. Within-model uncertainty and between-person heterogeneity are related empirical objects, not interchangeable ones.

The clearest positive result is the value of retaining uncertainty. For every system, the complete probability vector was substantially closer to human response frequencies than the same vector collapsed to its argmax. The reduction in mean JSD was 0.169 for GPT-4o, 0.102 for Sol, and 0.277 for Jev. Nonmodal probability mass therefore contains population-level information that point prediction systematically removes.

This matters for how synthetic respondents are conceptualized. A point predictor answers, in effect, “which response is most plausible?” A synthetic population asks a different question: “how are responses distributed across people?” The first objective can be useful without satisfying the second. Our results show that even when only one artificial model is available, its complete uncertainty distribution can recover some of the information lost by forcing it to return a single answer. But the improvement should not be confused with proof that model uncertainty is human heterogeneity.

The comparison among systems makes that distinction visible. Jev had the lowest overall JSD and expected-score error and clearly outperformed GPT-5.6 Sol on the primary matched comparison. But GPT-4o was close to Jev in mean JSD, slightly better in mean total variation, and better than Sol on each major distributional metric. The contemporary OpenAI model was therefore not a uniformly better population simulator than its historical-generation counterpart. Model recency and general capability should not be assumed to imply better synthetic-population fidelity.

Nor should the Jev result be treated as establishing a general advantage of decision-native architecture. GPT-4o, Sol, and Jev differ in many unobserved ways, including pretraining, post-training, model scale, objectives, and serving infrastructure. Our comparisons therefore describe complete systems. They show that probability semantics and model generation matter empirically; they do not isolate a causal architectural mechanism.

The entropy results reveal a deeper distinction between average and structured heterogeneity. Jev’s mean entropy was close to the human mean and its mean absolute entropy error was substantially smaller than either GPT model. If evaluation stopped there, one might conclude that Jev had recovered human disagreement particularly well.

Jev entropy is essentially unrelated to human entropy across pooled country-item cells, and remains weakly associated after item or country-and-item adjustment. The GPT models have lower mean entropy and positive pooled associations, but their two-way fixed-effect intervals include zero. Their response distributions are too concentrated on average; their residual ability to track where disagreement occurs is uncertain.

These are different evaluation failures. A model may understate mean disagreement, reproduce its average level while assigning it to the wrong cells, or show an association driven by stable item and country differences. The fixed-effect results limit how strongly the pooled associations can be interpreted as recovery of population-specific heterogeneity.

The population-specificity analysis sharpens this interpretation. Country prompting improves mean distributional fidelity relative to each model’s own default, but the improvement is uneven and the GPT-4o interval includes zero. Only 10.9% to 15.2% of cells beat the leave-one-country-out human baseline. Model uncertainty responds to country information without recovering most of the distributional information contained in this simple human comparison. Because the baseline draws on observed human surveys, this is an information benchmark rather than a like-for-like comparison of systems given identical data.

The interface analyses show that model uncertainty depends on how it is elicited. Respondent wording, arbitrary labels, and answer ordering alter the recovered distributions. Sensitivity requires repeated usable measurements: a singleton cannot establish stability, and an excluded reference ordering cannot be replaced by a later permutation without changing the estimand. Sol’s lower measured order sensitivity is conditional on selective request retention, including the absence of usable F120 reference comparisons.

GPT-5.6 Sol exposed a different interface problem because its next-token distribution was often highly concentrated. Low-probability permitted responses frequently fell outside the API’s returned top-logprob alternatives. Assigning those unobserved labels probability zero would overstate certainty. Dropping every incomplete call would produce a different problem, because complete cases are not randomly selected: they disproportionately occur when the model is diffuse enough that all alternatives enter the returned set.

A stricter residual-mass threshold yields a Sol mean JSD close to the primary estimate, while complete-case restriction leaves only 101 country-item cells and a substantially lower mean JSD. This comparison changes both the probability vectors and the populations and items represented. It therefore does not isolate the effect of the censoring policy or establish that the lower complete-case mean reflects better general fidelity.

The cultural-map analysis recovers the broad prompting pattern reported by Tao et al. (1), while changing the human-data release and using probability-derived expected scores. The variant-wise modal reconstruction provides a closer descriptive comparison, but its Y003 marginal treatment and temperature-one probability collection still differ from the original protocol. These results support continuity in the broad pattern rather than exact numerical reproduction.

But cultural maps necessarily compress. Each national response distribution becomes a set of expected item scores and ultimately a two-dimensional coordinate. Two models can occupy similar positions while differing substantially in the shape or entropy of their underlying response distributions. A cultural coordinate can therefore answer whether the location of model-implied values resembles the human population while leaving open whether the model preserves the population’s internal disagreement. The present distributional tests make this hidden dimension observable.

The GPT-4o versus Sol comparison also raises a temporal issue for synthetic-population research. Model development can alter uncertainty even when the elicitation procedure is held approximately constant. Sol was much more concentrated, suffered much more top- censoring, and had higher mean distributional error than GPT-4o on this benchmark. Synthetic-population findings should therefore be treated as model-snapshot results rather than stable properties of a provider or model family.

Several limitations bound the interpretation. First, country labels are coarse descriptors of internally heterogeneous populations. The benchmark assesses country-level response distributions and does not claim that nationality is sufficient to characterize individual preferences. Second, all model prompts were in English. Language itself can alter cultural expression and model behavior. Third, the empirical run used WVS Trend v4.1 rather than the earlier WVS release used by Tao et al., so the cultural benchmark is a release-updated replication and extension rather than an exact numerical reproduction.

Fourth, finite top-K output bounds rather than reveals the probabilities of omitted labels. Unequal retention affects both aggregation and robustness comparisons. Fifth, model training and post-training histories are incompletely observable, so system differences do not identify an architectural effect. Sixth, Y003 is assessed through marginals rather than its full joint distribution. Seventh, unknown training exposure to survey or cultural data may affect the outputs. Eighth, entropy intervals rely on only nine item clusters, limiting the accuracy of asymptotic cluster-robust inference. Finally, the cross-national human baseline uses observed survey distributions and has a different information source from the model prompts. Frozen identifiers and archived outputs are needed to interpret each result as a model-snapshot comparison.

The study also leaves open the relationship between probability distributions and richer synthetic-agent approaches. A single country-conditioned model has no explicit collection of individuals with different histories or latent traits. Its probability vector may nevertheless encode statistical regularities learned from heterogeneous human text and data. Future work can compare this compressed uncertainty with distributions generated by explicit synthetic populations whose agents differ in demographics, experiences, or latent preferences. Such comparisons could determine when one probabilistic model is sufficient and when population structure must be represented explicitly.

A second direction concerns joint distributions. The present study asks whether each survey item’s marginal response distribution is recovered. A convincing synthetic population may require more: relationships among attitudes, correlations across questions, subgroup differences, and the coexistence of minority positions within individuals. Marginal fidelity is therefore necessary for many applications but not sufficient for reconstructing a population’s complete social structure.

A third direction concerns the decomposition of uncertainty itself. Human survey frequencies combine stable between-person differences, within-person ambivalence, framing effects, and measurement error. Model probabilities likewise combine learned statistical regularities and uncertainty induced by context and representation. Future experiments with repeated human judgments, richer personal information, and controlled ambiguity could begin to separate these components rather than treating either side as a single undifferentiated probability.

The broader methodological lesson is that synthetic-population research should distinguish at least three objectives. A system may produce a plausible answer, approximate a population distribution, or reproduce the structure of variation across populations and questions. Success at one does not guarantee success at the others.

Model probabilities are therefore neither meaningless for social science nor automatically equivalent to human frequencies. They occupy an intermediate position. Their nonmodal mass clearly contains information about population variation; in some settings, it can materially improve synthetic distributions and cultural-map alignment. Yet the pattern of uncertainty can diverge from the pattern of disagreement among people.

The practical question is consequently not whether a model “has uncertainty,” but what that uncertainty tracks. When AI is used to simulate a population, the relevant test is not simply whether its probabilities sum to one or look appropriately diffuse. It is whether uncertainty within the model rises, falls, and redistributes itself in the same places that heterogeneity appears among the humans the model is intended to approximate.

## Materials and Methods

### Human data and analysis universe

The human benchmark was constructed from the European Values Study (EVS) Trend File 1981–2017, ZA7503 version 3.0.0, and the World Values Survey (WVS) Trend File 1981–2022 version 4.1.0 (11,12). The source files were harmonized using the common EVS/WVS variable dictionary and official merge logic supplied with the Integrated Values Surveys materials.

The resulting historical IVS file contained 666,907 respondent observations and 838 harmonized variables. The analysis retained common survey-wave codes 5, 6, and 7 and restricted observations to calendar years 2005–2022, leaving 392,832 respondent records.

Country identity was defined using the numeric IVS identifier S003 rather than alpha-label strings, because some survey releases use multiple alpha aliases for the same survey-defined country unit. After harmonization, 112 country/territory entities were present. Following Tao et al. (1), Egypt, Kuwait, Qatar, Tajikistan, and Uzbekistan were excluded from the strict cultural benchmark because at least one required construct lacked valid observations. The final analysis universe therefore contained 107 countries/territories.

The source study used an earlier WVS Trend release. The present analysis consequently preserves the substantive benchmark and wave logic but uses an updated WVS release. We treat this as a release-updated replication and extension.

### Human response distributions

The primary finite-response items were: A008 Feeling of Happiness; A165 Trust on People; E018 Respect for Authority; E025, Petition Signing Experience; F063, Importance of God; F118, Justifiability of Homosexuality; F120, Justifiability of Abortion; G006, Pride of Nationality; and Y002, Post-Materialist Index.

For each country, year, item, and valid response category, survey-weighted response frequencies were calculated using IVS weight S017. Values outside the documented substantive response set were treated as missing.

Country-year distributions were calculated first. Where a country contributed observations in multiple retained years/waves, its country-level distribution was obtained by averaging the available country-year distributions equally rather than pooling all respondents across years. This preserves the source study’s treatment of repeated national observations while avoiding mechanical overweighting of years with larger samples.

The nine primary constructs yield a maximum of  country–item distributions.

### Cultural-map construction

The cultural-map replication used the nine finite-response items plus Y003, the Autonomy Index. Human item scores were standardized using the reconstructed IVS benchmark. A weighted pairwise correlation matrix was calculated, two components were extracted, and varimax rotation was applied. Component signs were oriented so that the first dimension increased from survival toward self-expression values and the second from traditional toward secular-rational values.

Following the source study, the resulting coordinates were rescaled as

and

Expected model scores were standardized and projected using the corresponding human-derived transformation. Because the current human benchmark uses WVS v4.1 rather than the earlier source-study release, these map coordinates are interpreted internally against the release-updated human benchmark rather than asserted to reproduce the published source coordinates exactly.

### Respondent descriptors and country conditioning

We retained the ten respondent-descriptor variants used by Tao et al. (1), including “average human being,” “typical human being,” “human being,” “average person,” “typical person,” “person,” “average individual,” “typical individual,” “individual,” and “world citizen.”

For the country-conditioned analysis, the descriptor additionally stated that the respondent was born in and living in the named country/territory. A separate unconditioned __DEFAULT__ target omitted country information.

The model received no individual respondent profiles, demographics, or observed attitudes. Any within-country probability structure therefore arose from the model’s conditional uncertainty under the country descriptor rather than explicit simulation of observed individual respondents.

### OpenAI model conditions

Two OpenAI conditions were evaluated. The historical-generation anchor used gpt-4o-2024-05-13, providing continuity with the GPT-4o generation evaluated by Tao et al. (1). The contemporary condition used gpt-5.6-sol with reasoning effort set to none.

Both OpenAI conditions used temperature 1.0. This deliberately differs from the temperature-zero point-response procedure used in the source study. Tao et al. sought a near-deterministic selected answer; the present estimand is the probability distribution itself. Temperature 1.0 avoids deliberately sharpening that distribution before extracting next-token probabilities.

For every request, the replication package records the requested model identifier, model identifier returned by the provider, response ID, exact prompt, response-label mapping, usage metadata, and probability diagnostics.

### Controlled-label probability extraction

Each substantive response category was mapped to a short alphabetical output label. The user instruction required the model to return exactly one permitted label and no explanation.

The OpenAI Responses API was queried with top_logprobs = 20 and max_output_tokens = 16. The first generated token and alternative token log probabilities were collected. Returned raw token strings were normalized for surrounding whitespace before label matching. If multiple raw token forms mapped to the same semantic label—for example the label A with and without a leading space—their probabilities were summed.

For permitted label set , the observed pre-renormalization permitted-label mass is

When every permitted label is returned, the substantive response distribution is

Thus, the OpenAI probability object analyzed here is explicitly a conditional next-token distribution over the permitted response labels. The original permitted-label mass was retained separately as a diagnostic indicating how much model probability was assigned outside the imposed survey-answer vocabulary. In the expression above, t is the returned token and aₖ is the label assigned to response category k.

### Label rotation

Because token probabilities can depend on arbitrary token identity, the association between substantive responses and alphabetical labels was rotated. Each of the nine primary items was queried under three cyclic label assignments for every respondent descriptor. After collection, probabilities were mapped back to the same substantive response coding before aggregation. The four binary Y003 constituent questions used two label assignments. 

This yields, for each OpenAI model, target, and primary item,

 probability vectors before aggregation. Across the 107 country targets plus the unconditioned default target, the complete primary OpenAI collection contained 37,800 requests per model condition.

### Top- censoring

OpenAI may return fewer than 20 alternative token probabilities, particularly for highly concentrated outputs. A permitted response label absent from the returned alternatives is not known to have exact probability zero and was therefore treated as censored.

Let  denote observed permitted-label mass after clamping negligible numerical overshoot to the interval . The total probability assigned to all unobserved tokens is bounded by

Because any missing permitted labels form a subset of the unobserved vocabulary, their combined probability mass cannot exceed this residual. The primary analysis retained: (i) calls in which every permitted label was observed; and (ii) censored calls for which the residual upper bound was no greater than 0.001. A strict sensitivity analysis used an upper bound of 0.0001. A complete-only analysis retained only calls in which every permitted label appeared in the returned top-logprob set. Missing permitted labels were never silently assigned exact probability zero.

### Jev model and probability elicitation

The decision-native condition used TypeSafe’s Jev System One API with the model pinned as jev-1.13.0.

The respondent descriptor was supplied as shared state. Each primary finite-response item was represented as a typed Choice question with substantive alternatives matching the human response categories used in the OpenAI condition.

The API returned a probability dictionary over the declared alternatives. Probabilities were mapped directly to the human response support and normalized defensively to one for numerical analysis.

Choice rather than an ordered Score abstraction was used for the primary comparison so that OpenAI and Jev received the same substantive response alternatives without giving Jev additional information about ordinal structure. Exploratory native-Score requests were included in the computational audit but are not part of the reported primary results.

Jev’s Y003 constituents were issued jointly as four Noul questions sharing the same respondent state. Each returned a probability for the corresponding yes/no decision without allowing one constituent response to alter the state presented to the next.

The principal Jev collection contained 10,800 API requests.

### Post-Materialist Index, Y002

Y002 asks respondents to select the most important and second-most-important goal from four alternatives. The model response space therefore contains 12 ordered pairs of distinct goals.

OpenAI received one controlled label for each ordered pair, and Jev received the corresponding 12 declared Choice alternatives.

Pairs containing goals 1 and 3, in either order, were aggregated to the materialist class; pairs containing goals 2 and 4 were aggregated to the post-materialist class; all cross-group pairs were aggregated to the mixed class. The resulting three-category probability vector was compared with the human Y002 distribution.

### Autonomy Index, Y003

Y003 asks respondents to select up to five important child qualities from eleven alternatives. Including the empty set, the complete response space up to size five contains 1,024 possible subsets and is therefore unsuitable for a common exhaustive OpenAI/Jev probability-vector comparison.

The WVS autonomy index depends on four binary indicators:

Independence, A029; 

Determination/perseverance, A039; 

Religious faith, A040; and 

Obedience, A042. 

The index is

We therefore estimated each constituent’s marginal selection probability directly.

Expected Y003 can then be calculated as

which follows by linearity of expectation and requires no assumption that constituent selections are independent.

Y003 was excluded from the primary nine-item full-distribution divergence analysis.

### Aggregation of model distributions

For each condition, target, and primary item, retained probability vectors were mapped to common substantive response categories and averaged across respondent-descriptor variants and, for OpenAI, cyclic label assignments.

The resulting country–item vector represents the condition’s mean predicted response distribution for that population and item.

The unconditioned default target supplies the same-model baseline for country-conditioning comparisons and the default cultural-map position. It is excluded from country-level paired inference and the country-conditioned prompt and label sensitivity summaries.

### Distributional metrics

The primary metric was Jensen–Shannon divergence with base-2 logarithms:

JSD is symmetric, finite for discrete distributions containing zero probabilities, and bounded between 0 and 1.

Secondary distributional metrics included total variation distance,

and 1-Wasserstein distance for ordered items. Wasserstein distances were divided by the full response-scale range so that transport errors were comparable across items with different numbers of ordered categories.

Expected-score error was

where  denotes the numeric score attached to response category .

### Population specificity

For each observed model-country-item cell, country-conditioning gain equals JSD(human, unconditioned model) minus JSD(human, country-conditioned model). The leave-one-country-out human baseline is the equal-country average of all other countries’ distributions for the same item. Baseline gain is its JSD from the target human distribution minus the model’s JSD. Positive gain always favours the country-conditioned model. Each comparison uses identical cells on both sides. Means and 95% percentile intervals use the crossed country-by-item bootstrap; fractions improved count strictly positive gains and exclude unavailable comparisons.

### Entropy and heterogeneity

Shannon entropy was calculated as

To permit comparison across response spaces of different sizes, entropy was normalized by its maximum value:

where  is the number of response categories.

We report absolute normalized-entropy error,

and signed entropy difference.

Model normalized entropy was regressed on human normalized entropy in pooled, item-fixed-effect, country-fixed-effect, and two-way-fixed-effect specifications. Standard errors use two-way clustering by country and survey item with normal 1.96 critical values. These intervals are approximate because there are only nine item clusters. Undefined covariance estimates are not converted into zero-width intervals. Pearson and Spearman associations, within-item and within-country associations, and model-to-human entropy standard-deviation ratios are reported separately.

A unit slope denotes a one-unit fitted change in model entropy per unit of human entropy; a slope near zero indicates little linear association. A slope below one does not imply smaller cross-cell variance, because covariance and variance are distinct quantities. Two-way residual associations remove additive country and item effects by least-squares projection, including in the unbalanced Sol sample.

### Full-distribution versus argmax comparison

For every machine probability vector, an argmax representation was generated deterministically by assigning probability one to the highest-probability substantive response and zero to all others.

No second API request was made.

Distributional metrics were then recalculated against the human response distribution. The resulting argmax-minus-full difference isolates the value of retaining probability information while holding the underlying model, prompt, and probability vector fixed.

### Pairwise inference

Pairwise model comparisons were based on country–item cells observed for both relevant conditions.

For each metric, the principal interval for the average difference used a crossed bootstrap with 5,000 replicates. Each replicate independently resampled countries with replacement and items with replacement and evaluated the corresponding Cartesian set of observed paired cells.

This procedure treats country and item as two dimensions over which the result should generalize rather than treating all country–item observations as independently and identically distributed.

Paired Wilcoxon signed-rank tests across observed matched cells were reported as complementary robustness statistics. Because the rank test and crossed bootstrap target different aspects of the paired distribution, disagreement between a rank-test  value and a confidence interval for the mean difference was not treated as contradictory.

### Prompt sensitivity

For each respondent descriptor, the corresponding probability vector was compared with the model condition’s mean distribution for that country and item using JSD.

Groups with fewer than two retained descriptors have undefined sensitivity. Summaries exclude the unconditioned target, pool retained descriptor comparisons across country-item cells, and report usable counts. Unequal surviving label counts can give descriptors unequal weight in the aggregated condition mean.

### Label sensitivity

OpenAI label sensitivity was calculated after mapping each cyclic alphabetical label assignment back to the same substantive response categories.

Sensitivity is defined only when at least two label assignments survive for the same model, country, item, and descriptor. Singleton groups are retained in diagnostic files with missing sensitivity, rather than being interpreted as zero label dependence. Country-conditioned summaries exclude the unconditioned target and report valid comparison counts.

### Option-order robustness

A supplementary option-order experiment sampled 12 countries across the analysis universe and included all nine primary items.

Four answer-order configurations were queried for each model and country-item cell. Configuration 0 is the prespecified reference. Both that request and an alternative request must satisfy the primary censoring policy before their semantic distributions are compared. Cells without a retained reference are excluded from these comparisons; no replacement reference is selected.

The design generated 432 requests per model condition. There are 324 valid comparisons for GPT-4o, 157 for Sol, and 324 for Jev. Sol has no usable reference-based F120 comparisons. Mean JSD describes the retained comparisons and does not imply stability of the excluded requests.

### Cultural-map comparison

For each finite-response item, expected model score was calculated from the complete probability vector rather than selecting its argmax.

Expected Y003 was constructed from the four constituent marginal probabilities.

These ten expected scores were standardized and projected through the human-fitted cultural-map transformation.

For each country, cultural distance was defined as Euclidean distance between model and human coordinates.

The projection is repeated with the argmax of each final aggregated vector. A separate variant-wise modal reconstruction first averages retained label assignments within descriptor, selects each item’s modal response, thresholds each Y003 constituent at 0.5, projects complete ten-construct profiles, and averages coordinates over available complete variants. This differs from the source study’s direct point-response protocol. Sol provides 43 country-conditioned profiles under this reconstruction and no complete unconditioned profile; it is excluded from variant-wise modal prompting comparisons.

### Computational audit

The complete computational audit included the primary GPT-4o, GPT-5.6 Sol, and Jev collections, option-order robustness requests, and exploratory Jev native-Score collection.

Across providers, the archived records contained 95,186 distinct API requests, 20,713,572 input tokens, 1,215,251 output tokens, and 21,928,823 total provider-reported tokens.

Using the dated standard list-price configuration frozen on 25 September 2026, estimated API expenditure was US$44.87. These values are reproducibility estimates rather than invoices; provider billing records are authoritative.

Raw request identifiers, model identifiers, usage objects, flattened token counts, and dated pricing assumptions are retained in the replication package where provider terms permit.

## Acknowledgments

This research was supported by the Australian Research Council through the ARC Training Centre for Behavioural Insights for Technology Adoption (IC210100008). Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the Australian Research Council, the funding organizations, or the authors’ affiliated institutions. According to the GAIDeT taxonomy, the following tasks were delegated to generative AI tools under full human supervision: literature search and systematization; quality assessment, including assessment of arguments and proposed derivations; code optimization; visualization; and proofreading and editing. The generative AI tools used were ChatGPT (GPT-6 Astra and GPT-5.6 Sol) and Claude (Opus 5). Responsibility for the final manuscript, references, analyses, and conclusions lies entirely with the authors.

## Data and Code Availability

The human benchmark uses the WVS Trend File 1981–2022 version 4.1.0 (11) and EVS Trend File 1981–2017, ZA7503 version 3.0.0 (12). Respondent-level data must be obtained from the respective data providers under their access terms. Analysis code, configuration, aggregate outputs, and reproduction instructions are maintained at https://github.com/stevejbickley/from-answers-to-distributions. The replication package records source hashes, probability-recovery policies, model identifiers, and the dated pricing assumptions used for computational accounting.

## References

Tao Y, Viberg O, Baker RS, Kizilcec RF. Cultural bias and cultural alignment of large language models. PNAS Nexus. 2024;3:pgae346. doi:10.1093/pnasnexus/pgae346. 

Buttrick N. Studying large language models as compression algorithms for human culture. Trends Cogn Sci. 2024;28:187–189. 

Xie Y, Liang L, Li S, et al. Evaluating the statistical realism of LLM-generated social science data. Proc Natl Acad Sci USA. 2026;123:e2538145123. doi:10.1073/pnas.2538145123. 

Ashokkumar A, Hewitt L, Ghezae I, Willer R. Large language models can predict the results of social science experiments. Nature. 2026;656:115–122. doi:10.1038/s41586-026-10742-x. 

Cao Y, Liu H, Arora A, Augenstein I, Röttger P, Hershcovich D. Specializing large language models to simulate survey response distributions for global populations. Proc NAACL-HLT. 2025:3141–3154. doi:10.18653/v1/2025.naacl-long.162. 

Lee N, An NM, Thorne J. Can large language models capture dissenting human voices? Proc EMNLP. 2023:4569–4585. doi:10.18653/v1/2023.emnlp-main.278. 

Dominguez-Olmedo R, Hardt M, Mendler-Dünner C. Questioning the survey responses of large language models. Adv Neural Inf Process Syst. 2024. 

OpenAI. Responses API reference and model documentation. Accessed September 2026. 

TypeSafe AI. System One models and Jev; System One API documentation. Accessed September 2026. 

Inglehart R, Welzel C. Modernization, Cultural Change, and Democracy: The Human Development Sequence. Cambridge University Press; 2005. 

Haerpfer C, Inglehart R, Moreno A, et al., eds. World Values Survey Trend File (1981–2022) Cross-National Data-Set. Data File Version 4.1.0. JD Systems Institute & WVSA Secretariat; 2022. doi:10.14281/18241.27. 

European Values Study. EVS Trend File 1981–2017, ZA7503. Data File Version 3.0.0. GESIS Data Archive; 2022. doi:10.4232/1.14021. 

Gneiting T, Raftery AE. Strictly proper scoring rules, prediction, and estimation. J Am Stat Assoc. 2007;102:359–378. 

Guo C, Pleiss G, Sun Y, Weinberger KQ. On calibration of modern neural networks. Proc ICML. 2017. 

Abdurahman S, et al. Perils and opportunities in using large language models in psychological research. PNAS Nexus. 2024;3:pgae245. 

Argyle LP, Busby EC, Fulda N, Gubler J, Rytting C, Wingate D. Out of one, many: Using language models to simulate human samples. Political Analysis. 2023;31(3):337–351. doi:10.1017/pan.2023.2.

Rupprecht J, Ahnert G, Strohmaier M. Prompt perturbations reveal human-like biases in large language model survey responses. Proceedings of the Seventh Workshop on NLP and Computational Social Science. 2026:1–21. doi:10.18653/v1/2026.nlpcss-1.1. 

Ahnert G, Haensch A-C, Plank B, Strohmaier M. Survey response generation: Generating closed-ended survey responses in-silico with large language models. Proceedings of ACL 2026. 2026:41554–41577. doi:10.18653/v1/2026.acl-long.1927.

Cummins J. The threat of analytic flexibility in using large language models to simulate human data. Adv Methods Pract Psychol Sci. 2026;9(3). doi:10.1177/25152459261461505. 

Table 1. Probability objects compared in the study

Common response support permits numerical comparison without implying identical statistical meaning.

Table 2. Primary distributional fidelity

Lower errors indicate closer agreement. GPT-4o and Jev means use 963 cells; Sol uses 946. Contrasts are paired on common observed cells, so their means need not equal differences between the displayed marginal means. Wasserstein excludes the unordered trust item. Expected-score error is in original item units and is not normalized across response scales. Intervals use 5,000 crossed bootstrap replicates.

Table 3. Cultural prompting and population specificity

Map results use expected scores. Distributional gains are baseline JSD minus country-conditioned model JSD; positive values favour country conditioning. Intervals are crossed-bootstrap percentile intervals. Within-model comparisons are paired on identical countries or country-item cells. Model means have different coverage. LOCO denotes the equal-country human distribution for the same item excluding the target country.

Figure 1. Cultural location and cultural prompting. (a) The release-updated human cultural map uses Tao et al.’s eight region colours (1); red symbols locate the unconditioned models. All 107 countries and three models are labelled. (b) Paired Euclidean distances from unconditioned and country-conditioned expected-score positions to the same human countries. Pink/purple denotes no cultural prompting; blue denotes cultural prompting. Boxes show interquartile ranges, centre lines medians, whiskers observations within 1.5 interquartile ranges, and dots more extreme observations. White diamonds mark means. Annotations give mean distance changes and percentages improved. GPT-4o and Jev use 107 countries; Sol uses 91. These estimates extend the original point-response design. The external Tao benchmark and variant-wise modal reconstruction are reported separately in Table S16.

Figure 2. Information retained by full response distributions. Mean Jensen-Shannon divergence (JSD) between each model and human response frequencies is shown for the full probability vector (blue circles) and the deterministic argmax of that same aggregated vector (pink/purple squares). Lines connect the paired representations within each model. Right-hand columns report the mean argmax-minus-full difference, the fraction of country-item cells with strictly lower JSD under the full representation, and the number of paired cells. Means are descriptive and use each model’s observed coverage; no additional model responses are sampled.

Figure 3. Population specificity of model probabilities. (a) Mean country-conditioning gain, defined as JSD from the same model’s unconditioned distribution minus JSD from its country-conditioned distribution. Positive values indicate improved fidelity to the target human distribution. Bars show 95% percentile intervals from 5,000 crossed country-by-item bootstrap replicates; annotations show the fraction of observed cells improved. (b) Country-conditioned model JSD compared with an equal-country human distribution constructed from all other countries for that item, leaving out the target country (LOCO). Each human benchmark is averaged on the corresponding model’s observed cells. Annotations show the fraction of cells in which the model beats LOCO and the cell count. Colours identify GPT-4o (blue), Sol (orange), and Jev (green).

Figure 4. Average disagreement and the structure of disagreement. (a) Mean normalized entropy of each model and of the human distributions on the same observed cells. Right-hand values report model / human means. (b) Slopes from regressions of model entropy on human entropy: pooled, with item fixed effects, and with both country and item fixed effects. Error bars are asymptotic 95% normal intervals using two-way cluster-robust covariance by country and item. The dashed line marks zero association and the dotted line marks a unit slope. There are only nine item clusters, so these intervals should be interpreted cautiously. Sample sizes are 963 cells for GPT-4o and Jev and 946 for Sol. A slope below one is not itself evidence that the model’s cross-cell entropy variance is smaller than the human variance; Table S10 reports both quantities.
