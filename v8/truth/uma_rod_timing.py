"""Time one UMA single point and one UMA relaxation step on the 18-repeat rod system.

Amendment F item 6: a cost measurement on a dev system, nothing more. **No energy is
recorded as a margin and no matched angle is computed from it.** The script reports wall
time, host and GPU memory and whether the system fits at all; if UMA cannot hold a system
of this size, that is the finding and it bears on Gate F2.

Usage: python uma_rod_timing.py [--rod HRm-ea_18rep_pub] [--cation K] [--task omol]
"""
import argparse, json, os, resource, subprocess, time

import numpy as np


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
    ap.add_argument("--rod", default="HRm-ea_18rep_pub"); ap.add_argument("--cation", default="K")
    ap.add_argument("--task", default="omol")
    ap.add_argument("--out", default=os.path.expanduser("~/v8_data/fm/rod_timing"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    out = dict(rod=a.rod, cation=a.cation, task=a.task)

    import place as placemod
    import fm_path as F
    rod_pdb = os.path.expanduser(f"~/v8_data/ref/rod_scope/{a.rod}_heavy.pdb")
    if not os.path.exists(rod_pdb):
        rod_pdb = os.path.expanduser(f"~/v8_data/rods/{a.rod}.pdb")
    slab_pdb = os.path.expanduser(f"~/v8_data/slabs/slab_{a.cation}_rod.pdb")

    t = time.time()
    theta0, _, _, _, _ = placemod.scan_theta0(rod_pdb, slab_pdb, n=181)
    pos, _ = placemod.place(rod_pdb, slab_pdb, 0, 0, theta0=theta0)
    atoms, n_slab, n_rod = F.load_atoms(slab_pdb, rod_pdb, pos)
    out.update(n_atoms=len(atoms), n_slab=n_slab, n_rod=n_rod, theta0_deg=theta0,
               t_build_s=round(time.time() - t, 2))
    print(json.dumps(out), flush=True)

    try:
        from fairchem.core import FAIRChemCalculator, pretrained_mlip
        t = time.time()
        pu = pretrained_mlip.get_predict_unit("uma-s-1p2", device="cuda")
        calc = FAIRChemCalculator(pu, task_name=a.task)
        out["t_load_model_s"] = round(time.time() - t, 2)
        atoms.calc = calc

        t = time.time()
        e = atoms.get_potential_energy()           # timed only; NOT used as a margin
        out["t_single_point_s"] = round(time.time() - t, 2)
        out["single_point_finite"] = bool(np.isfinite(e))
        out["energy_recorded"] = False             # amendment F item 6
        out["gpu_mem_after_single_point_mib"] = gpu_mem_mib()

        from ase.optimize import LBFGS
        opt = LBFGS(atoms, logfile=None)
        t = time.time()
        opt.run(fmax=0.05, steps=1)                # exactly one relaxation step
        out["t_one_relax_step_s"] = round(time.time() - t, 2)
        out["fits"] = True
        out["gpu_mem_peak_mib"] = gpu_mem_mib()
    except Exception as ex:
        out["fits"] = False
        out["error_type"] = type(ex).__name__
        out["error"] = str(ex)[:300]
    out["peak_rss_mib"] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)

    if out.get("fits"):
        per = out.get("t_one_relax_step_s", 0.0)
        out["projection_60_steps_per_placement_s"] = round(60 * per, 1)
        out["projection_one_system_gpu_hours"] = round(2 * 64 * 60 * per / 3600.0, 2)
        out["projection_four_dev_systems_gpu_hours"] = round(4 * 2 * 64 * 60 * per / 3600.0, 2)
    json.dump(out, open(os.path.join(a.out, "uma_rod_timing.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
