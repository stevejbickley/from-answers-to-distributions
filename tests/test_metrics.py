import numpy as np
from src.metrics import *
def test_identical():
    p=[.1,.2,.7]; assert js_divergence(p,p)<1e-12; assert total_variation(p,p)<1e-12; assert normalized_wasserstein([1,2,3],p,p)<1e-12
def test_bounds():
    assert 0 <= js_divergence([1,0],[0,1]) <= 1.0000001
    assert abs(total_variation([1,0],[0,1])-1)<1e-12
