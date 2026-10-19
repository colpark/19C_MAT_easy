"""Stage 4b (V5_SPEC Appendix J with amendment A): primary stratum P, scenarios 71-82 (worlds 701-724), from stage4b/SELECTION.json, and
the FM-conditioned trust strata U and W, scenarios 91-95 (worlds 901-910), from stage4b/SELECTION_UW.json when it exists. Each world's
other side is every other library polymorph of the formula (J.8, scenarios.other_branches). The library holds every polymorph and two
distractors (stage4b/DISTRACTORS.json), sorted by name. install() adds the scenarios to scenarios.SCEN/TUNE/WORLD_SCEN."""
import json, os
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from . import scenarios as SC
from . import stage2 as S2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = os.path.join(ROOT, 'stage4b', 'SELECTION.json')
SEL_UW = os.path.join(ROOT, 'stage4b', 'SELECTION_UW.json')
DIS = os.path.join(ROOT, 'stage4b', 'DISTRACTORS.json')
MANUAL = os.path.join(ROOT, 'stage4b', 'MANUAL.md')
CACHE = os.path.join(ROOT, 'stage4b', 'library_structures.json')
CLAIM = {'R': 'The crystalline phase in this sample is the lowest-energy polymorph of {f}.',
         'H': 'The crystalline phase in this sample lies within 50 meV/atom of the convex hull.',
         'G': 'The crystalline phase in this sample has a PBE band gap above 0.5 eV.'}
P_ORDER = ('R', 'H', 'G')


def _mp_structure(mid, _cache={}):
    import gzip
    if not _cache:
        d = json.load(gzip.open(os.path.join(ROOT, 'data', 'stage4', '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
        _cache.update({v: d['entry'][k]['structure'] for k, v in d['material_id'].items()})
    return SpacegroupAnalyzer(Structure.from_dict(_cache[mid]), symprec=1e-3).get_conventional_standard_structure()


def chosen():
    """P in J.5 order (R, H, G; within a type in selection order), then U and W (selection order, U first)."""
    P = json.load(open(SEL))['chosen']
    out = [dict(c, stratum='P') for t in P_ORDER for c in P if c['type'] == t]
    if os.path.exists(SEL_UW):
        UW = json.load(open(SEL_UW))['chosen']
        out += [c for c in UW if c['stratum'] == 'U'] + [c for c in UW if c['stratum'] == 'W']
    return out


def structures(ids):
    cache = {k: Structure.from_dict(v) for k, v in json.load(open(CACHE)).items()} if os.path.exists(CACHE) else {}
    new = [i for i in ids if i not in cache]
    for i in new: cache[i] = S2.wbm(i) if i.startswith('wbm-') else _mp_structure(i)
    if new: json.dump({k: v.as_dict() for k, v in cache.items()}, open(CACHE, 'w'))
    return cache


def label(st):
    return f'{st.composition.reduced_formula} ({SpacegroupAnalyzer(st, symprec=0.1).get_space_group_symbol()})'


def setup():
    C = chosen(); dis = json.load(open(DIS)) if os.path.exists(DIS) else {}
    ids = [e['id'] for c in C for e in c['entries']] + [d['id'] for c in C for d in dis.get(c['formula'], {}).get('distractors', [])]
    st = structures(ids); out = {}
    nP = sum(1 for c in C if c['stratum'] == 'P')
    for i, c in enumerate(C):
        j = i if c['stratum'] == 'P' else i - nP
        s = (71 if c['stratum'] == 'P' else 91) + j; base = 700 if c['stratum'] == 'P' else 900
        wa, wb = base + 2 * j + 1, base + 2 * j + 2; f = c['formula']
        names = {}
        for mid in [e['id'] for e in c['entries']] + [d['id'] for d in dis.get(f, {}).get('distractors', [])]:
            nm = label(st[mid])
            if nm in names.values(): nm = f'{nm} [{mid}]'
            names[mid] = S2.register_structure(nm, st[mid])
        polys = [names[e['id']] for e in c['entries']]
        br = {n: SC.fixed([(n, {}, 1.0)], label=n) for n in polys}
        na, nb = names[c['ids'][0]], names[c['ids'][1]]
        system = '-'.join(sorted(e.symbol for e in Composition(f).elements))
        desc = (f'{f} powder from a new synthesis route, single crystalline phase. The library lists every known {f} polymorph '
                f'({len(polys)}; the candidates for this sample\'s phase) and two other phases of the {system} system, with their structures.')
        tk = c.get('taken') or c.get('ident_kind')
        out[s] = dict(name=f'S4b-{s} {c["type"]} {f}', kind=tk, claim_type=c['type'], stratum=c['stratum'], composition=f,
                      claim=CLAIM[c['type']].format(f=f), description=desc, library=sorted(names.values()), polymorphs=polys,
                      names_by_id=names, ids=c['ids'], classes=c.get('classes', []),
                      worlds={wa: dict(holds=True, phases=[[(na, {}, 1.0)]], wbm_id=c['ids'][0], other_branches=[br[n] for n in polys if n != na]),
                              wb: dict(holds=False, phases=[[(nb, {}, 1.0)]], wbm_id=c['ids'][1], other_branches=[br[n] for n in polys if n != nb])},
                      claim_side=[br[na]], other_side=[br[nb]], manual_file=MANUAL, stage='4b', pick=c,
                      N=float(c.get('N') or 1000.0))
    return out


def install(tune=None):
    S4 = setup()
    SC.SCEN.update(S4)
    for s, d in S4.items():
        SC.TUNE[s] = dict(L=100.0, N=d['N'], bg=20.0, Nn=1000.0, bgn=50.0)
    o = os.environ.get('V5_S4B_TUNE')
    if o: [SC.TUNE[int(s)].update(v) for s, v in json.loads(o).items()]
    if tune: [SC.TUNE[s].update(v) for s, v in tune.items()]
    SC.WORLD_SCEN.update({w: s for s, d in S4.items() for w in d['worlds']})
    return S4


def worlds(stratum=None):
    return sorted(w for s, d in SC.SCEN.items() if d.get('stage') == '4b' and (stratum is None or d['stratum'] == stratum) for w in d['worlds'])
