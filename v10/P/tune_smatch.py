"""V10-X6 (e): tuning S-match's TOL and MARGIN on the tuning split only, then freezing them in scripts10.py (by hand, recorded in
FREEZE.md). Offline: the inputs are S-match-tune runs of scripts10.py (one per tuning world and sample, the data captured with the
window and the candidates' Bragg positions), each with the true phase of every sample from the grader's truth.
Rule, fixed before any tuning run:
  grid      TOL in (0.03, 0.04, 0.06, 0.08, 0.10) deg, MARGIN in (1, 2, 3, 4, 6, 8) noise units
  per pair  correct = identified phase equals the truth; wrong = identified phase is another candidate; none = gap below MARGIN
  choose    among pairs whose wrong share is at most 0.05 of all samples, the highest correct share; ties go to the larger MARGIN,
            then the smaller TOL. When no pair keeps wrong at or under 0.05, the pair with the fewest wrong (ties as above) is
            chosen and the result says so.
  python tune_smatch.py RUNS.jsonl OUT.json
RUNS lines: {"world": ..., "truth": {"None" | "pre" | "post": phase}, "result": <scripts10 S-match-tune output>}"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'pilot'))     # recipes10 (the runner copies it beside scripts10)
import scripts10 as S

TOLS = (0.03, 0.04, 0.06, 0.08, 0.10)
MARGINS = (1.0, 2.0, 3.0, 4.0, 6.0, 8.0)
WRONG_MAX = 0.05


def samples(runs):
    out = []
    for r in runs:
        res = r['result']; lo, hi = res['plan']['window']; pos = {k: np.asarray(v) for k, v in res['plan']['positions'].items()}
        for sm, d in res['plan']['data'].items():
            y = np.asarray(d['y'], float); x = np.round(lo + S.STEP * np.arange(len(y)), 4)
            out.append(dict(world=r['world'], sample=sm, truth=r['truth'][sm], pos=pos, lo=lo, hi=hi, x=x, y=y))
    return out


def evaluate(ss, tol, margin):
    c = w = n = 0
    for s in ss:
        ph = S.smatch_identify(s['pos'], s['lo'], s['hi'], s['x'], s['y'], tol=tol, margin=margin)['phase']
        if ph is None: n += 1
        elif ph == s['truth']: c += 1
        else: w += 1
    N = len(ss)
    return dict(tol=tol, margin=margin, n=N, correct=c, wrong=w, none=n, correct_share=round(c / N, 4), wrong_share=round(w / N, 4))


def choose(table):
    key = lambda e: (e['margin'], -e['tol'])
    ok = [e for e in table if e['wrong_share'] <= WRONG_MAX]
    if ok: return max(ok, key=lambda e: (e['correct_share'],) + key(e)), True
    return max(table, key=lambda e: (-e['wrong'],) + key(e)), False


def main():
    runs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
    ss = samples(runs)
    table = [evaluate(ss, t, m) for t in TOLS for m in MARGINS]
    best, met = choose(table)
    out = dict(n_worlds=len(runs), n_samples=len(ss), rule=dict(tols=TOLS, margins=MARGINS, wrong_max=WRONG_MAX),
               chosen=dict(TOL=best['tol'], MARGIN=best['margin']), wrong_cap_met=met, chosen_row=best, table=table)
    json.dump(out, open(sys.argv[2], 'w'), indent=1)
    print(json.dumps(dict(chosen=out['chosen'], wrong_cap_met=met, row=best)))


if __name__ == '__main__':
    main()
