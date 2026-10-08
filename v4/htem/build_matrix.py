#!/usr/bin/env python3
"""build_matrix.py (stages H2 to H4): run the frozen readers on every cached sample of the given libraries and write the experiment matrix
plus the held-out and replicate checks.

Outputs under $HTEM_HOST/matrix/<tag>/:
  cells.jsonl     one row per (library, position): D fields (recipe, position, xyz), M fields (cation fractions, thickness), our derived
                  observables (xrd peaks, Eg, Rs, resistivity) with the reader freeze label, and a modality summary
  heldout.json    our readers against the database's own A columns (opt_direct_bandgap, fpm_sheet_resistance): n, ratio or bias,
                  Spearman, and the gate result (config gates.heldout_spearman). A-level evidence: report the bias, never key on it.
  replicates.json second route (R8): for libraries with the same recipe key, positions paired one to one by full cation-fraction vector
                  (L-infinity within 0.02), Eg and strongest-peak position differences against their combined uncertainty
  skipped.json    samples or libraries that failed (404, error body, reader exception), with the reason
usage: build_matrix.py --tag <name> --freeze <label> <library_id> [<library_id> ...]
"""
import argparse, json, math, os, sys
import numpy as np
from scipy.stats import spearmanr
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import htem_api as API
import sample_io as SIO
import census as CEN
from readers import xrd as RX, optical as RO, fpm as RF, edge as RE

R = API.CFG['readers']


def row_for(lib, s, freeze):
    x = SIO.xrd(s)
    op = SIO.optical(s)
    t = SIO.thickness_um(s)
    comp = SIO.composition(s)
    xr = RX.read(x['two_theta'], x['intensity'], R['xrd']) if x else None
    ob = RO.read(op, t, R['optical']) if op else None
    fp = RF.read(SIO.fpm(s), t, R['fpm']) if SIO.fpm(s) else None
    ed = RE.read(op, t, R['optical']) if op else None   # round 2: E04, E_U, edge width (readers S4ho2, S4hu)
    rk = CEN.recipe_key(lib, API.CFG['census']['temp_round_c'])
    return {'entity': f"{lib['id']}:{s.get('position')}", 'library': lib['id'], 'sample': s.get('id'), 'position': s.get('position'),
            'xyz_mm': SIO.xyz(s), 'system': SIO.system_key(lib.get('elements')), 'recipe': list(rk),
            'D': {'temp_c': rk[1], 'target_powers': [list(p) if isinstance(p, tuple) else p for p in rk[2]],
                  'gas_flows': [list(g) if isinstance(g, tuple) else g for g in rk[3]], 'pressure_mtorr': rk[4], 'time_min': rk[5],
                  'substrate': rk[6]},
            'M': {'cation_frac': comp, 'anion_frac': SIO.anion_fraction(s), 'thickness_um': t},
            'derived': {'freeze': freeze,
                        'xrd_peaks': None if xr is None else xr['peaks'], 'xrd_noise': None if xr is None else xr['noise'],
                        'Eg_eV': None if ob is None else ob.get('Eg'), 'Eg_err': None if ob is None else ob.get('Eg_err'),
                        'Eg_censored': None if ob is None else ob.get('censored'),
                        'Rs_ohm_sq': None if fp is None else fp.get('Rs_ohm_sq'), 'Rs_r2': None if fp is None else fp.get('linear_r2'),
                        'resistivity_ohm_cm': None if fp is None else fp.get('resistivity_ohm_cm'),
                        'E04_eV': None if ed is None else ed['E04'], 'E04_censored': None if ed is None else ed['E04_censored'],
                        'E04_dthick': None if ed is None else ed['E04_dthick'], 'E_U_eV': None if ed is None else ed['E_U'],
                        'E_U_dthick_rel': None if ed is None else ed['E_U_dthick_rel'], 'edge_width_eV': None if ed is None else ed['edge_width'],
                        'run_E': None if ed is None else ed['run_E']},
            'A': SIO.a_level(s), 'modalities': SIO.summary(s)}


def _fin(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def heldout(rows):
    out = {}
    pairs = [(r['derived']['Eg_eV'], r['A'].get('opt_direct_bandgap')) for r in rows
             if _fin(r['derived']['Eg_eV']) and not r['derived']['Eg_censored'] and _fin(r['A'].get('opt_direct_bandgap'))]
    if len(pairs) >= 5:
        a, b = np.array(pairs).T
        out['Eg'] = {'n': len(pairs), 'bias_eV': float(np.median(a - b)), 'sd_eV': float(np.std(a - b)),
                     'spearman': float(spearmanr(a, b).correlation)}
    pairs = [(r['derived']['Rs_ohm_sq'], r['A'].get('fpm_sheet_resistance')) for r in rows
             if _fin(r['derived']['Rs_ohm_sq']) and r['derived']['Rs_ohm_sq'] > 0
             and _fin(r['A'].get('fpm_sheet_resistance')) and r['A']['fpm_sheet_resistance'] > 0]
    if len(pairs) >= 5:
        a, b = np.array(pairs).T
        out['Rs'] = {'n': len(pairs), 'median_ratio': float(np.median(a / b)), 'log_sd': float(np.std(np.log10(a / b))),
                     'spearman': float(spearmanr(a, b).correlation)}
    pairs = [(r['derived'].get('E04_eV'), r['A'].get('opt_direct_bandgap')) for r in rows
             if _fin(r['derived'].get('E04_eV')) and _fin(r['A'].get('opt_direct_bandgap'))]
    if len(pairs) >= 5:   # round 2: different quantities, rank gate only; bias reported
        a, b = np.array(pairs).T
        out['E04'] = {'n': len(pairs), 'bias_eV': float(np.median(a - b)), 'sd_eV': float(np.std(a - b)), 'spearman': float(spearmanr(a, b).correlation)}
    g = API.CFG['gates']['heldout_spearman']
    for k in out:
        out[k]['pass'] = bool(out[k]['spearman'] >= g)
    return out


def _linf(a, b):
    return max(abs(a.get(e, 0.0) - b.get(e, 0.0)) for e in set(a) | set(b))


def replicates(rows, tol=0.02):
    """Second route (R8). Libraries with the same recipe key are compared once per library pair. Positions are matched one to one,
    greedily by the smallest L-infinity distance between full cation-fraction vectors, and only within tol."""
    by_recipe = {}
    for r in rows:
        if r['D']['temp_c'] is None or not r['D']['target_powers'] or not r['M']['cation_frac']:
            continue
        by_recipe.setdefault(json.dumps(r['recipe']), {}).setdefault(r['library'], []).append(r)
    out = []
    for rk in sorted(by_recipe):
        libs = by_recipe[rk]
        ids = sorted(libs)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                A, B = libs[ids[i]], libs[ids[j]]
                cand = sorted((_linf(a['M']['cation_frac'], b['M']['cation_frac']), ia, ib)
                              for ia, a in enumerate(A) for ib, b in enumerate(B))
                used_a, used_b = set(), set()
                for d, ia, ib in cand:
                    if d > tol:
                        break
                    if ia in used_a or ib in used_b:
                        continue
                    used_a.add(ia); used_b.add(ib)
                    a, b = A[ia], B[ib]
                    da, db = a['derived'], b['derived']
                    rec = {'pair': [a['entity'], b['entity']], 'dfrac_linf': d}
                    if _fin(da['Eg_eV']) and _fin(db['Eg_eV']) and not da['Eg_censored'] and not db['Eg_censored']:
                        u = math.hypot(da['Eg_err'] or 0, db['Eg_err'] or 0)
                        rec['dEg'] = da['Eg_eV'] - db['Eg_eV']
                        rec['dEg_over_u'] = None if u == 0 else abs(rec['dEg']) / u
                    if _fin(da.get('E04_eV')) and _fin(db.get('E04_eV')):
                        rec['dE04'] = da['E04_eV'] - db['E04_eV']
                    if _fin(da.get('E_U_eV')) and _fin(db.get('E_U_eV')):
                        rec['dEU_rel'] = abs(da['E_U_eV'] - db['E_U_eV']) / ((da['E_U_eV'] + db['E_U_eV']) / 2)
                    if da['xrd_peaks'] and db['xrd_peaks']:
                        pa = max(da['xrd_peaks'], key=lambda p: p['height'])
                        pb = min(db['xrd_peaks'], key=lambda p: abs(p['center'] - pa['center']))
                        rec['dpeak_deg'] = pa['center'] - pb['center']
                    out.append(rec)
    eg = [abs(r['dEg']) for r in out if 'dEg' in r]
    pk = [abs(r['dpeak_deg']) for r in out if 'dpeak_deg' in r and abs(r['dpeak_deg']) < 0.5]
    e4 = [abs(r['dE04']) for r in out if 'dE04' in r]; eu = [r['dEU_rel'] for r in out if 'dEU_rel' in r]
    return {'pairs': len(out), 'median_abs_dEg_eV': float(np.median(eg)) if eg else None,
            'n_dE04': len(e4), 'median_abs_dE04_eV': float(np.median(e4)) if e4 else None, 'n_dEU': len(eu), 'median_rel_dEU': float(np.median(eu)) if eu else None,
            'median_abs_dpeak_deg': float(np.median(pk)) if pk else None, 'rows': out}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--freeze', required=True, help='reader freeze label in v4/FREEZE.md, e.g. S4h (separability_s.py accepts S4* only)')
    ap.add_argument('libs', nargs='+')
    a = ap.parse_args(argv)
    c = API.Client()
    out = os.path.join(API.HOST, 'matrix', a.tag)
    os.makedirs(out, exist_ok=True)
    rows, skipped = [], []
    for lid in a.libs:
        try:
            lib = c.library(lid)
        except API.HTEMError as e:
            skipped.append({'library': lid, 'error': str(e)})
            continue
        for s in c.samples_of(lid, skipped):
            try:
                rows.append(row_for(lib, s, a.freeze))
            except Exception as e:  # noqa: BLE001  one bad sample must not cost the run; it is logged
                skipped.append({'library': lid, 'sample': s.get('id'), 'error': f'{type(e).__name__}: {e}'})
    rows.sort(key=lambda r: (r['library'], r['position'] if r['position'] is not None else -1))
    with open(os.path.join(out, 'cells.jsonl'), 'w') as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True, default=float) + '\n')
    h = heldout(rows)
    rep = replicates(rows)
    json.dump(h, open(os.path.join(out, 'heldout.json'), 'w'), indent=1)
    json.dump(rep, open(os.path.join(out, 'replicates.json'), 'w'), indent=1, default=float)
    json.dump(skipped, open(os.path.join(out, 'skipped.json'), 'w'), indent=1)
    print(json.dumps({'cells': len(rows), 'heldout': h, 'replicate_pairs': rep['pairs'], 'median_abs_dEg_eV': rep['median_abs_dEg_eV'],
                      'median_abs_dpeak_deg': rep['median_abs_dpeak_deg'], 'median_abs_dE04_eV': rep['median_abs_dE04_eV'], 'median_rel_dEU': rep['median_rel_dEU'], 'skipped': len(skipped),
                      'requests': c.n_requests}, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
