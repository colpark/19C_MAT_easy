"""Stage 2r scenario selection (V5_SPEC D.2, D.3), census and DFT truth only, no FM call. Candidates are ranked by sha256 of their
WBM ids; every candidate is listed with pass/fail reasons in stage2r/SELECTION.json; tuning (r3, r4) then takes the first candidate
of each shape that can meet the section 3 constraints, in this order.
  python stage2r/select.py DATA_ZIP"""
import hashlib, importlib.util, json, os, sys, zipfile
from collections import defaultdict
import numpy as np
from pymatgen.core import Composition, Element

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location('sel_v5', os.path.join(HERE, '..', 'stage2', 'select.py'))
V5 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(V5)       # rule v2 helpers of v5 stage 2, unchanged
rank = lambda *ids: hashlib.sha256('|'.join(ids).encode()).hexdigest()
N_A = 6.02214076e23
PEROV = ('perovskite_cubic', 'perovskite_P4mm', 'perovskite_Pnma', 'perovskite_R3c')
PLACEBO_MIN = 0.05            # r2: placebo lattice error above 5 %
N_KEEP = 25


def vol_atom(el):
    v = Element(el).molar_volume
    return float(v) / N_A * 1e24 if v else 20.0


def placebo_err(row):
    """cube root of (placebo volume-table volume per atom / DFT volume per atom) - 1 (stage2.placebo_volume rule)."""
    c = Composition(row['formula']); pv = sum(vol_atom(e.symbol) * a for e, a in c.items()) / c.num_atoms
    return (pv / row['vol_per_atom']) ** (1 / 3) - 1


def metals(els): return all(Element(e).is_metal for e in els)


def main():
    C = {r['id']: r for r in map(json.loads, open(os.path.join(HERE, '..', 'data', 'stage2', 'wbm_census.jsonl'))) if 'error' not in r}
    H = json.load(open(os.path.join(HERE, '..', 'stage2', 'prototype_hits.json')))
    proto_of = defaultdict(dict)            # formula -> prototype -> [ids by hash]
    for p, ids in H.items():
        for i in sorted(ids, key=rank): proto_of[C[i]['formula']].setdefault(p, []).append(i)
    base_ok = lambda r: V5.ok_elements(r['elements']) and V5.charge_ok(r['formula'])
    pe = lambda i: round(placebo_err(C[i]), 4)
    out = {}

    # 41 loud: ABO3 with a perovskite variant and an ilmenite
    cands = []
    for f, d in proto_of.items():
        pv = [p for p in PEROV if p in d]
        if not pv or 'ilmenite' not in d: continue
        r = C[d['ilmenite'][0]]
        if not base_ok(r) or len(r['elements']) != 3 or 'O' not in r['elements']: continue
        ip = d[pv[0]][0] if len(pv) == 1 else sorted((d[p][0] for p in pv), key=rank)[0]
        pp = next(p for p in pv if ip in d[p])
        ids = [ip, d['ilmenite'][0]]
        c = dict(formula=f, protos=[pp, 'ilmenite'], ids=ids, placebo_err=[pe(i) for i in ids])
        c['passes'] = all(abs(e) > PLACEBO_MIN for e in c['placebo_err'])
        cands.append(c)
    cands.sort(key=lambda c: rank(*c['ids'])); out['41'] = cands[:N_KEEP]

    # 42 quiet: two different perovskite variants of one composition
    cands = []
    for f, d in proto_of.items():
        pv = [p for p in PEROV if p in d]
        if len(pv) < 2: continue
        r = C[d[pv[0]][0]]
        if not base_ok(r) or len(r['elements']) != 3: continue
        firsts = sorted(((p, d[p][0]) for p in pv), key=lambda t: rank(t[1]))[:2]
        ids = [firsts[0][1], firsts[1][1]]
        c = dict(formula=f, protos=[firsts[0][0], firsts[1][0]], ids=ids, placebo_err=[pe(i) for i in ids])
        c['passes'] = all(abs(e) > PLACEBO_MIN for e in c['placebo_err'])
        cands.append(c)
    cands.sort(key=lambda c: rank(*c['ids'])); out['42'] = cands[:N_KEEP]

    # 43 trace: ABO3 perovskite main + two impurity phases of the same chemical system (binary oxides of A or B in listed prototypes)
    by_sys = defaultdict(list)
    for p, ids in H.items():
        for i in ids: by_sys[tuple(sorted(C[i]['elements']))].append((p, i))
    cands = []
    mains = sorted({i for p in PEROV for i in H[p]}, key=rank)
    for i in mains:
        r = C[i]; els = r['elements']
        if 'O' not in els or len(els) != 3 or not base_ok(r): continue
        AB = [e for e in els if e != 'O']
        imps = sorted({(p, j) for e in AB for (p, j) in by_sys.get(tuple(sorted([e, 'O'])), []) if base_ok(C[j])}, key=lambda t: rank(t[1]))
        seen, pick = set(), []
        for p, j in imps:                                        # distinct (formula, prototype) pairs
            key = (C[j]['formula'], p)
            if key in seen: continue
            seen.add(key); pick.append((p, j))
        if len(pick) < 2: continue
        (p1, j1), (p2, j2) = pick[:2]
        c = dict(main=i, main_formula=r['formula'], main_proto=next(p for p in PEROV if i in H[p]), impurities=[j1, j2],
                 impurity_formulas=[C[j1]['formula'], C[j2]['formula']], impurity_protos=[p1, p2], placebo_err=[pe(j1), pe(j2)], main_placebo_err=pe(i))
        c['passes'] = all(abs(e) > PLACEBO_MIN for e in c['placebo_err'])
        cands.append(c)
        if len(cands) >= N_KEEP: break
    out['43'] = cands

    # 44 L1_2 A3B, two metals; 45 B2 AB, two metals
    for key, proto in (('44', 'L1_2'), ('45', 'B2')):
        cands = []
        for i in sorted(H[proto], key=rank):
            r = C[i]
            if not V5.ok_elements(r['elements']) or len(r['elements']) != 2 or not metals(r['elements']): continue
            c = dict(id=i, formula=r['formula'], placebo_err=pe(i)); c['passes'] = abs(c['placebo_err']) > PLACEBO_MIN
            cands.append(c)
        out[key] = [c for c in cands if c['passes']][:N_KEEP] + [dict(n_total=len(cands), n_pass=sum(c['passes'] for c in cands))]
    json.dump(dict(rule='V5_SPEC D.3 (rule v2 + r2 placebo lattice error > 5 %); order = sha256 of WBM ids; r3/r4 applied at tuning',
                   candidates=out), open(os.path.join(HERE, 'SELECTION.json'), 'w'), indent=1)
    for k, v in out.items():
        first = [c for c in v if c.get('passes')][:3]
        print(k, json.dumps(first))


if __name__ == '__main__':
    main()
