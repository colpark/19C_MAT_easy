#!/usr/bin/env python3
"""census_mc23i.py (v4.5 MC v2.3, MV1i; HTEM_MC2_RULES_v23i.md): L4 with consensus end-member cells, the axial-ratio filter and the pinned
tag; 0 requests (cached COD search entries only). Writes $HTEM_HOST/refs/sticks_mc23i.json, v4/htem/MC23i_CENSUS.json and .md.
MC_DEV=1: dev libraries only (smoke test; writes nothing)."""
import copy, glob, json, math, os, sys
from collections import Counter, defaultdict
from itertools import combinations
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, co1_mc2 as C1, census_mc21 as M21, census_mc22 as M22, census_mc23 as C23, census_mc2 as C2M, keys_mc2 as KY
from pymatgen.core import Composition, Lattice
DEV = bool(os.environ.get('MC_DEV')); split = M22.split
CEN = json.load(open(os.path.join(CM.HERE, 'MC23_CENSUS.json')))
PAR = ('a', 'b', 'c', 'alpha', 'beta', 'gamma')


def ambient(e):
    for k in ('celltemp', 'diffrtemp'):
        v = C1.fnum(e.get(k))
        if v is not None and not 273 <= v <= 313: return False
    for k in ('cellpressure', 'diffrpressure'):
        v = C1.fnum(e.get(k))
        if v is not None and v > 110: return False
    return (e.get('status') or '') != 'retracted' and not e.get('duplicateof') and all(C1.fnum(e.get(k)) is not None for k in PAR)


def cod_entries():
    E = {}
    for f in glob.glob(os.path.join(C1.OUT, 'search_*.json')):
        try: L = json.load(open(f))
        except ValueError: continue
        for e in (L if isinstance(L, list) else []):
            if not ambient(e): continue
            try: rf = Composition(' '.join((e.get('formula') or '').strip('- ').split())).reduced_formula
            except Exception: continue
            E[int(e['file'])] = (rf, str(e.get('sgNumber')), [C1.fnum(e[k]) for k in PAR])
    return E


def hkl3(h):
    return (h[0], h[1], h[3]) if len(h) == 4 else tuple(h)


def niggli_params(params):
    N = Lattice.from_parameters(*params).get_niggli_reduced_lattice(); return N, [N.a, N.b, N.c, N.alpha, N.beta, N.gamma]


def consensus(ST):
    """VM-E11: entries are compared and medianed as Niggli-reduced cells (setting-free); an entry counts for a phase when its reduced
    cell agrees with the phase's own within 5 % per length and 3 deg per angle (same phase in any setting; other polytypes excluded).
    The median reduced cell is mapped back into the phase's own setting by the integer matrix M with L_own = M * N_own."""
    E = cod_entries(); ends = {p for pr in ST['l4_pairs'] for p in (pr['phase_A'], pr['phase_B'])}; rep = {}
    phases = []
    for p in ST['phases']:
        q = copy.deepcopy(p)
        if p['phase'] in ends:
            own = [p['lattice'][k] for k in PAR]; L0 = Lattice.from_parameters(*own); N0, n0 = niggli_params(own)
            M = np.rint(L0.matrix @ np.linalg.inv(N0.matrix))
            cand = [c for cid, (rf, sg, c) in E.items() if rf == p['formula'] and sg == str(p['sg'])]; match = []
            for c in cand:
                try: _, ne = niggli_params(c)
                except Exception: continue
                if all(abs(ne[j] / n0[j] - 1) <= 0.05 for j in range(3)) and all(abs(ne[j] - n0[j]) <= 3 for j in range(3, 6)): match.append(ne)
            if match and np.allclose(M @ N0.matrix, L0.matrix, atol=1e-3):
                med = [float(np.median([m[j] for m in match])) for j in range(6)]; L = Lattice(M @ Lattice.from_parameters(*med).matrix)
                st = []
                for t, i, hk in p['sticks']:
                    if not hk: st.append([t, i, hk]); continue
                    d = L.d_hkl(hkl3(hk[0])); st.append([2 * math.degrees(math.asin(min(1.0, KY.LAM / (2 * d)))), i, hk])
                q['sticks'] = st; q['lattice'] = {'a': L.a, 'b': L.b, 'c': L.c, 'alpha': L.alpha, 'beta': L.beta, 'gamma': L.gamma}
            shift = {k: (q['lattice'][k] - own[j]) / own[j] for j, k in enumerate(PAR[:3])}
            rep[p['phase']] = {'entries_same_formula_sg': len(cand), 'entries_matched': len(match), 'own': dict(zip(PAR, own)), 'consensus': q['lattice'],
                               'shift': shift, 'max_abs_shift': max(abs(v) for v in shift.values())}
        phases.append(q)
    return phases, rep


def axial(ST, phases):
    P = {p['phase']: p for p in phases}; keep, drop = [], []
    for pr in ST['l4_pairs']:
        a, b = P[pr['phase_A']], P[pr['phase_B']]
        if a['cubic'] and b['cubic']: keep.append(pr); continue
        ra = a['lattice']['c'] / a['lattice']['a']; rb = b['lattice']['c'] / b['lattice']['a']; d = abs(ra / rb - 1)
        (drop if d > 0.05 else keep).append({**pr, 'ca_A': ra, 'ca_B': rb, 'ca_diff': d} if d > 0.05 else pr)
    return keep, drop


def type_stats(F):
    crit, ctrl, sel = M21.mix_of(F, 'L4'); mix = crit + sel; c = len(sel) / len(mix) if mix else 0.0
    g = M21.gate_mix(mix, c); c34 = bool(mix) and all(v['pass'] for v in g.values()) and all(f['oracle'] for f in mix)
    c1 = bool(crit) and all(not f['cheap']['Vegard'] for f in crit)
    pairs = [(a, b) for a, b in combinations(mix, 2) if a['system'] == b['system']]
    c2 = sum(C2M.differ('L4', a, b) for a, b in pairs) / len(pairs) if pairs else None
    sysc = Counter(f['system'] for f in crit); eff = [f['effect'] for f in crit if f.get('effect') is not None]
    return {'decided': len(F), 'critical': len(crit), 'critical_systems': len(sysc), 'critical_by_system': dict(sysc.most_common()),
            'nsnzn_share': (sysc.get('N-Sn-Zn', 0) / len(crit)) if crit else None, 'control_available': len(ctrl), 'control_selected': len(sel),
            'control_share': c, 'critical_test': sum(f['test'] for f in crit), 'mix_test': sum(f['test'] for f in mix), 'C2': c2, 'C2_pairs': len(pairs),
            'cheap': g, 'C34': c34, 'C1_prior': c1,
            'effect': {'median': float(np.median(eff)), 'p10': float(np.percentile(eff, 10)), 'p90': float(np.percentile(eff, 90))} if eff else None,
            'includable': len(crit) >= 6 and len(sysc) >= 2 and c2 is not None and c2 >= 0.5 and c34 and c1, 'mix_ids': [f['id'] for f in mix]}


def run():
    ST = M22.ST22; phases, crep = consensus(ST); keep, drop = axial(ST, phases)
    STi = {'phases': phases, 'l4_pairs': keep, 'dropped': ST.get('dropped', []), 'axial_dropped': drop}
    save = M22.ST22; M22.ST22 = STi; F = []; lost = Counter()
    try:
        for r in CM.ROWS:
            if DEV != (split(r['id']) == 'dev'): continue
            P = CM.positions(r['id'])
            if P is None: continue
            out = C23.l4_v23(P, r['id'], r['system'])
            if out is None: lost['not eligible'] += 1
            for o in out or []:
                F.append({'id': f"{r['id']}|x0={o['x0']}", 'system': r['system'], 'libs': [r['id']], 'test': split(r['id']) == 'test', 'split': split(r['id']),
                          **{k: v for k, v in o.items() if k != 'decided'}})
    finally:
        M22.ST22 = save
    by = defaultdict(list)
    for f in F: by[f['libs'][0]].append(f)
    for lid, fs in by.items():
        for f in fs: f['pinned'] = False
        if len(fs) == 2:
            a, b = sorted(fs, key=lambda f: f['x0']); ks = (b['key'] - a['key']) / (b['x0'] - a['x0']); vs = (b['naive'] - a['naive']) / (b['x0'] - a['x0'])
            for f in fs: f['key_slope'] = ks; f['vegard_slope'] = vs; f['pinned'] = abs(ks) < abs(vs) / 3
    T = type_stats(F); T['lost'] = dict(lost); Tnp = type_stats([f for f in F if not f['pinned']])
    old = {f['id']: f for f in CEN['facts']['L4']}; new = {f['id']: f for f in F}
    flips = [{'id': i, 'MV1h': 'critical' if old[i]['critical'] else 'control', 'MV1i': 'critical' if new[i]['critical'] else 'control', 'pair': new[i]['pair'],
              'key_MV1h': old[i]['key'], 'key_MV1i': new[i]['key']} for i in sorted(set(old) & set(new)) if old[i]['critical'] != new[i]['critical']]
    gone = sorted(set(old) - set(new)); added = sorted(set(new) - set(old))
    P = {p['phase']: p for p in phases}
    snta = [{'pair': f"{d['A']}/{d['B']}", 'ca_A': d.get('ca_A'), 'ca_B': d.get('ca_B'), 'ca_diff': d.get('ca_diff')} for d in drop if {d['A'], d['B']} == {'Sn', 'Ta'}]
    for pr in keep:
        if {pr['A'], pr['B']} == {'Sn', 'Ta'}:
            a, b = P[pr['phase_A']], P[pr['phase_B']]
            if not (a['cubic'] and b['cubic']):
                ra, rb = a['lattice']['c'] / a['lattice']['a'], b['lattice']['c'] / b['lattice']['a']; snta.append({'pair': f"{pr['phase_A']} / {pr['phase_B']}", 'ca_A': ra, 'ca_B': rb, 'ca_diff': abs(ra / rb - 1)})
    used = {p for f in F + list(old.values()) for p in [f['pair']]}
    mv = {'consensus': {k: v for k, v in crep.items()}, 'shift_over_0.5pct': {k: v for k, v in crep.items() if v['max_abs_shift'] > 0.005},
          'flips': flips, 'facts_gone': gone, 'facts_added': added, 'axial_dropped_pairs': [{k: d[k] for k in ('A', 'B', 'phase_A', 'phase_B', 'ca_A', 'ca_B', 'ca_diff')} for d in drop],
          'axial_dropped_facts_MV1h': sorted(i for i in gone if any(old[i]['pair'] == f"{d['A']}/{d['B']} {d['ids']}" for d in drop)),
          'SnTa_ca': snta, 'pinned': {'facts': sum(f['pinned'] for f in F), 'critical': sum(f['pinned'] and f['critical'] for f in F),
                                      'libraries': sorted({f['libs'][0] for f in F if f['pinned']})},
          'L4_without_pinned': {k: Tnp[k] for k in ('decided', 'critical', 'critical_systems', 'C2', 'C34', 'includable', 'cheap')}}
    return STi, F, T, mv


def write(STi, F, T, mv):
    json.dump(STi, open(os.path.join(CM.API.HOST, 'refs', 'sticks_mc23i.json'), 'w'), indent=1)
    o = copy.deepcopy(CEN); o['types']['L4'] = {**T, 'section3_dropped': CEN['types']['L4']['section3_dropped']}; o['facts']['L4'] = F
    o['includable'] = [t for t in ('L8', 'L4', 'L7r') if o['types'][t]['includable']]
    o['release_label'] = ('L8 confirmed on F2; L4 re-derived after VM-E10 and L7r new, both without fresh confirmation'
                          if o['includable'] == ['L8', 'L4', 'L7r'] else f"includable: {', '.join(o['includable'])} (see MC23i_CENSUS.md)")
    o['mv1i'] = mv; o['sticks_path'] = 'refs/sticks_mc23i.json'
    o['l1_probe_statement'] = 'L1 probe: the naive answer is invalid in only 4 of 22 libraries, so it cannot carry an intention claim (diagnostic only).'
    json.dump(o, open(os.path.join(CM.HERE, 'MC23i_CENSUS.json'), 'w'), indent=1, default=lambda v: v.item() if hasattr(v, 'item') else str(v))
    t0 = CEN['types']['L4']; L = ['# MC v2.3 MV1i: L4 validity amendment (HTEM_MC2_RULES_v23i.md)', '',
         '**Disclosure:** post-hoc change on seen data; no fresh HTEM data remains. 0 requests (cached COD search entries).', '',
         f"**Includable:** {', '.join(o['includable'])}. **Release label:** {o['release_label']}.", '',
         '| L4 | MV1h | MV1i | MV1i without pinned |', '|---|---|---|---|',
         f"| critical (systems) | {t0['critical']} ({t0['critical_systems']}) | {T['critical']} ({T['critical_systems']}) | {mv['L4_without_pinned']['critical']} ({mv['L4_without_pinned']['critical_systems']}) |",
         f"| decided | {t0['decided']} | {T['decided']} | {mv['L4_without_pinned']['decided']} |",
         f"| C2 | {t0['C2']:.2f} | {T['C2']:.2f} | {mv['L4_without_pinned']['C2'] if mv['L4_without_pinned']['C2'] is None else round(mv['L4_without_pinned']['C2'], 2)} |",
         f"| Vegard k/n | {t0['cheap']['Vegard']['k']}/{t0['cheap']['Vegard']['n']} | {T['cheap']['Vegard']['k']}/{T['cheap']['Vegard']['n']} (p={T['cheap']['Vegard']['p']:.3f}) | {mv['L4_without_pinned']['cheap']['Vegard']['k']}/{mv['L4_without_pinned']['cheap']['Vegard']['n']} |",
         f"| includable | {t0['includable']} | {T['includable']} | {mv['L4_without_pinned']['includable']} |", '',
         '## 1. Consensus cells: end members shifted by more than 0.5 %', '', 'Cells compared as Niggli-reduced cells; an entry counts when its reduced cell is within 5 % per length and 3 deg per angle of the phase\'s own (VM-E11).', '', '| Phase | Entries (same formula and sg / matched) | a | b | c |', '|---|---|---|---|---|']
    for k, v in sorted(mv['shift_over_0.5pct'].items(), key=lambda kv: -kv[1]['max_abs_shift']):
        L.append(f"| {k} | {v['entries_same_formula_sg']} / {v['entries_matched']} | {v['shift']['a']:+.2%} | {v['shift']['b']:+.2%} | {v['shift']['c']:+.2%} |")
    L += ['', f"End members: {len(mv['consensus'])}; with only their own entry matched: {sum(1 for v in mv['consensus'].values() if v['entries_matched'] <= 1)}; entries of the same formula and sg not matched (other setting or polytype handled / excluded): {sum(v['entries_same_formula_sg'] - v['entries_matched'] for v in mv['consensus'].values())}.", '',
          f"**Critical/control flips against MV1h ({len(mv['flips'])}):**", ''] + [f"- {f['id']} {f['pair']}: {f['MV1h']} -> {f['MV1i']} (key {f['key_MV1h']:.4f} -> {f['key_MV1i']:.4f})" for f in mv['flips']]
    L += ['', f"**Facts gone ({len(mv['facts_gone'])}):** {mv['facts_gone']}", '', f"**Facts added ({len(mv['facts_added'])}):** {mv['facts_added']}", '',
          '## 2. Axial ratio', '', '| Pair | c/a A | c/a B | difference |', '|---|---|---|---|']
    L += [f"| {d['A']}/{d['B']} ({d['phase_A']} / {d['phase_B']}) | {d['ca_A']:.4f} | {d['ca_B']:.4f} | {d['ca_diff']:.1%} |" for d in mv['axial_dropped_pairs']]
    L += ['', f"Facts of MV1h on dropped pairs: {mv['axial_dropped_facts_MV1h']}.", '', f"**Sn/Ta (CoSn2/Ta2Co) c/a:** {mv['SnTa_ca']}", '',
          f"## 3. Pinned (report only): {mv['pinned']}", '', f"## L4 critical by pair (MV1i): {dict(Counter(f['pair'] for f in F if f['critical']))}", '',
          f"## L4 critical by system (MV1i): {T['critical_by_system']}", '', '## Probe statement', '', o['l1_probe_statement']]
    open(os.path.join(CM.HERE, 'MC23i_CENSUS.md'), 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))


if __name__ == '__main__':
    STi, F, T, mv = run()
    if DEV: print(json.dumps({'L4': {k: T[k] for k in ('decided', 'critical', 'C2', 'includable')}, 'shift>0.5%': len(mv['shift_over_0.5pct']), 'axial': len(mv['axial_dropped_pairs'])}, default=str))
    else: write(STi, F, T, mv)
