"""vP.1 reference: cross-fitted choice of one LLM-written program per family (PREREG_vP1.md, VP1-1).

Inputs are unit-level results (a unit is a B1 or H pair, or a T quad) for every program, compound and seed:
  ev[(prog, compound, seed)]   1 if the unit resolves under the evidence key, else 0
  reg[(prog, compound, seed)]  the same under the registered key
  cost[(prog, compound, seed)] mean measurement minutes over the unit's worlds
Rule, fixed before any score exists:
  For fold f, choose the program with the highest mean ev over the OTHER fold's compounds and the selection seeds.
  Ties: higher mean reg on the other fold, then lower mean cost, then the program name in sort order.
  Score the fold-f choice on fold f's compounds at the evaluation seeds. Pool both folds.
The function never reads a score from the fold it scores."""
from statistics import mean


def _mean(d, keys):
    v = [d[k] for k in keys if k in d]
    return mean(v) if v else float('-inf')


def choose(progs, ev, reg, cost, compounds, seeds):
    keys = lambda p: [(p, c, s) for c in compounds for s in seeds]
    def score(p):
        return (_mean(ev, keys(p)), _mean(reg, keys(p)), -_mean(cost, keys(p)) if any(k in cost for k in keys(p)) else 0.0)
    best = sorted(progs, key=lambda p: (tuple(-x for x in score(p)), p))
    return best[0]


def crossfit(progs, ev, reg, cost, fold_of, sel_seeds, eval_seeds):
    """returns dict(chosen={0: prog, 1: prog}, rows=[dict(compound, seed, fold, prog, ev, reg)])."""
    comps = {0: sorted(c for c, f in fold_of.items() if f == 0), 1: sorted(c for c, f in fold_of.items() if f == 1)}
    chosen, rows = {}, []
    for f in (0, 1):
        other = comps[1 - f]
        p = choose(progs, ev, reg, cost, other, sel_seeds)
        chosen[f] = p
        for c in comps[f]:
            for s in eval_seeds:
                k = (p, c, s)
                if k in ev:
                    rows.append(dict(compound=c, seed=s, fold=f, prog=p, ev=ev[k], reg=reg.get(k)))
    return dict(chosen=chosen, rows=rows)
