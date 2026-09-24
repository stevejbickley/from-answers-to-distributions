from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from .config import questions, analysis
from .utils import ensure_dir

CORE_VARS = ['S001','S002VS','S003','S009','S017','S020',
             'A008','A165','E018','E025','F063','F118','F120','G006','Y002','Y003',
             'A029','A039','A040','A042']

def _read(path, csv=False):
    path=Path(path)
    if csv or path.suffix.lower()=='.csv':
        return pd.read_csv(path), None
    import pyreadstat
    df, meta = pyreadstat.read_sav(path, usecols=None, apply_value_formats=False)
    return df, meta

def load_ivsd(ivs=None, wvs=None, evs=None, csv=False):
    if ivs:
        df, meta = _read(ivs, csv=csv)
        df['SOURCE'] = df.get('SOURCE','IVS')
        return df, {'IVS':meta}
    if not (wvs and evs):
        raise ValueError('Provide --ivs OR both --wvs and --evs')
    wdf, wm = _read(wvs); edf, em = _read(evs)
    wdf['SOURCE']='WVS'; edf['SOURCE']='EVS'
    cols=sorted(set(wdf.columns).intersection(edf.columns))
    return pd.concat([wdf[cols], edf[cols]], ignore_index=True), {'WVS':wm,'EVS':em}

def _valid_numeric(s, allowed):
    x=pd.to_numeric(s, errors='coerce')
    return x.where(x.isin(allowed))

def clean(df):
    cfg=analysis(); qs=questions(); out=df.copy()
    if cfg['wave_variable'] in out.columns:
        out=out[pd.to_numeric(out[cfg['wave_variable']], errors='coerce').isin(cfg['wave_codes'])].copy()
    for item,q in qs.items():
        if item in out.columns:
            out[item] = _valid_numeric(out[item], q['human_codes'])
    for v in ['A029','A039','A040','A042']:
        if v in out.columns:
            out[v] = _valid_numeric(out[v], [0,1])
    if 'Y003' not in out.columns or out['Y003'].isna().all():
        if all(v in out.columns for v in ['A029','A039','A040','A042']):
            out['Y003'] = out['A029'] + out['A039'] - out['A040'] - out['A042']
    out[cfg['weight_variable']] = pd.to_numeric(out[cfg['weight_variable']], errors='coerce').fillna(1.0)
    out.loc[out[cfg['weight_variable']]<=0, cfg['weight_variable']] = np.nan
    out[cfg['year_variable']] = pd.to_numeric(out[cfg['year_variable']], errors='coerce')
    return out

def _country_name_series(df, metas):
    cfg=analysis(); cvar=cfg['country_variable']
    # Prefer official S003 value labels because prompts need readable country names, not alpha/numeric codes.
    labels={}
    for m in metas.values():
        if m is not None:
            try:
                labels.update(m.variable_value_labels.get(cvar,{}) or {})
            except Exception:
                pass
    if labels:
        return df[cvar].map(labels).fillna(df[cvar].astype(str))
    # CSV/processed inputs may already contain country names.
    if cvar in df.columns and df[cvar].dtype == object:
        return df[cvar].astype(str)
    # Fall back to S009 alpha codes and expand through pycountry where possible.
    avar=cfg['country_alpha_variable']
    if avar in df.columns:
        try:
            import pycountry
            def lookup(x):
                z=str(x).strip()
                c=pycountry.countries.get(alpha_2=z.upper())
                return c.name if c else z
            return df[avar].map(lookup)
        except Exception:
            return df[avar].astype(str)
    return df[cvar].astype(str)

def weighted_distribution(x, w, levels):
    x=pd.to_numeric(x, errors='coerce'); w=pd.to_numeric(w, errors='coerce')
    mask=x.isin(levels) & w.notna() & (w>0)
    if not mask.any(): return None
    numer={str(k): float(w[mask & (x==k)].sum()) for k in levels}
    den=sum(numer.values())
    return {k:v/den for k,v in numer.items()} if den>0 else None

def make_country_item_distributions(df, metas):
    cfg=analysis(); qs=questions(); df=df.copy()
    df['COUNTRY_NAME']=_country_name_series(df, metas)
    wvar=cfg['weight_variable']; yvar=cfg['year_variable']
    rows=[]
    # Mirror original logic: within each country-year use survey weights, then average country-year estimates equally.
    for (country, year), g in df.groupby(['COUNTRY_NAME', yvar], dropna=True):
        for item in cfg['primary_items']:
            levels=qs[item]['human_codes']
            d=weighted_distribution(g[item],g[wvar],levels)
            if d:
                for response,p in d.items():
                    rows.append({'country':country,'year':int(year),'item':item,'response':response,'p':p})
    cy=pd.DataFrame(rows)
    country=(cy.groupby(['country','item','response'],as_index=False)['p'].mean())
    # Re-normalize after equal-year averaging (normally sums to 1 already).
    country['p']=country['p']/country.groupby(['country','item'])['p'].transform('sum')
    return cy, country

def y003_constituent_marginals(df, metas):
    cfg=analysis(); qs=questions(); df=df.copy(); df['COUNTRY_NAME']=_country_name_series(df, metas)
    rows=[]
    for (country,year),g in df.groupby(['COUNTRY_NAME',cfg['year_variable']], dropna=True):
        for quality,var in qs['Y003']['constituents'].items():
            d=weighted_distribution(g[var],g[cfg['weight_variable']],[0,1])
            if d:
                rows.append({'country':country,'year':int(year),'quality':quality,'variable':var,'p_selected':d.get('1',0.0)})
    cy=pd.DataFrame(rows)
    country=cy.groupby(['country','quality','variable'],as_index=False)['p_selected'].mean()
    return cy,country

def save_processed(df, metas, outdir):
    outdir=ensure_dir(outdir)
    cy, country=make_country_item_distributions(df,metas)
    ycy,yco=y003_constituent_marginals(df,metas)
    cy.to_csv(outdir/'human_country_year_distributions.csv',index=False)
    country.to_csv(outdir/'human_country_distributions.csv',index=False)
    ycy.to_csv(outdir/'human_y003_country_year_marginals.csv',index=False)
    yco.to_csv(outdir/'human_y003_country_marginals.csv',index=False)
    return cy,country,ycy,yco
