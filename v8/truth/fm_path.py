"""The FM path for one unit on one substrate: ESMFold geometry, UMA registry energies.

Independent of the truth path (V8-1): the fragment geometry comes from ESMFold rather
than the published model, and UMA relaxes it on the bare slab in vacuum, which is the
source of the FM error that risk R3 expects.

AdsorbML-style: 30 rigid placements per registry, each relaxed with the slab held fixed;
the minimum per registry is kept. theta_match is the lower registry and the margin is
E(theta0 + 30) - E(theta0), so a positive margin means the matched registry is theta0.

Dev units only before the freeze (addendum D item 3 Track 1, amendment A item 4).

Usage:
  python fm_path.py --unit HRm-ea --cation K --out ~/v8_data/fm/<tag> [--placements 30]
      [--steps 60] [--task omol] [--benchmark]
"""
import argparse, json, os, time

import numpy as np

EV_KJ = 96.485332  # kJ/mol per eV


def esmfold_geometry(seq, out_pdb):
    """Fold the repeat-unit sequence once and cache the PDB."""
    if os.path.exists(out_pdb):
        return out_pdb
    import torch
    from transformers import AutoTokenizer, EsmForProteinFolding
    tok = AutoTokenizer.from_pretrained("facebook/esmfold_v1")
    m = EsmForProteinFolding.from_pretrained("facebook/esmfold_v1").cuda().eval()
    m.esm = m.esm.half()
    with torch.no_grad():
        out = m(**tok([seq], return_tensors="pt", add_special_tokens=False).to("cuda"))
    plddt = float(out["plddt"][0, :, 1].mean())
    open(out_pdb, "w").write(m.output_to_pdb(out)[0])
    json.dump(dict(mean_plddt=plddt, n_res=len(seq)), open(out_pdb + ".json", "w"))
    del m
    torch.cuda.empty_cache()
    return out_pdb


def load_atoms(slab_pdb, frag_pdb, positions):
    """ASE Atoms for the complex, with the slab first and the fragment at `positions`."""
    from ase import Atoms
    from ase.constraints import FixAtoms
    import gemmi
    sl = gemmi.read_structure(slab_pdb)
    s_sym, s_xyz = [], []
    for ch in sl[0]:
        for r in ch:
            for a in r:
                s_sym.append(a.element.name)
                s_xyz.append([a.pos.x, a.pos.y, a.pos.z])
    fr = gemmi.read_structure(frag_pdb)
    fr.remove_hydrogens()
    f_sym = []
    for ch in fr[0]:
        for r in ch:
            for a in r:
                f_sym.append(a.element.name)
    cell = sl.cell
    at = Atoms(s_sym + f_sym, positions=np.vstack([np.array(s_xyz), positions]),
               cell=[cell.a, cell.b, cell.c, cell.alpha, cell.beta, cell.gamma], pbc=True)
    at.set_constraint(FixAtoms(indices=list(range(len(s_sym)))))
    return at, len(s_sym), len(f_sym)


def relax(atoms, calc, steps, fmax=0.1):
    from ase.optimize import LBFGS
    atoms.calc = calc
    opt = LBFGS(atoms, logfile=None)
    opt.run(fmax=fmax, steps=steps)
    return float(atoms.get_potential_energy()), opt.get_number_of_steps()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--unit", required=True); p.add_argument("--cation", required=True, choices=["K", "NA"])
    p.add_argument("--out", required=True); p.add_argument("--placements", type=int, default=30)
    p.add_argument("--steps", type=int, default=60); p.add_argument("--task", default="omol")
    p.add_argument("--benchmark", action="store_true"); p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    import place as placemod
    units = json.load(open(os.path.expanduser("~/v8_data/units.json")))
    unit = next(v for v in units.values() if v["hash_id"] == a.unit)
    frag_pdb = os.path.expanduser(f"~/v8_data/fm/esmfold_{a.unit}.pdb")
    os.makedirs(os.path.dirname(frag_pdb), exist_ok=True)
    esmfold_geometry(unit["unit"], frag_pdb)
    slab_pdb = os.path.expanduser(f"~/v8_data/slabs/slab_{a.cation}.pdb")

    from fairchem.core import FAIRChemCalculator, pretrained_mlip
    pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
    calc = FAIRChemCalculator(pu, task_name=a.task)

    # theta0 from the ESMFold geometry, by the same geometric criterion as the truth path
    theta0, _, _, _, _ = placemod.scan_theta0(frag_pdb, slab_pdb)

    if a.benchmark:
        pos, _ = placemod.place(frag_pdb, slab_pdb, 0, 0, theta0=theta0)
        at, ns, nf = load_atoms(slab_pdb, frag_pdb, pos)
        at.calc = calc
        t = time.time(); e = at.get_potential_energy(); t1 = time.time() - t
        t = time.time(); at.get_forces(); t2 = time.time() - t
        print(json.dumps(dict(n_atoms=len(at), n_slab=ns, n_frag=nf, task=a.task,
                              first_energy_s=round(t1, 2), force_call_s=round(t2, 2), e_ev=e)))
        return

    rng = np.random.default_rng(a.seed)
    res = {}
    for reg in (0, 1):
        best, series = None, []
        for k in range(a.placements):
            pos, _ = placemod.place(frag_pdb, slab_pdb, reg, k % 3, theta0=theta0)
            # jitter the rigid placement: in-plane shift and a small rotation about the normal
            sh = rng.uniform(-2.5, 2.5, 2)
            ang = np.radians(rng.uniform(-6, 6))
            c = pos.mean(0)
            R = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1.0]])
            pos = (pos - c) @ R.T + c
            pos[:, :2] += sh
            pos[:, 2] += rng.uniform(-0.3, 0.6)
            at, ns, nf = load_atoms(slab_pdb, frag_pdb, pos)
            e, nst = relax(at, calc, a.steps)
            series.append(dict(k=k, e_ev=e, steps=nst))
            if best is None or e < best:
                best = e
            print(f"  reg {reg} placement {k:2d}: {e:.4f} eV ({nst} steps, {time.time() - t0:.0f} s)", flush=True)
        res[reg] = dict(min_ev=best, series=series)

    # references for the adsorption energy
    pos, _ = placemod.place(frag_pdb, slab_pdb, 0, 0, theta0=theta0)
    at, ns, nf = load_atoms(slab_pdb, frag_pdb, pos)
    from ase import Atoms
    slab_only = at[:ns]; slab_only.calc = calc
    frag_only = at[ns:]; frag_only.set_constraint(); frag_only.calc = calc
    e_slab = float(slab_only.get_potential_energy())
    e_frag = float(frag_only.get_potential_energy())

    margin_ev = res[1]["min_ev"] - res[0]["min_ev"]
    spread = [np.std([s["e_ev"] for s in res[r]["series"]], ddof=1) for r in (0, 1)]
    out = dict(unit=a.unit, cation=a.cation, task=a.task, theta0_deg=theta0,
               placements=a.placements, steps=a.steps, n_atoms=ns + nf,
               e_min_reg0_ev=res[0]["min_ev"], e_min_reg1_ev=res[1]["min_ev"],
               e_slab_ev=e_slab, e_frag_ev=e_frag,
               e_ads_reg0_ev=res[0]["min_ev"] - e_slab - e_frag,
               e_ads_reg1_ev=res[1]["min_ev"] - e_slab - e_frag,
               margin_ev=margin_ev, margin_kj=margin_ev * EV_KJ,
               theta_match_deg=theta0 if margin_ev > 0 else (theta0 + 30.0) % 360,
               placement_spread_ev=spread, wall_s=time.time() - t0,
               series={str(k): v["series"] for k, v in res.items()})
    json.dump(out, open(os.path.join(a.out, "fm.json"), "w"), indent=1)
    print(f"DONE {a.unit}/{a.cation} margin {margin_ev:+.4f} eV ({margin_ev * EV_KJ:+.1f} kJ/mol), "
          f"theta_match {out['theta_match_deg']:.1f} deg, wall {(time.time() - t0) / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
