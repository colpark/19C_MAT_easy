"""V9-2: count the twin pairs that decide whether v9 has a benchmark.

Reads ~/v9_data/ds1_parsed/ds1.csv (sequence, intensity, class_si) and emits ONLY aggregate
counts to stdout. Individual pairs go to twins.json, which the builder does not read (V9-X1).

A twin pair is two peptides a cheap mass measurement cannot separate but whose truth classes are
opposite: one in the top affinity quartile, one in the bottom.

Usage: python3 -I twin_count.py IN.csv OUT_JSON
"""
import csv, json, os, sys
from collections import Counter, defaultdict

# Monoisotopic residue masses, Da (IUPAC / Unimod standard values).
# Note L and I are exactly equal (both C6H11NO), so an L/I swap is unresolvable by any mass
# measurement; that is a property of the chemistry, not of our instrument model.
RES = {
    "G": 57.02146, "A": 71.03711, "S": 87.03203, "P": 97.05276, "V": 99.06841,
    "T": 101.04768, "C": 103.00919, "L": 113.08406, "I": 113.08406, "N": 114.04293,
    "D": 115.02694, "Q": 128.05858, "K": 128.09496, "E": 129.04259, "M": 131.04049,
    "H": 137.05891, "F": 147.06841, "R": 156.10111, "Y": 163.06333, "W": 186.07931,
}
H2O = 18.0105646863
TOLS = [1.0, 0.5, 0.1, 0.05, 0.01]


def mono_mass(seq):
    return sum(RES[a] for a in seq) + H2O


def panel_score(seq):
    """The published sequence rules as code, and nothing else.

    Janairo, RSC Adv. 2023 (doi 10.1039/d3ra04269c): about 84% of the high-binding (Class A)
    rules involve tryptophan and no Class A rule involves arginine, while about 46% of the
    low-binding (Class B) rules involve arginine, each with confidence 1.0. The panel therefore
    scores tryptophan as favouring binding and arginine as opposing it.
    """
    return seq.count("W") - seq.count("R")


def main(src, out_json):
    rows = list(csv.DictReader(open(src)))
    seqs = [r["sequence"] for r in rows]
    inten = {r["sequence"]: float(r["intensity"]) for r in rows}
    mass = {s: mono_mass(s) for s in seqs}
    n = len(seqs)

    # ---- 1. mass distribution
    ms = sorted(mass.values())
    print(f"## 1. mass distribution\npeptides: {n}")
    print(f"monoisotopic mass range: {ms[0]:.5f} to {ms[-1]:.5f} Da  (span {ms[-1]-ms[0]:.3f})")
    print(f"median mass: {ms[n//2]:.5f} Da   mean: {sum(ms)/n:.5f} Da")
    hist = Counter(int(m // 50) * 50 for m in ms)
    print("histogram, 50 Da bins:")
    for b in sorted(hist):
        print(f"  {b:5d}-{b+49:5d} Da  {hist[b]:5d}  {'#' * (hist[b] * 60 // max(hist.values()))}")

    # ---- quartile classes from the continuous intensity, by rank so the sizes are exact
    order = sorted(seqs, key=lambda s: inten[s])
    qsize = n // 4
    bottom, top = set(order[:qsize]), set(order[-qsize:])
    q1_b, q3_b = inten[order[qsize - 1]], inten[order[-qsize]]
    print(f"\n## quartile classes\nbottom quartile (weak): {len(bottom)} peptides, intensity <= {q1_b:.0f}")
    print(f"top quartile (strong) : {len(top)} peptides, intensity >= {q3_b:.0f}")
    print(f"gap between the two quartile boundaries: {q3_b - q1_b:.0f} intensity units "
          f"({(q3_b - q1_b) / (ms and 1):.0f}); full range {min(inten.values()):.0f} to {max(inten.values()):.0f}")

    def cls(s):
        return "top" if s in top else ("bottom" if s in bottom else "mid")

    # ---- 2, 3, 4. pair counting on the mass-sorted list
    by_mass = sorted(seqs, key=lambda s: mass[s])
    results, twin_sets = {}, {}
    for tol in TOLS:
        near = opp = 0
        twins = []
        j0 = 0
        for i in range(n):
            si = by_mass[i]
            for j in range(i + 1, n):
                sj = by_mass[j]
                if mass[sj] - mass[si] > tol:
                    break
                near += 1
                ci, cj = cls(si), cls(sj)
                if {ci, cj} == {"top", "bottom"}:
                    opp += 1
                    strong, weak = (si, sj) if ci == "top" else (sj, si)
                    twins.append((strong, weak, round(abs(mass[si] - mass[sj]), 6)))
        results[tol] = (near, opp)
        twin_sets[tol] = twins
        rp = ms[n // 2] / tol
        print(f"\ntol {tol:5.2f} Da | near-isobaric pairs {near:8d} | opposite-quartile twins {opp:6d} "
              f"| implied resolving power m/dm ~ {rp:7.0f}")

    # exact ties
    exact_mass = defaultdict(list)
    comp = defaultdict(list)
    for s in seqs:
        exact_mass[round(mass[s], 6)].append(s)
        comp["".join(sorted(s))].append(s)

    def pairs_in(groups):
        tot = opp = 0
        out = []
        for g in groups.values():
            for a in range(len(g)):
                for b in range(a + 1, len(g)):
                    tot += 1
                    if {cls(g[a]), cls(g[b])} == {"top", "bottom"}:
                        opp += 1
                        strong, weak = (g[a], g[b]) if cls(g[a]) == "top" else (g[b], g[a])
                        out.append((strong, weak, 0.0))
        return tot, opp, out

    pt, po, perm_twins = pairs_in(comp)
    mt, mo, mass_twins = pairs_in(exact_mass)
    print(f"\n## 4. unresolvable-by-any-mass pairs")
    print(f"same amino-acid composition (permutations): {pt} pairs, of which opposite-quartile twins {po}")
    print(f"exactly equal monoisotopic mass (includes L/I swaps): {mt} pairs, of which twins {mo}")

    # ---- 5. heuristic panel stratification
    print(f"\n## 5. heuristic panel strata (W count minus R count; code only)")
    strata = {}
    for tol in TOLS:
        e = k = 0
        for strong, weak, dm in twin_sets[tol]:
            e += panel_score(strong) > panel_score(weak)
            k += panel_score(strong) <= panel_score(weak)
        strata[tol] = (e, k)
        tot = e + k
        print(f"  tol {tol:5.2f} Da | twins {tot:6d} | E (panel right) {e:6d} | K (panel wrong or tied) {k:6d}"
              + (f" | panel accuracy {e/tot:.3f}" if tot else ""))
    pe = sum(panel_score(a) > panel_score(b) for a, b, _ in perm_twins)
    print(f"  permutation twins: {po} | E {pe} | K {po - pe}")
    me = sum(panel_score(a) > panel_score(b) for a, b, _ in mass_twins)
    print(f"  equal-mass twins : {mo} | E {me} | K {mo - me}")

    # panel sanity on the whole labelled set, for context only
    acc = sum((panel_score(s) > 0) == (s in top) for s in list(top) + list(bottom))
    print(f"  panel sign vs quartile label over all {len(top)+len(bottom)} quartile peptides: "
          f"{acc}/{len(top)+len(bottom)} = {acc/(len(top)+len(bottom)):.3f}")

    json.dump(dict(
        source=os.path.basename(src), n_peptides=n,
        quartile_boundaries=dict(bottom_max=q1_b, top_min=q3_b),
        panel="W count minus R count (Janairo RSC Adv 2023 rules, code only)",
        tolerances={str(t): dict(near_isobaric=results[t][0], twins=results[t][1],
                                 E=strata[t][0], K=strata[t][1],
                                 pairs=[dict(strong=a, weak=b, dmass=d,
                                             panel=("E" if panel_score(a) > panel_score(b) else "K"))
                                        for a, b, d in twin_sets[t]])
                     for t in TOLS},
        permutation_twins=[dict(strong=a, weak=b, dmass=d,
                                panel=("E" if panel_score(a) > panel_score(b) else "K"))
                           for a, b, d in perm_twins],
        equal_mass_twins=[dict(strong=a, weak=b, dmass=d,
                               panel=("E" if panel_score(a) > panel_score(b) else "K"))
                          for a, b, d in mass_twins],
    ), open(out_json, "w"), indent=1)
    print(f"\nwrote {out_json} (not read back by the builder)")


if __name__ == "__main__":
    main(sys.argv[1], os.path.expanduser(sys.argv[2]))
