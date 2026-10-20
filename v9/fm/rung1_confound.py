"""V9-7, post hoc: is the rung 1 Gate N "pass" orthogonal information, or the subset's own shape?

Labelled **post hoc**: these diagnostics were written after rung 1's numbers were seen, and are
reported as such. They exist because the restated Gate N scores the FM on a subset **defined by
one descriptor being wrong**, and any model that correlates with that descriptor will score far
from 0.5 on that subset by construction, with no orthogonal information at all.

Code only, no FM call. Aggregates only (V9-X1).
"""
import csv, json, math, os, random, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from twin_count import mono_mass
from split_and_pairs import net_charge, gravy
import fm_gates as G

sp = json.load(open(os.path.expanduser("~/v9_data/split/split.json")))
fm = json.load(open(os.path.expanduser("~/v9_data/fm/rung1/fm_dev.json")))
inten = {r["sequence"]: float(r["intensity"]) for r in csv.DictReader(
    open(os.path.expanduser("~/v9_data/ds1_parsed/ds1.csv")))}
top, bot = sp["fm_subset"]["top"], sp["fm_subset"]["bottom"]
seq_of = {f"P{i:03d}": s for i, s in enumerate(top)}
seq_of.update({f"P{60+i:03d}": s for i, s in enumerate(bot)})
eads = {seq_of[p]: v["e_ads_min_eV"] for p, v in fm["results"].items()
        if v.get("e_ads_min_eV") is not None}
natoms = {seq_of[p]: v["n_atoms_peptide"] for p, v in fm["results"].items()}
kp = [tuple(p) for p in sp["fm_pairs_K"] if p[0] in eads and p[1] in eads]

FM = (lambda s: eads.get(s), True)
DESC = {"net_charge_pH7": (net_charge, True), "GRAVY": (gravy, True), "mass": (mono_mass, False)}
out = {"label": "post hoc, written after rung 1's numbers were seen"}

print("## 1. Does the FM agree with each descriptor, pair by pair, on the 323 K pairs?")
print("   (agreement = both order the pair the same way, whatever the truth is)")
for nm, (f, lw) in DESC.items():
    agree = n = ties = 0
    for s, w in kp:
        a, b = f(s), f(w)
        if a == b:
            ties += 1; continue
        d_pick_s = (a < b) if lw else (a > b)
        x, y = eads[s], eads[w]
        fm_pick_s = x < y
        n += 1; agree += (d_pick_s == fm_pick_s)
    out[f"fm_agreement_{nm}"] = dict(rate=agree / n, n=n, ties_excluded=ties)
    print(f"   FM vs {nm:16s} agreement {agree/n:.4f} on n={n} (ties excluded {ties})")

print("\n## 2. FM accuracy split by whether the primary descriptor was right or wrong")
f, lw = DESC["net_charge_pH7"]
right, wrong, tie = [], [], []
for s, w in kp:
    a, b = f(s), f(w)
    (tie if a == b else (right if ((a < b) if lw else (a > b)) else wrong)).append((s, w))
for nm, sub in (("net charge RIGHT", right), ("net charge WRONG", wrong), ("net charge TIED", tie)):
    if not sub:
        continue
    p = G.acc(sub, *FM)
    d, wp = G.boot_acc(sub, FM, random.Random(G.SEED))
    lo, hi = G.ci(d)
    out[f"fm_on_{nm.replace(' ','_')}"] = dict(n_pairs=len(sub), n_peptides=len(wp),
                                               fm_accuracy=p, ci=[lo, hi])
    print(f"   {nm:18s} n={len(sub):3d} pairs / {len(wp):2d} peptides   FM {p:.4f}  "
          f"95% CI [{lo:.4f}, {hi:.4f}]")

print("\n## 3. Rank correlation of E_ads with each descriptor and with the truth, over 120 peptides")
def spearman(u, v):
    def rank(z):
        o = sorted(range(len(z)), key=lambda i: z[i]); r = [0.0] * len(z); i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and z[o[j + 1]] == z[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ru, rv = rank(u), rank(v); n = len(u)
    mu, mv = sum(ru) / n, sum(rv) / n
    cov = sum((a - mu) * (b - mv) for a, b in zip(ru, rv))
    du = math.sqrt(sum((a - mu) ** 2 for a in ru)); dv = math.sqrt(sum((b - mv) ** 2 for b in rv))
    return cov / (du * dv) if du and dv else 0.0

seqs = sorted(eads)
x = [eads[s] for s in seqs]
for nm, f in (("net_charge_pH7", net_charge), ("GRAVY", gravy), ("mass", mono_mass),
              ("n_atoms_peptide", lambda s: natoms[s]), ("intensity (TRUTH)", lambda s: inten[s])):
    r = spearman(x, [f(s) for s in seqs])
    out[f"spearman_eads_{nm.split()[0]}"] = r
    print(f"   Spearman(E_ads, {nm:20s}) = {r:+.4f}")

print("\n## 4. Within-peptide spread of E_ads across the 30 rigid single points")
sds = sorted(v["e_ads_sd_eV"] for v in fm["results"].values() if v.get("e_ads_sd_eV"))
rngs = sorted(v["e_ads_range_eV"][1] - v["e_ads_range_eV"][0] for v in fm["results"].values()
              if v.get("e_ads_range_eV"))
mins = [v["e_ads_min_eV"] for v in fm["results"].values() if v.get("e_ads_min_eV") is not None]
q = lambda a, p: a[int(p * (len(a) - 1))]
out["within_peptide_sd_eV"] = dict(median=q(sds, .5), q25=q(sds, .25), q75=q(sds, .75), max=sds[-1])
out["within_peptide_range_eV"] = dict(median=q(rngs, .5), max=rngs[-1])
bsd = math.sqrt(sum((m - sum(mins) / len(mins)) ** 2 for m in mins) / (len(mins) - 1))
out["between_peptide_sd_of_minima_eV"] = bsd
print(f"   within-peptide SD of E_ads: median {q(sds,.5):.3f}, IQR [{q(sds,.25):.3f}, {q(sds,.75):.3f}], "
      f"max {sds[-1]:.3f} eV")
print(f"   within-peptide RANGE of E_ads: median {q(rngs,.5):.2f}, max {rngs[-1]:.2f} eV")
print(f"   between-peptide SD of the 120 minima: {bsd:.3f} eV")
print(f"   ratio median-within / between = {q(sds,.5)/bsd:.2f}")

json.dump(out, open(os.path.expanduser("~/v9_data/fm/rung1/confound.json"), "w"), indent=1)

print("\n## 5. Is the FM's sub-chance accuracy a PEPTIDE SIZE artefact?")
print("   David's spec: K pairs are where the published panel is wrong or tied; near-isobaric is")
print("   NOT required, so K pairs differ in size (median |delta n_atoms| within a K pair = 6).")
print("   If the rigid score is a steric-repulsion counter it ranks SMALLER peptides as better")
print("   binders, and in this data the HEAVIER peptide tends to be the stronger binder")
print("   (mass null 0.5511, 'higher wins'), so a size artefact drives accuracy BELOW 0.5.")
dn = sorted(abs(natoms[a] - natoms[b]) for a, b in kp)
qq = lambda A, pp: A[int(pp * (len(A) - 1))]
strata = [("|dn| <= 2", lambda a, b: abs(natoms[a]-natoms[b]) <= 2),
          ("|dn| 3..8",  lambda a, b: 3 <= abs(natoms[a]-natoms[b]) <= 8),
          ("|dn| >= 9",  lambda a, b: abs(natoms[a]-natoms[b]) >= 9)]
out["size_strata"] = {}
for nm, f in strata:
    sub = [(a, b) for a, b in kp if f(a, b)]
    if len(sub) < 10:
        continue
    p = G.acc(sub, *FM)
    d, wp = G.boot_acc(sub, FM, random.Random(G.SEED))
    lo, hi = G.ci(d)
    # how often does the FM simply pick the SMALLER peptide?
    sm = n2 = 0
    for a, b in sub:
        if natoms[a] == natoms[b]:
            continue
        n2 += 1
        sm += (eads[a] < eads[b]) == (natoms[a] < natoms[b])
    out["size_strata"][nm] = dict(n_pairs=len(sub), n_peptides=len(wp), fm_accuracy=p, ci=[lo, hi],
                                  fm_picks_smaller_rate=(sm / n2 if n2 else None), n_sized=n2)
    print(f"   {nm:11s} n={len(sub):3d} pairs / {len(wp):2d} peptides  FM acc {p:.4f} "
          f"95% CI [{lo:.4f}, {hi:.4f}]   FM picks the SMALLER peptide "
          f"{(sm/n2 if n2 else float('nan')):.4f} of the time")
# and the truth's own size dependence, for comparison
tr = sm2 = 0
for a, b in kp:
    if natoms[a] != natoms[b]:
        tr += 1; sm2 += natoms[a] < natoms[b]
print(f"   for reference, the STRONG binder is the smaller peptide {sm2/tr:.4f} of the time "
      f"(n={tr})")
out["truth_strong_is_smaller_rate"] = sm2 / tr
json.dump(out, open(os.path.expanduser("~/v9_data/fm/rung1/confound.json"), "w"), indent=1)
