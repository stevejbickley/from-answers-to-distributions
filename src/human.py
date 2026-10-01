from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
from .config import questions, analysis, country_universe
from .utils import ensure_dir

CORE_VARS = [
    'S001','S002VS','S003','S009','S017','S020',
    'A008','A165','E018','E025','F063','F118','F120','G006','Y002','Y003',
    'A029','A039','A040','A042'
]


def _read(path, csv=False):
    """Read human data.

    For CSV/CSV.GZ IVS files, read only variables used by this study. This avoids
    dtype warnings from hundreds of unused administrative variables and reduces
    memory use substantially. Stata/SPSS inputs retain metadata, so those are
    read through pyreadstat as before.
    """
    path = Path(path)
    name = path.name.lower()
    if csv or name.endswith('.csv') or name.endswith('.csv.gz'):
        wanted = set(CORE_VARS + ['SOURCE'])
        df = pd.read_csv(path, usecols=lambda c: c in wanted, low_memory=False)
        return df, None
    import pyreadstat
    if path.suffix.lower() == '.dta':
        df, meta = pyreadstat.read_dta(path, usecols=None, apply_value_formats=False)
        return df, meta
    if path.suffix.lower() == '.sav':
        df, meta = pyreadstat.read_sav(path, usecols=None, apply_value_formats=False)
        return df, meta
    raise ValueError(f'Unsupported human-data format: {path}. Use .dta, .sav, .csv, or .csv.gz')


def load_ivsd(ivs=None, wvs=None, evs=None, csv=False):
    if ivs:
        df, meta = _read(ivs, csv=csv)
        if 'SOURCE' not in df.columns:
            df = df.assign(SOURCE='IVS')
        else:
            df = df.copy()
            df['SOURCE'] = df['SOURCE'].fillna('IVS')
        return df, {'IVS': meta}
    if not (wvs and evs):
        raise ValueError('Provide --ivs OR both --wvs and --evs')
    wdf, wm = _read(wvs)
    edf, em = _read(evs)
    wdf = wdf.assign(SOURCE='WVS')
    edf = edf.assign(SOURCE='EVS')
    cols = sorted(set(wdf.columns).intersection(edf.columns))
    return pd.concat([wdf[cols], edf[cols]], ignore_index=True), {'WVS': wm, 'EVS': em}


def _valid_numeric(s, allowed):
    x = pd.to_numeric(s, errors='coerce')
    return x.where(x.isin(allowed))


def clean(df):
    cfg = analysis()
    qs = questions()
    out = df.copy()

    required = {
        cfg['wave_variable'], cfg['weight_variable'], cfg['year_variable'], *cfg['primary_items'],
        'A029', 'A039', 'A040', 'A042'
    }
    # Y003 itself may be structurally unavailable because it can be reconstructed
    # from A029/A039/A040/A042. All other required variables must exist.
    required.discard('Y003')
    missing = sorted(c for c in required if c not in out.columns)
    if missing:
        raise ValueError(f'Human input is missing required study variables: {missing}')

    if cfg['wave_variable'] in out.columns:
        out = out[pd.to_numeric(out[cfg['wave_variable']], errors='coerce').isin(cfg['wave_codes'])].copy()

    # Explicitly enforce the source-study calendar window. Newer WVS Trend
    # releases can contain a small number of interviews dated 2004 or 2023
    # inside common waves 5/7, so wave codes alone are insufficient.
    if cfg.get('year_min') is not None or cfg.get('year_max') is not None:
        y = pd.to_numeric(out[cfg['year_variable']], errors='coerce')
        keep = y.notna()
        if cfg.get('year_min') is not None:
            keep &= y.ge(cfg['year_min'])
        if cfg.get('year_max') is not None:
            keep &= y.le(cfg['year_max'])
        out = out.loc[keep].copy()

    for item, q in qs.items():
        if item in out.columns:
            out[item] = _valid_numeric(out[item], q['human_codes'])
    for v in ['A029', 'A039', 'A040', 'A042']:
        if v in out.columns:
            out[v] = _valid_numeric(out[v], [0, 1])

    # Y003 is structurally unavailable for some EVS rows in the official merged
    # file, while the four binary constituents are present. Reconstruct it only
    # where the official value is missing/invalid and all constituents are valid.
    if all(v in out.columns for v in ['A029', 'A039', 'A040', 'A042']):
        vals = [_valid_numeric(out[v], [0, 1]) for v in ['A029', 'A039', 'A040', 'A042']]
        derived = vals[0] + vals[1] - vals[2] - vals[3]
        if 'Y003' not in out.columns:
            out['Y003'] = derived
        else:
            existing = pd.to_numeric(out['Y003'], errors='coerce')
            out['Y003'] = existing.where(existing.notna(), derived)

    out[cfg['weight_variable']] = pd.to_numeric(out[cfg['weight_variable']], errors='coerce').fillna(1.0)
    out.loc[out[cfg['weight_variable']] <= 0, cfg['weight_variable']] = np.nan
    out[cfg['year_variable']] = pd.to_numeric(out[cfg['year_variable']], errors='coerce')
    if cfg['country_variable'] in out.columns:
        out[cfg['country_variable']] = pd.to_numeric(out[cfg['country_variable']], errors='coerce').astype('Int64')
    return out


def build_country_universe(df, strict=True):
    """Construct the frozen source-study country/territory universe using S003.

    S003 is the canonical identity key. S009 is retained only as source metadata
    because it contains aliases such as GB/GB-GBN and NIR/GB-NIR that otherwise
    split one S003 entity into multiple API prompt targets.
    """
    cfg = analysis()
    ucfg = country_universe()
    cvar = cfg['country_variable']
    avar = cfg['country_alpha_variable']

    ids = pd.to_numeric(df[cvar], errors='coerce').dropna().astype(int)
    observed_ids = set(ids.unique().tolist())
    configured_names = {int(k): str(v) for k, v in ucfg['countries'].items()}
    expected_ids = set(configured_names)

    missing_ids = sorted(expected_ids - observed_ids)
    unexpected_ids = sorted(observed_ids - expected_ids)
    if strict and (missing_ids or unexpected_ids):
        raise ValueError(
            'The cleaned 2005-2022 IVS country universe does not match the frozen '
            f'source-study universe. Missing S003 IDs={missing_ids}; unexpected S003 IDs={unexpected_ids}. '
            'Check the IVS build/data release before making API calls.'
        )

    active_ids = sorted(observed_ids & expected_ids) if not strict else sorted(expected_ids)
    excluded_ids = {int(x) for x in ucfg.get('excluded_country_ids', [])}

    counts = pd.to_numeric(df[cvar], errors='coerce').value_counts(dropna=True).to_dict()
    alpha_by_id = {}
    if avar in df.columns:
        tmp = df[[cvar, avar]].copy()
        tmp[cvar] = pd.to_numeric(tmp[cvar], errors='coerce').astype('Int64')
        for cid, g in tmp.dropna(subset=[cvar]).groupby(cvar):
            vals = sorted({str(x).strip() for x in g[avar].dropna() if str(x).strip()})
            alpha_by_id[int(cid)] = ';'.join(vals)

    rows = []
    for cid in active_ids:
        excluded = cid in excluded_ids
        rows.append({
            'country_id': cid,
            'country': configured_names[cid],
            'alpha_codes_observed': alpha_by_id.get(cid, ''),
            'n_records_2005_2022': int(counts.get(cid, 0)),
            'included_for_analysis': not excluded,
            'exclusion_reason': ucfg.get('exclusion_reason', '') if excluded else '',
        })
    universe = pd.DataFrame(rows).sort_values(['country_id']).reset_index(drop=True)

    if strict:
        pre = len(universe)
        post = int(universe['included_for_analysis'].sum())
        exp_pre = int(ucfg['expected_pre_exclusion_count'])
        exp_post = int(ucfg['expected_post_exclusion_count'])
        if pre != exp_pre or post != exp_post:
            raise ValueError(
                f'Country-universe validation failed: got {pre} pre-exclusion and {post} post-exclusion; '
                f'expected {exp_pre} and {exp_post}.'
            )
    return universe


def _attach_country_identity(df, universe):
    cfg = analysis()
    cvar = cfg['country_variable']
    out = df.copy()
    out['COUNTRY_ID'] = pd.to_numeric(out[cvar], errors='coerce').astype('Int64')
    name_map = dict(zip(universe['country_id'].astype(int), universe['country']))
    out['COUNTRY_NAME'] = out['COUNTRY_ID'].map(name_map)
    return out


def _analysis_subset(df, universe):
    included = set(universe.loc[universe['included_for_analysis'], 'country_id'].astype(int))
    out = _attach_country_identity(df, universe)
    return out[out['COUNTRY_ID'].isin(included) & out['COUNTRY_NAME'].notna()].copy()


def load_analysis_country_targets(universe_path='data/processed/human_country_universe.csv', expected_count=None):
    """Load and validate the exact country/territory names used for API prompting."""
    ucfg = country_universe()
    expected = int(expected_count or ucfg['expected_post_exclusion_count'])
    p = Path(universe_path)
    if not p.exists():
        raise FileNotFoundError(
            f'{p} not found. Run scripts/01_prepare_human.py first so the validated '
            'country universe is created before model collection.'
        )
    u = pd.read_csv(p)
    required = {'country_id', 'country', 'included_for_analysis'}
    missing = required - set(u.columns)
    if missing:
        raise ValueError(f'{p} is missing required columns: {sorted(missing)}')
    inc = u['included_for_analysis']
    if inc.dtype != bool:
        inc = inc.astype(str).str.strip().str.lower().isin({'true', '1', 'yes', 'y'})
    use = u.loc[inc, ['country_id', 'country']].copy()
    if use['country_id'].duplicated().any() or use['country'].duplicated().any():
        raise ValueError('Validated country universe contains duplicate included country IDs or prompt names.')
    if len(use) != expected:
        raise ValueError(f'Expected {expected} included country/territory targets, found {len(use)} in {p}.')
    return sorted(use['country'].astype(str).tolist())


def weighted_distribution(x, w, levels):
    x = pd.to_numeric(x, errors='coerce')
    w = pd.to_numeric(w, errors='coerce')
    mask = x.isin(levels) & w.notna() & (w > 0)
    if not mask.any():
        return None
    numer = {str(k): float(w[mask & (x == k)].sum()) for k in levels}
    den = sum(numer.values())
    return {k: v / den for k, v in numer.items()} if den > 0 else None


def make_country_item_distributions(df, metas=None, universe=None):
    cfg = analysis()
    qs = questions()
    universe = build_country_universe(df, strict=True) if universe is None else universe
    work = _analysis_subset(df, universe)
    wvar = cfg['weight_variable']
    yvar = cfg['year_variable']
    rows = []
    # Within each country-year use survey weights, then average country-year
    # distributions equally within country, matching the intended source-study logic.
    for (cid, country, year), g in work.groupby(['COUNTRY_ID', 'COUNTRY_NAME', yvar], dropna=True):
        for item in cfg['primary_items']:
            levels = qs[item]['human_codes']
            d = weighted_distribution(g[item], g[wvar], levels)
            if d:
                for response, prob in d.items():
                    rows.append({
                        'country_id': int(cid), 'country': country, 'year': int(year),
                        'item': item, 'response': response, 'p': prob
                    })
    cy = pd.DataFrame(rows)
    if cy.empty:
        raise ValueError('No valid human country-year distributions were constructed.')
    country = cy.groupby(['country_id', 'country', 'item', 'response'], as_index=False)['p'].mean()
    country['p'] = country['p'] / country.groupby(['country_id', 'country', 'item'])['p'].transform('sum')
    return cy, country


def y003_constituent_marginals(df, metas=None, universe=None):
    cfg = analysis()
    qs = questions()
    universe = build_country_universe(df, strict=True) if universe is None else universe
    work = _analysis_subset(df, universe)
    rows = []
    for (cid, country, year), g in work.groupby(['COUNTRY_ID', 'COUNTRY_NAME', cfg['year_variable']], dropna=True):
        for quality, var in qs['Y003']['constituents'].items():
            d = weighted_distribution(g[var], g[cfg['weight_variable']], [0, 1])
            if d:
                rows.append({
                    'country_id': int(cid), 'country': country, 'year': int(year),
                    'quality': quality, 'variable': var, 'p_selected': d.get('1', 0.0)
                })
    cy = pd.DataFrame(rows)
    if cy.empty:
        raise ValueError('No valid Y003 constituent marginals were constructed.')
    country = cy.groupby(['country_id', 'country', 'quality', 'variable'], as_index=False)['p_selected'].mean()
    return cy, country


def save_processed(df, metas, outdir, universe=None):
    outdir = ensure_dir(outdir)
    universe = build_country_universe(df, strict=True) if universe is None else universe
    universe.to_csv(outdir / 'human_country_universe.csv', index=False)
    cy, country = make_country_item_distributions(df, metas, universe=universe)
    ycy, yco = y003_constituent_marginals(df, metas, universe=universe)
    cy.to_csv(outdir / 'human_country_year_distributions.csv', index=False)
    country.to_csv(outdir / 'human_country_distributions.csv', index=False)
    ycy.to_csv(outdir / 'human_y003_country_year_marginals.csv', index=False)
    yco.to_csv(outdir / 'human_y003_country_marginals.csv', index=False)
    return cy, country, ycy, yco


def select_human_target(df, mode='pooled_equal_year', universe=None):
    """Select a temporal target from already-cleaned, harmonised microdata.

    Latest selects the latest observed calendar year for the country, not the
    latest nonmissing year separately for each item. Wave 7 retains equal-year
    aggregation within that wave. Neither changes the frozen model prompts.
    """
    cfg = analysis()
    universe = build_country_universe(df) if universe is None else universe
    work = _analysis_subset(df, universe)
    if mode == 'latest_available':
        latest = work.groupby('COUNTRY_ID')[cfg['year_variable']].transform('max')
        work = work.loc[work[cfg['year_variable']].eq(latest)].copy()
    elif mode == 'wave7':
        work = work.loc[work[cfg['wave_variable']].eq(7)].copy()
    elif mode != 'pooled_equal_year':
        raise ValueError(f'Unknown human target: {mode}')
    return work


def human_target_diagnostics(df, mode='pooled_equal_year', universe=None):
    """Return equal-year probabilities plus country-year/item sample diagnostics.

    aggregate_n_eff = T^2 / sum_t(1 / kish_n_eff_t), for equal-year averaging.
    This is a weight-dispersion diagnostic, not a complex-survey design effect.
    """
    cfg, qs = analysis(), questions()
    work = select_human_target(df, mode, universe)
    rows, probabilities = [], []
    for (cid, country, year), g in work.groupby(['COUNTRY_ID', 'COUNTRY_NAME', cfg['year_variable']]):
        for item in cfg['primary_items']:
            valid = g[item].isin(qs[item]['human_codes']) & g[cfg['weight_variable']].gt(0)
            x = g.loc[valid, item].to_numpy(float)
            w = g.loc[valid, cfg['weight_variable']].to_numpy(float)
            if not len(w):
                continue
            sw, sw2 = float(w.sum()), float(w @ w)
            base = {'target':mode, 'country_id':int(cid), 'country':country, 'year':int(year), 'item':item}
            rows.append({**base, 'raw_n':len(w), 'sum_weight':sw, 'sum_weight_sq':sw2,
                         'kish_n_eff':sw * sw / sw2})
            for level in qs[item]['human_codes']:
                probabilities.append({**base, 'response':str(level), 'p':float(w[x == level].sum() / sw)})
    if not rows:
        raise ValueError(f'No usable observations for human target {mode}')
    cy = pd.DataFrame(rows)
    aggregate = []
    for (cid, country, item), g in cy.groupby(['country_id', 'country', 'item']):
        aggregate.append({'target':mode, 'country_id':cid, 'country':country, 'item':item,
                          'raw_n':int(g.raw_n.sum()), 'sum_weight':g.sum_weight.sum(),
                          'sum_weight_sq':g.sum_weight_sq.sum(), 'n_years':len(g),
                          'year_min':int(g.year.min()), 'year_max':int(g.year.max()),
                          'kish_n_eff_pooled_weights':g.sum_weight.sum() ** 2 / g.sum_weight_sq.sum(),
                          'aggregate_n_eff':len(g) ** 2 / (1 / g.kish_n_eff).sum()})
    probs = (pd.DataFrame(probabilities)
             .groupby(['target', 'country_id', 'country', 'item', 'response'], as_index=False).p.mean())
    return probs, cy, pd.DataFrame(aggregate)


def bootstrap_human_probabilities(df, *, universe=None, reps=1000, seed=20260930,
                                  batch_size=100, progress=None):
    """Uniform respondent bootstrap within country-year, retaining survey weights.

    A single respondent multiplicity applies jointly to every item, preserving
    cross-item sampling dependence. No raw records are written. The returned
    tensor contains aggregate probabilities only: replicate x country x item x
    category, padded with zeros beyond each item's substantive support.
    """
    cfg, qs = analysis(), questions()
    work = select_human_target(df, 'pooled_equal_year', universe)
    countries = sorted(work.COUNTRY_NAME.unique())
    items = list(cfg['primary_items'])
    nc, ni, nk = len(countries), len(items), max(len(qs[j]['human_codes']) for j in items)
    index = {c:i for i,c in enumerate(countries)}
    result = np.zeros((reps, nc, ni, nk), dtype=float)
    years = np.zeros((nc, ni), dtype=int)
    rng = np.random.default_rng(seed)
    groups = list(work.groupby(['COUNTRY_NAME', cfg['year_variable']], sort=True))
    for gi, ((country, year), g) in enumerate(groups):
        weights = g[cfg['weight_variable']].to_numpy(float)
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 0.)
        n = len(g)
        # Indicator-weight matrix allows shared respondent draws across items.
        design = np.zeros((n, ni * nk), dtype=float)
        available = []
        for j, item in enumerate(items):
            vals = g[item].to_numpy(float)
            for k, code in enumerate(qs[item]['human_codes']):
                design[:, j * nk + k] = weights * (vals == code)
            if design[:, j * nk:(j + 1) * nk].sum() > 0:
                available.append(j)
                years[index[country], j] += 1
        for start in range(0, reps, batch_size):
            stop = min(start + batch_size, reps)
            multiplicities = rng.multinomial(n, np.full(n, 1 / n), size=stop - start)
            counts = (multiplicities @ design).reshape(stop - start, ni, nk)
            den = counts.sum(axis=-1, keepdims=True)
            estimates = np.divide(counts, den, out=np.full_like(counts, np.nan), where=den > 0)
            for j in available:
                result[start:stop, index[country], j] += estimates[:, j]
        if progress and ((gi + 1) % 25 == 0 or gi + 1 == len(groups)):
            progress(f'Respondent bootstrap: {gi + 1}/{len(groups)} country-years')
    result = np.divide(result, years[None, :, :, None], out=np.full_like(result, np.nan),
                       where=years[None, :, :, None] > 0)
    return result, countries, items
