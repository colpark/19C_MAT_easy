#!/usr/bin/env python3
"""co2_mc2.py (v4.5 MC v2.2, CO2; HTEM_MC2_RULES_v22.md section 5).
plan: systems with >= 2 XRD+XRF libraries over all multimodal libraries (F2 makes every one cached) that CO1 did not cover; their
      element subsets (size 1-3) not already searched by CO1; request count.
fetch: CO1 query and keep rules for the new subsets; CIFs of new kept (formula, space group) entries; cap 1,000 COD requests (stop).
sticks: all CO1 + CO2 phases with sticks (pymatgen, 1.5418 A, 19-52 deg), per-phase CO2 attributes (elements, anion set,
      charge balance by Composition.oxi_state_guesses), L4 pairs (CO1 pair rule) -> $HTEM_HOST/refs/sticks_mc22.json.
The per-library CO2 filter (admissible) is applied in census_mc22.py."""
import hashlib, itertools, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, co1_mc2 as C1
ANIONS = {'O', 'N', 'S', 'Se', 'Te'}
NONMETAL = {'O', 'N', 'S', 'Se', 'Te', 'H', 'F', 'Cl', 'C', 'P'}


def systems_all():
    cnt = {}
    for r in CM.ROWS:
        if int(float(r.get('has_xrd') or 0)) >= 10 and int(float(r.get('has_xrf') or 0)) >= 10: cnt[r['system']] = cnt.get(r['system'], 0) + 1
    return sorted(s for s, n in cnt.items() if n >= 2)


def plan():
    log1 = json.load(open(os.path.join(C1.OUT, 'co1_log.json'))); old = set(log1['systems'])
    new = [s for s in systems_all() if s not in old]
    done = {tuple(k.split('-')) for k in log1['searches']}
    sub = [s for s in C1.subsets(new) if s not in done]
    return new, sub


def fetch():
    new, sub = plan(); print(len(new), 'new systems;', len(sub), 'new searches')
    c = CM.API.Client(); c.t['max_requests'] = C1.LIMIT; log = {'systems': new, 'subsets': len(sub), 'searches': {}}
    if len(sub) > C1.LIMIT: raise SystemExit('plan exceeds cap: stop and report')
    best = {}
    for s in sub:
        p = os.path.join(C1.OUT, 'search_' + '_'.join(s) + '.json')
        if not os.path.exists(p):
            q = '&'.join(f'el{i + 1}={e}' for i, e in enumerate(s)); body, _ = c._get(C1.SEARCH.format(q, n=len(s))); open(p, 'wb').write(body)
        try: E = json.load(open(p))
        except ValueError: E = []
        E = E if isinstance(E, list) else []
        for e in E:
            if not C1.keep(e): continue
            try:
                from pymatgen.core import Composition
                f = Composition(' '.join((e.get('formula') or '').strip('- ').split())).reduced_formula
            except Exception: continue
            key = (f, str(e.get('sgNumber'))); R = C1.fnum(e.get('Robs')) or C1.fnum(e.get('Rall')); R = R if R is not None else math.inf
            cand = (R, int(e['file']))
            if key not in best or cand < best[key][0]: best[key] = (cand, e, s)
        log['searches']['-'.join(s)] = len(E)
    old = {(p['formula'], p['sg']) for p in json.load(open(os.path.join(CM.HERE, 'REF_PHASES_mc21.json')))}
    need = [(k, v) for k, v in sorted(best.items(), key=lambda kv: kv[1][0][1]) if k not in old]
    if c.n_requests + sum(1 for _, (cand, _, _) in need if not os.path.exists(os.path.join(C1.OUT, f'{cand[1]}.cif'))) > C1.LIMIT:
        json.dump(log, open(os.path.join(C1.OUT, 'co2_log.json'), 'w'), indent=1); raise SystemExit('CIF plan exceeds cap: stop and report')
    ref = []
    for (f, sg), (cand, e, s) in need:
        p = os.path.join(C1.OUT, f'{cand[1]}.cif')
        if not os.path.exists(p):
            body, _ = c._get(C1.CIF.format(cand[1]))
            if not body.lstrip().startswith((b'#', b'data_')): continue
            open(p, 'wb').write(body)
        ref.append({'cod_id': cand[1], 'formula': f, 'sg': sg, 'R': None if math.isinf(cand[0]) else cand[0], 'elements': list(s),
                    'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()})
    log['requests'] = c.n_requests; log['new_phases'] = len(ref)
    json.dump(ref, open(os.path.join(CM.HERE, 'REF_PHASES_mc22_new.json'), 'w'), indent=1)
    json.dump(log, open(os.path.join(C1.OUT, 'co2_log.json'), 'w'), indent=1)
    print(len(ref), 'new phases; COD requests', c.n_requests)


def sticks():
    from pymatgen.core import Structure, Composition
    from pymatgen.analysis.diffraction.xrd import XRDCalculator
    from pymatgen.analysis.structure_matcher import StructureMatcher, FrameworkComparator
    import warnings; warnings.filterwarnings('ignore')
    calc = XRDCalculator(wavelength=CM.API.CFG['readers']['xrd']['wavelength_A'])
    ref = json.load(open(os.path.join(CM.HERE, 'REF_PHASES_mc21.json')))
    pn = os.path.join(CM.HERE, 'REF_PHASES_mc22_new.json'); ref += json.load(open(pn)) if os.path.exists(pn) else []
    out, st, bad = [], {}, []
    for ph in ref:
        try:
            S = Structure.from_file(os.path.join(C1.OUT, f"{ph['cod_id']}.cif")); pat = calc.get_pattern(S, two_theta_range=(19.0, 52.0))
        except Exception as e:
            bad.append({'cod': ph['cod_id'], 'why': f'parse: {type(e).__name__}'}); continue
        comp = S.composition.reduced_composition; els = sorted(str(e) for e in comp.elements)
        try: cb = len(Composition(ph['formula']).oxi_state_guesses()) > 0
        except Exception: cb = False
        st[ph['cod_id']] = S; L = S.lattice
        out.append({'phase': f"{ph['formula']} sg{ph['sg']} COD {ph['cod_id']}", 'cod_id': ph['cod_id'], 'formula': ph['formula'], 'sg': ph['sg'],
                    'elements': els, 'anions': sorted(set(els) & ANIONS), 'nonmetals': sorted(set(els) & NONMETAL), 'charge_balanced': cb,
                    'cubic': L.is_orthogonal and abs(L.a - L.b) < 1e-3 and abs(L.a - L.c) < 1e-3,
                    'lattice': {'a': L.a, 'b': L.b, 'c': L.c, 'alpha': L.alpha, 'beta': L.beta, 'gamma': L.gamma},
                    'sticks': [[float(t), float(i), [list(h['hkl']) for h in hk]] for t, i, hk in zip(pat.x, pat.y, pat.hkls)]})
    sm = StructureMatcher(comparator=FrameworkComparator()); pairs = []
    for a, b in itertools.combinations(out, 2):
        if a['sg'] != b['sg']: continue
        ca, cb_ = C1.CM_comp(a['formula']), C1.CM_comp(b['formula'])
        if set(ca) == set(cb_) or len(ca) != len(cb_): continue
        da = {e: n for e, n in ca.items() if cb_.get(e) != n}; db = {e: n for e, n in cb_.items() if ca.get(e) != n}
        if len(da) != 1 or len(db) != 1 or list(da.values()) != list(db.values()): continue
        if not sm.fit(st[a['cod_id']], st[b['cod_id']]): continue
        pairs.append({'A': list(da)[0], 'B': list(db)[0], 'phase_A': a['phase'], 'phase_B': b['phase'], 'ids': sorted([a['cod_id'], b['cod_id']])})
    json.dump({'phases': out, 'l4_pairs': pairs, 'dropped': bad}, open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc22.json'), 'w'), indent=1)
    print(len(out), 'phases;', len(pairs), 'L4 pairs;', len(bad), 'dropped;', sum(p['charge_balanced'] for p in out), 'charge balanced')


def admissible(ph, system):
    """CO2 filter for one library of `system` (rules v22 section 5)."""
    el = set(system.split('-')); an = el & ANIONS; pe = set(ph['elements'])
    if not pe <= el: return False
    if an:
        return bool(pe & an) and bool(pe - ANIONS) and len(pe) >= 2 and ph['charge_balanced']
    return not (pe & NONMETAL)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'plan'
    if cmd == 'plan':
        n, s = plan(); print(len(n), 'new systems', n, len(s), 'new searches')
    else:
        {'fetch': fetch, 'sticks': sticks}[cmd]()
