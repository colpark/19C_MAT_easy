"""V7-3: family H frame, bars and takes (truth, physics and heuristics only; no FM call, no LLM).
Frame: the novel formulas of v6/exemplar/features/s1.jsonl (R and H records, one per formula; every polymorph with its WBM MP2020 formation
energy and hull distance), excluding the v5 stage 4b dev formulas (pool4b dev flag), every B1-built compound (v6/bench/WORLDS_B1.json) and
every T compound (v7/T/WORLDS_T.json), in hash order (rank).
Twin pair per formula: twin A hull <= 0.03 eV/atom (claim true), twin B hull >= 0.07 (false).
  type M  a lower polymorph exists: A = the lowest-energy polymorph with hull <= 0.03 that is not the formula's lowest, so the formula needs
          two polymorphs with hull <= 0.03 (the lowest polymorph always has the lowest hull distance); assigned whenever possible (M is scarce)
  type E  A = the formula's lowest polymorph
  B = the lowest-energy polymorph with hull >= 0.07
Bars as V6-8 (bench/select_b1.py functions: every polymorph is the other side of each twin): N_q >= 1.5 (bisection), N = 0.7 N_q, the
cheapest decisive plan 18-108 min on the dearer twin and <= 108 on both, diversity (anonymous formula and structure-type pair).
Labels: the stage 4b H panel (mcenv/heuristics4b.py, claim H): K if it fails the pair, E if it resolves it; the oracle R-rank baseline
("SUPPORTED iff the sample is the library's lowest polymorph", DFT) resolves the pair or not.
Takes: every M survivor (at most 12), then E survivors up to 24 takes in all, plus 6 reserves per type, in hash order.
  python v7/H/select_H.py OUT_DIR"""
import os, sys
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); V7 = os.path.join(HERE, '..'); V6 = os.path.join(V7, '..', 'v6')
sys.path.insert(0, V7); sys.path.insert(0, os.path.join(V6, 'bench'))
import json, time
from multiprocessing import get_context
import select_b1 as SB

NQ_MIN, SET, LO, HI = 1.5, 0.7, 18.0, 108.0
M_MAX, TAKES, RES = 12, 24, 6


def pair(m):
    es = sorted(m['entries'], key=lambda e: e['e_form'])
    lows = [e for e in es if e['e_hull'] <= 0.03]; highs = [e for e in es if e['e_hull'] >= 0.07]
    if not lows or not highs: return None
    b = highs[0]
    if len(lows) >= 2: return dict(type='M', a=lows[1], b=b)
    return dict(type='E', a=lows[0], b=b)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    M = [json.loads(l) for l in open(os.path.join(V6, 'exemplar', 'features', 's1.jsonl'))]
    pool = json.load(open(os.path.join(V7, 'data', 'stage4b', 'pool4b.json')))
    dev = {f for f, v in pool.items() if v.get('dev')}
    b1 = {w['formula'] for w in json.load(open(os.path.join(V6, 'bench', 'WORLDS_B1.json')))['worlds']}
    tt = {w['formula'] for w in json.load(open(os.path.join(V7, 'T', 'WORLDS_T.json')))['worlds']}
    byf = {}
    for m in M:
        if m.get('novel'): byf.setdefault(m['formula'], m)
    funnel = dict(novel_formulas=len(byf), excluded_dev=0, excluded_B1=0, excluded_T=0, no_twin_pair=0)
    F = []
    for f, m in byf.items():
        if f in dev: funnel['excluded_dev'] += 1; continue
        if f in b1: funnel['excluded_B1'] += 1; continue
        if f in tt: funnel['excluded_T'] += 1; continue
        p = pair(m)
        if p is None: funnel['no_twin_pair'] += 1; continue
        F.append(dict(m, a=p['a'], b=p['b'], htype=p['type']))
    F.sort(key=lambda m: m['rank'])
    funnel['frame'] = len(F); funnel['frame_E'] = sum(m['htype'] == 'E' for m in F); funnel['frame_M'] = sum(m['htype'] == 'M' for m in F)
    print(funnel, flush=True)
    nqp = os.path.join(out, 'nq_H.json')
    if os.path.exists(nqp): nqs = {r: tuple(v) for r, v in json.load(open(nqp)).items()}
    else:
        with get_context('spawn').Pool(18) as p: nqs = {r: (n, e) for r, n, e in p.imap_unordered(SB.nq, F, chunksize=1)}
        json.dump(nqs, open(nqp, 'w'))
    from mcenv import heuristics4b as Hh
    from mcenv import stage2 as S2
    Dh = Hh.Data(); log = []; seen = set(); surv = {'E': [], 'M': []}
    for m in F:
        n, err = nqs[m['rank']]
        rec = dict(rank=m['rank'], formula=m['formula'], type=m['htype'], a=m['a']['id'], b=m['b']['id'], n_polymorphs=len(m['entries']),
                   hull_a=m['a']['e_hull'], hull_b=m['b']['e_hull'], keys=[m['a']['key'], m['b']['key']], N_q=n, error=err)
        log.append(rec)
        if n is None or n < NQ_MIN: rec['first_failed_bar'] = 'quiet limit (N_q < 1.5)'; continue
        N = round(SET * n, 4); rec['N'] = N
        idn = SB.ident(m, N); rec['ident'] = idn
        if not idn['ok']: rec['first_failed_bar'] = 'identification cost'; continue
        div = (m['entries'][0]['key'].split('|')[0], tuple(sorted(rec['keys'])))
        if div in seen: rec['first_failed_bar'] = 'diversity'; continue
        seen.add(div)
        st = {e['id']: S2.wbm(e['id']) for e in m['entries']}
        pa, pb = Hh.panel(Dh, 'H', m['formula'], st, m['a']['id']), Hh.panel(Dh, 'H', m['formula'], st, m['b']['id'])
        fails = pa['verdict'] is not True or pb['verdict'] is not False
        low = min(m['entries'], key=lambda e: e['e_form'])['id']
        rec['panel'] = dict(a=pa['verdict'], b=pb['verdict'], fails=fails, stratum='K' if fails else 'E')
        rec['rank_baseline_resolves'] = (m['a']['id'] == low) and (m['b']['id'] != low)
        rec['survivor'] = True; surv[m['htype']].append(rec)
        print(m['htype'], len(surv[m['htype']]), m['formula'], 'N_q', n, 'costs', idn['costs'], 'panel', rec['panel']['stratum'], flush=True)
        json.dump(dict(funnel=funnel, log=log), open(os.path.join(out, 'selection_H.json'), 'w'), indent=1, default=str)
    takes_M = surv['M'][:M_MAX]; takes_E = surv['E'][:TAKES - len(takes_M)]
    res_M = surv['M'][M_MAX:M_MAX + RES]; res_E = surv['E'][len(takes_E):len(takes_E) + RES]
    for r in takes_M + takes_E: r['slot'] = 'take'
    for r in res_M + res_E: r['slot'] = 'reserve'
    gate = dict(E_survivors=len(surv['E']), M_survivors=len(surv['M']), passes=len(surv['E']) >= 16 and len(surv['M']) >= 5)
    json.dump(dict(funnel=funnel, log=log, takes=takes_M + takes_E, reserves=res_M + res_E, gate_H_supply=gate),
              open(os.path.join(out, 'selection_H.json'), 'w'), indent=1, default=str)
    print('gate H-supply', gate, 'takes', len(takes_M), 'M', len(takes_E), 'E', flush=True)


if __name__ == '__main__':
    main()
