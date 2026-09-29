"""Reproducible publication figures from the archived analysis outputs.

There are four main figures and eleven supplementary figures. Every canonical
figure is exported as 600 dpi PNG, editable SVG, and font-embedded vector PDF.
"""
from __future__ import annotations
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from .publication_style import (
    ORDER, LABELS, COLORS, WITHOUT, WITH, REGIONS, ITEMS, STYLE,
    conditions as _conditions, panel, clean, save_figure, region_lookup, place_map_labels,
)
from .utils import ensure_dir

TAO_GPT4O={'unconditioned':2.42,'conditioned':1.57,'pct_improved':71.0}

# Superseded renderings are preserved outside the canonical publication set.
LEGACY = [
 'figure1_probability_semantics','figure1_distributional_fidelity',
 'figure2_distributional_fidelity','figure2_entropy_recovery',
 'figure3_entropy_recovery','figure4_cultural_map','figure_s3_distribution_value_added',
 'figure_s4_item_error','figure_s5_allowed_mass','figure_s6_y003',
 'figure_s8_cultural_map','figure_s9_entropy_by_item','figure_s10_population_specificity_by_item',
 'figure_s3_label_sensitivity','figure_s4_option_order_sensitivity','figure_s5_item_error',
 'figure_s6_allowed_mass','figure_s7_y003',
]


def _archive_old(figdir):
    for stem in LEGACY:
        for ext in ['png','pdf','svg']:
            path=figdir/f'{stem}.{ext}'
            if path.exists():
                archive=ensure_dir(figdir/'archive')
                dest=archive/path.name
                if dest.exists() and dest.read_bytes()!=path.read_bytes():
                    raise ValueError(f'Conflicting archived figure: {dest}')
                shutil.move(str(path),str(dest))


def _read(results, name):
    path=results/name
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _boxes(ax, arrays, positions, colors, width=.6):
    bp=ax.boxplot(arrays,positions=positions,widths=width,patch_artist=True,
       showfliers=True,manage_ticks=False,
       medianprops={'color':'#303030','linewidth':1.3},
       boxprops={'linewidth':.7},whiskerprops={'linewidth':.7},capprops={'linewidth':.7},
       flierprops={'marker':'.','markersize':2.5,'markeredgecolor':'#555555','alpha':.55})
    for box,c in zip(bp['boxes'],colors): box.set_facecolor(c)
    return bp


def _heatmap(ax, frame, value, title, cbar_label, *, center_zero=False, limits=None, fmt='.3f', counts=True):
    rows=[i for i in ITEMS if i in set(frame.item)]
    rows += sorted(set(frame.item)-set(rows)); cols=_conditions(frame)
    mat=frame.pivot(index='item',columns='condition',values=value).reindex(index=rows,columns=cols).to_numpy(float)
    if center_zero:
        vmax=max(float(np.nanmax(np.abs(mat))),.01) if np.isfinite(mat).any() else 1
        vmin,vmax=limits or (-vmax,vmax); cmap=plt.get_cmap('RdBu').copy()
    else:
        vmin,vmax=limits or (0,max(float(np.nanmax(mat)),.001)); cmap=plt.get_cmap('viridis').copy()
    cmap.set_bad('#EDEDED')
    im=ax.imshow(np.ma.masked_invalid(mat),aspect='auto',cmap=cmap,vmin=vmin,vmax=vmax)
    ax.set_xticks(range(len(cols)),[LABELS.get(c,c) for c in cols])
    ax.set_yticks(range(len(rows)),[f'{i}  {ITEMS.get(i,i)}' for i in rows])
    ax.tick_params(length=0,pad=6)
    ax.set_title(title,loc='left',fontweight='bold',pad=14)
    for spine in ax.spines.values(): spine.set_visible(False)
    for i,item in enumerate(rows):
        for j,cond in enumerate(cols):
            val=mat[i,j]
            if not np.isfinite(val):
                ax.text(j,i,'NA',ha='center',va='center',fontsize=9,color='#666666'); continue
            rgba=im.cmap(im.norm(val)); lum=.2126*rgba[0]+.7152*rgba[1]+.0722*rgba[2]
            label=format(0.0 if abs(val)<.5*10**(-int(fmt[1])) else val,fmt)
            g=frame[(frame.item==item)&(frame.condition==cond)]
            ncol='n_valid' if 'n_valid' in g else 'n'
            if counts and ncol in g and pd.notna(g[ncol].iloc[0]): label+=f'\n(n={int(g[ncol].iloc[0])})'
            ax.text(j,i,label,ha='center',va='center',fontsize=8.1,color='white' if lum<.52 else '#151515',linespacing=1.5)
    ax.set_xticks(np.arange(-.5,len(cols),1),minor=True)
    ax.set_yticks(np.arange(-.5,len(rows),1),minor=True)
    ax.grid(which='minor',color='white',linewidth=1); ax.tick_params(which='minor',length=0)
    cb=ax.figure.colorbar(im,ax=ax,fraction=.045,pad=.045)
    cb.outline.set_visible(False); cb.set_label(cbar_label,labelpad=9)


def _map_figure(results, figdir, conds):
    coords=_read(results,'cultural_map_coordinates.csv')
    prompting=_read(results,'cultural_map_prompting_distances.csv')
    if coords.empty or prompting.empty: return
    human=coords[(coords.condition=='human')&(coords.representation=='expected')].copy()
    default=coords[(coords.country=='__DEFAULT__')&(coords.representation=='expected')].copy()
    region=region_lookup(); missing=set(human.country)-set(region)
    if missing: raise ValueError(f'Unclassified cultural-map countries: {sorted(missing)}')
    human['region']=human.country.map(region)
    fig=plt.figure(figsize=(8.0,10.0),dpi=120)
    # Fixed panel geometry keeps the verified label placement stable on export.
    ax=fig.add_axes([.10,.44,.875,.475])
    axb=fig.add_axes([.10,.055,.875,.26])
    panel(ax,'a','Human cultural regions and unconditioned model positions')
    allx=pd.concat([human.survival_self_expression,default.survival_self_expression])
    ally=pd.concat([human.traditional_secular,default.traditional_secular])
    ax.set_xlim(allx.min()-.8,allx.max()+.55)
    ax.set_ylim(ally.min()-.45,ally.max()+.45)
    ax.set_xlabel('Survival  ←  →  Self-expression',labelpad=7)
    ax.set_ylabel('Traditional  ←  →  Secular-rational',labelpad=7)
    handles=[]; pts=[]; labels=[]; colors=[]; sizes=[]; weights=[]
    for reg,color in REGIONS.items():
        g=human[human.region==reg]
        ax.scatter(g.survival_self_expression,g.traditional_secular,s=11,c=color,edgecolors='#555555',linewidths=.2,zorder=3)
        handles.append(Line2D([],[],marker='o',ls='',markersize=4,color=color,markeredgewidth=.2,markeredgecolor='#555555',label=reg.replace('English-Speaking','English-speaking')))
    for r in human.sort_values('country').itertuples():
        pts.append((r.survival_self_expression,r.traditional_secular)); labels.append(r.country)
        # Pale yellow is retained for points; dark olive improves label readability.
        colors.append('#887B00' if r.region=='West & South Asia' else REGIONS[r.region]); sizes.append(7.0); weights.append('normal')
    for j,c in enumerate(conds):
        g=default[default.condition==c]
        if g.empty:continue
        r=g.iloc[0]
        ax.scatter(r.survival_self_expression,r.traditional_secular,s=46,marker=['s','D','^','P'][j%4],c='#C7272D',edgecolor='white',linewidth=.5,zorder=4)
        pts.append((r.survival_self_expression,r.traditional_secular)); labels.append(LABELS.get(c,c))
        colors.append('#BA1821'); sizes.append(7.3); weights.append('bold')
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.54,.982),ncols=4,frameon=False,fontsize=7.1,columnspacing=1.25,handletextpad=.35)
    audit=place_map_labels(ax,pts,labels,colors,font_sizes=sizes,weights=weights)
    (results/'figure1_label_audit.json').write_text(json.dumps(audit,indent=2))
    p=prompting[prompting.representation=='expected']; shown=[c for c in conds if c in set(p.condition)]
    arrays=[]; pos=[]; boxcolors=[]
    for i,c in enumerate(shown):
        g=p[p.condition==c]; arrays += [g.unconditioned_distance,g.country_conditioned_distance]
        pos += [i*3+1,i*3+2]; boxcolors += [WITHOUT,WITH]
    _boxes(axb,arrays,pos,boxcolors)
    mx=max(a.max() for a in arrays); axb.set_ylim(-.03,mx*1.27)
    for i,c in enumerate(shown):
        g=p[p.condition==c]; u=g.unconditioned_distance.mean(); v=g.country_conditioned_distance.mean()
        axb.scatter([i*3+1,i*3+2],[u,v],marker='D',s=17,c='white',edgecolor='#222222',linewidth=.7,zorder=5)
        pct=100*(g.country_conditioned_distance<g.unconditioned_distance).mean()
        axb.text(i*3+1.5,mx*1.08,f'{u:.2f} → {v:.2f}\n{pct:.1f}% improved',ha='center',va='center',fontsize=8,linespacing=1.5)
    axb.set_xticks([i*3+1.5 for i in range(len(shown))],
                  [f'{LABELS.get(c,c)}\n(n={len(p[p.condition==c])})' for c in shown])
    axb.set_ylabel('Distance from target human country')
    panel(axb,'b','Effect of cultural prompting on expected-score positions')
    fig.legend(handles=[Patch(facecolor=WITHOUT,edgecolor='#333333',label='Without cultural prompting'),
                        Patch(facecolor=WITH,edgecolor='#333333',label='With cultural prompting')],
               loc='center',bbox_to_anchor=(.54,.377),ncol=2,frameon=False,fontsize=7.8)
    clean(axb,'y')
    save_figure(fig,figdir,'figure1_tao_replication')


def empirical(results='results',figdir='figures'):
    results=Path(results); figdir=ensure_dir(figdir); _archive_old(figdir)
    with plt.rc_context(STYLE):
        _empirical(results,figdir)
    stems=sorted(p.stem for p in figdir.glob('*.png'))
    (figdir/'manifest.json').write_text(json.dumps({'main_figures':4,'supplementary_figures':11,'formats':['png','pdf','svg'],'png_dpi':600,'figures':stems},indent=2))


def _empirical(results,figdir):
    m=_read(results,'country_item_metrics.csv'); full=m[m.representation=='full']; conds=_conditions(m)
    _map_figure(results,figdir,conds)

    rep=_read(results,'tables/table_s5_full_vs_argmax.csv')
    if not rep.empty:
        rep=rep.set_index('condition').reindex(conds).dropna(subset=['mean_js_full']).reset_index()
        fig,(ax,note)=plt.subplots(1,2,figsize=(7.6,3.25),gridspec_kw={'width_ratios':[3.2,1.65]},layout='constrained')
        y=np.arange(len(rep))
        for i,r in rep.iterrows(): ax.plot([r.mean_js_full,r.mean_js_argmax],[i,i],c='#B8B8B8',lw=2.3,zorder=1)
        ax.scatter(rep.mean_js_full,y,c=WITH,s=44,label='Full distribution',zorder=3)
        ax.scatter(rep.mean_js_argmax,y,c=WITHOUT,s=44,marker='s',label='Argmax',zorder=3)
        ax.set_yticks(y,[LABELS[c] for c in rep.condition]);ax.set_ylim(len(rep)-.5,-.7)
        ax.set_xlim(0,float(rep.mean_js_argmax.max())+.07)
        ax.set_xlabel('Mean Jensen–Shannon divergence\n(lower is better)');clean(ax)
        ax.legend(loc='lower center',bbox_to_anchor=(.5,1.02),ncol=2,frameon=False)
        note.axis('off'); note.set_ylim(ax.get_ylim())
        note.text(0,-.7,'JSD reduction   Cells improved',fontsize=8.2,weight='bold')
        for i,r in rep.iterrows():
            note.text(0,i,f'{r.mean_argmax_minus_full:.3f}              {r.pct_full_better:.1f}%\n{int(r.n):,} paired cells',va='center',fontsize=8.5,linespacing=1.65)
        save_figure(fig,figdir,'figure2_probability_value')

    t=_read(results,'tables/table3_population_specificity.csv')
    ps=_read(results,'population_specificity_metrics.csv')
    if not t.empty:
        t=t.set_index('condition').reindex(conds).dropna(subset=['gain_vs_default_mean']).reset_index()
        fig,axs=plt.subplots(2,1,figsize=(7.5,5.75),layout='constrained')
        a,b=axs; yy=np.arange(len(t))
        low=min(t.gain_vs_default_ci95_low.min(),0)-.025
        high=t.gain_vs_default_ci95_high.max()+.13
        for i,r in t.iterrows():
            a.errorbar(r.gain_vs_default_mean,i,xerr=[[r.gain_vs_default_mean-r.gain_vs_default_ci95_low],[r.gain_vs_default_ci95_high-r.gain_vs_default_mean]],fmt='o',color=COLORS[r.condition],capsize=3)
            a.text(high-.005,i,f'{r.pct_country_conditioning_improves:.1f}% improve',ha='right',va='center',fontsize=8)
        a.axvline(0,color='#666666',ls='--',lw=.8);a.set_xlim(low,high)
        a.set_yticks(yy,[LABELS[c] for c in t.condition]);a.set_ylim(len(t)-.5,-.5)
        a.set_xlabel('Mean JSD gain from country prompting (positive = improvement)')
        panel(a,'a','Distributional gain relative to the same unconditioned model'); clean(a)
        for i,r in t.iterrows():
            b.plot([r.loco_human_js_mean,r.country_model_js_mean],[i,i],c='#BBBBBB',lw=1.5)
            b.scatter(r.loco_human_js_mean,i,c='#555555',marker='s',s=35,zorder=3)
            b.scatter(r.country_model_js_mean,i,c=COLORS[r.condition],s=40,zorder=3)
            b.text(.435,i,f'{r.pct_model_beats_loco_human:.1f}% beat LOCO\n(n={int(r.n_country_item)})',ha='right',va='center',fontsize=8,linespacing=1.5)
        b.set_yticks(yy,[LABELS[c] for c in t.condition]);b.set_ylim(len(t)-.5,-.5);b.set_xlim(0,.445)
        b.set_xlabel('Mean Jensen–Shannon divergence (lower is better)');clean(b)
        panel(b,'b','Comparison with a leave-one-country-out human baseline')
        b.legend(handles=[Line2D([],[],color='#555555',marker='s',ls='',label='LOCO human'),Line2D([],[],color='#555555',marker='o',ls='',label='Country-conditioned model')],loc='lower center',bbox_to_anchor=(.5,1),ncol=2,frameon=False,fontsize=7.5)
        b.set_title(b.get_title(loc='left'),loc='left',pad=34,fontweight='bold')
        save_figure(fig,figdir,'figure3_population_specificity')

    e=_read(results,'entropy_structure_summary.csv')
    if not e.empty:
        e=e.set_index('condition').reindex(conds).dropna(subset=['n']).reset_index()
        fig,(a,b)=plt.subplots(2,1,figsize=(7.5,5.8),layout='constrained',gridspec_kw={'height_ratios':[.85,1.2]})
        y=np.arange(len(e))
        for i,r in e.iterrows():
            g=full[full.condition==r.condition]; hm=g.human_entropy.mean(); mm=g.model_entropy.mean()
            a.plot([mm,hm],[i,i],color='#BBBBBB',lw=1.5)
            a.scatter(hm,i,c='#555555',s=36,marker='s');a.scatter(mm,i,c=COLORS[r.condition],s=40)
            a.text(.99,i,f'{mm:.3f} / {hm:.3f}',ha='right',va='center',fontsize=8)
        a.set_xlim(0,1);a.set_yticks(y,[LABELS[c] for c in e.condition]);a.set_ylim(len(e)-.5,-.5)
        a.set_xlabel('Mean normalized entropy');clean(a)
        panel(a,'a','Average disagreement on each model’s observed cells')
        a.legend(handles=[Line2D([],[],color='#555555',marker='s',ls='',label='Human'),Line2D([],[],color='#555555',marker='o',ls='',label='Model')],loc='lower center',bbox_to_anchor=(.5,1),ncol=2,frameon=False,fontsize=7.5)
        a.set_title(a.get_title(loc='left'),loc='left',pad=34,fontweight='bold')
        specs=[('ols','Pooled'),('item_fe','Item fixed effects'),('two_way_fe','Country + item\nfixed effects')]
        for j,r in e.iterrows():
            offset=(j-(len(e)-1)/2)*.2
            vals=np.array([r[f'{k}_slope'] for k,_ in specs]); lo=np.array([r[f'{k}_ci_low'] for k,_ in specs]);hi=np.array([r[f'{k}_ci_high'] for k,_ in specs])
            b.errorbar(vals,np.arange(3)+offset,xerr=np.vstack([vals-lo,hi-vals]),fmt='o',ms=4,capsize=2.5,color=COLORS[r.condition],label=LABELS[r.condition])
        b.axvline(0,color='#666666',ls='--',lw=.8);b.axvline(1,color='#999999',ls=':',lw=.8)
        b.set_yticks(range(3),[s[1] for s in specs]);b.set_ylim(2.5,-.6);b.set_xlim(-.28,1.1)
        b.set_xlabel('Slope of model entropy on human entropy (95% CI)');clean(b)
        panel(b,'b','Association with the pattern of human disagreement')
        b.legend(loc='lower center',bbox_to_anchor=(.5,1.01),ncol=len(e),frameon=False,fontsize=7.5)
        b.set_title(b.get_title(loc='left'),loc='left',pad=34,fontweight='bold')
        save_figure(fig,figdir,'figure4_heterogeneity_structure')

    # S1: paired comparison, with equal scales and an explicit sample size.
    piv=full.pivot(index=['country','item'],columns='condition',values='js')
    if {'gpt56_sol','jev'} <= set(piv):
        p=piv[['gpt56_sol','jev']].dropna();fig,ax=plt.subplots(figsize=(5.3,4.7),layout='constrained')
        ax.scatter(p.gpt56_sol,p.jev,s=10,c=COLORS['jev'],alpha=.42,edgecolors='none',rasterized=True)
        ax.plot([0,1],[0,1],c='#888888',ls='--',lw=.8);ax.set(xlim=(0,1),ylim=(0,1),xlabel='GPT-5.6 Sol JSD',ylabel='Jev JSD',aspect='equal')
        ax.set_title(f'Paired distributional fidelity (n={len(p):,})',loc='left',fontweight='bold')
        ax.text(.04,.94,'Above line: GPT-5.6 Sol closer\nBelow line: Jev closer',transform=ax.transAxes,va='top',fontsize=8)
        save_figure(fig,figdir,'figure_s1_sol_vs_jev_fidelity')

    # S2: preserve the full range; an ECDF avoids hiding outliers in boxplots.
    s=_read(results,'prompt_sensitivity.csv')
    if not s.empty:
        s=s[s.country!='__DEFAULT__']
        fig,ax=plt.subplots(figsize=(6.7,4),layout='constrained')
        for c in _conditions(s):
            vals=np.sort(s.loc[s.condition==c,'js_to_condition_mean'].dropna())
            if not len(vals):continue
            ax.step(vals,np.arange(1,len(vals)+1)/len(vals),where='post',c=COLORS[c],label=f'{LABELS[c]} (n={len(vals):,})')
        ax.set(xlim=(0,max(s.js_to_condition_mean.max(),.01)),ylim=(0,1.015),xlabel='JSD from the condition mean',ylabel='Cumulative fraction of retained variants')
        ax.set_title('Sensitivity to respondent wording',loc='left',fontweight='bold');clean(ax)
        ax.legend(loc='lower right',frameon=False)
        save_figure(fig,figdir,'figure_s2_prompt_sensitivity')

    specs=[
        ('tables/table_s13_label_sensitivity.csv','figure_s3_label_sensitivity_heatmap','mean_js','Sensitivity to response-label assignments','Mean JSD from label mean',False,None,'.3f'),
        ('tables/table_s14_option_order_sensitivity.csv','figure_s4_option_order_heatmap','mean_js','Sensitivity to answer-option order','Mean JSD from order 0',False,None,'.3f'),
        ('tables/table_s6_item_summary.csv','figure_s5_item_error_heatmap','js_mean','Distributional error by survey item','Mean JSD',False,(0,1),'.3f'),
        ('entropy_structure_by_item.csv','figure_s9_entropy_by_item_heatmap','pearson','Entropy association across countries within each item','Pearson correlation',True,(-1,1),'.2f'),
        ('tables/table_s12_population_specificity_by_item.csv','figure_s10_population_specificity_by_item_heatmap','gain_vs_default_mean','Country-prompting gain by survey item','Mean JSD gain',True,None,'.3f'),
    ]
    for path,stem,val,title,clabel,div,limits,fmt in specs:
        data=_read(results,path)
        if data.empty:continue
        fig,ax=plt.subplots(figsize=(7.1,5.4),layout='constrained')
        _heatmap(ax,data,val,title,clabel,center_zero=div,limits=limits,fmt=fmt)
        save_figure(fig,figdir,stem)

    d=_read(results,'openai_censoring_policy_counts.csv')
    if not d.empty:
        cs=_conditions(d);fig,ax=plt.subplots(figsize=(6.6,3.9),layout='constrained')
        policies=[('primary','Primary (≤0.001)','#0072B2'),('strict','Strict (≤0.0001)','#56B4E9'),('complete_only','All labels observed','#CC79A7')]
        for j,(p,lab,color) in enumerate(policies):
            vals=[d[(d.condition==c)&(d.censoring_policy==p)].included_percent.iloc[0] for c in cs]
            x=np.arange(len(cs))+(j-1)*.24;ax.bar(x,vals,.22,color=color,label=lab)
            for xx,v in zip(x,vals):ax.text(xx,v+1.5,f'{v:.1f}%',ha='center',fontsize=8)
        ax.set_xticks(range(len(cs)),[LABELS[c] for c in cs]);ax.set_ylim(0,115);ax.set_ylabel('Retained calls (%)');clean(ax,'y')
        ax.legend(loc='lower center',bbox_to_anchor=(.5,1.01),ncol=3,frameon=False,fontsize=7.5)
        save_figure(fig,figdir,'figure_s6_topk_retention')

    y=_read(results,'tables/table_s9_y003.csv')
    if not y.empty:
        qs=['Independence','Determination, perseverance','Religious faith','Obedience'];cs=_conditions(y)
        fig,ax=plt.subplots(figsize=(6.7,4),layout='constrained');width=.8/len(cs)
        for j,c in enumerate(cs):
            vals=[y[(y.condition==c)&(y.quality==q)].mae.mean() for q in qs]
            x=np.arange(4)+(j-(len(cs)-1)/2)*width;ax.bar(x,vals,width*.92,color=COLORS[c],label=LABELS[c])
        ax.set_xticks(range(4),['Independence','Determination /\nperseverance','Religious faith','Obedience'])
        ax.set_ylim(0,.75);ax.set_ylabel('Mean absolute probability error');clean(ax,'y')
        ax.legend(loc='lower center',bbox_to_anchor=(.5,1),ncol=len(cs),frameon=False)
        save_figure(fig,figdir,'figure_s7_y003_mae')

    d=_read(results,'cultural_map_distances.csv')
    if not d.empty:
        cs=_conditions(d);fig,ax=plt.subplots(figsize=(7,4.2),layout='constrained')
        reps=[('expected','Expected score',WITH),('argmax','Aggregated argmax',WITHOUT),('tao_modal','Variant-wise modal','#E69F00')]
        arrays=[];pos=[];colors=[];ticks=[]
        for i,c in enumerate(cs):
            for j,(rep,lab,col) in enumerate(reps):
                v=d[(d.condition==c)&(d.representation==rep)].distance.dropna()
                if v.empty: continue
                arrays.append(v);pos.append(i*4+j+1);colors.append(col)
                ax.text(i*4+j+1,-.28,f'n={len(v)}',ha='center',fontsize=6.8)
        _boxes(ax,arrays,pos,colors);ax.set_ylim(-.4,max(a.max() for a in arrays)*1.05)
        ax.set_xticks([i*4+2 for i in range(len(cs))],[LABELS[c] for c in cs]);ax.set_ylabel('Distance from target human country');clean(ax,'y')
        ax.legend(handles=[Patch(facecolor=c,label=l) for _,l,c in reps],loc='lower center',bbox_to_anchor=(.5,1),ncol=3,frameon=False,fontsize=7.5)
        save_figure(fig,figdir,'figure_s8_cultural_map_representations')

    fig,axs=plt.subplots(1,len(conds),figsize=(8.2,3.15),sharex=True,sharey=True,layout='constrained',squeeze=False)
    for ax,c in zip(axs[0],conds):
        g=full[full.condition==c]
        ax.scatter(g.human_entropy,g.model_entropy,s=7,c=COLORS[c],alpha=.3,edgecolors='none',rasterized=True)
        ax.plot([0,1],[0,1],c='#888888',ls='--',lw=.8)
        ax.set(xlim=(-.015,1.015),ylim=(-.015,1.015),aspect='equal')
        ax.set_title(f'{LABELS[c]} (n={len(g)})',fontweight='bold')
        ax.set_xlabel('Human entropy');ax.set_xticks([0,.5,1])
    axs[0,0].set_ylabel('Model entropy')
    save_figure(fig,figdir,'figure_s11_entropy_scatter_diagnostic')
