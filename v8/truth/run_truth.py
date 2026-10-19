"""One IFF truth run: a capped fragment on a muscovite slab in one registry and placement.

Protocol (V8-1, amendment B item 4): IFF surface model with full charges, CHARMM36 for
the fragment, TIP3P water, 100 mM salt of the surface cation. Minimise, equilibrate,
then NVT with the fragment backbone restrained to its registry. The interaction energy
is evaluated every 10 ps as E(fragment+slab) - E(fragment) - E(slab), each a single
point in the same periodic box with identical PME settings, on solvent-stripped
coordinates (v8/OPEN_QUESTIONS.md Q3).

Storage (addendum D): energies every 10 ps plus the final frame only.

Usage:
  python run_truth.py --unit HRm-ea --cation K --registry 0 --placement 0 \
      --out ~/v8_data/runs/<tag> [--ns 2.0] [--platform CUDA]
"""
import argparse, json, os, time

import numpy as np
import openmm as mm
import openmm.app as app
import openmm.unit as u

import place as placemod

BOX_Z = 7.0            # nm, total box height (slab 0-1 nm, water above and, through PBC, below)
RESTRAINT = 2092.0     # kJ/mol/nm^2 = 5 kcal/mol/A^2 on backbone N, CA, C
CHECK_PS = 10.0        # interaction-energy checkpoint interval
EQ_PS = 100.0          # equilibration before production


def build(unit, cation, registry, placement, platform_name):
    frag_pdb = os.path.expanduser(f"~/v8_data/frags/{unit}.pdb")
    slab_pdb = os.path.expanduser(f"~/v8_data/slabs/slab_{cation}.pdb")
    slab_xml = os.path.expanduser(f"~/v8_data/slabs/slab_{cation}.xml")

    pos_frag, theta0 = placemod.place(frag_pdb, slab_pdb, registry, placement)
    fr = app.PDBFile(frag_pdb)
    sl = app.PDBFile(slab_pdb)
    here = os.path.dirname(os.path.abspath(__file__))
    app.Modeller.loadHydrogenDefinitions(os.path.join(here, "caps_hydrogens.xml"))
    ff = app.ForceField("charmm36.xml", "charmm36/water.xml",
                        os.path.join(here, "caps_charmm36.xml"), slab_xml)

    # fragment first (hydrogens added on it alone), then the slab, then solvent
    mod = app.Modeller(fr.topology, pos_frag * 0.1 * u.nanometer)
    mod.addHydrogens(ff)
    n_frag = mod.topology.getNumAtoms()
    mod.add(sl.topology, sl.positions)
    n_cx = mod.topology.getNumAtoms()
    n_slab = n_cx - n_frag

    cell = sl.topology.getUnitCellDimensions()
    box = mm.Vec3(cell[0].value_in_unit(u.nanometer), cell[1].value_in_unit(u.nanometer), BOX_Z) * u.nanometer
    mod.topology.setUnitCellDimensions(box)

    # complex / fragment / slab systems for the interaction energy, same box, same PME
    def sub(keep_frag, keep_slab):
        m = app.Modeller(mod.topology, mod.positions)
        atoms = list(m.topology.atoms())
        drop = [a for i, a in enumerate(atoms)
                if (i < n_frag and not keep_frag) or (n_frag <= i < n_cx and not keep_slab)]
        m.delete(drop)
        m.topology.setUnitCellDimensions(box)
        return m

    def mk(m):
        s = ff.createSystem(m.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.2 * u.nanometer,
                            constraints=None, rigidWater=False)
        return s

    ie = {}
    for name, (kf, ks) in dict(cx=(True, True), fr=(True, False), sl=(False, True)).items():
        m = sub(kf, ks)
        s = mk(m)
        plat = mm.Platform.getPlatformByName(platform_name)
        ie[name] = mm.Context(s, mm.VerletIntegrator(1 * u.femtosecond), plat)

    # production system: solvate
    mod.addSolvent(ff, model="tip3p", boxVectors=(mm.Vec3(box[0].value_in_unit(u.nanometer), 0, 0) * u.nanometer,
                                                  mm.Vec3(0, box[1].value_in_unit(u.nanometer), 0) * u.nanometer,
                                                  mm.Vec3(0, 0, BOX_Z) * u.nanometer),
                   positiveIon=("K+" if cation == "K" else "Na+"), negativeIon="Cl-",
                   ionicStrength=0.1 * u.molar, neutralize=True)
    system = ff.createSystem(mod.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.2 * u.nanometer,
                             constraints=app.HBonds, rigidWater=True)

    atoms = list(mod.topology.atoms())
    # freeze the mineral framework; surface cations stay mobile (Q2)
    frozen = 0
    for i in range(n_frag, n_cx):
        if atoms[i].element is not None and atoms[i].element.symbol not in ("K", "Na"):
            system.setParticleMass(i, 0.0)
            frozen += 1
    # restrain the fragment backbone to its registry
    rest = mm.CustomExternalForce("k*periodicdistance(x,y,z,x0,y0,z0)^2")
    rest.addGlobalParameter("k", RESTRAINT * u.kilojoule_per_mole / u.nanometer ** 2)
    for p in ("x0", "y0", "z0"):
        rest.addPerParticleParameter(p)
    nres = 0
    for i in range(n_frag):
        a = atoms[i]
        if a.name in ("N", "CA", "C") and a.residue.name not in ("ACE", "NME"):
            rest.addParticle(i, mod.positions[i].value_in_unit(u.nanometer))
            nres += 1
    system.addForce(rest)

    return dict(ff=ff, mod=mod, system=system, ie=ie, n_frag=n_frag, n_slab=n_slab, n_cx=n_cx,
                theta0=theta0, frozen=frozen, n_restrained=nres, box=box)


def e_int(ie, pos_cx, n_frag):
    """kJ/mol interaction energy for solvent-stripped coordinates."""
    out = {}
    for name, sl in dict(cx=slice(None), fr=slice(0, n_frag), sl=slice(n_frag, None)).items():
        ie[name].setPositions(pos_cx[sl])
        out[name] = ie[name].getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
    return out["cx"] - out["fr"] - out["sl"], out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--unit", required=True); p.add_argument("--cation", required=True, choices=["K", "NA"])
    p.add_argument("--registry", type=int, required=True); p.add_argument("--placement", type=int, required=True)
    p.add_argument("--out", required=True); p.add_argument("--ns", type=float, default=2.0)
    p.add_argument("--platform", default="CUDA"); p.add_argument("--seed", type=int, default=0)
    a = p.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    b = build(a.unit, a.cation, a.registry, a.placement, a.platform)
    system, mod = b["system"], b["mod"]
    integ = mm.LangevinMiddleIntegrator(300 * u.kelvin, 1.0 / u.picosecond, 2.0 * u.femtosecond)
    integ.setRandomNumberSeed(a.seed or 1)
    sim = app.Simulation(mod.topology, system, integ, mm.Platform.getPlatformByName(a.platform))
    sim.context.setPositions(mod.positions)
    meta = dict(unit=a.unit, cation=a.cation, registry=a.registry, placement=a.placement,
                theta0_deg=b["theta0"], n_atoms=system.getNumParticles(), n_frag=b["n_frag"],
                n_slab=b["n_slab"], n_frozen=b["frozen"], n_restrained=b["n_restrained"],
                ns=a.ns, seed=a.seed, platform=a.platform,
                box_nm=[b["box"][i].value_in_unit(u.nanometer) for i in range(3)])
    print(json.dumps(meta), flush=True)

    sim.minimizeEnergy(maxIterations=5000)
    e_min = sim.context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)
    sim.context.setVelocitiesToTemperature(300 * u.kelvin, a.seed or 1)
    sim.step(int(EQ_PS / 0.002))
    t_eq = time.time()
    print(f"minimised {e_min:.1f} kJ/mol; equilibrated {EQ_PS:.0f} ps in {t_eq - t0:.0f} s", flush=True)

    n_check = int(round(a.ns * 1000 / CHECK_PS))
    steps = int(CHECK_PS / 0.002)
    series = []
    for k in range(n_check):
        sim.step(steps)
        st = sim.context.getState(getPositions=True, getEnergy=True)
        pos = st.getPositions(asNumpy=True)[:b["n_cx"]]
        ei, parts = e_int(b["ie"], pos, b["n_frag"])
        series.append(dict(ps=(k + 1) * CHECK_PS, e_int=ei,
                           e_total=st.getPotentialEnergy().value_in_unit(u.kilojoule_per_mole)))
        if (k + 1) % 20 == 0:
            ns_day = ((k + 1) * CHECK_PS / 1000) / ((time.time() - t_eq) / 86400)
            print(f"  {(k + 1) * CHECK_PS:6.0f} ps  E_int {ei:9.1f} kJ/mol  {ns_day:.1f} ns/day", flush=True)

    app.PDBFile.writeFile(sim.topology, sim.context.getState(getPositions=True).getPositions(),
                          open(os.path.join(a.out, "final.pdb"), "w"))
    wall = time.time() - t0
    meta.update(e_min=e_min, wall_s=wall,
                ns_per_day=(a.ns) / ((time.time() - t_eq) / 86400), series=series)
    json.dump(meta, open(os.path.join(a.out, "run.json"), "w"), indent=1)
    half = [s["e_int"] for s in series[len(series) // 2:]]
    print(f"DONE E_int(last half) {np.mean(half):.2f} +- {np.std(half, ddof=1) / np.sqrt(len(half)):.2f} "
          f"kJ/mol over {len(half)} checkpoints; wall {wall / 60:.1f} min", flush=True)


if __name__ == "__main__":
    main()
