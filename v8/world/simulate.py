"""Simulator tool (analog of B1's window search): for a hypothesis and a scan plan, predicted angle
statistics and expected D. Model-based Monte Carlo on angles, no rendering and NO access to any world
truth: it only sees the hypothesis, the plans, the rod unit id, repeat count and nuisance priors.

Pipeline model (calibrated against the rendered pipeline by calib_sim.py, see sim_calib.json):
  detected rods  = coverage * (fov - L/2)^2 / (L W) * det_frac(pixel size) * noise_factor
  angle error    = sigma_theta(pixel size) (robust sigma of segmentation angle vs truth)
  lattice error  = hypot(C1 * (sigma_lat / A) / sqrt(npx^2), drift term), unresolved if pixel too coarse
Then angles are drawn from the hypothesis mixture and fit_D is applied exactly as for real scans.
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sample as S, cost as C, fit as F, lattice as LAT  # noqa: E402

_CAL = json.load(open(os.path.dirname(os.path.abspath(__file__)) + "/sim_calib.json"))
_PX = np.array([c["px_nm"] for c in _CAL])
_DET = np.array([c["det_per_true"] for c in _CAL])
_SIG = np.array([c["sigma_theta_deg"] for c in _CAL])
C1_DEG = 42.0            # lattice angle error = C1 * (noise/corrugation) / sqrt(pixels), from the rendered scaling
NOISE_TOL_NM, NOISE_EXP = 0.38, 3.0


def det_model(plan, noise_nm, hash_id="HRm-ea", n_rep=18):
    px = plan.fov_nm / plan.npx
    det = float(np.interp(px, _PX, _DET, right=0.0))
    if px > _PX[-1]:
        det *= max(0.0, 1 - (px - _PX[-1]) / 1.0)
    sig = float(np.interp(px, _PX, _SIG, right=_SIG[-1] + 2 * (px - _PX[-1])))
    s_eff = noise_nm * C.noise_scale(plan)
    det *= 1.0 / (1.0 + (s_eff / NOISE_TOL_NM) ** NOISE_EXP)
    return det, sig


def lattice_sigma(plan, noise_nm):
    """Expected lattice-angle standard error (deg), or None if the lattice is unresolved."""
    px = plan.fov_nm / plan.npx
    if 2.0 / (np.sqrt(3) * LAT.A_LAT_NM) > 0.9 * 0.5 / px:
        return None
    s = LAT.LATTICE_NOISE_REL * noise_nm * C.noise_scale(plan)
    noise_term = C1_DEG * (s / LAT.CORRUGATION_NM) / np.sqrt(plan.npx * plan.ny)
    import render as RR
    drift = np.degrees(0.7 * F.DRIFT_PRIOR_NM_MIN * plan.frame_minutes() / (RR.DRIFT_CORR_FOV * plan.fov_nm))
    return float(np.hypot(max(noise_term, 0.05), drift))


def simulate(hypothesis, rod_plan, lattice_plan=None, hash_id="HRm-ea", n_rep=18, n_mc=30, seed=0,
             priors=None, total_minutes=None):
    assert hypothesis in ("A", "B")
    pr = dict(S.NUIS_RANGE)
    if priors:
        pr.update(priors)
    L, W = S.rod_dims(hash_id, n_rep)
    rng = np.random.default_rng(seed)
    out = dict(D=[], n=[], R6=[], frac15=[], sig_a=[])
    for _ in range(n_mc):
        nz = {k: float(rng.uniform(*v)) for k, v in pr.items() if k != "kappa"}
        nz["kappa"] = float(np.exp(rng.uniform(np.log(pr["kappa"][0]), np.log(pr["kappa"][1]))))
        det, sig_th = det_model(rod_plan, nz["noise_nm"], hash_id, n_rep)
        area = max(rod_plan.fov_nm - L / 2, 0.0) ** 2
        lam = nz["coverage"] * area / (L * W) * det
        n = int(rng.poisson(lam))
        th_world = S.draw_angles(rng, n, S.REG_OFFSET_DEG[hypothesis], nz["kappa"], nz["f_iso"])
        th = np.mod(th_world + nz["azimuth_deg"] + rng.normal(0, sig_th, n), 180.0)
        lat = None
        if lattice_plan is not None:
            sa = lattice_sigma(lattice_plan, nz["noise_nm"])
            if sa is not None:
                lat = dict(angle_deg=float((nz["azimuth_deg"] + rng.normal(0, sa)) % 60), sigma_deg=sa)
                out["sig_a"].append(sa)
        d = F.fit_D(th, hypothesis, lat)["D"] if n >= 3 else 0.0
        out["D"].append(d)
        out["n"].append(n)
        if lat is not None and n:
            rel = np.radians(th - lat["angle_deg"])
            out["R6"].append(float(abs(np.mean(np.exp(6j * rel)))))
            dev = ((th - lat["angle_deg"]) + 30) % 60 - 30      # deviation from the nearest row direction (registry A)
            out["frac15"].append(float(np.mean(np.abs(dev) < 15)))
    D = np.array(out["D"])
    res = dict(hypothesis=hypothesis, expected_D=float(D.mean()), median_D=float(np.median(D)),
               D_q10=float(np.quantile(D, 0.1)), D_q90=float(np.quantile(D, 0.9)), P_D_gt_9=float(np.mean(D > 9)),
               expected_n_rods=float(np.mean(out["n"])),
               predicted_R6_about_lattice=float(np.mean(out["R6"])) if out["R6"] else None,
               predicted_frac_within_15deg_of_rows=float(np.mean(out["frac15"])) if out["frac15"] else None,
               lattice_sigma_deg=float(np.mean(out["sig_a"])) if out["sig_a"] else None,
               lattice_resolved=bool(out["sig_a"]) if lattice_plan is not None else False,
               minutes=rod_plan.minutes() + (lattice_plan.minutes() if lattice_plan is not None else 0.0),
               note="Without a resolved lattice scan D = 0 (azimuth hides the registry). R6/frac15 are relative to the fitted lattice; for registry B R6 is the same and frac15 is ~0.")
    return res


if __name__ == "__main__":
    rp = C.Plan("rods", 250, 256, 1, 1)
    lp = C.Plan("lattice", 12, 96, 1, 1)
    for h in "AB":
        print(simulate(h, rp, lp, n_mc=20, seed=1))
    print(simulate("A", rp, None, n_mc=10))
