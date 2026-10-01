import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.tables import make_tables
from src.figures import empirical
from src.manuscript_autofill import build_tokens
import json

Path('figures').mkdir(exist_ok=True)
make_tables('results')
empirical('results','figures')
Path('results/manuscript_tokens.json').write_text(json.dumps(build_tokens('results'),indent=2)+'\n')
print('Tables and figures complete.')
print('Main Figure 1: Tao replication + cultural-prompting extension')
print('Main Figure 2: country-specific direction, projection, default gain and LOCO benchmark')
print('Main Figure 3: average entropy and heterogeneity structure')
print('Supplementary Figures S1-S16 include full-versus-argmax as S15.')
