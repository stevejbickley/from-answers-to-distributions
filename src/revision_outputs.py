"""Publication tables and figures for the cultural-signal revision.

Only outputs explicitly completed in the analysis manifest may be published.
"""
from pathlib import Path
from hashlib import sha256
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from .publication_style import ORDER, LABELS, COLORS, ITEMS, panel, clean, save_figure


def completed_manifest(results):
    path=Path(results)/'revision_analysis_manifest.json'
    if not path.exists():
        raise ValueError('Run scripts/04_analyze.py before building revision outputs')
    manifest=json.loads(path.read_text())
    if not manifest.get('completed'):
        raise ValueError('Revision analyses have not completed; refusing stale publication outputs')
    expected=manifest.get('frozen_model_probabilities_sha256')
    if expected and sha256((Path(results)/'model_mean_probabilities.csv').read_bytes()).hexdigest()!=expected:
        raise ValueError('Model probabilities changed after the completed revision analysis')
    return manifest


def make_revision_tables(results):
    results=Path(results);out=results/'tables';manifest=completed_manifest(results)
    mapping={
        'table_s19_cultural_deviation_summary.csv':'cultural_deviation_summary.csv',
        'table_s19_cultural_deviation_by_item.csv':'cultural_deviation_by_item.csv',
        'table_s22_entropy_leave_one_item_out.csv':'entropy_leave_one_item_out.csv',
        'table_s22_entropy_leave_one_item_out_summary.csv':'entropy_leave_one_item_out_summary.csv',
    }
    if manifest.get('temporal_targets')=='completed':
        mapping['table_s20_temporal_target_sensitivity.csv']='temporal_target_sensitivity.csv'
    if manifest.get('sample_diagnostics')=='completed':
        mapping.update({'table_s21_human_sample_sizes.csv':'human_sample_size_diagnostics.csv',
                        'table_s21_country_year_sample_sizes.csv':'human_country_year_sample_sizes.csv',
                        'table_s24_effective_sample_size_sensitivity.csv':'effective_sample_size_sensitivity.csv'})
        d=pd.read_csv(results/'human_sample_size_diagnostics.csv'); rows=[]
        for (target,item),g in d.groupby(['target','item']):
            rows.append({'target':target,'item':item,'n_cells':len(g),'raw_n_min':g.raw_n.min(),
                         'raw_n_median':g.raw_n.median(),'raw_n_max':g.raw_n.max(),
                         'effective_n_min':g.aggregate_n_eff.min(),'effective_n_median':g.aggregate_n_eff.median(),
                         'effective_n_max':g.aggregate_n_eff.max(),
                         **{f'n_below_{v}':int(g.aggregate_n_eff.lt(v).sum()) for v in [200,500,1000]}})
        pd.DataFrame(rows).to_csv(out/'table_s21_sample_size_summary.csv',index=False)
    if manifest.get('human_sampling')=='completed':
        mapping['table_s23_human_sampling_sensitivity.csv']='human_sampling_sensitivity.csv'
    for destination,source in mapping.items():
        pd.read_csv(results/source).to_csv(out/destination,index=False)
    # Machine-readable S17 and S18 companions preserve the existing numbering.
    contrasts=json.loads((out/'paired_contrasts.json').read_text())
    rows=[]
    for contrast,metrics in contrasts.items():
        for metric,values in metrics.items():
            if values:rows.append({'contrast':contrast,'metric':metric,**values})
    pd.DataFrame(rows).to_csv(out/'table_s17_paired_contrasts.csv',index=False)
    usage=results/'api_usage_summary.csv'
    if usage.exists():pd.read_csv(usage).to_csv(out/'table_s18_api_usage.csv',index=False)
    # Add direction to the concise main population-specificity table.
    main=pd.read_csv(out/'table3_country_conditioning.csv')
    direction=pd.read_csv(results/'cultural_deviation_summary.csv')
    # Allow this supplementary stage to be rerun on an already-enriched table.
    added=set(direction.columns)-{'condition'}
    main=main.drop(columns=[c for c in main if c.removesuffix('_x').removesuffix('_y') in added])
    main.merge(direction,on='condition',validate='one_to_one').to_csv(out/'table3_country_conditioning.csv',index=False)
    (out/'revision_table_manifest.json').write_text(json.dumps({'analysis_status':manifest,
        'tables':list(mapping),'supplementary_numbering':'S1-S24; S19, S21 and S22 have detail companions'},indent=2)+'\n')


def _ordered(df):
    return df.set_index('condition').reindex([c for c in ORDER if c in set(df.condition)]).reset_index()


def _rows(ax, frame):
    ax.set_yticks(range(len(frame)),[LABELS[c] for c in frame.condition])
    ax.set_ylim(len(frame)-.5,-.5);clean(ax)


def _intervals(ax, frame, point, low, high, *, values=False, digits=2):
    for i,r in frame.iterrows():
        # Draw interval endpoints directly: percentile CIs need not contain a point estimate.
        ax.plot([r[low],r[high]],[i,i],color=COLORS[r.condition],lw=1.5)
        ax.plot([r[low],r[high]],[i,i],ls='',marker='|',color=COLORS[r.condition],ms=6)
        ax.scatter(r[point],i,color=COLORS[r.condition],s=28,zorder=3)
        if values:ax.annotate(f'{r[point]:.{digits}f}',(r[point],i),xytext=(0,-13),textcoords='offset points',ha='center',fontsize=7)
    _rows(ax,frame)


def revision_figures(results, figdir, heatmap):
    results,figdir=Path(results),Path(figdir);manifest=completed_manifest(results)
    d=_ordered(pd.read_csv(results/'cultural_deviation_summary.csv'))
    p=_ordered(pd.read_csv(results/'tables/table3_population_specificity.csv'))
    fig,axes=plt.subplots(2,2,figsize=(9.0,6.6),layout='constrained')
    a,b,c,e=axes.flat
    _intervals(a,d,'direction_correct_percent','direction_correct_percent_ci_low','direction_correct_percent_ci_high',values=True,digits=1)
    a.set_xlim(0,100);a.set_xlabel('Cells with positive directional alignment (%)')
    panel(a,'a','Direction of country-specific change')
    _intervals(b,d,'projection_pooled','projection_pooled_ci_low','projection_pooled_ci_high',values=True,digits=3)
    b.axvline(0,c='#777777',ls='--',lw=.8);b.axvline(1,c='#999999',ls=':',lw=.8)
    b.set_xlim(-.08,max(1.15,d.projection_pooled_ci_high.max()+.1));b.set_xlabel('Pooled projection onto human deviation')
    panel(b,'b','Magnitude along the human direction')
    _intervals(c,p,'gain_vs_default_mean','gain_vs_default_ci95_low','gain_vs_default_ci95_high')
    c.axvline(0,c='#777777',ls='--',lw=.8);c.set_xlabel('Mean JSD gain from country prompting')
    panel(c,'c','Gain relative to the model default')
    for i,r in p.iterrows():
        e.plot([r.loco_human_js_mean,r.country_model_js_mean],[i,i],c='#BBBBBB',lw=1.5)
        e.scatter(r.loco_human_js_mean,i,c='#555555',marker='s',s=27)
        e.scatter(r.country_model_js_mean,i,c=COLORS[r.condition],s=28)
        e.text(.435,i,f'{r.pct_model_beats_loco_human:.1f}%\nbeat LOCO',ha='right',va='center',fontsize=7.4)
    _rows(e,p);e.set_xlim(0,.45);e.set_xlabel('Mean JSD (lower is better)')
    panel(e,'d','Fidelity against the human baseline')
    e.legend(handles=[Line2D([],[],c='#555555',marker='s',ls='',label='LOCO human'),Line2D([],[],c='#555555',marker='o',ls='',label='Model')],loc='upper center',bbox_to_anchor=(.5,-.23),ncols=2,frameon=False,fontsize=7)
    save_figure(fig,figdir,'figure2_country_specific_signal')

    byitem=pd.read_csv(results/'cultural_deviation_by_item.csv')
    fig,axes=plt.subplots(1,3,figsize=(12.2,5.4),layout='constrained')
    for ax,col,title,label,center,limits,fmt in zip(axes,
            ['direction_correct_percent','cosine_mean','projection_pooled'],
            ['a  Positive direction','b  Mean cosine','c  Pooled projection'],
            ['Cells with positive direction (%)','Cosine similarity','Projection coefficient'],
            [False,True,True],[(0,100),(-1,1),None],['.1f','.2f','.2f']):
        heatmap(ax,byitem,col,title,label,center_zero=center,limits=limits,fmt=fmt,counts=False)
    save_figure(fig,figdir,'figure_s12_cultural_direction')

    if manifest.get('temporal_targets')=='completed':
        t=pd.read_csv(results/'temporal_target_sensitivity.csv')
        targets=['pooled_equal_year','latest_available','wave7'];target_labels=['Pooled years','Latest year','Wave 7']
        fig,axes=plt.subplots(2,3,figsize=(10.8,6.0),layout='constrained')
        for ax,col,label in zip(axes.flat,['js_mean','gain_vs_default_mean','pct_model_beats_loco','direction_correct_percent','projection_pooled','two_way_slope'],
                ['Mean JSD','Mean gain vs model default','Cells beating LOCO (%)','Positive direction (%)','Pooled projection','Two-way entropy slope']):
            for i,condition in enumerate([c for c in ORDER if c in set(t.condition)]):
                g=t[t.condition.eq(condition)].set_index('target').reindex(targets)
                ax.plot(range(3),g[col],'-o',c=COLORS[condition],ms=4,label=LABELS[condition])
            ax.set_xticks(range(3),target_labels,rotation=20,ha='right');ax.set_ylabel(label);clean(ax,'y')
            if col in ['gain_vs_default_mean','two_way_slope']:ax.axhline(0,c='#888888',ls='--',lw=.6)
        axes[0,0].legend(frameon=False,fontsize=7)
        fig.suptitle('Temporal human targets; model probabilities held fixed',fontsize=10,weight='bold')
        save_figure(fig,figdir,'figure_s13_temporal_targets')

    lo=pd.read_csv(results/'entropy_leave_one_item_out.csv');omissions=list(ITEMS)
    omissions=[j for j in omissions if j in set(lo.omitted_item)]
    fig,axes=plt.subplots(1,3,figsize=(10.7,4.8),sharey=True,layout='constrained')
    for ax,col,title in zip(axes,['two_way_slope','two_way_pearson','two_way_spearman'],['a  Regression slope','b  Residual Pearson correlation','c  Residual Spearman correlation']):
        for i,condition in enumerate([c for c in ORDER if c in set(lo.condition)]):
            g=lo[lo.condition.eq(condition)].set_index('omitted_item')
            base=g.loc['none',col];vals=g.reindex(omissions)[col]
            ax.scatter(vals,np.arange(len(omissions))+(i-1)*.2,c=COLORS[condition],s=19,label=LABELS[condition])
            ax.axvline(base,c=COLORS[condition],lw=.8,alpha=.6,ls=':')
        ax.axvline(0,c='#777777',lw=.7);ax.set_yticks(range(len(omissions)),omissions);ax.set_ylim(len(omissions)-.5,-.5)
        ax.set_title(title,loc='left',weight='bold',fontsize=9);ax.set_xlabel('Country and item effects removed');clean(ax)
    axes[0].set_ylabel('Omitted survey item')
    fig.legend(*axes[2].get_legend_handles_labels(),frameon=False,fontsize=8,loc='outside lower center',ncols=3)
    save_figure(fig,figdir,'figure_s14_entropy_leave_one_item_out')

    if manifest.get('human_sampling')=='completed':
        s=pd.read_csv(results/'human_sampling_sensitivity.csv')
        fig,axes=plt.subplots(2,3,figsize=(10.8,6),layout='constrained')
        for ax,metric,label in zip(axes.flat,['js_mean','gain_vs_default_mean','pct_model_beats_loco','direction_correct_percent','projection_pooled','two_way_slope'],
                ['Mean JSD','Mean gain vs model default','Cells beating LOCO (%)','Positive direction (%)','Pooled projection','Two-way entropy slope']):
            g=_ordered(s[s.metric.eq(metric)])
            _intervals(ax,g,'point_estimate','ci_low','ci_high');ax.set_xlabel(label)
        fig.suptitle('Human respondent sampling: 95% conditional percentile intervals',fontsize=10,weight='bold')
        save_figure(fig,figdir,'figure_s16_human_sampling_sensitivity')
