#!/usr/bin/env python3
"""co1_mc2.py (v4.5 MC v2.1, CO1; HTEM_MC2_RULES_v21.md section 5): COD reference phases for L4 and L6.
plan: systems with >= 2 XRD+XRF libraries (fully cached or F1), element subsets of size 1-3, request count.
fetch: searches (strictmin = strictmax = |subset|, JSON), keep rule, CIFs of kept entries; total COD requests <= 1,000 (stop if the plan
exceeds it). sticks: pymatgen XRDCalculator at 1.5418 A, 19-52 deg; L4 pairs (same space group, StructureMatcher ignore_species,
one substituting pair at equal multiplicity). Writes v4/htem/REF_PHASES_mc21.json, $HTEM_HOST/refs/sticks_mc21.json, the search
cache under $HTEM_HOST/refs/cod_mc21/ and the log $HTEM_HOST/refs/cod_mc21/co1_log.json."""
import hashlib, itertools, json, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM
OUT = os.path.join(CM.API.HOST, 'refs', 'cod_mc21'); os.makedirs(OUT, exist_ok=True)
SEARCH = 'https://www.crystallography.net/cod/result?{}&strictmin={n}&strictmax={n}&format=json'
CIF = 'https://www.crystallography.net/cod/{}.cif'
LIMIT = 1000


def systems():
    f1 = set(json.load(open(os.path.join(CM.API.HOST, 'mc', 'f1_list.json'))))
    cnt = {}
    for r in CM.ROWS:
        if int(float(r.get('has_xrd') or 0)) >= 10 and int(float(r.get('has_xrf') or 0)) >= 10 and (r['id'] in f1 or CM.fully_cached(r['id'])):
            cnt[r['system']] = cnt.get(r['system'], 0) + 1
    return sorted(s for s, n in cnt.items() if n >= 2)


def subsets(ss):
    out = set()
    for s in ss:
        el = s.split('-')
        for k in (1, 2, 3):
            for c in itertools.combinations(sorted(el), k): out.add(c)
    return sorted(out, key=lambda c: (len(c), c))


def fnum(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def keep(e):
    fl = e.get('flags') or ''
    if 'has coordinates' not in fl or 'has disorder' in fl: return False
    for k in ('celltemp', 'diffrtemp'):
        v = fnum(e.get(k))
        if v is not None and not 273 <= v <= 313: return False
    for k in ('cellpressure', 'diffrpressure'):
        v = fnum(e.get(k))
        if v is not None and v > 110: return False
    return (e.get('status') or '') != 'retracted' and not e.get('duplicateof')


def main(cmd):
    ss = systems(); sub = subsets(ss)
    if cmd == 'plan':
        print(len(ss), 'systems;', len(sub), 'searches'); print(ss); return
    c = CM.API.Client(); c.t['max_requests'] = LIMIT; log = {'systems': ss, 'subsets': len(sub), 'searches': {}, 'kept': {}, 'cif': {}, 'dropped': []}
    if len(sub) > LIMIT: raise SystemExit(f'plan {len(sub)} searches > {LIMIT}: stop and report')
    best = {}
    for s in sub:
        p = os.path.join(OUT, 'search_' + '_'.join(s) + '.json')
        if not os.path.exists(p):
            q = '&'.join(f'el{i + 1}={e}' for i, e in enumerate(s)); body, _ = c._get(SEARCH.format(q, n=len(s)))
            open(p, 'wb').write(body)
        try: E = json.load(open(p))
        except ValueError: E = []
        E = E if isinstance(E, list) else []; nk = 0
        for e in E:
            if not keep(e): continue
            try:
                from pymatgen.core import Composition
                f = Composition(' '.join((e.get('formula') or '').strip('- ').split())).reduced_formula
            except Exception: continue
            key = (f, str(e.get('sgNumber'))); R = fnum(e.get('Robs')) or fnum(e.get('Rall')); R = R if R is not None else math.inf
            cand = (R, int(e['file']))
            if key not in best or cand < best[key][0]: best[key] = (cand, e, s); nk += 1
        log['searches']['-'.join(s)] = {'entries': len(E), 'kept_updates': nk}
    need = sorted(best.items(), key=lambda kv: kv[1][0][1])
    print(len(need), 'kept (formula, space group); requests so far', c.n_requests)
    if c.n_requests + sum(1 for _, (cand, _, _) in need if not os.path.exists(os.path.join(OUT, f'{cand[1]}.cif'))) > LIMIT:
        json.dump(log, open(os.path.join(OUT, 'co1_log.json'), 'w'), indent=1, default=str)
        raise SystemExit(f'plan exceeds {LIMIT} COD requests: stop and report')
    ref = []
    for (f, sg), (cand, e, s) in need:
        p = os.path.join(OUT, f'{cand[1]}.cif')
        if not os.path.exists(p):
            body, _ = c._get(CIF.format(cand[1]))
            if not body.lstrip().startswith((b'#', b'data_')): log['dropped'].append({'cod': cand[1], 'why': 'not a CIF'}); continue
            open(p, 'wb').write(body)
        ref.append({'cod_id': cand[1], 'formula': f, 'sg': sg, 'R': None if math.isinf(cand[0]) else cand[0], 'elements': list(s),
                    'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()})
    log['requests'] = c.n_requests
    json.dump(ref, open(os.path.join(CM.HERE, 'REF_PHASES_mc21.json'), 'w'), indent=1)
    json.dump(log, open(os.path.join(OUT, 'co1_log.json'), 'w'), indent=1, default=str)
    print(len(ref), 'phases; COD requests', c.n_requests)


def sticks():
    from pymatgen.core import Structure
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.analysis.structure_matcher import StructureMatcher, FrameworkComparator
    import warnings; warnings.filterwarnings('ignore')
    calc = XRDCalculator(wavelength=CM.API.CFG['readers']['xrd']['wavelength_A']); ref = json.load(open(os.path.join(CM.HERE, 'REF_PHASES_mc21.json')))
    out, st, bad = [], {}, []
    for ph in ref:
        try:
            S = Structure.from_file(os.path.join(OUT, f"{ph['cod_id']}.cif")); pat = calc.get_pattern(S, two_theta_range=(19.0, 52.0))
        except Exception as e:
            bad.append({'cod': ph['cod_id'], 'why': f'parse: {type(e).__name__}'}); continue
        st[ph['cod_id']] = S; L = S.lattice
        out.append({'phase': f"{ph['formula']} sg{ph['sg']} COD {ph['cod_id']}", 'cod_id': ph['cod_id'], 'formula': ph['formula'], 'sg': ph['sg'],
                    'elements': sorted(S.composition.reduced_composition.as_dict()), 'cubic': L.is_orthogonal and abs(L.a - L.b) < 1e-3 and abs(L.a - L.c) < 1e-3,
                    'lattice': {'a': L.a, 'b': L.b, 'c': L.c, 'alpha': L.alpha, 'beta': L.beta, 'gamma': L.gamma},
                    'sticks': [[float(t), float(i), [list(h['hkl']) for h in hk]] for t, i, hk in zip(pat.x, pat.y, pat.hkls)]})
    sm = StructureMatcher(comparator=FrameworkComparator()); pairs = []   # species ignored (VM-E06: no ignore_species kwarg in pymatgen 2026.9.24)
    for a, b in itertools.combinations(out, 2):
        if a['sg'] != b['sg']: continue
        ca = CM_comp(a['formula']); cb = CM_comp(b['formula'])
        if set(ca) == set(cb) or len(ca) != len(cb): continue
        da = {e: n for e, n in ca.items() if cb.get(e) != n}; db = {e: n for e, n in cb.items() if ca.get(e) != n}
        if len(da) != 1 or len(db) != 1 or list(da.values()) != list(db.values()): continue
        if not sm.fit(st[a['cod_id']], st[b['cod_id']]): continue
        pairs.append({'A': list(da)[0], 'B': list(db)[0], 'phase_A': a['phase'], 'phase_B': b['phase'], 'ids': sorted([a['cod_id'], b['cod_id']])})
    json.dump({'phases': out, 'l4_pairs': pairs, 'dropped': bad}, open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc21.json'), 'w'), indent=1)
    print(len(out), 'phases with sticks;', len(pairs), 'L4 pairs;', len(bad), 'dropped')


def CM_comp(f):
    from pymatgen.core import Composition
    return {str(k): v for k, v in Composition(f).as_dict().items()}


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    sticks() if cmd == 'sticks' else main(cmd)
