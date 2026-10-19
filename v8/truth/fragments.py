"""V8-1: cut one repeat unit with its caps from each design in Supplementary Table 2.

Builder-only (names the published designs). Agent-facing ids are HRm-xx hashes.
Fragment = N-cap + the design's minimal internal period + C-cap. The minimal period is
one 50-residue repeat, or two for designs whose charge pattern alternates between
neighbouring repeats (checker, scrambled controls), so the pattern survives the cut (V8-X4).
Non-capped (NC) designs have no caps; their fragment is the internal unit alone.
"""
import hashlib, json, os, sys

P = 50  # repeat period (self-similarity 0.94 on the 18-repeat design)
TAG = "LVPRGS"  # thrombin site; expressed tag removed up to and including GS


def core(seq):
    i = seq.find(TAG)
    s = seq[i + len(TAG):] if i >= 0 else seq
    return s


def split(seq):
    """Return (ncap, [internal repeats], ccap) using the conserved helix-1 motif."""
    starts = [i for i in range(len(seq) - 4) if seq[i + 3:i + 6] == "SSE" and seq[i] == "G"]
    # internal repeats begin at G..SSE at period P; the C-cap is the last such block
    if not starts:
        return None
    blocks = []
    for st in starts:
        if not blocks or st - blocks[-1] >= P - 2:
            blocks.append(st)
    ncap = seq[:blocks[0]]
    reps = [seq[a:b] for a, b in zip(blocks, blocks[1:])]
    ccap = seq[blocks[-1]:]
    return ncap, reps, ccap


def minimal_unit(reps):
    for k in (1, 2, 3):
        if len(reps) >= 2 * k and all(reps[i] == reps[i % k] for i in range(len(reps))):
            return reps[:k]
    for k in (1, 2):  # tolerate a differing first/last internal repeat
        inner = reps[1:-1] if len(reps) > 3 else reps
        if len(inner) >= k and all(inner[i] == inner[i % k] for i in range(len(inner))):
            return inner[:k]
    return reps[:2]


def hid(s):
    return "HRm-" + hashlib.sha256(s.encode()).hexdigest()[:2]


if __name__ == "__main__":
    tab = json.load(open(sys.argv[1]))
    out, seen = {}, {}
    for name, seq in tab.items():
        c = core(seq)
        sp = split(c)
        ncap, reps, ccap = sp
        unit = minimal_unit(reps) if reps else []
        capped = "NC" not in name
        frag = (ncap if capped else "") + "".join(unit) + (ccap if capped else "")
        key = frag
        seen.setdefault(key, []).append(name)
        out[name] = dict(ncap=len(ncap), n_internal=len(reps), unit_repeats=len(unit), ccap=len(ccap),
                         capped=capped, fragment=frag, frag_len=len(frag),
                         DE=sum(frag.count(x) for x in "DE"), KR=sum(frag.count(x) for x in "KR"))
    for k, names in seen.items():
        print(f"{len(k):4d} aa  DE {sum(k.count(x) for x in 'DE'):3d} KR {sum(k.count(x) for x in 'KR'):3d}  {names}")
    json.dump(out, open(sys.argv[2], "w"), indent=1)
