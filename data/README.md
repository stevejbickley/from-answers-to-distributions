# Human survey data are intentionally not stored in this repository

The WVS, EVS and any locally constructed IVS microdata are licensed/source-controlled inputs and are **not redistributed here**.

For full end-to-end replication, obtain the cited releases from the World Values Survey and European Values Study repositories under their applicable terms. Store them outside this repository and either:

1. set `IVS_DATA_PATH=/absolute/path/to/your/IVS_file.dta` in `.env`, or
2. pass `--ivs /absolute/path/to/your/IVS_file.dta` to `scripts/run_all.py`.

If rebuilding IVS from separate source files, use `scripts/00_build_ivs.py` with the external WVS/EVS paths. The generated IVS should also remain outside source control.

The repository may contain code, configuration, provenance/checksum manifests, manuscript text, and generated aggregate tables/figures. It does not contain the licensed raw microdata.
