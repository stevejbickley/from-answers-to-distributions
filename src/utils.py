from __future__ import annotations
import json, time, random, hashlib
from pathlib import Path
from typing import Any
import numpy as np


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return Path(path)


def atomic_json(path, obj):
    path = Path(path)
    ensure_dir(path.parent)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    tmp.replace(path)


def jsonl_append(path, record):
    path = Path(path)
    ensure_dir(path.parent)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False, default=str) + '\n')


def stable_id(*parts):
    s = '||'.join(map(str, parts))
    return hashlib.sha256(s.encode()).hexdigest()[:20]


def retry_call(fn, retries=6, base=1.0, cap=30.0):
    last = None
    for attempt in range(retries):
        try:
            return fn()
        except Exception as e:
            last = e
            if attempt == retries - 1:
                raise
            time.sleep(min(cap, base * (2 ** attempt)) + random.random() * 0.25)
    raise last


def normalize(p, eps=0.0):
    x = np.asarray(p, dtype=float)
    if eps:
        x = np.maximum(x, eps)
    s = x.sum()
    if not np.isfinite(s) or s <= 0:
        raise ValueError('Probability vector has non-positive/invalid sum')
    return x / s
