from __future__ import annotations
from pathlib import Path
import json, pandas as pd, numpy as np
from docx import Document

def _fmt(x,d=3):
    try:
        if x is None or pd.isna(x): return 'NA'
        return f'{float(x):.{d}f}'
    except Exception: return str(x)

def build_tokens(results='results'):
    r=Path(results); tokens={}; m=pd.read_csv(r/'country_item_metrics.csv'); full=m[m.representation=='full'] if 'representation' in m else m
    summary=pd.read_csv(r/'tables/table2_primary_summary.csv')
    contrasts=json.loads((r/'tables/paired_contrasts.json').read_text()) if (r/'tables/paired_contrasts.json').exists() else {}
    tokens['<<AUTO:N_COUNTRIES>>']=str(m.country.nunique()); tokens['<<AUTO:N_COUNTRY_ITEM>>']=str(m[['country','item']].drop_duplicates().shape[0]); tokens['<<AUTO:HUMAN_ENTROPY_MEAN>>']=_fmt(m[['country','item','human_entropy']].drop_duplicates().human_entropy.mean())
    aliases={'gpt4o_anchor':'GPT4O','gpt56_sol':'SOL','gpt56_terra':'TERRA','jev':'JEV'}
    for cond,alias in aliases.items():
        g=summary[(summary.condition==cond)&(summary.representation=='full')]
        if len(g):
            row=g.iloc[0]
            for key,col in [('JS_MEAN','js_mean'),('TV_MEAN','tv_mean'),('WASS_MEAN','wasserstein_mean'),('EXPECTED_ERROR','expected_abs_error_mean'),('ENTROPY_ERROR','entropy_abs_error_mean')]: tokens[f'<<AUTO:{alias}_{key}>>']=_fmt(row[col])
    primary=contrasts.get('gpt56_sol_vs_jev',{}).get('js') or {}
    tokens['<<AUTO:JS_DIFF>>']=_fmt(primary.get('mean_error_a_minus_b')); tokens['<<AUTO:JS_CI_LOW>>']=_fmt(primary.get('ci95_low')); tokens['<<AUTO:JS_CI_HIGH>>']=_fmt(primary.get('ci95_high')); tokens['<<AUTO:JS_WILCOXON_P>>']=_fmt(primary.get('wilcoxon_p'),4)
    tokens['<<AUTO:PRIMARY_DIRECTION>>']='lower for Jev' if (primary.get('mean_error_a_minus_b') or 0)>0 else 'lower for GPT-5.6 Sol'
    # Backward-compatible aliases used by the earlier manuscript draft.
    for old,new in [('OPENAI_JS_MEAN','SOL_JS_MEAN'),('OPENAI_TV_MEAN','SOL_TV_MEAN'),('OPENAI_WASS_MEAN','SOL_WASS_MEAN'),('OPENAI_EXPECTED_ERROR','SOL_EXPECTED_ERROR'),('OPENAI_ENTROPY_ERROR','SOL_ENTROPY_ERROR'),('JEV_JS_MEAN','JEV_JS_MEAN'),('JEV_TV_MEAN','JEV_TV_MEAN'),('JEV_WASS_MEAN','JEV_WASS_MEAN'),('JEV_EXPECTED_ERROR','JEV_EXPECTED_ERROR'),('JEV_ENTROPY_ERROR','JEV_ENTROPY_ERROR')]:
        if f'<<AUTO:{new}>>' in tokens: tokens[f'<<AUTO:{old}>>']=tokens[f'<<AUTO:{new}>>']
    dpath=r/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath); tokens['<<AUTO:OPENAI_CALLS>>']=str(len(d)); tokens['<<AUTO:OPENAI_COMPLETE_CALLS>>']=str(int((d.missing_count==0).sum())); tokens['<<AUTO:OPENAI_MISSING_RATE>>']=_fmt(100*(d.missing_count>0).mean(),1); tokens['<<AUTO:OPENAI_ALLOWED_MASS>>']=_fmt(d.allowed_mass.mean()); tokens['<<AUTO:OPENAI_ALLOWED_MASS_MEDIAN>>']=_fmt(d.allowed_mass.median()); tokens['<<AUTO:OPENAI_INVALID_RATE>>']=_fmt(100*(~d.valid_generated.astype(bool)).mean(),1); retained=int(d.primary_included.astype(bool).sum()) if 'primary_included' in d else int((d.missing_count==0).sum()); tokens['<<AUTO:OPENAI_COMPLETENESS_ACTION>>']=f'retained {retained} of {len(d)} calls under the prespecified tail-mass upper-bound rule (complete calls plus negligible top-K censoring)'; tokens['<<AUTO:OPENAI_MAX_MISSING_MASS_UB>>']=_fmt(d.missing_allowed_mass_upper_bound.max(),6) if 'missing_allowed_mass_upper_bound' in d else 'NA'
    # Condition-level entropy slopes and prompt sensitivity.
    for cond,alias in aliases.items():
        g=full[full.condition==cond].dropna(subset=['human_entropy','model_entropy'])
        if len(g)>2: tokens[f'<<AUTO:{alias}_ENTROPY_SLOPE>>']=_fmt(np.polyfit(g.human_entropy,g.model_entropy,1)[0])
    sp=r/'prompt_sensitivity.csv'
    if sp.exists():
        s=pd.read_csv(sp)
        for cond,alias in aliases.items(): tokens[f'<<AUTO:{alias}_PROMPT_JSD>>']=_fmt(s[s.condition==cond].js_to_condition_mean.mean())
    lp=r/'openai_label_sensitivity.csv'
    if lp.exists(): tokens['<<AUTO:LABEL_EFFECT>>']=_fmt(pd.read_csv(lp).js_to_label_mean.mean())
    cp=r/'cultural_map_distances.csv'
    if cp.exists():
        c=pd.read_csv(cp)
        for cond,alias in aliases.items():
            e=c[(c.condition==cond)&(c.representation=='expected')].distance.mean(); a=c[(c.condition==cond)&(c.representation=='argmax')].distance.mean()
            tokens[f'<<AUTO:{alias}_MAP_DISTANCE>>']=_fmt(e); tokens[f'<<AUTO:{alias}_ARGMAX_MAP>>']=_fmt(a); tokens[f'<<AUTO:{alias}_MAP_CHANGE>>']=_fmt(e-a)
    yp=r/'y003_marginal_metrics.csv'
    if yp.exists():
        y=pd.read_csv(yp)
        for cond,alias in aliases.items(): tokens[f'<<AUTO:{alias}_Y003_MAE>>']=_fmt(y[y.condition==cond].abs_error.mean())
    defaults={'<<AUTO:ORDER_EFFECT_OPENAI>>':'[run robustness script]','<<AUTO:ORDER_EFFECT_JEV>>':'[run robustness script]','<<AUTO:JEV_MODEL>>':'[recorded at collection]','<<AUTO:JEV_RELEASE_DATE>>':'[recorded from GET /v1/models]','<<AUTO:JEV_COLLECTION_DATES>>':'[recorded at collection]','<<AUTO:JEV_CHOICE_CALLS>>':'[generated at collection]','<<AUTO:JEV_NOUL_DECISIONS>>':'[generated at collection]','<<AUTO:JEV_SUM_FAILURES>>':'0 if validation passes','<<AUTO:PCA_CORR_PC1>>':'[validate against archived source]','<<AUTO:PCA_CORR_PC2>>':'[validate against archived source]','<<AUTO:PCA_MAE_PC1>>':'[validate]','<<AUTO:PCA_MAE_PC2>>':'[validate]','<<AUTO:PCA_MAX_PC1>>':'[validate]','<<AUTO:PCA_MAX_PC2>>':'[validate]','<<AUTO:DISCUSSION_PRIMARY>>':'the empirical comparison reported above; interpret it together with the historical-anchor, full-versus-argmax, heterogeneity, and robustness results'}
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
