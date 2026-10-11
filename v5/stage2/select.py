"""Stage 2 scenario selection (V5_SPEC B.4), census only, no FM call. Candidates are ranked by sha256 of their WBM ids; every
candidate is listed with pass/fail reasons in stage2/SELECTION.json, and the first passing one per scenario is chosen.
  python stage2/select.py DATA_ZIP"""
import hashlib, json, os, sys, zipfile
from collections import defaultdict
import numpy as np
from pymatgen.core import Composition, Element, Lattice, Structure

HERE = os.path.dirname(os.path.abspath(__file__))
EXCL = {'H', 'He', 'Ne', 'Ar', 'Kr', 'Xe', 'Rn'} | {e.symbol for e in Element if e.is_actinoid or (e.is_lanthanoid and e.symbol != 'La')}
rank = lambda *ids: hashlib.sha256('|'.join(ids).encode()).hexdigest()


def load_struct(z, mid):
    txt = z.read(f'{mid}.extxyz').decode().strip().splitlines()
    import re
    n = int(txt[0]); lat = np.array([float(x) for x in re.search(r'Lattice="([^"]+)"', txt[1]).group(1).split()]).reshape(3, 3)
    sp = [l.split()[0] for l in txt[2:2 + n]]; pos = [[float(v) for v in l.split()[1:4]] for l in txt[2:2 + n]]
    return Structure(Lattice(lat), sp, pos, coords_are_cartesian=True)


ANIONS = {'O', 'S', 'Se', 'Te', 'N', 'F', 'Cl', 'Br', 'I'}


def ok_elements(els): return not (set(els) & EXCL)


def charge_ok(formula):
    """rule v2: a compound containing an anion must be charge-balanced with common oxidation states only."""
    c = Composition(formula)
    if not ({e.symbol for e in c.elements} & ANIONS): return True
    try: return len(c.oxi_state_guesses(all_oxi_states=False)) > 0
    except Exception: return False


def main():
    zp = sys.argv[1]; z = zipfile.ZipFile(zp)
    C = {r['id']: r for r in map(json.loads, open(os.path.join(HERE, 'wbm_census.jsonl')))}
    H = json.load(open(os.path.join(HERE, 'prototype_hits.json')))
    proto_of = defaultdict(list)
    for p, ids in H.items():
        for i in ids: proto_of[C[i]['formula']].append((p, i))
    log = {}; chosen = {}

    # S2-A: one formula in two different listed prototypes
    cands = []
    for f, lst in proto_of.items():
        ps = {}
        for p, i in sorted(lst, key=lambda t: rank(t[1])): ps.setdefault(p, i)
        if len(ps) >= 2 and ok_elements([e.symbol for e in Composition(f).elements]) and len(Composition(f)) <= 3 and charge_ok(f):
            pp = sorted(ps)[:2]; cands.append(dict(formula=f, protos=pp, ids=[ps[pp[0]], ps[pp[1]]]))
    cands.sort(key=lambda c: rank(*c['ids']))
    log['S2-A'] = cands[:20]; chosen['S2-A'] = cands[0] if cands else None

    # S2-B: P4mm perovskite with 1.003 <= c/a <= 1.03, closest to 1 first
    cands = []
    for i in H['perovskite_P4mm']:
        if not ok_elements(C[i]['elements']) or len(C[i]['elements']) > 3 or not charge_ok(C[i]['formula']): continue
        s = load_struct(z, i); a, b, c = s.lattice.abc
        ca = max(a, b, c) / min(a, b, c)
        cands.append(dict(id=i, formula=C[i]['formula'], c_over_a=round(ca, 5), passes=1.003 <= ca <= 1.03))
    good = sorted([c for c in cands if c['passes']], key=lambda c: (c['c_over_a'], rank(c['id'])))
    log['S2-B'] = dict(n=len(cands), n_pass=len(good), first=good[:10]); chosen['S2-B'] = good[0] if good else None

    # S2-C: cubic perovskite ABO3 + impurity phase of the same chemical system in a listed prototype
    by_sys = defaultdict(list)
    for p, ids in H.items():
        for i in ids: by_sys[tuple(sorted(C[i]['elements']))].append((p, i))
    cands = []
    for i in sorted(H['perovskite_cubic'], key=rank):
        els = C[i]['elements']
        if 'O' not in els or not ok_elements(els) or len(els) != 3 or not charge_ok(C[i]['formula']): continue
        A_B = [e for e in els if e != 'O']
        imps = [(p, j) for e in A_B for (p, j) in by_sys.get(tuple(sorted([e, 'O'])), []) if charge_ok(C[j]['formula'])]
        if imps:
            p, j = sorted(imps, key=lambda t: rank(t[1]))[0]
            cands.append(dict(main=i, main_formula=C[i]['formula'], impurity=j, impurity_formula=C[j]['formula'], impurity_proto=p))
        if len(cands) >= 20: break
    log['S2-C'] = cands; chosen['S2-C'] = cands[0] if cands else None

    # S2-D: rocksalt or B2 AX, BX (same X) with lattice mismatch 0.3 to 0.8 %
    cands = []
    for proto in ('rocksalt', 'B2'):
        rows = [C[i] for i in H[proto] if ok_elements(C[i]['elements'])]
        a_of = {r['id']: (r['vol_per_atom'] * 2) ** (1 / 3) for r in rows}     # rough conventional-scale proxy from volume
        byX = defaultdict(list)
        for r in rows:
            for x in r['elements']: byX[x].append(r)
        seen = set()
        for x, rs in byX.items():
            for r1 in rs:
                for r2 in rs:
                    if r1['id'] >= r2['id'] or (r1['id'], r2['id']) in seen: continue
                    seen.add((r1['id'], r2['id']))
                    o1 = [e for e in r1['elements'] if e != x]; o2 = [e for e in r2['elements'] if e != x]
                    if len(o1) != 1 or len(o2) != 1 or o1 == o2: continue
                    A_, B_ = Element(o1[0]), Element(o2[0])
                    if not (A_.is_metal and B_.is_metal): continue                     # rule v2: mixed site of two metals
                    if proto == 'rocksalt' and x not in ANIONS: continue               # rocksalt: X an anion
                    if proto == 'B2' and not Element(x).is_metal: continue             # B2: intermetallic
                    if not (charge_ok(r1['formula']) and charge_ok(r2['formula'])): continue
                    mis = abs(a_of[r1['id']] / a_of[r2['id']] - 1)
                    if 0.003 <= mis <= 0.008: cands.append(dict(proto=proto, X=x, ids=[r1['id'], r2['id']], formulas=[r1['formula'], r2['formula']], mismatch=round(mis, 5)))
    cands.sort(key=lambda c: rank(*c['ids']))
    log['S2-D'] = dict(n=len(cands), first=cands[:20]); chosen['S2-D'] = cands[0] if cands else None

    # S2-E: L1_2 A3B
    cands = [dict(id=i, formula=C[i]['formula']) for i in sorted(H['L1_2'], key=rank) if ok_elements(C[i]['elements'])]
    log['S2-E'] = dict(n=len(cands), first=cands[:20]); chosen['S2-E'] = cands[0] if cands else None

    json.dump(dict(chosen=chosen, candidates=log), open(os.path.join(HERE, 'SELECTION.json'), 'w'), indent=1)
    print(json.dumps(chosen, indent=1))


if __name__ == '__main__':
    main()
