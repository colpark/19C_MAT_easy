"""Stage 4 (V5_SPEC Appendix I): eight scenarios 61-68 (worlds 601-616) from stage4/SELECTION.json and stage4/DISTRACTORS.json (WBM and
MP DFT structures). R (61-65): "the crystalline phase is the lowest-energy polymorph of <formula>"; H (66-68): "within 50 meV/atom of the
convex hull". World 600 + 2i - 1 holds the claim-true polymorph, 600 + 2i the other. The library holds the two polymorphs and two
distractors with their structures, sorted by name (no order cue). install() adds the scenarios to scenarios.SCEN/TUNE/WORLD_SCEN."""
import json, os
from pymatgen.core import Composition, Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from . import scenarios as SC
from . import stage2 as S2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEL = os.path.join(ROOT, 'stage4', 'SELECTION.json')
DIS = os.path.join(ROOT, 'stage4', 'DISTRACTORS.json')
MANUAL = os.path.join(ROOT, 'stage4', 'MANUAL.md')
SCENS = tuple(range(61, 69))
# scenario order (I.3): R quiet, R loud x 4 (selection order), H quiet, H loud x 2
# ---- frozen at V5-23 (stage4/TUNING.md): count rates; loud scenarios keep the stage 1 default N 1000
TUNE4 = {61: dict(N=2.4215), 66: dict(N=3.9857)}


def _mp_structure(mid):
    import gzip
    d = json.load(gzip.open(os.path.join(ROOT, 'data', 'stage4', '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    k = next(k for k, v in d['material_id'].items() if v == mid)
    return SpacegroupAnalyzer(Structure.from_dict(d['entry'][k]['structure']), symprec=1e-3).get_conventional_standard_structure()


_STRUCT_CACHE = os.path.join(ROOT, 'stage4', 'library_structures.json')


def structures():
    """conventional standard cells of every library structure, cached in stage4/library_structures.json (written once at V5-23)."""
    if os.path.exists(_STRUCT_CACHE):
        return {k: Structure.from_dict(v) for k, v in json.load(open(_STRUCT_CACHE)).items()}
    ch = json.load(open(SEL))['chosen']; dis = json.load(open(DIS)); out = {}
    for c in ch:
        for i in c['ids']: out[i] = S2.wbm(i)
        for d in dis[c['formula']]['distractors']: out[d['id']] = S2.wbm(d['id']) if d['id'].startswith('wbm-') else _mp_structure(d['id'])
    json.dump({k: v.as_dict() for k, v in out.items()}, open(_STRUCT_CACHE, 'w'))
    return out


def label(st):
    sga = SpacegroupAnalyzer(st, symprec=0.1)                # name only (the WBM prototype-label tolerance); the structure is unchanged
    sym = sga.get_space_group_symbol(); f = st.composition.reduced_formula
    return f'{f} ({sym})'


def ordered_choice():
    ch = json.load(open(SEL))['chosen']
    R = [c for c in ch if c['type'] == 'R']; H = [c for c in ch if c['type'] == 'H']
    key = lambda c: (c['taken'] != 'quiet',)                  # quiet first, then selection order (sort is stable)
    return sorted(R, key=key) + sorted(H, key=key)


def setup():
    st = structures(); dis = json.load(open(DIS)); out = {}
    for i, c in enumerate(ordered_choice()):
        s = 61 + i; wa, wb = 600 + 2 * i + 1, 600 + 2 * i + 2; f = c['formula']
        names = {}
        for mid in c['ids'] + [d['id'] for d in dis[f]['distractors']]:
            nm = label(st[mid])
            if nm in names.values(): nm = f'{nm} [{mid}]'
            names[mid] = S2.register_structure(nm, st[mid])
        na, nb = names[c['ids'][0]], names[c['ids'][1]]
        system = '-'.join(sorted(e.symbol for e in Composition(f).elements))
        if c['type'] == 'R':
            claim = f'The crystalline phase in this sample is the lowest-energy polymorph of {f}.'
        else:
            claim = 'The crystalline phase in this sample lies within 50 meV/atom of the convex hull.'
        desc = (f'{f} powder from a new synthesis route, single crystalline phase. The library lists two {f} polymorphs (the candidates for '
                f'this sample\'s phase) and two other phases of the {system} system, with their structures.')
        out[s] = dict(name=f'S4-{s} {c["type"]} {f}', kind=c['taken'], claim_type=c['type'], composition=f, claim=claim, description=desc,
                      library=sorted(names.values()), ids=c['ids'], distractor_ids=[d['id'] for d in dis[f]['distractors']],
                      names_by_id=names, polymorphs=[na, nb],
                      worlds={wa: dict(holds=True, phases=[[(na, {}, 1.0)]], wbm_id=c['ids'][0]),
                              wb: dict(holds=False, phases=[[(nb, {}, 1.0)]], wbm_id=c['ids'][1])},
                      claim_side=[SC.fixed([(na, {}, 1.0)], label='claim-true polymorph')],
                      other_side=[SC.fixed([(nb, {}, 1.0)], label='other polymorph')],
                      manual_file=MANUAL, stage='4', pick=c)
    return out


def install(tune=None):
    S4 = setup()
    SC.SCEN.update(S4)
    for s in S4:
        SC.TUNE[s] = dict(L=100.0, N=1000.0, bg=20.0, Nn=1000.0, bgn=50.0); SC.TUNE[s].update(TUNE4.get(s, {}))
    o = os.environ.get('V5_S4_TUNE')                     # tuning sweeps only
    if o: [SC.TUNE[int(s)].update(v) for s, v in json.loads(o).items()]
    if tune: [SC.TUNE[s].update(v) for s, v in tune.items()]
    SC.WORLD_SCEN.update({w: s for s, d in S4.items() for w in d['worlds']})
    return S4


def worlds(): return list(range(601, 617))
