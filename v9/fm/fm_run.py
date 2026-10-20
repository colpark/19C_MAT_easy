"""V9-5 / V9-7 / V9-8: UMA adsorption energies for dev peptides on Au(111).

Pre-declared before any number was seen (hard rule 5):

* Head: **oc20**. Of UMA's heads (oc20, oc22, oc25, odac, omat, omc, omol) it is the only one
  trained on molecular adsorbates on metal slabs, which is exactly this geometry. Disclosure:
  OC20's adsorbates are small molecules, not 10-residue peptides, so adsorbate size is an
  extrapolation.
* Estimator: per peptide, E_ads = min over all conformers x placements of
      E(complex) - E(slab, relaxed once) - E(conformer k, same cell)
  and the FM predicts the peptide with the **lower (more negative) E_ads** as the stronger
  binder. Fixed in V9-5, before any energy was computed, and not revisited since.
* Convergence recorded per relaxation: step count and final fmax (hard rule 4). No cap is
  assumed generous; `hit_cap` is reported per evaluation.
* Validity check (hard rule 3) runs on every complex before it reaches the FM.

Two modes, both pre-registered (`v9/fm/PREREG_3_DECISIONS.md`):

* ``--mode rigid`` (rung 1, V9-7). The slab is relaxed **once** and held rigid; every complex
  and every conformer reference is a **single point**. Relaxing the isolated conformer would be
  a relaxation, which rung 1 forbids, so the conformer term is a single point too. That term is
  constant across the placements of a given conformer and so cannot change which placement is
  the minimum; it does affect comparison across conformers, and it is recorded per conformer.
* ``--mode relax`` (rung 2, V9-8, and V9-5's original protocol). Converged LBFGS, fmax 0.05,
  step cap reported. Per David's three requirements, every evaluation records the **final**
  energy and the **minimum energy over the trajectory**, and each peptide records its running
  minimum against evaluation count and whether that minimum was still falling at the last
  evaluation.

``--resume`` keeps peptides already present in the output JSON. The first launch of V9-7's
conformer step died with an unexplained CUDA out-of-memory and an identical relaunch succeeded
(V9-X5), so a long run must not depend on never being interrupted.

Usage: python fm_run.py CONFDIR OUTDIR --mode rigid|relax [--placements N] [--pids ...] [--resume]
"""
import argparse, json, os, time

import numpy as np

SOBOL_SEED = 20261019
GAP_A = 2.6               # nominal peptide-surface gap
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


def still_falling(run):
    """Was the running minimum still falling at the last evaluation? (David's requirement 3)"""
    return bool(len(run) >= 2 and run[-1] < run[-2] - 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("confdir"); ap.add_argument("outdir")
    ap.add_argument("--mode", choices=("rigid", "relax"), required=True)
    ap.add_argument("--pids", default=""); ap.add_argument("--placements", type=int, default=10)
    ap.add_argument("--max-steps", type=int, default=1000); ap.add_argument("--fmax", type=float, default=0.05)
    ap.add_argument("--conformers", type=int, default=3)
    ap.add_argument("--out-name", default="fm_dev.json")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    rigid = a.mode == "rigid"
    cd = os.path.expanduser(a.confdir); od = os.path.expanduser(a.outdir)
    os.makedirs(od, exist_ok=True)
    outp = os.path.join(od, a.out_name)
    man = json.load(open(os.path.join(cd, "conformers.json")))
    pids = a.pids.split(",") if a.pids else [e["pid"] for e in man["peptides"]]
    cls = {e["pid"]: e["cls"] for e in man["peptides"]}

    results = {}
    if a.resume and os.path.exists(outp):
        results = json.load(open(outp)).get("results", {})
        pids = [p for p in pids if p not in results]
        print(f"resuming: {len(results)} peptides already done, {len(pids)} to go", flush=True)

    from ase import Atoms
    from ase.constraints import FixAtoms
    from ase.optimize import LBFGS
    from fairchem.core import FAIRChemCalculator, pretrained_mlip
    pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
    calc = FAIRChemCalculator(pu, task_name="oc20")

    S, fixed = slab()
    cell = S.cell.array
    t = time.time()
    S.calc = calc
    optS = LBFGS(S, logfile=None); optS.run(fmax=a.fmax, steps=a.max_steps)
    e_slab = float(S.get_potential_energy())
    slab_pos = S.get_positions()
    ztop = slab_pos[:, 2].max()
    slab_steps = optS.get_number_of_steps()
    header = dict(mode=a.mode, n_slab=len(S), n_fixed=int(fixed.sum()),
                  cell=[round(x, 3) for x in S.cell.lengths()],
                  e_slab_eV=round(e_slab, 4), slab_steps=slab_steps,
                  slab_hit_cap=slab_steps >= a.max_steps,
                  slab_fmax=round(float(np.abs(S.get_forces()[~fixed]).max()), 4),
                  t_slab_s=round(time.time() - t, 1), head="oc20", model="uma-s-1p2",
                  sobol_seed=SOBOL_SEED, gap_A=GAP_A, dz_range=list(DZ_RANGE),
                  placements=a.placements, conformers=a.conformers,
                  max_steps=a.max_steps, fmax_target=a.fmax)
    print(json.dumps(header), flush=True)

    tab = placements(a.placements)
    n_sp = n_relax = 0
    t_sp = t_relax = 0.0
    for pid in pids:
        sym = list(np.load(os.path.join(cd, f"{pid}_sym.npy")))
        rows, t_pep = [], time.time()
        e_conf, conf_meta = {}, {}
        for k in range(a.conformers):
            f = os.path.join(cd, f"{pid}_c{k}.npy")
            if not os.path.exists(f):
                continue
            base = lie_flat(np.load(f))
            # reference energy: this conformer alone in the same cell, same head
            at = Atoms(symbols=sym, positions=base - base.min(0) + 6.0, cell=cell, pbc=True)
            at.calc = calc
            t0 = time.time()
            if rigid:
                e_conf[k] = float(at.get_potential_energy())
                conf_meta[k] = dict(single_point=True)
                n_sp += 1; t_sp += time.time() - t0
            else:
                o = LBFGS(at, logfile=None); o.run(fmax=a.fmax, steps=a.max_steps)
                e_conf[k] = float(at.get_potential_energy())
                ns = o.get_number_of_steps()
                conf_meta[k] = dict(single_point=False, steps=ns, hit_cap=ns >= a.max_steps,
                                    fmax=round(float(np.abs(at.get_forces()).max()), 4))
                n_relax += 1; t_relax += time.time() - t0
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
                rec = dict(k=k, j=j, refused=False, min_heavy_pair_A=round(mn, 4))
                if rigid:
                    e = float(cx.get_potential_energy())
                    rec.update(e_complex_eV=round(e, 4), e_complex_traj_min_eV=round(e, 4),
                               steps=0, hit_cap=False, single_point=True)
                    n_sp += 1; t_sp += time.time() - t0
                else:
                    # David's requirement 1: keep the minimum energy along the trajectory as
                    # well as the final energy. LBFGS does not guarantee a monotonic path.
                    traj = []
                    opt = LBFGS(cx, logfile=None)
                    opt.attach(lambda c=cx, tr=traj: tr.append(float(c.get_potential_energy())))
                    opt.run(fmax=a.fmax, steps=a.max_steps)
                    ns = opt.get_number_of_steps()
                    e = float(cx.get_potential_energy())
                    rec.update(e_complex_eV=round(e, 4),
                               e_complex_traj_min_eV=round(min(traj) if traj else e, 4),
                               steps=ns, hit_cap=ns >= a.max_steps, single_point=False,
                               fmax=round(float(np.abs(cx.get_forces()[~m]).max()), 4),
                               n_traj_points=len(traj),
                               final_is_traj_min=bool(traj and abs(e - min(traj)) < 1e-9))
                    n_relax += 1; t_relax += time.time() - t0
                rec["e_conf_eV"] = round(e_conf[k], 4)
                rec["e_ads_eV"] = round(rec["e_complex_eV"] - e_slab - e_conf[k], 4)
                rec["e_ads_traj_min_eV"] = round(rec["e_complex_traj_min_eV"] - e_slab - e_conf[k], 4)
                rec["t_s"] = round(time.time() - t0, 2)
                rows.append(rec)
        ok = [r for r in rows if not r["refused"]]
        ea = [r["e_ads_eV"] for r in ok]
        run = list(np.minimum.accumulate(ea)) if ea else []
        r = dict(pid=pid, cls=cls[pid], n_atoms_peptide=len(sym),
                 n_eval=len(ok), n_refused=len(rows) - len(ok),
                 e_ads_min_eV=(min(ea) if ea else None),
                 e_ads_min_traj_eV=(min(r_["e_ads_traj_min_eV"] for r_ in ok) if ok else None),
                 e_ads_mean_eV=(float(np.mean(ea)) if ea else None),
                 e_ads_sd_eV=(float(np.std(ea, ddof=1)) if len(ea) > 1 else None),
                 e_ads_range_eV=([min(ea), max(ea)] if ea else None),
                 running_min_eV=[round(float(x), 4) for x in run],
                 still_falling=still_falling(run),
                 n_hit_cap=sum(1 for x in ok if x.get("hit_cap")),
                 e_conf_eV={str(k): round(v, 4) for k, v in e_conf.items()},
                 conformer_meta={str(k): v for k, v in conf_meta.items()},
                 t_peptide_s=round(time.time() - t_pep, 1), rows=rows)
        results[pid] = r
        print(f"{pid} {cls[pid]:6s} evals {r['n_eval']:3d} refused {r['n_refused']:2d} "
              f"E_ads_min {r['e_ads_min_eV']} eV  sd {r['e_ads_sd_eV'] and round(r['e_ads_sd_eV'],3)} "
              f"{r['t_peptide_s']}s cap {r['n_hit_cap']} "
              f"{'STILL FALLING' if r['still_falling'] else ''}", flush=True)
        header.update(n_single_points=n_sp, t_single_points_s=round(t_sp, 1),
                      n_relaxations=n_relax, t_relaxations_s=round(t_relax, 1),
                      t_per_single_point_s=(round(t_sp / n_sp, 4) if n_sp else None),
                      t_per_relaxation_s=(round(t_relax / n_relax, 2) if n_relax else None))
        json.dump(dict(**header, results=results), open(outp, "w"), indent=1)
    print(f"\ndone: {len(results)} peptides; {n_sp} single points "
          f"({t_sp/n_sp:.4f}s each)" if n_sp else "", flush=True)
    if n_relax:
        print(f"{n_relax} relaxations ({t_relax/n_relax:.1f}s each)")


if __name__ == "__main__":
    main()
