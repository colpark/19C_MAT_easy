"""Step 3: scope one 18-repeat rod under the step 2 reference protocol, then stop.

Amendment E item 5. Builds one rod on one slab, times the system build and a single
placement minimisation, and reports atom count, wall time per placement, peak memory and
the projected wall time for a full set across the two usable GPUs. Starts no production
set and writes no energies that any gate would read.

Usage: python scope_rod.py --rod HRm-ea_18rep --cation K [--placements 1]
"""
import argparse, json, os, resource, subprocess, time

import numpy as np
import openmm as mm
import openmm.app as app
import openmm.unit as u

import place as placemod
import placements as plc
from run_truth import exclude_frozen_pairs

BOX_Z = 9.0
GAP = 3.2


def gpu_mem_mib():
    try:
        q = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=20)
        me = str(os.getpid())
        for line in q.stdout.strip().splitlines():
            f = [x.strip() for x in line.split(",")]
            if len(f) >= 2 and f[0] == me:
                return float(f[1])
    except Exception:
        pass
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rod", default="HRm-ea_18rep"); ap.add_argument("--cation", default="K")
    ap.add_argument("--placements", type=int, default=1)
    ap.add_argument("--platform", default="CUDA"); ap.add_argument("--max-iter", type=int, default=2000)
    ap.add_argument("--out", default=os.path.expanduser("~/v8_data/ref/rod_scope"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    t0 = time.time()

    # a heavy-atom-only copy, so the topology matches what place.py returns
    import gemmi
    rod_src = os.path.expanduser(f"~/v8_data/rods/{a.rod}.pdb")
    rod_pdb = os.path.join(a.out, f"{a.rod}_heavy.pdb")
    os.makedirs(a.out, exist_ok=True)
    if not os.path.exists(rod_pdb):
        # cap the rod the same way the fragments are capped: drop the first and last
        # residue and rebuild neutral ACE/NME from them (the V8-X4 reading, at rod scale)
        import fragment
        _st = gemmi.read_structure(rod_src)
        _st.remove_hydrogens(); _st.remove_alternative_conformations(); _st.setup_entities()
        _ch, _seq = fragment.longest_protein_chain(_st)
        names = [r.name for r in _ch]
        if names[0] == "ACE" and names[-1] == "NME":
            _st.write_pdb(rod_pdb)          # already capped
        else:
            fragment.cut(rod_src, _seq[1:-1], rod_pdb)
    slab_pdb = os.path.expanduser(f"~/v8_data/slabs/slab_{a.cation}_rod.pdb")
    slab_xml = os.path.expanduser(f"~/v8_data/slabs/slab_{a.cation}_rod.xml")
    here = os.path.dirname(os.path.abspath(__file__))
    app.Modeller.loadHydrogenDefinitions(os.path.join(here, "caps_hydrogens.xml"))
    ff = app.ForceField("charmm36.xml", "charmm36/water.xml",
                        os.path.join(here, "caps_charmm36.xml"), slab_xml)

    # orient the rod with its acid face down and its long axis along theta0, as for fragments
    t = time.time()
    theta0, _, body, cb, cat = placemod.scan_theta0(rod_pdb, slab_pdb, n=181)
    t_theta = time.time() - t
    pos, _ = placemod.place(rod_pdb, slab_pdb, 0, 0, theta0=theta0)

    rod = app.PDBFile(rod_pdb)
    sl = app.PDBFile(slab_pdb)
    t = time.time()
    mod = app.Modeller(rod.topology, pos * 0.1 * u.nanometer)
    mod.addHydrogens(ff)
    n_rod = mod.topology.getNumAtoms()
    mod.add(sl.topology, sl.positions)
    n_cx = mod.topology.getNumAtoms()
    cell = sl.topology.getUnitCellDimensions()
    bx = mm.Vec3(cell[0].value_in_unit(u.nanometer), cell[1].value_in_unit(u.nanometer), BOX_Z) * u.nanometer
    mod.topology.setUnitCellDimensions(bx)
    t_model = time.time() - t

    atoms = list(mod.topology.atoms())
    frozen = [i for i in range(n_rod, n_cx)
              if atoms[i].element is not None and atoms[i].element.symbol not in ("K", "Na")]
    t = time.time()
    sysm = ff.createSystem(mod.topology, nonbondedMethod=app.PME, nonbondedCutoff=1.2 * u.nanometer,
                           constraints=None, rigidWater=False)
    for i in frozen:
        sysm.setParticleMass(i, 0.0)
    n_excl, _ = exclude_frozen_pairs(sysm, frozen, np.array(mod.positions.value_in_unit(u.nanometer)))
    t_system = time.time() - t

    t = time.time()
    ctx = mm.Context(sysm, mm.VerletIntegrator(1 * u.femtosecond),
                     mm.Platform.getPlatformByName(a.platform))
    ctx.setPositions(mod.positions)
    t_ctx = time.time() - t

    table = plc.placement_table(max(a.placements, 2))
    lat_a = np.array([cell[0].value_in_unit(u.angstrom), 0.0])
    lat_b = np.array([0.0, cell[1].value_in_unit(u.angstrom)])
    times, mem = [], []
    for k in range(a.placements):
        p = plc.apply_placement(np.array(mod.positions.value_in_unit(u.angstrom))[:n_rod],
                                table[k], lat_a, lat_b)
        full = np.vstack([p, np.array(mod.positions.value_in_unit(u.angstrom))[n_rod:]]) * 0.1
        ctx.setPositions(full)
        t = time.time()
        mm.LocalEnergyMinimizer.minimize(ctx, 1.0, a.max_iter)
        times.append(time.time() - t)
        m = gpu_mem_mib()
        if m:
            mem.append(m)
        print(f"  placement {k}: minimised in {times[-1]:.1f} s", flush=True)

    per = float(np.median(times))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    # projections: a (unit, cation) system is 2 registries x 30 placements
    per_system_h = 2 * plc.N_PLACEMENTS * per / 3600.0
    out = dict(rod=a.rod, cation=a.cation, theta0_deg=theta0,
               n_atoms=n_cx, n_rod_atoms=n_rod, n_slab_atoms=n_cx - n_rod, n_frozen=len(frozen),
               n_frozen_pair_exclusions=n_excl,
               slab_cell_A=[cell[0].value_in_unit(u.angstrom), cell[1].value_in_unit(u.angstrom)],
               box_nm=[bx[i].value_in_unit(u.nanometer) for i in range(3)],
               t_theta0_s=t_theta, t_modeller_s=t_model, t_createsystem_s=t_system, t_context_s=t_ctx,
               minimise_times_s=times, minimise_median_s=per,
               peak_rss_mib=rss, gpu_proc_mem_mib=(max(mem) if mem else None),
               placements_per_registry=plc.N_PLACEMENTS,
               per_system_gpu_hours=per_system_h,
               projection_10_unit_cation_systems_gpu_hours=10 * per_system_h,
               projection_10_systems_two_lengths_gpu_hours=20 * per_system_h,
               projection_wall_hours_two_gpus_10_systems=10 * per_system_h / 2,
               projection_wall_hours_two_gpus_two_lengths=20 * per_system_h / 2,
               wall_s=time.time() - t0)
    json.dump(out, open(os.path.join(a.out, "rod_scope.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "minimise_times_s"}, indent=1))


if __name__ == "__main__":
    main()
