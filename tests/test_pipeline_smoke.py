from pathlib import Path
import subprocess,sys

def test_fixture_exists_or_builds():
    if not Path('tests/fixtures/synthetic_ivsd.csv').exists(): subprocess.run([sys.executable,'tests/fixtures/create_synthetic_ivsd.py'],check=True)
    assert Path('tests/fixtures/synthetic_ivsd.csv').exists()
