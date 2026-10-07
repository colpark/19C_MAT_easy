"""C2 reconstruction for JARVIS (CARD_jarvis). Imported by reconstruct.py.

Joins figshare 21370572 (1,058 EPC records) to JARVIS-DFT 3D (jarvis-tools dft_3d 2025-09-24) by jid, recomputes the
second route (lambda, omega_log, Tc from alpha2F with allen_dynes.py, mu* = 0.09, eq. 7 without f1 f2), rebuilds
theta_D (eq. 2) from Kv, Gv and density and n_atoms from the parent, and writes one record per material.
Frequency unit of alpha2F: identified from the axis range against the units QE and the paper use (THz, meV, cm-1,
Ry), and confirmed by the omega_log comparison (unit identification is metadata, like the Li-ion velocity unit).
"""
import json, os, sys, zipfile
import numpy as np
import allen_dynes as ad

RAW = os.path.expanduser('~/Documents/harbor/v4_host/trackC/raw')
H, KB, NA = 6.62607015e-34, 1.380649e-23, 6.02214076e23
MUSTAR = 0.09


def load_deposit(name='jarvis_epc_data_figshare_1058.json'):
    z = zipfile.ZipFile(os.path.join(RAW, 'figshare_21370572', name + '.zip'))
    return json.loads(z.read(name))


PARENT = os.environ.get('JARVIS_PARENT', 'dft_3d_2021')   # the paper's snapshot (v08.18.2021, 55,723 entries)


def load_parent(name=None):
    from jarvis.db.figshare import data
    return {r['jid']: r for r in data(name or PARENT, store_dir=os.path.join(RAW, 'jarvis_dft3d'))}


def _num(x):
    try:
        v = float(x)
        return v if np.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def theta_debye(rec):
    """Revision J1-R1 (VC-E17): the authors' own implementation, jarvis.analysis.elastic.tensor.ElasticTensor
    .debye_temperature on the parent elastic_tensor (Voigt-Reuss-Hill moduli, eq. 2). Unit check: jarvis-tools' own
    test value JVASP-19821 -> 1047.55 K (test_theta_jvasp19821). Disclosure (I4): adopted after the first recount with
    Voigt-only moduli (theta_debye_voigt) overcounted J1 (8,824 vs 5,618 stated)."""
    et = rec.get('elastic_tensor')
    if not isinstance(et, list) or len(et) != 6:
        return None
    from jarvis.analysis.elastic.tensor import ElasticTensor
    from jarvis.core.atoms import Atoms
    try:
        t = ElasticTensor(et_tensor=np.array(et, float)).debye_temperature(atoms=Atoms.from_dict(rec['atoms']))
    except Exception:
        return None
    return float(t) if np.isfinite(t) else None


def theta_debye_voigt(rec):
    """First reading (superseded): eq. 2 with v_m from Voigt K and G (GPa), density, atoms per volume."""
    K, G, rho = _num(rec.get('bulk_modulus_kv')), _num(rec.get('shear_modulus_gv')), _num(rec.get('density'))
    if not (K and G and rho) or K <= 0 or G <= 0:
        return None
    rho_si = rho * 1000.0
    vs = np.sqrt(G * 1e9 / rho_si)
    vl = np.sqrt((K + 4.0 * G / 3.0) * 1e9 / rho_si)
    vm = (1.0 / 3.0 * (2.0 / vs ** 3 + 1.0 / vl ** 3)) ** (-1.0 / 3.0)
    at = rec['atoms']
    lat = np.array(at['lattice_mat'], float)
    vol = abs(np.linalg.det(lat)) * 1e-30
    n = len(at['elements']) / vol
    return float(H / KB * (3.0 * n / (4.0 * np.pi)) ** (1.0 / 3.0) * vm)


def a2f_arrays(r):
    x, y = r.get('a2F_original_x'), r.get('a2F_original_y')
    if x and y and len(x) == len(y):
        return np.array(x, float), np.array(y, float), 'original'
    return None, None, None


def run(out):
    dep = load_deposit()
    par = load_parent()
    par25 = load_parent('dft_3d')   # fallback for jids added after 2021 (B1 icsd, n_atoms); never for recounts
    # unit identification on the axis ranges
    xmax = np.array([max(r['a2F_original_x']) for r in dep if r.get('a2F_original_x')])
    unit_guess = {'median_xmax': float(np.median(xmax)), 'p95_xmax': float(np.percentile(xmax, 95))}
    rows = []
    for r in dep:
        jid = r['jid']
        p = par.get(jid)
        pver = PARENT if p is not None else None
        if p is None and jid in par25:
            p, pver = par25[jid], 'dft_3d (2025 fallback)'
        x, y, src = a2f_arrays(r)
        rec = {'jid': jid, 'formula': r.get('formula') or (p and p.get('formula')), 'in_parent': p is not None,
               'parent_version': pver,
               'stability': r.get('stability'), 'press': r.get('press'),
               'dep_lamb': _num(r.get('lamb')), 'dep_wlog': _num(r.get('wlog')), 'dep_Tc': _num(r.get('Tc')),
               'n_atoms': len(r['atoms']['elements']), 'a2f_source': src, 'level': 'S',
               'source_address': {'file': 'jarvis_epc_data_figshare_1058.json', 'jid': jid}}
        if x is not None:
            for unit in ('THz', 'meV', 'cm-1'):
                m = ad.from_a2f(x, y, unit, MUSTAR)
                rec[f'ours_{unit}'] = {'lambda': m['lambda'], 'omega_log_K': m['omega_log_K'], 'Tc_K': m['Tc_K'],
                                       'n_negative_w': m['n_negative_w']}
        if p is not None:
            rec['parent'] = {'theta_D_K': theta_debye(p), 'nat_parent': _num(p.get('nat')),
                             'icsd': p.get('icsd'), 'Tc_supercon': p.get('Tc_supercon'),
                             'formation_energy_peratom': _num(p.get('formation_energy_peratom')),
                             'ehull': _num(p.get('ehull'))}
        rows.append(rec)
    with open(out, 'w') as f:
        for r in rows:
            f.write(json.dumps(r) + '\n')
    # parent-wide J1 / J3 recount (all dft_3d entries with elastic data)
    th = []
    for jid, p in par.items():
        t = theta_debye(p)
        if t is not None:
            th.append((jid, t, len(p['atoms']['elements'])))
    summ = {'parent_version': PARENT, 'n_deposit': len(dep), 'n_in_parent': sum(r['in_parent'] for r in rows), 'unit_axis': unit_guess,
            'n_in_2021_parent': sum(r['parent_version'] == PARENT for r in rows), 'parent_n': len(par), 'parent_with_elastic': len(th),
            'parent_theta_gt_300': sum(t > 300 for _, t, _ in th),
            'parent_theta_gt_300_natoms_le5': sum(t > 300 and n <= 5 for _, t, n in th)}
    json.dump({'summary': summ, 'parent_theta': th}, open(out.replace('.jsonl', '_parent.json'), 'w'))
    print(json.dumps(summ, indent=1))
