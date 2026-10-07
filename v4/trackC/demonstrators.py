#!/usr/bin/env python3
"""C3 demonstrators (skill D1, C3). FMs approximate pipeline stages; they never write a key.

Run specification (frozen at C3spec before any run):
  Li-ion MD   : start from the deposited FPMD supercell (experimental geometry); relax positions only at fixed cell
                (FIRE, fmax 0.05 eV/Å, <= 300 steps); NVT Langevin (friction 0.01 1/fs), time step 2 fs, Li mass
                unchanged; 50 ps at the target temperature after 2 ps of equilibration; frames every 20 fs are kept in
                memory only; cached: Li MSD curve (msd.msd_for_panel) and D from msd.diffusion (frozen C2proc), never
                the frames. Wall-clock cap 4 GPU-hours per material (all its temperatures), then stop and log.
                Temperatures: 1000 K for every deposited cell (55 xm-46 + 11 1c-13); 750, 600, 500 K for cells with a
                deposited ladder.
  JARVIS phon.: start from the deposited atoms; relax cell and positions (FIRE + FrechetCellFilter, fmax 0.02 eV/Å,
                <= 500 steps); force constants of the 2x2x2 supercell by finite displacement (phonopy, 0.01 Å);
                frequencies at the 8 q-points commensurate with 2x2x2 (the paper's minimum q-grid); 'unstable' iff any
                frequency is imaginary with |nu| > 0.3 THz, the three acoustic modes at Gamma excluded (named default).
  Validation  : on the dev split only (SPLITS.json): Li-ion log10 D error against our FPMD D (C2), and the
                1 mS/cm gate at 1000 K (precision, recall, flip rate within tau_D of the threshold); JARVIS stability
                precision / recall / accuracy against the deposited DFPT label. Frozen to fm_errors.json.
Leak status (D1): set per FM from its documented training data, by keyed target type and by structure match where the
training set is on the host. Leaky or unknown FMs stay reference routes (no tool arm, no Arbitrate input).
"""
import argparse, hashlib, json, os, sys, time
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FM = {
    'mace_mpa0': {'name': 'MACE-MPA-0 (medium-mpa-0)', 'package': 'mace-torch 0.3.16', 'license': 'MIT',
                  'training_data': 'MPtrj + sAlex (PBE/PBE+U relaxation frames; public)',
                  'keyed_target_types_in_training': 'none (energies, forces, stresses of near-equilibrium frames; no '
                                                    'MD diffusivity, no DFPT phonon stability, no EPC)',
                  'leak_status': 'clean', 'venv': '.venv'},
    'orb_v3': {'name': 'Orb v3 conservative inf MPA', 'package': 'orb-models 0.5.5 (0.7.0 ships no ASE calculator)', 'license': 'Apache-2.0',
               'training_data': 'MPtrj + Alexandria (public)', 'leak_status': 'clean', 'venv': '.venv',
               'keyed_target_types_in_training': 'none (as above)'},
    'mattersim_v1': {'name': 'MatterSim v1.0.0-5M', 'package': 'mattersim 1.2.5', 'license': 'MIT',
                     'training_data': 'proprietary generated set (~17M structures, elements x T x P); not public',
                     'keyed_target_types_in_training': 'energies/forces/stresses only (documented), but the structure '
                                                       'list is undisclosed: the id/structure check is impossible',
                     'leak_status': 'unknown', 'venv': '.venv-ms'},
    'petmad_ft_1c13': {'name': 'PET-MAD v1.0.2 fine-tuned on Li chemistries (1c-13)', 'license': 'record CC BY 4.0',
                       'training_data': 'fine-tuning.xyz (3,558 frames, 814 formulas): covers all 52 keyed FPMD '
                                        'formulas (structure/formula match, C3)', 'leak_status': 'leaky',
                       'use': 'reference engine route in C2 only'},
    'petmad_base': {'name': 'PET-MAD base', 'leak_status': 'not run',
                    'note': 'weights via HuggingFace/metatomic; MAD includes MC3D AIMD frames from the same group: '
                            'leak unknown without a MAD structure check; skipped in this pilot'},
    'alignn_tc': {'name': 'ALIGNN Tc/lambda/wlog (JARVIS)', 'leak_status': 'leaky',
                  'note': 'trained on this deposit (same group); never run'},
    'bee_net': {'name': 'BEE-NET', 'leak_status': 'unknown', 'note': 'training list not verified to exclude these jids; '
                                                                     'skipped (prompt C3.4)'},
}
IMAG_THz = 0.3


# ------------------------------------------------------------------ calculators
def calculator(fm, device='cuda'):
    if fm == 'mace_mpa0':
        from mace.calculators import mace_mp
        return mace_mp(model='medium-mpa-0', device=device, default_dtype='float32')
    if fm == 'orb_v3':
        from orb_models.forcefield import pretrained
        try:
            from orb_models.forcefield.calculator import ORBCalculator
        except ImportError:
            from orb_models.forcefield.forcefield_adapter import ORBCalculator  # noqa
        m = pretrained.orb_v3_conservative_inf_mpa(device=device, precision='float32-high')
        return ORBCalculator(m, device=device)
    if fm == 'mattersim_v1':
        from mattersim.forcefield import MatterSimCalculator
        return MatterSimCalculator(load_path='MatterSim-v1.0.0-5M.pth', device=device)
    raise ValueError(fm)


def weights_sha(fm):
    import glob
    pats = {'mace_mpa0': '~/.cache/mace/*mpa*', 'orb_v3': '~/.cache/cached_path/*', 'mattersim_v1': '~/.local/mattersim/pretrained_models/*5M*'}
    out = {}
    for p in glob.glob(os.path.expanduser(pats.get(fm, '')), recursive=True):
        if os.path.isfile(p):
            out[os.path.basename(p)] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return out


# ------------------------------------------------------------------ Li-ion MD
def liion_md(job, fm, outdir, cap_h=4.0, only_T=None):
    from ase import Atoms, units
    from ase.optimize import FIRE
    from ase.md.langevin import Langevin
    from ase.md.velocitydistribution import MaxwellBoltzmannDistribution
    import msd
    calc = calculator(fm)
    os.makedirs(outdir, exist_ok=True)
    t_start = time.time()
    a0 = Atoms(symbols=job['symbols'], positions=job['positions'], cell=job['cell'], pbc=True)
    a = a0.copy()
    a.calc = calc
    FIRE(a, logfile=None).run(fmax=0.05, steps=300)
    relaxed = a.get_positions().copy()
    for T in job['temperatures']:
        if only_T is not None and T != only_T:
            continue
        out = os.path.join(outdir, f"{job['material_id']}_{fm}_{T}K.json")
        if os.path.exists(out):
            continue
        if (time.time() - t_start) / 3600 > cap_h:
            json.dump({'material_id': job['material_id'], 'fm': fm, 'T': T, 'status': 'cap_exceeded'}, open(out, 'w'))
            continue
        b = a0.copy()
        b.set_positions(relaxed)
        b.calc = calc
        MaxwellBoltzmannDistribution(b, temperature_K=T, rng=np.random.default_rng(17))
        dyn = Langevin(b, 2.0 * units.fs, temperature_K=T, friction=0.01 / units.fs, rng=np.random.default_rng(23))
        try:
            dyn.run(1000)  # 2 ps equilibration
            frames = []
            nsteps, stride = 25000, 10
            t0 = time.time()
            for i in range(nsteps // stride):
                dyn.run(stride)
                frames.append(b.get_positions(wrap=True).copy())
                if i % 500 == 0:
                    print('progress', job['material_id'], fm, T, i * stride, round(time.time() - t0), flush=True)
            ok, err = True, None
        except Exception as e:  # MD blow-up is a demonstrator failure, recorded
            ok, err = False, repr(e)[:300]
        rec = {'material_id': job['material_id'], 'fm': fm, 'T': T, 'status': 'ok' if ok else 'failed', 'error': err,
               'dt_fs': 2.0, 'frame_fs': 20.0, 'n_frames': len(frames) if ok else 0, 'host': os.uname().nodename,
               'wall_s': time.time() - t0 if ok else None}
        if ok:
            pos = np.array(frames)
            mask = np.array([s == 'Li' for s in job['symbols']])
            r = msd.diffusion(pos, np.array(job['cell']), 0.02, mask)
            tp, mp = msd.msd_for_panel(pos, np.array(job['cell']), 0.02, mask)
            rec.update({'D_cm2_s': r['D'], 'D_se': r['D_se'], 't_total_ps': r['t_total_ps'],
                        'msd_t_ps': tp.tolist(), 'msd_A2': mp.tolist()})
        json.dump(rec, open(out, 'w'))
        print(job['material_id'], fm, T, rec['status'], rec.get('D_cm2_s'), flush=True)


# ------------------------------------------------------------------ JARVIS phonons
def jarvis_phonon(job, fm, calc):
    from ase import Atoms
    from ase.optimize import FIRE
    from ase.filters import FrechetCellFilter
    from phonopy import Phonopy
    from phonopy.structure.atoms import PhonopyAtoms
    a = Atoms(symbols=job['elements'], positions=job['cart'], cell=job['lattice'], pbc=True)
    a.calc = calc
    try:
        FIRE(FrechetCellFilter(a), logfile=None).run(fmax=0.02, steps=500)
        u = PhonopyAtoms(symbols=a.get_chemical_symbols(), cell=a.cell[:], positions=a.get_positions())
        ph = Phonopy(u, supercell_matrix=np.diag([2, 2, 2]), primitive_matrix=None)
        ph.generate_displacements(distance=0.01)
        F = []
        for sc in ph.supercells_with_displacements:
            s = Atoms(symbols=sc.symbols, positions=sc.positions, cell=sc.cell, pbc=True)
            s.calc = calc
            F.append(s.get_forces())
        ph.forces = np.array(F)
        ph.produce_force_constants()
        qs = [[i / 2, j / 2, k / 2] for i in (0, 1) for j in (0, 1) for k in (0, 1)]
        ph.run_qpoints(qs)
        fr = ph.get_qpoints_dict()['frequencies']   # THz, imaginary as negative
        g = np.sort(fr[0])[3:]                        # drop 3 acoustic at Gamma
        rest = np.concatenate([g] + [fr[i] for i in range(1, len(qs))])
        mn = float(rest.min())
        return {'status': 'ok', 'min_freq_THz': mn, 'stable': bool(mn > -IMAG_THz),
                'n_disp': len(F), 'cell_volume_change': float(a.get_volume() / abs(np.linalg.det(job['lattice'])) - 1)}
    except Exception as e:
        return {'status': 'failed', 'error': repr(e)[:300]}


def make_jobs(outdir):
    """Builder host: Li-ion jobs from the deposited supercells (xm-46 FPMD, 1c-13 PET-MAD), JARVIS jobs from the
    deposited atoms. Material ids are the neutral ids of materials.jsonl (1c-13: PM- ids, split test)."""
    from aiida import load_profile, orm
    load_profile('trackC')
    mats = [json.loads(l) for l in open(os.path.join(HERE, 'materials_liion.jsonl'))]
    by_uc = {m['unitcell_uuid']: m for m in mats}
    jobs = []
    for g, tag in [('First_principles_MD_supercells', 'xm46'), ('finetuned_petmad_mlmd_screening_new_fast_li_conductors', '1c13')]:
        for n in orm.load_group(g).nodes:
            uc = n.base.extras.get('original_unitcell', None)
            if uc is None:
                continue
            if tag == 'xm46':
                m = by_uc.get(uc)
                if m is None:
                    continue
                mid = m['material_id']
                temps = [1000] + sorted([int(T) for T in m['stages']['FPMD'] if int(T) in (750, 600, 500)], reverse=True)
                if len(m['stages']['FPMD']) < 2:
                    temps = [1000]
                if mid in {j['material_id'] for j in jobs}:
                    continue
            else:
                mid = 'PM-' + hashlib.sha256(uc.encode()).hexdigest()[:8]
                temps = [1000]
            a = n.get_ase()
            jobs.append({'material_id': mid, 'set': tag, 'symbols': a.get_chemical_symbols(),
                         'positions': a.get_positions().tolist(), 'cell': a.cell[:].tolist(), 'temperatures': temps,
                         'n_atoms': len(a), 'supercell_uuid': n.uuid})
    jobs.sort(key=lambda j: j['n_atoms'])
    json.dump(jobs, open(os.path.join(outdir, 'liion_jobs.json'), 'w'))
    jj = []
    for l in open(os.path.join(HERE, 'materials_jarvis.jsonl')):
        m = json.loads(l)
        jj.append({'material_id': m['material_id'], 'jid': m['jid']})
    import zipfile
    raw = os.path.expanduser('~/Documents/harbor/v4_host/trackC/raw/figshare_21370572/jarvis_epc_data_figshare_1058.json.zip')
    dep = {r['jid']: r for r in json.loads(zipfile.ZipFile(raw).read('jarvis_epc_data_figshare_1058.json'))}
    for j in jj:
        at = dep[j['jid']]['atoms']
        lat = np.array(at['lattice_mat'], float)
        co = np.array(at['coords'], float)
        j.update({'elements': at['elements'], 'lattice': lat.tolist(),
                  'cart': (co if at.get('cartesian') else co @ lat).tolist()})
    json.dump(jj, open(os.path.join(outdir, 'jarvis_jobs.json'), 'w'))
    na = [j['n_atoms'] for j in jobs]
    print(len(jobs), 'li-ion jobs; atoms', min(na), np.median(na), max(na), '; runs', sum(len(j['temperatures']) for j in jobs),
          '; atom-runs', sum(j['n_atoms'] * len(j['temperatures']) for j in jobs), '|', len(jj), 'jarvis jobs')


def validate(md_dir, ph_dir, out):
    """C3.5 on the dev split only (SPLITS.json): Li-ion log10 D error vs our FPMD D (1000 K and ladder temperatures
    present), 1 mS/cm gate at 1000 K (precision / recall / accuracy, flip rate within tau_D of the threshold);
    JARVIS stability precision / recall / accuracy vs the deposited DFPT label. Also writes fm_outputs_table.json (R0)."""
    import nernst_einstein as ne
    S = json.load(open(os.path.join(HERE, 'SPLITS.json')))['materials']
    tau = json.load(open(os.path.join(HERE, 'TOLERANCES_trackC.json')))['liion_tau_D_dex']
    L = {json.loads(l)['material_id']: json.loads(l) for l in open(os.path.join(HERE, 'materials_liion.jsonl'))}
    J = {json.loads(l)['material_id']: json.loads(l) for l in open(os.path.join(HERE, 'materials_jarvis.jsonl'))}
    md = defaultdict(dict)
    for fn in sorted(os.listdir(md_dir)) if os.path.isdir(md_dir) else []:
        r = json.load(open(os.path.join(md_dir, fn)))
        md[(r['material_id'], r['fm'])][r['T']] = r
    ph = defaultdict(dict)
    for fn in sorted(os.listdir(ph_dir)) if os.path.isdir(ph_dir) else []:
        for l in open(os.path.join(ph_dir, fn)):
            r = json.loads(l)
            ph[r['fm']][r['material_id']] = r
    rep = {'split_used': 'dev', 'liion': {}, 'jarvis': {}}
    table = defaultdict(list)
    for fm in [k for k in FM if k in {f for _, f in md}]:
        err, gate, flips, n_fail = [], [], 0, 0
        for (mid, f), byT in md.items():
            if f != fm:
                continue
            for T, r in byT.items():
                if r['status'] != 'ok':
                    n_fail += 1
                    continue
                v = L[mid]['stages']['FPMD'].get(str(T))
                sig = ne.sigma_mS_cm(v['n_li'], v['volume_A3'], max(r['D_cm2_s'], 0), T) if v else None
                table[mid].append((FM[fm]['name'] + f' ({FM[fm]["leak_status"]})', f'D at {T} K (cm^2/s)', f"{r['D_cm2_s']:.3g}"))
                if sig is not None:
                    table[mid].append((FM[fm]['name'] + f' ({FM[fm]["leak_status"]})', f'sigma at {T} K, H = 1 (mS/cm)', f'{sig:.3g}'))
                if S[mid]['split'] != 'dev' or v is None:
                    continue
                if v['D'] > 0 and r['D_cm2_s'] > 0:
                    err.append(np.log10(r['D_cm2_s'] / v['D']))
                if T == 1000:
                    key = v['sigma_H1'] >= 1.0
                    pred = sig >= 1.0
                    gate.append((key, pred))
                    if abs(np.log10(max(v['sigma_H1'], 1e-12))) <= tau and key != pred:
                        flips += 1
        tp = sum(k and p for k, p in gate); fp = sum((not k) and p for k, p in gate); fn_ = sum(k and (not p) for k, p in gate)
        rep['liion'][fm] = {'leak_status': FM[fm]['leak_status'], 'n_dev_runs': len(err), 'log10_D_err_mean': float(np.mean(err)) if err else None,
                            'log10_D_err_mae': float(np.mean(np.abs(err))) if err else None, 'gate_n': len(gate),
                            'gate_precision': tp / (tp + fp) if tp + fp else None, 'gate_recall': tp / (tp + fn_) if tp + fn_ else None,
                            'gate_accuracy': sum(k == p for k, p in gate) / len(gate) if gate else None,
                            'flip_within_tau': flips, 'failed_runs': n_fail,
                            'validation_pass': bool(err and np.mean(np.abs(err)) <= tau and gate and sum(k == p for k, p in gate) / len(gate) >= 0.8)}
    for fm, rows in ph.items():
        y = [(J[m]['stages']['J6']['pass'], r['stable']) for m, r in rows.items() if r.get('status') == 'ok' and S[m]['split'] == 'dev']
        for m, r in rows.items():
            if r.get('status') == 'ok':
                table[m].append((FM[fm]['name'] + f' ({FM[fm]["leak_status"]})', 'lowest phonon frequency, 2x2x2 (THz)', f"{r['min_freq_THz']:.2f}"))
        tp = sum(k and p for k, p in y); fp = sum((not k) and p for k, p in y); fn_ = sum(k and (not p) for k, p in y)
        acc = sum(k == p for k, p in y) / len(y) if y else None
        rep['jarvis'][fm] = {'leak_status': FM[fm]['leak_status'], 'n_dev': len(y), 'stable_precision': tp / (tp + fp) if tp + fp else None,
                             'stable_recall': tp / (tp + fn_) if tp + fn_ else None, 'accuracy': acc,
                             'failed': sum(1 for r in rows.values() if r.get('status') != 'ok'),
                             'validation_pass': bool(acc is not None and acc >= 0.7)}
    rep['criteria'] = {'liion': 'mean |log10 D err| <= tau_D and gate accuracy >= 0.8 on dev', 'jarvis': 'accuracy >= 0.7 on dev',
                       'note': 'criteria fixed in this function before the first validation run; a failed FM stays a marked tool'}
    json.dump(rep, open(out, 'w'), indent=1)
    json.dump({k: v for k, v in table.items()}, open(os.path.join(HERE, 'fm_outputs_table.json'), 'w'))
    print(json.dumps(rep, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['registry', 'liion-md', 'jarvis-phonon', 'jobs', 'validate'])
    ap.add_argument('--md')
    ap.add_argument('--ph')
    ap.add_argument('--jobs')
    ap.add_argument('--fm')
    ap.add_argument('--out')
    ap.add_argument('--shard', default='0/1')
    a = ap.parse_args()
    if a.cmd == 'validate':
        validate(a.md, a.ph, a.out)
        return
    if a.cmd == 'jobs':
        make_jobs(a.out)
        return
    if a.cmd == 'registry':
        reg = {k: dict(v, weights_sha256=weights_sha(k)) for k, v in FM.items()}
        json.dump(reg, open(a.out, 'w'), indent=1)
        print(json.dumps({k: (v['leak_status'], list(v['weights_sha256'].values())[:1]) for k, v in reg.items()}, indent=1))
        return
    jobs = json.load(open(a.jobs))
    i, n = map(int, a.shard.split('/'))
    jobs = jobs[i::n]
    if a.cmd == 'liion-md':
        # scheduling only (run content frozen at C3spec): every 1000 K run first, then 750, 600, 500 K
        for T in (1000, 750, 600, 500):
            for j in jobs:
                if T in j['temperatures']:
                    liion_md(j, a.fm, a.out, only_T=T)
    else:
        calc = calculator(a.fm)
        os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
        done = set()
        if os.path.exists(a.out):
            done = {json.loads(l)['material_id'] for l in open(a.out)}
        with open(a.out, 'a') as f:
            for j in jobs:
                if j['material_id'] in done:
                    continue
                t0 = time.time()
                r = jarvis_phonon(j, a.fm, calc)
                r.update({'material_id': j['material_id'], 'fm': a.fm, 'wall_s': time.time() - t0, 'host': os.uname().nodename})
                f.write(json.dumps(r) + '\n')
                f.flush()


if __name__ == '__main__':
    main()
