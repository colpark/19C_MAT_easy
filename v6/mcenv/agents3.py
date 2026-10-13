"""Stage 3 scripted agents (V5_SPEC F.6), played through the stage 3 server code path on clean and fault worlds.
  ceiling     knows the fault: m0 faults are repeated with m0's settings; a fault due on a plan measurement is absorbed first by the
              cheapest triggering X-ray measurement (2 points inside the route window at 0.1 s) when plan plus sacrifice fit the budget;
              a neutron fault cannot be absorbed or repeated within the budget, so it answers CANNOT_TELL without spending; reads on valid data
  trusting    runs the oracle plan of the world and reads all data by likelihood ratio
  repeat      repeats m0, then takes every oracle-plan measurement twice as far as the budget allows; drops pairs that disagree (chi2 per
              point of their difference > 2), keeps unrepeated measurements, reads by likelihood ratio
  consistency runs the oracle plan; after each measurement fits the best side to it alone and to m0 alone and repeats it once when its
              chi2 per point exceeds 2, its fitted scale differs from m0's by more than a factor 1.25, or its effective zero (zero offset and
              displacement combined at the measurement's centre) differs from m0's by more than 0.02 deg (twice the manual's zero range);
              neutron measurements: chi2 per point and scale relative to the manual's neutron count statement; reads on kept measurements
  prior       SUPPORTED without measuring (stage 1 prior agent); abstain: CANNOT_TELL without measuring
  python -m mcenv.agents3 OUT_TOKENS.txt AGENTS KS [WORLDS: clean|fault|all]"""
import json, math, os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
import numpy as np
from . import server3 as SV            # installs stage 3 and the fault server
from . import server as S
from . import scenarios as SC
from . import separation as SP
from . import physics as P
from . import stage3 as F
from . import admin as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS = json.load(open(os.path.join(ROOT, 'stage1b', 'validation', 'oracle_plans.json')))
CHI_PP, SCALE_F, ZERO_D = 2.0, 1.25, 0.02


def call(tok, tool, **a): return S.call(tok, tool, a)[0]


def plan_of(world):
    p = PLANS.get(str(SC.SCEN[SC.WORLD_SCEN[world]]['worlds'][world]['mirror_1b']))
    return None if p is None else [SP.meas_from(d) for d in p]


def measure(tok, m):
    if m.radiation == 'neutron': return call(tok, 'measure', radiation='neutron')['id']
    return call(tok, 'measure', start=m.start, stop=round(m.start + m.step * (m.n - 1), 6), step=m.step, time_per_step=m.t, optics=m.optics,
                si_standard=m.si_standard)['id']


def left(tok): ep = S.get_episode(tok); return S.BUDGET - ep.state['spent']


def cost(m, tok):
    ep = S.get_episode(tok); return m.cost + (S.STD_PREP if m.si_standard and not ep.state['std_prepared'] else 0.0)


def meas_ys(tok, ids):
    ep = S.get_episode(tok); return [ep.meas(i) for i in ids], [ep.counts(i) for i in ids]


def answer_lr(tok, scen, ids, note=''):
    if not ids:
        call(tok, 'answer', verdict='CANNOT_TELL', region='', rationale='no valid data ' + note); return
    ms, ys = meas_ys(tok, ids); r = SP.lr_read(scen, ms, ys, 100.0)
    m = [x for x in ms if x.radiation == 'neutron'] or [x for x in ms if not (x.start == 10.0 and x.n == 1501)] or ms; m = m[-1]
    call(tok, 'answer', verdict='SUPPORTED' if r['dchi2'] > 0 else 'REFUTED', region=f'{m.start:.2f}-{m.start + m.step * (m.n - 1):.2f}',
         rationale=f'likelihood ratio dchi2 = {r["dchi2"]:.1f} {note}')


def cannot(tok, why): call(tok, 'answer', verdict='CANNOT_TELL', region='', rationale=why)


# ---------------------------------------------------------------- agents
def ceiling(tok, world):
    scen = SC.WORLD_SCEN[world]; plan = plan_of(world); ids = ['m0']
    if plan is None: cannot(tok, 'no affordable plan separates the claim from its alternative'); return
    if F.is_fault(world):
        sc = F.SCHEDULE[scen]
        if sc['trigger'] == 'm0':
            ids = [measure(tok, SP.DEFAULT)]                              # repeat m0 (valid: a fault never repeats); drop the failed m0
        else:
            due = [m for m in plan if F.triggers(scen, m)]
            if due:
                if sc['trigger'][0] == 'neutron':
                    cannot(tok, 'the neutron measurement this claim needs will fail and cannot be repeated within the budget'); return
                lo = sc['trigger'][1] + 0.5
                sac = SP.Meas('xray', round(lo, 4), 0.01, 2, 0.1, 'standard', False)
                if sum(cost(m, tok) for m in plan) + sac.cost <= left(tok) + 1e-9:
                    measure(tok, sac)                                       # absorbs the fault; not used in the reading
                else:
                    cannot(tok, 'plan plus sacrifice exceed the budget'); return
    for m in plan: ids.append(measure(tok, m))
    answer_lr(tok, scen, ids)


def trusting(tok, world):
    scen = SC.WORLD_SCEN[world]; plan = plan_of(world)
    if plan is None: cannot(tok, 'no affordable plan separates the claim from its alternative'); return
    ids = ['m0'] + [measure(tok, m) for m in plan]
    answer_lr(tok, scen, ids)


def _disagree(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    return float(((a - b) ** 2 / np.maximum(a + b, 1.0)).mean()) > CHI_PP


def repeat(tok, world):
    scen = SC.WORLD_SCEN[world]; plan = plan_of(world) or []; ep = S.get_episode(tok)
    pairs = [('m0', measure(tok, SP.DEFAULT) if SP.DEFAULT.cost <= left(tok) else None)]
    for m in plan:
        if cost(m, tok) > left(tok) + 1e-9: break
        a = measure(tok, m)
        b = measure(tok, m) if cost(m, tok) <= left(tok) + 1e-9 else None
        pairs.append((a, b))
    keep = []
    for a, b in pairs:
        if b is None: keep.append(a)
        elif not _disagree(ep.counts(a), ep.counts(b)): keep += [a, b]
    if plan_of(world) is None: cannot(tok, 'no affordable plan'); return
    answer_lr(tok, scen, keep)


def _best_fit(scen, m, y):
    """best side fitted to one measurement: (chi2 per point, scale relative to nominal, effective zero at the centre)."""
    yv = np.asarray(y, float); best = None
    for side in ('claim_side', 'other_side'):
        for br in SC.SCEN[scen][side]:
            w = 1.0 / np.maximum(yv, 1.0)
            c, th = SP.fit_branch([m], yv, w, br, 100.0, L_bounds=(5.0, 3000.0), n_sobol=64, n_refine=4)
            mu = SP._model([m], br, th); w = 1.0 / np.maximum(mu, 1.0)
            c, th = SP.fit_branch([m], yv, w, br, 100.0, starts=[np.array([th['disp_mm'], th['zero_deg'], math.log(th['L_nm'])] + th['u'])],
                                  L_bounds=(5.0, 3000.0), n_sobol=0, n_refine=1)
            if best is None or c < best[0]: best = (c, br, th)
    c, br, th = best
    tr = SP.world_truth(SC.twins(scen)[0]); ng = th['ng']; amp = float(sum(th['coef'][:ng - 3]))
    nom = tr['An'] if m.radiation == 'neutron' else tr['A']
    tc = m.start + m.step * (m.n - 1) / 2
    zeff = None if m.radiation == 'neutron' else float(P.peak_shift(np.array([tc]), th['disp_mm'], th['zero_deg'])[0])
    return c / len(yv), amp / nom, zeff, (th['disp_mm'], th['zero_deg'])


def _flag(scen, m, y, ref):
    cpp, sc, z, _ = _best_fit(scen, m, y)
    if cpp > CHI_PP: return True
    if m.radiation == 'neutron': return not (1 / SCALE_F <= sc <= SCALE_F)
    if ref is None: return False
    rs = ref[1]
    if rs > 0 and not (1 / SCALE_F <= sc / rs <= SCALE_F): return True
    tc = m.start + m.step * (m.n - 1) / 2
    zref = float(P.peak_shift(np.array([tc]), ref[3][0], ref[3][1])[0])
    return abs(z - zref) > ZERO_D


def consistency(tok, world):
    scen = SC.WORLD_SCEN[world]; plan = plan_of(world); ep = S.get_episode(tok)
    ref = _best_fit(scen, SP.DEFAULT, ep.counts('m0')); keep = ['m0']
    if ref[0] > CHI_PP and SP.DEFAULT.cost <= left(tok):
        keep = [measure(tok, SP.DEFAULT)]; ref = _best_fit(scen, SP.DEFAULT, ep.counts(keep[0]))
    if plan is None: cannot(tok, 'no affordable plan separates the claim from its alternative'); return
    for m in plan:
        if cost(m, tok) > left(tok) + 1e-9: break
        a = measure(tok, m)
        if _flag(scen, m, ep.counts(a), ref):
            if cost(m, tok) <= left(tok) + 1e-9: keep.append(measure(tok, m))      # the repeat is valid (a fault never repeats)
        else: keep.append(a)
    answer_lr(tok, scen, keep)


def prior(tok, world): call(tok, 'answer', verdict='SUPPORTED', region='', rationale='prior')
def abstain(tok, world): cannot(tok, 'always abstain')


AGENTS = dict(ceiling=ceiling, trusting=trusting, repeat=repeat, consistency=consistency, prior=prior, abstain=abstain)


def _play(args):
    tok, agent, world = args
    try: AGENTS[agent](tok, world); return tok, None
    except Exception:
        import traceback; return tok, traceback.format_exc()[-1500:]


def main():
    out, names, ks = sys.argv[1], sys.argv[2].split(','), [int(k) for k in sys.argv[3].split(',')]
    which = sys.argv[4] if len(sys.argv) > 4 else 'all'
    W = {'clean': F.clean_worlds(), 'fault': F.fault_worlds(), 'all': F.clean_worlds() + F.fault_worlds()}[which]
    batch = os.environ.get('V5_BATCH', 'v5-15-validation')
    items = [dict(world=w, arm='active', k=k, model='scripted:' + a, batch=batch) for a in names for w in W for k in ks]
    toks = A._register(items)
    from multiprocessing import Pool
    with Pool(int(os.environ.get('V5_PROCS', '16'))) as pool, open(out, 'a') as f:
        for tok, err in pool.imap_unordered(_play, [(t, it['model'].split(':')[1], it['world']) for it, t in zip(items, toks)]):
            f.write(tok + '\n'); f.flush()
            if err: print('ERROR', tok[:8], err, flush=True)


if __name__ == '__main__':
    main()
