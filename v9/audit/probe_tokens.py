"""Count every amino-acid-alphabet token in a text, by length. Aggregates only (V9-X1).

Replaces the first-match-per-line behaviour of probe_table.py, which under-counts when a whole
document sits on one line (V9-E2).
"""
import re, sys
from collections import Counter

AA = "ACDEFGHIKLMNPQRSTVWY"
t = open(sys.argv[1], errors="replace").read()
lo = int(sys.argv[2]) if len(sys.argv) > 2 else 6
toks = re.findall(rf"\b[{AA}]{{{lo},}}\b", t)
print(f"chars: {len(t)}  tokens of length >= {lo}: {len(toks)}  distinct: {len(set(toks))}")
print(f"length histogram: {dict(sorted(Counter(len(x) for x in toks).items()))}")
print(f"most repeated token lengths with counts of distinct values:")
for L, c in sorted(Counter(len(x) for x in toks).items()):
    d = len({x for x in toks if len(x) == L})
    print(f"  len {L:3d}: {c:5d} occurrences, {d:5d} distinct")
