"""Parse the ACS Omega SI table into a clean CSV. Aggregates only to stdout (V9-X1).

Input : pdftotext -layout output of ao2c00640_si_001.pdf
Output: ~/v9_data/ds1_parsed/ds1.csv  with columns sequence,intensity,class_si
"""
import csv, hashlib, os, re, statistics, sys
from collections import Counter

AA = "ACDEFGHIKLMNPQRSTVWY"
ROW = re.compile(rf"^\s*([{AA}]{{10}})\s+(-?\d+(?:\.\d+)?)\s+([AB])\s*$")

src, out = sys.argv[1], os.path.expanduser(sys.argv[2])
os.makedirs(os.path.dirname(out), exist_ok=True)
rows, skipped = [], 0
for line in open(src, errors="replace"):
    m = ROW.match(line)
    if m:
        rows.append((m.group(1), float(m.group(2)), m.group(3)))
    elif re.search(rf"\b[{AA}]{{10}}\b", line):
        skipped += 1

with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["sequence", "intensity", "class_si"])
    w.writerows(rows)

inten = sorted(r[1] for r in rows)
n = len(inten)


def q(p):
    i = p * (n - 1)
    lo, hi = int(i), min(int(i) + 1, n - 1)
    return inten[lo] + (i - lo) * (inten[hi] - inten[lo])


print(f"parsed rows            : {n}")
print(f"lines with a 10-mer but not matching the row pattern: {skipped}")
print(f"unique sequences       : {len(set(r[0] for r in rows))}")
print(f"length check           : {Counter(len(r[0]) for r in rows)}")
print(f"class counts (SI label): {dict(Counter(r[2] for r in rows))}")
print(f"intensity min / max    : {inten[0]:.1f} / {inten[-1]:.1f}")
print(f"Q1 / median / Q3       : {q(.25):.1f} / {q(.5):.1f} / {q(.75):.1f}")
print(f"mean / stdev           : {statistics.mean(inten):.1f} / {statistics.stdev(inten):.1f}")
agree = sum(1 for s, v, c in rows if (v > 207500) == (c == "A"))
print(f"SI class == (intensity > 207500): {agree}/{n} = {agree/n:.4f}  (paper's stated cutoff)")
med = q(.5)
agree2 = sum(1 for s, v, c in rows if (v > med) == (c == "A"))
print(f"SI class == (intensity > dataset median {med:.0f}): {agree2}/{n} = {agree2/n:.4f}")
print(f"csv sha256             : {hashlib.sha256(open(out,'rb').read()).hexdigest()}")
print(f"csv written            : {out}")
