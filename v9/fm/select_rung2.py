"""V9-8 step 0: pick rung 2's 60 peptides from rung 1's 120, by the rule fixed before rung 1 ran.

Rule B of `v9/fm/PREREG_3_DECISIONS.md` section 2, committed before the first FM call of
iteration 3: within each quartile, sort by the number of FM-subset K pairs the peptide
participates in (descending), break ties by hfrac(PICK_SALT, sequence) ascending, take the
first 30. Rule A (hash order alone) was rejected in advance because it keeps only 110 of the
323 K pairs against rule B's 270.

This script reads **no FM output of any kind**. K-pair membership comes from monoisotopic mass
and the published sequence rule, both code-only and both frozen in V9-4.

Writes a pid list and prints aggregates only (V9-X1).

Usage: python select_rung2.py SPLIT_JSON OUT_JSON
"""
import json, os, sys
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
from split_and_pairs import hfrac, net_charge, gravy, PICK_SALT
from twin_count import mono_mass

N_PER_QUARTILE = 30


def main(split_p, out_p):
    sp = json.load(open(os.path.expanduser(split_p)))
    top, bot = sp["fm_subset"]["top"], sp["fm_subset"]["bottom"]
    kp = [tuple(p) for p in sp["fm_pairs_K"]]
    pid_of = {s: f"P{i:03d}" for i, s in enumerate(top)}
    pid_of.update({s: f"P{60+i:03d}" for i, s in enumerate(bot)})

    deg = Counter()
    for s, w in kp:
        deg[s] += 1; deg[w] += 1

    def pick(pool):
        return sorted(pool, key=lambda s: (-deg[s], hfrac(PICK_SALT, s)))[:N_PER_QUARTILE]

    sel_top, sel_bot = pick(top), pick(bot)
    sel = set(sel_top + sel_bot)
    kept = [p for p in kp if p[0] in sel and p[1] in sel]
    kept_peps = sorted({s for p in kept for s in p})

    def wrong(score, lower_wins, pairs):
        n = 0
        for s, w in pairs:
            a, b = score(s), score(w)
            if a != b and not ((a < b) if lower_wins else (a > b)):
                n += 1
        return n

    desc = dict(net_charge_pH7=wrong(net_charge, True, kept),
                GRAVY=wrong(gravy, True, kept),
                mass=wrong(mono_mass, False, kept))
    out = dict(rule="B: K-pair degree descending, then hfrac(PICK_SALT, seq) ascending",
               rule_fixed_in="v9/fm/PREREG_3_DECISIONS.md section 2, before the first FM call",
               pick_salt=PICK_SALT, n_per_quartile=N_PER_QUARTILE,
               reads_fm_output=False,
               pids_top=sorted(pid_of[s] for s in sel_top),
               pids_bottom=sorted(pid_of[s] for s in sel_bot),
               n_k_pairs_kept=len(kept), n_k_pairs_total=len(kp),
               n_k_peptides_kept=len(kept_peps),
               descriptor_wrong_pairs_kept=desc,
               k_degree_of_selected=sorted((deg[s] for s in sel), reverse=True))
    print(f"rung 2 selection, rule B: {len(sel_top)} top + {len(sel_bot)} bottom = {len(sel)} peptides")
    print(f"K pairs kept: {len(kept)} of {len(kp)} over {len(kept_peps)} peptides")
    print(f"descriptor-wrong K pairs kept: {desc}")
    print(f"K-degree of the 60: max {max(deg[s] for s in sel)}, "
          f"min {min(deg[s] for s in sel)}, zero-degree {sum(1 for s in sel if deg[s]==0)}")
    json.dump(out, open(os.path.expanduser(out_p), "w"), indent=1)
    print(f"wrote {out_p}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
