from __future__ import annotations
from itertools import permutations
from string import ascii_uppercase
from .config import questions, variants

LABELS = list(ascii_uppercase[:20])


def descriptor(variant_id: int, country: str | None = None) -> str:
    v = next(x for x in variants() if int(x['id']) == int(variant_id))
    return v['country_descriptor'].format(country=country) if country else v['descriptor']


def y002_pairs():
    goals = questions()['Y002']['goals']
    out = []
    for a, b in permutations(['1','2','3','4'], 2):
        if {a,b} == {'1','3'}:
            idx = 1
        elif {a,b} == {'2','4'}:
            idx = 3
        else:
            idx = 2
        out.append({'pair': f'{a},{b}', 'first': a, 'second': b, 'index': idx,
                    'description': f'First: {a} {goals[a]}; second: {b} {goals[b]}'})
    return out


def semantic_options(item_id: str):
    q = questions()[item_id]
    if item_id == 'Y002':
        return [(x['pair'], x['description']) for x in y002_pairs()]
    if item_id == 'Y003':
        raise ValueError('Y003 uses constituent marginal questions, not one-of-K primary elicitation')
    return [(str(k), str(v)) for k, v in q['choices'].items()]


def balanced_label_map(item_id: str, variant_id: int, permutation_id: int = 0):
    """Map semantic values to simple labels, rotating by variant/permutation.

    Labels are kept within A-L for all primary items. Rotation helps diagnose
    token-label and order artifacts without changing the substantive question.
    """
    options = semantic_options(item_id)
    n = len(options)
    labels = LABELS[:n]
    shift = (int(variant_id) + int(permutation_id)) % n
    rotated = labels[shift:] + labels[:shift]
    return {semantic: rotated[i] for i, (semantic, _) in enumerate(options)}


def probability_prompt(item_id: str, variant_id: int, country: str | None = None,
                       permutation_id: int = 0, option_order: list[str] | None = None):
    q = questions()[item_id]
    sys = descriptor(variant_id, country)
    opts = semantic_options(item_id)
    if option_order is not None:
        by_key=dict(opts); opts=[(k,by_key[k]) for k in option_order]
    mapping = balanced_label_map(item_id, variant_id, permutation_id)
    # Keep semantic option order fixed in primary analysis. Label rotation is diagnostic/fairness control.
    lines = []
    for semantic, desc in opts:
        lines.append(f"{mapping[semantic]} = {desc}")
    if item_id == 'Y002':
        stem = q['source_prompt'].split('You can only respond')[0].strip()
    else:
        stem = q['source_prompt'].split('You can only respond')[0].strip()
    user = (
        f"{stem}\n\nResponse options:\n" + "\n".join(lines) +
        "\n\nReturn exactly ONE option label and nothing else. "
        "Do not explain your answer. Your response:"
    )
    reverse = {v: k for k, v in mapping.items()}
    return {'system': sys, 'user': user, 'semantic_to_label': mapping,
            'label_to_semantic': reverse, 'allowed_labels': list(reverse)}


def original_discrete_prompt(item_id: str, variant_id: int, country: str | None = None):
    return {'system': descriptor(variant_id, country), 'user': questions()[item_id]['source_prompt']}


def y003_constituent_prompt(target_quality: str, variant_id: int, country: str | None = None,
                            label_yes='A', label_no='B'):
    q = questions()['Y003']
    sys = descriptor(variant_id, country)
    full = q['source_prompt'].split('You can only respond')[0].strip()
    user = (
        f"{full}\n\nConsidering the same instruction to choose up to five qualities, "
        f"would you include \"{target_quality}\" among your choices?\n"
        f"{label_yes} = Yes\n{label_no} = No\n\n"
        f"Return exactly {label_yes} or {label_no}, and nothing else. Your response:"
    )
    return {'system': sys, 'user': user, 'semantic_to_label': {'1': label_yes, '0': label_no},
            'label_to_semantic': {label_yes:'1', label_no:'0'}, 'allowed_labels':[label_yes,label_no]}
