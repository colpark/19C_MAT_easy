"""Collect the IFF truth runs into TRUTH_TABLE.json and report Gate F1.

Per (unit, cation): for each of the three placements, the interaction energy of each
registry is averaged over the second half of production with a block standard error
(5 blocks). The margin is E(theta0 + 30) - E(theta0), so a positive margin means the
matched registry is theta0. The reported standard error combines the spread over the
three placements with the block errors, as V8-1 specifies.

Gate F1 (amendment C item 6): |margin| >= 3 SE for the dev units on both cations.
Amendment C item 7: a test (unit, cation) system below 3 SE has no defined theta_match
and leaves the pilot.

Usage: python analyze_truth.py RUNS_DIR OUT.json
"""
import json, os, sys
from collections import defaultdict

import numpy as np

DEV = ("HRm-ea", "HRm-60")
NBLOCK = 5


def block_stats(series):
    """Mean and block standard error over the second half of a checkpoint series."""
    e = np.array([s["e_int"] for s in series], float)
    e = e[len(e) // 2:]
    if len(e) < NBLOCK:
        return float(e.mean()), float(e.std(ddof=1) / np.sqrt(len(e))) if len(e) > 1 else float("nan"), len(e)
    k = len(e) // NBLOCK
    means = np.array([e[i * k:(i + 1) * k].mean() for i in range(NBLOCK)])
    return float(e.mean()), float(means.std(ddof=1) / np.sqrt(NBLOCK)), len(e)


def main(runs_dir, out_path):
    runs = {}
    for d in sorted(os.listdir(runs_dir)):
        f = os.path.join(runs_dir, d, "run.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        if not r.get("series"):
            continue
        m, se, n = block_stats(r["series"])
        runs[(r["unit"], r["cation"], r["registry"], r["placement"])] = dict(
            e_int=m, block_se=se, n_check=n, theta0=r["theta0_deg"], ns=r["ns"],
            dt_fs=r.get("dt_fs"), wall_s=r.get("wall_s"), n_atoms=r.get("n_atoms"))

    systems = defaultdict(dict)
    for (unit, cat, reg, pl), v in runs.items():
        systems[(unit, cat)][(reg, pl)] = v

    table, gate_rows = {}, []
    for (unit, cat), d in sorted(systems.items()):
        per_pl, blocks = [], []
        for pl in (0, 1, 2):
            a, b = d.get((0, pl)), d.get((1, pl))
            if a is None or b is None:
                continue
            per_pl.append(b["e_int"] - a["e_int"])
            blocks.append(a["block_se"] ** 2 + b["block_se"] ** 2)
        if not per_pl:
            continue
        m = float(np.mean(per_pl))
        se_pl = float(np.std(per_pl, ddof=1) / np.sqrt(len(per_pl))) if len(per_pl) > 1 else float("nan")
        se_bl = float(np.sqrt(np.mean(blocks) / len(per_pl)))
        se = float(np.sqrt((0.0 if np.isnan(se_pl) else se_pl) ** 2 + se_bl ** 2))
        nsig = abs(m) / se if se > 0 else float("inf")
        theta0 = next(iter(d.values()))["theta0"]
        key = f"{unit}_{cat}"
        table[key] = dict(unit=unit, cation=cat, theta0_deg=theta0, n_placements=len(per_pl),
                          margin_kj=m, se_kj=se, se_placements_kj=se_pl, se_blocks_kj=se_bl,
                          n_sigma=nsig, truth_exists=bool(nsig >= 3.0),
                          theta_match_deg=(theta0 if m > 0 else (theta0 + 30.0) % 360) if nsig >= 3 else None,
                          margins_per_placement_kj=per_pl, split="dev" if unit in DEV else "test")
        gate_rows.append((key, m, se, nsig, len(per_pl), unit in DEV))

    print(f"{'system':16s} {'split':5s} {'margin kJ/mol':>14s} {'SE':>8s} {'n sigma':>8s} {'npl':>4s}  truth")
    for key, m, se, nsig, npl, isdev in gate_rows:
        print(f"{key:16s} {'dev' if isdev else 'test':5s} {m:+14.2f} {se:8.2f} {nsig:8.2f} {npl:4d}  {'yes' if nsig >= 3 else 'NO'}")

    dev_needed = [f"{u}_{c}" for u in DEV for c in ("K", "NA")]
    have = [k for k in dev_needed if k in table]
    passed = [k for k in have if table[k]["truth_exists"]]
    gate = len(have) == len(dev_needed) and len(passed) == len(dev_needed)
    print(f"\nGate F1 (dev units, both cations, |margin| >= 3 SE): "
          f"{'PASSED' if gate else 'FAILED'} ({len(passed)} of {len(dev_needed)} dev systems; present {len(have)})")
    test_ok = [k for k, v in table.items() if v["split"] == "test" and v["truth_exists"]]
    test_all = [k for k, v in table.items() if v["split"] == "test"]
    if test_all:
        print(f"Test systems with defined theta_match: {len(test_ok)} of {len(test_all)} "
              f"(amendment C item 7 needs at least 4)")
    json.dump(dict(gate_F1_passed=bool(gate), dev_required=dev_needed, systems=table),
              open(out_path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
