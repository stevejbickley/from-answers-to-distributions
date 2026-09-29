# Data acquisition and version pinning

**Repository policy.** WVS, EVS and constructed IVS microdata are intentionally excluded from source control. Keep them in a separate local/restricted data directory and pass an absolute path with `--ivs`/`--wvs`/`--evs`, or set `IVS_DATA_PATH`, `WVS_DATA_PATH` and `EVS_DATA_PATH` in the local `.env`. The public repository should cite the source releases and explain acquisition, but should not redistribute the microdata. Generated aggregate tables and figures are produced from those external inputs.
`scripts/01_prepare_human.py` also writes `human_input_provenance.json` containing only each external input's filename, byte size and SHA-256 checksum (not its local path). This manifest can be archived with the code/results so another researcher can verify that they acquired the same release without the repository redistributing the dataset.

The replication targets the versions reported in the source study, not the newest files available in 2026:

- **World Values Survey trend file (1981–2022), data file version 3.0.0**, DOI: 10.14281/18241.23.
- **European Values Study trend file 1981–2017, ZA7503, data file version 3.0.0**, DOI: 10.4232/1.14021.

The source study combined WVS and EVS, retained the three most recent joint survey waves (2005–2022), retained observations from both sources for countries present in both, and used `S017` survey weights. Five countries/territories were omitted from the cultural-map analysis because at least one of the ten map variables lacked valid observations: Egypt, Kuwait, Qatar, Tajikistan, and Uzbekistan.

WVS/EVS files are not redistributed in this package. Download them from their official repositories under their applicable terms, then pass either an already harmonized IVS file via `--ivs`, or both trend files via `--wvs` and `--evs`.


The human-data preparation step additionally enforces the stated **2005–2022 calendar-year window** as well as common-wave codes 5–7. This matters for newer WVS Trend releases: the supplied v4.1 file contains a small number of interviews dated 2004 and 2023 within those common waves.

With the supplied EVS ZA7503 v3.0.0 and WVS Trend v4.1, the raw full merge contains 666,907 observations across all waves. Restricting to common waves 5–7 and years 2005–2022 yields 392,832 observations from 112 countries/territories before the cultural-map exclusions. This need not equal the source paper's reported 393,536 because the paper pins WVS Trend v3.0.0 whereas the supplied WVS file is v4.1; use v3.0.0 (or the authors' archived processed data) when exact sample-count replication is required, and treat v4.1 as a data-update robustness analysis.

## Required variables

`S001, S002VS, S003, S009, S017, S020, A008, A165, E018, E025, F063, F118, F120, G006, Y002, Y003, A029, A039, A040, A042`.

Y003 is reconstructed from its four constituent binary variables when necessary:

`Y003 = A029 + A039 - A040 - A042`.

## Version sensitivity

Current WVS downloads may contain later revisions and slightly different published rescaling constants. For direct replication, this package uses the constants stated in the 2024 source paper:

- `PC1' = 1.81 × PC1 + 0.38`
- `PC2' = 1.61 × PC2 − 0.01`

If you deliberately update the human benchmark to a newer WVS/EVS release, treat that as a robustness/update analysis and report it separately.

## Building the IVS file from EVS and WVS

Use `scripts/00_build_ivs.py` before `scripts/01_prepare_human.py` when starting from separate EVS/WVS Stata files. The merger parses the official EVS/WVS Stata merge syntax for the 838-variable schema and structural-missing rules, validates the common dictionary, writes provenance/QC files, and can stream to `.csv.gz` to avoid loading the complete IVS table in memory.

**Important:** `ZA7505_v5-0-0.dta` is the Joint EVS/WVS 2017–2022 file (EVS5 + WVS7), not the EVS Trend File expected by the official 1981–2022 IVS merge syntax. The script therefore refuses to treat ZA7505 as a full EVS history. With `--allow-partial-joint`, it extracts only `study==1` (EVS5), excludes the embedded WVS7 cases to avoid duplication, and produces an explicitly partial WVS1–7 + EVS5 dataset. For the full IVS benchmark used in the paper, supply the EVS Trend File containing EVS waves 1–5 (e.g. a ZA7503-compatible release).

The merger preserves the source missing codes `-1` to `-5` rather than converting them to Stata extended missings `.a`–`.e`; this is intentional for portable Python analysis. Structural `-4` (not asked) and `-3` (not applicable) values are applied from the official merge syntax. `src/human.py` filters negative substantive codes and reconstructs the EVS autonomy index (`Y003`) row-by-row from `A029 + A039 - A040 - A042` when the official merged `Y003` value is structurally unavailable.
