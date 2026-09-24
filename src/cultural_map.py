from __future__ import annotations
import numpy as np
import pandas as pd
from .config import analysis

ITEMS = analysis()['cultural_map_items']

def weighted_mean(x,w):
    m=np.isfinite(x)&np.isfinite(w)&(w>0)
    return np.average(x[m],weights=w[m]) if m.any() else np.nan

def weighted_sd(x,w):
    m=np.isfinite(x)&np.isfinite(w)&(w>0)
    if m.sum()<2:return np.nan
    mu=np.average(x[m],weights=w[m]); return np.sqrt(np.average((x[m]-mu)**2,weights=w[m]))

def pairwise_weighted_corr(df, cols, weight):
    R=np.eye(len(cols)); w=np.asarray(df[weight],float)
    for i,a in enumerate(cols):
        for j,b in enumerate(cols[:i]):
            x=np.asarray(df[a],float); y=np.asarray(df[b],float)
            m=np.isfinite(x)&np.isfinite(y)&np.isfinite(w)&(w>0)
            if m.sum()<3: r=np.nan
            else:
                ww=w[m]; xx=x[m]; yy=y[m]
                mx=np.average(xx,weights=ww); my=np.average(yy,weights=ww)
                cov=np.average((xx-mx)*(yy-my),weights=ww)
                vx=np.average((xx-mx)**2,weights=ww); vy=np.average((yy-my)**2,weights=ww)
                r=cov/np.sqrt(vx*vy) if vx>0 and vy>0 else np.nan
            R[i,j]=R[j,i]=r
    if np.isnan(R).any(): raise ValueError('Pairwise correlation matrix contains NaN; inspect missingness/variables')
    return R

def varimax(Phi, gamma=1.0, q=100, tol=1e-7):
    p,k=Phi.shape; R=np.eye(k); d=0
    for _ in range(q):
        d_old=d; Lambda=Phi@R
        u,s,vh=np.linalg.svd(Phi.T@(Lambda**3-(gamma/p)*Lambda@np.diag(np.diag(Lambda.T@Lambda))))
        R=u@vh; d=s.sum()
        if d_old and d/d_old < 1+tol: break
    return Phi@R

def fit_pca(df, weight='S017'):
    cols=ITEMS
    R=pairwise_weighted_corr(df,cols,weight)
    vals,vecs=np.linalg.eigh(R); order=np.argsort(vals)[::-1]
    vals=vals[order][:2]; vecs=vecs[:,order][:,:2]
    load=vecs*np.sqrt(vals)
    load=varimax(load)
    # Orient factor 1 so Y003 (autonomy) is positive; factor 2 so F063 (importance of God) is negative.
    if load[cols.index('Y003'),0] < 0: load[:,0]*=-1
    if load[cols.index('F063'),1] > 0: load[:,1]*=-1
    B=np.linalg.solve(R,load)  # regression-style scoring coefficients for standardized variables
    means={c:weighted_mean(np.asarray(df[c],float),np.asarray(df[weight],float)) for c in cols}
    sds={c:weighted_sd(np.asarray(df[c],float),np.asarray(df[weight],float)) for c in cols}
    return {'items':cols,'R':R,'eigenvalues':vals,'loadings':load,'score_coef':B,'means':means,'sds':sds}

def project_expected_scores(expected: dict[str,float], pca):
    z=[]
    for c in pca['items']:
        z.append((float(expected[c])-pca['means'][c])/pca['sds'][c])
    f=np.asarray(z)@pca['score_coef']
    rcfg=analysis()['paper_rescaling']
    return {
        'survival_self_expression': float(rcfg['pc1_multiplier']*f[0]+rcfg['pc1_intercept']),
        'traditional_secular': float(rcfg['pc2_multiplier']*f[1]+rcfg['pc2_intercept'])
    }
