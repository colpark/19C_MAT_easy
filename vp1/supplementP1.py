"""vP.1 supplementary lines (written after the VP1-4a freeze, after the main analysis ran; descriptive and sensitivity only, never used
to decide an expectation). Uses analyzeP1's loading and analyzeF's units, rates and contrasts unchanged.
  1. Programs under fit-once against the same programs unmanipulated (seed 1, same worlds): unit resolution, both keys, per family.
  2. Sensitivity, VP1-X7: the episodes whose runner record is void for a bare run_python call dropped.
  3. Sensitivity, VP1-X10: the episodes with probable client retries (ops/client_retries.py output) dropped, for the cross-fitted and
     manipulation contrasts.
  4. Qwen online and offline: answered share and the verdict mix, to show where Qwen's zeros come from.
  python vp1/supplementP1.py RETRIES.json OUT.json"""
import json, os, sys
from collections import Counter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyzeP1 as P  # noqa: E402
AF = P.AF


def main():
    retries, outp = json.load(open(sys.argv[1])), sys.argv[2]
    R, raw, tabs, bad = P.load(); ST = AF.strata_of(); out = {}
    # 1. programs under fit-once against themselves unmanipulated
    s1 = {}
    for fam in ('B1', 'H'):
        U = {k: AF.units(R[fam], fam, k) for k in ('ev', 'reg')}; f = {}
        for a in sorted(x for x in U['ev'] if x.endswith('@fit-once')):
            base = a.split('@')[0]
            f[base] = {k: dict(fit_once=AF.rate(U[k][a], {1}), unmanipulated_seed1=AF.rate({c: v for c, v in U[k][base].items() if c[1] == 1}, {1}),
                               contrast=AF.contrast(U[k][a], [U[k][base]], ST[fam], {1})) for k in ('ev', 'reg')}
        s1[fam] = f
    out['programs_fit_once_vs_unmanipulated'] = s1
    # 2. and 3. sensitivity lines
    void_runner = set()
    for d in ('vp1-3', 'vp1-2h'):
        p = os.path.join(HERE, 'runs', d, 'episodes.jsonl')
        if os.path.exists(p):
            void_runner |= {json.loads(l)['token'][:12] for l in open(p) if json.loads(l).get('void')}
    def rerun(drop):
        R2 = {f: [r for r in R[f] if r['token'][:12] not in drop] for f in R}
        return dict(dropped=sum(len(R[f]) - len(R2[f]) for f in R), offline_vs_online={m: {f: {k: (v.get(k) or {}).get('cross-fitted minus online') for k in ('ev', 'reg')}
                                                                                               for f, v in d.items() if f in ('B1', 'H', 'T')}
                                                                                         for m, d in P.offline_online(R2, ST).items()},
                    manipulations={m: {f: {k: (v.get(k) or {}).get('contrast') for k in ('ev', 'reg')} for f, v in d.items() if f in ('B1', 'H')}
                                   for m, d in P.manipulations(R2, {t: x for t, x in raw.items() if t[:12] not in drop}, tabs, ST, {}).items()})
    out['sensitivity_VP1-X7_bare_run_python_dropped'] = dict(tokens=sorted(void_runner), **rerun(void_runner))
    out['sensitivity_VP1-X10_probable_retries_dropped'] = dict(n_episodes=len(retries), **rerun(set(retries)))
    # 4. Qwen
    q = {}
    for fam in ('B1', 'H', 'T'):
        for lab in ('qwen3-8b-fm',) + tuple(f'sllmGQ-{fam[0] if fam != "B1" else "R"}{i}' for i in range(1, 6)):
            L = [g for t, (f2, g) in raw.items() if f2 == fam and P.label(g) == lab]
            if L: q[f'{fam} {lab}'] = dict(episodes=len(L), answered=sum(bool(g.get('answered')) for g in L), verdicts=dict(Counter(str(g.get('verdict')) for g in L)),
                                           D25=sum(g['D'] >= 25 for g in L))
    out['qwen_detail'] = q
    json.dump(out, open(outp, 'w'), indent=1)
    print(json.dumps(out['programs_fit_once_vs_unmanipulated'])[:1500])


if __name__ == '__main__':
    main()
