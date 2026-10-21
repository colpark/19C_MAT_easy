"""V10-1 pilot report: v10/PILOT.md and pilot/pilot_summary.json from the pilot stage outputs (pilot/run/s0..s4/out) and run/state.json.
Per family: qualification rate and why units fail, N_plan / N_rec, kappa and the ratio spread, decisive-plan kinds, each recipe's D at
the final N, control fall-to shares, and the projected bench and control supply against 1.25 x the Gate V10-supply minima.
Projection (fixed before the pilot numbers were read):
  candidates  R: R frame minus tuning (paired-v7 kept, flagged); H: H frame minus tuning, less the R and T bench takes that fall in it
              (at most the R and T targets, counted as the expected overlap: share of H candidates in the R frame x (24 + 16), capped
              by that count); T: R candidates x the R qualification rate
  bench       candidates x the tuning-unit qualification rate (H type M: the M candidates x the pooled H rate, and x the M rate when
              there are 3 or more M tuning units)
  controls    candidates x the share of tuning units that fail qualification and pass v7's bars (T: T tuning units failing T
              qualification whose R unit passes v7's bars)
  python pilot_report.py"""
import json, os, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..'); RUN = os.path.join(HERE, 'run')
sys.path.insert(0, HERE)
import frames10 as FR
import recipes10 as RC

MIN = dict(R=16, H=12, H_M=5, T=12, control=6)
TARGET = dict(R=24, T=16)
D_RES = 50.0


def outs(stage):
    d = os.path.join(RUN, stage, 'out')
    return [json.load(open(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith('.json')] if os.path.isdir(d) else []


def q(xs, ps=(0.1, 0.5, 0.9)):
    xs = sorted(x for x in xs if x is not None)
    return [round(xs[int(p * (len(xs) - 1))], 3) for p in ps] if xs else None


def fam_rows(s2, fam):
    return [o for o in s2 if o['family'] == fam]


def recipe_table(rows, key):
    """per recipe: median and deciles over units of min-over-worlds D, the share of units resolved by it (D >= 50 on every world)."""
    out = {}
    for r in RC.NAMES:
        mins = [min(o[key][r].values()) for o in rows if o.get(key) and r in o[key]]
        if mins: out[r] = dict(deciles=q(mins), share_ge50=round(sum(m >= D_RES for m in mins) / len(mins), 3), n=len(mins))
    return out


def falls_to(rows, key):
    out = {}
    for r in RC.NAMES:
        hits = [min(o[key][r].values()) >= D_RES for o in rows if o.get(key) and r in o[key]]
        if hits: out[r] = dict(share=round(sum(hits) / len(hits), 3), n=len(hits))
    return out


def kinds(rows):
    k = {}
    for o in rows:
        if o.get('qualifies'): kk = o['plan_check']['kind']; k[kk] = k.get(kk, 0) + 1
    return k


def summarize():
    st = json.load(open(os.path.join(RUN, 'state.json')))
    s2, s3, s4 = outs('s2'), outs('s3'), outs('s4')
    R, H, F = FR.tuning_units()
    candR = [m for m in F['R'] if m['formula'] not in F['tuning']]
    candH = [m for m in F['H'] if m['formula'] not in F['tuning']]
    Rf = {m['formula'] for m in F['R']}
    bars = {o['unit']: o for o in s3 if o['mode'] == 'v7bars'}
    tq = [o for o in s3 if o['mode'] == 'round']
    S = dict(kappa=dict(kappa1=st.get('kappa1'), kappa1_info=st.get('kappa1_info'), kappa2=st.get('kappa2'), kappa2_info=st.get('kappa2_info'),
                        kappa_final=st.get('kappa_final'), final_ratio_info=st.get('final_ratio_info'), final_median_ratio=st.get('final_median_ratio')),
             families={})
    for fam in ('R', 'H', 'T'):
        rows = tq if fam == 'T' else fam_rows(s2, fam)
        n = len(rows); nq = sum(bool(o.get('qualifies')) for o in rows)
        why = {}
        for o in rows:
            if not o.get('qualifies'):
                w = o.get('why_not') or ('N_rec none' if o.get('N_rec') is None else 'N_plan none' if o.get('N_plan') is None else 'no final')
                why[w] = why.get(w, 0) + 1
        ratio = [o['N_plan'] / o['N_rec'] for o in rows if o.get('N_plan') and o.get('N_rec')]
        if fam == 'T':
            ctrl = [o for o in rows if not o.get('qualifies') and bars.get('R|' + o['formula'], {}).get('v7', {}).get('passes')]
            ctrl_rows = [o for o in s4]
        else:
            ctrl = [o for o in rows if not o.get('qualifies') and bars.get(o['unit'], {}).get('v7', {}).get('passes')]
            ctrl_rows = [dict(recipe_D=bars[o['unit']]['v7'].get('recipe_D')) for o in ctrl]
        f = dict(n_tuning=n, n_qualify=nq, rate=round(nq / n, 3) if n else None, why_not=why, N_plan_over_N_rec=q(ratio),
                 N_final=q([o['plan_check']['N_final'] for o in rows if o.get('qualifies')]), plan_kinds=kinds(rows),
                 recipe_D_at_final=recipe_table([o for o in rows if o.get('qualifies')], 'recipe_D_at_final'),
                 n_control_tuning=len(ctrl), control_rate=round(len(ctrl) / n, 3) if n else None, control_falls_to=falls_to(ctrl_rows, 'recipe_D'))
        if fam == 'H':
            for t in 'EM':
                rt = [o for o, u in ((o, next(x for x in H if x['id'] == o['unit'])) for o in rows) if u['htype'] == t]
                f[f'type_{t}'] = dict(n=len(rt), n_qualify=sum(bool(o.get('qualifies')) for o in rt))
        S['families'][fam] = f
    # projection
    rR = S['families']['R']['rate'] or 0.0; rH = S['families']['H']['rate'] or 0.0; rT = S['families']['T']['rate'] or 0.0
    nR = len(candR)
    share_in_R = sum(m['formula'] in Rf for m in candH) / max(1, len(candH))
    overlap = min(sum(m['formula'] in Rf for m in candH), round(share_in_R * (TARGET['R'] + TARGET['T'])))
    nH = len(candH) - overlap
    nM = sum(m['htype'] == 'M' for m in candH)
    HM = S['families']['H']['type_M']
    rM = HM['n_qualify'] / HM['n'] if HM['n'] >= 3 else None
    nT = nR * rR
    P = dict(candidates=dict(R=nR, H=nH, H_M=nM, T=round(nT, 1), H_overlap_removed=overlap),
             bench=dict(R=round(nR * rR, 1), H=round(nH * rH, 1), H_M_pooled_rate=round(nM * rH, 1),
                        H_M_own_rate=None if rM is None else round(nM * rM, 1), T=round(nT * rT, 1)),
             controls={fam: round(c * (S['families'][fam]['control_rate'] or 0.0), 1) for fam, c in (('R', nR), ('H', nH), ('T', nT))})
    need = {k: 1.25 * v for k, v in MIN.items()}
    checks = dict(R=P['bench']['R'] >= need['R'], H=P['bench']['H'] >= need['H'],
                  H_M=(P['bench']['H_M_own_rate'] if P['bench']['H_M_own_rate'] is not None else P['bench']['H_M_pooled_rate']) >= need['H_M'],
                  T=P['bench']['T'] >= need['T'], **{f'control_{fam}': P['controls'][fam] >= need['control'] for fam in ('R', 'H', 'T')})
    P.update(need_1_25x=need, checks=checks, all_pass=all(checks.values()))
    S['projection'] = P
    return S


def md(S):
    L = ['# V10-1 pilot (truth-only, tuning split)', '',
         'Built by `pilot/pilot_report.py` from `pilot/run/` (stage outputs) and `pilot/run/state.json`. No FM call, no LLM. Numbers are also '
         'in `pilot/pilot_summary.json`.', '', '## κ', '']
    k = S['kappa']
    for nm, inf in (('κ1 (s0, N0 before κ)', k['kappa1_info']), ('κ2 (s1, at κ1)', k['kappa2_info'])):
        if inf: L.append(f"- {nm}: median D(neutron, κ=1)/D(R1) {inf['median_ratio_k1']:.3f} over {inf['n_worlds']} worlds, deciles "
                         f"{', '.join(f'{x:.2f}' for x in inf['deciles'])}; continuous κ {inf['kappa_continuous']:.4f}")
    L.append(f"- κ1 = {k['kappa1']}, κ2 = {k['kappa2']}; **final κ = {k['kappa_final']}**.")
    fi = k.get('final_ratio_info')
    if fi:
        L.append(f"- Final median ratio D(neutron)/D(R1) at κ_final and the final N: **{k['final_median_ratio']:.3f}** (tolerance 0.5 to 2), "
                 f"deciles at κ = 1 {', '.join(f'{x:.2f}' for x in fi['deciles'])} (× κ_final: "
                 f"{', '.join(f'{x * k['kappa_final']:.2f}' for x in fi['deciles'])}), {fi['n_worlds']} worlds.")
    for fam, f in S['families'].items():
        L += ['', f'## {fam}', '',
              f"- Tuning units {f['n_tuning']}, qualify {f['n_qualify']} (rate {f['rate']}). Not qualifying: "
              + (', '.join(f'{w} {n}' for w, n in sorted(f['why_not'].items(), key=lambda x: -x[1])) or 'none') + '.',
              f"- N_plan / N_rec deciles (10, 50, 90 %): {f['N_plan_over_N_rec']}. Final N of qualifiers: {f['N_final']}.",
              f"- Decisive-plan kinds (qualifiers): {f['plan_kinds']}."]
        if fam == 'H': L.append(f"- Types: E {f['type_E']}, M {f['type_M']}.")
        L += ['', '| Recipe | min-over-worlds D at final N (10, 50, 90 %) | share with D ≥ 50 on every world | n |', '|---|---|---|---|']
        L += [f"| {r} | {v['deciles']} | {v['share_ge50']} | {v['n']} |" for r, v in f['recipe_D_at_final'].items()]
        L += ['', f"- Pilot controls (fail qualification, pass v7's bars): {f['n_control_tuning']} (rate {f['control_rate']}). "
                  'Share each recipe falls to (D ≥ 50 on every world): '
                  + (', '.join(f"{r} {v['share']} (n {v['n']})" for r, v in f['control_falls_to'].items()) or 'none') + '.']
    P = S['projection']
    L += ['', '## Projected supply', '', f"- Candidates: {P['candidates']}.", f"- Bench units: {P['bench']}.", f"- Bench controls: {P['controls']}.",
          f"- Needed (1.25 × Gate V10-supply minima): {P['need_1_25x']}.", f"- Checks: {P['checks']}. **{'All pass' if P['all_pass'] else 'Not all pass'}.**"]
    if 'R5' in S['families']['R']['recipe_D_at_final']:
        L += ['', f"- R5 (the neutron, then R1) on qualifying units: share with D ≥ 50 on every world = "
                  + ', '.join(f"{fam} {S['families'][fam]['recipe_D_at_final'].get('R5', {}).get('share_ge50')}" for fam in S['families'])
                  + '. On bench units the neutron alone never decides; it helps only inside a two-measurement plan.']
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    S = summarize()
    json.dump(S, open(os.path.join(HERE, 'pilot_summary.json'), 'w'), indent=1)
    open(os.path.join(V10, 'PILOT.md'), 'w').write(md(S))
    print(md(S))
