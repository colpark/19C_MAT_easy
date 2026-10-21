"""v10 recipe suite (V10-1), frozen and hashed before the pilot. A recipe is a fixed list of measurements, plus the free scan(s), that
uses the whole budget and never reads the library. Budgets: R and H 180 min; T 120 min per sample (the recipe is applied to each sample).

  R0   repeated free scan     X-ray standard, 10-70 deg at 0.04 (1501 points)
  R1   broad                  X-ray standard, 10-89.96 deg at 0.04 (2000 points)
  R2   broad high-res         X-ray high resolution, as R1
  R3   low angle              X-ray standard, 10-49.98 deg at 0.02 (2000 points)
  R3a  narrow                 X-ray standard, 10-29.98 deg at 0.02 (1000 points)
  R3b  narrow                 X-ray standard, 20-39.98 deg at 0.02 (1000 points)
  R3c  narrow                 X-ray standard, 30-49.98 deg at 0.02 (1000 points)
  R4   high angle             X-ray standard, 50-129.96 deg at 0.04 (2000 points)
  R5   neutron then broad     the neutron pattern (120 min), then R1 over what remains (R and H: 60 min; T: nothing remains)
  R6   Si standard broad      X-ray standard with the Si standard, as R1, the whole budget less the 10 min preparation

Time per step: the budget left (less the 5 min overhead of a measurement) spread over the points, rounded down to 0.01 s. If that exceeds
20 s (the instrument's maximum), the same measurement is repeated at 20 s while it fits, and once more at the time the remainder allows
(at least 0.1 s); a remainder below that is left unspent.
  fill(template, budget) -> list of measure-argument dicts; recipe(name, budget) -> list of measure-argument dicts (one sample)"""
import math

COST_OVERHEAD = 5.0
SI_PREP = 10.0
T_MAX, T_MIN = 20.0, 0.1
NEUTRON_MIN = 120.0

TEMPLATES = {
    'R0': dict(start=10.0, stop=70.0, step=0.04, optics='standard', si_standard=False),
    'R1': dict(start=10.0, stop=89.96, step=0.04, optics='standard', si_standard=False),
    'R2': dict(start=10.0, stop=89.96, step=0.04, optics='high_resolution', si_standard=False),
    'R3': dict(start=10.0, stop=49.98, step=0.02, optics='standard', si_standard=False),
    'R3a': dict(start=10.0, stop=29.98, step=0.02, optics='standard', si_standard=False),
    'R3b': dict(start=20.0, stop=39.98, step=0.02, optics='standard', si_standard=False),
    'R3c': dict(start=30.0, stop=49.98, step=0.02, optics='standard', si_standard=False),
    'R4': dict(start=50.0, stop=129.96, step=0.04, optics='standard', si_standard=False),
    'R6': dict(start=10.0, stop=89.96, step=0.04, optics='standard', si_standard=True),
}
NAMES = ['R0', 'R1', 'R2', 'R3', 'R3a', 'R3b', 'R3c', 'R4', 'R5', 'R6']


def n_points(tp): return int(math.floor((tp['stop'] - tp['start']) / tp['step'] + 1e-9)) + 1


def cost(tp, t): return n_points(tp) * t / 60.0 + COST_OVERHEAD


def fill(tp, budget):
    """measure arguments that spend `budget` minutes on template tp (Si preparation not included here)."""
    n = n_points(tp); out = []; left = float(budget)
    while True:
        t = math.floor(max(0.0, (left - COST_OVERHEAD) * 60.0 / n) * 100) / 100
        if t < T_MIN: break
        t = min(T_MAX, t)
        out.append(dict(radiation='xray', start=tp['start'], stop=tp['stop'], step=tp['step'], time_per_step=t, optics=tp['optics'],
                        si_standard=tp['si_standard']))
        left -= cost(tp, t)
        if t < T_MAX: break
    return out


def recipe(name, budget):
    """the measurements of recipe `name` for one sample with `budget` minutes (the free scan is not included)."""
    if name == 'R5':
        if budget < NEUTRON_MIN: return []
        return [dict(radiation='neutron')] + fill(TEMPLATES['R1'], budget - NEUTRON_MIN)
    tp = TEMPLATES[name]
    if tp['si_standard']: return fill(tp, budget - SI_PREP)
    return fill(tp, budget)
