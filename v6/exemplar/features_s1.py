"""V6-2 (amendment A) features, part 1: the pool and bar 1 (pattern similarity). DFT data and simulation only; no FM, no LLM.
Pool (V6_SPEC 3): R pairs (and, for the H funnel, H pairs) from the stage 4 census and the stage 4b pool: formulas with no MP entry, a
library of two or three polymorphs (one per J.6 prototype key, the lowest-energy entry of a key), rule v2 exclusions with the V5-E27
charge rule, at most 4 elements, at most 24 sites per polymorph, novelty against MP (the anonymous formula with world A's prototype key
at most twice in MP); dev formulas excluded (stage 4b dev formulas and the formulas of the stage 4 dev split).
  R: world A = P1 (DFT ground state), world B = the first polymorph by sha256 of its id at least 75 meV/atom above P1.
  H: world A at most 15 meV/atom above the MP hull, world B at least 125, the first such pair by sha256 of the sorted ids.
Bar 1: D(m0) of each twin against its nearest other polymorph at N = 1000; s = the larger over the twins / 1000; N_q,lin = 9 / s; the
exact N_q (largest N with both twins' D(m0) < 9, bisection) for members with N_q,lin >= 5 (D grows at least linearly with N below
1000, so N_q >= N_q,lin; V6-X6). Bar: N_q >= 50.
  python v6/exemplar/features_s1.py OUT.jsonl"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
import gzip, hashlib, json, math
from collections import Counter, defaultdict
from multiprocessing import get_context

V5 = os.path.join(HERE, '..', '..', '..', 'v5', 'v5')
sha = lambda s: hashlib.sha256(s.encode()).hexdigest()
TMP = 989


def _key_sites(mid):
    from mcenv import stage2 as S2
    from mcenv import heuristics4b as H
    try: st = S2.wbm(mid); return mid, H.proto_key(st), len(st)
    except Exception: return mid, None, None


def _mp_key(sd):
    from pymatgen.core import Structure
    from mcenv import heuristics4b as H
    return H.proto_key(Structure.from_dict(sd))


def pool():
    import pandas as pd
    from pymatgen.core import Composition
    from mcenv import heuristics4b as H
    W = pd.read_csv(os.path.join(V5, 'data', 'stage4', '2023-12-13-wbm-summary.csv.gz'))
    W['rf'] = [Composition(f).reduced_formula for f in W.formula]
    c4 = json.load(open(os.path.join(V5, 'data', 'stage4', 'census4.json')))['formulas']
    p4b = json.load(open(os.path.join(V5, 'data', 'stage4b', 'pool4b.json')))
    dev = {f for f, v in p4b.items() if v['dev']}
    dev |= {r['formula'] for r in json.load(open(os.path.join(V5, 'stage4', 'dev', 'dev500.json')))}
    forms = [f for f in set(c4) | set(p4b) if f not in dev and len(Composition(f).elements) <= 4
             and not {e.symbol for e in Composition(f).elements} & H.EXCL and H.charge_ok(f)]
    g = W[W.rf.isin(set(forms))]
    ids = list(g.material_id)
    with get_context('spawn').Pool(18) as p: ks = {m: (k, n) for m, k, n in p.imap_unordered(_key_sites, ids, chunksize=64)}
    by = defaultdict(dict)
    for r in g.sort_values('e_form_per_atom_mp2020_corrected').itertuples(index=False):
        k, n = ks[r.material_id]
        if k is None or k in by[r.rf]: continue
        by[r.rf][k] = dict(id=r.material_id, key=k, sites=n, e_form=float(r.e_form_per_atom_mp2020_corrected),
                           e_hull=float(r.e_above_hull_mp2020_corrected_ppd_mp), gap=float(r.bandgap_pbe))
    members = []
    for f, d in by.items():
        ents = sorted(d.values(), key=lambda e: e['e_form'])
        if not 2 <= len(ents) <= 3 or any(e['sites'] is None or e['sites'] > 24 for e in ents): continue
        bs = sorted([e for e in ents[1:] if e['e_form'] - ents[0]['e_form'] >= 0.075], key=lambda e: sha(e['id']))
        if bs: members.append(dict(type='R', formula=f, entries=ents, a=ents[0], b=bs[0], rank=sha('|'.join(sorted([ents[0]['id'], bs[0]['id']])))))
        A = [e for e in ents if e['e_hull'] <= 0.015]; B = [e for e in ents if e['e_hull'] >= 0.125]
        hp = sorted([(sha('|'.join(sorted([a['id'], b['id']]))), a, b) for a in A for b in B if a['id'] != b['id']], key=lambda t: t[0])
        if hp: members.append(dict(type='H', formula=f, entries=ents, a=hp[0][1], b=hp[0][2], rank=hp[0][0]))
    # novelty against MP: anonymous formula with world A's key at most twice in MP
    mp = json.load(gzip.open(os.path.join(V5, 'data', 'stage4', '2023-02-07-mp-computed-structure-entries.json.gz'), 'rt'))
    anons = {Composition(m['formula']).anonymized_formula for m in members}
    mp_s = [v['structure'] for v in mp['entry'].values() if Composition(v['composition']).anonymized_formula in anons]
    del mp
    with get_context('spawn').Pool(18) as p: mk = Counter(p.imap_unordered(_mp_key, mp_s, chunksize=64))
    out = []
    for m in members:
        m['mp_cooccurrence'] = mk.get(m['a']['key'], 0)
        out.append(m)
    return out


def register(m, N):
    from mcenv import scenarios as SC
    from mcenv import stage2 as S2
    names = {e['id']: S2.register_structure(f"v6pool {e['id']}", S2.wbm(e['id'])) for e in m['entries']}
    br = {i: SC.fixed([(n, {}, 1.0)], label=i) for i, n in names.items()}
    wa, wb = TMP * 10 + 1, TMP * 10 + 2
    SC.SCEN[TMP] = dict(name='v6pool', kind='tmp', claim='', description='', library=list(names.values()),
                        worlds={wa: dict(holds=True, phases=[[(names[m['a']['id']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != m['a']['id']]),
                                wb: dict(holds=False, phases=[[(names[m['b']['id']], {}, 1.0)]], other_branches=[b for i, b in br.items() if i != m['b']['id']])},
                        claim_side=[br[m['a']['id']]], other_side=[br[m['b']['id']]])
    SC.TUNE[TMP] = dict(L=100.0, N=N, bg=20.0, Nn=1000.0, bgn=50.0)
    SC.WORLD_SCEN.update({wa: TMP, wb: TMP})


def dm0(m, N):
    from mcenv import separation as SP
    register(m, N)
    return [SP.separation(TMP * 10 + i, [SP.DEFAULT]) for i in (1, 2)]


def bar1(m):
    try:
        d = dm0(m, 1000.0); s = max(d) / 1000.0; nlin = 9.0 / s if s > 0 else float('inf')
        out = dict(D_m0_N1000=[round(x, 3) for x in d], s=round(s, 6), N_q_lin=round(nlin, 3))
        if nlin >= 5:
            lo, hi = nlin, 1000.0
            if max(dm0(m, hi)) < 9: lo = hi
            else:
                for _ in range(25):
                    mid = math.sqrt(lo * hi)
                    if max(dm0(m, mid)) < 9: lo = mid
                    else: hi = mid
            out['N_q'] = round(lo, 3)
        else: out['N_q'] = None
        out['bar1'] = bool(out['N_q'] and out['N_q'] >= 50)
        return m['rank'], out
    except Exception as e:
        return m['rank'], dict(error=f'{type(e).__name__}: {str(e)[:120]}', bar1=False)


if __name__ == '__main__':
    M = pool()
    print(len(M), 'pool members', Counter(m['type'] for m in M), 'novel', sum(m['mp_cooccurrence'] <= 2 for m in M), flush=True)
    with get_context('spawn').Pool(18) as p: res = dict(p.imap_unordered(bar1, [m for m in M if m['mp_cooccurrence'] <= 2], chunksize=4))
    with open(sys.argv[1], 'w') as f:
        for m in M:
            m['novel'] = m['mp_cooccurrence'] <= 2
            m.update(res.get(m['rank'], {}))
            m['first_failed_bar'] = 'pool: novelty' if not m['novel'] else (None if m.get('bar1') else 'bar 1: pattern similarity (N_q < 50)')
            f.write(json.dumps(m) + '\n')
    print('bar 1 passes', {t: sum(1 for m in M if m['type'] == t and m.get('bar1')) for t in ('R', 'H')})
