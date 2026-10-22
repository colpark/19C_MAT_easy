"""Stage 2 gate report (V5_SPEC B.6): scripted planner with placebo, FM and ceiling relax, pair resolution per scenario over k.
  python -m mcenv.gate_report GATE_GRADED.jsonl ORACLE_PLANS2.json PLANS.json OUT.md"""
import json, sys
from collections import defaultdict

QUIET = (12, 13, 14, 15)
NAMES = {11: 'S2-A RbAsO3 polymorph (loud control)', 12: 'S2-B PbNbO3 tetragonality', 13: 'S2-C NiSeO3 + NiO2 trace',
         14: 'S2-D Ag(Rh,Ru) alloy', 15: 'S2-E Ru3Ni order'}


def main():
    G = [json.loads(l) for l in open(sys.argv[1])]; decid = {int(w): p is not None for w, p in json.load(open(sys.argv[2])).items()}
    plans = json.load(open(sys.argv[3])); out = sys.argv[4]
    res = defaultdict(dict); wrong = defaultdict(int); cost = defaultdict(list)
    by = defaultdict(list)
    for g in G: by[(g['arm'], g['scen'], g['k'])].append(g)
    for (a, s, k), eps in by.items():
        res[(a, s)][k] = all(e['correct'] and ((e['verdict'] == e['truth']) if decid[e['world']] else e['verdict'] == 'CANNOT_TELL') for e in eps)
        for e in eps: wrong[(a, s)] += e['wrong_conclusion']; cost[(a, s)].append(e['cost'])
    arms = ['placebo', 'fm', 'ceiling']
    L = ['# Stage 2 gate (V5_SPEC B.6): scripted planner, placebo vs FM vs ceiling', '',
         'Pairs resolved out of 5 (k = 1..5), wrong conclusions in brackets, mean instrument cost. The planner builds its hypotheses from '
         'prototypes, relaxes them with the arm\'s relax, plans the cheapest grid measurement decisive between its own hypotheses '
         '(lattice_scale free within ±1 %) and reads by likelihood ratio. A planner that finds no decisive plan answers CANNOT_TELL.', '',
         '| scenario | ' + ' | '.join(arms) + ' | FM beats placebo |', '|---|---|---|---|---|']
    gate_ok = True
    for s in sorted({g['scen'] for g in G}):
        cells = []; nres = {}
        for a in arms:
            r = res.get((a, s), {}); n = sum(r.values()); nres[a] = n
            c = cost.get((a, s), [0]); cells.append(f'{n}/{len(r)} ({wrong[(a, s)]}) {sum(c) / len(c):.0f} min')
        beats = nres['fm'] > nres['placebo']
        if s in QUIET and not beats: gate_ok = False
        L.append(f'| {NAMES.get(s, s)} | ' + ' | '.join(cells) + f" | {'yes' if beats else 'no'}{' (control, not gated)' if s not in QUIET else ''} |")
    L += ['', f"**Gate (FM beats placebo on every quiet scenario): {'PASS' if gate_ok else 'FAIL'}.**", '', '## Plans chosen by the planner', '']
    for k, v in sorted(plans.items()):
        L.append(f'- {k}: ' + ('no decisive plan (answers CANNOT_TELL)' if v is None else
                              f"{v['optics']} {v['start']:.2f}-{v['start'] + v['step'] * (v['n'] - 1):.2f} deg, step {v['step']}, {v['t']} s"))
    open(out, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
    return gate_ok


if __name__ == '__main__':
    main()
