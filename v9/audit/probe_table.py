"""Aggregate-only probe of the SI table. Emits counts, never a sequence."""
import re, sys
from collections import Counter

AA = "ACDEFGHIKLMNPQRSTVWY"
TOK = re.compile(rf"\b[{AA}]{{4,}}\b")

lines = open(sys.argv[1], errors="replace").read().splitlines()
lens, ncols, labels, numeric = Counter(), Counter(), Counter(), Counter()
rec = 0
for l in lines:
    m = TOK.search(l)
    if not m:
        continue
    rec += 1
    f = l.split()
    ncols[len(f)] += 1
    lens[len(m.group(0))] += 1
    # any field that is not the sequence: classify it
    for x in f:
        if x == m.group(0):
            continue
        if re.fullmatch(r"-?\d+(\.\d+)?([eE]-?\d+)?", x):
            numeric["number"] += 1
        elif len(x) <= 2:
            labels[x] += 1
        else:
            labels["<other>"] += 1
print(f"record-like lines: {rec}")
print(f"token length histogram: {dict(sorted(lens.items()))}")
print(f"fields per line: {dict(sorted(ncols.items()))}")
print(f"numeric fields seen: {dict(numeric)}")
print(f"short non-sequence field values: {dict(sorted(labels.items(), key=lambda kv: -kv[1])[:12])}")
