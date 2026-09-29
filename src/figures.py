from __future__ import annotations
from pathlib import Path
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from .utils import ensure_dir

ORDER=['gpt4o_anchor','gpt56_sol','gpt56_terra','jev']
LABELS={'gpt4o_anchor':'GPT-4o anchor','gpt56_sol':'GPT-5.6 Sol','gpt56_terra':'GPT-5.6 Terra','jev':'Jev'}

def conceptual(outfile):
    fig,ax=plt.subplots(figsize=(10.5,5)); ax.axis('off')
    boxes=[(0.03,0.60,0.22,0.25,'Human population','Survey frequencies\nP(response | country)'),
           (0.29,0.60,0.22,0.25,'GPT-4o','Historical-generation\nnext-token probabilities'),
           (0.55,0.60,0.22,0.25,'GPT-5.6 Sol','Contemporary\nnext-token probabilities'),
           (0.81,0.60,0.16,0.25,'Jev','Typed decision\nprobabilities')]
    for x,y,w,h,title,body in boxes:
        ax.add_patch(plt.Rectangle((x,y),w,h,fill=False,linewidth=1.5,transform=ax.transAxes)); ax.text(x+w/2,y+h*.68,title,ha='center',weight='bold',transform=ax.transAxes); ax.text(x+w/2,y+h*.30,body,ha='center',transform=ax.transAxes,fontsize=9)
        ax.annotate('',xy=(.50,.45),xytext=(x+w/2,y),xycoords=ax.transAxes,textcoords=ax.transAxes,arrowprops=dict(arrowstyle='->'))
    ax.text(.5,.37,'Distributional fidelity + point-versus-distribution decomposition',ha='center',weight='bold',transform=ax.transAxes)
    ax.text(.5,.18,'Human heterogeneity  ↔  lexical uncertainty  ↔  temporal model change  ↔  decision uncertainty',ha='center',transform=ax.transAxes,fontsize=10)
    fig.tight_layout(); fig.savefig(outfile,dpi=220,bbox_inches='tight'); plt.close(fig)

def _conditions(df): return [c for c in ORDER if c in set(df.condition)] + [c for c in sorted(set(df.condition)) if c not in ORDER]
def empirical(results='results',figdir='figures'):
    figdir=ensure_dir(figdir); results=Path(results); m=pd.read_csv(results/'country_item_metrics.csv'); full=m[m.representation=='full']
    # Primary Sol-vs-Jev fidelity scatter.
    piv=full.pivot_table(index=['country','item'],columns='condition',values='js')
    if {'gpt56_sol','jev'}.issubset(piv.columns):
        pp=piv[['gpt56_sol','jev']].dropna(); fig,ax=plt.subplots(figsize=(6.5,6)); ax.scatter(pp.gpt56_sol,pp.jev,s=18,alpha=.5)
        lim=max(pp.max().max()*1.02,.01); ax.plot([0,lim],[0,lim],linestyle='--',linewidth=1); ax.set(xlabel='GPT-5.6 Sol logprob JSD',ylabel='Jev decision-probability JSD',xlim=(0,lim),ylim=(0,lim)); fig.tight_layout(); fig.savefig(figdir/'figure2_distributional_fidelity.png',dpi=220); plt.close(fig)
    # All model conditions: human vs model entropy.
    fig,ax=plt.subplots(figsize=(7.5,6));
    for c in _conditions(full):
        g=full[full.condition==c]; ax.scatter(g.human_entropy,g.model_entropy,s=15,alpha=.35,label=LABELS.get(c,c))
    ax.plot([0,1],[0,1],linestyle='--',linewidth=1); ax.set(xlabel='Human normalized entropy',ylabel='Model normalized entropy',xlim=(0,1),ylim=(0,1)); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'figure3_entropy_recovery.png',dpi=220); plt.close(fig)
    # Full-vs-argmax gain by condition.
    rows=[]
    for c in _conditions(m):
        p=m[m.condition==c].pivot_table(index=['country','item'],columns='representation',values='js').dropna()
        if {'full','argmax'}.issubset(p.columns): rows.append((LABELS.get(c,c),(p.argmax-p.full).values))
    if rows:
        fig,ax=plt.subplots(figsize=(7.5,5)); ax.boxplot([x[1] for x in rows],tick_labels=[x[0] for x in rows],showfliers=False); ax.axhline(0,linewidth=1,linestyle='--'); ax.set_ylabel('JSD(argmax) - JSD(full distribution)'); ax.tick_params(axis='x',rotation=20); fig.tight_layout(); fig.savefig(figdir/'figure_s3_distribution_value_added.png',dpi=220); plt.close(fig)
    s=pd.read_csv(results/'prompt_sensitivity.csv'); conds=_conditions(s); fig,ax=plt.subplots(figsize=(7.5,5)); ax.boxplot([s[s.condition==c].js_to_condition_mean.dropna().values for c in conds],tick_labels=[LABELS.get(c,c) for c in conds],showfliers=False); ax.set_ylabel('JSD to condition mean across prompt variants'); ax.tick_params(axis='x',rotation=20); fig.tight_layout(); fig.savefig(figdir/'figure_s2_prompt_sensitivity.png',dpi=220); plt.close(fig)
    # Item errors.
    items=sorted(full.item.unique()); conds=_conditions(full); positions=np.arange(len(items)); width=.8/max(len(conds),1); fig,ax=plt.subplots(figsize=(11,5.5))
    for idx,c in enumerate(conds):
        vals=[full[(full.condition==c)&(full.item==it)].js.mean() for it in items]; ax.bar(positions+(idx-(len(conds)-1)/2)*width,vals,width,label=LABELS.get(c,c))
    ax.set_xticks(positions,items,rotation=45,ha='right'); ax.set_ylabel('Mean Jensen-Shannon divergence'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'figure_s4_item_error.png',dpi=220); plt.close(fig)
    dpath=results/'openai_logprob_diagnostics.csv'
    if dpath.exists():
        d=pd.read_csv(dpath); conds=_conditions(d); fig,ax=plt.subplots(figsize=(7,5)); ax.boxplot([d[d.condition==c].allowed_mass.values for c in conds],tick_labels=[LABELS.get(c,c) for c in conds],showfliers=False); ax.set_ylim(0,1.01); ax.set_ylabel('Permitted-label next-token probability mass'); ax.tick_params(axis='x',rotation=20); fig.tight_layout(); fig.savefig(figdir/'figure_s5_allowed_mass.png',dpi=220); plt.close(fig)
    ypath=results/'y003_marginal_metrics.csv'
    if ypath.exists():
        y=pd.read_csv(ypath); fig,ax=plt.subplots(figsize=(7,6));
        for c in _conditions(y):
            g=y[y.condition==c]; ax.scatter(g.p_selected_human,g.p_selected_model,s=16,alpha=.4,label=LABELS.get(c,c))
        ax.plot([0,1],[0,1],linestyle='--',linewidth=1); ax.set(xlabel='Human marginal selection probability',ylabel='Model probability',xlim=(0,1),ylim=(0,1)); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'figure_s6_y003.png',dpi=220); plt.close(fig)
    cpath=results/'cultural_map_coordinates.csv'
    if cpath.exists():
        c=pd.read_csv(cpath); fig,ax=plt.subplots(figsize=(8,7)); h=c[(c.condition=='human')&(c.representation=='expected')]; ax.scatter(h.survival_self_expression,h.traditional_secular,s=18,alpha=.40,label='Human countries')
        for cond in [x for x in _conditions(c) if x!='human']:
            g=c[(c.condition==cond)&(c.representation=='expected')&(c.country!='__DEFAULT__')]; ax.scatter(g.survival_self_expression,g.traditional_secular,s=13,alpha=.30,label=LABELS.get(cond,cond))
        ax.set(xlabel='Survival vs. self-expression',ylabel='Traditional vs. secular-rational'); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(figdir/'figure4_cultural_map.png',dpi=220); plt.close(fig)
