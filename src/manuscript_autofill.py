from __future__ import annotations
from pathlib import Path
import json, pandas as pd, numpy as np
from docx import Document

def _fmt(x,d=3):
    try:
        if x is None or pd.isna(x): return 'NA'
        return f'{float(x):.{d}f}'
    except Exception: return str(x)

def _ci(c):
    if not c: return 'NA'
    return f"{_fmt(c.get('mean_openai_minus_jev'))} ({_fmt(c.get('ci95_low'))}, {_fmt(c.get('ci95_high'))})"

def build_tokens(results='results'):
    r=Path(results); tokens={}
    m=pd.read_csv(r/'country_item_metrics.csv')
    summary=pd.read_csv(r/'tables/table2_primary_summary.csv').set_index('provider')
    contrasts=json.loads((r/'tables/paired_contrasts.json').read_text())
    tokens['<<AUTO:N_COUNTRIES>>']=str(m.country.nunique())
    tokens['<<AUTO:N_COUNTRY_ITEM>>']=str(m[['country','item']].drop_duplicates().shape[0])
    tokens['<<AUTO:HUMAN_ENTROPY_MEAN>>']=_fmt(m[['country','item','human_entropy']].drop_duplicates().human_entropy.mean())
    for p in ['openai','jev']:
        P=p.upper()
        if p in summary.index:
            row=summary.loc[p]
            tokens[f'<<AUTO:{P}_JS_MEAN>>']=_fmt(row.js_mean)
            tokens[f'<<AUTO:{P}_TV_MEAN>>']=_fmt(row.tv_mean)
            tokens[f'<<AUTO:{P}_WASS_MEAN>>']=_fmt(row.wasserstein_mean)
            tokens[f'<<AUTO:{P}_EXPECTED_ERROR>>']=_fmt(row.expected_abs_error_mean)
            tokens[f'<<AUTO:{P}_ENTROPY_ERROR>>']=_fmt(row.entropy_abs_error_mean)
    for key,met in [('JS','js'),('TV','tv'),('WASS','wasserstein'),('EXPECTED','expected_abs_error'),('ENTROPY','entropy_abs_error')]:
        c=contrasts.get(met) or {}
        tokens[f'<<AUTO:{key}_DIFF_CI>>']=_ci(c)
        if key=='JS':
            tokens['<<AUTO:JS_DIFF>>']=_fmt(c.get('mean_openai_minus_jev'))
            tokens['<<AUTO:JS_CI_LOW>>']=_fmt(c.get('ci95_low'))
            tokens['<<AUTO:JS_CI_HIGH>>']=_fmt(c.get('ci95_high'))
            tokens['<<AUTO:JS_WILCOXON_P>>']=_fmt(c.get('wilcoxon_p'),4)
            tokens['<<AUTO:PRIMARY_DIRECTION>>']='lower for Jev' if (c.get('mean_openai_minus_jev') or 0)>0 else 'lower for OpenAI'
    # OpenAI diagnostics
    dpath=r/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath)
        tokens['<<AUTO:OPENAI_CALLS>>']=str(len(d))
        tokens['<<AUTO:OPENAI_COMPLETE_CALLS>>']=str(int((d.missing_count==0).sum()))
        tokens['<<AUTO:OPENAI_MISSING_RATE>>']=_fmt(100*(d.missing_count>0).mean(),1)
        tokens['<<AUTO:OPENAI_ALLOWED_MASS>>']=_fmt(d.allowed_mass.mean())
        tokens['<<AUTO:OPENAI_ALLOWED_MASS_MEDIAN>>']=_fmt(d.allowed_mass.median())
        tokens['<<AUTO:OPENAI_INVALID_RATE>>']=_fmt(100*(~d.valid_generated.astype(bool)).mean(),1)
        tokens['<<AUTO:OPENAI_COMPLETENESS_ACTION>>']='retained all calls because every permitted label was observed' if (d.missing_count>0).sum()==0 else 'restricted the primary OpenAI estimates to request records in which every permitted label was observed'
    # Item differences
    piv=m.pivot_table(index=['country','item'],columns='provider',values='js').dropna().reset_index()
    if len(piv):
        itemd=(piv.assign(diff=piv.openai-piv.jev).groupby('item')['diff'].mean().sort_values())
        tokens['<<AUTO:LARGEST_DIFF_ITEM>>']=str(itemd.abs().idxmax())
        tokens['<<AUTO:SMALLEST_DIFF_ITEM>>']=str(itemd.abs().idxmin())
    # Entropy slopes
    for p in ['openai','jev']:
        g=m[m.provider==p].dropna(subset=['human_entropy','model_entropy'])
        if len(g)>2:
            slope=np.polyfit(g.human_entropy,g.model_entropy,1)[0]
            tokens[f'<<AUTO:{p.upper()}_ENTROPY_SLOPE>>']=_fmt(slope)
    signed=m.groupby('provider').entropy_signed_error.mean().to_dict()
    if signed:
        if all(v<0 for v in signed.values()): interp='both systems were, on average, more concentrated than the human distributions'
        elif all(v>0 for v in signed.values()): interp='both systems were, on average, more diffuse than the human distributions'
        else: interp='the systems differed in the direction of their average dispersion error'
        tokens['<<AUTO:ENTROPY_INTERPRETATION>>']=interp
    # Prompt + label sensitivity
    sp=r/'prompt_sensitivity.csv'
    if sp.exists():
        s=pd.read_csv(sp)
        for p in ['openai','jev']: tokens[f'<<AUTO:{p.upper()}_PROMPT_JSD>>']=_fmt(s[s.provider==p].js_to_provider_mean.mean())
    lp=r/'openai_label_sensitivity.csv'
    if lp.exists(): tokens['<<AUTO:LABEL_EFFECT>>']=_fmt(pd.read_csv(lp).js_to_label_mean.mean())
    # Map
    cp=r/'cultural_map_distances.csv'
    if cp.exists():
        c=pd.read_csv(cp)
        for p in ['openai','jev']:
            e=c[(c.provider==p)&(c.representation=='expected')].distance.mean()
            a=c[(c.provider==p)&(c.representation=='argmax')].distance.mean()
            tokens[f'<<AUTO:{p.upper()}_MAP_DISTANCE>>']=_fmt(e)
            tokens[f'<<AUTO:{p.upper()}_ARGMAX_MAP>>']=_fmt(a)
            tokens[f'<<AUTO:{p.upper()}_MAP_CHANGE>>']=_fmt(e-a)
    # Y003
    yp=r/'y003_marginal_metrics.csv'
    if yp.exists():
        y=pd.read_csv(yp)
        for p in ['openai','jev']: tokens[f'<<AUTO:{p.upper()}_Y003_MAE>>']=_fmt(y[y.provider==p].abs_error.mean())
    # Provider metadata from raw is not stored in results by default.
    defaults={
      '<<AUTO:ORDER_EFFECT_OPENAI>>':'[run robustness script]', '<<AUTO:ORDER_EFFECT_JEV>>':'[run robustness script]',
      '<<AUTO:JEV_MODEL>>':'[recorded at collection]', '<<AUTO:JEV_RELEASE_DATE>>':'[recorded from GET /v1/models]',
      '<<AUTO:JEV_COLLECTION_DATES>>':'[recorded at collection]', '<<AUTO:JEV_CHOICE_CALLS>>':'[generated at collection]',
      '<<AUTO:JEV_NOUL_DECISIONS>>':'[generated at collection]', '<<AUTO:JEV_SUM_FAILURES>>':'0 if validation passes',
      '<<AUTO:PCA_CORR_PC1>>':'[validate against archived source]', '<<AUTO:PCA_CORR_PC2>>':'[validate against archived source]',
      '<<AUTO:PCA_MAE_PC1>>':'[validate]', '<<AUTO:PCA_MAE_PC2>>':'[validate]', '<<AUTO:PCA_MAX_PC1>>':'[validate]', '<<AUTO:PCA_MAX_PC2>>':'[validate]',
      '<<AUTO:DISCUSSION_PRIMARY>>':'the empirical comparison reported above; interpret the direction together with the heterogeneity and robustness results'
    }
    for k,v in defaults.items(): tokens.setdefault(k,v)
    return tokens

def replace_docx(template, output, tokens):
    doc=Document(template)
    def replace_para(p):
        if not any(k in p.text for k in tokens): return
        full=''.join(r.text for r in p.runs)
        for k,v in tokens.items(): full=full.replace(k,str(v))
        if p.runs:
            p.runs[0].text=full
            for rr in p.runs[1:]: rr.text=''
    for p in doc.paragraphs: replace_para(p)
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                for p in cell.paragraphs: replace_para(p)
    doc.save(output)
