"""V9-6 / V9-7: Gate M and the restated Gate N on the FM-evaluated dev peptides.

**Gate M** (unchanged): on dev K-stratum pairs, FM accuracy's 95 percent interval excludes 0.5.

**Gate N** (restated by David in the iteration 3 note, before any FM accuracy existed): on the
subset of dev K pairs **where the best descriptor is wrong**, the FM picks the stronger binder
with a 95 percent interval excluding 0.5.

*Gate order disclosure, required in every report from here on.* David wrote the original Gate N
as "the FM beats each null". The V9-4 null measurement (GRAVY 0.6911, net charge 0.6743) showed
that phrasing asks whether the FM beats a one-line descriptor, when the question is whether it
knows something the descriptors do not. He restated it **before any FM accuracy existed**, so the
change was made in ignorance of the outcome. Both forms are reported side by side forever: the
head-to-head paired difference against each of the three descriptors as a **diagnostic** (the
original form, computed exactly as V9-6 wrote it), and the orthogonal-information form as the
**gate**.

Which descriptor is "best" is fixed in `v9/fm/PREREG_3_DECISIONS.md`, before any FM call:
net charge at pH 7 is best on the 323 FM-subset K pairs the gate is scored on (0.7229) and is
the **primary** gate subset; GRAVY is best on the full 1,664-pair dev K set (0.6911) and is
reported **beside** it. Ties are not "wrong" and are excluded from a subset, with their count
reported.

Bootstrap is over peptides (10,000 replicates, seed 29): a replicate resamples the peptide pool
of the set in question and a pair contributes with weight = multiplicity(strong) * multiplicity(weak).
The FM and every null are evaluated on the identical replicate, so differences are genuinely paired.

Null orientation was fixed in V9-4 as the better of the two directions, which is the conservative
choice for the FM. The FM's own direction was fixed in V9-5 before any energy existed: lower (more
negative) E_ads = stronger binder.

Aggregates only (V9-X1). Usage: python fm_gates.py SPLIT_JSON DS1_CSV FM_JSON OUT_JSON
"""
import csv, json, math, os, random, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from twin_count import mono_mass, panel_score
from split_and_pairs import net_charge, gravy

BOOT, SEED = 10000, 29
PRIMARY_DESCRIPTOR = "net_charge_pH7"     # best on the 323 K pairs the gate is scored on
SECONDARY_DESCRIPTOR = "GRAVY"            # best on the full 1,664-pair dev K set


def acc(pairs, score, lower_wins, weights=None):
    num = den = 0.0
    for s, w in pairs:
        ws = 1.0 if weights is None else weights.get(s, 0) * weights.get(w, 0)
        if not ws:
            continue
        a, b = score(s), score(w)
        if a is None or b is None:
            continue
        den += ws
        if a == b:
            num += 0.5 * ws
        else:
            num += ws * ((a < b) if lower_wins else (a > b))
    return (num / den) if den else None


def ci(vals, lo=2.5, hi=97.5):
    v = sorted(x for x in vals if x is not None)
    if not v:
        return (None, None)
    return v[int(lo / 100 * len(v))], v[min(len(v) - 1, int(hi / 100 * len(v)))]


def boot_acc(pairs, scorer, rng):
    """Bootstrap FM accuracy over the peptide pool of `pairs`."""
    peps = sorted({s for p in pairs for s in p})
    out = []
    for _ in range(BOOT):
        w = Counter(peps[rng.randrange(len(peps))] for _ in range(len(peps)))
        out.append(acc(pairs, *scorer, weights=w))
    return out, peps


def wrong_subset(pairs, score, lower_wins):
    """Pairs where the descriptor strictly picks the WEAKER binder. Ties are not wrong."""
    wrong, ties = [], 0
    for s, w in pairs:
        a, b = score(s), score(w)
        if a == b:
            ties += 1
            continue
        if not ((a < b) if lower_wins else (a > b)):
            wrong.append((s, w))
    return wrong, ties


def fmt(x, n=4):
    return "n/a" if x is None else f"{x:.{n}f}"


def main(split_p, ds1_p, fm_p, out_p):
    sp = json.load(open(os.path.expanduser(split_p)))
    fm = json.load(open(os.path.expanduser(fm_p)))
    inten = {r["sequence"]: float(r["intensity"]) for r in csv.DictReader(open(os.path.expanduser(ds1_p)))}

    top, bot = sp["fm_subset"]["top"], sp["fm_subset"]["bottom"]
    seq_of = {f"P{i:03d}": s for i, s in enumerate(top)}
    seq_of.update({f"P{60+i:03d}": s for i, s in enumerate(bot)})
    eads = {seq_of[p]: v["e_ads_min_eV"] for p, v in fm["results"].items()
            if v.get("e_ads_min_eV") is not None}
    falling = [p for p, v in fm["results"].items() if v.get("still_falling")]
    done = set(eads)
    print(f"mode: {fm.get('mode')}   head: {fm.get('head')}   model: {fm.get('model')}")
    print(f"peptides with an FM energy: {len(done)} of {len(seq_of)}")
    print(f"peptides whose running minimum was still falling at the last evaluation: {len(falling)}")

    kp = [tuple(p) for p in sp["fm_pairs_K"] if p[0] in done and p[1] in done]
    ep = [(a, b) for a in top for b in bot
          if a in done and b in done and panel_score(a) > panel_score(b)]
    peps = sorted({s for p in kp for s in p})
    print(f"K pairs with both members evaluated: {len(kp)} over {len(peps)} peptides")
    print(f"E pairs with both members evaluated: {len(ep)}")

    scorers = {
        "FM_uma_oc20": (lambda s: eads.get(s), True),
        "mass": (mono_mass, False),
        "net_charge_pH7": (net_charge, True),
        "GRAVY": (gravy, True),
    }
    for nm in ("mass", "net_charge_pH7", "GRAVY"):
        f, lw = scorers[nm]
        if acc(kp, f, lw) < 0.5:
            scorers[nm] = (f, not lw)        # keep V9-4's better-orientation convention

    point = {nm: acc(kp, f, lw) for nm, (f, lw) in scorers.items()}
    rng = random.Random(SEED)
    draws = {nm: [] for nm in scorers}
    diffs = {nm: [] for nm in scorers if nm != "FM_uma_oc20"}
    for _ in range(BOOT):
        w = Counter(peps[rng.randrange(len(peps))] for _ in range(len(peps)))
        a_fm = acc(kp, *scorers["FM_uma_oc20"], weights=w)
        for nm, (f, lw) in scorers.items():
            v = acc(kp, f, lw, weights=w)
            draws[nm].append(v)
            if nm != "FM_uma_oc20" and v is not None and a_fm is not None:
                diffs[nm].append(a_fm - v)

    out = dict(mode=fm.get("mode"), head=fm.get("head"), model=fm.get("model"),
               n_peptides_evaluated=len(done), n_k_pairs=len(kp), n_k_peptides=len(peps),
               n_e_pairs=len(ep), n_still_falling=len(falling),
               bootstrap=dict(replicates=BOOT, seed=SEED, unit="peptide"),
               accuracy={}, gate_M=None, gate_N={},
               gate_N_headtohead_diagnostic={}, diagnostics={})
    print("\n## accuracy on all dev K pairs")
    for nm in scorers:
        lo, hi = ci(draws[nm])
        out["accuracy"][nm] = dict(point=point[nm], ci=[lo, hi],
                                   orientation="lower wins" if scorers[nm][1] else "higher wins")
        print(f"  {nm:16s} {fmt(point[nm])}  95% CI [{fmt(lo)}, {fmt(hi)}]"
              f"  ({'lower' if scorers[nm][1] else 'higher'} wins)")

    mlo, mhi = ci(draws["FM_uma_oc20"])
    gm = bool(mlo > 0.5 or mhi < 0.5)
    out["gate_M"] = dict(passed=gm, accuracy=point["FM_uma_oc20"], ci=[mlo, mhi], excludes_half=gm)
    print(f"\n## Gate M: FM CI [{fmt(mlo)}, {fmt(mhi)}] vs 0.5 -> {'PASSED' if gm else 'FAILED'}")

    # ---- Gate N, restated: orthogonal information on the descriptor-wrong subset ----
    print("\n## Gate N (restated): FM on the subset where the best descriptor is WRONG")
    subsets = {}
    for nm in ("net_charge_pH7", "GRAVY", "mass"):
        f, lw = scorers[nm]
        wrong, ties = wrong_subset(kp, f, lw)
        subsets[nm] = set(wrong)
        if not wrong:
            out["gate_N"][nm] = dict(n_pairs=0, note="empty subset")
            continue
        d, wp = boot_acc(wrong, scorers["FM_uma_oc20"], random.Random(SEED))
        p = acc(wrong, *scorers["FM_uma_oc20"])
        lo, hi = ci(d)
        role = ("PRIMARY GATE" if nm == PRIMARY_DESCRIPTOR else
                "secondary" if nm == SECONDARY_DESCRIPTOR else "diagnostic")
        ok = bool(lo is not None and (lo > 0.5 or hi < 0.5))
        out["gate_N"][nm] = dict(role=role, n_pairs=len(wrong), n_peptides=len(wp),
                                 ties_excluded=ties, fm_accuracy=p, ci=[lo, hi],
                                 excludes_half=ok, passed=ok)
        print(f"  {nm+'-wrong':22s} n={len(wrong):3d} pairs / {len(wp):2d} peptides "
              f"(ties excluded {ties:3d})  FM {fmt(p)}  95% CI [{fmt(lo)}, {fmt(hi)}]"
              f"  -> {'excludes 0.5' if ok else 'includes 0.5'}   [{role}]")
    allw = subsets["net_charge_pH7"] & subsets["GRAVY"] & subsets["mass"]
    out["gate_N"]["all_three_wrong_n_pairs"] = len(allw)
    out["gate_N"]["all_three_wrong_n_peptides"] = len({s for p in allw for s in p})
    print(f"  all three descriptors wrong: {len(allw)} pairs "
          f"({len({s for p in allw for s in p})} peptides) -- too thin for an interval, "
          f"reported as a count (PREREG_3_DECISIONS section 1)")
    gn = out["gate_N"].get(PRIMARY_DESCRIPTOR, {}).get("passed", False)
    out["gate_N"]["passed"] = bool(gn)
    out["gate_N"]["primary_descriptor"] = PRIMARY_DESCRIPTOR
    print(f"  Gate N (primary, {PRIMARY_DESCRIPTOR}-wrong) -> {'PASSED' if gn else 'FAILED'}")

    # ---- the ORIGINAL Gate N, kept as a diagnostic, computed exactly as V9-6 wrote it ----
    print("\n## Original Gate N form, now a DIAGNOSTIC: paired difference FM - null, all K pairs")
    alln = True
    for nm in diffs:
        lo, hi = ci(diffs[nm])
        med = sorted(diffs[nm])[len(diffs[nm]) // 2]
        ok = bool(lo > 0)
        alln &= ok
        out["gate_N_headtohead_diagnostic"][nm] = dict(
            beats_null=ok, diff_point=point["FM_uma_oc20"] - point[nm], diff_median=med, ci=[lo, hi])
        print(f"  FM - {nm:16s} {point['FM_uma_oc20']-point[nm]:+.4f}  95% CI "
              f"[{lo:+.4f}, {hi:+.4f}] -> {'above zero' if ok else 'spans zero'}")
    out["gate_N_headtohead_diagnostic"]["beats_all"] = alln
    print(f"  beats all three -> {alln}  (DIAGNOSTIC ONLY; the gate is the subset form above)")

    # ---- diagnostics ----
    common = [s for s in eads if s in inten]
    x = [eads[s] for s in common]; y = [inten[s] for s in common]

    def spearman(u, v):
        def rank(z):
            o = sorted(range(len(z)), key=lambda i: z[i])
            r = [0.0] * len(z); i = 0
            while i < len(o):
                j = i
                while j + 1 < len(o) and z[o[j + 1]] == z[o[i]]:
                    j += 1
                for k in range(i, j + 1):
                    r[o[k]] = (i + j) / 2 + 1
                i = j + 1
            return r
        ru, rv = rank(u), rank(v)
        n = len(u); mu = sum(ru) / n; mv = sum(rv) / n
        cov = sum((a - mu) * (b - mv) for a, b in zip(ru, rv))
        du = math.sqrt(sum((a - mu) ** 2 for a in ru)); dv = math.sqrt(sum((b - mv) ** 2 for b in rv))
        return cov / (du * dv) if du and dv else 0.0

    rho = spearman(x, y)
    tset = [s for s in common if s in set(top)]; bset = [s for s in common if s in set(bot)]
    pairs_tb = [(a, b) for a in tset for b in bset]
    auc = (sum((eads[a] < eads[b]) + 0.5 * (eads[a] == eads[b]) for a, b in pairs_tb) / len(pairs_tb)
           if pairs_tb else None)
    acc_e = acc(ep, *scorers["FM_uma_oc20"]) if ep else None

    # David's rung 2 requirement 2: within-peptide spread against between-peptide signal.
    # Free in rigid mode too, so it is computed in both.
    sds = [v["e_ads_sd_eV"] for v in fm["results"].values() if v.get("e_ads_sd_eV") is not None]
    mins = [v["e_ads_min_eV"] for v in fm["results"].values() if v.get("e_ads_min_eV") is not None]
    med_sd = sorted(sds)[len(sds) // 2] if sds else None
    bet_sd = (math.sqrt(sum((m - sum(mins) / len(mins)) ** 2 for m in mins) / (len(mins) - 1))
              if len(mins) > 1 else None)
    ratio = (med_sd / bet_sd) if (med_sd and bet_sd) else None
    out["diagnostics"] = dict(spearman_eads_vs_intensity=rho, n_spearman=len(common),
                              auc_top_vs_bottom=auc, n_auc_pairs=len(pairs_tb),
                              accuracy_dev_E_pairs=acc_e, n_e_pairs=len(ep),
                              within_peptide_sd_median_eV=med_sd,
                              between_peptide_sd_of_minima_eV=bet_sd,
                              within_over_between=ratio,
                              n_still_falling=len(falling), n_peptides_with_sd=len(sds))
    print(f"\n## diagnostics\n  Spearman(E_ads, intensity) over {len(common)} peptides: {rho:+.4f}")
    print(f"  AUC top vs bottom quartile ({len(pairs_tb)} pairs): {fmt(auc)}")
    print(f"  accuracy on dev E pairs ({len(ep)}): {fmt(acc_e)}")
    print(f"  within-peptide SD of E_ads, median: {fmt(med_sd, 3)} eV")
    print(f"  between-peptide SD of the minima:   {fmt(bet_sd, 3)} eV")
    print(f"  ratio within/between: {fmt(ratio, 2)}   "
          f"({'WITHIN SWAMPS BETWEEN' if (ratio or 0) > 1 else 'between exceeds within'})")

    json.dump(out, open(os.path.expanduser(out_p), "w"), indent=1)
    print(f"\nwrote {out_p}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
