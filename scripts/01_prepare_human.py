import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, hashlib, json
from src.human import load_ivsd, clean, save_processed, build_country_universe
from src.cultural_map import fit_pca
from src.config import country_universe


def file_manifest(path):
    p = Path(path).expanduser().resolve()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return {'filename':p.name,'size_bytes':p.stat().st_size,'sha256':h.hexdigest()}


p = argparse.ArgumentParser()
p.add_argument('--ivs')
p.add_argument('--wvs')
p.add_argument('--evs')
p.add_argument('--csv', action='store_true')
p.add_argument('--outdir', default='data/processed')
a = p.parse_args()

df, metas = load_ivsd(a.ivs, a.wvs, a.evs, csv=a.csv)
df = clean(df)
universe = build_country_universe(df, strict=True)
save_processed(df, metas, a.outdir, universe=universe)

# Fit the human PCA on the full cleaned 2005-2022 individual-level benchmark,
# before the five source-study country exclusions are applied to downstream
# country-level/model comparisons.
pca = fit_pca(df)
serial = {k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in pca.items()}
outdir = Path(a.outdir)
outdir.mkdir(parents=True, exist_ok=True)
(outdir / 'pca_model.json').write_text(json.dumps(serial, indent=2), encoding='utf-8')

inputs = {}
if a.ivs:
    inputs['ivs'] = file_manifest(a.ivs)
if a.wvs:
    inputs['wvs'] = file_manifest(a.wvs)
if a.evs:
    inputs['evs'] = file_manifest(a.evs)

ucfg = country_universe()
included = universe.loc[universe['included_for_analysis']].copy()
excluded = universe.loc[~universe['included_for_analysis']].copy()
(outdir / 'human_input_provenance.json').write_text(json.dumps({
    'note': 'Paths are intentionally omitted so this manifest can be shared without exposing local/restricted storage locations.',
    'inputs': inputs,
    'analysis_window': {'year_min': 2005, 'year_max': 2022, 'common_waves': [5, 6, 7]},
    'prepared_records': int(len(df)),
    'country_universe': {
        'canonical_identity_variable': 'S003',
        'pre_exclusion_count': int(len(universe)),
        'post_exclusion_count': int(len(included)),
        'expected_pre_exclusion_count': int(ucfg['expected_pre_exclusion_count']),
        'expected_post_exclusion_count': int(ucfg['expected_post_exclusion_count']),
        'excluded_country_ids': [int(x) for x in excluded['country_id'].tolist()],
        'excluded_countries': excluded['country'].tolist(),
        'country_universe_file': 'human_country_universe.csv'
    }
}, indent=2), encoding='utf-8')

print('Prepared', len(df), 'human records')
print('IVS entities before exclusions:', len(universe))
print('Excluded source-study cultural-map entities:', len(excluded), '-', ', '.join(excluded['country'].tolist()))
print('Country/territory analysis targets:', len(included))
print('Wrote validated country universe to', outdir / 'human_country_universe.csv')
print('Wrote shareable input checksums to', outdir / 'human_input_provenance.json')
