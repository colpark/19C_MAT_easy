#!/usr/bin/env python3
"""C2 reconstruction.

Li-ion (AiiDA profile trackC):
  reconstruct.py liion-traj OUT.jsonl      per FPMD trajectory: material (unit cell uuid), temperature, frame spacing,
                                           D_Li (msd.py, frozen C2proc), sigma by Nernst-Einstein (H = 1)
  reconstruct.py liion-meta-check OUT.json  validates the two metadata estimators on QE trajectories, where both are
                                           recorded: frame spacing dt = <dr.v>/<v.v> and kinetic temperature
JARVIS:
  reconstruct.py jarvis OUT.jsonl          join figshare 1058 with dft_3d, recompute lambda / omega_log / Tc from
                                           alpha2F (allen_dynes.py), theta_D from Kv, Gv, density (eq. 2), n_atoms

Metadata estimators (named procedures, validated on the QE half of the deposit before use on SIRIUS runs):
  * QE runs store timestep_in_fs = time between saved frames; `times` restarts at each concatenated segment, so time
    is frame index x timestep_in_fs.
  * dt_est = sum(dr . v_mid) / sum(v_mid . v_mid) over consecutive frames (minimum image), v in Hartree atomic units
    (bohr / (hbar/Eh)); T_kin = sum m v^2 / (3 N k_B) over frames after the first 10 %.
  * Revision M1 (dev evidence, 2026-10-07): the deposit's 'atomic' velocities are Rydberg atomic units (bohr per
    2 hbar/Eh): on the 118 QE runs the Hartree reading gave dt x 0.54 and T x 3.94 (factors 1/2 and 4). V_UNIT = 0.5
    converts to Hartree a.u. The dt estimator is validated on recorded runs whose stride matches the SIRIUS runs
    (criterion fixed before that run: |dt err| <= 5 % and |T err| <= 5 % on every regime-matched run); on QE FPMD
    frames (10 MD steps apart, 14.5 fs) its trapezoid bias is reported, not used.
"""
import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import msd, nernst_einstein as ne

BOHR = 0.529177210903          # Å
AUT_FS = 0.02418884326585747   # fs per Hartree atomic unit of time
AMU_ME = 1822.888486           # electron masses per amu
KB_HA = 3.166811563e-6         # Hartree per K
V_UNIT = 0.5                   # deposit velocities (Rydberg a.u.) -> Hartree a.u. (revision M1)


def _masses(symbols):
    from ase.data import atomic_masses, atomic_numbers
    return np.array([atomic_masses[atomic_numbers[s]] for s in symbols])


def dt_estimate_fs(pos, vel, cell, stride=1, nmax=400):
    """Frame spacing from positions (Å) and velocities (a.u.)."""
    idx = np.linspace(0, len(pos) - 2, min(nmax, len(pos) - 1)).astype(int)
    inv = np.linalg.inv(cell)
    num = den = 0.0
    for i in idx:
        d = pos[i + 1] - pos[i]
        f = d @ inv
        f -= np.round(f)
        d = f @ cell / BOHR                       # bohr
        v = 0.5 * (vel[i] + vel[i + 1]) * V_UNIT  # bohr / Hartree a.u.
        num += np.sum(d * v)
        den += np.sum(v * v)
    return num / den * AUT_FS


def t_kinetic(vel, symbols, skip=0.1):
    m = _masses(symbols) * AMU_ME
    v = vel[int(skip * len(vel)):] * V_UNIT
    ke = 0.5 * np.einsum('i,tij->t', m, v * v)    # Hartree
    return float(np.mean(2 * ke / (3 * len(symbols) * KB_HA)))


def _symbols(n):
    nat = n.get_shape('positions')[1]
    sym = n.base.attributes.get('symbols', None)
    if sym is not None and len(sym) == nat:
        return list(sym)
    if 'atomic_species_name' in n.get_arraynames():
        a = [str(s) for s in n.get_array('atomic_species_name')]
        if len(a) == nat:
            return a
    raise ValueError(f'no per-atom species for {n.uuid}')


def liion_index():
    from aiida import orm
    uc = {n.uuid: n for n in orm.load_group('First_principles_MD_unitcells').nodes}
    sc = list(orm.load_group('First_principles_MD_supercells').nodes)
    sc_by_uc = {}
    for s in sc:
        sc_by_uc.setdefault(s.base.extras.get('original_unitcell', None), []).append(s)
    return uc, sc, sc_by_uc


def match_supercell(traj, sc):
    """Untagged trajectory -> supercell by species multiset and first-frame cell (within 1e-3 Å)."""
    sym = sorted(_symbols(traj))
    c0 = traj.get_array('cells')[0]
    hits = []
    for s in sc:
        if sorted(x.kind_name for x in s.sites) != sym and sorted(x.symbol for x in s.get_ase()) != sym:
            continue
        if np.allclose(np.array(s.cell), c0, atol=1e-3):
            hits.append(s)
    return hits


def liion_meta_check(out):
    from aiida import load_profile, orm
    load_profile('trackC')
    rows = []
    for n in orm.load_group('xm46_trajectories').nodes:
        if 'times' not in n.get_arraynames():
            continue
        pos, vel, cell = n.get_array('positions'), n.get_array('velocities'), n.get_array('cells')[0]
        sym = _symbols(n)
        rows.append({'uuid': n.uuid, 'dt_rec': n.base.attributes.get('timestep_in_fs'),
                     'dt_est': float(dt_estimate_fs(pos, vel, cell)),
                     'T_rec': float(n.get_array('temperatures')[int(0.1 * len(pos)):].mean()),
                     'T_kin': t_kinetic(vel, sym)})
    dt_err = np.array([r['dt_est'] / r['dt_rec'] - 1 for r in rows])
    T_err = np.array([r['T_kin'] / r['T_rec'] - 1 for r in rows])
    rep = {'n': len(rows), 'dt_rel_err_median': float(np.median(dt_err)), 'dt_rel_err_maxabs': float(np.max(np.abs(dt_err))),
           'T_rel_err_median': float(np.median(T_err)), 'T_rel_err_maxabs': float(np.max(np.abs(T_err))),
           'criterion': 'pass if |dt err| <= 5 % and |T err| <= 5 % on every QE trajectory (fixed before the run)',
           'rows': rows}
    rep['pass'] = rep['dt_rel_err_maxabs'] <= 0.05 and rep['T_rel_err_maxabs'] <= 0.05
    json.dump(rep, open(out, 'w'), indent=1)
    print({k: v for k, v in rep.items() if k != 'rows'})


LADDER = (1000, 750, 600, 500)
SIRIUS_SET = (1100, 1000, 800, 750, 600, 500, 475)   # temperatures named in SIRIUS run extras (VC-E18)


def nearest_T(T, choices=LADDER):
    return min(choices, key=lambda x: abs(x - T))


def label_T(ex, kind, Tm):
    """Revision T1 (VC-E18): extras 'temperature' first; else a temperature named in an extras key ('..._1100K');
    else QE: nearest paper ladder value to the recorded mean; SIRIUS: nearest of SIRIUS_SET to the kinetic T."""
    import re
    if ex.get('temperature'):
        return int(ex['temperature']), 'extras'
    named = sorted({int(m) for k in ex for m in re.findall(r'_(\d{3,4})K$', k)})
    if len(named) == 1:
        return named[0], 'extras_key'
    if kind == 'qe':
        return nearest_T(Tm), 'qe_mean_nearest_ladder'
    return nearest_T(Tm, SIRIUS_SET), 'kinetic_nearest'



def liion_traj(out):
    from aiida import load_profile, orm
    load_profile('trackC')
    uc, sc, sc_by_uc = liion_index()
    sc_uc = {s.uuid: s.base.extras.get('original_unitcell', None) for s in sc}
    f = open(out, 'w')
    for n in orm.load_group('xm46_trajectories').nodes:
        ex = n.base.extras.all
        sym = _symbols(n)
        pos, vel = n.get_array('positions'), n.get_array('velocities')
        cells = n.get_array('cells')
        cell = cells[0]
        kind = 'qe' if 'times' in n.get_arraynames() else 'sirius'
        if kind == 'qe':
            dt = float(n.base.attributes.get('timestep_in_fs'))
            Tm = float(n.get_array('temperatures')[int(0.1 * len(pos)):].mean())
            dt_src, T_src = 'recorded', 'recorded'
        else:
            dt = float(dt_estimate_fs(pos, vel, cell))
            Tm = t_kinetic(vel, sym)
            dt_src, T_src = 'estimated', 'kinetic'
        ucid = ex.get('original_unitcell')
        how = 'extras'
        if ucid is None:
            hits = match_supercell(n, sc)
            ucid = sc_uc[hits[0].uuid] if len(hits) == 1 else None
            how = f'supercell_match({len(hits)})'
        Tlab, Tlab_src = label_T(ex, kind, Tm)
        mask = np.array([s == 'Li' for s in sym])
        r = msd.diffusion(pos, cell, dt / 1000.0, mask)
        vol = abs(np.linalg.det(cell))
        nli = int(mask.sum())
        sig = ne.sigma_mS_cm(nli, vol, r['D'], Tlab) if r['D'] > 0 else 0.0
        rec = {'traj_uuid': n.uuid, 'kind': kind, 'unitcell_uuid': ucid, 'map': how,
               'formula_uc': uc[ucid].get_formula(mode='hill_compact') if ucid in uc else None,
               'T_label': int(Tlab), 'T_label_src': Tlab_src, 'T_label_dev': abs(Tm - Tlab) / Tlab,
               'T_mean': Tm, 'T_src': T_src, 'dt_fs': dt, 'dt_src': dt_src, 'n_frames': int(len(pos)),
               't_total_ps': r['t_total_ps'], 'n_li': nli, 'n_atoms': len(sym), 'volume_A3': float(vol),
               'final_trajectory': ex.get('final_trajectory'), 'extras_keys': sorted(ex.keys()),
               'D_cm2_s': r['D'], 'D_se': r['D_se'], 'D_se_block': r['D_se_block'], 'D_se_atom': r['D_se_atom'],
               'sigma_mS_cm_H1': sig, 'level': 'S', 'source_address': {'archive': 'xm-46 fpmd_trajectories.aiida',
                                                                     'node': n.uuid, 'array': 'positions'}}
        f.write(json.dumps(rec) + '\n')
        f.flush()
        print(rec['formula_uc'], rec['T_label'], kind, f"{rec['D_cm2_s']:.2e}", how, flush=True)


def liion_cells(out):
    """Unit-cell table (deposited per-stage extras, S level) and the Li7NbO6 SAMOS route (deposited D)."""
    from aiida import load_profile, orm
    load_profile('trackC')
    from pymatgen.core import Composition
    cells = []
    for n in orm.load_group('First_principles_MD_unitcells').nodes:
        ex = n.base.extras.all
        sc = ex.get('source_cif', {}) or {}
        cells.append({'uuid': n.uuid, 'formula': n.get_formula(mode='hill_compact'),
                      'reduced': Composition(n.get_formula(mode='hill_compact')).reduced_formula,
                      'n_sites': len(n.sites), 'volume_A3': float(n.get_cell_volume()),
                      'origin_db': sc.get('db_name'), 'origin_id': sc.get('id'),
                      'flags': {k: ex.get(k) for k in ('integer_occupancy_filter', 'composition_filter',
                                                       'atomic_distance_filter', 'electronic_insulator',
                                                       'pinball_parameters_converged', 'ionic_conductor',
                                                       'ionic_conductor_1000K', 'has_partial_occupancies')},
                      'direct_bandgap_eV': ex.get('direct_bandgap'), 'old_study_exists': (ex.get('old_study') or {}).get('exists'),
                      'source_address': {'archive': 'xm-46 fpmd_structures.aiida', 'node': n.uuid, 'field': 'extras'}})
    samos = []
    for n in orm.load_group('xm46_Li7NbO6').nodes:
        if isinstance(n, orm.CalcFunctionNode) and n.process_label == 'get_diffusion_from_msd' and n.exit_status == 0:
            ins = {l.link_label: l.node for l in n.base.links.get_incoming().all()}
            out_ = {l.link_label: l.node for l in n.base.links.get_outgoing().all()}
            li = out_['msd_results'].base.attributes.get('Li')
            d = li['diffusion_mean_cm2_s']
            samos.append({'traj_uuid': ins['trajectory'].uuid, 'T': ins['trajectory'].base.extras.get('temperature', None),
                          'D_cm2_s': d if not isinstance(d, list) else None, 'D_variants': d if isinstance(d, list) else None,
                          'D_sem': li['diffusion_sem_cm2_s'], 'calc_uuid': n.uuid, 'level': 'S (deposited author output)'})
    json.dump({'cells': cells, 'samos_li7nbo6': samos}, open(out, 'w'), indent=1)
    st = []   # structures for B2 matching (xm-46 FPMD unit cells and 1c-13 PET-MAD unit cells)
    for g, tag in [('First_principles_MD_unitcells', 'xm46'), ('finetuned_petmad_mlmd_screening_new_fast_li_conductors', '1c13')]:
        for n in orm.load_group(g).nodes:
            if tag == '1c13' and n.base.extras.get('original_unitcell', None) is not None:
                continue
            ps = n.get_pymatgen_structure()
            st.append({'uuid': n.uuid, 'set': tag, 'reduced': ps.composition.reduced_formula, 'structure': ps.as_dict()})
    json.dump(st, open(out.replace('.json', '_struct.json'), 'w'))
    print(len(cells), 'cells;', len(samos), 'SAMOS fits')


if __name__ == '__main__':
    cmd, out = sys.argv[1], sys.argv[2]
    if cmd == 'liion-cells':
        liion_cells(out)
    if cmd == 'liion-meta-check':
        liion_meta_check(out)
    elif cmd == 'liion-traj':
        liion_traj(out)
    elif cmd == 'jarvis':
        import reconstruct_jarvis
        reconstruct_jarvis.run(out)
