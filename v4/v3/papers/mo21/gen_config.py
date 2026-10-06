"""gen_config.py (mo21): paper-specific inputs of generate.py (frozen with it). Everything here is a design record, a display string or a
binding; no value enters a key from this file except the D series values."""
import laws as L

PAPER = 'mo21'; DOI = '10.1016/j.jma.2020.11.023'; JOURNAL = 'Journal of Magnesium and Alloys'; YEAR = 2022
RELEASE_ELIGIBLE = False   # CC BY-NC-ND: paper 1 items stay private
COMP = 'Mg3.2Bi1.4Sb0.6−xSex'; SAMPLES = [0.0, 0.005, 0.01, 0.02, 0.04]; SE = [0.005, 0.01, 0.02, 0.04]
SERIES_TEXT = 'five {comp} samples (x = 0, 0.005, 0.01, 0.02, 0.04)'
GRID = [300, 350, 400, 450, 500, 550, 600]; COND = 'T'; COND_UNIT = 'K'; COND_TEXT = 'temperature'
CONTAMINATION_MARKERS = ['Mo21', '10.1016/j.jma.2020.11.023']
DESC = {   # neutral panel descriptions (written by the builder, not quoted)
    'F4a': 'Hall carrier concentration n_H versus temperature', 'F4b': 'Hall mobility μ_H versus temperature',
    'F5a': 'electrical resistivity ρ versus temperature', 'F5b': 'Seebeck coefficient S versus temperature',
    'F5c': 'power factor PF versus temperature', 'F5d': 'total thermal conductivity κ versus temperature',
    'F5e': 'electronic thermal conductivity κ_e versus temperature', 'F5f': 'κ_L + κ_b (lattice plus bipolar thermal conductivity) versus temperature',
    'F6a': 'figure of merit ZT versus temperature (with two literature curves for comparison)',
    'F3a': 'SEM image of the fracture surface of the x = 0.01 sample', 'F3b': 'SEM image of the fracture surface of the x = 0.01 sample (higher magnification)',
    'F3c': 'EDS element map of the x = 0.01 sample', 'F3d': 'EDS element map of the x = 0.01 sample', 'F3e': 'EDS element map of the x = 0.01 sample',
    'F3f': 'EDS element map of the x = 0.01 sample'}
PANEL_NOTES = {'F4b': ' Note: the Hall mobility panel prints the unit 10^19 cm^-3 on its axis; that is a slip in the figure, the mobility is in cm^2 V^-1 s^-1.'}
Q_PANEL = {'n_H': 'F4a', 'mu_H': 'F4b', 'rho': 'F5a', 'S': 'F5b', 'PF': 'F5c', 'kappa': 'F5d', 'kappa_e': 'F5e', 'kappa_Lb': 'F5f', 'ZT': 'F6a'}
DATA_PANELS = ['F4a', 'F4b', 'F5a', 'F5b', 'F5c', 'F5d', 'F5e', 'F5f', 'F6a']
MAGNITUDE = {'S'}   # quantities asked and keyed as magnitudes
# panel sets that decide a quantity (directly or through a law of laws.py; v3.2 adds rho = S^2/PF and its consequences)
DECIDING = {'n_H': [{'F4a'}, {'F5a', 'F4b'}, {'F5b', 'F5c', 'F4b'}], 'mu_H': [{'F4b'}, {'F4a', 'F5a'}, {'F4a', 'F5b', 'F5c'}],
            'rho': [{'F5a'}, {'F4a', 'F4b'}, {'F5b', 'F5c'}],
            'S': [{'F5b'}, {'F4a'}, {'F5c', 'F5a'}, {'F6a', 'F5a', 'F5d'}], 'PF': [{'F5c'}, {'F5a', 'F5b'}, {'F6a', 'F5d'}],
            'kappa': [{'F5d'}, {'F5e', 'F5f'}, {'F5c', 'F6a'}], 'kappa_e': [{'F5e'}, {'F5a', 'F5b'}, {'F5d', 'F5f'}, {'F5a', 'F4a'}, {'F5b', 'F5c'}],
            'kappa_Lb': [{'F5f'}, {'F5d', 'F5e'}, {'F5d', 'F5a', 'F5b'}, {'F5d', 'F5b', 'F5c'}], 'ZT': [{'F6a'}, {'F5c', 'F5d'}, {'F5a', 'F5b', 'F5d'}]}
QNAME = {'n_H': 'Hall carrier concentration', 'mu_H': 'Hall mobility', 'rho': 'electrical resistivity', 'S': 'magnitude of the Seebeck coefficient |S|',
         'PF': 'power factor', 'kappa': 'total thermal conductivity', 'kappa_e': 'electronic thermal conductivity',
         'kappa_Lb': 'sum of lattice and bipolar thermal conductivity κ_L + κ_b', 'ZT': 'figure of merit ZT'}
UFORMS = {'uW cm^-1 K^-2': [('μW cm⁻¹ K⁻²', 1.0), ('mW m⁻¹ K⁻²', 0.1)], 'uV K^-1': [('μV K⁻¹', 1.0), ('mV K⁻¹', 0.001)],
          'uOhm m': [('μΩ m', 1.0), ('mΩ cm', 0.1)], '1e19 cm^-3': [('× 10¹⁹ cm⁻³', 1.0), ('× 10²⁵ m⁻³', 1.0)],
          'cm^2 V^-1 s^-1': [('cm² V⁻¹ s⁻¹', 1.0)], 'W m^-1 K^-1': [('W m⁻¹ K⁻¹', 1.0), ('mW cm⁻¹ K⁻¹', 10.0)], '': [('', 1.0)]}
UNIT_SHOW = {'1e19 cm^-3': '10^19 cm^-3', 'cm^2 V^-1 s^-1': 'cm^2 V^-1 s^-1', 'uOhm m': 'µΩ m', 'uV K^-1': 'µV K^-1',
             'uW cm^-1 K^-2': 'µW cm^-1 K^-2', 'W m^-1 K^-1': 'W m^-1 K^-1', '': '', '1e-8 W Ohm K^-2': '10^-8 W Ω K^-2', 'm_e': 'm_e'}
T1_EXAMPLE = {'1e19 cm^-3': '1.5 10^19 cm^-3', 'cm^2 V^-1 s^-1': '95 cm^2 V^-1 s^-1', 'uOhm m': '42 µΩ m', 'uV K^-1': '120 µV K^-1',
              'uW cm^-1 K^-2': '12.5 µW cm^-1 K^-2', 'W m^-1 K^-1': '0.75 W m^-1 K^-1', '': '0.45'}
# T2 sets: target, references; prediction from reference cells for ambiguity classes only (acceptance width, never the key)
T2_SETS = [
    ('F5a', ['F4a', 'F4b'], [('n_H', 'F4a'), ('mu_H', 'F4b')], lambda c, T: L.rho_hall(c['n_H'], c['mu_H'])),
    ('F4a', ['F5a', 'F4b'], [('rho', 'F5a'), ('mu_H', 'F4b')], lambda c, T: L.rho_hall(c['rho'], c['mu_H'])),
    ('F4b', ['F4a', 'F5a'], [('n_H', 'F4a'), ('rho', 'F5a')], lambda c, T: L.rho_hall(c['n_H'], c['rho'])),
    ('F5c', ['F5a', 'F5b'], [('S', 'F5b'), ('rho', 'F5a')], lambda c, T: L.pf(c['S'], c['rho'])),
    ('F5e', ['F5a', 'F5b'], [('S', 'F5b'), ('rho', 'F5a')], lambda c, T: L.kappa_e(c['S'], c['rho'], T)),
    ('F5f', ['F5d', 'F5e'], [('kappa', 'F5d'), ('kappa_e', 'F5e')], lambda c, T: L.kappa_Lb(c['kappa'], c['kappa_e'])),
    ('F5d', ['F5e', 'F5f'], [('kappa_e', 'F5e'), ('kappa_Lb', 'F5f')], lambda c, T: c['kappa_e'] + c['kappa_Lb']),
    ('F5b', ['F4a'], [('n_H', 'F4a')], lambda c, T: -L.spb_S(c['n_H'], T)),
]
TEMPLATES = [   # v3 templates kept (<= 2): F3 shows only x = 0.01
    {'id': 'i_se_uniform_x004', 'panels': ['F3c', 'F3d', 'F3e', 'F3f'], 'claim': 'Se is distributed uniformly through the x = 0.04 sample.',
     'why': 'the EDS maps show only the x = 0.01 sample (sem_sample span)'},
    {'id': 'i_grain_x002', 'panels': ['F3a', 'F3b'], 'claim': 'The x = 0.02 sample has coarser grains than the x = 0.01 sample.',
     'why': 'SEM images show only the x = 0.01 sample (sem_sample span)'},
]
MATRIX_SPECS = 7
# recompute audits: binding id -> (A panel audited, M input panels, display formula, A quantity name)
RECOMPUTE = {'mo21_mu_recompute': ('F4b', ['F4a', 'F5a'], 'μ_H = 1/(e n_H ρ)', 'Hall mobility μ_H'),
             'mo21_pf': ('F5c', ['F5b', 'F5a'], 'S²/ρ', 'power factor PF'),
             'mo21_kappa_e': ('F5e', ['F5b', 'F5a'], 'L T/ρ with L = 1.5 + exp(−|S|/116) (10^-8 W Ω K^-2)', 'electronic thermal conductivity κ_e'),
             'mo21_kappa_Lb': ('F5f', ['F5d', 'F5e'], 'κ − κ_e', 'κ_L + κ_b'),
             'mo21_zt': ('F6a', ['F5b', 'F5a', 'F5d'], 'S² T/(ρ κ)', 'figure of merit ZT')}
# T7 (fit laws): binding id -> fitted parameter (name, unit, bounds), the law with the parameter free, input/target panels
T7 = {'mo21_spb_S': {'param': 'm_star', 'pname': 'density-of-states effective mass m*', 'punit': 'm_e', 'bounds': (0.3, 5.0),
                     'f': lambda v, T, p: L.spb_S(v['n_H'], T, p), 'inputs': [('n_H', 'F4a')], 'target': ('S', 'F5b'), 'target_abs': True,
                     'model_err': L.SPB_ERR, 'law_text': 'a single parabolic band model with acoustic phonon scattering (r = −1/2) and Hall factor r_H from the same model'}}
SIGNATURE_PAIRS = []   # T5/T6: none for paper 1 (no cause/outcome panels for rival mechanisms)
IMAGE_SETS = []        # T2 image variant: none for paper 1 (micrographs of one sample only)
