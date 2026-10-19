"""Structure probe: never emits a peptide sequence.

Prints a line verbatim only when it contains no amino-acid-alphabet token of length >= 6.
Record-like lines are replaced by a character-class skeleton (L=letter, 9=digit), which shows
the field layout without showing identity. V9-X1 requires this.
"""
import re, sys

AA = "ACDEFGHIKLMNPQRSTVWY"
RECORD = re.compile(rf"\b[{AA}]{{6,}}\b")


def skeleton(s):
    return re.sub(r"\d", "9", re.sub(r"[A-Za-z]", "L", s))


def main(path, head, tail):
    lines = open(path, errors="replace").read().splitlines()
    print(f"# lines: {len(lines)}  nonblank: {sum(1 for l in lines if l.strip())}")
    n_rec = sum(1 for l in lines if RECORD.search(l))
    print(f"# record-like lines (amino-acid token >= 6): {n_rec}")
    idx = list(range(min(head, len(lines)))) + list(range(max(0, len(lines) - tail), len(lines)))
    for i in sorted(set(idx)):
        l = lines[i]
        print(f"{i:5d}| {skeleton(l) if RECORD.search(l) else l}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
