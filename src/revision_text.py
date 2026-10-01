"""Current manuscript captions and tables, rendered directly from audited results."""
from pathlib import Path
import pandas as pd
from .publication_style import LABELS
from .publication_text import MAIN_CAPTIONS as OLD_MAIN_CAPTIONS, SI_FIGURES as OLD_SI_FIGURES

MODELS=['gpt4o_anchor','gpt56_sol','jev']
MAIN_FIGURES=['figure1_tao_replication','figure2_country_specific_signal','figure3_heterogeneity_structure']
MAIN_CAPTIONS={1:OLD_MAIN_CAPTIONS[1],3:OLD_MAIN_CAPTIONS[4]}
MAIN_CAPTIONS[2]=('Country-specific signal and population fidelity. (a) Percentage of observed country–item cells with a positive inner product between the country-conditioned model shift from its own default and the human country deviation from the leave-one-country-out (LOCO) human distribution. Zero model shifts count as non-positive; no chance benchmark is assumed. (b) Pooled projection, calculated as the sum of inner products divided by the sum of squared human-deviation norms. Zero denotes no projected movement and one denotes matching the human deviation along that direction; one does not establish complete distributional recovery. (c) Mean JSD improvement relative to each model’s default. Intervals in a–c are 95% percentiles from 5,000 crossed country-by-item resamples. (d) Mean JSD against the target human distribution for the country-conditioned model and the LOCO human benchmark; annotations give the fraction of cells in which the model beats LOCO. GPT-4o and Jev use 963 cells; Sol uses 946. Colours identify models consistently across panels.')
SI_FIGURES=[]
for stem,caption in OLD_SI_FIGURES:
    caption=caption.replace('Figure 4','Figure 3')
    if stem=='figure_s4_option_order_heatmap':
        caption += ' Reference order 0 was itself randomly shuffled. The OpenAI manipulation also rotates label assignments, so it measures combined order/label perturbation; Jev changes the declared-alternative order. Repeated permutations need not be distinct.'
    SI_FIGURES.append((stem,caption))
SI_FIGURES.extend([
 ('figure_s12_cultural_direction','Country-deviation alignment by item. Panels report the percentage of positive inner products, mean cosine similarity among nonzero shifts, and pooled projection onto the human deviation. Binary-item cosines are ±1 when both shifts are nonzero. Zero model shifts enter the direction percentage as non-positive and are excluded from cosine means. Pooled projection is a ratio of sums. Table S19 supplies cell counts and overall crossed-bootstrap intervals.'),
 ('figure_s13_temporal_targets','Sensitivity to the human target’s date. Model probabilities are held fixed while the target is the equal-year pooled benchmark, the latest observed calendar year in each country, or wave 7 with equal-year averaging. Panels show JSD, gain relative to the model default, the fraction beating LOCO, directional alignment, projection and the two-way entropy slope. Points are descriptive estimates, not confidence limits. Coverage differs across targets; Table S20 also evaluates the pooled benchmark on matched cells.'),
 ('figure_s14_entropy_leave_one_item_out','Influence of individual items on adjusted entropy associations. Each row omits the indicated item and re-estimates country and item effects. Panels show the slope of model entropy on human entropy and the Pearson and Spearman correlations of their two-way residuals. Dotted coloured lines mark full-sample estimates. Points are omission diagnostics, not uncertainty intervals. Table S22 reports every fit.'),
 ('figure_s15_probability_value',OLD_MAIN_CAPTIONS[2]+' This representation diagnostic compares full probabilities with their own deterministic collapse. A nondegenerate human target structurally disadvantages one-hot predictions; an advantage here does not establish population calibration or country specificity.'),
 ('figure_s16_human_sampling_sensitivity','Propagation of respondent sampling variability. Points show original estimates and bars show 95% percentile intervals from 1,000 uniform respondent resamples within country-year, retaining original S017 weights and common respondent multiplicities across items. Model probabilities, countries and items remain fixed. Panels report JSD, default gain, the fraction beating LOCO, direction, projection and the two-way entropy slope. These conditional human-reference intervals do not represent crossed country/item uncertainty or full complex-survey design variance. Table S23 contains the complete numerical summaries.'),
])


VALUE_LABELS={
 'pooled_equal_year':'Pooled', 'latest_available':'Latest year', 'wave7':'Wave 7',
 'pooled_matched_latest_available':'Pooled, latest cells', 'pooled_matched_wave7':'Pooled, wave-7 cells',
 'expected':'Expected score','argmax':'Aggregated argmax','tao_modal':'Variant-wise modal',
 'complete_only':'Complete only','primary':'Primary','strict':'Strict',
 'js':'JSD','tv':'TV','wasserstein':'Wasserstein','expected_abs_error':'Score error','entropy_abs_error':'Entropy error',
 'js_mean':'Mean JSD','gain_vs_default_mean':'Default gain','loco_js_mean':'LOCO JSD','gain_vs_loco_mean':'LOCO gain',
 'pct_default_improved':'Improved vs default (%)','pct_model_beats_loco':'Beat LOCO (%)',
 'human_entropy_mean':'Human mean entropy','entropy_abs_error_mean':'Entropy error',
 'direction_correct_percent':'Positive direction (%)','cosine_mean':'Mean cosine','projection_pooled':'Pooled projection',
 'pooled_slope':'Pooled entropy slope','pooled_pearson':'Pooled Pearson r','pooled_spearman':'Pooled Spearman rho',
 'two_way_slope':'Two-way entropy slope','two_way_pearson':'Residual Pearson r','two_way_spearman':'Residual Spearman rho',
}

def f(value,digits=3):
    if pd.isna(value):return 'NA'
    if isinstance(value,str):return VALUE_LABELS.get(value,value).replace('|','\\|').replace('\n',' ')
    return f'{value:.{digits}f}'


def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(v).replace('\n',' ') for v in row)+' |' for row in rows])


def make_tables_text(results='results'):
    root=Path(results);read=lambda name:pd.read_csv(root/name)
    parts=[]
    def add(n,title,headers,rows,note=''):
        parts.append(f'### Table S{n}. {title}\n\n'+table(headers,rows)+(f'\n\n{note}' if note else ''))
    def plain(n,title,name,columns,headers,note='',integer=()):
        d=read('tables/'+name);rows=[]
        for _,r in d.iterrows():
            rows.append([LABELS.get(r[c],r[c]) if c=='condition' else str(int(r[c])) if c in integer and pd.notna(r[c]) else f(r[c]) for c in columns])
        add(n,title,headers,rows,note)
    plain(1,'Survey constructs and response representation','table_s1_survey_constructs.csv',
          ['item','construct','human_support','probability_representation'],['Item','Construct','Human support','Model representation'],
          'Nine finite-response items enter JSD analyses. Y003 contributes only marginal probabilities and an expected index. Complete question wording and option coding are frozen in config/questions.yaml; the wording is reproduced in S1.3.')
    d=read('tables/table_s2_prompt_variants.csv')
    add(2,'Respondent descriptors',['ID','Descriptor phrase'],[[int(r.id),r.descriptor.replace('You are ','').replace(' responding to the following survey question.','')] for r in d.itertuples()],
        'Unconditioned template: “You are {descriptor phrase} responding to the following survey question.” Country-conditioned template: “You are {descriptor phrase} born in {country} and living in {country} responding to the following survey question.” The descriptor phrase includes its article. Country names follow the frozen 107-target universe.')
    plain(3,'Request-level probability recovery','table_s3_openai_diagnostics.csv',
          ['condition','calls','complete_calls','incomplete_percent','primary_retained_percent','strict_retained_percent','complete_only_percent'],
          ['Model','Requests','Complete','Incomplete (%)','Primary kept (%)','Strict kept (%)','Complete only (%)'],
          'Counts include default targets and Y003 constituent requests. “Complete” means that every permitted label appears in the returned alternatives.',integer=['calls','complete_calls'])
    d=read('tables/table_s3_openai_diagnostics.csv')
    parts[-1]+='\n\n'+table(['Model','Mean allowed mass','Median allowed mass','Maximum missing-mass bound','Invalid label (%)'],[[LABELS[r.condition],f(r.allowed_mass_mean,6),f(r.allowed_mass_median,6),f(r.missing_mass_upper_bound_max,6),f(r.invalid_generated_percent,2)] for r in d.itertuples()])
    plain(4,'Censoring-policy sensitivity','table_s4_openai_censoring_sensitivity.csv',
          ['condition','censoring_policy','n_country_item','js_mean','tv_mean','expected_abs_error_mean','entropy_abs_error_mean'],
          ['Model','Policy','Cells','JSD','TV','Score error','Entropy error'],
          'Primary and strict missing-mass bounds are 0.001 and 0.0001; complete_only requires every permitted label. Means use each policy’s retained cells and are not paired policy effects.',integer=['n_country_item'])
    plain(5,'Full distributions versus their argmax','table_s5_full_vs_argmax.csv',
          ['condition','n','mean_js_full','mean_js_argmax','mean_argmax_minus_full','median_argmax_minus_full','pct_full_better'],
          ['Model','Cells','Full JSD','Argmax JSD','Mean gain','Median gain','Full better (%)'],integer=['n'])
    plain(6,'Distributional error by item','table_s6_item_summary.csv',
          ['item','condition','n','js_mean','tv_mean','wasserstein_mean','expected_error','entropy_error'],
          ['Item','Model','n','JSD','TV','Wasserstein','Score error','Entropy error'],
          'Wasserstein is normalized by the response-scale range and is unavailable for unordered A165. Score error retains original item units.',integer=['n'])
    d=read('tables/table_s7_country_summary.csv');rows=[]
    for country,g in d.groupby('country',sort=True):
        g=g.set_index('condition');rows.append([country,*[f"{int(g.loc[c,'n'])}; {g.loc[c,'js_mean']:.3f}; {g.loc[c,'tv_mean']:.3f}; {g.loc[c,'entropy_error']:.3f}" for c in MODELS]])
    add(7,'All country-level summaries',['Country or territory',*map(LABELS.get,MODELS)],rows,
        'Each entry is number of observed items; mean JSD; mean TV; mean absolute entropy error. Every country and model is included.')
    plain(8,'Descriptor sensitivity','table_s8_prompt_sensitivity.csv',
          ['item','condition','n','n_retained','mean_js','median_js'],['Item','Model','Valid comparisons','Retained variants','Mean JSD','Median JSD'],
          'Default targets are excluded. Singletons count as retained but have undefined sensitivity.',integer=['n','n_retained'])
    plain(9,'Autonomy constituent errors','table_s9_y003.csv',
          ['condition','quality','n','mae','mse'],['Model','Constituent','Countries','MAE','MSE'],integer=['n'])
    d=read('tables/table_s10_entropy_structure.csv').set_index('condition')
    cols={'pearson_overall':'Pooled Pearson r','spearman_overall':'Pooled Spearman rho','human_entropy_sd':'Human entropy SD','model_entropy_sd':'Model entropy SD','sd_ratio_model_to_human':'Model/human SD','two_way_resid_pearson':'Two-way residual Pearson r','two_way_resid_spearman':'Two-way residual Spearman rho','two_way_resid_human_sd':'Human residual SD','two_way_resid_model_sd':'Model residual SD','two_way_resid_sd_ratio':'Model/human residual SD','within_item_pearson_fisher_mean':'Within-item Pearson Fisher mean','within_item_spearman_fisher_mean':'Within-item Spearman Fisher mean','within_item_pearson_median':'Within-item Pearson median','within_item_spearman_median':'Within-item Spearman median','within_country_pearson_fisher_mean':'Within-country Pearson Fisher mean','within_country_spearman_fisher_mean':'Within-country Spearman Fisher mean','within_country_pearson_median':'Within-country Pearson median','within_country_spearman_median':'Within-country Spearman median'}
    add(10,'Entropy variation and association',['Diagnostic',*map(LABELS.get,MODELS)],[[label,*[f(d.loc[c,key]) for c in MODELS]] for key,label in cols.items()],
        'Fisher means transform correlations to z, average equally across available groups, then transform back. SDs quantify variation across cells, rather than the entropy within a response distribution.')
    rows=[]
    for prefix,label in [('ols','Pooled'),('item_fe','Item FE'),('country_fe','Country FE'),('two_way_fe','Country + item FE')]:
        for c in MODELS:
            r=d.loc[c];rows.append([label,LABELS[c],f(r[prefix+'_slope']),f"[{f(r[prefix+'_ci_low'])}, {f(r[prefix+'_ci_high'])}]",f(r[prefix+'_se']),f(r[prefix+'_r2'])])
    parts[-1]+='\n\n'+table(['Specification','Model','Slope','95% CI','SE','R²'],rows)+'\n\nIntervals use two-way country/item cluster covariance and normal critical values. Only nine item clusters are available. P values remain in the machine-readable companion; interpretation emphasizes effect sizes and stability.'
    plain(11,'Within-item entropy associations','table_s11_entropy_by_item.csv',['item','condition','n','pearson','spearman','slope','human_entropy_mean','model_entropy_mean'],['Item','Model','n','Pearson r','Spearman rho','Slope','Human mean','Model mean'],integer=['n'])
    plain(12,'Country-conditioning gains by item','table_s12_population_specificity_by_item.csv',['item','condition','n','country_model_js_mean','default_model_js_mean','gain_vs_default_mean','gain_vs_loco_human_mean','model_shift_from_default_js_mean'],['Item','Model','n','Country JSD','Default JSD','Default gain','LOCO gain','Model shift'],
          'Positive gain favours the country-conditioned model. Model shift is JSD between conditioned and default model probabilities. LOCO JSD equals country JSD plus LOCO gain.',integer=['n'])
    plain(13,'Semantic label sensitivity','table_s13_label_sensitivity.csv',['condition','item','n','n_retained','mean_js','median_js'],['Model','Item','Valid comparisons','Retained vectors','Mean JSD','Median JSD'],
          'At least two retained assignments are required within descriptor; default targets are excluded.',integer=['n','n_retained'])
    d=read('tables/table_s14_option_order_sensitivity.csv');rows=[]
    for c in MODELS:
        for item in read('tables/table_s1_survey_constructs.csv').item:
            if item=='Y003':continue
            g=d[d.condition.eq(c)&d.item.eq(item)]
            rows.append([LABELS[c],item,int(g.n.iloc[0]) if len(g) else 0,f(g.mean_js.iloc[0]) if len(g) else 'NA',f(g.median_js.iloc[0]) if len(g) else 'NA'])
    add(14,'Order perturbation relative to reference 0',['Model','Item','Valid comparisons','Mean JSD','Median JSD'],rows,
        'Up to 36 comparisons per item: three perturbations in 12 countries. OpenAI also rotates response labels; Jev changes order only. Sol F120 has no valid reference comparison. Reference 0 is never replaced after exclusion.')
    plain(15,'Cultural-map representation sensitivity','table_s15_cultural_map.csv',['condition','representation','n','mean_distance','median_distance'],['Model','Representation','Countries','Mean distance','Median distance'],integer=['n'])
    d=read('cultural_map_common_country_summary.csv');d=d[d.representation.isin(['expected','argmax'])]
    parts[-1]+='\n\nCommon 91-country subset:\n\n'+table(['Model','Representation','Countries','Mean distance','Median distance'],[[LABELS[r.condition],r.representation,int(r.n),f(r.mean_distance),f(r.median_distance)] for r in d.itertuples()])
    d=read('tables/table_s16_tao_replication.csv')
    add(16,'Cultural prompting and the Tao benchmark',['Source/model','Representation','Countries','Without','With','Mean gain','Improved (%)'],[[LABELS.get(r.condition,'Tao GPT-4o'),r.representation,int(r.n_countries),f(r.unconditioned_distance_mean),f(r.country_conditioned_distance_mean),f(r.mean_distance_improvement),f(r.pct_countries_improved,1)] for r in d.itertuples()],
        'The published-point row is the external Tao et al. benchmark [1]. Current expected, aggregated-argmax and variant-wise modal estimates use different response representations. Sol has no complete default variant-wise modal profile and therefore no modal prompting comparison.')
    d=read('tables/table_s17_paired_contrasts.csv')
    add(17,'Paired cross-model contrasts',['Contrast','Metric','Cells','Mean difference','95% CI'],[[LABELS[r.condition_a]+' − '+LABELS[r.condition_b],VALUE_LABELS.get(r.metric,r.metric),int(r.n_country_item),f(r.mean_error_a_minus_b,4),f'[{f(r.ci95_low,4)}, {f(r.ci95_high,4)}]'] for r in d.itertuples()],
        'Differences are the first model minus the second; positive errors favour the second. Intervals use 5,000 crossed country-by-item bootstrap replicates. Each metric uses its common observed cells.')
    d=read('tables/table_s18_api_usage.csv')
    add(18,'Archived API usage',['Condition','Model identifier','Requests','Input tokens','Output tokens','Total tokens','Estimated US$'],[[LABELS.get(r.condition,'Jev Score (exploratory)'),r.model,int(r.requests),int(r.input_tokens),int(r.output_tokens),int(r.total_tokens),f(r.estimated_total_cost_usd,3)] for r in d.itertuples()],
        'Costs are dated list-price estimates, not provider-reported charges. Cached-input, cache-write and reasoning-token counts were zero in the archived ledger. Request identifiers are deduplicated; the joint Jev Y003 call is counted once. No revision analysis issued an API request.')
    d=read('tables/table_s19_cultural_deviation_summary.csv').set_index('condition')
    add(19,'Direction and magnitude of country deviations',['Model','Cells','Zero shifts','Positive direction %, 95% CI','Mean cosine, 95% CI','Pooled projection, 95% CI'],
        [[LABELS[c],int(d.loc[c,'n_cells']),int(d.loc[c,'n_zero_model_shift']),*[f"{d.loc[c,k]:.3f} [{d.loc[c,k+'_ci_low']:.3f}, {d.loc[c,k+'_ci_high']:.3f}]" for k in ['direction_correct_percent','cosine_mean','projection_pooled']]] for c in MODELS],
        'No primary cell has a human-deviation norm below 10⁻⁸. Zero shifts (norm ≤10⁻¹²) count as non-positive direction but are excluded from cosine means. Intervals use 5,000 crossed resamples. Projection is a ratio of sums.')
    d=read('tables/table_s19_cultural_deviation_by_item.csv')
    parts[-1]+='\n\n'+table(['Item','Model','Cells','Positive (%)','Mean cosine','Pooled projection'],[[r.item,LABELS[r.condition],int(r.n_cells),f(r.direction_correct_percent,1),f(r.cosine_mean),f(r.projection_pooled)] for r in d.itertuples()])
    d=read('tables/table_s20_temporal_target_sensitivity.csv')
    add(20,'Temporal target sensitivity',['Target','Model','Countries/cells','JSD','Default gain','Beat LOCO (%)','Positive (%)','Projection','Two-way slope'],[[VALUE_LABELS[r.target],LABELS[r.condition],f'{int(r.n_countries)}/{int(r.n_cells)}',f(r.js_mean),f(r.gain_vs_default_mean),f(r.pct_model_beats_loco,1),f(r.direction_correct_percent,1),f(r.projection_pooled),f(r.two_way_slope)] for r in d.itertuples()],
        'pooled_matched rows restrict the primary benchmark to the comparison target’s retained model-country-item cells. Their LOCO reference remains the primary equal-country benchmark; latest/wave7 rows rebuild LOCO within the available target universe. Full entropy, cosine, direction intervals and coverage diagnostics are retained in the CSV.')
    d=read('tables/table_s21_sample_size_summary.csv')
    add(21,'Human sample-size diagnostics',['Target','Item','Cells','Raw n min/median/max','Effective n min/median/max','Below 200/500/1000'],[[VALUE_LABELS[r.target],r.item,int(r.n_cells),f'{int(r.raw_n_min)}/{r.raw_n_median:.1f}/{int(r.raw_n_max)}',f'{r.effective_n_min:.1f}/{r.effective_n_median:.1f}/{r.effective_n_max:.1f}',f'{int(r.n_below_200)}/{int(r.n_below_500)}/{int(r.n_below_1000)}'] for r in d.itertuples()],
        'Effective n for equal-year targets is T²/Σ(1/n_eff,t), where each country-year Kish n_eff,t=(Σw)²/Σw². It measures weight dispersion, not complex-survey design effects. Complete country-year and country-item diagnostics accompany this summary as machine-readable Table S21 files.')
    d=read('tables/table_s22_entropy_leave_one_item_out.csv')
    add(22,'Every leave-one-item-out entropy fit',['Omitted item','Model','Cells','Two-way slope','Residual Pearson r','Residual Spearman rho'],[[r.omitted_item,LABELS[r.condition],int(r.n_cells),f(r.two_way_slope),f(r.two_way_pearson),f(r.two_way_spearman)] for r in d.itertuples()],
        'none denotes the full nine-item analysis. Every omitted-item fit re-estimates country and item effects. The companion summary CSV records minimum, median, maximum and the largest absolute change from the full fit for each statistic.')
    d=read('tables/table_s23_human_sampling_sensitivity.csv')
    add(23,'Human respondent-bootstrap sensitivity',['Metric','Model','Point','95% interval'],[[VALUE_LABELS.get(r.metric,r.metric),LABELS[r.condition],f(r.point_estimate,4),f'[{r.ci_low:.4f}, {r.ci_high:.4f}]'] for r in d.itertuples()],
        'All entries use 1,000 valid replicates. Coverage remains 963/946/963 cells for GPT-4o/Sol/Jev. These intervals condition on the countries, items, model probabilities and released S017 weights, and do not replace crossed-bootstrap or complex-survey intervals.')
    d=read('tables/table_s24_effective_sample_size_sensitivity.csv')
    add(24,'Minimum effective-sample sensitivity',['Minimum effective n','Model','Cells','JSD','Default gain','Beat LOCO (%)','Positive (%)','Projection','Two-way slope'],[[int(r.minimum_aggregate_n_eff),LABELS[r.condition],int(r.n_cells),f(r.js_mean),f(r.gain_vs_default_mean),f(r.pct_model_beats_loco,1),f(r.direction_correct_percent,1),f(r.projection_pooled),f(r.two_way_slope)] for r in d.itertuples()],
        'The threshold filters target-country items; the LOCO human benchmark continues to use all other primary-target countries. This isolates sensitivity to the precision of the target reference rather than simultaneously redefining the comparison population.')
    return '\n\n'.join(parts)+'\n'


def main_tables_text(results='results'):
    root=Path(results);read=lambda name:pd.read_csv(root/name)
    parts=['## Main tables']
    parts.append('### Table 1. Probability objects and interpretation\n\n'+table(
        ['Source','Probability object','Support','Interpretation'],[
            ['Human surveys','S017-weighted response frequencies, averaged equally across years','Substantive item categories','Between-person response heterogeneity in the historical target'],
            ['GPT-4o / Sol','Returned next-token mass mapped to labels and conditionally normalized','Observed permitted labels; explicit missing-mass policy','Model output uncertainty under a respondent prompt'],
            ['Jev','Full probability vector over declared Choice alternatives','All declared alternatives','Structured-choice uncertainty under the same descriptor design']])+ '\n\nA common response support permits comparison without establishing equivalent probability semantics. The interface comparison does not isolate architecture or demonstrate population calibration.')
    d=read('tables/table2_primary_summary.csv');d=d[d.representation.eq('full')].set_index('condition')
    contrasts=read('tables/table_s17_paired_contrasts.csv');contrasts=contrasts[contrasts.condition_a.eq('gpt56_sol')&contrasts.condition_b.eq('jev')].set_index('metric')
    fields=[('js','js_mean','JSD'),('tv','tv_mean','Total variation'),('wasserstein','wasserstein_mean','Normalized Wasserstein'),('expected_abs_error','expected_abs_error_mean','Absolute expected-score error'),('entropy_abs_error','entropy_abs_error_mean','Absolute entropy error')]
    rows=[]
    for metric,col,label in fields:
        r=contrasts.loc[metric];rows.append([label,*[f(d.loc[c,col]) for c in MODELS],f"{r.mean_error_a_minus_b:.4f} [{r.ci95_low:.4f}, {r.ci95_high:.4f}]",int(r.n_country_item)])
    parts.append('### Table 2. Distributional fidelity\n\n'+table(['Metric',*map(LABELS.get,MODELS),'Sol − Jev [95% CI]','Paired n'],rows)+'\n\nLower errors indicate greater fidelity. Marginal means use 963/946/963 cells for GPT-4o/Sol/Jev; Wasserstein excludes unordered trust. Paired differences need not equal differences of displayed marginal means. Score error is in original item units. Intervals use 5,000 crossed country/item resamples.')
    d=read('tables/table3_country_conditioning.csv').set_index('condition')
    parts.append('### Table 3. Cultural location and country-specific population signal\n\n'+table(['Model','Map distance without → with','Countries improved (%)','Map n','JSD without → with','Cells improved (%)','Cell n'],[[LABELS[c],f"{d.loc[c,'map_unconditioned_distance_mean']:.3f} → {d.loc[c,'map_country_conditioned_distance_mean']:.3f}",f(d.loc[c,'map_pct_countries_improved'],1),int(d.loc[c,'map_n_countries']),f"{d.loc[c,'distribution_unconditioned_js_mean']:.3f} → {d.loc[c,'distribution_country_conditioned_js_mean']:.3f}",f(d.loc[c,'distribution_pct_cells_improved'],1),int(d.loc[c,'n_country_item'])] for c in MODELS]))
    parts[-1]+='\n\n'+table(['Model','Positive direction (%)','Pooled projection','Default gain [95% CI]','LOCO JSD','Cells beating LOCO (%)'],[[LABELS[c],f(d.loc[c,'direction_correct_percent'],1),f(d.loc[c,'projection_pooled']),f"{d.loc[c,'gain_vs_default_mean']:.3f} [{d.loc[c,'gain_vs_default_ci95_low']:.3f}, {d.loc[c,'gain_vs_default_ci95_high']:.3f}]",f(d.loc[c,'loco_human_js_mean']),f(d.loc[c,'distribution_pct_model_beats_loco_human'],1)] for c in MODELS])+'\n\nMap contrasts use expected scores and matched countries. Positive JSD gain favours country conditioning. Direction compares model changes from their own default with human deviations from LOCO. Projection is a ratio of sums. Table S19 gives uncertainty and zero-shift counts; Table S20 gives temporal sensitivity.'
    return '\n\n'.join(parts)+'\n'
