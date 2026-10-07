"""Addendum B tool tests on synthetic matches: a known exact pair, a doped family pair, a polymorph that must not match."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import match_exp as M
from pymatgen.core import Structure, Lattice, Composition


def rocksalt(a, el=('Li', 'Cl')):
    return Structure.from_spacegroup('Fm-3m', Lattice.cubic(a), list(el), [[0, 0, 0], [0.5, 0.5, 0.5]])


def zincblende(a, el=('Li', 'Cl')):
    return Structure.from_spacegroup('F-43m', Lattice.cubic(a), list(el), [[0, 0, 0], [0.25, 0.25, 0.25]])


def test_exact_pair():
    s = rocksalt(5.13)
    t = rocksalt(5.20)          # same structure, 1.4 % strain (within ltol)
    t.perturb(0.02, 0.0)
    assert M.struct_match(s, t)


def test_polymorph_must_not_match():
    assert not M.struct_match(rocksalt(5.13), zincblende(5.6))


def test_doped_family_pair():
    ok, m = M.family_dope(Composition('Li3.1P0.9Si0.1S4'), Composition('Li3PS4'))
    assert ok and m <= 0.1 + 1e-9


def test_heavy_substitution_not_family():
    ok, _ = M.family_dope(Composition('Li6.4La3Zr1.4Ta0.6O12'), Composition('Li7La3Zr2O12'))
    assert not ok
