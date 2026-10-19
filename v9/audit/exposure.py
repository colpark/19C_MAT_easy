"""How many of the counted twin pairs have a member re-published elsewhere as a labelled binder?

A twin whose strong member appears in another paper's explicit "high-binding" list is more
exposed to model recall. Counts only (V9-X1).
Usage: python3 -I exposure.py twins.json TEXT [TEXT ...]
"""
import json, re, sys

AA = "ACDEFGHIKLMNPQRSTVWY"
d = json.load(open(sys.argv[1]))
exposed = set()
for p in sys.argv[2:]:
    exposed |= set(re.findall(rf"\b[{AA}]{{10}}\b", open(p, errors="replace").read()))
print(f"distinct peptides re-published in the other papers: {len(exposed)}")
for tol, v in d["tolerances"].items():
    pr = v["pairs"]
    both = sum(1 for x in pr if x["strong"] in exposed and x["weak"] in exposed)
    strong = sum(1 for x in pr if x["strong"] in exposed)
    either = sum(1 for x in pr if x["strong"] in exposed or x["weak"] in exposed)
    k = [x for x in pr if x["panel"] == "K"]
    k_clean = sum(1 for x in k if x["strong"] not in exposed and x["weak"] not in exposed)
    print(f"tol {float(tol):5.2f} Da | twins {len(pr):4d} | strong member exposed {strong:4d} "
          f"({strong/len(pr):5.1%}) | either exposed {either:4d} | both {both:3d} "
          f"|| K stratum {len(k):3d}, of which fully unexposed {k_clean:3d}")
