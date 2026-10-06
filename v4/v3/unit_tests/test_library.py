#!/usr/bin/env python3
"""unit tests for the v3.2 law library entries and the signature helpers (synthetic values)."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import laws as L, signatures as SG
fails = []
def check(n, c):
    print(('ok   ' if c else 'FAIL ') + n)
    if not c: fails.append(n)
check('Bragg: Si(111) 2theta 28.44 deg -> d = 0.3136 nm', abs(L.bragg_d(28.44) - 0.3136) < 2e-4)
check('Bragg: d decreases with 2theta', L.bragg_d(30) > L.bragg_d(40))
check('Scherrer: broader peak -> smaller D', L.scherrer_D(0.2, 35) > L.scherrer_D(0.4, 35))
check('Scherrer: D(0.3 deg, 35.5 deg) ~ 27.8 nm', abs(L.scherrer_D(0.3, 35.5) - 27.8) < 0.2)
check('Scherrer library entry is ranking-only with model error >= 25%', L.LIBRARY['scherrer']['mode'] == 'ranking' and L.LIBRARY['scherrer']['model_err'] >= 0.25)
check('Vegard: midpoint', abs(L.vegard(0.04, 8.40, 8.30, 0.08) - 8.35) < 1e-12)
check('mixing residue: 30/70 of residues 0.10 and 0.60 -> 0.45', abs(L.mixing_residue([0.3, 0.7], [0.1, 0.6]) - 0.45) < 1e-12)
check('Reuss <= Voigt, equal for a single phase', L.reuss([0.4, 0.6], [10, 200]) < L.voigt([0.4, 0.6], [10, 200]) and abs(L.reuss([1.0], [70]) - L.voigt([1.0], [70])) < 1e-12)
check('Hall-Petch: smaller grains -> stronger', L.hall_petch(1.0, 100, 300) > L.hall_petch(10.0, 100, 300))
check('Hall-Petch value', abs(L.hall_petch(4.0, 100, 300) - 250.0) < 1e-9)
check('porosity: rho = 0.95 rho_th -> 5%', abs(L.porosity_archimedes(0.95, 1.0) - 0.05) < 1e-12)
for k in ('bragg', 'scherrer', 'vegard', 'mixing_residue', 'voigt_reuss', 'hall_petch', 'porosity_agreement'):
    e = L.LIBRARY[k]; check(f'library entry {k} has formula, inputs, target, f, params', all(x in e for x in ('formula', 'inputs', 'target', 'f', 'params')))
check('agreement flags: bragg, scherrer, porosity', all(L.LIBRARY[k].get('agreement') for k in ('bragg', 'scherrer', 'porosity_agreement')))
a = SG.SYNTHETIC['syn_grain_growth']; b = SG.SYNTHETIC['syn_pinning']
check('signatures validate', SG.validate(SG.SYNTHETIC) == [])
check('decidable: up vs none', SG.decidable(a, b, 'grain_size(T up)'))
check('not decidable: up vs up', not SG.decidable(a, b, 'density(T up)'))
check('winner: observed up -> A', SG.winner_for(a, b, 'grain_size(T up)', 'up') == 'A')
check('winner: observed down -> neither', SG.winner_for(a, b, 'grain_size(T up)', 'down') == 'neither')
check('validate catches a bad direction', SG.validate({'x': {'mechanism': 'm', 'relation': 'r', 'source': 's', 'prior_rank': 1, 'predicts': {'o': 'sideways'}}}) != [])
print(f'\n{len(fails)} failures' if fails else '\nall passed'); sys.exit(1 if fails else 0)
