"""V9-6: Gate M and Gate N on the FM-evaluated dev peptides, plus the three diagnostics.

Gate M: on dev K-stratum pairs, FM accuracy's 95 percent interval excludes 0.5.
Gate N: FM accuracy exceeds each null, with the PAIRED difference's interval above zero.

Bootstrap is over peptides (10,000 replicates, seed 29): a replicate resamples the peptide pool
and a pair contributes with weight = multiplicity(strong) * multiplicity(weak). The FM and every
null are evaluated on the identical replicate, so the difference is genuinely paired.

Null orientation was fixed in V9-4 as the better of the two directions, which is the conservative
choice for the FM. The FM's own direction was fixed before any energy existed: lower (more
negative) E_ads = stronger binder.

Aggregates only (V9-X1). Usage: python fm_gates.py SPLIT_JSON DS1_CSV FM_JSON OUT_JSON
"""
import csv, json, os, random, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from twin_count import mono_mass, panel_score
from split_and_pairs import net_charge, gravy

BOOT, SEED = 10000, 29


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


def main(split_p, ds1_p, fm_p, out_p):
    sp = json.load(open(os.path.expanduser(split_p)))
    fm = json.load(open(os.path.expanduser(fm_p)))
    inten = {r["sequence"]: float(r["intensity"]) for r in csv.DictReader(open(os.path.expanduser(ds1_p)))}

    top, bot = sp["fm_subset"]["top"], sp["fm_subset"]["bottom"]
    seq_of = {f"P{i:03d}": s for i, s in enumerate(top)}
    seq_of.update({f"P{60+i:03d}": s for i, s in enumerate(bot)})
    eads = {seq_of[p]: v["e_ads_min_eV"] for p, v in fm["results"].items()
            if v.get("e_ads_min_eV") is not None}
    undet = [p for p, v in fm["results"].items() if v.get("undetermined")]
    done = set(eads)
    print(f"peptides with an FM energy: {len(done)} of {len(seq_of)}  (undetermined {len(undet)})")

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

    out = dict(n_peptides_evaluated=len(done), n_k_pairs=len(kp), n_k_peptides=len(peps),
               n_e_pairs=len(ep), bootstrap=dict(replicates=BOOT, seed=SEED, unit="peptide"),
               accuracy={}, gate_M=None, gate_N={}, diagnostics={})
    print("\n## accuracy on dev K pairs")
    for nm in scorers:
        lo, hi = ci(draws[nm])
        out["accuracy"][nm] = dict(point=point[nm], ci=[lo, hi],
                                   orientation="lower wins" if scorers[nm][1] else "higher wins")
        print(f"  {nm:16s} {point[nm]:.4f}  95% CI [{lo:.4f}, {hi:.4f}]"
              f"  ({'lower' if scorers[nm][1] else 'higher'} wins)")

    mlo, mhi = ci(draws["FM_uma_oc20"])
    gm = bool(mlo > 0.5 or mhi < 0.5)
    out["gate_M"] = dict(passed=gm, accuracy=point["FM_uma_oc20"], ci=[mlo, mhi],
                         excludes_half=gm)
    print(f"\n## Gate M: FM CI [{mlo:.4f}, {mhi:.4f}] vs 0.5 -> {'PASSED' if gm else 'FAILED'}")

    print("\n## Gate N: paired difference FM - null on identical K pairs")
    alln = True
    for nm in diffs:
        lo, hi = ci(diffs[nm])
        med = sorted(diffs[nm])[len(diffs[nm]) // 2]
        ok = bool(lo > 0)
        alln &= ok
        out["gate_N"][nm] = dict(passed=ok, diff_point=point["FM_uma_oc20"] - point[nm],
                                 diff_median=med, ci=[lo, hi])
        print(f"  FM - {nm:16s} {point['FM_uma_oc20']-point[nm]:+.4f}  95% CI "
              f"[{lo:+.4f}, {hi:+.4f}] -> {'PASSED' if ok else 'FAILED'}")
    out["gate_N"]["all_passed"] = alln
    print(f"  Gate N overall -> {'PASSED' if alln else 'FAILED'}")

    # diagnostics
    import math
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
    auc = sum((eads[a] < eads[b]) + 0.5 * (eads[a] == eads[b]) for a, b in pairs_tb) / len(pairs_tb)
    acc_e = acc(ep, *scorers["FM_uma_oc20"])
    out["diagnostics"] = dict(spearman_eads_vs_intensity=rho, n_spearman=len(common),
                              auc_top_vs_bottom=auc, n_auc_pairs=len(pairs_tb),
                              accuracy_dev_E_pairs=acc_e, n_e_pairs=len(ep))
    print(f"\n## diagnostics\n  Spearman(E_ads, intensity) over {len(common)} peptides: {rho:+.4f}")
    print(f"  AUC top vs bottom quartile ({len(pairs_tb)} pairs): {auc:.4f}")
    print(f"  accuracy on dev E pairs ({len(ep)}): {acc_e:.4f}")

    json.dump(out, open(os.path.expanduser(out_p), "w"), indent=1)
    print(f"\nwrote {out_p}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
