"""Set the FM band m* from the dev split and report Gate F2.

Amendment A item 5:
  sigma_FM is the RMS of (FM margin - IFF margin) over the dev points, one per
  (fragment, substrate, placement).
  m* = max(2 sigma_FM, the empirical bound), where the empirical bound is the smallest
  margin above which the dev sign error falls below 10 %, computed only when at least
  10 dev points exist. Report n and the bootstrap interval.

Gate F2 (amendment A item 4): outside m*, the FM's sign agrees with IFF on at least
80 % of dev points. The count of test systems outside m* is reported after the freeze.

Usage: python band.py TRUTH_TABLE.json FM_DEV.json OUT.json [--boot 10000]
"""
import argparse, json

import numpy as np

DEV = ("HRm-ea", "HRm-60")


def dev_points(truth, fm):
    """One point per (unit, cation, placement): the FM margin against that placement's IFF margin."""
    pts = []
    for key, t in truth["systems"].items():
        if t["unit"] not in DEV:
            continue
        f = fm.get(key)
        if f is None:
            continue
        for i, iff_m in enumerate(t["margins_per_placement_kj"]):
            pts.append(dict(system=key, unit=t["unit"], cation=t["cation"], placement=i,
                            iff_kj=iff_m, fm_kj=f["margin_kj"],
                            diff_kj=f["margin_kj"] - iff_m,
                            sign_agrees=bool(np.sign(f["margin_kj"]) == np.sign(iff_m))))
    return pts


def empirical_bound(pts, target=0.10):
    """Smallest |FM margin| threshold above which the dev sign error falls below target."""
    cands = sorted({abs(p["fm_kj"]) for p in pts})
    for c in cands:
        out = [p for p in pts if abs(p["fm_kj"]) >= c]
        if not out:
            continue
        err = 1.0 - sum(p["sign_agrees"] for p in out) / len(out)
        if err < target:
            return float(c), float(err), len(out)
    return None, None, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("truth"); ap.add_argument("fm"); ap.add_argument("out")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--seed", type=int, default=11)
    a = ap.parse_args()
    truth = json.load(open(a.truth))
    fm = json.load(open(a.fm))
    pts = dev_points(truth, fm)
    n = len(pts)
    if n == 0:
        raise SystemExit("no dev points: need both TRUTH_TABLE and FM_DEV for the dev units")

    diffs = np.array([p["diff_kj"] for p in pts])
    sigma = float(np.sqrt((diffs ** 2).mean()))
    eb, eb_err, eb_n = (empirical_bound(pts) if n >= 10 else (None, None, 0))
    mstar = max(2 * sigma, eb) if eb is not None else 2 * sigma

    # bootstrap over (unit, cation) clusters, then points inside them (amendment C item 8)
    rng = np.random.default_rng(a.seed)
    clusters = sorted({p["system"] for p in pts})
    by = {c: [p for p in pts if p["system"] == c] for c in clusters}
    sig_b, ms_b = [], []
    for _ in range(a.boot):
        pick = rng.choice(len(clusters), len(clusters), replace=True)
        samp = []
        for i in pick:
            g = by[clusters[i]]
            samp += [g[j] for j in rng.choice(len(g), len(g), replace=True)]
        d = np.array([p["diff_kj"] for p in samp])
        s = float(np.sqrt((d ** 2).mean()))
        sig_b.append(s)
        e, _, _ = empirical_bound(samp) if len(samp) >= 10 else (None, None, 0)
        ms_b.append(max(2 * s, e) if e is not None else 2 * s)
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

    outside = [p for p in pts if abs(p["fm_kj"]) >= mstar]
    agree = sum(p["sign_agrees"] for p in outside)
    frac = (agree / len(outside)) if outside else float("nan")
    gate = bool(outside) and frac >= 0.80

    print(f"dev points n = {n} over {len(clusters)} (unit, cation) clusters")
    print(f"sigma_FM = {sigma:.2f} kJ/mol  95 % CI {ci(sig_b)[0]:.2f} to {ci(sig_b)[1]:.2f}")
    print(f"2 sigma_FM = {2 * sigma:.2f} kJ/mol")
    print(f"empirical bound = {('%.2f kJ/mol (dev sign error %.0f %%, n outside %d)' % (eb, 100 * eb_err, eb_n)) if eb is not None else 'not computed'}")
    print(f"m* = {mstar:.2f} kJ/mol  95 % CI {ci(ms_b)[0]:.2f} to {ci(ms_b)[1]:.2f}  ({a.boot} replicates)")
    print(f"outside m*: {len(outside)} dev points, sign agreement {agree}/{len(outside)}"
          f"{'' if not outside else ' = %.0f %%' % (100 * frac)}")
    print(f"\nGate F2 (>= 80 % sign agreement outside m*): {'PASSED' if gate else 'FAILED'}")

    json.dump(dict(n_dev_points=n, n_clusters=len(clusters), sigma_fm_kj=sigma,
                   sigma_fm_ci=ci(sig_b), two_sigma_kj=2 * sigma,
                   empirical_bound_kj=eb, empirical_bound_err=eb_err, empirical_bound_n=eb_n,
                   m_star_kj=float(mstar), m_star_ci=ci(ms_b), bootstrap_replicates=a.boot,
                   n_outside=len(outside), sign_agreement=frac, gate_F2_passed=gate,
                   points=pts), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
