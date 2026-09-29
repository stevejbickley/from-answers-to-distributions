# EVS/WVS → IVS merger

`../scripts/00_build_ivs.py` is the replication package's guarded Python implementation of the supplied official EVS/WVS merge workflow.

## Full/canonical IVS

The official Stata syntax expects the **EVS Trend File covering EVS waves 1–5** plus the WVS Trend File. With the appropriate EVS Trend release:

```bash
python scripts/00_build_ivs.py \
  --evs data/raw/ZA7503_v3-0-0.dta \
  --wvs data/raw/Trends_VS_1981_2022_Stata_v4_1.dta \
  --merge-syntax "data/raw/EVS_WVS_Merge Syntax_stata.do" \
  --dictionary data/raw/F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx \
  --countries data/raw/F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx \
  --output data/processed/Integrated_values_surveys_1981-2022.csv.gz
```

Then prepare the human benchmark with:

```bash
python scripts/01_prepare_human.py \
  --ivs data/processed/Integrated_values_surveys_1981-2022.csv.gz \
  --csv \
  --outdir data/processed
```


### Verified against ZA7503 v3.0.0

The merger has been executed successfully against `ZA7503_v3-0-0.dta` (EVS Trend File 1981–2017, 224,434 records, 635 source variables) together with the supplied WVS Trend v4.1 file. In `--core-only` mode it produces 666,907 merged records (224,434 EVS + 442,473 WVS); a full-schema smoke test materialises all 838 official IVS variables without dtype warnings.

Use the **original** `ZA7503_v3-0-0.dta` as the input. The accompanying `ZA7503_v3-0-0_missing.do` is not required: the Python merger deliberately preserves the source `-1`…`-5` missing-reason codes and applies the official structural `-3`/`-4` rules itself. Running the Stata missing-value conversion first would convert these codes to Stata extended missings and is therefore not the recommended Python path.

## The currently supplied ZA7505 file

`ZA7505_v5-0-0.dta` is the **Joint EVS/WVS 2017–2022** dataset: it contains EVS5 (`study==1`) and WVS7 (`study==2`). It is not a replacement for the EVS 1981–2017 Trend File. The merger therefore refuses to call it a full IVS input by default.

For a diagnostic/partial dataset using exactly the currently supplied files:

```bash
python scripts/00_build_ivs.py \
  --evs data/raw/ZA7505_v5-0-0.dta \
  --wvs data/raw/Trends_VS_1981_2022_Stata_v4_1.dta \
  --merge-syntax "data/raw/EVS_WVS_Merge Syntax_stata.do" \
  --dictionary data/raw/F00011424-Common_EVS_WVS_Dictionary_IVS.xlsx \
  --countries data/raw/F00011426-EVS_WVS_ParticipatingCountries_June2024.xlsx \
  --allow-partial-joint \
  --output data/processed/IVS_PARTIAL_WVS1-7_EVS5.csv.gz
```

This extracts only the EVS5 observations and explicitly excludes the WVS7 observations already embedded in ZA7505, because WVS7 is already present in the WVS Trend File. The output is **not** the full IVS because EVS1–4 are absent.

Add `--core-only` for a smaller 22-variable dataset containing the fields required by the cultural-values replication. Every run also writes a JSON provenance manifest, wave/year row counts, and core-variable missing-code diagnostics next to the output.
