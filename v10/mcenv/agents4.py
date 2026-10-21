"""Stage 4 scripted agents (V5_SPEC I.10), played through the stage 4 server code path. Identification: the world's oracle plan
(stage4/validation/oracle_plans.json; none in loud scenarios), then a likelihood-ratio reading between the two library polymorphs
(separation.lr_read, nuisances free). Property:
  ceiling   arm active-ceiling: DFT energies through the energy/hull tools (R: identified polymorph strictly lower than the other; H: hull <= 50)
  fm        arm active-fm: the same with the FM tables (the scripted FM planner of I.12, run for FM_CHECK)
  placebo   arm active-placebo: the same with the placebo (equal energies within a formula read as "not lowest")
  noprior   arm active-noprior: R, the denser polymorph (lower volume per atom) is the lowest; H, within 50 meV/atom only if its prototype is
            the most frequent prototype in MP for its anonymous formula (stage4/validation/noprior_prototypes.json)
  blindfm   arm blind-fm: no measurement; FM energies of both polymorphs; assumes the sample is the lower one and answers for it
  prior     arm active-noprior: SUPPORTED without measuring; abstain: CANNOT_TELL without measuring
  python -m mcenv.agents4 OUT_TOKENS.txt AGENTS KS"""
import json, os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
from . import server4 as SV            # installs stage 4 and the stage 4 arms
from . import server as S
from . import scenarios as SC
from . import separation as SP
from . import physics as P
from . import stage4 as F
from . import admin as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS = json.load(open(os.path.join(ROOT, 'stage4', 'validation', 'oracle_plans.json')))
NOPRIOR = os.path.join(ROOT, 'stage4', 'validation', 'noprior_prototypes.json')
ARM = dict(ceiling='active-ceiling', fm='active-fm', placebo='active-placebo', noprior='active-noprior', blindfm='blind-fm',
           prior='active-noprior', abstain='active-noprior')


def call(tok, tool, **a): return S.call(tok, tool, a)[0]


def identify(tok, world):
    """oracle plan of the world, then the likelihood-ratio reading: the library polymorph the data favour, its region and dchi2."""
    scen = SC.WORLD_SCEN[world]; d = SC.SCEN[scen]
    for m in [SP.meas_from(x) for x in PLANS.get(str(world), [])]:
        call(tok, 'measure', start=m.start, stop=round(m.start + m.step * (m.n - 1), 6), step=m.step, time_per_step=m.t, optics=m.optics,
             si_standard=m.si_standard)
    ep = S.get_episode(tok); ids = [r['id'] for r in ep.state['measurements']]
    ms = [ep.meas(i) for i in ids]; ys = [ep.counts(i) for i in ids]
    r = SP.lr_read(scen, ms, ys, 100.0)
    claim_poly = d['claim_side'][0].groups([])[0][0][0]; other_poly = d['other_side'][0].groups([])[0][0][0]
    m = ms[-1]
    return (claim_poly if r['dchi2'] > 0 else other_poly), f'{m.start:.2f}-{m.start + m.step * (m.n - 1):.2f}', r['dchi2']


def _other(scen, poly): return [p for p in SC.SCEN[scen]['polymorphs'] if p != poly][0]


def by_energy(tok, scen, poly):
    d = SC.SCEN[scen]
    if d['claim_type'] == 'R':
        e = {p: call(tok, 'energy', structure_name=p)['formation_energy_eV_per_atom'] for p in d['polymorphs']}
        return e[poly] < e[_other(scen, poly)], f'energies {e}'
    h = call(tok, 'hull', structure_name=poly)['energy_above_hull_eV_per_atom']
    return h <= 0.050, f'hull {h}'


def answer(tok, holds, region, note):
    call(tok, 'answer', verdict='SUPPORTED' if holds else 'REFUTED', region=region, rationale=note)


def _energy_agent(tok, world):
    scen = SC.WORLD_SCEN[world]; poly, region, dchi2 = identify(tok, world)
    holds, note = by_energy(tok, scen, poly)
    answer(tok, holds, region, f'identified {poly} (dchi2 {dchi2:.1f}); {note}')


ceiling = fm = placebo = _energy_agent


def _vpa(name):
    st = P.PHASES[name].structure({'lattice_scale': 1.0}); return st.volume / len(st)


def noprior(tok, world):
    scen = SC.WORLD_SCEN[world]; d = SC.SCEN[scen]; poly, region, dchi2 = identify(tok, world)
    if d['claim_type'] == 'R':
        holds = _vpa(poly) < _vpa(_other(scen, poly)); note = f'denser polymorph rule: {poly} {_vpa(poly):.3f} A3/atom'
    else:
        H = json.load(open(NOPRIOR)); holds = bool(H[poly]['is_most_frequent']); note = f'prototype rule: {H[poly]}'
    answer(tok, holds, region, f'identified {poly} (dchi2 {dchi2:.1f}); {note}')


def blindfm(tok, world):
    scen = SC.WORLD_SCEN[world]; d = SC.SCEN[scen]
    e = {p: call(tok, 'energy', structure_name=p)['formation_energy_eV_per_atom'] for p in d['polymorphs']}
    low = min(e, key=e.get)
    if d['claim_type'] == 'R': holds, note = True, f'assume the sample is the lowest polymorph {low}; energies {e}'
    else:
        h = call(tok, 'hull', structure_name=low)['energy_above_hull_eV_per_atom']; holds, note = h <= 0.050, f'assume {low}; hull {h}'
    answer(tok, holds, '', note)


def prior(tok, world): call(tok, 'answer', verdict='SUPPORTED', region='', rationale='prior')
def abstain(tok, world): call(tok, 'answer', verdict='CANNOT_TELL', region='', rationale='always abstain')


AGENTS = dict(ceiling=ceiling, fm=fm, placebo=placebo, noprior=noprior, blindfm=blindfm, prior=prior, abstain=abstain)


def _play(args):
    tok, agent, world = args
    try: AGENTS[agent](tok, world); return tok, None
    except Exception:
        import traceback; return tok, traceback.format_exc()[-1500:]


def main():
    out, names, ks = sys.argv[1], sys.argv[2].split(','), [int(k) for k in sys.argv[3].split(',')]
    batch = os.environ.get('V5_BATCH', 'v5-24-validation')
    items = [dict(world=w, arm=ARM[a], k=k, model='scripted:' + a, batch=batch) for a in names for w in F.worlds() for k in ks]
    toks = A._register(items)
    from multiprocessing import Pool
    with Pool(int(os.environ.get('V5_PROCS', '16'))) as pool, open(out, 'a') as f:
        for tok, err in pool.imap_unordered(_play, [(t, it['model'].split(':')[1], it['world']) for it, t in zip(items, toks)]):
            f.write(tok + '\n'); f.flush()
            if err: print('ERROR', tok[:8], err, flush=True)


if __name__ == '__main__':
    main()
