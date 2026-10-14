# Shadow D for PanelBench v6 B1 (V6-9): brief for a fresh implementation

You implement the separation D of PanelBench from the written specification only, as an independent check of the reference
implementation on the B1 bench worlds. Do not read, import, grep or copy anything under `v5/mcenv/` or `v6/mcenv/`, any `shadow_d*.py`
file, `v6/bench/*.py`, or any other existing implementation of D. Read only:

- `v5/V5_SPEC.md`: section 1.2 (instrument model), section 3.1 (D) and Appendix A (exact forward model and D).
- `v6/bench/shadow/WORLDS.json`: both twins of every B1 compound (60 worlds): truth groups, hidden nuisances, scales, backgrounds and the
  other-side branches D minimises over. Every B1 branch is fixed (lo == hi == []): one other polymorph of the compound per branch; D is
  the minimum over the branches.
- `v6/bench/shadow/peak_tables.json`: per phase, radiation and intensity key, the hkl list and intensity per unit weight fraction, and the
  lattice rule of each phase (a reference matrix; lattice_scale is 1 for every B1 phase).
- `v6/bench/shadow/shadow_plans.json`: per world, a list of plans; each plan lists every measurement D is computed on (m0 is listed
  explicitly where it counts). The field `D` is the reference value; use it only after you have computed your own.

Write one self-contained file `v6/bench/shadow/shadow_d_b1.py` (numpy and scipy only, run with `~/v5env/bin/python`) and run it over
every plan. Write `v6/bench/shadow/shadow_results.json`: per world and plan, your D, the reference D and whether they agree.
Agreement: within 1 % relative, or within 0.05 absolute where the reference D is below 5. D is a minimum over nuisances: where your D is
lower than the reference by more than the tolerance, say so explicitly (the reference may be under-minimised); where it is higher, your
minimiser may be stuck: search harder before reporting.

Use multiprocessing (at most 16 workers, OPENBLAS_NUM_THREADS=1). Report: the number of plans, the number agreeing, every disagreement
with both values and the world, and anything in the spec you found ambiguous and how you resolved it.
