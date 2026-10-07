#!/usr/bin/env python3
"""separability_s.py: separability pilot (skill rule R6, v1.3 proposal R2) on the output of a VALIDATED reader.

usage: separability_s.py --table measurements.csv --reader-freeze LABEL [--order-by given|mean] [--bootstrap 2000]
                         [--unit-type specimen|track|cell|grain|field|tile|indent] [--out pilot.json] [--allow-unvalidated]

Input CSV columns: condition, unit, value, and optionally order (numeric position of the condition in its series) and sub
(sub-measurement id, for example a field inside a specimen). Rows with the same condition and unit average into one unit value,
so the replicate is always the unit, never the sub-measurement.

Outputs, per the rule:
  * per condition: n units, mean, SD, SE (bootstrap SE over sub-measurements when a condition has one unit)
  * adjacent pairs along the series: difference, combined SE, separated = |diff| > 2 combined SE,
    and the between-over-within ratio |diff| / sqrt((SD_a^2 + SD_b^2) / 2) used in the screens (target 2)
  * one-way ANOVA across conditions (F, p)
  * verdict: pass (every adjacent pair separates), partial (some do: merged classes are listed for T2 ambiguity), fail
  * unit_type field, grain, tile or indent inside one specimen measures spatial heterogeneity, not replicate specimens: the
    output flags such ratios as optimistic
The run refuses (verdict "deferred") when --reader-freeze names no entry in v4/FREEZE.md, unless --allow-unvalidated, which
marks the result exploratory and never counts for M0.
"""
import argparse
import collections
import csv
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE = os.path.join(os.path.dirname(HERE), 'FREEZE.md')
SPATIAL = {'field', 'grain', 'tile', 'indent', 'cell', 'pixel', 'bin'}


def frozen(label):
    """True only for a reader freeze (labels S4...) recorded in v4/FREEZE.md."""
    if not label or not re.match(r'^S4[A-Za-z0-9]*$', label) or not os.path.exists(FREEZE):
        return False
    return re.search(rf'^## {re.escape(label)} \(', open(FREEZE).read(), flags=re.M) is not None


def anova(groups):
    groups = [np.asarray(g, float) for g in groups if len(g) > 0]
    k, n = len(groups), sum(len(g) for g in groups)
    if k < 2 or n <= k:
        return None, None
    try:
        from scipy import stats  # noqa: PLC0415
        r = stats.f_oneway(*groups)
        return float(r.statistic), float(r.pvalue)
    except ImportError:
        grand = np.concatenate(groups).mean()
        ssb = sum(len(g) * (g.mean() - grand) ** 2 for g in groups)
        ssw = sum(((g - g.mean()) ** 2).sum() for g in groups)
        return float((ssb / (k - 1)) / (ssw / (n - k))) if ssw > 0 else math.inf, None


def boot_se(values, B, rng):
    v = np.asarray(values, float)
    if len(v) < 2:
        return None
    means = rng.choice(v, size=(B, len(v)), replace=True).mean(axis=1)
    return float(means.std(ddof=1))


def run(rows, order_by='given', B=2000, unit_type=None, seed=0):
    rng = np.random.default_rng(seed)
    per_unit = collections.defaultdict(list)
    subs = collections.defaultdict(list)
    order = {}
    for r in rows:
        c, u, v = r['condition'], r['unit'], float(r['value'])
        per_unit[(c, u)].append(v)
        subs[c].append(v)
        if r.get('order') not in (None, ''):
            order[c] = float(r['order'])
    units = collections.defaultdict(list)
    for (c, u), vals in per_unit.items():
        units[c].append(float(np.mean(vals)))
    summ = {}
    for c, vals in units.items():
        n = len(vals)
        sd = float(np.std(vals, ddof=1)) if n > 1 else None
        se = sd / math.sqrt(n) if sd is not None else boot_se(subs[c], B, rng)
        wsd = sd if sd is not None else (float(np.std(subs[c], ddof=1)) if len(subs[c]) > 1 else None)
        summ[c] = {'n_units': n, 'n_sub': len(subs[c]), 'mean': float(np.mean(vals)), 'sd': sd, 'se': se,
                   'se_source': 'units' if sd is not None else ('bootstrap over sub-measurements' if se is not None else 'none'),
                   'within_sd_for_ratio': wsd}
    if order_by == 'given':
        if len(order) != len(summ):
            raise ValueError(f'order missing for conditions {sorted(set(summ) - set(order))}: fill the order column or pass --order-by mean')
        seq = sorted(summ, key=lambda c: order[c])
    else:
        seq = sorted(summ, key=lambda c: summ[c]['mean'])
    pairs = []
    for a, b in zip(seq, seq[1:]):
        A, Bc = summ[a], summ[b]
        diff = Bc['mean'] - A['mean']
        cse = math.sqrt((A['se'] or 0) ** 2 + (Bc['se'] or 0) ** 2) if A['se'] is not None and Bc['se'] is not None else None
        pooled = math.sqrt(((A['within_sd_for_ratio'] or 0) ** 2 + (Bc['within_sd_for_ratio'] or 0) ** 2) / 2) \
            if A['within_sd_for_ratio'] is not None and Bc['within_sd_for_ratio'] is not None else None
        pairs.append({'a': a, 'b': b, 'diff': diff, 'combined_se': cse,
                      'separated': bool(cse is not None and abs(diff) > 2 * cse),
                      'between_over_within': abs(diff) / pooled if pooled else None})
    n_units = [len(units[c]) for c in seq]
    if all(n > 1 for n in n_units):
        F, p = anova([units[c] for c in seq])
        anova_basis = 'unit means'
    elif all(n == 1 for n in n_units):
        F, p = anova([subs[c] for c in seq])
        anova_basis = 'sub-measurements inside single units (pseudo-replicated: spatial, optimistic)'
    else:
        F, p, anova_basis = None, None, 'not run: some conditions have one unit and others several'
    sep = [x['separated'] for x in pairs]
    verdict = 'pass' if sep and all(sep) else ('partial' if any(sep) else 'fail')
    classes, cur = [], [seq[0]] if seq else []
    for x in pairs:
        if x['separated']:
            classes.append(cur)
            cur = [x['b']]
        else:
            cur.append(x['b'])
    if cur:
        classes.append(cur)
    ratios = [x['between_over_within'] for x in pairs if x['between_over_within'] is not None]
    spatial = (unit_type or '').lower() in SPATIAL or any(s['se_source'].startswith('bootstrap') for s in summ.values())
    return {'conditions': seq, 'ordered_by': order_by, 'summary': summ, 'adjacent_pairs': pairs, 'pairs_separated': sum(sep), 'pairs': len(pairs),
            'anova_F': F, 'anova_p': p, 'anova_basis': anova_basis, 'verdict': verdict, 'classes_for_T2': classes,
            'min_between_over_within': min(ratios) if ratios else None, 'unit_type': unit_type,
            'optimistic_spatial_units': spatial,
            'note': ('units are spatial (fields, grains, tiles or indents inside one specimen) or bootstrapped: the ratio measures '
                     'heterogeneity inside a specimen, not replicate specimens, so read it as optimistic') if spatial else None}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--table', required=True)
    ap.add_argument('--reader-freeze')
    ap.add_argument('--order-by', choices=['given', 'mean'], default='given')
    ap.add_argument('--bootstrap', type=int, default=2000)
    ap.add_argument('--unit-type')
    ap.add_argument('--out')
    ap.add_argument('--allow-unvalidated', action='store_true')
    a = ap.parse_args(argv)
    ok = frozen(a.reader_freeze)
    if not ok and not a.allow_unvalidated:
        res = {'verdict': 'deferred', 'why': f'reader freeze {a.reader_freeze!r} not found in {FREEZE}: run the pilot only on a validated, frozen reader'}
    else:
        rows = list(csv.DictReader(open(a.table)))
        try:
            res = run(rows, a.order_by, a.bootstrap, a.unit_type)
        except ValueError as e:
            sys.exit(f'STOP: {e}')
        res['reader_freeze'] = a.reader_freeze if ok else None
        res['exploratory'] = not ok
    res['table'] = os.path.abspath(a.table)
    out = a.out or os.path.splitext(a.table)[0] + '_separability.json'
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: res.get(k) for k in ('verdict', 'pairs_separated', 'pairs', 'anova_p', 'min_between_over_within', 'optimistic_spatial_units', 'exploratory', 'why')}, indent=0))
    sys.exit(0)


if __name__ == '__main__':
    main()
