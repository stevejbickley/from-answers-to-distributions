# Cultural regions from Tao et al.

`tao_cultural_regions.csv` is the country lookup `s003.csv` from Tao et al.'s
public research archive, downloaded on 29 September 2026:
https://osf.io/7sj3w/ (file https://osf.io/download/zqaxf/).

Source: Tao Y, Viberg O, Baker RS, Kizilcec RF (2024). Cultural bias and cultural
alignment of large language models. PNAS Nexus 3, pgae346.
https://doi.org/10.1093/pnasnexus/pgae346

The 107 assignments are joined through canonical S003 numeric identifiers.
Names displayed in this study follow `config/countries.yaml`.
These broad categories reproduce the source figure's classifications and do not
assert cultural homogeneity within a country. They do not enter any calculation.

Colours are from `Analysis_Script_OSF.R`, lines 104–105 and 479
(https://osf.io/download/wa74z/). Without cultural prompting is `#CC79A7`;
with cultural prompting is `#0072B2`. Figure 1 uses the same eight region colours.
