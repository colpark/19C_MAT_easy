"""Truth and library structures for v5 (fallback V5-E1: pymatgen-built from published parameters; sources in SOURCES)."""
from pymatgen.core import Lattice, Structure

SOURCES = {
    'anatase': 'Horn, Schwerdtfeger, Meagher, Z. Kristallogr. 136 (1972) 273: I4_1/amd a 3.7845 c 9.5143, O z 0.2081 (origin 1)',
    'rutile': 'Abrahams, Bernstein, J. Chem. Phys. 55 (1971) 3206: P4_2/mnm a 4.5937 c 2.9587, O x 0.3048',
    'brookite': 'Meagher, Lager, Can. Mineral. 17 (1979) 77: Pbca a 9.184 b 5.447 c 5.145',
    'Si': 'NIST SRM 640c a 5.43114 (Fd-3m)', 'Ge': 'a 5.6579 (Cooper 1962)',
    'BaTiO3': 'pseudo-cubic fine-grained ceramic, a 4.005; cubic Pm-3m and P4mm at the same volume with ideal fractional positions (builder choice)',
    'Mo': 'a 3.1470 (Im-3m)', 'W': 'a 3.1652 (Im-3m); mismatch 0.578 %',
    'CZTS': 'Schorr, Sol. Energy Mater. Sol. Cells 95 (2011) 1482: kesterite I-4 a 5.427 c 10.871, S (0.756, 0.757, 0.872); stannite on the same lattice and anion positions',
    'Ni3Al': 'a 3.5720 (L1_2 Pm-3m)', 'NiAl': 'a 2.887 (B2)', 'Ni': 'a 3.524 (Fm-3m)',
    'ZrO2_m': 'Howard, Hill, Reichert, Acta Cryst. B44 (1988) 116: P2_1/c a 5.1507 b 5.2028 c 5.3156 beta 99.194',
    'ZrO2_t': 'Howard et al. (1988): P4_2/nmc a 3.5984 c 5.1520, O z 0.2044 (origin 1)',
    'ZrO2_c': 'fluorite Fm-3m a 5.09',
    'ZnS': 'sphalerite F-43m a 5.4093', 'Cu2SnS3': 'cubic disordered F-43m a 5.43 (Cu2/3 Sn1/3 cation site)',
}

def anatase(): return Structure.from_spacegroup(141, Lattice.tetragonal(3.7845, 9.5143), ['Ti', 'O'], [[0, 0, 0], [0, 0, 0.2081]])
def rutile(): return Structure.from_spacegroup('P4_2/mnm', Lattice.tetragonal(4.5937, 2.9587), ['Ti', 'O'], [[0, 0, 0], [0.3048, 0.3048, 0]])
def brookite(): return Structure.from_spacegroup('Pbca', Lattice.orthorhombic(9.184, 5.447, 5.145), ['Ti', 'O', 'O'],
                                                  [[0.1289, 0.0972, 0.8628], [0.0095, 0.1491, 0.1835], [0.2314, 0.1110, 0.5366]])
def diamond(sp, a): return Structure.from_spacegroup('Fd-3m', Lattice.cubic(a), [sp], [[0, 0, 0]])
def bcc(sp, a): return Structure.from_spacegroup('Im-3m', Lattice.cubic(a), [sp], [[0, 0, 0]])
def batio3(c_over_a=1.0, a_pc=4.005):
    a = a_pc * c_over_a ** (-1 / 3); lat = Lattice.tetragonal(a, a * c_over_a)
    return Structure(lat, ['Ba', 'Ti', 'O', 'O', 'O'], [[0, 0, 0], [.5, .5, .5], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
def czts(order='kesterite'):
    sites = {'kesterite': ['Cu', 'Sn', 'Cu', 'Zn'], 'stannite': ['Zn', 'Sn', 'Cu', 'Cu']}[order]  # 2a, 2b, 2c, 2d of I-4
    return Structure.from_spacegroup('I-4', Lattice.tetragonal(5.427, 10.871), sites + ['S'],
                                     [[0, 0, 0], [0, 0, .5], [0, .5, .25], [0, .5, .75], [0.756, 0.757, 0.872]])
def ni3al(S=1.0, a=3.5720):
    xa = 0.25; corner = {'Al': xa + (1 - xa) * S, 'Ni': (1 - xa) * (1 - S)}; face = {'Al': xa * (1 - S), 'Ni': 1 - xa * (1 - S)}
    clean = lambda d: {k: v for k, v in d.items() if v > 1e-9}
    return Structure(Lattice.cubic(a), [clean(corner)] + [clean(face)] * 3, [[0, 0, 0], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]])
def nial(): return Structure(Lattice.cubic(2.887), ['Ni', 'Al'], [[0, 0, 0], [.5, .5, .5]])
def fcc(sp, a): return Structure.from_spacegroup('Fm-3m', Lattice.cubic(a), [sp], [[0, 0, 0]])
def zro2_m(): return Structure.from_spacegroup('P2_1/c', Lattice.monoclinic(5.1507, 5.2028, 5.3156, 99.194), ['Zr', 'O', 'O'],
                                               [[0.2754, 0.0395, 0.2083], [0.0700, 0.3317, 0.3447], [0.4496, 0.7569, 0.4792]])
def zro2_t(): return Structure.from_spacegroup(137, Lattice.tetragonal(3.5984, 5.1520), ['Zr', 'O'], [[0, 0, 0], [0, 0.5, 0.2044]])
def zro2_c(): return Structure.from_spacegroup('Fm-3m', Lattice.cubic(5.09), ['Zr', 'O'], [[0, 0, 0], [.25, .25, .25]])
def zns(): return Structure.from_spacegroup('F-43m', Lattice.cubic(5.4093), ['Zn', 'S'], [[0, 0, 0], [.25, .25, .25]])
def cu2sns3(): return Structure.from_spacegroup('F-43m', Lattice.cubic(5.43), [{'Cu': 2 / 3, 'Sn': 1 / 3}, 'S'], [[0, 0, 0], [.25, .25, .25]])
def sige(x_ge=0.5):
    return Structure.from_spacegroup('Fd-3m', Lattice.cubic((1 - x_ge) * 5.43114 + x_ge * 5.6579), [{'Si': 1 - x_ge, 'Ge': x_ge}], [[0, 0, 0]])
def mow(x_w=0.5): return Structure.from_spacegroup('Im-3m', Lattice.cubic((1 - x_w) * 3.1470 + x_w * 3.1652), [{'Mo': 1 - x_w, 'W': x_w}], [[0, 0, 0]])
