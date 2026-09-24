from __future__ import annotations
import numpy as np
from scipy.stats import wasserstein_distance
from .utils import normalize

def js_divergence(p,q,base=2):
    p=normalize(p); q=normalize(q); m=.5*(p+q)
    def kl(a,b):
        z=a>0
        out=np.sum(a[z]*np.log(a[z]/b[z]))
        return out/np.log(base) if base else out
    return float(.5*kl(p,m)+.5*kl(q,m))

def total_variation(p,q):
    return float(.5*np.abs(normalize(p)-normalize(q)).sum())

def normalized_wasserstein(values,p,q):
    v=np.asarray(values,float); p=normalize(p); q=normalize(q)
    rng=float(v.max()-v.min())
    if rng==0:return 0.0
    return float(wasserstein_distance(v,v,u_weights=p,v_weights=q)/rng)

def expected_value(values,p):
    return float(np.dot(np.asarray(values,float),normalize(p)))

def entropy(p,base=2,normalized=True):
    x=normalize(p); z=x>0; h=float(-np.sum(x[z]*np.log(x[z]))/np.log(base))
    if normalized and len(x)>1: h/=np.log(len(x))/np.log(base)
    return h

def effective_categories(p):
    x=normalize(p); z=x>0
    return float(np.exp(-np.sum(x[z]*np.log(x[z]))))
