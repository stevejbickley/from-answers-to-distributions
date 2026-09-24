from pathlib import Path
import numpy as np,pandas as pd
rng=np.random.default_rng(7); rows=[]
for country_code,country in [(36,'Australia'),(392,'Japan'),(710,'South Africa')]:
    for year,wave in [(2006,5),(2012,6),(2020,7)]:
        for i in range(150):
            r={'S001':i,'S002VS':wave,'S003':country,'S009':country,'S017':rng.uniform(.5,1.5),'S020':year}
            r.update({'A008':rng.integers(1,5),'A165':rng.integers(1,3),'E018':rng.integers(1,4),'E025':rng.integers(1,4),
                      'F063':rng.integers(1,11),'F118':rng.integers(1,11),'F120':rng.integers(1,11),'G006':rng.integers(1,5),'Y002':rng.integers(1,4)})
            for v in ['A029','A039','A040','A042']: r[v]=rng.integers(0,2)
            r['Y003']=r['A029']+r['A039']-r['A040']-r['A042']; rows.append(r)
Path('tests/fixtures').mkdir(parents=True,exist_ok=True); pd.DataFrame(rows).to_csv('tests/fixtures/synthetic_ivsd.csv',index=False)
print('wrote synthetic fixture')
