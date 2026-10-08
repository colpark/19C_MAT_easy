# dev-seed comparison (seeds 0-99) of single-pass vs incoherent inversion; E_U 0.03-0.30, d 0.1-0.6 um (kit default eg/A/R)
import sys, os, numpy as np
sys.path.insert(0, os.path.expanduser('~/Documents/harbor_htem/v4/htem'))
import synth as SY
from readers import edge as RE
SY.P = dict(SY.P, opt_Eu=(0.03, 0.30), opt_thick_um=(0.1, 0.6))
E = SY.HC / SY.OPT_GRID
for inv in ('single', 'incoherent'):
    e4, eu, cen_ok, ncen = [], [], 0, 0
    for sd in range(100):
        op, tr = SY.optical_spectra(sd)
        rng = np.random.default_rng(sd); eg = tr['Eg']
        # truth: reconstruct alpha with the same draws
        r = np.random.default_rng(sd); eg_ = r.uniform(*SY._r('opt_eg', (1.6, 3.6))); d = r.uniform(*SY._r('opt_thick_um', (0.15, 0.6)))
        A = np.exp(r.uniform(*np.log(SY._r('opt_A', (1.5e5, 6e5))))); EU = r.uniform(*SY._r('opt_Eu', (0.03, 0.08)))
        Ef = np.linspace(E.min(), E.max(), 20000)
        al = np.where(Ef > eg_, np.maximum(A * np.sqrt(np.clip(Ef - eg_, 0, None)) / Ef, A * np.sqrt(EU / 2) / eg_), A * np.sqrt(EU / 2) / eg_ * np.exp((Ef - eg_) / EU))
        k = np.flatnonzero(al >= 1e4); t04 = Ef[k[0]] if k.size else None
        res = RE.read(op, d, {'t_min': 0.01, 'edge_inversion': inv})
        if t04 is None:
            ncen += 1; cen_ok += bool(res['E04_censored'])
        elif res['E04'] is not None:
            e4.append(res['E04'] - t04)
        if res['E_U']: eu.append(res['E_U'] / EU - 1)
    e4 = np.array(e4); eu = np.array(eu)
    print(inv, 'E04 n', len(e4), 'within0.03 %.2f' % np.mean(abs(e4) <= 0.03), 'bias %.3f sd %.3f' % (e4.mean(), e4.std()), '| censor truth', ncen, 'flagged', cen_ok, '| EU n', len(eu), 'within15 %.2f' % (np.mean(abs(eu) <= 0.15) if len(eu) else 0))
