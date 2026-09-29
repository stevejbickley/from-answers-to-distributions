# Publication output inventory

Validated 43 CSV files and 15 canonical figures in three formats.

| File | Rows | Columns | Missing entries |
|---|---:|---:|---:|
| `results/api_request_usage.csv` | 95,186 | 26 | 96,482 |
| `results/api_usage_summary.csv` | 4 | 16 | 4 |
| `results/country_item_metrics.csv` | 5,744 | 19 | 642 |
| `results/country_item_metrics_censoring_sensitivity.csv` | 9,612 | 20 | 1,114 |
| `results/cultural_map_common_country_summary.csv` | 9 | 6 | 0 |
| `results/cultural_map_coordinates.csv` | 982 | 8 | 723 |
| `results/cultural_map_distances.csv` | 867 | 6 | 0 |
| `results/cultural_map_prompting_distances.csv` | 824 | 9 | 0 |
| `results/cultural_map_prompting_summary.csv` | 8 | 12 | 0 |
| `results/cultural_map_tao_style_variant_coordinates.csv` | 2,247 | 8 | 0 |
| `results/entropy_structure_by_country.csv` | 321 | 7 | 0 |
| `results/entropy_structure_by_item.csv` | 27 | 9 | 0 |
| `results/entropy_structure_summary.csv` | 3 | 45 | 0 |
| `results/model_mean_probabilities.csv` | 15,720 | 10 | 0 |
| `results/model_y003_mean_marginals.csv` | 1,296 | 9 | 0 |
| `results/openai_censoring_policy_counts.csv` | 6 | 6 | 0 |
| `results/openai_censoring_sensitivity_summary.csv` | 6 | 8 | 0 |
| `results/openai_label_sensitivity.csv` | 46,965 | 7 | 1,770 |
| `results/openai_logprob_diagnostics.csv` | 75,600 | 25 | 94,662 |
| `results/option_order_coverage.csv` | 324 | 9 | 0 |
| `results/option_order_metrics.csv` | 805 | 8 | 0 |
| `results/population_specificity_metrics.csv` | 2,872 | 11 | 0 |
| `results/prompt_sensitivity.csv` | 27,082 | 8 | 24 |
| `results/tables/table2_primary_summary.csv` | 6 | 15 | 0 |
| `results/tables/table3_country_conditioning.csv` | 3 | 15 | 0 |
| `results/tables/table3_population_specificity.csv` | 3 | 17 | 0 |
| `results/tables/table_s10_entropy_structure.csv` | 3 | 45 | 0 |
| `results/tables/table_s11_entropy_by_item.csv` | 27 | 9 | 0 |
| `results/tables/table_s12_population_specificity_by_item.csv` | 27 | 10 | 0 |
| `results/tables/table_s13_label_sensitivity.csv` | 18 | 7 | 0 |
| `results/tables/table_s14_option_order_sensitivity.csv` | 26 | 6 | 0 |
| `results/tables/table_s15_cultural_map.csv` | 9 | 6 | 0 |
| `results/tables/table_s16_tao_replication.csv` | 9 | 9 | 0 |
| `results/tables/table_s1_survey_constructs.csv` | 10 | 5 | 0 |
| `results/tables/table_s2_prompt_variants.csv` | 10 | 3 | 0 |
| `results/tables/table_s3_openai_diagnostics.csv` | 2 | 12 | 0 |
| `results/tables/table_s4_openai_censoring_sensitivity.csv` | 6 | 8 | 0 |
| `results/tables/table_s5_full_vs_argmax.csv` | 3 | 8 | 0 |
| `results/tables/table_s6_item_summary.csv` | 27 | 9 | 3 |
| `results/tables/table_s7_country_summary.csv` | 321 | 7 | 0 |
| `results/tables/table_s8_prompt_sensitivity.csv` | 27 | 8 | 0 |
| `results/tables/table_s9_y003.csv` | 12 | 6 | 0 |
| `results/y003_marginal_metrics.csv` | 1,284 | 11 | 0 |

## Interpretation notes

- Wasserstein is undefined for unordered A165.
- Prompt/label singleton groups remain in diagnostic files with undefined sensitivity.
- No retained Sol F120 order-0 reference: order sensitivity is not estimable for that item.
- Sol entropy CIs use only nine item clusters and asymptotic normal critical values.
- Tao-style Sol modal map uses 43 countries and lacks an unconditioned profile; it is not a paired prompting estimate.
- Main condition means have different coverage; inferential contrasts use matched cells.
- Expected-score and aggregated-argmax map common-country summaries use 91 countries.
- Provider-reported dollar costs are unavailable; dated list-price estimates are separate.
