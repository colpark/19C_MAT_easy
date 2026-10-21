"""Stage 3 scripted-agent validation report (V5_SPEC F.6, F.7), from graded logs (mcenv.grade3).
  python -m mcenv.validation3 GRADED.jsonl OUT.md OUT.json
Checks the predictions written in F.6: the trusting oracle fails every fault world; the consistency agent catches F1, F3, F4 and F6 and
misses F2 on m0 and F5; repeat-everything runs out of budget on quiet worlds; the ceiling oracle answers every world correctly."""
import json, sys
from collections import defaultdict
from . import stage3 as F

PLAN_LEN = None


def main():
    G = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    by = defaultdict(list)
    for g in G: by[g['model'].split(':')[1]].append(g)
    res = {}; L = ['# Stage 3 scripted agents (V5_SPEC F.6, F.7)\n', f'{len(G)} episodes: six agents x 56 worlds (28 clean, 28 fault) x k = 1 to 5, played through the stage 3 server code path and graded from logs (valid-only keys).\n']
    L.append('| agent | correct, clean | correct, fault | fault fired | fault-induced wrong (strict) | detected / fired | mean cost clean | mean cost fault |')
    L.append('|---|---|---|---|---|---|---|---|')
    for a in ('ceiling', 'trusting', 'repeat', 'consistency', 'prior', 'abstain'):
        e = by.get(a, []); c = [g for g in e if not g['fault_world']]; f = [g for g in e if g['fault_world']]; fi = [g for g in f if g.get('fault')]
        det = defaultdict(list)
        for g in fi: det[g['fault']['type'] + ('-m0' if g['scen'] in F.M0_FAULT else '')].append(g['detected'])
        per = defaultdict(list)
        for g in f: per[g['scen']].append(g['correct'])
        res[a] = dict(correct_clean=[sum(g['correct'] for g in c), len(c)], correct_fault=[sum(g['correct'] for g in f), len(f)], fired=[len(fi), len(f)],
                      fault_induced_wrong=sum(g['fault_induced_wrong'] for g in f), detection={k: [sum(v), len(v)] for k, v in sorted(det.items())},
                      per_scenario_fault_correct={str(s): [sum(v), len(v)] for s, v in sorted(per.items())},
                      cost_clean=round(sum(g['cost'] for g in c) / max(1, len(c)), 1), cost_fault=round(sum(g['cost'] for g in f) / max(1, len(f)), 1))
        r = res[a]
        L.append(f"| {a} | {r['correct_clean'][0]}/{r['correct_clean'][1]} | {r['correct_fault'][0]}/{r['correct_fault'][1]} | {len(fi)}/{len(f)} | "
                 f"{r['fault_induced_wrong']} | {sum(sum(v) for v in det.values())}/{len(fi)} | {r['cost_clean']} | {r['cost_fault']} |")
    L.append('\n## Detection by fault type (detected / fired)\n')
    types = sorted({t for r in res.values() for t in r['detection']})
    L.append('| agent | ' + ' | '.join(types) + ' |'); L.append('|---|' + '---|' * len(types))
    for a, r in res.items(): L.append(f'| {a} | ' + ' | '.join('/'.join(map(str, r['detection'].get(t, [0, 0]))) for t in types) + ' |')
    L.append('\n## Fault-world correctness per scenario\n')
    sc = sorted({s for r in res.values() for s in r['per_scenario_fault_correct']}, key=int)
    L.append('| agent | ' + ' | '.join(sc) + ' |'); L.append('|---|' + '---|' * len(sc))
    for a, r in res.items(): L.append(f'| {a} | ' + ' | '.join('/'.join(map(str, r['per_scenario_fault_correct'].get(s, [0, 0]))) for s in sc) + ' |')
    # predictions
    tr = res['trusting']; co = res['consistency']; ce = res['ceiling']; rp = by['repeat']
    rp_quiet = [g for g in rp if g['scen'] in F.QUIET]
    exhausted = [g for g in rp_quiet if g['cost'] > 180 - 25]          # spent within one typical measurement of the budget
    pred = dict(
        trusting_fails_every_fault_world=tr['correct_fault'][0] == 0,
        consistency_catches={t: co['detection'].get(t) for t in ('F1', 'F3', 'F4', 'F6')},
        consistency_misses={t: co['detection'].get(t) for t in ('F2-m0', 'F5')},
        repeat_runs_out_on_quiet=[len(exhausted), len(rp_quiet)],
        ceiling_all_correct=ce['correct_clean'][0] == ce['correct_clean'][1] and ce['correct_fault'][0] == ce['correct_fault'][1])
    res['predictions'] = pred
    L.append('\n## Predictions (F.6)\n')
    L.append(f"- Trusting oracle fails every fault world: {'met' if pred['trusting_fails_every_fault_world'] else 'NOT met'} ({tr['correct_fault'][0]} of {tr['correct_fault'][1]} fault-world episodes correct).")
    L.append(f"- Consistency agent catches F1, F3, F4, F6: {pred['consistency_catches']}; misses F2 on m0 and F5: {pred['consistency_misses']} (F5 never fires under the oracle plan, which uses no standard; X38).")
    L.append(f"- Repeat-everything runs out of budget on quiet worlds: {len(exhausted)} of {len(rp_quiet)} quiet-world episodes end within 25 min of the 180-min budget.")
    L.append(f"- Ceiling oracle answers every world correctly: {'met' if pred['ceiling_all_correct'] else 'NOT met'} (clean {ce['correct_clean'][0]}/{ce['correct_clean'][1]}, fault {ce['correct_fault'][0]}/{ce['correct_fault'][1]}).")
    open(sys.argv[2], 'w').write('\n'.join(L) + '\n'); json.dump(res, open(sys.argv[3], 'w'), indent=1)
    print('\n'.join(L))


if __name__ == '__main__':
    main()
