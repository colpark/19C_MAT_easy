"""Export the frozen scenario data as plain JSON (V5-2 freeze; input to the shadow-D implementation, which never reads mcenv/).
  python -m mcenv.export_worlds   -> scenarios/WORLDS.json, scenarios/peak_tables.json"""
import json, os
import numpy as np
from . import physics as P
from . import scenarios as SC
from . import separation as SP

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scenarios')


def lattice_rule(name):
    ph = P.PHASES[name]
    if name.startswith('BaTiO3 tetragonal'): return 'tetragonal a = a_pc * c_over_a^(-1/3), c = a_pc * c_over_a^(2/3)'
    if name.startswith('BaTiO3 cubic'): return 'cubic a = a_pc'
    if name == 'Si1-xGex': return 'cubic a = ((1-x) 5.43114 + x 5.6579) * lattice_scale'
    if name == 'Mo1-xWx': return 'cubic a = ((1-x) 3.1470 + x 3.1652) * lattice_scale'
    lat = P._ref_lattice(name)
    return dict(reference_matrix=np.round(lat.matrix, 8).tolist(), scaled_by='lattice_scale' if 'lattice_scale' in ph.defaults else None)


def main():
    worlds = {}
    for w in SC.WORLDS:
        tr = SP.world_truth(w); s = SC.WORLD_SCEN[w]
        br = lambda side: [dict(label=b.label, lo=b.lo.tolist(), hi=b.hi.tolist(), groups_at_lo=b.groups(b.lo), groups_at_hi=b.groups(b.hi))
                           for b in side]
        worlds[w] = dict(scenario=s, holds=SC.SCEN[s]['worlds'][w]['holds'], truth_groups=tr['groups'], disp_mm=tr['disp_mm'],
                         zero_deg=tr['zero_deg'], L_nm=tr['L_nm'], A_xray=tr['A'], A_neutron=tr['An'], b0=tr['b0'], b1=tr['b1'],
                         bn0=tr['bn0'], bn1=tr['bn1'], other_side=br(SC.other_side(w)))
    json.dump(dict(worlds=worlds, note='other_side: the branches D minimises over; a branch with lo == hi == [] is fixed; '
                   'otherwise its parameter u enters the phase params or weights linearly as shown at lo and hi'),
              open(os.path.join(OUT, 'WORLDS.json'), 'w'), indent=1, default=float)
    tabs = {}
    for (name, ikey, rad), (hk, I) in sorted(P._tables().items(), key=lambda kv: str(kv[0])):
        tabs[f'{name}|{rad}|' + ','.join(f'{k}={v}' for k, v in ikey)] = dict(hkl=hk.astype(int).tolist(), intensity_per_weight=I.tolist())
    rules = {n: lattice_rule(n) for n in P.PHASES}
    json.dump(dict(tables=tabs, lattice=rules, note='intensity per unit weight fraction for each hkl family member; positions from the '
                   'actual lattice by Bragg (lambda 1.5406); Ni3Al: I(S) = I(S=0) + S^2 (I(S=1) - I(S=0)) per hkl; alloys: table at x rounded '
                   'to 0.01'), open(os.path.join(OUT, 'peak_tables.json'), 'w'))
    print(len(worlds), 'worlds;', len(tabs), 'tables')


if __name__ == '__main__':
    main()
