"""Gate F1 under both estimators, side by side (amendment E item 2).

Estimator A (paired, pre-registered in V8-1, came first): pair placement i of theta0
with placement i of theta0 + 30, take the signed difference, average over placements and
take the error from their spread combined with the block errors.

Estimator B (minimum over placements, chosen post hoc after A failed): per registry take
the minimum interaction energy over placements; margin = E_min(theta0 + 30) - E_min(theta0);
uncertainty from a bootstrap over placements with 10,000 replicates. Gate F1 keeps
|margin| >= 3 SE.

Estimator B also reports convergence: the running minimum per registry against the number
of placements. A minimum still falling at the last placement is not converged, and that
system is reported undetermined rather than passed.

Usage: python reestimate.py RUNS_DIR OUT.json [--boot 10000]
"""
import argparse, json, os
from collections import defaultdict

import numpy as np

DEV = ("HRm-ea", "HRm-60")
NBLOCK = 5


def block_stats(series):
    e = np.array([s["e_int"] for s in series], float)
    e = e[len(e) // 2:]
    if len(e) < NBLOCK:
        return float(e.mean()), float(e.std(ddof=1) / np.sqrt(len(e))) if len(e) > 1 else float("nan")
    k = len(e) // NBLOCK
    m = np.array([e[i * k:(i + 1) * k].mean() for i in range(NBLOCK)])
    return float(e.mean()), float(m.std(ddof=1) / np.sqrt(NBLOCK))


def collect(runs_dir):
    out = {}
    for d in sorted(os.listdir(runs_dir)):
        f = os.path.join(runs_dir, d, "run.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        if not r.get("series"):
            continue
        m, se = block_stats(r["series"])
        out[(r["unit"], r["cation"], r["registry"], r["placement"])] = dict(
            e=m, se=se, theta0=r["theta0_deg"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs"); ap.add_argument("out")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--seed", type=int, default=19)
    a = ap.parse_args()
    runs = collect(a.runs)
    systems = defaultdict(dict)
    for (u, c, reg, pl), v in runs.items():
        systems[(u, c)][(reg, pl)] = v

    rng = np.random.default_rng(a.seed)
    table = {}
    for (u, c), d in sorted(systems.items()):
        e0 = [d[(0, p)]["e"] for p in sorted({p for (r, p) in d if r == 0})]
        e1 = [d[(1, p)]["e"] for p in sorted({p for (r, p) in d if r == 1})]
        b0 = [d[(0, p)]["se"] for p in sorted({p for (r, p) in d if r == 0})]
        b1 = [d[(1, p)]["se"] for p in sorted({p for (r, p) in d if r == 1})]
        if not e0 or not e1:
            continue
        theta0 = next(iter(d.values()))["theta0"]

        # estimator A, paired
        npl = min(len(e0), len(e1))
        per = [e1[i] - e0[i] for i in range(npl)]
        mA = float(np.mean(per))
        seA_pl = float(np.std(per, ddof=1) / np.sqrt(npl)) if npl > 1 else float("nan")
        seA_bl = float(np.sqrt(np.mean([b0[i] ** 2 + b1[i] ** 2 for i in range(npl)]) / npl))
        seA = float(np.sqrt((0.0 if np.isnan(seA_pl) else seA_pl) ** 2 + seA_bl ** 2))

        # estimator B, minimum over placements, bootstrap over placements
        mB = float(min(e1) - min(e0))
        a0, a1 = np.array(e0), np.array(e1)
        bs = np.array([a1[rng.integers(0, len(a1), len(a1))].min()
                       - a0[rng.integers(0, len(a0), len(a0))].min() for _ in range(a.boot)])
        seB = float(bs.std(ddof=1))
        ciB = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]

        # convergence of each minimum against the number of placements
        run0 = list(np.minimum.accumulate(a0))
        run1 = list(np.minimum.accumulate(a1))
        fell0 = len(run0) > 1 and run0[-1] < run0[-2] - 1e-9
        fell1 = len(run1) > 1 and run1[-1] < run1[-2] - 1e-9
        converged = not (fell0 or fell1)

        nsigA = abs(mA) / seA if seA > 0 else float("inf")
        nsigB = abs(mB) / seB if seB > 0 else float("inf")
        passB = bool(nsigB >= 3.0 and converged)
        table[f"{u}_{c}"] = dict(
            unit=u, cation=c, theta0_deg=theta0, split="dev" if u in DEV else "test",
            n_placements=[len(e0), len(e1)],
            e_reg0=e0, e_reg1=e1,
            paired_margin_kj=mA, paired_se_kj=seA, paired_n_sigma=nsigA,
            min_margin_kj=mB, min_se_kj=seB, min_ci_kj=ciB, min_n_sigma=nsigB,
            running_min_reg0=run0, running_min_reg1=run1,
            min_still_falling=dict(reg0=bool(fell0), reg1=bool(fell1)), converged=bool(converged),
            gate_F1_min_estimator=passB)

    print(f"{'system':12s} | {'paired margin':>13s} {'SE':>7s} {'nsig':>5s} | {'min margin':>11s} {'SE':>7s} {'nsig':>5s} {'conv':>5s} | result")
    for k, v in table.items():
        print(f"{k:12s} | {v['paired_margin_kj']:+13.1f} {v['paired_se_kj']:7.1f} {v['paired_n_sigma']:5.2f} | "
              f"{v['min_margin_kj']:+11.1f} {v['min_se_kj']:7.1f} {v['min_n_sigma']:5.2f} {('yes' if v['converged'] else 'NO'):>5s} | "
              f"{'pass' if v['gate_F1_min_estimator'] else ('undetermined' if not v['converged'] else 'fail')}")
    dev = [k for k, v in table.items() if v["split"] == "dev"]
    need = [f"{u}_{c}" for u in DEV for c in ("K", "NA")]
    ok = [k for k in need if k in table and table[k]["gate_F1_min_estimator"]]
    print(f"\nGate F1 under the minimum estimator: {'PASSED' if len(ok) == len(need) else 'FAILED'} "
          f"({len(ok)} of {len(need)} dev systems; present {len([k for k in need if k in table])})")
    json.dump(dict(estimator_order="paired first (pre-registered in V8-1), minimum second (post hoc, amendment E item 2)",
                   bootstrap_replicates=a.boot, systems=table,
                   gate_F1_min_estimator_passed=bool(len(ok) == len(need))),
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
