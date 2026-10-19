"""Physics and fallback world for server8 (graph I). Truth lives only here and in the server process.

Dependency note: Track 2 writes v8/world/*.py (sampler, render, lattice, cost, fit, simulate). This module imports none of them at
import time; backend() tries them lazily and only reports availability. The scans below are a self-contained statistical stand-in
that returns per-rod angles, not images, so the server runs without Track 2. When the real renderer lands, replace afm()/lattice().

World file (JSON, ~/v8_state/server8/worlds/<world_id>.json), written by the parent, never shown to the agent:
  world_id, key (SUPPORTED|REFUTED), claim, sample_text, sequence,
  truth: azimuth_deg (0..360, hidden), rod_rel_deg (rod angle relative to the lattice), dir_sd_deg (scatter about each lattice
         direction), iso_frac, rod_density_per_um2, meas_sd_deg, drift_bias_deg, lattice_sd_deg
  fm:    registry_angles {name: deg}, energies {name: eV}, stated_error_eV, (optional) structure {...}
A world id of the form demo_A_<seed> or demo_B_<seed> is generated on the fly (tests only).
"""
import json
import math
import os
import re

import numpy as np
from scipy.special import i0, i1

PERIOD = 60.0
PHI = 360.0 / PERIOD          # angle times PHI maps the 60 degree period onto the circle


def backend():
    """Lazy, defensive look for Track 2's modules. Returns the names importable, never raises."""
    found = []
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    import importlib.util
    for n in ('sampler', 'render', 'lattice', 'cost', 'fit', 'simulate'):
        try:
            if os.path.exists(os.path.join(here, 'world', n + '.py')):
                found.append(n)
        except Exception:
            pass
    return found


SEQ_DEMO = ('GSDEEKLKELAEKAIELLKRAGDPEAAKELVRLAEEILKRHPNDPELLKRILELAHEA' * 1)
SAMPLE_TEXT = ('Sample HRm-{h}: a self-assembled protein rod array deposited on a cleaved crystal surface (a layered silicate with a '
               'hexagonal surface cation sublattice) in 100 mM salt solution, imaged by AFM. The rods are built from a repeat unit '
               'of 50 residues, {rep} repeats long. One repeat reads {seq}. The orientation of the sample on the scanner is not '
               'known.')


def demo_world(world_id):
    m = re.fullmatch(r'demo_([AB])_(\d+)', world_id)
    if not m:
        return None
    ab, seed = m.group(1), int(m.group(2))
    rng = np.random.default_rng(seed)
    theta = float(rng.uniform(0, 60))
    return {
        'world_id': world_id, 'key': 'SUPPORTED' if ab == 'A' else 'REFUTED',
        'claim': 'The protein rods on this surface lie in the registry that the acidic-residue array of the protein matches to the surface cation sublattice.',
        'sample_text': SAMPLE_TEXT.format(h='ea', rep=18, seq=SEQ_DEMO), 'sequence': SEQ_DEMO,
        'truth': {'azimuth_deg': float(rng.uniform(0, 360)), 'rod_rel_deg': theta + (0 if ab == 'A' else 30.0),
                  'dir_sd_deg': 7.0, 'iso_frac': 0.06, 'rod_density_per_um2': 35.0, 'meas_sd_deg': 4.0,
                  'drift_bias_deg': float(rng.normal(0, 1.0)), 'lattice_sd_deg': 3.5},
        'fm': {'registry_angles': {'row_1': theta, 'row_2': theta + 30.0}, 'energies': {'row_1': -1.10, 'row_2': -0.70},
               'stated_error_eV': 0.1},
    }


def load_world(state_dir, world_id):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', world_id):
        raise ValueError('bad world id')
    p = os.path.join(state_dir, 'worlds', world_id + '.json')
    if os.path.exists(p):
        return json.load(open(p))
    w = demo_world(world_id)
    if w is None:
        raise KeyError(f'unknown world {world_id}')
    return w


# ---------------------------------------------------------------- statistics
def vm_kappa(R):
    """Inverse of A(k) = I1/I0 (Best-Fisher approximation)."""
    R = min(max(R, 0.0), 0.995)
    if R < 0.53:
        return 2 * R + R ** 3 + 5 * R ** 5 / 6
    if R < 0.85:
        return -0.4 + 1.39 * R + 0.43 / (1 - R)
    return 1 / (R ** 3 - 4 * R ** 2 + 3 * R)


def log_i0(k):
    return float(np.log(i0(k))) if k < 500 else k - 0.5 * math.log(2 * math.pi * k)


def wrapped_sd(deg_sd):
    """concentration of the 60-periodic phase for a Gaussian scatter of deg_sd degrees about each lattice direction"""
    s = math.radians(deg_sd * PHI)
    return vm_kappa(math.exp(-0.5 * s * s))


def D_from(N, kappa, R):
    """Twice the log likelihood ratio of the fitted phase against the phase shifted by half a period and against isotropic."""
    if N <= 0 or R <= 0:
        return 0.0
    ll_fit_shift = 2 * N * kappa * R
    ll_fit_iso = N * (kappa * R - log_i0(kappa))
    return float(2 * min(ll_fit_shift, ll_fit_iso))


def lattice_sd(px, sec, base):
    return base * math.sqrt(128.0 / px) * math.sqrt(2.0 / max(sec, 0.1))


def p_detect(size_nm, px):
    nm_px = size_nm / px
    return 0.98 if nm_px <= 6 else float(min(1.0, max(0.0, 1.2 - 0.12 * nm_px)))


def rod_sd(base, sec):
    return base * math.sqrt(2.0 / max(sec, 0.1))


# ---------------------------------------------------------------- costs (scan minutes)
AFM_SIZE = (100, 2000)
AFM_PX = (128, 1024)
AFM_SEC = (0.5, 8.0)
LAT_SIZE = (4, 60)
LAT_PX = (128, 512)
LAT_SEC = (0.5, 8.0)


def afm_cost(px, sec):
    return round(px * sec / 60.0 + 5.0, 3)


def lat_cost(px, sec):
    return round(px * sec * 1.5 / 60.0 + 5.0, 3)


def check_afm(a):
    s, px, sec = float(a.get('size_nm', 500)), int(a.get('px', 256)), float(a.get('sec_per_line', 2.0))
    if not (AFM_SIZE[0] <= s <= AFM_SIZE[1] and AFM_PX[0] <= px <= AFM_PX[1] and AFM_SEC[0] <= sec <= AFM_SEC[1]):
        raise ValueError(f'afm_scan limits: size_nm {AFM_SIZE}, px {AFM_PX}, sec_per_line {AFM_SEC}')
    return s, px, sec


def check_lat(a):
    s, px, sec = float(a.get('size_nm', 20)), int(a.get('px', 256)), float(a.get('sec_per_line', 2.0))
    if not (LAT_SIZE[0] <= s <= LAT_SIZE[1] and LAT_PX[0] <= px <= LAT_PX[1] and LAT_SEC[0] <= sec <= LAT_SEC[1]):
        raise ValueError(f'lattice_scan limits: size_nm {LAT_SIZE}, px {LAT_PX}, sec_per_line {LAT_SEC}')
    return s, px, sec


# ---------------------------------------------------------------- scans (truth side)
def afm(world, size_nm, px, sec, rng):
    t = world['truth']
    area_um2 = (size_nm / 1000.0) ** 2
    n = int(rng.poisson(t['rod_density_per_um2'] * area_um2 * p_detect(size_nm, px)))
    sd_dir = t['dir_sd_deg']
    sd_m = rod_sd(t['meas_sd_deg'], sec)
    rods = []
    for _ in range(n):
        if rng.random() < t['iso_frac']:
            a = rng.uniform(0, 180)
        else:
            k = int(rng.integers(0, 3))
            a = t['azimuth_deg'] + t['rod_rel_deg'] + 60.0 * k + rng.normal(0, sd_dir)
        a = (a + t['drift_bias_deg'] + rng.normal(0, sd_m)) % 180.0
        rods.append({'x_nm': round(float(rng.uniform(0, size_nm)), 1), 'y_nm': round(float(rng.uniform(0, size_nm)), 1),
                     'angle_deg': round(float(a), 2)})
    return {'kind': 'afm', 'size_nm': size_nm, 'px': px, 'sec_per_line': sec, 'n_rods': n, 'rods': rods}


def lattice(world, size_nm, px, sec, rng):
    t = world['truth']
    sd = lattice_sd(px, sec, t['lattice_sd_deg'])
    est = (t['azimuth_deg'] + t['drift_bias_deg'] * 0.0 + rng.normal(0, sd)) % PERIOD
    return {'kind': 'lattice', 'size_nm': size_nm, 'px': px, 'sec_per_line': sec, 'azimuth_deg_mod60': round(float(est), 2),
            'se_deg': round(float(sd), 2)}


# ---------------------------------------------------------------- fit (agent-visible data only)
def circ_mean(angles_deg, w=None):
    a = np.radians(np.asarray(angles_deg, float) * PHI)
    w = np.ones_like(a) if w is None else np.asarray(w, float)
    c, s = (w * np.cos(a)).sum(), (w * np.sin(a)).sum()
    R = math.hypot(c, s) / w.sum()
    return (math.degrees(math.atan2(s, c)) / PHI) % PERIOD, R


def fit(meas_list):
    """Fit the rod angle relative to the lattice on all given measurements. No lattice scan: angle undefined."""
    rods, lats = [], []
    for m in meas_list:
        if m['kind'] == 'afm':
            rods += [r['angle_deg'] for r in m['rods']]
        elif m['kind'] == 'lattice':
            lats.append((m['azimuth_deg_mod60'], m['se_deg']))
    N = len(rods)
    base = {'n_rods': N, 'n_lattice_scans': len(lats)}
    if not lats:
        return dict(base, phase=None, angle_rel_deg=None, angle_se_deg=None, runner_up=None, D=0.0,
                    note='no lattice scan: the angle relative to the lattice is not defined')
    if N < 3:
        return dict(base, phase=None, angle_rel_deg=None, angle_se_deg=None, runner_up=None, D=0.0, note='fewer than 3 rods')
    az, _ = circ_mean([a for a, _ in lats], [1.0 / s ** 2 for _, s in lats])
    se_lat = 1.0 / math.sqrt(sum(1.0 / s ** 2 for _, s in lats))
    rel = [(a - az) % PERIOD for a in rods]
    mu, R = circ_mean(rel)
    kappa = vm_kappa(R)
    R_eff = R * math.exp(-0.5 * math.radians(se_lat * PHI) ** 2)
    D = D_from(N, kappa, R_eff)
    se_stat = 1.0 / (PHI * math.sqrt(max(N * kappa * max(R, 1e-3), 1e-6))) * (180 / math.pi)
    se = math.hypot(se_stat, se_lat)
    return dict(base, phase=str(round(mu)), angle_rel_deg=round(mu, 2), angle_se_deg=round(se, 2),
                runner_up=str(round((mu + 30) % PERIOD)), D=round(D, 2), lattice_azimuth_deg_mod60=round(az, 2),
                lattice_se_deg=round(se_lat, 2), concentration=round(kappa, 3))


# ---------------------------------------------------------------- simulate (agent-side model built from observables)
def simulate(m0, plan, budget_left):
    """Expected counts, expected D and cost of a plan, from what the free scan shows (density, concentration)."""
    rods0 = [r['angle_deg'] for r in m0['rods']]
    area0 = (m0['size_nm'] / 1000.0) ** 2
    dens = m0['n_rods'] / max(area0 * p_detect(m0['size_nm'], m0['px']), 1e-9)
    _, R0 = circ_mean(rods0) if len(rods0) >= 3 else (0.0, 0.0)
    kappa = vm_kappa(R0)
    items, N, cost, lat_w = [], m0['n_rods'], 0.0, 0.0
    for p in plan:
        k = p.get('kind')
        if k == 'afm_scan':
            s, px, sec = check_afm(p)
            n = dens * (s / 1000.0) ** 2 * p_detect(s, px)
            N += n
            c = afm_cost(px, sec)
            items.append({'kind': k, 'expected_rods': round(n, 1), 'cost_min': c})
        elif k == 'lattice_scan':
            s, px, sec = check_lat(p)
            lat_w += 1.0 / lattice_sd(px, sec, 3.5) ** 2          # agent's own prior on the lattice-scan error (manual)
            c = lat_cost(px, sec)
            items.append({'kind': k, 'cost_min': c})
        else:
            raise ValueError('plan items are afm_scan or lattice_scan')
        cost += c
    if lat_w == 0:
        D, se_lat = 0.0, None
    else:
        se_lat = 1.0 / math.sqrt(lat_w)
        D = D_from(N, kappa, R0 * math.exp(-0.5 * math.radians(se_lat * PHI) ** 2))
    return {'items': items, 'expected_rods_total': round(N, 1), 'estimated_density_per_um2': round(dens, 1),
            'estimated_concentration': round(kappa, 3), 'predicted_lattice_se_deg': None if se_lat is None else round(se_lat, 2),
            'predicted_D': round(D, 1), 'predicted_cost_min': round(cost, 2), 'within_budget': cost <= budget_left,
            'note': 'predicted_D is 0 without a lattice scan in the plan' if lat_w == 0 else ''}


# ---------------------------------------------------------------- FM stand-ins (protein FM, materials FM)
def structure_from_sequence(seq):
    """Carboxylate geometry of a helical repeat from the sequence: aspartate and glutamate carboxylates at an axial rise of
    1.5 A per residue, 100 degrees per residue, radius 4.5 A. A stand-in used when the world file carries no structure."""
    pos = []
    for i, aa in enumerate(seq):
        if aa in 'DE':
            ph = math.radians(100.0 * i)
            pos.append({'residue': i + 1, 'aa': aa, 'axial_A': round(1.5 * i, 2), 'x_A': round(4.5 * math.cos(ph), 2),
                        'y_A': round(4.5 * math.sin(ph), 2)})
    return {'n_carboxylate': len(pos), 'carboxylates': pos, 'repeat_length_A': round(1.5 * len(seq), 1), 'stated_error_A': 0.8}


def registry(world, flip=False):
    f = world['fm']
    e, a = dict(f['energies']), dict(f['registry_angles'])
    names = sorted(e, key=e.get)
    low, other = names[0], names[1]
    margin = round(e[other] - e[low], 6)
    if flip:                                     # theta_match swapped with the other registry
        a[low], a[other] = a[other], a[low]
    return {'energies': e, 'registry_angles': a, 'theta_match': a[low], 'lowest': low, 'margin': margin,
            'stated_error': f.get('stated_error_eV', 0.1)}
