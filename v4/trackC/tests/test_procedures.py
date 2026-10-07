"""Fast unit tests for the Track C procedures (synthetic and published reference values only)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import msd, arrhenius, nernst_einstein as ne, allen_dynes as ad, synth_md as sm


def test_msd_recovers_D():
    tr = sm.trajectory(3e-5, n_li=48, n_host=24, t_ps=150, dt_ps=0.1, seed=3)
    r = msd.diffusion(tr['pos'], tr['cell'], 0.1, tr['mask'])
    assert abs(np.log10(r['D'] / 3e-5)) < 0.15


def test_nondiffuser_below_floor():
    tr = sm.trajectory(1e-12, n_li=24, n_host=24, t_ps=100, dt_ps=0.1, seed=4)
    assert msd.diffusion(tr['pos'], tr['cell'], 0.1, tr['mask'])['D'] <= 1e-9


def test_arrhenius_exact():
    T = np.array([1000, 750, 600, 500.0]); Ea = 0.2
    D = 1e-3 * np.exp(-Ea / (arrhenius.KB_EV * T))
    assert abs(arrhenius.fit(T, D)['Ea_eV'] - Ea) < 1e-9


def test_nernst_einstein_hand():
    hand = 32 * (1.602176634e-19) ** 2 * 1e-9 / (1e-27 * 1.380649e-23 * 600) * 10
    assert abs(ne.sigma_mS_cm(32, 1000.0, 1e-5, 600) / hand - 1) < 1e-12


def test_allen_dynes_einstein_peak():
    w = np.linspace(0.01, 100, 200001); a = 1.2 * 30 / 2 * np.exp(-0.5 * ((w - 30) / 0.3) ** 2) / (0.3 * np.sqrt(2 * np.pi))
    m = ad.moments(w, a)
    assert abs(m['lambda'] - 1.2) < 0.01 and abs(m['omega_log'] - 30) < 0.3


def test_mcmillan_reference():
    # eq. 7 by hand: lambda 1, omega_log 300 K, mu* 0.09
    hand = 300 / 1.2 * np.exp(-1.04 * 2 / (1 - 0.09 * 1.62))
    assert abs(ad.tc_mcmillan_ad(1.0, 300.0, 0.09) - hand) < 1e-9


def test_theta_jvasp19821():
    """jarvis-tools' own reference value (its test_tensor.py), offline from the cached 2025 parent."""
    import reconstruct_jarvis as RJ
    par = RJ.load_parent('dft_3d')
    t = RJ.theta_debye(par['JVASP-19821'])
    assert round(t, 2) == round(1047.547632064132, 2)
