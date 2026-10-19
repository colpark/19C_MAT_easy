"""V9-5: UMA adsorption energies for dev peptides on Au(111).

Pre-declared before any number was seen (hard rule 5):

* Head: **oc20**. Of UMA's heads (oc20, oc22, oc25, odac, omat, omc, omol) it is the only one
  trained on molecular adsorbates on metal slabs, which is exactly this geometry. Disclosure:
  OC20's adsorbates are small molecules, not 10-residue peptides, so adsorbate size is an
  extrapolation.
* Estimator: per peptide, E_ads = min over all 3x10 = 30 evaluations of
      E(complex, relaxed) - E(slab, relaxed) - E(conformer, relaxed in the same cell)
  and the FM predicts the peptide with the **lower (more negative) E_ads** as the stronger
  binder. Fixed now, before any energy was computed.
* Convergence recorded per relaxation: step count and final fmax (hard rule 4). No cap is
  assumed generous; `hit_cap` is reported per evaluation.
* Validity check (hard rule 3) runs on every complex before it reaches the FM.

Usage: python fm_run.py CONFDIR OUTDIR [--pids P000,P060] [--placements 10] [--max-steps 200]
"""
import argparse, json, os, time

import numpy as np

SOBOL_SEED = 20261019
GAP_A = 2.6               # nominal peptide-surface gap before relaxation
DZ_RANGE = (-0.3, 0.7)
FIXED_LAYERS = 2          # of 4
LIMIT_A = 1.0


def slab():
    from ase.build import fcc111
    from ase.constraints import FixAtoms
    s = fcc111("Au", size=(14, 10, 4), vacuum=12.0, orthogonal=True)
    z = s.positions[:, 2]
    layers = np.unique(np.round(z, 3))
    fixed = np.isin(np.round(z, 3), layers[:FIXED_LAYERS])
    s.set_constraint(FixAtoms(mask=fixed))
    s.set_tags(np.where(fixed, 0, 1))
    return s, fixed


def placements(n):
    from scipy.stats import qmc
    s = qmc.Sobol(d=4, scramble=True, seed=SOBOL_SEED).random(n)
    out = np.empty_like(s)
    out[:, 0] = s[:, 0]                                   # fractional x
    out[:, 1] = s[:, 1]                                   # fractional y
    out[:, 2] = s[:, 2] * 360.0                           # rotation about z
    out[:, 3] = DZ_RANGE[0] + s[:, 3] * (DZ_RANGE[1] - DZ_RANGE[0])
    return out


def lie_flat(p):
    """Put the longest principal axis along x and the shortest along z, deterministically."""
    c = p - p.mean(0)
    w, v = np.linalg.eigh(np.cov(c.T))
    R = v[:, ::-1]                                        # columns: largest -> smallest
    if np.linalg.det(R) < 0:
        R[:, 2] *= -1
    return c @ R


def rotz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])


def validity(pos, sym):
    from scipy.spatial import cKDTree
    h = [i for i, s in enumerate(sym) if s != "H"]
    t = cKDTree(pos[h])
    d, _ = t.query(pos[h], k=2)
    return float(d[:, 1].min()), len(t.query_pairs(LIMIT_A))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("confdir"); ap.add_argument("outdir")
    ap.add_argument("--pids", default=""); ap.add_argument("--placements", type=int, default=10)
    ap.add_argument("--max-steps", type=int, default=200); ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--conformers", type=int, default=3)
    a = ap.parse_args()
    cd = os.path.expanduser(a.confdir); od = os.path.expanduser(a.outdir)
    os.makedirs(od, exist_ok=True)
    man = json.load(open(os.path.join(cd, "conformers.json")))
    pids = a.pids.split(",") if a.pids else [e["pid"] for e in man["peptides"]]
    cls = {e["pid"]: e["cls"] for e in man["peptides"]}

    from ase import Atoms
    from ase.constraints import FixAtoms
    from ase.optimize import LBFGS
    from fairchem.core import FAIRChemCalculator, pretrained_mlip
    pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
    calc = FAIRChemCalculator(pu, task_name="oc20")

    S, fixed = slab()
    cell = S.cell.array
    ztop = S.positions[:, 2].max()
    t = time.time()
    S.calc = calc
    optS = LBFGS(S, logfile=None); optS.run(fmax=a.fmax, steps=a.max_steps)
    e_slab = float(S.get_potential_energy())
    slab_pos = S.get_positions()
    print(json.dumps(dict(n_slab=len(S), n_fixed=int(fixed.sum()),
                          cell=[round(x, 3) for x in S.cell.lengths()],
                          e_slab_eV=round(e_slab, 4), slab_steps=optS.get_number_of_steps(),
                          slab_fmax=round(float(np.abs(S.get_forces()[~fixed]).max()), 4),
                          t_slab_s=round(time.time() - t, 1), head="oc20",
                          sobol_seed=SOBOL_SEED, gap_A=GAP_A, dz_range=list(DZ_RANGE))), flush=True)

    tab = placements(a.placements)
    results = {}
    for pid in pids:
        sym = list(np.load(os.path.join(cd, f"{pid}_sym.npy")))
        rows, t_pep = [], time.time()
        e_conf = {}
        for k in range(a.conformers):
            f = os.path.join(cd, f"{pid}_c{k}.npy")
            if not os.path.exists(f):
                continue
            base = lie_flat(np.load(f))
            # reference energy: this conformer alone in the same cell, same head
            at = Atoms(symbols=sym, positions=base - base.min(0) + 6.0, cell=cell, pbc=True)
            at.calc = calc
            o = LBFGS(at, logfile=None); o.run(fmax=a.fmax, steps=a.max_steps)
            e_conf[k] = float(at.get_potential_energy())
            for j, row in enumerate(tab):
                p = base @ rotz(row[2]).T
                p[:, 0] += row[0] * cell[0, 0] - p[:, 0].mean()
                p[:, 1] += row[1] * cell[1, 1] - p[:, 1].mean()
                p[:, 2] += (ztop + GAP_A + row[3]) - p[:, 2].min()
                allpos = np.vstack([slab_pos, p])
                allsym = list(S.get_chemical_symbols()) + sym
                mn, nbad = validity(allpos, allsym)
                if nbad:
                    rows.append(dict(k=k, j=j, refused=True, min_heavy_pair_A=round(mn, 4),
                                     n_pairs_below_1A=nbad))
                    continue
                cx = Atoms(symbols=allsym, positions=allpos, cell=cell, pbc=True)
                m = np.zeros(len(cx), bool); m[:len(S)] = fixed
                cx.set_constraint(FixAtoms(mask=m))
                cx.set_tags(np.concatenate([np.where(fixed, 0, 1), np.full(len(sym), 2)]))
                cx.calc = calc
                t0 = time.time()
                opt = LBFGS(cx, logfile=None)
                opt.run(fmax=a.fmax, steps=a.max_steps)
                ns = opt.get_number_of_steps()
                e = float(cx.get_potential_energy())
                rows.append(dict(k=k, j=j, refused=False,
                                 e_complex_eV=round(e, 4), e_conf_eV=round(e_conf[k], 4),
                                 e_ads_eV=round(e - e_slab - e_conf[k], 4),
                                 steps=ns, hit_cap=ns >= a.max_steps,
                                 fmax=round(float(np.abs(cx.get_forces()[~m]).max()), 4),
                                 t_s=round(time.time() - t0, 2),
                                 min_heavy_pair_A=round(mn, 4)))
        ok = [r for r in rows if not r["refused"]]
        results[pid] = dict(pid=pid, cls=cls[pid], n_atoms_peptide=len(sym),
                            n_eval=len(ok), n_refused=len(rows) - len(ok),
                            e_ads_min_eV=min((r["e_ads_eV"] for r in ok), default=None),
                            e_conf_eV={str(k): round(v, 4) for k, v in e_conf.items()},
                            t_peptide_s=round(time.time() - t_pep, 1), rows=rows)
        r = results[pid]
        print(f"{pid} {cls[pid]:6s} evals {r['n_eval']:3d} refused {r['n_refused']:2d} "
              f"E_ads_min {r['e_ads_min_eV']} eV  {r['t_peptide_s']}s "
              f"(cap hits {sum(1 for x in ok if x['hit_cap'])})", flush=True)
        json.dump(dict(head="oc20", model="uma-s-1p2", e_slab_eV=e_slab,
                       sobol_seed=SOBOL_SEED, max_steps=a.max_steps, fmax=a.fmax,
                       placements=a.placements, conformers=a.conformers,
                       results=results),
                  open(os.path.join(od, "fm_dev.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
