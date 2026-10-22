"""v7 families (V7-1): install the T scenarios (v7/T/WORLDS_T.json, scenarios 301-370) and the H scenarios (v7/H/WORLDS_H.json, 401 and up)
into scenarios.SCEN/TUNE/WORLD_SCEN.

T. A T world is one cell of a compound's quad (cell 1 H to L, 2 L to L, 3 H to H, 4 L to H) or one of its hold variants (10+c displacement
+0.10 mm, 20+c zero offset +0.005 deg, 30+c size x 1.2, applied to both samples). Its registry id is scen*100 + cell. Each world holds two
physical samples, pre and post; each sample is its own mcenv sub-world (id scen*1000 + 2 + 2*cell + (0 pre, 1 post)) with its phase, the
sample's hidden displacement, zero offset and size (WORLDS_T 'samples'; the same in all cells), and every other library polymorph as the
other side (D against the best other polymorph, as B1). Sub-world scen*1000 is the reference: twin A's (L) polymorph at size 100 nm,
nominal geometry, so the count scale is B1's (N counts at L's strongest m0 peak). The noise key of a sample is f'{seed_scen}|{sample}'
(server7), shared by the four cells and the holds.

H. As B1 (mcenv/bench6.py): worlds scen*10+1 (twin A, hull <= 0.03), scen*10+2 (twin B, hull >= 0.07), hold worlds +3..8."""
import json, os
from pymatgen.core import Composition, Structure
from . import scenarios as SC
from . import stage2 as S2
from . import physics as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T_WORLDS = os.path.join(ROOT, 'T', 'WORLDS_T.json')
T_CACHE = os.path.join(ROOT, 'T', 'library_structures_T.json')
H_WORLDS = os.path.join(ROOT, 'H', 'WORLDS_H.json')
H_CACHE = os.path.join(ROOT, 'H', 'library_structures_H.json')
MANUAL_T = os.path.join(ROOT, 'MANUAL_T.md')
MANUAL_H = os.path.join(ROOT, 'MANUAL_H.md')
NUM = {2: 'two', 3: 'three'}
HOLD_T = {10: dict(disp_add=0.10), 20: dict(zero_add=0.005), 30: dict(L_factor=1.2)}
CELLS = {1: ('H', 'L', 'SUPPORTED', True), 2: ('L', 'L', 'REFUTED', False), 3: ('H', 'H', 'REFUTED', False), 4: ('L', 'H', 'REFUTED', True)}
COUNT_TEXT = ("This lab has one count scale, the same for every library phase and every sample: simulate returns expected counts at this "
              "scale (X-ray and neutron), so the expected count level of any library phase at any measurement is what simulate gives for it. The "
              "count level is not otherwise stated. The statement is the same whichever library phase the sample holds.")     # B1 wording (V6-X17)
T_SCEN = {}          # T world id -> dict(scen, cell, base_cell, hold, pre, post, key, fm_decides)


def _register(name, st):
    if name in P.PHASES:
        old = P.PHASES[name].structure({'lattice_scale': 1.0})
        if len(old) != len(st) or abs(old.lattice.volume - st.lattice.volume) > 1e-3:
            raise ValueError(f'structure name {name!r} is already registered with another structure')
    return S2.register_structure(name, st)


def t_sub(scen, cell, sample): return scen * 1000 + 2 + 2 * cell + (0 if sample == 'pre' else 1)


def setup_T(path=T_WORLDS, cache=T_CACHE):
    if not os.path.exists(path): return {}
    B = json.load(open(path)); cs = {k: Structure.from_dict(v) for k, v in json.load(open(cache)).items()}
    out = {}
    for W in B['worlds']:
        s, f = W['scen'], W['formula']
        ids = W['polymorph_ids'] + [d['id'] for d in W['distractors']]
        names = {i: _register(W['names_by_id'][i], cs[i]) for i in ids}
        polys = [names[i] for i in W['polymorph_ids']]; nL, nH = names[W['L']], names[W['H']]
        br = {n: SC.fixed([(n, {}, 1.0)], label=n) for n in polys}
        other = lambda n: [br[o] for o in polys if o != n]
        worlds = {s * 1000: dict(holds=True, phases=[[(nL, {}, 1.0)]], other_branches=other(nL), disp_mm=0.0, zero_deg=0.0, L_factor=1.0, reference=True)}
        for c, (pre, post, key, fmd) in CELLS.items():
            for hold in (0, 10, 20, 30):
                cell = hold + c
                for sample, ph in (('pre', pre), ('post', post)):
                    n = nL if ph == 'L' else nH; nu = W['samples'][sample]
                    d = dict(holds=ph == 'L', phases=[[(n, {}, 1.0)]], other_branches=other(n), disp_mm=nu['disp_mm'], zero_deg=nu['zero_deg'],
                             L_factor=nu['L_nm'] / 100.0, sample=sample, t_world=s * 100 + cell, polymorph=ph)
                    if hold == 10: d['disp_mm'] = round(d['disp_mm'] + 0.10, 6)
                    if hold == 20: d['zero_deg'] = round(d['zero_deg'] + 0.005, 6)
                    if hold == 30: d['L_factor'] = d['L_factor'] * 1.2
                    if hold: d.update(added_hold=True, hold=f'{list(HOLD_T[hold])[0]} {list(HOLD_T[hold].values())[0]}')
                    worlds[t_sub(s, cell, sample)] = d
                T_SCEN[s * 100 + cell] = dict(scen=s, cell=cell, base_cell=c, hold=hold, pre=t_sub(s, cell, 'pre'), post=t_sub(s, cell, 'post'),
                                              key=key, fm_decides=fmd, phase_pre=nL if pre == 'L' else nH, phase_post=nL if post == 'L' else nH)
        system = '-'.join(sorted(e.symbol for e in Composition(f).elements))
        out[s] = dict(name=f'v7-T-{s} {f}', kind='T', claim_type='T', stage='7T', composition=f, set=W['set'], stratum=W['stratum'], slot=W.get('slot', 'take'),
                      claim=f'The heat treatment left this {f} material in a lower-energy polymorph than before.',
                      description=(f'Two samples of {f}: pre was taken before a heat treatment, post after it. The treatment may or may not have changed '
                                   f'the polymorph. Each sample is {f} powder, single crystalline phase. The library lists every known {f} polymorph '
                                   f'({NUM[len(polys)]}; the candidates for each sample\'s phase) and two other phases of the {system} system, with their structures.'),
                      library=sorted(names.values()), polymorphs=polys, names_by_id=names, ids=W['polymorph_ids'], L=nL, H=nH,
                      worlds=worlds, claim_side=[br[nL]], other_side=other(nL), manual_file=MANUAL_T, N=float(W['N']), budget=float(W.get('budget', 240.0)),
                      seed_scen=s)
    return out


def setup_H(path=H_WORLDS, cache=H_CACHE):
    if not os.path.exists(path): return {}
    B = json.load(open(path)); cs = {k: Structure.from_dict(v) for k, v in json.load(open(cache)).items()}
    out = {}
    HOLDS = {3: ('A', dict(disp_add=0.10)), 4: ('A', dict(zero_add=0.005)), 5: ('A', dict(L_factor=1.2)),
             6: ('B', dict(disp_add=0.10)), 7: ('B', dict(zero_add=0.005)), 8: ('B', dict(L_factor=1.2))}
    for W in B['worlds']:
        s, f = W['scen'], W['formula']
        ids = W['polymorph_ids'] + [d['id'] for d in W['distractors']]
        names = {i: _register(W['names_by_id'][i], cs[i]) for i in ids}
        polys = [names[i] for i in W['polymorph_ids']]
        br = {n: SC.fixed([(n, {}, 1.0)], label=n) for n in polys}
        na, nb = names[W['a']], names[W['b']]
        worlds = {s * 10 + 1: dict(holds=True, phases=[[(na, {}, 1.0)]], other_branches=[br[o] for o in polys if o != na]),
                  s * 10 + 2: dict(holds=False, phases=[[(nb, {}, 1.0)]], other_branches=[br[o] for o in polys if o != nb])}
        for off, (tw, nu) in HOLDS.items():
            base = worlds[s * 10 + (1 if tw == 'A' else 2)]
            worlds[s * 10 + off] = dict(base, added_hold=True, hold=f'{tw}: ' + ', '.join(f'{k} {v}' for k, v in nu.items()), **nu)
        system = '-'.join(sorted(e.symbol for e in Composition(f).elements))
        out[s] = dict(name=f'v7-H-{s} {f}', kind='H', claim_type='H', stage='7H', composition=f, type=W['type'], stratum=W.get('panel'), slot=W.get('slot', 'take'),
                      claim='The crystalline phase in this sample lies within 50 meV/atom of the convex hull.',
                      description=(f'{f} powder from a new synthesis route, single crystalline phase. The library lists every known {f} polymorph '
                                   f'({NUM.get(len(polys), str(len(polys)))}; the candidates for this sample\'s phase) and two other phases of the {system} system, with their structures.'),
                      library=sorted(names.values()), polymorphs=polys, names_by_id=names, ids=W['polymorph_ids'],
                      worlds=worlds, claim_side=[br[na]], other_side=[br[o] for o in polys if o != na], manual_file=MANUAL_H, N=float(W['N']))
    return out


def install():
    S = {}; S.update(setup_T()); S.update(setup_H())
    SC.SCEN.update(S)
    for s, d in S.items():
        SC.TUNE[s] = dict(L=100.0, N=d['N'], bg=20.0, Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({w: s for s, d in S.items() for w in d['worlds']})
    SC.WORLD_SCEN.update({tw: v['scen'] for tw, v in T_SCEN.items()})
    return S
