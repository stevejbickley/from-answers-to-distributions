from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from .utils import ensure_dir

def conceptual(outfile):
    fig,ax=plt.subplots(figsize=(10,4.8)); ax.axis('off')
    boxes=[(0.05,0.58,0.25,0.27,'Human population','Survey-weighted frequencies\nP(response | country)'),
           (0.375,0.58,0.25,0.27,'OpenAI','Next-token uncertainty\nP(token | prompt)'),
           (0.70,0.58,0.25,0.27,'Jev','Typed decision uncertainty\nP(choice | state, options)')]
    for x,y,w,h,title,body in boxes:
        rect=plt.Rectangle((x,y),w,h,fill=False,linewidth=1.5,transform=ax.transAxes); ax.add_patch(rect)
        ax.text(x+w/2,y+h*.68,title,ha='center',va='center',weight='bold',transform=ax.transAxes,fontsize=12)
        ax.text(x+w/2,y+h*.33,body,ha='center',va='center',transform=ax.transAxes,fontsize=10)
    ax.text(.5,.36,'Distributional comparison',ha='center',weight='bold',transform=ax.transAxes,fontsize=12)
    for x in [.175,.50,.825]: ax.annotate('',xy=(.50,.47),xytext=(x,.57),xycoords=ax.transAxes,textcoords=ax.transAxes,arrowprops=dict(arrowstyle='->'))
    ax.text(.5,.18,'Jensen-Shannon / total variation / Wasserstein / expected score / entropy',ha='center',transform=ax.transAxes,fontsize=10)
    fig.tight_layout(); fig.savefig(outfile,dpi=220,bbox_inches='tight'); plt.close(fig)

def empirical(results='results',figdir='figures'):
    figdir=ensure_dir(figdir); results=Path(results); m=pd.read_csv(results/'country_item_metrics.csv')
    piv=m.pivot_table(index=['country','item'],columns='provider',values='js').dropna()
    fig,ax=plt.subplots(figsize=(6.5,6)); ax.scatter(piv['openai'],piv['jev'],s=18,alpha=.5)
    lim=max(piv.max().max()*1.02,.01); ax.plot([0,lim],[0,lim],linestyle='--',linewidth=1)
    ax.set(xlabel='OpenAI logprob JSD',ylabel='Jev decision-probability JSD',xlim=(0,lim),ylim=(0,lim))
    fig.tight_layout(); fig.savefig(figdir/'figure2_distributional_fidelity.png',dpi=220); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,6))
    for provider,g in m.groupby('provider'): ax.scatter(g['human_entropy'],g['model_entropy'],s=16,alpha=.45,label=provider)
    ax.plot([0,1],[0,1],linestyle='--',linewidth=1); ax.set(xlabel='Human normalized entropy',ylabel='Model normalized entropy',xlim=(0,1),ylim=(0,1)); ax.legend()
    fig.tight_layout(); fig.savefig(figdir/'figure3_entropy_recovery.png',dpi=220); plt.close(fig)
    s=pd.read_csv(results/'prompt_sensitivity.csv'); data=[s[s.provider==p]['js_to_provider_mean'].dropna().values for p in ['openai','jev']]
    fig,ax=plt.subplots(figsize=(6.5,5)); ax.boxplot(data,tick_labels=['OpenAI','Jev'],showfliers=False); ax.set_ylabel('JSD to provider mean across prompt variants')
    fig.tight_layout(); fig.savefig(figdir/'figure_s2_prompt_sensitivity.png',dpi=220); plt.close(fig)
    # Item error figure
    items=sorted(m.item.unique()); positions=np.arange(len(items)); width=.36
    fig,ax=plt.subplots(figsize=(10,5.5))
    for idx,p in enumerate(['openai','jev']):
        vals=[m[(m.provider==p)&(m.item==it)].js.mean() for it in items]
        ax.bar(positions+(idx-.5)*width,vals,width,label=p)
    ax.set_xticks(positions,items,rotation=45,ha='right'); ax.set_ylabel('Mean Jensen-Shannon divergence'); ax.legend(); fig.tight_layout(); fig.savefig(figdir/'figure_s4_item_error.png',dpi=220); plt.close(fig)
    # OpenAI allowed mass
    dpath=results/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath); fig,ax=plt.subplots(figsize=(7,5));
        groups=[d[d.item==it].allowed_mass.values for it in sorted(d.item.unique())]
        ax.boxplot(groups,tick_labels=sorted(d.item.unique()),showfliers=False); ax.set_ylim(0,1.01); ax.set_ylabel('Allowed next-token probability mass'); ax.tick_params(axis='x',rotation=45)
        fig.tight_layout(); fig.savefig(figdir/'figure_s5_allowed_mass.png',dpi=220); plt.close(fig)
    # Y003 marginals
    ypath=results/'y003_marginal_metrics.csv'
    if ypath.exists():
        y=pd.read_csv(ypath); fig,ax=plt.subplots(figsize=(7,6))
        for p,g in y.groupby('provider'): ax.scatter(g.p_selected_human,g.p_selected_model,s=18,alpha=.5,label=p)
        ax.plot([0,1],[0,1],linestyle='--',linewidth=1); ax.set(xlabel='Human marginal selection probability',ylabel='Model probability',xlim=(0,1),ylim=(0,1)); ax.legend(); fig.tight_layout(); fig.savefig(figdir/'figure_s6_y003.png',dpi=220); plt.close(fig)
    # Cultural map and distance panel
    cpath=results/'cultural_map_coordinates.csv'
    if cpath.exists():
        c=pd.read_csv(cpath); fig,ax=plt.subplots(figsize=(8,7)); h=c[(c.provider=='human')&(c.representation=='expected')]
        ax.scatter(h.survival_self_expression,h.traditional_secular,s=18,alpha=.45,label='Human countries')
        for p in ['openai','jev']:
            g=c[(c.provider==p)&(c.representation=='expected')&(c.country!='__DEFAULT__')]
            ax.scatter(g.survival_self_expression,g.traditional_secular,s=14,alpha=.35,label=p)
            d=c[(c.provider==p)&(c.representation=='expected')&(c.country=='__DEFAULT__')]
            if len(d): ax.scatter(d.survival_self_expression,d.traditional_secular,s=90,marker='*',label=p+' default')
        ax.set(xlabel='Survival vs. self-expression',ylabel='Traditional vs. secular-rational'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'figure4_cultural_map.png',dpi=220); plt.close(fig)
