"""Shared publication design, deterministic map labels, and vector export."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox
from .config import load_yaml

ORDER = ['gpt4o_anchor', 'gpt56_sol', 'gpt56_terra', 'jev']
LABELS = {'gpt4o_anchor':'GPT-4o', 'gpt56_sol':'GPT-5.6 Sol',
          'gpt56_terra':'GPT-5.6 Terra', 'jev':'Jev'}
COLORS = {'gpt4o_anchor':'#0072B2', 'gpt56_sol':'#D55E00',
          'gpt56_terra':'#CC79A7', 'jev':'#009E73'}
WITHOUT = '#CC79A7'
WITH = '#0072B2'
REGIONS = dict(zip(
    ['African-Islamic','Catholic Europe','Confucian','English-Speaking',
     'Latin America','Orthodox Europe','Protestant Europe','West & South Asia'],
    ['#000000','#E69F00','#56B4E9','#009E73','#CC79A7','#0072B2','#D55E00','#F0E442']))
ITEMS = {'A008':'Happiness', 'A165':'Interpersonal trust', 'E018':'Respect for authority',
         'E025':'Petition signing', 'F063':'Importance of God', 'F118':'Homosexuality',
         'F120':'Abortion', 'G006':'National pride', 'Y002':'Post-materialism'}
STYLE = {'font.family':'DejaVu Sans', 'font.size':9, 'axes.titlesize':10,
         'axes.labelsize':9, 'xtick.labelsize':8, 'ytick.labelsize':8,
         'legend.fontsize':8, 'axes.spines.top':False, 'axes.spines.right':False,
         'axes.linewidth':.65, 'lines.linewidth':1.1, 'text.color':'#252525',
         'axes.labelcolor':'#252525', 'xtick.color':'#454545', 'ytick.color':'#454545',
         'pdf.fonttype':42, 'ps.fonttype':42, 'svg.fonttype':'none',
         'savefig.facecolor':'white', 'figure.facecolor':'white'}


def conditions(df):
    vals=set(df.condition.astype(str)) - {'human'} if 'condition' in df else set()
    return [c for c in ORDER if c in vals] + sorted(vals-set(ORDER))


def panel(ax, letter, title):
    ax.set_title(f'{letter}  {title}', loc='left', fontweight='bold', pad=12)


def clean(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color='#E9E9E9', linewidth=.6)
    ax.tick_params(length=3, width=.6)


def save_figure(fig, directory, stem):
    """Keep vector text editable; tight bounding boxes include external annotations."""
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    fig.canvas.draw()
    for extension in ['png','pdf','svg']:
        fig.savefig(directory/f'{stem}.{extension}', dpi=600, bbox_inches='tight', pad_inches=.08)
    plt.close(fig)


def region_lookup():
    root=Path(__file__).resolve().parents[1]
    countries=load_yaml(root/'config/countries.yaml')['countries']
    source=pd.read_csv(root/'config/reference/tao_cultural_regions.csv')
    return {countries[int(r.s003)]:r.Category for r in source.itertuples() if int(r.s003) in countries}


def place_map_labels(ax, points, labels, colors, *, font_sizes=None, weights=None):
    """Place every label in free display space; never cover a marker or another label.

    Placement is deterministic and checked using rendered bounding boxes. Leader
    lines connect displaced labels to their unchanged coordinates. A crowded map
    fails explicitly rather than silently dropping labels or hiding observations.
    Call only after axes geometry and limits are final; do not use tight_layout later.
    """
    fig=ax.figure; fig.canvas.draw(); renderer=fig.canvas.get_renderer()
    points=np.asarray(points,float); px=ax.transData.transform(points)
    scale=fig.dpi/72
    bounds=ax.get_window_extent(renderer).padded(-3*scale)
    radii=np.full(len(points),3.3*scale)
    if weights is not None:
        radii=np.array([5.5 if w=='bold' else 3.3 for w in weights])*scale
    occupied=[]; texts=[]; audits=[]
    # Largest labels and model labels first; subsequent labels adapt to them.
    order=sorted(range(len(labels)),key=lambda i: (weights is not None and weights[i]=='bold',len(labels[i])),reverse=True)
    for i in order:
        size=font_sizes[i] if font_sizes else 6.4
        weight=weights[i] if weights else 'normal'
        txt=ax.text(0,0,labels[i],fontsize=size,color=colors[i],weight=weight,
                    ha='center',va='center',zorder=5,clip_on=False)
        bb=txt.get_window_extent(renderer); w,h=bb.width,bb.height
        best=None
        # Search nearest legal placement; fixed angular order gives stable output.
        for radius in np.arange(7,245,3)*scale:
            candidates=[]
            for theta in np.linspace(0,2*np.pi,40,endpoint=False):
                cx=px[i,0]+np.cos(theta)*(radius+w*.45)
                cy=px[i,1]+np.sin(theta)*(radius+h*.45)
                b=Bbox.from_bounds(cx-w/2-1.2*scale,cy-h/2-1.0*scale,w+2.4*scale,h+2*scale)
                if not (bounds.x0 <= b.x0 and b.x1 <= bounds.x1 and bounds.y0 <= b.y0 and b.y1 <= bounds.y1):
                    continue
                if any(b.overlaps(o) for o in occupied):
                    continue
                near=(px[:,0]+radii>b.x0)&(px[:,0]-radii<b.x1)&(px[:,1]+radii>b.y0)&(px[:,1]-radii<b.y1)
                if near.any():
                    continue
                candidates.append((np.hypot(cx-px[i,0],cy-px[i,1]),cx,cy,b))
            if candidates:
                best=min(candidates,key=lambda c:c[0]); break
        if best is None:
            raise RuntimeError(f'No collision-free map label position for {labels[i]}; enlarge map.')
        dist,cx,cy,b=best
        txt.set_position(ax.transData.inverted().transform((cx,cy)))
        occupied.append(b); texts.append(txt)
        # Connect to the nearest edge; lines sit below points and labels.
        tx=np.clip(px[i,0],b.x0+1,b.x1-1); ty=np.clip(px[i,1],b.y0+1,b.y1-1)
        if np.hypot(tx-px[i,0],ty-px[i,1])>4*scale:
            a=ax.transData.inverted().transform((tx,ty))
            ax.annotate('',xy=points[i],xytext=a,arrowprops={'arrowstyle':'-','color':'#A3A3A3','lw':.35,'shrinkA':1,'shrinkB':3},zorder=1)
        audits.append({'label':labels[i],'displacement_points':round(dist/scale,2)})
    fig.canvas.draw()
    actual=[t.get_window_extent(fig.canvas.get_renderer()) for t in texts]
    overlaps=sum(a.overlaps(b) for j,a in enumerate(actual) for b in actual[:j])
    point_overlaps=sum(int(((px[:,0]+radii>a.x0)&(px[:,0]-radii<a.x1)&(px[:,1]+radii>a.y0)&(px[:,1]-radii<a.y1)).sum()) for a in actual)
    if overlaps or point_overlaps:
        raise RuntimeError(f'Map label collision check failed: labels={overlaps}, points={point_overlaps}')
    return {'n_labels':len(labels),'label_overlaps':int(overlaps),'point_overlaps':int(point_overlaps),'labels':audits}
