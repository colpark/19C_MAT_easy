"""Reference (IFF) registry energies by rigid placements without water.

Amendment E item 4. For one (unit, cation) system: both registries, 30 rigid placements
each from the shared quasi-random table, each minimised with the mineral framework fixed
and the surface cations plus the fragment mobile. No water, no dynamics. The minimum per
registry is kept, and the margin follows amendment E item 2.

The interaction energy uses the same decomposition as the solvated runs
(v8/OPEN_QUESTIONS.md Q3): at the minimised geometry,
E_int = E(fragment + slab) - E(fragment) - E(slab), each a single point in the same
periodic box with identical PME settings.

The reference carries no explicit water. Interfacial water is known to matter at this
interface, so this is a self-consistent citable reference, not a claim about experiment
(amendment E item 4).

Usage:
  python run_ref.py --unit HRm-ea --cation K --out ~/v8_data/ref/<tag> [--placements 30]
"""
import argparse, json, os, time

import numpy as np
import openmm as mm
import openmm.app as app
import openmm.unit as u

import place as placemod
import placements as plc
from run_truth import exclude_frozen_pairs


class ConvergenceReporter(mm.MinimizationReporter):
    """Counts minimiser iterations and keeps the last gradient norm (amendment F item 4.3)."""

    def __init__(self):
        super().__init__()
        self.iterations = 0
        self.grad_norm = float("nan")
        self.grad_rms = float("nan")

    def report(self, iteration, x, grad, args):
        self.iterations = int(iteration)
        g = np.asarray(grad, dtype=float)
        self.grad_norm = float(np.sqrt((g * g).sum()))
        self.grad_rms = float(np.sqrt((g * g).mean()))   # what OpenMM's tolerance is on
        return False

BOX_Z = 7.0


def build(unit, cation, platform_name, frag_pdb=None, slab_tag=""):
    frag_pdb = frag_pdb or os.path.expanduser(f"~/v8_data/frags/{unit}.pdb")
    slab_pdb = os.path.expanduser(f"~/v8_data/slabs/slab_{cation}{slab_tag}.pdb")
    slab_xml = os.path.expanduser(f"~/v8_data/slabs/slab_{cation}{slab_tag}.xml")
    here = os.path.dirname(os.path.abspath(__file__))
    app.Modeller.loadHydrogenDefinitions(os.path.join(here, "caps_hydrogens.xml"))
    ff = app.ForceField("charmm36.xml", "charmm36/water.xml",
                        os.path.join(here, "caps_charmm36.xml"), slab_xml)
    fr = app.PDBFile(frag_pdb)
    sl = app.PDBFile(slab_pdb)

    pos0, theta0 = placemod.place(frag_pdb, slab_pdb, 0, 0)
    mod = app.Modeller(fr.topology, pos0 * 0.1 * u.nanometer)
    mod.addHydrogens(ff)
    n_frag = mod.topology.getNumAtoms()
    mod.add(sl.topology, sl.positions)
    n_cx = mod.topology.getNumAtoms()
    cell = sl.topology.getUnitCellDimensions()
    bx = mm.Vec3(cell[0].value_in_unit(u.nanometer), cell[1].value_in_unit(u.nanometer), BOX_Z) * u.nanometer
    mod.topology.setUnitCellDimensions(bx)

    atoms = list(mod.topology.atoms())
    frozen = [i for i in range(n_frag, n_cx)
              if atoms[i].element is not None and atoms[i].element.symbol not in ("K", "Na")]

    plat = mm.Platform.getPlatformByName(platform_name)
    # Energy-evaluation contexts: no frozen-pair exclusions in ANY of the three, so the
    # slab's large self-energy cancels exactly in E(cx) - E(fr) - E(sl). This is the same
    # convention the solvated runs used (Q3), which keeps the two protocols comparable.
    contexts = {}
    for name, (kf, ks) in dict(cx=(True, True), fr=(True, False), sl=(False, True)).items():
        m = app.Modeller(mod.topology, mod.positions)
        drop = [a for i, a in enumerate(list(m.topology.atoms()))
                if (i < n_frag and not kf) or (n_frag <= i < n_cx and not ks)]
        m.delete(drop)
        m.topology.setUnitCellDimensions(bx)
        s = ff.createSystem(m.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.2 * u.nanometer,
                            constraints=None, rigidWater=False)
        contexts[name] = mm.Context(s, mm.VerletIntegrator(1 * u.femtosecond), plat)
    # A separate complex system for minimisation only: framework frozen, and frozen-frozen
    # pairs excluded so single-precision force noise cannot drive the minimiser (V8-E11).
    min_sys = ff.createSystem(mod.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.2 * u.nanometer,
                              constraints=None, rigidWater=False)
    for i in frozen:
        min_sys.setParticleMass(i, 0.0)
    n_excl, _ = exclude_frozen_pairs(min_sys, frozen, np.array(mod.positions.value_in_unit(u.nanometer)))
    lat_a = np.array([cell[0].value_in_unit(u.angstrom), 0.0])
    lat_b = np.array([0.0, cell[1].value_in_unit(u.angstrom)])
    return dict(ff=ff, mod=mod, contexts=contexts, min_sys=min_sys, n_frag=n_frag, n_cx=n_cx,
                theta0=theta0, frozen=len(frozen), n_excl=n_excl, lat_a=lat_a, lat_b=lat_b,
                frag_pdb=frag_pdb, slab_pdb=slab_pdb)


def e_int(ctx, pos_cx_nm, n_frag):
    out = {}
    for name, sl in dict(cx=slice(None), fr=slice(0, n_frag), sl=slice(n_frag, None)).items():
        ctx[name].setPositions(pos_cx_nm[sl])
        out[name] = ctx[name].getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
    return out["cx"] - out["fr"] - out["sl"], out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--unit", required=True); p.add_argument("--cation", required=True, choices=["K", "NA"])
    p.add_argument("--out", required=True); p.add_argument("--placements", type=int, default=plc.N_PLACEMENTS)
    p.add_argument("--platform", default="CUDA"); p.add_argument("--max-iter", type=int, default=20000)
    p.add_argument("--frag-pdb", default=None, help="override the structure (e.g. a rod)")
    p.add_argument("--slab-tag", default="", help='slab suffix, e.g. "_rod"')
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    b = build(a.unit, a.cation, a.platform, a.frag_pdb, a.slab_tag)
    table = plc.placement_table(a.placements)
    slab_pos = np.array(b["mod"].positions.value_in_unit(u.angstrom))[b["n_frag"]:b["n_cx"]]

    meta = dict(unit=a.unit, cation=a.cation, theta0_deg=b["theta0"], protocol="rigid placements, no water",
                n_atoms=b["n_cx"], n_frag=b["n_frag"], n_frozen=b["frozen"], n_excl=b["n_excl"],
                placements=a.placements, placement_sequence=plc.describe(a.placements),
                platform=a.platform, max_iter=a.max_iter)
    print(json.dumps(meta), flush=True)

    sim_ctx = mm.Context(b["min_sys"], mm.VerletIntegrator(1 * u.femtosecond),
                         mm.Platform.getPlatformByName(a.platform))

    results = {}
    for reg in (0, 1):
        base, _ = placemod.place(b["frag_pdb"], b["slab_pdb"], reg, 0, theta0=b["theta0"])
        # base has only heavy atoms; re-derive the hydrogenated fragment by rigid transform
        rows = []
        for k in range(a.placements):
            fpos = plc.apply_placement(base, table[k], b["lat_a"], b["lat_b"])
            # map the heavy-atom placement onto the hydrogenated fragment by rigid fit
            full = hydrogenate_like(b, fpos)
            pos = np.vstack([full, slab_pos]) * 0.1  # nm
            sim_ctx.setPositions(pos)
            e_before, _ = e_int(b["contexts"], np.asarray(pos), b["n_frag"])
            rep = ConvergenceReporter()
            mm.LocalEnergyMinimizer.minimize(sim_ctx, 1.0, a.max_iter, rep)
            pm = sim_ctx.getState(getPositions=True).getPositions(asNumpy=True).value_in_unit(u.nanometer)
            ei, _ = e_int(b["contexts"], pm, b["n_frag"])
            rows.append(dict(k=k, e_int=ei, e_int_before_min=e_before,
                             iterations=rep.iterations, grad_norm=rep.grad_norm,
                             grad_rms=rep.grad_rms,
                             hit_cap=bool(rep.iterations >= a.max_iter - 1),
                             frac_a=float(table[k][0]), frac_b=float(table[k][1]),
                             rot_deg=float(table[k][2]), dz=float(table[k][3])))
            if (k + 1) % 10 == 0:
                print(f"  reg {reg}: {k + 1}/{a.placements} placements, best {min(r['e_int'] for r in rows):.1f} kJ/mol, "
                      f"{time.time() - t0:.0f} s", flush=True)
        results[reg] = rows

    meta["series"] = {str(k): v for k, v in results.items()}
    meta["e_min"] = {str(k): min(r["e_int"] for r in v) for k, v in results.items()}
    allrows = [r for v in results.values() for r in v]
    meta["max_iter_cap"] = a.max_iter
    meta["n_hit_cap"] = sum(r["hit_cap"] for r in allrows)
    meta["iterations"] = dict(min=min(r["iterations"] for r in allrows),
                              median=float(np.median([r["iterations"] for r in allrows])),
                              max=max(r["iterations"] for r in allrows))
    meta["grad_norm"] = dict(min=float(np.nanmin([r["grad_norm"] for r in allrows])),
                             median=float(np.nanmedian([r["grad_norm"] for r in allrows])),
                             max=float(np.nanmax([r["grad_norm"] for r in allrows])))
    meta["grad_rms"] = dict(min=float(np.nanmin([r["grad_rms"] for r in allrows])),
                            median=float(np.nanmedian([r["grad_rms"] for r in allrows])),
                            max=float(np.nanmax([r["grad_rms"] for r in allrows])))
    meta["wall_s"] = time.time() - t0
    json.dump(meta, open(os.path.join(a.out, "ref.json"), "w"), indent=1)
    m = meta["e_min"]["1"] - meta["e_min"]["0"]
    print(f"DONE {a.unit}/{a.cation}: E_min(theta0) {meta['e_min']['0']:.1f}, "
          f"E_min(theta0+30) {meta['e_min']['1']:.1f}, margin {m:+.1f} kJ/mol; "
          f"wall {meta['wall_s'] / 60:.1f} min", flush=True)


def hydrogenate_like(b, heavy_pos):
    """Place the hydrogenated fragment given new heavy-atom positions (rigid-body move).

    The placement is a rigid transform of the whole fragment, so fit the transform from
    the heavy atoms of the reference pose and apply it to every fragment atom, hydrogens
    included. That keeps the ESMFold-free internal geometry exactly as published.
    """
    ref_full = np.array(b["mod"].positions.value_in_unit(u.angstrom))[:b["n_frag"]]
    heavy_idx = b.setdefault("_heavy_idx", [i for i, at in enumerate(list(b["mod"].topology.atoms())[:b["n_frag"]])
                                            if at.element is not None and at.element.symbol != "H"])
    ref_heavy = ref_full[heavy_idx]
    A = ref_heavy - ref_heavy.mean(0)
    B = heavy_pos - heavy_pos.mean(0)
    U, _, Vt = np.linalg.svd(A.T @ B)
    d = np.sign(np.linalg.det(U @ Vt))
    R = U @ np.diag([1.0, 1.0, d]) @ Vt
    return (ref_full - ref_heavy.mean(0)) @ R + heavy_pos.mean(0)


if __name__ == "__main__":
    main()
