# Data acquisition and version pinning

The replication targets the versions reported in the source study, not the newest files available in 2026:

- **World Values Survey trend file (1981–2022), data file version 3.0.0**, DOI: 10.14281/18241.23.
- **European Values Study trend file 1981–2017, ZA7503, data file version 3.0.0**, DOI: 10.4232/1.14021.

The source study combined WVS and EVS, retained the three most recent joint survey waves (2005–2022), retained observations from both sources for countries present in both, and used `S017` survey weights. Five countries/territories were omitted from the cultural-map analysis because at least one of the ten map variables lacked valid observations: Egypt, Kuwait, Qatar, Tajikistan, and Uzbekistan.

WVS/EVS files are not redistributed in this package. Download them from their official repositories under their applicable terms, then pass either an already harmonized IVS file via `--ivs`, or both trend files via `--wvs` and `--evs`.

## Required variables

`S001, S002VS, S003, S009, S017, S020, A008, A165, E018, E025, F063, F118, F120, G006, Y002, Y003, A029, A039, A040, A042`.

Y003 is reconstructed from its four constituent binary variables when necessary:

`Y003 = A029 + A039 - A040 - A042`.

## Version sensitivity

Current WVS downloads may contain later revisions and slightly different published rescaling constants. For direct replication, this package uses the constants stated in the 2024 source paper:

- `PC1' = 1.81 × PC1 + 0.38`
- `PC2' = 1.61 × PC2 − 0.01`

If you deliberately update the human benchmark to a newer WVS/EVS release, treat that as a robustness/update analysis and report it separately.
