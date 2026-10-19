"""Structure of lines that contain a peptide: field layout and numeric columns. No sequences."""
import re, sys
from collections import Counter

AA = "ACDEFGHIKLMNPQRSTVWY"
TOK = re.compile(rf"\b[{AA}]{{10}}\b")
NUM = re.compile(r"^-?\d+(?:[.,]\d+)?(?:[eE]-?\d+)?$")
layout, ncols, nnum = Counter(), Counter(), Counter()
for l in open(sys.argv[1], errors="replace"):
    if not TOK.search(l):
        continue
    f = l.split()
    ncols[len(f)] += 1
    nnum[sum(1 for x in f if NUM.match(x))] += 1
    layout["".join("S" if TOK.fullmatch(x) else ("9" if NUM.match(x) else "x") for x in f)] += 1
print(f"fields per peptide line : {dict(sorted(ncols.items()))}")
print(f"numeric fields per line : {dict(sorted(nnum.items()))}")
print("field-type patterns (S=sequence, 9=number, x=other), top 8:")
for p, c in layout.most_common(8):
    print(f"  {c:5d}  {p}")
