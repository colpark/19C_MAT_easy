#!/usr/bin/env python3
"""test_derived33.py (v3.3 definition 7): synthetic tests of the derived observable procedures."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import laws as L
ok = True
E = [1.2 + 0.001 * k for k in range(400)]; cur = [(e, 0.5 + 10 ** ((e - 1.45) / 0.05)) for e in E]   # Tafel-like curve, j = 10 at E = 1.45 + 0.05*log10(9.5)
want = 1.45 + 0.05 * math.log10(9.5); got = L.potential_at_current(cur, 10.0); ok &= abs(got - want) < 2e-4
pk = [(x / 10, math.exp(-((x / 10 - 3.37) / 0.5) ** 2)) for x in range(0, 80)]; ok &= abs(L.peak_position(pk) - 3.37) < 0.01
lin = [(x / 10, 2 * x / 10) for x in range(0, 51)]; ok &= abs(L.integral(lin) - 25.0) < 1e-9
az = [(a, 1 + 0.5 * math.cos(math.radians(2 * a))) for a in range(-90, 91)]; ok &= abs(L.azimuthal_anisotropy(az) - 0.5) < 1e-3
ok &= L.potential_at_current([(1.2, 0.1), (1.3, 1.0)], 10.0) is None
print('derived procedures:', 'PASS' if ok else 'FAIL'); sys.exit(0 if ok else 1)
