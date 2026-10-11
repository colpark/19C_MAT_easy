# Shadow D for stage 1b (V5_SPEC C.6): brief for a fresh implementation

You implement the separation D of PanelBench v5 stage 1b from the written specification only, as an independent check of the
reference implementation. Do not read, import, grep or copy anything under `v5/mcenv/`, `v5/validation/shadow_d.py` or any other
existing implementation of D. Read only:

- `v5/V5_SPEC.md`: section 1.2 (instrument model), section 3.1 (D), Appendix A (exact forward model and D) and Appendix C (stage 1b:
  hold worlds, shared scale, time grid).
- `v5/stage1b/WORLDS.json`: every stage 1b world's truth groups, hidden nuisances, scales, backgrounds and the other-side branches D
  minimises over.
- `v5/stage1b/peak_tables.json`: per phase, radiation and intensity key, the hkl list and intensity per unit weight fraction, and the
  lattice rule of each phase.
- `v5/stage1b/validation/shadow_plans.json`: per world, a list of measurement plans (each plan already starts with m0) and the
  reference D for each plan (field `D`). Use the reference D only after you have computed your own, to compare.

Write your implementation as one self-contained file `v5/stage1b/validation/shadow_d_1b.py` (numpy and scipy only, run with
`~/v5env/bin/python`), and run it over every plan of every world in `shadow_plans.json`. Write `v5/stage1b/validation/shadow_results.json`:
per world and plan, your D, the reference D, and whether they agree. Agreement: within 1 % relative, or within 0.05 absolute where the
reference D is below 5. D is a minimum over nuisances; where your D is lower than the reference by more than the tolerance, say so
explicitly (the reference may be under-minimised); where it is higher, your minimiser may be stuck: search harder before reporting.

Use multiprocessing (at most 18 workers, OPENBLAS_NUM_THREADS=1) — there are about 28 worlds x 15 plans. Report: number of plans, number
agreeing, and every disagreement with both values and the world, plus anything in the spec you found ambiguous and how you resolved it.
