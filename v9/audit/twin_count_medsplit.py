"""Robustness check: the same twin count under the SOURCE'S OWN reported classes.

The ACS Omega SI reports a binary class from a median split at intensity 207,500. Gate D's
second clause ("the source reports discrete classes") covers exactly these labels, so this
variant shows what Gate T looks like on the classes that clause actually certifies.
Aggregates only (V9-X1).
"""
import csv, os, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_count import mono_mass, panel_score, TOLS

rows = list(csv.DictReader(open(sys.argv[1])))
seqs = [r["sequence"] for r in rows]
cls = {r["sequence"]: r["class_si"] for r in rows}
mass = {s: mono_mass(s) for s in seqs}
n = len(seqs)
print(f"peptides: {n}  class counts: {dict(Counter(cls.values()))}")
by_mass = sorted(seqs, key=lambda s: mass[s])
for tol in TOLS:
    near = opp = e = k = 0
    for i in range(n):
        for j in range(i + 1, n):
            if mass[by_mass[j]] - mass[by_mass[i]] > tol:
                break
            near += 1
            a, b = by_mass[i], by_mass[j]
            if cls[a] != cls[b]:
                opp += 1
                strong, weak = (a, b) if cls[a] == "A" else (b, a)
                if panel_score(strong) > panel_score(weak):
                    e += 1
                else:
                    k += 1
    print(f"tol {tol:5.2f} Da | near-isobaric {near:7d} | opposite-class twins {opp:6d} "
          f"| E {e:6d} | K {k:5d}" + (f" | accuracy {e/opp:.3f}" if opp else ""))
