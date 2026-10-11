"""Stage 2 (V5_SPEC Appendix B): structure-generic phases, prototype builder, placebo relax, and the five scenarios from
stage2/SELECTION.json (WBM truth). Registers phases into physics.PHASES so the stage 1 instrument model, D and grader apply unchanged."""
import hashlib, json, math, os, re, zipfile
import numpy as np
from pymatgen.core import Composition, Element, Lattice, Structure
from . import physics as P
from . import scenarios as SC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WBM_ZIP = os.path.join(ROOT, 'data', 'stage2', '2024-08-04-wbm-relaxed-atoms.extxyz.zip')
SEL = os.path.join(ROOT, 'stage2', 'SELECTION.json')
N_A = 6.02214076e23


# ---------------------------------------------------------------- structure phases
def _hash(st): return hashlib.sha256(json.dumps(st.as_dict(), sort_keys=True, default=str).encode()).hexdigest()[:12]


def register_structure(name, st, c_strain=False):
    """phase `name` from a Structure; params lattice_scale (all axes) and, with c_strain, c_over_a_rel (c/a relative to the
    structure's, at constant volume). Intensities from the reference geometry (c_over_a_rel 1.01 when c_strain, distinct families)."""
    st = st.copy()

    def build(p, ref):
        s = st.copy(); r = (1.01 if ref else p['c_over_a_rel']) if c_strain else 1.0
        m = s.lattice.matrix.copy(); m[0] *= r ** (-1 / 3); m[1] *= r ** (-1 / 3); m[2] *= r ** (2 / 3)
        s.lattice = Lattice(m * (1.0 if ref else p['lattice_scale']))
        return s

    def lat(p):
        r = p['c_over_a_rel'] if c_strain else 1.0
        m = st.lattice.matrix.copy(); m[0] *= r ** (-1 / 3); m[1] *= r ** (-1 / 3); m[2] *= r ** (2 / 3)
        return Lattice(m * p['lattice_scale'])
    d = {'lattice_scale': 1.0}
    if c_strain: d['c_over_a_rel'] = 1.0
    P.PHASES[name] = P.Phase(name, build, d, lat=lat)
    return name


def register_l12(name, A, B, a):
    """L1_2 A3B with order parameter S (B on the corner when ordered)."""
    def mk(S):
        corner = {B: 0.25 + 0.75 * S, A: 0.75 * (1 - S)}; face = {B: 0.25 * (1 - S), A: 1 - 0.25 * (1 - S)}
        clean = lambda d: {k: v for k, v in d.items() if v > 1e-9}
        return Structure(Lattice.cubic(a), [clean(corner)] + [clean(face)] * 3, [[0, 0, 0], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
    P.PHASES[name] = P.Phase(name, lambda p, ref: mk(p['S']), {'S': 1.0, 'lattice_scale': 1.0}, order_param='S',
                             lat=lambda p: Lattice.cubic(a * p['lattice_scale']))
    return name


def register_b2_alloy(name, A, X1, X2, a1, a2):
    """B2 A(X1_{1-x} X2_x) with Vegard lattice between a1 and a2."""
    def mk(x):
        return Structure(Lattice.cubic((1 - x) * a1 + x * a2), [A, {X1: 1 - x, X2: x}] if 0 < x < 1 else [A, X1 if x == 0 else X2], [[0, 0, 0], [.5, .5, .5]])
    P.PHASES[name] = P.Phase(name, lambda p, ref: mk(round(p['x'], 2)), {'x': 0.5, 'lattice_scale': 1.0}, iparams=('x',),
                             lat=lambda p: Lattice.cubic(((1 - p['x']) * a1 + p['x'] * a2) * p['lattice_scale']))
    return name


# ---------------------------------------------------------------- WBM
def wbm(mid):
    with zipfile.ZipFile(WBM_ZIP) as z:
        txt = z.read(f'{mid}.extxyz').decode().strip().splitlines()
    n = int(txt[0]); lat = np.array([float(x) for x in re.search(r'Lattice="([^"]+)"', txt[1]).group(1).split()]).reshape(3, 3)
    sp = [l.split()[0] for l in txt[2:2 + n]]; pos = [[float(v) for v in l.split()[1:4]] for l in txt[2:2 + n]]
    from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
    s = Structure(Lattice(lat), sp, pos, coords_are_cartesian=True)
    return SpacegroupAnalyzer(s, symprec=1e-3).get_conventional_standard_structure()


def cubic_from_tetragonal(st):
    """same volume, cubic metric, fractional positions symmetrized to the ideal perovskite (z -> 0 or 0.5)."""
    a = st.volume ** (1 / 3)
    fr = np.round(st.frac_coords * 2) / 2
    return Structure(Lattice.cubic(a), st.species, fr)


# ---------------------------------------------------------------- prototypes (agent build) and placebo
PROTOTYPES = {
    'cubic perovskite': dict(roles=['A', 'B', 'X'], params={'a': None}),
    'tetragonal perovskite': dict(roles=['A', 'B', 'X'], params={'a': None, 'c_over_a': 1.01, 'dz_B': 0.0, 'dz_X': 0.0}),
    'orthorhombic perovskite': dict(roles=['A', 'B', 'X'], params={'a_pc': None}),
    'rhombohedral perovskite': dict(roles=['A', 'B', 'X'], params={'a_pc': None}),
    'ilmenite': dict(roles=['A', 'B', 'X'], params={'a_pc': None}),
    'spinel': dict(roles=['A', 'B', 'X'], params={'a': None, 'u': 0.2625}),
    'rocksalt': dict(roles=['A', 'X'], params={'a': None}),
    'fluorite': dict(roles=['A', 'X'], params={'a': None}),
    'rutile': dict(roles=['A', 'X'], params={'a': None, 'c_over_a': 0.65, 'x': 0.305}),
    'L1_2': dict(roles=['A', 'B'], params={'a': None, 'S': 1.0}),
    'B2': dict(roles=['A', 'B'], params={'a': None}),
    'kesterite': dict(roles=['A', 'B', 'C', 'X'], params={'a': None, 'c_over_a': 2.0}),
}


def vol_atom(el):
    v = Element(el).molar_volume
    return float(v) / N_A * 1e24 if v else 20.0


def placebo_volume(st):
    """fixed additive table (B.3): sum over sites of occupancy-weighted elemental-solid volume per atom."""
    return sum(sum(f * vol_atom(e.symbol) for e, f in site.species.items()) for site in st)


def _site(v): return v if isinstance(v, str) else dict(v)


def build(proto, sites, params):
    """sites: role -> element or {element: fraction}. Lattice parameters missing -> placebo volume rule."""
    if proto not in PROTOTYPES: raise ValueError(f'unknown prototype {proto!r}; known: {sorted(PROTOTYPES)}')
    roles = PROTOTYPES[proto]['roles']
    if set(sites) != set(roles): raise ValueError(f'{proto} needs sites for roles {roles}')
    pr = dict(PROTOTYPES[proto]['params']); pr.update({k: float(v) for k, v in (params or {}).items() if k in pr})
    S = {r: _site(sites[r]) for r in roles}
    if proto == 'cubic perovskite':
        st = Structure(Lattice.cubic(1), [S['A'], S['B'], S['X'], S['X'], S['X']], [[0, 0, 0], [.5, .5, .5], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
    elif proto == 'tetragonal perovskite':
        ca = pr['c_over_a']; st = Structure(Lattice.tetragonal(1, ca), [S['A'], S['B'], S['X'], S['X'], S['X']],
                                           [[0, 0, 0], [.5, .5, .5 + pr['dz_B']], [.5, .5, pr['dz_X']], [.5, 0, .5 + pr['dz_X']], [0, .5, .5 + pr['dz_X']]])
    elif proto == 'orthorhombic perovskite':
        st = Structure.from_spacegroup('Pnma', Lattice.orthorhombic(math.sqrt(2), 2, math.sqrt(2)), [S['A'], S['B'], S['X'], S['X']],
                                       [[0.05, 0.25, 0.99], [0, 0, 0.5], [0.47, 0.25, 0.09], [0.30, 0.05, 0.70]])
    elif proto == 'rhombohedral perovskite':
        st = Structure.from_spacegroup('R3c', Lattice.hexagonal(math.sqrt(2), 2 * math.sqrt(3)), [S['A'], S['B'], S['X']],
                                       [[0, 0, 0.28], [0, 0, 0.0], [0.05, 0.34, 0.06]])
    elif proto == 'ilmenite':
        st = Structure.from_spacegroup('R-3', Lattice.hexagonal(math.sqrt(2), 2 * math.sqrt(3)), [S['A'], S['B'], S['X']],
                                       [[0, 0, 0.355], [0, 0, 0.146], [0.317, 0.02, 0.245]])
    elif proto == 'spinel':
        st = Structure.from_spacegroup(227, Lattice.cubic(1), [S['A'], S['B'], S['X']], [[0.125, 0.125, 0.125], [0.5, 0.5, 0.5], [pr['u']] * 3])
    elif proto == 'rocksalt':
        st = Structure.from_spacegroup('Fm-3m', Lattice.cubic(1), [S['A'], S['X']], [[0, 0, 0], [.5, .5, .5]])
    elif proto == 'fluorite':
        st = Structure.from_spacegroup('Fm-3m', Lattice.cubic(1), [S['A'], S['X']], [[0, 0, 0], [.25, .25, .25]])
    elif proto == 'rutile':
        st = Structure.from_spacegroup('P4_2/mnm', Lattice.tetragonal(1, pr['c_over_a']), [S['A'], S['X']], [[0, 0, 0], [pr['x'], pr['x'], 0]])
    elif proto == 'L1_2':
        Sv = pr['S']; A, B = S['A'], S['B']
        if not isinstance(A, str) or not isinstance(B, str): raise ValueError('L1_2: A (majority) and B (minority) must be single elements')
        corner = {B: 0.25 + 0.75 * Sv, A: 0.75 * (1 - Sv)}; face = {B: 0.25 * (1 - Sv), A: 1 - 0.25 * (1 - Sv)}
        cl = lambda d: {k: v for k, v in d.items() if v > 1e-9}
        st = Structure(Lattice.cubic(1), [cl(corner)] + [cl(face)] * 3, [[0, 0, 0], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
    elif proto == 'B2':
        st = Structure(Lattice.cubic(1), [S['A'], S['B']], [[0, 0, 0], [.5, .5, .5]])
    elif proto == 'kesterite':
        st = Structure.from_spacegroup('I-4', Lattice.tetragonal(1, pr['c_over_a']), [S['A'], S['C'], S['A'], S['B'], S['X']],
                                       [[0, 0, 0], [0, 0, .5], [0, .5, .25], [0, .5, .75], [0.756, 0.757, 0.872]])
    given = pr.get('a') or pr.get('a_pc')
    if given:
        st.scale_lattice(st.volume * (given / st.lattice.a) ** 3 if 'a' in pr else (given ** 3 * len(st) / 5))
    else:
        st.scale_lattice(placebo_volume(st))
    return st


def placebo_relax(st):
    s = st.copy(); s.scale_lattice(placebo_volume(s))
    e = sum(-sum(f * 1.0 for _, f in site.species.items()) for site in s) / len(s)    # no physics: table energy -1 eV/atom
    return s, e


# ---------------------------------------------------------------- scenarios
def pick_candidates():
    """the chosen candidate per scenario, or (env V5_S2_PICK='S2-B:1,S2-D:2') the n-th passing candidate of that scenario's frozen
    candidate list in SELECTION.json (gate replacements, prompt 6.5; no rule change)."""
    d = json.load(open(SEL)); sel = dict(d['chosen'])
    for item in filter(None, os.environ.get('V5_S2_PICK', '').split(',')):
        key, n = item.split(':'); n = int(n); c = d['candidates'][key]
        lst = c if isinstance(c, list) else c['first']
        lst = [x for x in lst if x.get('passes', True)]
        sel[key] = lst[n]
    return sel


def setup():
    """register stage 2 phases and return the stage 2 scenario dict (same schema as scenarios.SCEN)."""
    sel = pick_candidates(); S2 = {}
    # S2-A loud: two DFT polymorphs
    a = sel['S2-A']; f = a['formula']
    pA = register_structure(f'{f} {a["protos"][0]}', wbm(a['ids'][0])); pB = register_structure(f'{f} {a["protos"][1]}', wbm(a['ids'][1]))
    S2[11] = dict(name='S2-A polymorph', kind='loud', claim=f'This {f} powder has the {a["protos"][0].replace("_", " ")} structure rather than the {a["protos"][1].replace("_", " ")} structure.',
                  description=f'{f} powder from a new synthesis route.', composition=f,
                  worlds={101: dict(holds=True, phases=[[(pA, {}, 1.0)]]), 102: dict(holds=False, phases=[[(pB, {}, 1.0)]])},
                  claim_side=[SC.fixed([(pA, {}, 1.0)], label=a['protos'][0])], other_side=[SC.fixed([(pB, {}, 1.0)], label=a['protos'][1])])
    # S2-B tetragonality
    b = sel['S2-B']; f = b['formula']; st = wbm(b['id']); ca = st.lattice.c / st.lattice.a
    if ca < 1: ca = 1 / ca
    t = round((1 + ca) / 2, 5)
    pT = register_structure(f'{f} tetragonal (truth)', st, c_strain=True); pC = register_structure(f'{f} cubic', cubic_from_tetragonal(st))
    rel_t = t / ca
    S2[12] = dict(name='S2-B tetragonality', kind='quiet', claim=f'This {f} ceramic is tetragonal (P4mm) with c/a of at least {t}, rather than cubic.',
                  description=f'Fine-grained {f} ceramic, crushed to powder.', composition=f, threshold=t,
                  worlds={103: dict(holds=True, phases=[[(pT, {}, 1.0)]]), 104: dict(holds=False, phases=[[(pC, {}, 1.0)]])},
                  claim_side=[SC.Branch(lambda u, pT=pT: [[(pT, {'c_over_a_rel': u[0], 'lattice_scale': u[1]}, 1.0)]], [rel_t, 0.995], [1.03 / ca, 1.005],
                                        f'P4mm c/a in [{t}, 1.03], volume free')],
                  other_side=[SC.Branch(lambda u, pC=pC: [[(pC, {'lattice_scale': u[0]}, 1.0)]], [0.995], [1.005], 'cubic, a free')])
    # S2-C trace impurity
    c = sel['S2-C']; fm, fi = c['main_formula'], c['impurity_formula']
    pM = register_structure(f'{fm} cubic perovskite', wbm(c['main'])); pI = register_structure(f'{fi} {c["impurity_proto"]}', wbm(c['impurity']))
    S2[13] = dict(name='S2-C trace impurity', kind='quiet', claim=f'This {fm} powder contains less than 0.3 wt % {fi}.',
                  description=f'{fm} powder; {fi} ({c["impurity_proto"]}) is the possible impurity.', composition=fm,
                  worlds={105: dict(holds=True, phases=[[(pM, {}, 1.0), (pI, {}, 0.0)]]), 106: dict(holds=False, phases=[[(pM, {}, 0.99), (pI, {}, 0.01)]])},
                  claim_side=[SC.mix(pM, pI, 0.0, 0.003)], other_side=[SC.mix(pM, pI, 0.003, 0.05)])
    # S2-D alloy vs two phases (B2)
    d = sel['S2-D']; X = d['X']; s1, s2 = wbm(d['ids'][0]), wbm(d['ids'][1])
    o1 = [e.symbol for e in s1.composition.elements if e.symbol != X][0]; o2 = [e.symbol for e in s2.composition.elements if e.symbol != X][0]
    a1, a2 = s1.volume ** (1 / 3) / (len(s1) / 2) ** (1 / 3), s2.volume ** (1 / 3) / (len(s2) / 2) ** (1 / 3)
    p1 = register_structure(f'{X}{o1} B2', Structure(Lattice.cubic(a1), [X, o1], [[0, 0, 0], [.5, .5, .5]]))
    p2 = register_structure(f'{X}{o2} B2', Structure(Lattice.cubic(a2), [X, o2], [[0, 0, 0], [.5, .5, .5]]))
    pAl = register_b2_alloy(f'{X}({o1},{o2}) B2 alloy', X, o1, o2, a1, a2)
    m1 = Composition(f'{X}{o1}').weight; m2 = Composition(f'{X}{o2}').weight
    S2[14] = dict(name='S2-D alloy', kind='quiet', claim=f'This {X}({o1}0.5{o2}0.5) sample is one B2 alloy phase rather than a mixture of {X}{o1} and {X}{o2}.',
                  description=f'Mechanically alloyed {X}-{o1}-{o2} powder, overall {X}({o1}0.5{o2}0.5), nanocrystalline.', composition=f'{X}2{o1}{o2}',
                  mismatch=abs(a1 / a2 - 1),
                  worlds={107: dict(holds=True, phases=[[(pAl, {'x': 0.5}, 1.0)]]), 108: dict(holds=False, phases=[[(p1, {}, m1 / (m1 + m2)), (p2, {}, m2 / (m1 + m2))]])},
                  claim_side=[SC.fixed([(pAl, {'x': 0.5}, 1.0)], label='one alloy, x = 0.5')],
                  other_side=[SC.fixed([(p1, {}, 1.0)], [(p2, {}, 1.0)], label=f'{X}{o1} + {X}{o2}, ratio free')])
    # S2-E L1_2 order
    e = sel['S2-E']; st = wbm(e['id']); comp = st.composition.get_el_amt_dict()
    A = max(comp, key=comp.get); B = min(comp, key=comp.get); aL = st.volume ** (1 / 3) / (len(st) / 4) ** (1 / 3)
    pL = register_l12(f'{A}3{B} L1_2', A, B, aL)
    S2[15] = dict(name='S2-E order', kind='quiet', claim=f'This {A}3{B} sample has L1_2 order with order parameter S above 0.3.',
                  description=f'{A}3{B} powder ({A} 75 at %), heat treatment unknown.', composition=f'{A}3{B}',
                  worlds={109: dict(holds=True, phases=[[(pL, {'S': 0.7}, 1.0)]]), 110: dict(holds=False, phases=[[(pL, {'S': 0.0}, 1.0)]])},
                  claim_side=[SC.Branch(lambda u, pL=pL: [[(pL, {'S': u[0]}, 1.0)]], [0.3], [1.0], 'S in [0.3, 1]')],
                  other_side=[SC.Branch(lambda u, pL=pL: [[(pL, {'S': u[0]}, 1.0)]], [0.0], [0.3], 'S in [0, 0.3]')])
    for s, dd in S2.items(): dd['library'] = sorted(PROTOTYPES)
    return S2


# stage 2 tunables (stage2/TUNING2.md; sweeps s2a to s2d in scenarios/tuning_runs/)
TUNE2 = {11: dict(), 12: dict(N=32.0, L=60.0, bg=5.0), 13: dict(), 14: dict(N=10.0, L=30.0), 15: dict(N=400.0)}


# tunables of replacement candidates (gate replacement round, stage2/TUNING2.md), keyed by V5_S2_PICK entries
TUNE2_PICK = {'S2-B:1': dict(N=10.0, L=30.0, bg=5.0), 'S2-C:1': dict(N=450.0), 'S2-D:1': dict(), 'S2-E:1': dict(N=500.0)}
_PICK_SCEN = {'S2-A': 11, 'S2-B': 12, 'S2-C': 13, 'S2-D': 14, 'S2-E': 15}


def install(tune=None):
    """add stage 2 scenarios to scenarios.SCEN/TUNE/WORLD_SCEN (worlds 101-110, scenarios 11-15)."""
    S2 = setup()
    SC.SCEN.update(S2)
    for s in S2:
        SC.TUNE.setdefault(s, dict(L=100.0, N=1000.0, bg=20.0, Nn=1000.0, bgn=50.0)); SC.TUNE[s].update(TUNE2.get(s, {}))
    for item in filter(None, os.environ.get('V5_S2_PICK', '').split(',')):
        SC.TUNE[_PICK_SCEN[item.split(':')[0]]].update(TUNE2_PICK.get(item, {}))
    if tune: [SC.TUNE[s].update(v) for s, v in tune.items()]
    SC.WORLD_SCEN.update({w: s for s, d in S2.items() for w in d['worlds']})
    return S2
