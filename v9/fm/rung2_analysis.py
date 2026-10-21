"""V9-8: the three requirements David attached to rung 2, plus two sensitivity runs.

Requirement 1 -- record the minimum energy over each trajectory as well as the final energy.
  Reported as the count of relaxations whose final energy is **not** the trajectory minimum,
  with the size of every gap, and the gate re-scored on trajectory minima instead of finals.

Requirement 2 -- report within-peptide spread beside between-peptide spread of the minima.
  "If within swamps between, the minimum is noise." Reported as the median and the full
  distribution of the within-peptide SD of the 9 E_ads values, beside the SD of the 59
  per-peptide minima, and as the one-way variance decomposition (ICC) over the same numbers.

Requirement 3 -- report the running minimum against evaluation count and mark a peptide
  **undetermined** if still falling. Reported per peptide, with the gate re-scored on the
  determined subset only.

Also here, because they are the same filtering machinery: the two relaxations that hit the
1000-step cap are named, and a filtered FM json is written for each sensitivity run so
`fm_gates.py` -- the pre-registered estimator, untouched -- scores it.

Post hoc: this script was written after rung 2's numbers existed. The gate values it feeds
to fm_gates.py are sensitivity checks on a gate that was already scored on the full set in
`out/gates_rung2.json`; the full set is the pre-registered answer.

Usage: python rung2_analysis.py FM_JSON OUTDIR
"""
import json, os, statistics as st, sys


def within_sd(p):
    es = [r["e_ads_eV"] for r in p["rows"] if not r["refused"]]
    return st.stdev(es) if len(es) > 1 else None


def main(fm_p, outdir):
    d = json.load(open(os.path.expanduser(fm_p)))
    R = d["results"]
    os.makedirs(outdir, exist_ok=True)
    rows = [(p["pid"], r) for p in R.values() for r in p["rows"] if not r["refused"]]
    out = dict(n_peptides=len(R), n_complex_relaxations=len(rows),
               n_relaxations_total=d["n_relaxations"], t_per_relaxation_s=d["t_per_relaxation_s"],
               elapsed_gpu_hours=d["elapsed_gpu_hours"], stopped_on_budget=d.get("stopped_on_budget"))

    # ---- requirement 1: trajectory minimum against final energy
    gaps = [(pid, r["k"], r["j"], r["e_ads_eV"], r["e_ads_traj_min_eV"],
             round(r["e_ads_eV"] - r["e_ads_traj_min_eV"], 4), r["steps"], r["hit_cap"])
            for pid, r in rows if not r["final_is_traj_min"]]
    pept_gap = [(p["pid"], p["e_ads_min_eV"], p["e_ads_min_traj_eV"])
                for p in R.values() if abs(p["e_ads_min_eV"] - p["e_ads_min_traj_eV"]) > 1e-9]
    out["requirement_1_trajectory_minimum"] = dict(
        n_relaxations=len(rows), n_final_not_traj_min=len(gaps),
        gaps=gaps, max_gap_eV=(max(g[5] for g in gaps) if gaps else 0.0),
        n_peptides_whose_minimum_differs=len(pept_gap), peptides_whose_minimum_differs=pept_gap)

    # ---- convergence and cost
    steps = [r["steps"] for _, r in rows]
    caps = [(pid, r["k"], r["j"], r["steps"], r["fmax"]) for pid, r in rows if r["hit_cap"]]
    out["convergence"] = dict(
        max_steps=d["max_steps"], fmax_target=d["fmax_target"],
        steps_mean=round(st.mean(steps), 1), steps_median=st.median(steps),
        steps_min=min(steps), steps_max=max(steps),
        n_hit_cap=len(caps), cap_hits=caps,
        n_fmax_above_target=sum(1 for _, r in rows if r["fmax"] > d["fmax_target"]),
        max_final_fmax=max(r["fmax"] for _, r in rows))

    # ---- requirement 2: within against between
    w = sorted([(p["pid"], within_sd(p)) for p in R.values() if within_sd(p) is not None],
               key=lambda t: t[1])
    ws = [x for _, x in w]
    mins = [p["e_ads_min_eV"] for p in R.values()]
    means = [p["e_ads_mean_eV"] for p in R.values()]
    q = lambda xs, f: sorted(xs)[min(len(xs) - 1, int(f * len(xs)))]
    between_min = st.stdev(mins)
    # one-way decomposition on the raw 9 values per peptide (not the minima)
    allv = [r["e_ads_eV"] for _, r in rows]
    grand = st.mean(allv)
    k = st.mean([sum(1 for r in p["rows"] if not r["refused"]) for p in R.values()])
    ms_b = sum(sum(1 for r in p["rows"] if not r["refused"]) * (p["e_ads_mean_eV"] - grand) ** 2
               for p in R.values()) / (len(R) - 1)
    ms_w = sum((r["e_ads_eV"] - R[pid]["e_ads_mean_eV"]) ** 2 for pid, r in rows) / (len(rows) - len(R))
    var_b = max(0.0, (ms_b - ms_w) / k)
    icc = var_b / (var_b + ms_w) if (var_b + ms_w) else None
    out["requirement_2_spread"] = dict(
        within_peptide_sd_of_9_values=dict(
            median=round(st.median(ws), 3), mean=round(st.mean(ws), 3),
            iqr=[round(q(ws, 0.25), 3), round(q(ws, 0.75), 3)],
            min=[w[0][0], round(w[0][1], 3)], max=[w[-1][0], round(w[-1][1], 3)]),
        between_peptide_sd_of_minima=round(between_min, 3),
        between_peptide_sd_of_means=round(st.stdev(means), 3),
        ratio_median_within_over_between_minima=round(st.median(ws) / between_min, 3),
        within_swamps_between=bool(st.median(ws) > between_min),
        variance_decomposition=dict(ms_between=round(ms_b, 3), ms_within=round(ms_w, 3),
                                   var_between=round(var_b, 3), icc=round(icc, 3) if icc else None,
                                   note="ICC on the 9 raw E_ads values per peptide; the gate uses "
                                        "the minimum, which is a different statistic, so this is a "
                                        "diagnostic on the underlying scatter, not on the gate."),
        minima_eV=dict(median=round(st.median(mins), 3), min=round(min(mins), 3), max=round(max(mins), 3)))

    # ---- requirement 3: running minimum against evaluation count
    und = sorted(p["pid"] for p in R.values() if p["still_falling"])
    out["requirement_3_running_minimum"] = dict(
        n_undetermined=len(und), undetermined=und,
        rule="still falling = the running minimum fell during the last quarter of evaluations",
        running_minima={p["pid"]: [round(x, 4) for x in p["running_min_eV"]] for p in R.values()},
        eval_at_which_minimum_was_reached={
            p["pid"]: 1 + p["running_min_eV"].index(min(p["running_min_eV"]))
            for p in R.values()},
        n_whose_minimum_came_in_the_last_third=sum(
            1 for p in R.values()
            if p["running_min_eV"].index(min(p["running_min_eV"])) >= (2 * len(p["running_min_eV"])) // 3))

    # ---- filtered FM jsons for the sensitivity gate runs
    drop_cap = sorted({pid for pid, _, _, _, _ in caps})
    for tag, drop in (("determined_only", set(und)),
                      ("no_cap_hit_peptides", set(drop_cap)),
                      ("determined_and_no_cap", set(und) | set(drop_cap))):
        f = dict(d)
        f["results"] = {k2: v for k2, v in R.items() if k2 not in drop}
        f["filter"] = dict(tag=tag, dropped=sorted(drop), n_kept=len(f["results"]))
        json.dump(f, open(os.path.join(outdir, f"rung2_{tag}.json"), "w"), indent=1)
    # requirement 1's alternative scoring: trajectory minima in place of finals
    f = dict(d)
    f["results"] = {k2: dict(v, e_ads_min_eV=v["e_ads_min_traj_eV"]) for k2, v in R.items()}
    f["filter"] = dict(tag="traj_minima", note="per-peptide minimum taken over trajectory minima")
    json.dump(f, open(os.path.join(outdir, "rung2_traj_minima.json"), "w"), indent=1)
    out["sensitivity_files_written"] = ["determined_only", "no_cap_hit_peptides",
                                        "determined_and_no_cap", "traj_minima"]
    out["peptides_dropped"] = dict(undetermined=und, cap_hit=drop_cap)

    print(f"relaxations {len(rows)}  final-not-traj-min {len(gaps)}  cap hits {len(caps)}")
    print(f"steps mean {out['convergence']['steps_mean']} median {out['convergence']['steps_median']} "
          f"max {out['convergence']['steps_max']}")
    r2 = out["requirement_2_spread"]
    print(f"within-peptide SD median {r2['within_peptide_sd_of_9_values']['median']} eV "
          f"IQR {r2['within_peptide_sd_of_9_values']['iqr']}")
    print(f"between-peptide SD of minima {r2['between_peptide_sd_of_minima']} eV  "
          f"ratio {r2['ratio_median_within_over_between_minima']}  "
          f"within swamps between: {r2['within_swamps_between']}")
    print(f"ICC on raw values {r2['variance_decomposition']['icc']}")
    print(f"undetermined {len(und)}: {und}")
    json.dump(out, open(os.path.join(outdir, "rung2_analysis.json"), "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
