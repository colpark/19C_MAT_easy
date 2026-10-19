"""Gate F1 on the rigid-placement reference runs (amendment E items 2 and 4).

Margin = E_min(theta0 + 30) - E_min(theta0) over the placement set, uncertainty from a
bootstrap over placements with 10,000 replicates, Gate F1 at |margin| >= 3 SE. Reports
the convergence of each minimum against the number of placements; a minimum still
falling at the last placement is undetermined rather than passed.

Usage: python analyze_ref.py REF_DIR OUT.json [--boot 10000]
"""
import argparse, glob, json, os

import numpy as np

DEV = ("HRm-ea", "HRm-60")


def tail_fall(run, k=5):
    """Did the running minimum fall within the last k placements?"""
    if len(run) <= k:
        return True
    return bool(run[-1] < run[-1 - k] - 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("refdir"); ap.add_argument("out")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--seed", type=int, default=23)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    table = {}
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(a.refdir), "*", "ref.json"))):
        d = json.load(open(f))
        if os.path.basename(os.path.dirname(f)) == "test":
            continue
        e0 = np.array([r["e_int"] for r in d["series"]["0"]], float)
        e1 = np.array([r["e_int"] for r in d["series"]["1"]], float)
        m = float(e1.min() - e0.min())
        bs = np.array([e1[rng.integers(0, len(e1), len(e1))].min()
                       - e0[rng.integers(0, len(e0), len(e0))].min() for _ in range(a.boot)])
        se = float(bs.std(ddof=1))
        ci = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        r0, r1 = np.minimum.accumulate(e0), np.minimum.accumulate(e1)
        conv = not (tail_fall(list(r0)) or tail_fall(list(r1)))
        nsig = abs(m) / se if se > 0 else float("inf")
        unit, cat = d["unit"], d["cation"]
        table[f"{unit}_{cat}"] = dict(
            unit=unit, cation=cat, split="dev" if unit in DEV else "test",
            theta0_deg=d["theta0_deg"], n_placements=len(e0), protocol=d["protocol"],
            e_min_reg0=float(e0.min()), e_min_reg1=float(e1.min()),
            e_spread_reg0=[float(e0.min()), float(e0.max())],
            e_spread_reg1=[float(e1.min()), float(e1.max())],
            margin_kj=m, se_kj=se, ci_kj=ci, n_sigma=nsig,
            running_min_reg0=[float(x) for x in r0], running_min_reg1=[float(x) for x in r1],
            min_fell_in_last_5=dict(reg0=tail_fall(list(r0)), reg1=tail_fall(list(r1))),
            converged=bool(conv),
            theta_match_deg=(d["theta0_deg"] if m > 0 else (d["theta0_deg"] + 30.0) % 360) if (nsig >= 3 and conv) else None,
            gate_F1=bool(nsig >= 3 and conv))

    print(f"{'system':12s} {'npl':>4s} {'E_min(t0)':>10s} {'E_min(+30)':>11s} {'margin':>9s} {'SE':>7s} "
          f"{'nsig':>5s} {'conv':>5s}  result")
    for k, v in sorted(table.items()):
        print(f"{k:12s} {v['n_placements']:4d} {v['e_min_reg0']:10.1f} {v['e_min_reg1']:11.1f} "
              f"{v['margin_kj']:+9.1f} {v['se_kj']:7.1f} {v['n_sigma']:5.2f} {('yes' if v['converged'] else 'NO'):>5s}  "
              f"{'pass' if v['gate_F1'] else ('undetermined' if not v['converged'] else 'fail')}")
    need = [f"{u}_{c}" for u in DEV for c in ("K", "NA")]
    ok = [k for k in need if k in table and table[k]["gate_F1"]]
    gate = len(ok) == len(need)
    print(f"\nGate F1 (rigid placements, minimum estimator): {'PASSED' if gate else 'FAILED'} "
          f"({len(ok)} of {len(need)} dev systems)")
    test = {k: v for k, v in table.items() if v["split"] == "test"}
    if test:
        tok = [k for k, v in test.items() if v["gate_F1"]]
        print(f"Test systems with defined theta_match: {len(tok)} of {len(test)} (amendment C item 7 needs at least 4)")
    json.dump(dict(gate_F1_passed=bool(gate), estimator="minimum over placements (amendment E item 2, post hoc)",
                   protocol="rigid placements, no water (amendment E item 4)",
                   bootstrap_replicates=a.boot, systems=table), open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
