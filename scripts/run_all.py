import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse, os, subprocess
from dotenv import load_dotenv
load_dotenv()
def envpath(name):
    v=os.getenv(name); return str(Path(v).expanduser()) if v else None
def is_csv_path(path):
    n=str(path).lower() if path else ''; return n.endswith('.csv') or n.endswith('.csv.gz')
p=argparse.ArgumentParser(description='Run human + GPT-4o anchor + GPT-5.6 Sol + Jev pipeline.')
p.add_argument('--ivs',default=envpath('IVS_DATA_PATH')); p.add_argument('--wvs',default=envpath('WVS_DATA_PATH')); p.add_argument('--evs',default=envpath('EVS_DATA_PATH')); p.add_argument('--csv',action='store_true')
p.add_argument('--skip-openai',action='store_true'); p.add_argument('--skip-jev',action='store_true'); p.add_argument('--include-terra',action='store_true',help='Also run GPT-5.6 Terra robustness condition.')
p.add_argument('--robustness',action='store_true'); p.add_argument('--autofill',action='store_true')
a=p.parse_args()
cmd=[sys.executable,'scripts/01_prepare_human.py']
if a.ivs:
    cmd += ['--ivs',a.ivs];
    if a.csv or is_csv_path(a.ivs): cmd += ['--csv']
elif a.wvs and a.evs: cmd += ['--wvs',a.wvs,'--evs',a.evs]
else: raise SystemExit('Provide --ivs/IVS_DATA_PATH OR both --wvs/--evs.')
subprocess.run(cmd,check=True)
if not a.skip_openai:
    ocmd=[sys.executable,'scripts/02_collect_openai.py']
    if a.include_terra: ocmd.append('--include-terra')
    subprocess.run(ocmd,check=True)
if not a.skip_jev: subprocess.run([sys.executable,'scripts/03_collect_jev.py'],check=True)
subprocess.run([sys.executable,'scripts/04_analyze.py'],check=True); subprocess.run([sys.executable,'scripts/05_make_outputs.py'],check=True)
if a.robustness:
    rcmd=[sys.executable,'scripts/07_option_order_robustness.py']
    if a.include_terra: rcmd.append('--include-terra')
    subprocess.run(rcmd,check=True); subprocess.run([sys.executable,'scripts/08_jev_native_score.py'],check=True); subprocess.run([sys.executable,'scripts/09_analyze_robustness.py'],check=True)
subprocess.run([sys.executable,'scripts/10_summarize_api_usage.py'],check=True)
if a.autofill: subprocess.run([sys.executable,'scripts/06_autofill_manuscript.py'],check=True)
print('Done. Primary model conditions: GPT-4o anchor, GPT-5.6 Sol, Jev. Terra is optional robustness.')
