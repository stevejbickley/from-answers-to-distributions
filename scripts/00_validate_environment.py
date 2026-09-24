import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os, sys
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
print('Python:',sys.version)
for k in ['OPENAI_API_KEY','TYPESAFE_API_KEY']:
    print(k, 'set' if os.getenv(k) else 'NOT SET')
for p in ['config/questions.yaml','config/prompt_variants.yaml','config/analysis.yaml']:
    assert Path(p).exists(),p
print('Configuration files OK')
