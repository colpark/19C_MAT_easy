"""Stage 2s (V5_SPEC Appendix E): the stage 2r shapes and replacement-round truths as scenarios 46-50 (worlds 461-470), with no free
default scan, a 10-min per-measurement overhead (neutron 125 min, X31), a budget per scenario and the stage 2s manual. Additive: the
stage 2r scenarios 41-45 stay as frozen. install() adds the scenarios to scenarios.SCEN/TUNE/WORLD_SCEN and switches the cost model of
this process to the stage 2s overhead (stage 2s processes only: the server, planner and tuning; the grader reads costs from state)."""
import json, os
from . import physics as P
from . import scenarios as SC
from . import stage2r as S2R

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, 'stage2s', 'MANUAL.md')
OVERHEAD = 10.0
NEUTRON_COST = 125.0
OFF = 5                        # scenario id offset from stage 2r (41 -> 46)
WOFF = 60                      # world id offset (401 -> 461)
QUIET = (47, 48, 49, 50)
PRIOR_DEPENDENT = (47, 48)     # 49, 50 prior-independent (X43): exempt from T2', T3 and the gate
CONTROL = 46

# ---- frozen at V5-13a (stage2s/TUNING.md): tunables, budgets (minutes) and grid window widths per scenario ----
TUNE2S = {46: dict(), 47: dict(N=10.0), 48: dict(N=200.0), 49: dict(N=330.0), 50: dict(N=300.0)}  # stage2s/TUNING.md
BUDGET2S = {46: 30.0, 47: 66.0, 48: 20.0, 49: 61.0, 50: 29.0}                                    # E.4: ceil(1.2 c_dec); 46: max(round(1.25 c_dec), 30)
WIDTHS2S = {s: (2.0, 4.0, 6.0) for s in range(46, 51)}
# gate replacement round (E.6, one round under the frozen stage 2r rule): 47 takes the next passing quiet-polymorph candidate, ScMnO3
ROUND2 = os.environ.get('V5_S2S_ROUND') == '2'
ROUND2_PICK = {42: 3}                                       # stage 2r candidate index (mirror of 47)
ROUND2_TUNE = {47: dict(N=5.0)}
ROUND2_BUDGET = {47: 25.0}
if ROUND2:
    [TUNE2S[s].update(v) for s, v in ROUND2_TUNE.items()]; BUDGET2S.update(ROUND2_BUDGET)


def cost_min(n_points, t_step): return n_points * t_step / 60.0 + OVERHEAD


def _round2_setup():
    saved = dict(S2R.PICK); S2R.PICK.update(S2R.ROUND2_PICK)
    if ROUND2: S2R.PICK.update(ROUND2_PICK)
    try: return S2R.setup()
    finally: S2R.PICK.clear(); S2R.PICK.update(saved)


def setup():
    d2r = _round2_setup(); out = {}
    for s, d in d2r.items():
        e = dict(d); e['worlds'] = {w + WOFF: dict(v) for w, v in d['worlds'].items()}
        e['name'] = d['name'].replace('S2r-%d' % s, 'S2s-%d' % (s + OFF)); e['manual_file'] = MANUAL; e['stage'] = '2s'
        e['mirror_2r'] = s; e['budget'] = BUDGET2S[s + OFF]; e['widths'] = WIDTHS2S[s + OFF]
        out[s + OFF] = e
    return out


def install(tune=None, cost=True):
    S2S = setup()
    SC.SCEN.update(S2S)
    for s in S2S:
        SC.TUNE[s] = dict(L=100.0, N=1000.0, bg=20.0, Nn=1000.0, bgn=50.0); SC.TUNE[s].update(dict(S2R.TUNE2R.get(s - OFF, {})))
        SC.TUNE[s].update(S2R.ROUND2_TUNE.get(s - OFF, {})); SC.TUNE[s].update(TUNE2S.get(s, {}))
    o = os.environ.get('V5_2S_TUNE')                    # tuning sweeps only
    if o: [SC.TUNE[int(s)].update(v) for s, v in json.loads(o).items()]
    b = os.environ.get('V5_2S_BUDGET')
    if b: [SC.SCEN[int(s)].update(budget=float(v)) for s, v in json.loads(b).items()]
    wd = os.environ.get('V5_2S_WIDTHS')
    if wd: [SC.SCEN[int(s)].update(widths=tuple(v)) for s, v in json.loads(wd).items()]
    if tune: [SC.TUNE[s].update(v) for s, v in tune.items()]
    SC.WORLD_SCEN.update({w: s for s, d in S2S.items() for w in d['worlds']})
    if cost:
        P.cost_min = cost_min; P.NEUTRON['cost_min'] = NEUTRON_COST           # t of the neutron protocol is unchanged (115 min of counting)
    return S2S


def worlds(): return list(range(461, 471))
def budget(scen): return SC.SCEN[scen]['budget']
