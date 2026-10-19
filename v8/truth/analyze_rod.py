"""Gate F1 on the amendment F rod runs, with both estimators and the scaling diagnostic.

Amendment F item 4: minimum over placements, bootstrap over placements with 10,000
replicates, |margin| >= 3 SE, and a system marked **undetermined** if its running minimum
is still falling over the last quarter of placements. The paired estimator is reported
beside it throughout (amendment E item 2's disclosure applies: paired came first and was
pre-registered; minimum is post hoc).

Amendment F item 5: the margin at 14 repeats beside the margin at 18 repeats per cation.
If the physical story holds, |margin(18)| should exceed |margin(14)|.

A separate script from analyze_ref.py so the step 2 analysis stays reproducible.

Usage: python analyze_rod.py REF_DIR OUT.json [--boot 10000]
"""
import argparse, glob, json, os, re

import numpy as np


def still_falling(run):
    """Did the running minimum fall during the last quarter of placements?"""
    n = len(run)
    q = max(1, n // 4)
    return bool(run[-1] < run[-1 - q] - 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("refdir"); ap.add_argument("out")
    ap.add_argument("--boot", type=int, default=10000); ap.add_argument("--seed", type=int, default=29)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    table = {}
    for f in sorted(glob.glob(os.path.join(os.path.expanduser(a.refdir), "rod*", "ref.json"))):
        d = json.load(open(f))
        tag = os.path.basename(os.path.dirname(f))
        m = re.match(r"rod(\d+)_(K|NA)$", tag)
        if not m:
            continue
        reps, cat = int(m.group(1)), m.group(2)
        r0 = d["series"]["0"]
        r1 = d["series"]["1"]
        e0 = np.array([r["e_int"] for r in r0], float)
        e1 = np.array([r["e_int"] for r in r1], float)

        # estimator B: minimum over placements, bootstrap over placements
        mB = float(e1.min() - e0.min())
        bs = np.array([e1[rng.integers(0, len(e1), len(e1))].min()
                       - e0[rng.integers(0, len(e0), len(e0))].min() for _ in range(a.boot)])
        seB = float(bs.std(ddof=1))
        ciB = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        run0 = list(np.minimum.accumulate(e0))
        run1 = list(np.minimum.accumulate(e1))
        conv = not (still_falling(run0) or still_falling(run1))
        nsigB = abs(mB) / seB if seB > 0 else float("inf")

        # estimator A: paired by placement (the shared set makes the pairing well defined)
        npl = min(len(e0), len(e1))
        per = e1[:npl] - e0[:npl]
        mA = float(per.mean())
        seA = float(per.std(ddof=1) / np.sqrt(npl))
        nsigA = abs(mA) / seA if seA > 0 else float("inf")

        rows = r0 + r1
        table[tag] = dict(
            repeats=reps, cation=cat, theta0_deg=d["theta0_deg"], n_placements=len(e0),
            n_atoms=d["n_atoms"], protocol=d["protocol"],
            e_min_reg0=float(e0.min()), e_min_reg1=float(e1.min()),
            e_span_reg0=[float(e0.min()), float(e0.max())],
            e_span_reg1=[float(e1.min()), float(e1.max())],
            min_margin_kj=mB, min_se_kj=seB, min_ci_kj=ciB, min_n_sigma=nsigB,
            paired_margin_kj=mA, paired_se_kj=seA, paired_n_sigma=nsigA,
            running_min_reg0=[float(x) for x in run0], running_min_reg1=[float(x) for x in run1],
            still_falling=dict(reg0=still_falling(run0), reg1=still_falling(run1)),
            converged=bool(conv),
            iterations=d.get("iterations"), grad_rms=d.get("grad_rms"),
            max_iter_cap=d.get("max_iter_cap"), n_hit_cap=d.get("n_hit_cap"),
            wall_s=d.get("wall_s"),
            theta_match_deg=(d["theta0_deg"] if mB > 0 else (d["theta0_deg"] + 30.0) % 360)
            if (nsigB >= 3 and conv) else None,
            gate_F1=bool(nsigB >= 3 and conv))

    print(f"{'system':12s} {'npl':>4s} {'E_min(t0)':>11s} {'E_min(+30)':>11s} | "
          f"{'min margin':>11s} {'SE':>8s} {'nsig':>5s} {'conv':>5s} | {'paired':>10s} {'SE':>8s} {'nsig':>5s} | result")
    for k, v in sorted(table.items()):
        print(f"{k:12s} {v['n_placements']:4d} {v['e_min_reg0']:11.1f} {v['e_min_reg1']:11.1f} | "
              f"{v['min_margin_kj']:+11.1f} {v['min_se_kj']:8.1f} {v['min_n_sigma']:5.2f} "
              f"{('yes' if v['converged'] else 'NO'):>5s} | {v['paired_margin_kj']:+10.1f} {v['paired_se_kj']:8.1f} "
              f"{v['paired_n_sigma']:5.2f} | {'pass' if v['gate_F1'] else ('undetermined' if not v['converged'] else 'fail')}")

    passed = [k for k, v in table.items() if v["gate_F1"]]
    gate = len(passed) >= 3 and len(table) == 4
    print(f"\nGate F1 on the rod: {len(passed)} of {len(table)} systems pass "
          f"(amendment F item 7 needs at least 3 of 4) -> {'PASS' if gate else 'FAIL'}")

    # amendment F item 5: length scaling, reported either way
    print("\nScaling diagnostic (item 5): |margin| at 18 repeats against 14 repeats")
    scaling = {}
    for cat in ("K", "NA"):
        a14, a18 = table.get(f"rod14_{cat}"), table.get(f"rod18_{cat}")
        if not a14 or not a18:
            continue
        m14, m18 = abs(a14["min_margin_kj"]), abs(a18["min_margin_kj"])
        holds = m18 > m14
        scaling[cat] = dict(abs_margin_14=m14, abs_margin_18=m18, ratio=(m18 / m14 if m14 else None),
                            margin_14=a14["min_margin_kj"], margin_18=a18["min_margin_kj"],
                            same_sign=bool(np.sign(a14["min_margin_kj"]) == np.sign(a18["min_margin_kj"])),
                            story_holds=bool(holds))
        print(f"  {cat:3s}: |m(14)| {m14:8.1f}  |m(18)| {m18:8.1f}  ratio {m18 / m14 if m14 else float('nan'):5.2f}  "
              f"same sign {scaling[cat]['same_sign']}  -> {'holds' if holds else 'DOES NOT HOLD'}")

    json.dump(dict(gate_F1_rod_passed=bool(gate), n_passed=len(passed), systems=table,
                   scaling=scaling, bootstrap_replicates=a.boot,
                   estimator_order="paired first (pre-registered, V8-1); minimum second (post hoc, amendment E item 2)",
                   protocol_note="rigid placements, no explicit water (amendment E item 4)"),
              open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
