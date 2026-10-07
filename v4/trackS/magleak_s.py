#!/usr/bin/env python3
"""magleak_s.py: magnification leak test (Track S, the UHCSDB lesson: magnification tracked annealing time, Spearman -0.32).

usage: magleak_s.py --dataset ID [--root DIR] [--roles sem_image sem_montage_tile] [--rules joinrules/ID.json]

Reads join.csv (role, condition fields, pixel size from native tags) and tests, for every condition field, whether the
image scale follows the condition:
  constant     every SEM image has the same pixel size (within 0.5 %)                         -> PASS
  independent  numeric or ordered field: |Spearman rho| < 0.1 or p >= 0.05; categorical field:
               Kruskal-Wallis p >= 0.05 and group medians within 0.5 %                          -> PASS (note)
  leak         otherwise                                                                        -> FAIL: resample every image to one
                                                                                                   pixel size before any measurement,
                                                                                                   and keep magnification out of T2 panels
  missing      some SEM images lack a native pixel size                                         -> CHECK: list them (a validated
                                                                                                   scale-bar reader or exclusion follows)
The same test runs on the horizontal field width when the tags carry it. Writes <root>/<ID>/magleak.json.
"""
import argparse
import collections
import csv
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
HARBOR = os.environ.get('HARBOR', '/home/aid1/Documents/harbor')
ROOT_DEFAULT = os.path.join(HARBOR, 'v4_host/trackS')
TOL = 0.005


def _rank(x):
    order = np.argsort(x, kind='mergesort')
    ranks = np.empty(len(x), float)
    ranks[order] = np.arange(len(x))
    xs = np.asarray(x)[order]
    i = 0
    while i < len(xs):  # average ties
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2
        i = j + 1
    return ranks


def spearman(x, y):
    try:
        from scipy import stats  # noqa: PLC0415
        r = stats.spearmanr(x, y)
        return float(r.statistic if hasattr(r, 'statistic') else r[0]), float(r.pvalue if hasattr(r, 'pvalue') else r[1])
    except ImportError:
        rx, ry = _rank(np.asarray(x, float)), _rank(np.asarray(y, float))
        rho = float(np.corrcoef(rx, ry)[0, 1])
        return rho, None


def kruskal(groups):
    if len({x for g in groups for x in g}) < 2:  # all values identical
        return 1.0
    try:
        from scipy import stats  # noqa: PLC0415
        return float(stats.kruskal(*groups).pvalue)
    except ImportError:
        return None
    except ValueError:
        return 1.0


def test_field(vals, scale, field, order=None):
    """vals: condition values (str), scale: floats. Returns a verdict dict.
    Ordered or numeric fields get Spearman (monotone trend) and Kruskal-Wallis (any shape, for example U shaped). Categorical
    fields get Kruskal-Wallis. A leak needs a significant test and a real scale difference between level medians (over 5 %),
    or a strong rank correlation with that difference on few images."""
    if len(set(vals)) < 2:
        return {'field': field, 'verdict': 'single_level', 'levels': len(set(vals))}
    per = collections.defaultdict(list)
    for v, s in zip(vals, scale):
        per[v].append(s)
    medians = {k: float(np.median(v)) for k, v in per.items()}
    rel = (max(medians.values()) - min(medians.values())) / max(min(medians.values()), 1e-12)
    base = {'field': field, 'group_medians': medians, 'median_spread_rel': rel}
    if len(set(scale)) < 2 or rel <= TOL:
        return dict(base, kind='any', verdict='independent', note='one scale across levels')
    kw = kruskal(list(per.values()))
    kw_leak = kw is not None and kw < 0.05 and rel > 0.05
    rank_of = {str(k): i for i, k in enumerate(order)} if order else None
    unordered = sorted(v for v in per if rank_of is not None and v not in rank_of)
    numeric = all(_isnum(v) for v in per)
    if (rank_of and not unordered) or (not rank_of and numeric):
        xv = [rank_of[v] if rank_of else float(v) for v in vals]
        rho, p = spearman(xv, scale)
        sp_leak = (abs(rho) >= 0.1 and p is not None and p < 0.05 and rel > 0.05) or (abs(rho) >= 0.3 and rel > 0.05)
        return dict(base, kind='ordered' if rank_of else 'numeric', spearman_rho=rho, p=p, kruskal_p=kw,
                    verdict='leak' if (sp_leak or kw_leak) else 'independent')
    return dict(base, kind='categorical', kruskal_p=kw, unordered_levels=unordered or None,
                verdict='leak' if kw_leak or (kw is None and rel > 0.05) else 'independent')


def _isnum(v):
    try:
        float(v)
        return True
    except (TypeError, ValueError):
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dataset', required=True)
    ap.add_argument('--root', default=ROOT_DEFAULT)
    ap.add_argument('--roles', nargs='*', default=['sem_image', 'sem_montage_tile'])
    ap.add_argument('--rules')
    a = ap.parse_args(argv)
    spec = json.load(open(a.rules or os.path.join(HERE, 'joinrules', f'{a.dataset}.json')))
    rows = list(csv.DictReader(open(os.path.join(a.root, a.dataset, 'join.csv'))))
    sem = [r for r in rows if r['role'] in a.roles]
    out = {'dataset': a.dataset, 'roles': a.roles, 'sem_images': len(sem), 'fields': []}
    if not sem:
        out['verdict'] = 'no_sem_images'
        print('no SEM images under the given roles: check the join rules')
    else:
        trusted = lambda r: r.get('pixel_size_nm') not in (None, '') and r.get('pixel_size_source') not in (None, '', 'none', 'resolution_tag')
        have = [r for r in sem if trusted(r)]
        missing = [r['path'] for r in sem if not trusted(r)]  # resolution tags (dpi of an export) never count as a scale
        out['with_native_pixel_size'] = len(have)
        out['missing_pixel_size'] = missing[:200]
        out['missing_count'] = len(missing)
        ps = np.array([float(r['pixel_size_nm']) for r in have]) if have else np.array([])
        out['pixel_size_nm'] = {'min': float(ps.min()), 'max': float(ps.max()), 'distinct': sorted({round(x, 4) for x in ps})[:50]} if len(ps) else None
        constant = len(ps) > 0 and (ps.max() - ps.min()) / ps.min() <= TOL
        verdicts = []
        for cf in spec.get('condition_fields', []):
            sub = [r for r in have if r.get(cf) not in (None, '')]
            if not sub:
                out['fields'].append({'field': cf, 'verdict': 'no_values'})
                continue
            res = test_field([r[cf] for r in sub], [float(r['pixel_size_nm']) for r in sub], cf, (spec.get('order') or {}).get(cf))
            hfw = [(r[cf], float(r['hfw_um'])) for r in sub if r.get('hfw_um') not in (None, '')]
            if len(hfw) == len(sub):
                res['hfw'] = test_field([v for v, _ in hfw], [s for _, s in hfw], cf, (spec.get('order') or {}).get(cf))
            out['fields'].append(res)
            verdicts.append(res['verdict'])
        if not have:
            out['verdict'] = 'missing'
        elif constant:
            out['verdict'] = 'constant'
        elif 'leak' in verdicts:
            out['verdict'] = 'leak'
        elif 'independent' in verdicts:
            out['verdict'] = 'independent'
        else:
            out['verdict'] = 'untested'  # pixel size varies and no condition field could be tested
        if missing and out['verdict'] != 'missing':
            out['verdict'] += '+missing'
        out['action'] = {
            'constant': 'PASS: one pixel size for every SEM image',
            'independent': 'PASS: pixel size varies but does not follow any condition; still resample before cross-image measurements',
            'leak': 'FAIL: resample every image to one pixel size before measurement, and keep magnification and scale bars out of T2 panels',
            'missing': 'CHECK: no SEM image carries a native pixel size, so no leak test is possible yet',
            'untested': 'CHECK: pixel size varies, but no condition field carries values on the SEM images: fill the join rules',
        }[out['verdict'].split('+')[0]] + (' | CHECK: images without native pixel size need a validated scale-bar reader or exclusion' if missing else '')
    json.dump(out, open(os.path.join(a.root, a.dataset, 'magleak.json'), 'w'), indent=1)
    print(json.dumps({k: out.get(k) for k in ('dataset', 'sem_images', 'with_native_pixel_size', 'missing_count', 'verdict', 'action')}, indent=0))
    for f in out['fields']:
        print('  ', {k: f.get(k) for k in ('field', 'kind', 'verdict', 'spearman_rho', 'p', 'kruskal_p', 'median_spread_rel')})


if __name__ == '__main__':
    main()
