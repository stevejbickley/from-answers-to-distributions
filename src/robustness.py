"""Sensitivity estimates with explicit, reproducible comparison sets."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .analyze import aggregate_y002, openai_record_included
from .config import questions
from .metrics import js_divergence


def option_order_metrics(records):
    """Compare retained alternative orders with prespecified rep=0.

    Excluded reference requests never get replaced by another permutation.
    Return a cell-level coverage audit alongside the valid comparisons.
    """
    qs = questions()
    rows, coverage = [], []
    frame = pd.DataFrame(records)
    if frame.empty:
        return pd.DataFrame(), pd.DataFrame()
    frame['condition'] = frame.get('condition', frame.provider)
    frame['condition_label'] = frame.get('condition_label', frame.condition)
    frame['included'] = [r.get('provider') != 'openai' or openai_record_included(r) for r in records]

    def vector(record, item):
        probs = record['probabilities']
        if item == 'Y002':
            probs = aggregate_y002(probs)
        v = np.array([float(probs.get(str(k), 0)) for k in qs[item]['human_codes']])
        if not np.isfinite(v).all() or v.sum() <= 0:
            raise ValueError(f'Invalid option-order probability vector: {item}')
        return v / v.sum()

    keys = ['provider', 'condition', 'condition_label', 'country', 'item']
    for key, g in frame.groupby(keys):
        if g.rep.duplicated().any():
            raise ValueError(f'Duplicate option-order replicate: {key}')
        base = dict(zip(keys, key))
        good = g[g.included]
        ref = good[good.rep == 0]
        coverage.append({**base, 'requests':len(g), 'retained_requests':len(good),
                         'reference_retained':not ref.empty,
                         'valid_comparisons':int((good.rep != 0).sum()) if len(ref) else 0})
        if ref.empty:
            continue
        rv = vector(ref.iloc[0], base['item'])
        for _, r in good[good.rep != 0].iterrows():
            rows.append({**base, 'reference_rep':0, 'rep':int(r.rep),
                         'js_from_first_order':js_divergence(rv, vector(r, base['item']))})
    return pd.DataFrame(rows), pd.DataFrame(coverage)
