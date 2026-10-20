"""V9-7, post hoc: is Gate M reachable at all at 82 peptides, and at rung 2's 54?

Written after rung 1's intervals were seen and labelled post hoc. It asks a question that does
not involve the FM: given this pair structure and the pre-registered bootstrap over PEPTIDES,
what accuracy must ANY predictor reach for the 95 percent interval to exclude 0.5?

The empirical anchor needs no simulation: net charge at pH 7 scores **0.7229** on the 323
FM-subset K pairs and its interval still includes 0.5. On the full 1,664-pair dev K set the same
descriptor scores 0.6743 and its interval **excludes** 0.5. Same descriptor, lower accuracy,
tighter interval: the binding constraint is the number of PEPTIDES, not the number of pairs.

The synthetic oracle gives the curve. A scorer is built as the true intensity rank plus Gaussian
noise; the noise is tuned by bisection to hit a target pair accuracy; then the pre-registered
peptide bootstrap runs on it. No FM value is used anywhere in this file.

Code only, no FM call. Aggregates only (V9-X1).
"""
import csv, json, os, random, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
import fm_gates as G
from split_and_pairs import net_charge, gravy
from twin_count import mono_mass

sp = json.load(open(os.path.expanduser("~/v9_data/split/split.json")))
sel = json.load(open(os.path.expanduser("~/v9_data/fm/rung2_selection.json")))
inten = {r["sequence"]: float(r["intensity"]) for r in csv.DictReader(
    open(os.path.expanduser("~/v9_data/ds1_parsed/ds1.csv")))}
top, bot = sp["fm_subset"]["top"], sp["fm_subset"]["bottom"]
pid_of = {s: f"P{i:03d}" for i, s in enumerate(top)}
pid_of.update({s: f"P{60+i:03d}" for i, s in enumerate(bot)})
kp_all = [tuple(p) for p in sp["dev_pairs_K_list"]]
kp_120 = [tuple(p) for p in sp["fm_pairs_K"]]
sel60 = set(sel["pids_top"] + sel["pids_bottom"])
kp_60 = [(a, b) for a, b in kp_120 if pid_of[a] in sel60 and pid_of[b] in sel60]

SETS = [("full dev K set", kp_all), ("rung 1, 120 peptides", kp_120), ("rung 2, 60 peptides", kp_60)]
out = {"label": "post hoc, written after rung 1's intervals were seen", "uses_fm_values": False}

print("## 1. The three real descriptors on each pair set (the empirical anchor)")
print(f"{'set':24s} {'pairs':>6s} {'peps':>5s} | " + " | ".join(f"{n:>26s}" for n in
      ("mass", "net_charge_pH7", "GRAVY")))
rows = {}
for nm, ps in SETS:
    peps = sorted({s for p in ps for s in p})
    cells = []
    rows[nm] = dict(n_pairs=len(ps), n_peptides=len(peps), descriptors={})
    for dn, f, lw in (("mass", mono_mass, False), ("net_charge_pH7", net_charge, True),
                      ("GRAVY", gravy, True)):
        a = G.acc(ps, f, lw)
        if a < 0.5:
            lw = not lw; a = G.acc(ps, f, lw)
        d, _ = G.boot_acc(ps, (f, lw), random.Random(G.SEED))
        lo, hi = G.ci(d)
        rows[nm]["descriptors"][dn] = dict(accuracy=a, ci=[lo, hi], excludes_half=bool(lo > 0.5))
        cells.append(f"{a:.4f} [{lo:.3f},{hi:.3f}]{'*' if lo > 0.5 else ' '}")
    print(f"{nm:24s} {len(ps):6d} {len(peps):5d} | " + " | ".join(f"{c:>26s}" for c in cells))
print("   * = 95% interval excludes 0.5, i.e. this descriptor would clear Gate M's criterion")

print("\n## 2. Synthetic oracle: what accuracy does ANY predictor need to clear Gate M?")
def oracle(ps, peps, target, seed=11):
    """Truth rank plus Gaussian noise, noise tuned by bisection to hit `target` pair accuracy."""
    order = {s: i for i, s in enumerate(sorted(peps, key=lambda z: inten[z]))}
    rng = random.Random(seed)
    base = {s: rng.gauss(0, 1) for s in peps}
    lo_s, hi_s = 1e-4, 400.0
    for _ in range(60):
        sg = (lo_s + hi_s) / 2
        sc = {s: order[s] + sg * base[s] for s in peps}
        a = G.acc(ps, lambda z: sc.get(z), False)      # higher rank = stronger, "higher wins"
        if a > target:
            lo_s = sg
        else:
            hi_s = sg
    return sc, G.acc(ps, lambda z: sc.get(z), False)

print(f"{'target acc':>10s} | " + " | ".join(f"{nm:>34s}" for nm, _ in SETS))
out["power"] = {}
for target in (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95):
    cells = []
    out["power"][target] = {}
    for nm, ps in SETS:
        peps = sorted({s for p in ps for s in p})
        sc, got = oracle(ps, peps, target)
        d, _ = G.boot_acc(ps, (lambda z: sc.get(z), False), random.Random(G.SEED))
        lo, hi = G.ci(d)
        ok = bool(lo > 0.5)
        out["power"][target][nm] = dict(realised_accuracy=got, ci=[lo, hi], clears_gate_M=ok)
        cells.append(f"{got:.3f} [{lo:.3f},{hi:.3f}] {'CLEARS' if ok else '  --  '}")
    print(f"{target:10.2f} | " + " | ".join(f"{c:>34s}" for c in cells))

for nm, _ in SETS:
    need = [t for t in sorted(out["power"]) if out["power"][t][nm]["clears_gate_M"]]
    rows[nm]["min_target_accuracy_clearing_gate_M"] = (need[0] if need else None)
    print(f"   {nm:24s}: Gate M first clears at a target accuracy of "
          f"{need[0] if need else 'NOT CLEARED up to 0.95'}")
out["sets"] = rows
json.dump(out, open(os.path.expanduser("~/v9_data/fm/rung1/gate_m_power.json"), "w"), indent=1)
