import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
from pathlib import Path
from src.human import load_ivsd,clean,save_processed
from src.cultural_map import fit_pca
import json, numpy as np
p=argparse.ArgumentParser(); p.add_argument('--ivs'); p.add_argument('--wvs'); p.add_argument('--evs'); p.add_argument('--csv',action='store_true'); p.add_argument('--outdir',default='data/processed')
a=p.parse_args(); df,metas=load_ivsd(a.ivs,a.wvs,a.evs,csv=a.csv); df=clean(df); save_processed(df,metas,a.outdir)
pca=fit_pca(df)
serial={k:(v.tolist() if hasattr(v,'tolist') else v) for k,v in pca.items()}
Path(a.outdir,'pca_model.json').write_text(json.dumps(serial,indent=2),encoding='utf-8')
print('Prepared',len(df),'human records')
