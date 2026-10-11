"""Stage 2r (V5_SPEC Appendix D): five scenarios 41-45 (worlds 401-410) from stage2r/SELECTION.json (WBM truth), the B2 order phase,
the claim orientation of D.4 (stage2r/ORIENT.json, MACE energies) and the stage 2r tunables. Additive: v5 stage 2 is unchanged.
install() adds the scenarios to scenarios.SCEN/TUNE/WORLD_SCEN."""
import json, os
from pymatgen.core import Composition, Lattice, Structure
from . import physics as P
from . import scenarios as SC
from . import stage2 as S2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = os.path.join(ROOT, 'stage2r', 'SELECTION.json')
ORIENT = os.path.join(ROOT, 'stage2r', 'ORIENT.json')
MANUAL = os.path.join(ROOT, 'stage2r', 'MANUAL.md')
PROTO_NAME = {'perovskite_cubic': 'cubic perovskite', 'perovskite_P4mm': 'tetragonal perovskite', 'perovskite_Pnma': 'orthorhombic perovskite',
              'perovskite_R3c': 'rhombohedral perovskite', 'ilmenite': 'ilmenite', 'rutile': 'rutile', 'fluorite': 'fluorite', 'rocksalt': 'rocksalt',
              'spinel': 'spinel', 'L1_2': 'L1_2', 'B2': 'B2'}
IMP_FRAC, IMP_LO, IMP_HI = 0.03, 0.02, 0.05
S_ORD = 0.7                   # ordered twin of 44 and 45 (as v5 S2-E and stage 1 scenario 8; D.2 amended before V5-10, X21)

# ---- frozen at V5-10 (stage2r/TUNING.md): candidate index per shape (first passing = 0; r3/r4 rejections move it) and tunables ----
PICK = {41: 0, 42: 1, 43: 0, 44: 0, 45: 0}      # 42: candidate 0 fails r3, none passes the strict r4 (X28)
TUNE2R = {41: dict(), 42: dict(N=4.0), 43: dict(N=30.0), 44: dict(N=70.0), 45: dict(N=500.0)}      # stage2r/TUNING.md


def register_b2_order(name, A, B, a):
    """B2 AB with order parameter S (S = 1: A on the corner, B at the body centre; S = 0: random bcc)."""
    def mk(S):
        s1 = {A: 0.5 + 0.5 * S, B: 0.5 - 0.5 * S}; s2 = {B: 0.5 + 0.5 * S, A: 0.5 - 0.5 * S}
        cl = lambda d: {k: v for k, v in d.items() if v > 1e-9}
        return Structure(Lattice.cubic(a), [cl(s1), cl(s2)], [[0, 0, 0], [.5, .5, .5]])
    P.PHASES[name] = P.Phase(name, lambda p, ref: mk(p['S']), {'S': 1.0, 'lattice_scale': 1.0}, order_param='S',
                             lat=lambda p: Lattice.cubic(a * p['lattice_scale']))
    return name


def _picks():
    d = json.load(open(SEL))['candidates']; pk = dict(PICK)
    for item in filter(None, os.environ.get('V5_S2R_PICK', '').split(',')):
        k, n = item.split(':'); pk[int(k)] = int(n)
    return {s: [c for c in d[str(s)] if c.get('passes')][pk[s]] for s in pk}


def _orient():
    return json.load(open(ORIENT)) if os.path.exists(ORIENT) else {}


def _pn(p): return PROTO_NAME.get(p, p)


def setup():
    sel = _picks(); ori = _orient(); out = {}
    # 41 loud polymorph control: perovskite vs ilmenite (claim names the structure MACE ranks higher in energy, D.4)
    a = sel[41]; f = a['formula']
    st = {p: S2.wbm(i) for p, i in zip(a['protos'], a['ids'])}
    names = {p: S2.register_structure(f'{f} {_pn(p)}', st[p]) for p in a['protos']}
    hi = ori.get('41', {}).get('higher', a['protos'][0]); lo = [p for p in a['protos'] if p != hi][0]
    out[41] = dict(name='S2r-41 polymorph (loud control)', kind='loud', composition=f, protos=a['protos'], ids=a['ids'],
                   claim=f'This {f} powder has the {_pn(hi)} structure rather than the {_pn(lo)} structure.',
                   description=f'{f} powder from a new synthesis route.',
                   worlds={401: dict(holds=True, phases=[[(names[hi], {}, 1.0)]]), 402: dict(holds=False, phases=[[(names[lo], {}, 1.0)]])},
                   claim_side=[SC.fixed([(names[hi], {}, 1.0)], label=_pn(hi))], other_side=[SC.fixed([(names[lo], {}, 1.0)], label=_pn(lo))])
    # 42 quiet polymorph: two perovskite variants
    b = sel[42]; f = b['formula']
    n1, n2 = [S2.register_structure(f'{f} {_pn(p)}', S2.wbm(i)) for p, i in zip(b['protos'], b['ids'])]
    p1, p2 = [_pn(p) for p in b['protos']]
    out[42] = dict(name='S2r-42 polymorph (quiet)', kind='quiet', composition=f, protos=b['protos'], ids=b['ids'],
                   claim=f'This {f} powder has the {p1} structure rather than the {p2} structure.',
                   description=f'{f} powder from a new synthesis route; both perovskite variants are plausible.',
                   worlds={403: dict(holds=True, phases=[[(n1, {}, 1.0)]]), 404: dict(holds=False, phases=[[(n2, {}, 1.0)]])},
                   claim_side=[SC.fixed([(n1, {}, 1.0)], label=p1)], other_side=[SC.fixed([(n2, {}, 1.0)], label=p2)])
    # 43 trace phase identification
    c = sel[43]; fm = c['main_formula']
    nm = S2.register_structure(f'{fm} {_pn(c["main_proto"])}', S2.wbm(c['main']))
    nP, nQ = [S2.register_structure(f'{fi} {_pn(pi)}', S2.wbm(j)) for fi, pi, j in zip(c['impurity_formulas'], c['impurity_protos'], c['impurities'])]
    lP, lQ = [f'{fi} ({_pn(pi)})' for fi, pi in zip(c['impurity_formulas'], c['impurity_protos'])]
    out[43] = dict(name='S2r-43 trace phase', kind='quiet', composition=fm, main_proto=c['main_proto'], impurity_formulas=c['impurity_formulas'],
                   impurity_protos=c['impurity_protos'],
                   claim=f'The impurity phase in this {fm} powder is {lP} rather than {lQ}.',
                   description=f'{fm} powder ({_pn(c["main_proto"])}) with one impurity phase at 2 to 5 wt %; the candidates are {lP} and {lQ}.',
                   worlds={405: dict(holds=True, phases=[[(nm, {}, 1 - IMP_FRAC), (nP, {}, IMP_FRAC)]]),
                           406: dict(holds=False, phases=[[(nm, {}, 1 - IMP_FRAC), (nQ, {}, IMP_FRAC)]])},
                   claim_side=[SC.mix(nm, nP, IMP_LO, IMP_HI)], other_side=[SC.mix(nm, nQ, IMP_LO, IMP_HI)])
    # 44 L1_2 order vs disorder (orientation D.4)
    e = sel[44]; st = S2.wbm(e['id']); comp = st.composition.get_el_amt_dict()
    A = max(comp, key=comp.get); B = min(comp, key=comp.get); aL = st.volume ** (1 / 3) / (len(st) / 4) ** (1 / 3)
    nL = S2.register_l12(f'{A}3{B} L1_2 (2r)', A, B, aL)
    ordered_higher = ori.get('44', {}).get('higher') == 'ordered'
    ordered = [[(nL, {'S': S_ORD}, 1.0)]]; disordered = [[(nL, {'S': 0.0}, 1.0)]]
    Sfam = lambda lo, hi, lab: SC.Branch(lambda u, nL=nL: [[(nL, {'S': u[0]}, 1.0)]], [lo], [hi], lab)
    if ordered_higher:
        claim = f'This {A}3{B} sample has L1_2 order with order parameter S above 0.3.'
        w = {407: dict(holds=True, phases=ordered), 408: dict(holds=False, phases=disordered)}
        cs, os_ = [Sfam(0.3, 1.0, 'S in [0.3, 1]')], [Sfam(0.0, 0.3, 'S in [0, 0.3]')]
    else:
        claim = f'This {A}3{B} sample is a disordered fcc solid solution (L1_2 order parameter S below 0.3) rather than L1_2 ordered.'
        w = {407: dict(holds=True, phases=disordered), 408: dict(holds=False, phases=ordered)}
        cs, os_ = [Sfam(0.0, 0.3, 'S in [0, 0.3]')], [Sfam(0.3, 1.0, 'S in [0.3, 1]')]
    out[44] = dict(name='S2r-44 L1_2 order', kind='quiet', composition=f'{A}3{B}', A=A, B=B, claim=claim,
                   description=f'{A}3{B} powder ({A} 75 at %), heat treatment unknown.', worlds=w, claim_side=cs, other_side=os_)
    # 45 B2 order vs disordered bcc
    g = sel[45]; st = S2.wbm(g['id']); els = sorted(st.composition.get_el_amt_dict())
    A, B = els; aB = st.volume ** (1 / 3) / (len(st) / 2) ** (1 / 3)
    nB = register_b2_order(f'{A}{B} B2 (2r)', A, B, aB)
    Sb = lambda lo, hi, lab: SC.Branch(lambda u, nB=nB: [[(nB, {'S': u[0]}, 1.0)]], [lo], [hi], lab)
    out[45] = dict(name='S2r-45 B2 order', kind='quiet', composition=f'{A}{B}', A=A, B=B,
                   claim=f'This {A}{B} sample has B2 order with order parameter S above 0.3 rather than a disordered bcc solid solution.',
                   description=f'{A}{B} powder (equiatomic), heat treatment unknown.',
                   worlds={409: dict(holds=True, phases=[[(nB, {'S': S_ORD}, 1.0)]]), 410: dict(holds=False, phases=[[(nB, {'S': 0.0}, 1.0)]])},
                   claim_side=[Sb(0.3, 1.0, 'S in [0.3, 1]')], other_side=[Sb(0.0, 0.3, 'S in [0, 0.3]')])
    for s, d in out.items():
        d['library'] = sorted(S2.PROTOTYPES); d['manual_file'] = MANUAL; d['stage'] = '2r'; d['pick'] = sel[s]
    return out


def install(tune=None):
    S2R = setup()
    SC.SCEN.update(S2R)
    for s in S2R:
        SC.TUNE[s] = dict(L=100.0, N=1000.0, bg=20.0, Nn=1000.0, bgn=50.0); SC.TUNE[s].update(TUNE2R.get(s, {}))
    o = os.environ.get('V5_2R_TUNE')                    # tuning sweeps only
    if o: [SC.TUNE[int(s)].update(v) for s, v in json.loads(o).items()]
    if tune: [SC.TUNE[s].update(v) for s, v in tune.items()]
    SC.WORLD_SCEN.update({w: s for s, d in S2R.items() for w in d['worlds']})
    return S2R


def worlds(): return list(range(401, 411))
