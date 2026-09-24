from __future__ import annotations
from pathlib import Path
import os, re, yaml

ROOT = Path(__file__).resolve().parents[1]

def _expand_env(obj):
    if isinstance(obj, dict):
        return {k: _expand_env(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_expand_env(v) for v in obj]
    if isinstance(obj, str):
        m = re.fullmatch(r"\$\{([A-Z0-9_]+)(?::([^}]*))?\}", obj)
        if m:
            return os.getenv(m.group(1), m.group(2) or "")
    return obj

def load_yaml(relpath: str):
    with open(ROOT / relpath, 'r', encoding='utf-8') as f:
        return _expand_env(yaml.safe_load(f))

def questions(): return load_yaml('config/questions.yaml')['items']
def variants(): return load_yaml('config/prompt_variants.yaml')['variants']
def models(): return load_yaml('config/models.yaml')
def analysis(): return load_yaml('config/analysis.yaml')
