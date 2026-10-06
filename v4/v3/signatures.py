#!/usr/bin/env python3
"""signatures.py (v3.2, frozen): the signature table for T5/T6. Each entry: a mechanism, a textbook relation, its source, the predicted
direction of each observable ('up', 'down', 'none') and a prior rank (1 = the textbook default, used only by the 'textbook prior'
shortcut). Entries are written per paper domain in Stage 5B, unit-tested, and audited blind by GPT-5.6-Sol (any disagreement removes the
entry). An observable is a named change of a quantity between two conditions, e.g. 'grain_size(x up)'.
Phase 1 holds only the validator and the synthetic entries used by the unit tests; papers add their own tables (papers/<p>/signatures.json)."""
DIRS = ('up', 'down', 'none')

def validate(entries):
    errs = []
    for sid, e in entries.items():
        for k in ('mechanism', 'relation', 'source', 'predicts', 'prior_rank'):
            if k not in e: errs.append(f'{sid}: missing {k}')
        for obs, d in (e.get('predicts') or {}).items():
            if d not in DIRS: errs.append(f'{sid}: {obs} -> {d!r} not in {DIRS}')
        if not str(e.get('source', '')).strip(): errs.append(f'{sid}: empty source')
    return errs

def decidable(sa, sb, obs):
    """a comparison on observable obs separates two signatures when they predict opposite signs, or a change against no change."""
    a, b = sa['predicts'].get(obs), sb['predicts'].get(obs)
    if a is None or b is None or a == b: return False
    return {a, b} == {'up', 'down'} or 'none' in (a, b)

def winner_for(sa, sb, obs, observed):
    """observed in ('up', 'down') (|change| > 2u). Returns 'A', 'B' or 'neither' (neither prediction matches)."""
    a, b = sa['predicts'][obs], sb['predicts'][obs]
    if a == observed and b != observed: return 'A'
    if b == observed and a != observed: return 'B'
    return 'neither'

SYNTHETIC = {   # for unit tests only
    'syn_grain_growth': {'mechanism': 'grain growth during sintering', 'relation': 'd^n - d0^n = k t exp(-Q/RT)', 'source': 'Burke & Turnbull 1952',
                         'prior_rank': 1, 'predicts': {'grain_size(T up)': 'up', 'density(T up)': 'up', 'hardness(T up)': 'down'}},
    'syn_pinning': {'mechanism': 'Zener pinning by second-phase particles', 'relation': 'd_lim = 4r/(3f)', 'source': 'Smith (Zener) 1948',
                    'prior_rank': 2, 'predicts': {'grain_size(T up)': 'none', 'density(T up)': 'up', 'hardness(T up)': 'none'}},
}
