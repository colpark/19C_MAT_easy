"""Stage 1b (V5_SPEC Appendix C): v5 scenarios 1-10 mirrored as scenarios 21-30 (worlds 201-228), retuned, with hold worlds and the
unstated arm. Additive: install() adds the stage 1b scenarios to scenarios.SCEN/TUNE/WORLD_SCEN and switches the plan grid to the
refined time grid (C.3). v5 definitions are not changed. Tunables, margins and hold choices are logged in stage1b/TUNING.md."""
import copy, json, os
from . import scenarios as SC
from . import plangrid as PG

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANUAL = os.path.join(ROOT, 'stage1b', 'MANUAL.md')
TIMES_1B = (0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.5, 15.0, 20.0)
OFFSET = 20                                  # scenario 20 + i mirrors v5 scenario i
WORLD_IDS = {21: (201, 202), 22: (203, 204), 23: (205, 206, 207), 24: (208, 209, 210), 25: (211, 212, 213), 26: (214, 215, 216),
             27: (217, 218, 219), 28: (220, 221, 222), 29: (223, 224, 225), 30: (226, 227, 228)}
QUIET = (23, 24, 25, 26, 27, 28, 30)
HOLD_OPTIONS = {'displacement': dict(disp_add=0.15), 'zero': dict(zero_deg=0.01), 'size': dict(L_factor=0.5), 'background': dict(bg_factor=2.0)}
HOLD_PREF = {23: 'displacement', 24: 'background', 25: 'displacement', 26: 'size', 28: 'size', 29: 'background', 30: 'displacement'}
HOLD_FALLBACK = ('size', 'background', 'displacement', 'zero')

# ---- frozen at V5-8 (stage1b/TUNING.md); overridable for tuning sweeps through V5_1B_OVERRIDE (JSON) ----
TUNE1B = {s + OFFSET: dict(v) for s, v in SC.TUNE.items() if 1 <= s <= 10}
TUNE1B[23].update(N=13.0, L=60.0, bg=20.0, Nn=500.0)          # neutron is the decisive route (X22)
TUNE1B[24].update(N=420.0)
TUNE1B[25].update(N=2.0, L=30.0, bg=20.0, Nn=100.0)
TUNE1B[27].update(N=14.0)                                      # L 1000, bg 2 as v5
TUNE1B[28].update(N=97.0, Nn=300.0)
TUNE1B[30].update(N=15.5, Nn=30.0)
MARGIN = {24: 0.006, 27: 0.0006, 28: 0.43}   # far-twin margins (C.2, X24): 24 rutile fraction of the claim-false twin, 27 lattice change, 28 S of the claim-true twin
HOLD = dict(HOLD_PREF)
HOLD.update({24: 'displacement', 28: 'displacement'})          # preferred nuisance breaks rule H (stage1b/TUNING.md)


def _override():
    o = os.environ.get('V5_1B_OVERRIDE')
    if not o: return
    d = json.loads(open(o).read() if os.path.exists(o) else o)
    for s, v in d.get('tune', {}).items(): TUNE1B[int(s)].update(v)
    MARGIN.update({int(s): v for s, v in d.get('margin', {}).items()})
    HOLD.update({int(s): v for s, v in d.get('hold', {}).items()})


def build():
    _override()
    out = {}
    for s0 in range(1, 11):
        s = s0 + OFFSET; d = copy.copy(SC.SCEN[s0]); ids = WORLD_IDS[s]
        old = [d['worlds'][w] for w in sorted(d['worlds'])]
        worlds = {}
        for w, ow in zip(ids, old): worlds[w] = copy.deepcopy(ow)
        if s == 24 and 24 in MARGIN:
            f = MARGIN[24]; worlds[ids[1]]['phases'] = [[('anatase', {}, 1 - f), ('rutile', {}, f)]]
        if s == 27 and 27 in MARGIN:
            worlds[ids[2]]['phases'] = [[('rutile', {'lattice_scale': 1 + MARGIN[27]}, 1.0)]]
        if s == 28 and 28 in MARGIN:
            worlds[ids[0]]['phases'] = [[('Ni3Al', {'S': MARGIN[28]}, 1.0)]]
        if s == 27:
            worlds[ids[1]]['hold'] = 'displacement (absolute s = +0.15 mm, as v5 world 14)'
        elif s in HOLD_PREF:
            twin = worlds[ids[0]]
            hw = dict(holds=twin['holds'], phases=copy.deepcopy(twin['phases']), hold=HOLD[s], added_hold=True, hold_of=ids[0])
            hw.update(HOLD_OPTIONS[HOLD[s]])
            worlds[ids[2]] = hw
        d['worlds'] = worlds; d['manual_file'] = MANUAL; d['v5_scenario'] = s0
        out[s] = d
    return out


def install():
    S1B = build()
    SC.SCEN.update(S1B)
    for s in S1B: SC.TUNE[s] = dict(TUNE1B[s])
    SC.WORLD_SCEN.update({w: s for s, d in S1B.items() for w in d['worlds']})
    PG.TIMES = TIMES_1B
    return S1B


def worlds(): return sorted(w for ws in WORLD_IDS.values() for w in ws)


def pair_worlds(scen):
    """worlds that count for pair resolution (C.8): all but the added hold world."""
    return [w for w in SC.twins(scen) if not SC.SCEN[scen]['worlds'][w].get('added_hold')]


def hold_world(scen):
    for w in SC.twins(scen):
        if SC.SCEN[scen]['worlds'][w].get('hold'): return w
    return None
