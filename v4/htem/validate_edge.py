#!/usr/bin/env python3
"""validate_edge.py (round 2, HR1): synthetic gates for readers S4ho2 (E04) and S4hu (E_U) on FRESH seeds (HTEM_ROUND2_RULES 9).
Generator: synth.optical_spectra with the dev-library ranges of HTEM_ROLE (config synth.<role>: opt_eg, opt_A, opt_R, noise) and the
pre-registered E_U 0.03-0.30 eV and d 0.1-0.6 um, fringes on (saturation arises where T < t_min). Truth E04: first energy where the
model alpha reaches 1e4 cm^-1 on a 20000-point grid over the measured range (None when it never does). Truth E_U: the model tail energy.
Seeds: FRESH_BASE + 0..99 (gates on all 100: E04 within 0.03 eV on >= 90 % of uncensored reads with bias SD <= 0.02 eV, E_U within 15 %
on >= 90 % of resolved reads); censor set: FRESH_BASE + 100..119 with Eg drawn above the measured range (truth never reaches 1e4):
every one must be flagged censored. Writes $HTEM_HOST/validation/edge_<role>.json. usage: HTEM_ROLE=P1 validate_edge.py"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import synth as SY, htem_api as API
from readers import edge as RE
FRESH_BASE = 731100
role = os.environ.get('HTEM_ROLE', '?'); cfg = dict(API.CFG['readers']['optical'], edge_inversion='incoherent')
SY.P = dict(SY.P, opt_Eu=(0.03, 0.30), opt_thick_um=(0.1, 0.6))
E = SY.HC / SY.OPT_GRID; Ef = np.linspace(E.min(), E.max(), 20000)


def model_alpha(seed, eg_override=None):
    r = np.random.default_rng(seed)
    eg = float(eg_override) if eg_override is not None else float(r.uniform(*SY._r('opt_eg', (1.6, 3.6))))   # same draw order as synth
    d = r.uniform(*SY._r('opt_thick_um', (0.15, 0.6)))
    A = np.exp(r.uniform(*np.log(SY._r('opt_A', (1.5e5, 6e5))))); eu = r.uniform(*SY._r('opt_Eu', (0.03, 0.08)))
    al = np.where(Ef > eg, np.maximum(A * np.sqrt(np.clip(Ef - eg, 0, None)) / Ef, A * np.sqrt(eu / 2) / eg), A * np.sqrt(eu / 2) / eg * np.exp((Ef - eg) / eu))
    k = np.flatnonzero(al >= 1e4)
    return (float(Ef[k[0]]) if k.size else None), eu, d


def main():
    rows = []
    for i in range(100):
        sd = FRESH_BASE + i; op, tr = SY.optical_spectra(sd); t04, eu, d = model_alpha(sd)
        r = RE.read(op, tr['thickness_um'], cfg)
        rows.append({'seed': sd, 'E04_true': t04, 'E04': r['E04'], 'censored': r['E04_censored'], 'EU_true': eu, 'EU': r['E_U']})
    cen = []
    for i in range(100, 120):
        sd = FRESH_BASE + i; eg_hi = float(np.random.default_rng(sd + 7).uniform(E.max() + 0.3, E.max() + 1.0))
        op, tr = SY.optical_spectra(sd, eg=eg_hi); t04, _, _ = model_alpha(sd, eg_override=eg_hi)
        r = RE.read(op, tr['thickness_um'], cfg); cen.append({'seed': sd, 'Eg': eg_hi, 'E04_true': t04, 'flagged': bool(r['E04_censored'])})
    e = np.array([x['E04'] - x['E04_true'] for x in rows if x['E04'] is not None and x['E04_true'] is not None])
    u = np.array([x['EU'] / x['EU_true'] - 1 for x in rows if x['EU']])
    g = {'role': role, 'fresh_base': FRESH_BASE, 'n_seeds': len(rows),
         'E04': {'n_read': int(e.size), 'within_0.03': float(np.mean(np.abs(e) <= 0.03)) if e.size else 0.0, 'bias': float(e.mean()) if e.size else None,
                 'bias_sd': float(e.std()) if e.size else None},
         'censor': {'n': len(cen), 'n_truth_none': sum(c['E04_true'] is None for c in cen), 'flagged': sum(c['flagged'] for c in cen if c['E04_true'] is None)},
         'E_U': {'n_read': int(u.size), 'within_15pct': float(np.mean(np.abs(u) <= 0.15)) if u.size else 0.0, 'median_rel_err': float(np.median(u)) if u.size else None}}
    g['E04']['pass'] = bool(e.size >= 50 and g['E04']['within_0.03'] >= 0.9 and g['E04']['bias_sd'] <= 0.02)
    g['censor']['pass'] = g['censor']['n_truth_none'] > 0 and g['censor']['flagged'] == g['censor']['n_truth_none']   # HR0 9: every truth-censored seed flagged
    g['E_U']['pass'] = bool(u.size >= 50 and g['E_U']['within_15pct'] >= 0.9)
    g['S4ho2_pass'] = g['E04']['pass'] and g['censor']['pass']; g['S4hu_pass'] = g['E_U']['pass']
    os.makedirs(os.path.join(API.HOST, 'validation'), exist_ok=True)
    json.dump({'gates': g, 'rows': rows, 'censor_rows': cen}, open(os.path.join(API.HOST, 'validation', f'edge_{role}.json'), 'w'), indent=1)
    print(json.dumps(g, indent=1))


if __name__ == '__main__':
    main()
