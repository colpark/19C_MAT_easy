"""v5 instrument model (V5_SPEC 1.2): phase peak tables, pseudo-Voigt profiles, Caglioti widths, Scherrer size, displacement, zero offset.

Intensities come from pymatgen XRDCalculator (Cu Ka1) and NDCalculator (1.5406 A). A peak table is computed once per phase and
intensity-relevant parameter (alloy x rounded to 0.01; order parameter S through I(S) = I(0) + S^2 (I(1) - I(0)), exact for L1_2),
at a reference geometry whose hkl families are distinct; positions are recomputed for the actual lattice from each family's hkl.
Per-phase intensity per unit weight fraction = raw |F|^2 LP m / (V^2 rho) (absorption contrast ignored, stated in the manual)."""
import functools, math, os, pickle, warnings
import numpy as np
import numba
from pymatgen.analysis.diffraction.xrd import XRDCalculator
from pymatgen.analysis.diffraction.neutron import NDCalculator
from pymatgen.core import Lattice
from . import structures as S

warnings.filterwarnings('ignore')
LAM = 1.5406
R_MM = 240.0
TT_MIN, TT_MAX = 5.0, 150.0
# Caglioti (deg^2): FWHM^2 = U tan^2(th) + V tan(th) + W
CAGLIOTI = {'standard': (0.012, -0.002, 0.0085), 'high_resolution': (0.0011, -0.00018, 0.00077), 'neutron': (0.06, -0.03, 0.09)}
FLUX = {'standard': 1.0, 'high_resolution': 0.25}
ETA = 0.5
SI_STD_WEIGHT = 0.20          # weight fraction of the Si internal standard in the measured mixture
NEUTRON = dict(start=5.0, stop=150.0, step=0.05, cost_min=120.0)
NEUTRON['n'] = int(round((NEUTRON['stop'] - NEUTRON['start']) / NEUTRON['step'])) + 1
NEUTRON['t'] = (NEUTRON['cost_min'] - 5.0) * 60.0 / NEUTRON['n']


# ---------------------------------------------------------------- phases
class Phase:
    """name: library name; build(params, ref) -> Structure; ref=True returns the reference geometry for the hkl table.
    iparams: names of params that change intensities (rounded for caching); lattice(params) -> pymatgen Lattice of the actual sample."""
    def __init__(self, name, build, defaults=None, iparams=(), order_param=None, lat=None):
        self.name, self._build, self.defaults, self.iparams, self.order_param = name, build, dict(defaults or {}), tuple(iparams), order_param
        self._lat = lat

    def lattice(self, p):
        """actual lattice, computed analytically (no structure build in the hot path)."""
        p = self.params(p)
        if self._lat: return self._lat(p)
        ref = _ref_lattice(self.name)
        return ref.__class__(ref.matrix * p.get('lattice_scale', 1.0))

    def params(self, p):
        q = dict(self.defaults); q.update({k: v for k, v in (p or {}).items() if k in self.defaults}); return q

    def structure(self, p, ref=False): return self._build(self.params(p), ref)


def _ls(st, scale):
    if scale != 1.0: st = st.copy(); st.scale_lattice(st.volume * scale ** 3)
    return st


PHASES = {}
def _reg(ph): PHASES[ph.name] = ph; return ph

_reg(Phase('anatase', lambda p, ref: _ls(S.anatase(), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('rutile', lambda p, ref: _ls(S.rutile(), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('brookite', lambda p, ref: _ls(S.brookite(), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('Si', lambda p, ref: _ls(S.diamond('Si', 5.43114), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('Ge', lambda p, ref: _ls(S.diamond('Ge', 5.6579), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('Si1-xGex', lambda p, ref: _ls(S.sige(round(p['x'], 2)), p['lattice_scale']) if not ref else S.sige(round(p['x'], 2)),
           {'x': 0.5, 'lattice_scale': 1.0}, iparams=('x',), lat=lambda p: Lattice.cubic(((1 - p['x']) * 5.43114 + p['x'] * 5.6579) * p['lattice_scale'])))
_reg(Phase('BaTiO3 cubic', lambda p, ref: S.batio3(1.0, p['a_pc']), {'a_pc': 4.005}, lat=lambda p: Lattice.cubic(p['a_pc'])))
_reg(Phase('BaTiO3 tetragonal', lambda p, ref: S.batio3(1.01 if ref else p['c_over_a'], p['a_pc']), {'c_over_a': 1.0025, 'a_pc': 4.005},
           lat=lambda p: Lattice.tetragonal(p['a_pc'] * p['c_over_a'] ** (-1 / 3), p['a_pc'] * p['c_over_a'] ** (2 / 3))))
_reg(Phase('BaCO3', lambda p, ref: _ls(_witherite(), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('Mo', lambda p, ref: _ls(S.bcc('Mo', 3.1470), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('W', lambda p, ref: _ls(S.bcc('W', 3.1652), p['lattice_scale']), {'lattice_scale': 1.0}))
_reg(Phase('Mo1-xWx', lambda p, ref: _ls(S.mow(round(p['x'], 2)), p['lattice_scale']) if not ref else S.mow(round(p['x'], 2)),
           {'x': 0.5, 'lattice_scale': 1.0}, iparams=('x',), lat=lambda p: Lattice.cubic(((1 - p['x']) * 3.1470 + p['x'] * 3.1652) * p['lattice_scale'])))
_reg(Phase('Cu2ZnSnS4 kesterite', lambda p, ref: S.czts('kesterite'), {}))
_reg(Phase('Cu2ZnSnS4 stannite', lambda p, ref: S.czts('stannite'), {}))
_reg(Phase('ZnS sphalerite', lambda p, ref: S.zns(), {}))
_reg(Phase('Cu2SnS3', lambda p, ref: S.cu2sns3(), {}))
_reg(Phase('Ni3Al', lambda p, ref: S.ni3al(p['S']), {'S': 1.0}, order_param='S'))
_reg(Phase('NiAl', lambda p, ref: S.nial(), {}))
_reg(Phase('Ni', lambda p, ref: S.fcc('Ni', 3.524), {}))
_reg(Phase('ZrO2 monoclinic', lambda p, ref: S.zro2_m(), {}))
_reg(Phase('ZrO2 tetragonal', lambda p, ref: S.zro2_t(), {}))
_reg(Phase('ZrO2 cubic', lambda p, ref: S.zro2_c(), {}))
_reg(Phase('Si standard', lambda p, ref: S.diamond('Si', 5.43102), {}))


@functools.lru_cache(maxsize=None)
def _ref_lattice(name): return PHASES[name].structure({}).lattice


def _witherite():
    from pymatgen.core import Lattice, Structure
    return Structure.from_spacegroup('Pmcn', Lattice.orthorhombic(5.3126, 8.8958, 6.4284), ['Ba', 'C', 'O', 'O'],
                                     [[0.25, 0.4167, 0.7548], [0.25, 0.7553, -0.0818], [0.25, 0.9002, -0.0929], [0.4594, 0.6807, -0.0859]])


TABLE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scenarios', 'peak_tables.pkl')
_TABLES = None


def _tables():
    global _TABLES
    if _TABLES is None:
        _TABLES = pickle.load(open(TABLE_FILE, 'rb')) if os.path.exists(TABLE_FILE) else {}
    return _TABLES


def save_tables():
    """freeze the computed peak tables (frozen at V5-2 with their sha256; every host then uses identical tables)."""
    pickle.dump(_tables(), open(TABLE_FILE, 'wb'), protocol=4)


def _table(name, ikey, radiation):
    T = _tables(); k = (name, ikey, radiation)
    if k not in T: T[k] = _table_compute(name, ikey, radiation)
    return T[k]


def _table_compute(name, ikey, radiation):
    """hkl table at the reference geometry: (hkl array (n,3), intensity per unit weight fraction (n,))."""
    ph = PHASES[name]; p = dict(ikey)
    st = ph.structure(p, ref=True)
    calc = XRDCalculator(LAM) if radiation == 'xray' else NDCalculator(LAM)
    pat = calc.get_pattern(st, scaled=False, two_theta_range=(1.0, 179.0))
    hkls, ints = [], []
    for y, fam in zip(pat.y, pat.hkls):
        m = np.array([f['multiplicity'] for f in fam], float)
        for f, mi in zip(fam, m):                      # split merged families by multiplicity (exact when they share |F|^2)
            hk = f['hkl']; hk = hk if len(hk) == 3 else (hk[0], hk[1], hk[3])
            hkls.append(hk); ints.append(y * mi / m.sum())
    rho = st.density
    return np.array(hkls, float), np.array(ints) / (st.volume ** 2 * rho)


def peak_table(name, params, radiation='xray'):
    """(two_theta_deg, intensity per unit weight fraction) for the actual lattice."""
    ph = PHASES[name]; p = ph.params(params)
    ikey = tuple(sorted((k, round(p[k], 2)) for k in ph.iparams))
    if ph.order_param:
        sv = p[ph.order_param]
        h0, i0 = _table(name, tuple(sorted(dict(ikey, **{ph.order_param: 0.0}).items())), radiation)
        h1, i1 = _table(name, tuple(sorted(dict(ikey, **{ph.order_param: 1.0}).items())), radiation)
        hk, ints = _merge_order(h0, i0, h1, i1, sv)
    else:
        hk, ints = _table(name, ikey, radiation)
    d = _dhkl(ph.lattice(p), hk)
    s = LAM / (2 * d); ok = s < 1
    return np.degrees(2 * np.arcsin(s[ok])), ints[ok]


def _merge_order(h0, i0, h1, i1, sv):
    key = lambda h: tuple(int(round(x)) for x in h)
    d0 = {key(h): v for h, v in zip(h0, i0)}
    hk = h1; out = np.array([d0.get(key(h), 0.0) + sv ** 2 * (v - d0.get(key(h), 0.0)) for h, v in zip(h1, i1)])
    return hk, out


def _dhkl(lat, hk):
    g = lat.reciprocal_lattice_crystallographic.matrix
    q = hk @ g
    return 1.0 / np.linalg.norm(q, axis=1)


# ---------------------------------------------------------------- profiles
def fwhm_instr(tt, optics):
    U, V, W = CAGLIOTI[optics]; t = np.tan(np.radians(tt / 2))
    return np.sqrt(np.maximum(U * t * t + V * t + W, 1e-8))


def fwhm_size(tt, L_nm):
    return np.degrees(0.9 * LAM / 10.0 / (L_nm * np.cos(np.radians(tt / 2))))


def peak_shift(tt, disp_mm, zero_deg):
    return zero_deg - np.degrees(2 * disp_mm * np.cos(np.radians(tt / 2)) / R_MM)


@numba.njit(cache=True, fastmath=False)
def _pv_kernel(start, step, n, c, a, H, eta, trunc):
    out = np.zeros(n)
    k = 2.0 * math.sqrt(math.log(2.0) / math.pi); ln2 = math.log(2.0)
    for j in range(c.shape[0]):
        h = H[j]; w = trunc * h
        i0 = int(math.ceil((c[j] - w - start) / step)); i1 = int(math.floor((c[j] + w - start) / step)) + 1
        if i0 < 0: i0 = 0
        if i1 > n: i1 = n
        if i1 <= i0: continue
        g0 = a[j] * (1.0 - eta) * k / h; l0 = a[j] * eta * 2.0 / (math.pi * h)
        for i in range(i0, i1):
            dx = start + step * i - c[j]
            z = 4.0 * dx * dx / (h * h)
            out[i] += g0 * math.exp(-ln2 * z) + l0 / (1.0 + z)
    return out


TRUNC = 25.0


def profile_sum(x, centers, heights_area, fwhm):
    """sum of area-normalized pseudo-Voigts (eta 0.5) on the uniform grid x; each peak truncated at 25 FWHM."""
    if len(centers) == 0 or len(x) == 0: return np.zeros(len(x))
    step = (x[-1] - x[0]) / (len(x) - 1) if len(x) > 1 else 1.0
    return _pv_kernel(float(x[0]), float(step), len(x), np.ascontiguousarray(centers, float), np.ascontiguousarray(heights_area, float),
                      np.ascontiguousarray(fwhm, float), ETA, TRUNC)


def grid(start, step, n): return start + step * np.arange(n)


def signal(x, phases, radiation='xray', optics='standard', L_nm=100.0, disp_mm=0.0, zero_deg=0.0, si_standard=False):
    """Noise-free signal per second per unit scale (no background, no flux): sum over phases of w * intensity * profile.
    phases: list of (name, params, weight). With si_standard the sample phases are diluted to 1 - SI_STD_WEIGHT."""
    comp = list(phases)
    if si_standard and radiation == 'xray':
        comp = [(n, p, w * (1 - SI_STD_WEIGHT)) for n, p, w in comp] + [('Si standard', {}, SI_STD_WEIGHT)]
    cs, hs = [], []
    for n, p, w in comp:
        if w <= 0: continue
        tt, I = peak_table(n, p, radiation); cs.append(tt); hs.append(I * w)
    if not cs: return np.zeros_like(x)
    c = np.concatenate(cs); h = np.concatenate(hs)
    if radiation == 'xray': c = c + peak_shift(c, disp_mm, zero_deg)
    opt = 'neutron' if radiation == 'neutron' else optics
    H = np.sqrt(fwhm_instr(c, opt) ** 2 + fwhm_size(c, L_nm) ** 2)
    return profile_sum(x, c, h, H)


def cost_min(n_points, t_step): return n_points * t_step / 60.0 + 5.0
