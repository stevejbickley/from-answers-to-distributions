import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse,subprocess,sys
p=argparse.ArgumentParser(); p.add_argument('--ivs'); p.add_argument('--wvs'); p.add_argument('--evs'); p.add_argument('--csv',action='store_true'); p.add_argument('--skip-openai',action='store_true'); p.add_argument('--skip-jev',action='store_true'); p.add_argument('--robustness',action='store_true'); a=p.parse_args()
cmd=[sys.executable,'scripts/01_prepare_human.py']
if a.ivs: cmd += ['--ivs',a.ivs]
else: cmd += ['--wvs',a.wvs,'--evs',a.evs]
if a.csv: cmd += ['--csv']
subprocess.run(cmd,check=True)
if not a.skip_openai: subprocess.run([sys.executable,'scripts/02_collect_openai.py'],check=True)
if not a.skip_jev: subprocess.run([sys.executable,'scripts/03_collect_jev.py'],check=True)
subprocess.run([sys.executable,'scripts/04_analyze.py'],check=True)
subprocess.run([sys.executable,'scripts/05_make_outputs.py'],check=True)
if a.robustness:
    subprocess.run([sys.executable,'scripts/07_option_order_robustness.py'],check=True)
    subprocess.run([sys.executable,'scripts/08_jev_native_score.py'],check=True)
    subprocess.run([sys.executable,'scripts/09_analyze_robustness.py'],check=True)
print('Done. Numerical manuscript tokens are in results/manuscript_tokens.json')
