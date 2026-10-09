#!/usr/bin/env python3
"""vg_mc2.py (v4.5 MC v2.1, VG; HTEM_MC2_RULES_v21.md section 3 and the prompt's VG list): the S4mc6 v2 real gate.
1 synthetic fresh seeds (FRESH_BASE, N per class): each class recovered >= 0.9, false fault flags on non-fault curves <= 0.05.
2 replicate agreement: replicate libraries (same system and recipe key) with I-V data, matched by grid index and |dx| <= s:
  valid/not-valid agreement >= 0.90 over matched positions (4-class agreement reported); < 50 matched positions -> 'insufficient'.
3 threshold sensitivity: share of positions whose valid call flips between r2 0.999, 0.995, 0.99.
4 database consistency (level A, validation only): Spearman of our Rs vs fpm_sheet_resistance on valid positions; positions we call
  fault or beyond range where the database lists a finite Rs.
Usage: vg_mc2.py [--libs cached|all]   (cached: the fully cached libraries at run time). Writes v4/htem/VG_S4MC6.json and .md."""
import json, math, os, sys
from collections import Counter, defaultdict
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_mc2 as CM, keys_mc2 as KY, iv_classes as IVC, sample_io as SIO
from scipy.stats import spearmanr
FRESH_BASE = 915300; N = 200
FN = CM.API.CFG['synth']['P1']['fpm_rel_noise'][1]


def synth(kind, r):
    amp = {'valid': [5e-8, 5e-7, 1e-6, 1e-3], 'beyond range': [1e-9, 5e-9, 1e-8, 2e-8]}.get(kind, [5e-8, 1e-6])
    I = np.array([-1, -0.5, 0, 0.5, 1.0]) * r.choice(amp); Rr = 10 ** r.uniform(1, 5); V = Rr * I
    if kind == 'non-ohmic': V = V + r.uniform(0.15, 0.4) * Rr * np.max(I) * (I / np.max(I)) ** 2 * r.choice([-1, 1])
    if kind == 'fault':
        sub = r.choice(['polarity', 'zero', 'erratic', 'degenerate'])
        if sub == 'polarity': V = -V
        elif sub == 'zero': I = I * 0
        elif sub == 'erratic': V = r.normal(0, 1, V.size) * np.max(np.abs(V))
        else: I = np.array([np.nan, np.nan, 0.0, np.nan, np.nan])
    V = V + r.normal(0, FN * np.nanmax(np.abs(V)) if np.nanmax(np.abs(V)) > 0 else 1e-6, V.size)
    return I, V


def gate_synth():
    rec, ff = {}, []
    for j, kind in enumerate(IVC.CLASSES):
        hit = 0
        for k in range(N):
            r = np.random.default_rng(FRESH_BASE + 1000 * j + k); I, V = synth(kind, r); c = IVC.classify(I, V)['cls']
            hit += c == kind
            if kind != 'fault': ff.append(c == 'fault')
        rec[kind] = hit / N
    fault_rate = sum(ff) / len(ff)
    return {'recovery': rec, 'false_fault': fault_rate, 'pass': all(v >= 0.9 for v in rec.values()) and fault_rate <= 0.05}


def main():
    libs = {}
    for r in CM.ROWS:
        P = CM.positions(r['id'])
        if P is not None: libs[r['id']] = (r, P)
    cls = {}
    for lid, (r, P) in libs.items():
        for i, p in enumerate(P):
            fp = SIO.fpm(p['_s'])
            if fp: cls[(lid, i)] = {t: IVC.classify(fp['current_A'], fp['voltage_V'], t) for t in (0.999, 0.995, 0.99)}
    # 2 replicate agreement
    groups = defaultdict(list)
    for lid, (r, P) in libs.items():
        if r.get('recipe') and any((lid, i) in cls for i in range(len(P))): groups[(r['system'], r['recipe'])].append(lid)
    agree2 = agree4 = n = 0; conf = Counter(); by_split = Counter()
    for (s, rk), ids in groups.items():
        ids = sorted(ids, key=int)
        for a in range(len(ids)):
            for b in range(a + 1, len(ids)):
                A, B = libs[ids[a]][1], libs[ids[b]][1]; cat, _ = KY.comp_var(A + B)
                _, xa = KY.comp_var(A, cat) if cat else (None, None); _, xb = KY.comp_var(B, cat) if cat else (None, None)
                if cat and (xa is None or xb is None): continue   # VM-E05: a library without XRF composition cannot be matched
                sa = KY.comp_step(A, xa) if xa else None; sb = KY.comp_step(B, xb) if xb else None; st = max(sa or 0, sb or 0)
                for i in range(min(len(A), len(B))):
                    if (ids[a], i) not in cls or (ids[b], i) not in cls: continue
                    if cat and (xa[i] is None or xb[i] is None or abs(xa[i] - xb[i]) > st): continue
                    ca, cb = cls[(ids[a], i)][0.999], cls[(ids[b], i)][0.999]; n += 1
                    agree2 += ca['valid'] == cb['valid']; agree4 += ca['cls'] == cb['cls']; conf[(ca['cls'], cb['cls'])] += 1
                    by_split[CM.SPL.get(ids[a], {}).get('split')] += 1
    rep = {'matched_positions': n, 'groups': sum(1 for v in groups.values() if len(v) >= 2), 'agree_valid': agree2 / n if n else None,
           'agree_4class': agree4 / n if n else None, 'confusion': {f'{a}|{b}': v for (a, b), v in conf.items()}, 'by_split_of_first': dict(by_split),
           'status': 'insufficient (< 50 matched positions)' if n < 50 else ('pass' if agree2 / n >= 0.9 else 'fail')}
    # 3 sensitivity
    flips = {k: sum(c[0.999]['valid'] != c[k]['valid'] for c in cls.values()) / len(cls) for k in (0.995, 0.99)}
    # 4 database consistency
    ours, db = [], []; trap = Counter()
    for (lid, i), c in cls.items():
        s = libs[lid][1][i]['_s']; v = s.get('fpm_sheet_resistance')
        try: v = float(v)
        except (TypeError, ValueError): v = None
        fin = v is not None and math.isfinite(v) and v > 0
        if c[0.999]['valid'] and fin: ours.append(KY.GF * c[0.999]['R']); db.append(v)
        if c[0.999]['cls'] in ('fault', 'beyond range') and fin: trap[c[0.999]['cls']] += 1
    rho = float(spearmanr(ours, db).correlation) if len(ours) >= 3 else None
    classes = Counter(c[0.999]['cls'] for c in cls.values()); why = Counter(c[0.999]['why'] for c in cls.values() if c[0.999]['cls'] == 'fault')
    syn = gate_synth()
    out = {'fresh_base': FRESH_BASE, 'n_per_class': N, 'libraries': len(libs), 'positions_with_iv': len(cls), 'classes': dict(classes), 'fault_why': dict(why),
           'synthetic': syn, 'replicate': rep, 'flip_share': flips, 'db': {'spearman_valid': rho, 'n_valid_with_db': len(ours), 'trap_db_finite': dict(trap)},
           'VG': 'pass' if syn['pass'] and rep['status'] == 'pass' else ('pending (replicates insufficient)' if syn['pass'] and rep['status'].startswith('insufficient') else 'fail')}
    json.dump(out, open(os.path.join(CM.HERE, 'VG_S4MC6.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
