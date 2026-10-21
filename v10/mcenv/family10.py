"""v10 families (V10-3): install the R, H and T worlds of a v10 world directory (select/build10.py output; default v10/bench, or
V10_WORLDS) with v7's installers: R by bench6.setup (B1 worlds, claim R), H by family7.setup_H, T by family7.setup_T. Then, per
scenario, v10's settings: seed_scen from the world file ('v10|FAM|formula': hidden displacement and zero offset, and the noise key),
family, budget (R and H 180, T 240) and the count scale N with neutron_scale(N) at the frozen κ (v10/KAPPA.json).
Hold worlds are installed (v7's installers make them) but v10 units are twins only (hard rule 5)."""
import json, os
from . import scenarios as SC
from . import bench6 as B6
from . import family7 as F7

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WDIR = os.environ.get('V10_WORLDS', os.path.join(ROOT, 'bench'))
FAMILY = {}          # scen -> 'R' | 'H' | 'T'
RECORDS = {}         # scen -> the world file record


def _path(fam): return os.path.join(WDIR, f'WORLDS_{fam}10.json')


def setup():
    cache = os.path.join(WDIR, 'library_structures10.json'); out = {}
    if os.path.exists(_path('R')):
        old = (B6.WORLDS, B6.CACHE)
        B6.WORLDS, B6.CACHE = _path('R'), cache
        try: R = B6.setup()
        finally: B6.WORLDS, B6.CACHE = old
        out.update({s: ('R', d) for s, d in R.items()})
    if os.path.exists(_path('H')): out.update({s: ('H', d) for s, d in F7.setup_H(_path('H'), cache).items()})
    if os.path.exists(_path('T')): out.update({s: ('T', d) for s, d in F7.setup_T(_path('T'), cache).items()})
    recs = {}
    for fam in 'RHT':
        if os.path.exists(_path(fam)): recs.update({w['scen']: w for w in json.load(open(_path(fam)))['worlds']})
    S = {}
    for s, (fam, d) in out.items():
        W = recs[s]
        d.update(seed_scen=W['seed_scen'], family=fam, v10=True, slot=W['slot'], role=W['role'], flag=W['flag'],
                 budget=240.0 if fam == 'T' else 180.0)
        S[s] = d; FAMILY[s] = fam; RECORDS[s] = W
    return S


def install():
    S = setup()
    SC.SCEN.update(S)
    for s, d in S.items():
        Nn, bgn = SC.neutron_scale(d['N'])
        SC.TUNE[s] = dict(L=100.0, N=d['N'], bg=20.0, Nn=Nn, bgn=bgn)
    SC.WORLD_SCEN.update({w: s for s, d in S.items() for w in d['worlds']})
    SC.WORLD_SCEN.update({tw: v['scen'] for tw, v in F7.T_SCEN.items() if v['scen'] in S})
    for s, d in S.items():
        if FAMILY[s] == 'R': d['count_text'] = B6.COUNT_TEXT
    return S
