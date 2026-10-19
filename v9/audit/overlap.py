"""Is candidate set B a subset of dataset 1, and where does it sit in the intensity ranking?

Aggregates only: counts and rank statistics, never a sequence (V9-X1).
Usage: python3 -I overlap.py DS1.csv TEXT_WITH_SEQUENCES
"""
import csv, re, statistics, sys

AA = "ACDEFGHIKLMNPQRSTVWY"
rows = list(csv.DictReader(open(sys.argv[1])))
inten = {r["sequence"]: float(r["intensity"]) for r in rows}
order = sorted(inten, key=lambda s: -inten[s])          # rank 1 = strongest binder
rank = {s: i + 1 for i, s in enumerate(order)}
n = len(order)

text = open(sys.argv[2], errors="replace").read()
cand = sorted(set(re.findall(rf"\b[{AA}]{{10}}\b", text)))
inside = [s for s in cand if s in inten]
outside = [s for s in cand if s not in inten]
print(f"dataset 1 size            : {n}")
print(f"candidate distinct 10-mers: {len(cand)}")
print(f"  found in dataset 1      : {len(inside)}  ({len(inside)/len(cand):.1%})")
print(f"  NOT in dataset 1        : {len(outside)}")
if inside:
    rk = sorted(rank[s] for s in inside)
    print(f"  their rank range        : {rk[0]} to {rk[-1]} of {n} (1 = strongest binder)")
    print(f"  median rank             : {statistics.median(rk):.0f}")
    print(f"  how many in the top quartile (rank <= {n//4}) : {sum(1 for r in rk if r <= n//4)}")
    print(f"  how many in the bottom quartile (rank > {n - n//4}): {sum(1 for r in rk if r > n - n // 4)}")
    print(f"  how many in the top 200 : {sum(1 for r in rk if r <= 200)}")
