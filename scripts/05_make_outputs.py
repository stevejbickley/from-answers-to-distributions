import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path
from src.tables import make_tables
from src.figures import conceptual, empirical
Path('figures').mkdir(exist_ok=True); conceptual('figures/figure1_probability_semantics.png'); make_tables('results'); empirical('results','figures'); print('Tables and figures complete')
