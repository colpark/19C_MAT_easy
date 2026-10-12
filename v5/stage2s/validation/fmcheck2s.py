import json, os, sys, glob
import numpy as np
from pymatgen.core import Structure
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
from mcenv import stage2s as ST, scenarios as SC, physics as P, stage2 as S2
ST.install(cost=False)
state = sys.argv[1]; out = []
reg = json.load(open(os.path.join(state, 'truth', 'episodes.json')))
seen = set()
for tok, r in reg.items():
    if not r['batch'].endswith('-plan'): continue
    s = SC.WORLD_SCEN[r['world']]; d = SC.SCEN[s]
    stp = os.path.join(state, 'episodes', tok, 'state.json')
    if not os.path.exists(stp): continue
    st = json.load(open(stp)).get('structures', {})
    truths = []
    for side in ('claim_side', 'other_side'):
        for br in d[side]:
            for g in br.groups(br.lo if br.dim else []):
                for n, p, w in g:
                    t = P.PHASES[n].structure(dict(p, S=1.0) if P.PHASES[n].order_param else p)
                    if t.is_ordered: truths.append((n, t))
    for sid, rec in st.items():
        if not rec['origin'].startswith('relax'): continue
        x = Structure.from_dict(rec['structure'])
        for n, t in truths:
            if t.composition.reduced_formula == x.composition.reduced_formula:
                try: sx = SpacegroupAnalyzer(x, 1e-2).get_space_group_symbol(); stt = SpacegroupAnalyzer(t, 1e-2).get_space_group_symbol()
                except Exception: continue
                if len(x) != len(t) and sx != stt: continue
                key = (s, r['arm'], n)
                if key in seen: continue
                seen.add(key)
                vol = (x.volume / len(x)) / (t.volume / len(t)) - 1
                abx = sorted(x.lattice.abc); abt = sorted(t.lattice.abc)
                out.append(dict(scen=s, arm=r['arm'], truth=n, sg_relaxed=sx, sg_truth=stt, vol_per_atom_err=round(vol, 4),
                                lattice_err_cuberoot=round((1 + vol) ** (1 / 3) - 1, 4),
                                abc_relaxed=[round(v, 4) for v in abx], abc_truth=[round(v, 4) for v in abt]))
for o in sorted(out, key=lambda o: (o['scen'], o['arm'])): print(json.dumps(o))
