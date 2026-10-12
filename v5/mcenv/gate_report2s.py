"""Stage 2s gate report (V5_SPEC E.5, E.6; X43): pair resolution and decisive pair resolution (both worlds D >= 25, truth verdicts) per
scripted agent and scenario, the predictions of E.5 and the gate (FM-first beats placebo-first on 47 and 48 with the ceiling precondition
met; 46, 49, 50 reported).
  python -m mcenv.gate_report2s GATE_GRADED.jsonl PRE_GRADED.jsonl OUT.md OUT.json"""
import json, sys
from collections import defaultdict

SCENS = (46, 47, 48, 49, 50)
GATED = (47, 48)


def pairs(G):
    by = defaultdict(list)
    for g in G: by[(g['model'], g['scen'], g['k'])].append(g)
    res = defaultdict(lambda: defaultdict(list))
    for (m, s, k), v in by.items():
        ok = len(v) == 2 and all(g['correct'] and g['verdict'] == g['truth'] for g in v)
        dec = ok and all(g['D'] >= 25 for g in v)
        res[m][s].append((ok, dec))
    return res


def main():
    G = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]; PRE = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
    R = pairs(G); P = pairs(PRE); out = {}
    L = ['# Stage 2s gate (V5_SPEC E.5, E.6; X43)\n', 'Scripted agents played through the stage 2s server code path (node A2; FM service MACE-MP-0 at 8771), k = 1 to 5; graded from logs. '
         'Cells: pairs resolved (both worlds get their key\'s truth verdict) / decisive pairs (both worlds D >= 25).\n',
         '| agent | ' + ' | '.join(str(s) for s in SCENS) + ' |', '|---|' + '---|' * len(SCENS)]
    rows = [('ceiling (precondition, FM disabled)', P.get('scripted:first-ceiling', {}))] + [(m.split(':')[1], R[m]) for m in sorted(R)]
    for name, r in rows:
        L.append(f'| {name} | ' + ' | '.join(f"{sum(o for o, _ in r.get(s, []))}/{len(r.get(s, []))} ({sum(d for _, d in r.get(s, []))})" for s in SCENS) + ' |')
        out[name] = {s: dict(resolved=sum(o for o, _ in r.get(s, [])), decisive=sum(d for _, d in r.get(s, [])), n=len(r.get(s, []))) for s in SCENS}
    ce = out['ceiling (precondition, FM disabled)']; fm = out.get('first-fm', {}); pl = out.get('first-placebo', {})
    pre_ok = all(ce[s]['resolved'] == ce[s]['n'] == 5 for s in SCENS)
    beats = {s: fm.get(s, {}).get('resolved', 0) > pl.get(s, {}).get('resolved', 0) for s in SCENS}
    gate = pre_ok and all(beats[s] for s in GATED)
    pred = dict(fm_first_all=all(fm.get(s, {}).get('resolved') == 5 for s in SCENS), ceiling_all=pre_ok,
                survey_first_none_quiet=all(out.get('survey-placebo', {}).get(s, {}).get('resolved', 0) == 0 for s in (47, 48, 49, 50)),
                placebo_first_none_quiet=all(pl.get(s, {}).get('resolved', 0) == 0 for s in (47, 48, 49, 50)),
                prior_none=all(out.get('prior-fm', {}).get(s, {}).get('resolved', 0) == 0 for s in SCENS),
                abstain_none=all(out.get('abstain-placebo', {}).get(s, {}).get('resolved', 0) == 0 for s in SCENS))
    pr = [g for g in G if g['model'] == 'scripted:prior-fm']; ab = [g for g in G if g['model'] == 'scripted:abstain-placebo']
    pred['prior_truth_match'] = f"{sum(g['verdict'] == g['truth'] for g in pr)}/{len(pr)}"
    pred['abstain_wrong'] = sum(g['wrong_conclusion'] for g in ab)
    L.append('\n## Gate\n')
    L.append(f"- Ceiling precondition (5 of 5 on every scenario): {'met' if pre_ok else 'NOT met'}.")
    L.append('- FM-first beats placebo-first: ' + ', '.join(f"{s}: {'yes' if beats[s] else 'no'}" for s in SCENS) + ' (gated: 47, 48; X43).')
    L.append(f"- **Gate: {'PASS' if gate else 'FAIL'}.**")
    L.append('\n## Predictions (E.5)\n')
    for k, v in pred.items(): L.append(f'- {k}: {v}')
    open(sys.argv[3], 'w').write('\n'.join(L) + '\n')
    json.dump(dict(cells=out, gate=gate, beats={str(k): v for k, v in beats.items()}, precondition=pre_ok, predictions=pred), open(sys.argv[4], 'w'), indent=1)
    print('\n'.join(L))


if __name__ == '__main__':
    main()
