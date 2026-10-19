"""V9-4: reserve the benchmark split, form dev pairs, run the three code-only null baselines.

Pre-declared conventions, fixed before any number was computed (hard rule 5):

* Split: sha256 of SPLIT_SALT + sequence, first 8 hex digits as a fraction of 2^32.
  fraction < 0.30 -> dev, else reserved. Deterministic, order-independent, logged salt.
* Null baseline direction: each descriptor is scored in BOTH orientations and the null's
  accuracy is the **better** of the two. An agent computing a free descriptor would be free to
  fit its sign, so the conservative null is the best-oriented one. Both orientations reported.
* Ties count as 0.5 (chance), and the tie count is reported.
* Net charge at pH 7 = (#R + #K) - (#D + #E). His and the termini are ignored; the array
  peptides are surface-tethered so a free C-terminus is not assumed.
* GRAVY = mean Kyte-Doolittle hydropathy.
* Bootstrap is over PEPTIDES, not pairs, 10,000 replicates, seed logged.

Aggregates only to stdout (V9-X1). Per-peptide and per-pair data go to JSON.
"""
import csv, hashlib, json, os, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_count import mono_mass, panel_score

SPLIT_SALT = "v9-split-20261019"      # logged
DEV_FRACTION = 0.30
PICK_SALT = "v9-fmpick-20261019"      # logged, selects the FM subset FM-blind
N_PER_QUARTILE = 60
BOOT, BOOT_SEED = 10000, 29

KD = {"A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5, "G": -0.4,
      "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8, "P": -1.6, "S": -0.8,
      "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2}


def hfrac(salt, seq):
    return int(hashlib.sha256((salt + seq).encode()).hexdigest()[:8], 16) / 2 ** 32


def net_charge(s):
    return (s.count("R") + s.count("K")) - (s.count("D") + s.count("E"))


def gravy(s):
    return sum(KD[a] for a in s) / len(s)


def acc_both(pairs, score):
    """(best accuracy, orientation, accuracy of 'higher wins', ties) with ties at 0.5."""
    hi = ties = 0.0
    for strong, weak in pairs:
        a, b = score(strong), score(weak)
        if a == b:
            hi += 0.5
            ties += 1
        else:
            hi += a > b
    n = len(pairs)
    accs = hi / n
    return (max(accs, 1 - accs), "higher wins" if accs >= 1 - accs else "lower wins",
            accs, int(ties))


def boot_ci(pairs, score, peptides, rng):
    """Bootstrap over peptides: resample the peptide pool, keep pairs with both members in."""
    import math
    idx = {p: i for i, p in enumerate(peptides)}
    out = []
    best_or = acc_both(pairs, score)[1]
    hi_wins = best_or == "higher wins"
    for _ in range(BOOT):
        keep = Counter(peptides[rng.randrange(len(peptides))] for _ in range(len(peptides)))
        num = den = 0.0
        for strong, weak in pairs:
            w = keep.get(strong, 0) * keep.get(weak, 0)
            if not w:
                continue
            den += w
            a, b = score(strong), score(weak)
            if a == b:
                num += 0.5 * w
            else:
                num += w * ((a > b) if hi_wins else (a < b))
        if den:
            out.append(num / den)
    out.sort()
    lo = out[int(0.025 * len(out))]
    hi = out[int(0.975 * len(out))]
    return lo, hi


def main(src, outdir):
    import random
    os.makedirs(os.path.expanduser(outdir), exist_ok=True)
    rows = list(csv.DictReader(open(src)))
    inten = {r["sequence"]: float(r["intensity"]) for r in rows}
    seqs = list(inten)
    n = len(seqs)

    # quartiles on the FULL dataset, so the class definition does not depend on the split
    order = sorted(seqs, key=lambda s: inten[s])
    q = n // 4
    bottom, top = set(order[:q]), set(order[-q:])

    dev = [s for s in seqs if hfrac(SPLIT_SALT, s) < DEV_FRACTION]
    reserved = [s for s in seqs if s not in set(dev)]
    print(f"## split (salt {SPLIT_SALT!r}, dev fraction {DEV_FRACTION})")
    print(f"total {n} | dev {len(dev)} ({len(dev)/n:.4f}) | reserved {len(reserved)} ({len(reserved)/n:.4f})")
    dev_top = [s for s in dev if s in top]
    dev_bot = [s for s in dev if s in bottom]
    print(f"dev top quartile {len(dev_top)} | dev bottom quartile {len(dev_bot)} | "
          f"dev mid {len(dev) - len(dev_top) - len(dev_bot)}")
    res_top = [s for s in reserved if s in top]
    res_bot = [s for s in reserved if s in bottom]
    print(f"reserved top {len(res_top)} | reserved bottom {len(res_bot)}")

    # dev pairs: every top x bottom combination within dev
    pairs = [(a, b) for a in dev_top for b in dev_bot]
    lab = ["E" if panel_score(a) > panel_score(b) else "K" for a, b in pairs]
    print(f"\n## dev pairs\ntotal {len(pairs)} | E {lab.count('E')} | K {lab.count('K')} "
          f"| K fraction {lab.count('K')/len(pairs):.4f}")
    kpairs = [p for p, l in zip(pairs, lab) if l == "K"]
    kpep = sorted({s for p in kpairs for s in p})
    print(f"peptides appearing in a dev K pair: {len(kpep)}")

    # FM subset, chosen FM-blind by hash rank
    pick_top = sorted(dev_top, key=lambda s: hfrac(PICK_SALT, s))[:N_PER_QUARTILE]
    pick_bot = sorted(dev_bot, key=lambda s: hfrac(PICK_SALT, s))[:N_PER_QUARTILE]
    fm_pairs = [(a, b) for a in pick_top for b in pick_bot]
    fm_lab = ["E" if panel_score(a) > panel_score(b) else "K" for a, b in fm_pairs]
    fm_k = [p for p, l in zip(fm_pairs, fm_lab) if l == "K"]
    print(f"\n## FM subset (salt {PICK_SALT!r}, {N_PER_QUARTILE} per quartile)")
    print(f"peptides {len(pick_top)+len(pick_bot)} | pairs {len(fm_pairs)} | "
          f"E {fm_lab.count('E')} | K {len(fm_k)}")

    # three nulls, on dev K pairs and on the FM subset's K pairs
    nulls = {"mass": mono_mass, "net_charge_pH7": net_charge, "GRAVY": gravy}
    rng = random.Random(BOOT_SEED)
    report = {}
    for name, label, ps in (("all dev K pairs", "dev_K", kpairs), ("FM-subset K pairs", "fm_K", fm_k)):
        print(f"\n## null baselines on {name} ({len(ps)} pairs)")
        peps = sorted({s for p in ps for s in p})
        for nm, fn in nulls.items():
            best, orient, raw, ties = acc_both(ps, fn)
            lo, hi = boot_ci(ps, fn, peps, rng)
            report[f"{label}:{nm}"] = dict(accuracy=best, orientation=orient,
                                           accuracy_higher_wins=raw, ties=ties, ci=[lo, hi])
            print(f"  {nm:16s} acc {best:.4f} ({orient:12s}) 95% CI [{lo:.4f}, {hi:.4f}] "
                  f"| 'higher wins' acc {raw:.4f} | ties {ties}")
        pb, po, pr, pt = acc_both(ps, panel_score)
        print(f"  {'panel W-R':16s} acc {pr:.4f} by construction on K pairs (ties {pt})")

    json.dump(dict(
        split=dict(salt=SPLIT_SALT, dev_fraction=DEV_FRACTION, n_total=n,
                   n_dev=len(dev), n_reserved=len(reserved),
                   dev_top=len(dev_top), dev_bottom=len(dev_bot),
                   reserved_top=len(res_top), reserved_bottom=len(res_bot)),
        fm_subset=dict(salt=PICK_SALT, n_per_quartile=N_PER_QUARTILE,
                       top=pick_top, bottom=pick_bot),
        dev_peptides=dev, dev_top=dev_top, dev_bottom=dev_bot,
        dev_pairs_E=lab.count("E"), dev_pairs_K=lab.count("K"),
        fm_pairs_K=[list(p) for p in fm_k], dev_pairs_K_list=[list(p) for p in kpairs],
        nulls=report, bootstrap=dict(replicates=BOOT, seed=BOOT_SEED, unit="peptide"),
    ), open(os.path.join(os.path.expanduser(outdir), "split.json"), "w"), indent=1)
    print(f"\nwrote {outdir}/split.json")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
