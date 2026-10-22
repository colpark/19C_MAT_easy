"""V10-X10 change 3: the development-chosen S-llm program per family, fixed before any bench run (output hashed into FREEZE.md).
Inputs: grade10 records of the S-llm programs' development runs (tuning-split development worlds, k = 99; labels S-llm-<FAM><i>).
Score of a program: the share of its family's development units it resolves under the evidence key (a pair needs both twins, a T quad
all four cells, as analyze10.unit_table), each unit counted once. Ties go to the higher V7-X4 resolved share, then to the program whose
calls are fewest in total (cheaper), then to the lower program index.
  python F/sllm/choose_dev10.py OUT.json DEV_GRADED.json [DEV_GRADED.json ...]"""
import json, re, sys
from collections import defaultdict

FAMS = ('R', 'H', 'T')


def main():
    out_p = sys.argv[1]; G = []
    for p in sys.argv[2:]: G += json.load(open(p))
    by = defaultdict(list)
    for g in G:
        lab = g.get('model') or ''
        if g.get('k') != 99 or not re.fullmatch(r'S-llm-[RHT]\d+', lab) or g.get('void'): continue
        by[(lab, g['scen'])].append(g)
    prog = defaultdict(lambda: dict(units=0, ev=0, x4=0, calls=0))
    for (lab, s), gs in by.items():
        fam = lab[6]; need = 4 if fam == 'T' else 2
        cells = {(g['cell'] if fam == 'T' else g['twin']): g for g in gs}
        p = prog[lab]; p['units'] += 1; p['calls'] += sum(len(g.get('calls') or []) for g in gs)
        if len(cells) == need:
            p['ev'] += all(c['credit'] for c in cells.values()); p['x4'] += all(c['resolved_v7x4'] for c in cells.values())
    chosen, table = {}, {}
    for f in FAMS:
        labs = sorted((l for l in prog if l[6] == f), key=lambda l: int(l[7:]))
        rows = {l: dict(prog[l], score=round(prog[l]['ev'] / prog[l]['units'], 4), x4_share=round(prog[l]['x4'] / prog[l]['units'], 4)) for l in labs}
        table[f] = rows
        if rows: chosen[f] = sorted(labs, key=lambda l: (-rows[l]['score'], -rows[l]['x4_share'], rows[l]['calls'], int(l[7:])))[0]
    json.dump(dict(rule='max evidence-key unit share on development worlds (k = 99); ties: V7-X4 share, fewer calls, lower index',
                   chosen=chosen, table=table), open(out_p, 'w'), indent=1)
    print(json.dumps(chosen))


if __name__ == '__main__':
    main()
