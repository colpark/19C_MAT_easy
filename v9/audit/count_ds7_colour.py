"""Audit dataset 7 Table S2: 40 peptides with a measured COLOUR class, not a binding affinity.

Colour group (Red / Green / Blue / Negative) is a discrete class reported by the source, 10
peptides each. A twin here is a near-isobaric pair in two different colour groups. Aggregates
only (V9-X1); the parsed table goes to a CSV the builder does not read back.
"""
import csv, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twin_count import mono_mass, TOLS

AA = "ACDEFGHIKLMNPQRSTVWY"
SEQ = re.compile(rf"\b([{AA}]{{10}})\b")
NUM = r"-?\d+(?:\.\d+)?"
colour, rows = None, []
for line in open(sys.argv[1], errors="replace"):
    for c in ("Negative", "Red", "Green", "Blue"):
        if re.search(rf"^\s*{c}\b", line):
            colour = c
    m = SEQ.search(line)
    if m and colour:
        nums = re.findall(NUM, line[m.end():])
        rows.append((m.group(1), colour, [float(x) for x in nums]))

seen, uniq = set(), []
for s, c, n in rows:
    if s not in seen:
        seen.add(s)
        uniq.append((s, c, n))
print(f"rows parsed: {len(rows)}  distinct peptides: {len(uniq)}")
print(f"colour groups: {dict(Counter(c for _, c, _ in uniq))}")
print(f"numeric columns per row: {dict(Counter(len(n) for _, _, n in uniq))}")

with open(os.path.expanduser(sys.argv[2]), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["sequence", "colour", "numbers"])
    w.writerows([(s, c, ";".join(map(str, n))) for s, c, n in uniq])

mass = {s: mono_mass(s) for s, _, _ in uniq}
grp = {s: c for s, c, _ in uniq}
seqs = sorted(mass, key=lambda s: mass[s])
n = len(seqs)
print(f"\nmass range: {min(mass.values()):.4f} to {max(mass.values()):.4f} Da")
print(f"total pairs: {n*(n-1)//2}")
for tol in TOLS:
    near = twin = 0
    for i in range(n):
        for j in range(i + 1, n):
            if mass[seqs[j]] - mass[seqs[i]] > tol:
                break
            near += 1
            if grp[seqs[i]] != grp[seqs[j]]:
                twin += 1
    print(f"tol {tol:5.2f} Da | near-isobaric {near:4d} | different-colour twins {twin:4d} "
          f"| Gate T needs 30 -> {'PASS' if twin >= 30 else 'FAIL'}")
