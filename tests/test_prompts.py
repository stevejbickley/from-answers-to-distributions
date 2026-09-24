from src.prompts import probability_prompt,y002_pairs

def test_y002_12_pairs():
    x=y002_pairs(); assert len(x)==12; assert sum(a['index']==1 for a in x)==2; assert sum(a['index']==3 for a in x)==2; assert sum(a['index']==2 for a in x)==8

def test_labels_unique():
    p=probability_prompt('F063',0,'Australia'); assert len(p['allowed_labels'])==10; assert len(set(p['allowed_labels']))==10
