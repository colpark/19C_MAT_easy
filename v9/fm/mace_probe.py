"""V9-9: time MACE-MH-1 on the identical 647-atom system UMA was timed on.

David's note: "Install MACE-MH-1 and time one single point and one converged relaxation on the
same 647-atom system. Nothing more. This exists so that if UMA fails Gate M we can try the
second model without another budget stop, and so its rate is measured rather than assumed."

Same system as `conv_probe.py`: P000 conformer 1, placement 0 of the frozen Sobol table, on the
same relaxed Au(111) slab, same fixed-layer mask, same 0.05 eV/A target. The slab reference is
relaxed with MACE itself, because a cross-model slab energy would be meaningless.

Head: **oc20_usemppbe**. MACE-MH-1's six heads are matpes_r2scan, mp_pbe_refit_add, spice_wB97M,
oc20_usemppbe, omol and omat_pbe. oc20_usemppbe is the OC20 head, chosen for exactly the reason
UMA's oc20 head was chosen in V9-5: it is the only one trained on molecular adsorbates on metal
slabs. The same disclosure applies, that OC20's adsorbates are small molecules so a 10-residue
peptide is an extrapolation of adsorbate size.

Runs under a separate interpreter (`~/v9_data/macenv`) so nothing is installed into the
read-only v8 environment (V9-X4). No energy from this probe is used as a margin or a prediction;
it is a rate measurement only.

Usage: macenv/bin/python mace_probe.py [--cap 1000] [--dtype float64]
"""
import argparse, json, os, sys, time
import warnings

warnings.filterwarnings("ignore")
import numpy as np

MODEL = os.path.expanduser("~/v9_data/mace/mace-mh-1.model")
HEAD = "oc20_usemppbe"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fm_run as F


def build():
    """The conv_probe.py system, bit for bit: P000 / conformer 1 / placement 0."""
    cd = os.path.expanduser("~/v9_data/fm/conf")
    S, fixed = F.slab()
    sym = list(np.load(os.path.join(cd, "P000_sym.npy")))
    base = F.lie_flat(np.load(os.path.join(cd, "P000_c1.npy")))
    row = F.placements(2)[0]
    cell = S.cell.array
    ztop = S.positions[:, 2].max()
    p = base @ F.rotz(row[2]).T
    p[:, 0] += row[0] * cell[0, 0] - p[:, 0].mean()
    p[:, 1] += row[1] * cell[1, 1] - p[:, 1].mean()
    p[:, 2] += (ztop + F.GAP_A + row[3]) - p[:, 2].min()
    return S, fixed, sym, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cap", type=int, default=1000)
    ap.add_argument("--dtype", default="float64")
    ap.add_argument("--out", default=os.path.expanduser("~/v9_data/fm/probe/mace_probe.json"))
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out), exist_ok=True)

    from ase import Atoms
    from ase.constraints import FixAtoms
    from ase.optimize import LBFGS
    from mace.calculators import MACECalculator

    S, fixed, sym, p = build()
    out = dict(model="mace-mh-1", head=HEAD, dtype=a.dtype, cap=a.cap,
               model_bytes=os.path.getsize(MODEL),
               n_atoms=len(S) + len(sym), n_slab=len(S), n_peptide=len(sym),
               n_fixed=int(fixed.sum()), energy_recorded_as_a_margin=False)

    t = time.time()
    calc = MACECalculator(model_paths=MODEL, device="cuda", default_dtype=a.dtype, head=HEAD)
    out["t_load_model_s"] = round(time.time() - t, 2)
    print(json.dumps(out), flush=True)

    cell = S.cell.array
    S.calc = calc
    t = time.time()
    optS = LBFGS(S, logfile=None); optS.run(fmax=0.05, steps=a.cap)
    e_slab = float(S.get_potential_energy())
    out.update(slab_steps=optS.get_number_of_steps(), t_slab_s=round(time.time() - t, 1),
               slab_fmax=round(float(np.abs(S.get_forces()[~fixed]).max()), 4))
    slab_pos = S.get_positions()
    print(f"slab: {out['slab_steps']} steps, {out['t_slab_s']}s, fmax {out['slab_fmax']}", flush=True)

    allsym = list(S.get_chemical_symbols()) + sym
    allpos = np.vstack([slab_pos, p])
    m = np.zeros(len(allsym), bool); m[:len(S)] = fixed

    def complex_atoms():
        cx = Atoms(symbols=allsym, positions=allpos.copy(), cell=cell, pbc=True)
        cx.set_constraint(FixAtoms(mask=m))
        cx.set_tags(np.concatenate([np.where(fixed, 0, 1), np.full(len(sym), 2)]))
        cx.calc = calc
        return cx

    # (1) one single point
    cx = complex_atoms()
    t = time.time()
    e0 = float(cx.get_potential_energy())
    out["t_single_point_s"] = round(time.time() - t, 4)
    t = time.time()
    e0b = float(complex_atoms().get_potential_energy())
    out["t_single_point_warm_s"] = round(time.time() - t, 4)
    out["single_point_finite"] = bool(np.isfinite(e0) and np.isfinite(e0b))
    print(f"single point: {out['t_single_point_s']}s cold, {out['t_single_point_warm_s']}s warm",
          flush=True)

    # (2) one converged relaxation, trajectory recorded (the fmax path wanders; V9-E3)
    cx = complex_atoms()
    traj, t0 = [], time.time()
    opt = LBFGS(cx, logfile=None)
    for conv in opt.irun(fmax=0.05, steps=a.cap):
        n = opt.get_number_of_steps()
        if n % 50 == 0 or conv:
            fm = float(np.abs(cx.get_forces()[~m]).max())
            traj.append(dict(step=n, fmax=round(fm, 4), t=round(time.time() - t0, 1)))
            print(f"  LBFGS step {n:5d} fmax {fm:8.4f} t {time.time()-t0:7.1f}s", flush=True)
        if conv:
            break
    ns = opt.get_number_of_steps()
    fmf = float(np.abs(cx.get_forces()[~m]).max())
    out.update(relax_steps=ns, relax_converged=bool(fmf <= 0.05), relax_final_fmax=round(fmf, 4),
               relax_hit_cap=ns >= a.cap, t_relax_s=round(time.time() - t0, 1),
               s_per_step=round((time.time() - t0) / max(ns, 1), 4), traj=traj)
    print(f"relaxation: {ns} steps, converged={out['relax_converged']}, fmax {out['relax_final_fmax']}, "
          f"{out['t_relax_s']}s ({out['s_per_step']}s/step)", flush=True)

    # rung 2's shape, for the budget question this probe exists to answer
    out["projection_60_peptides_3x3_gpu_hours"] = round(60 * 9 * out["t_relax_s"] / 3600.0, 2)
    out["projection_120_peptides_3x10_single_points_gpu_hours"] = round(
        120 * 3 * 10 * out["t_single_point_warm_s"] / 3600.0, 3)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "traj"}, indent=1))


if __name__ == "__main__":
    main()
