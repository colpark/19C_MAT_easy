#!/usr/bin/env python3
"""Synthetic validation of the keyed procedures (hard rule 6; PanelBench M2 raw data, R5).

Pass criteria are fixed here before any run (pre-registered, C2):
  V1 msd.py     on resolvable diffusers (expected total hops n_li x Gamma x t >= 200; revision R1, see below)
                |log10(D_est / D_true)| <= 0.15 in >= 90 % of cases and median |bias| <= 0.05 dex;
                on all diffusers with >= 20 expected hops the block SE covers the error within 3 SE in >= 80 %.
  V2 msd.py     on non-diffusers (true D <= 1e-10) D_est <= 1e-9 cm^2/s (S10 frozen reading) in 100 % of cases.
  V3 arrhenius  on the paper ladder (1000/750/600/500 K, 100/125/150/180 ps) with Ea in [0.15, 0.35] eV and
                D(1000 K) in [2e-6, 1e-4] cm^2/s: |Ea_est - Ea| <= 0.03 eV in >= 90 % of the cases whose 500 K
                run holds >= 200 expected hops, and |Ea_est - Ea| <= 3 bootstrap SD in >= 85 % of all cases.
  V4 arrhenius  T7 form (fit 1000/750/600, predict 500 K): |log10(D500_pred / D500_true)| <= 0.25 in >= 90 %.
  V5 nernst     analytic case reproduces a hand calculation to 1e-9 relative.
  V6 allen_dynes narrow Einstein peak alpha2F = (lambda w0 / 2) delta(w - w0): lambda and omega_log within 1 %.
Revision R1 (2026-10-07, before any real trajectory was read; synthetic data only, I7): the first quick run
failed V1 and V3 only where trajectories held < 1 hop per Li (D ~ 1e-7 cm^2/s in 100 ps). The V1 text had two
inconsistent resolvability clauses (D >= 1e-7 and >= 1 hop per Li per 10 ps); both are replaced by the expected
hop count, which sets the counting precision. Keys on real data additionally require D_se / D <= 0.15 (C2).
usage: validate_procedures.py OUT.json [--quick]
"""
import json, sys
import numpy as np
sys.path.insert(0, __import__('os').path.dirname(__file__))
import msd, arrhenius, nernst_einstein as ne, allen_dynes as ad, synth_md as sm


def v1_v2(quick):
    rng = np.random.default_rng(2026)
    n = 16 if quick else 60
    res, non = [], []
    for k in range(n):
        D = 10 ** rng.uniform(-7, -4)
        tp = float(rng.choice([100, 125, 150, 180]))
        dt = float(rng.choice([0.05, 0.1, 0.2]))
        nli = int(rng.choice([12, 24, 48]))
        tr = sm.trajectory(D, n_li=nli, n_host=nli, t_ps=tp, dt_ps=dt, seed=k)
        r = msd.diffusion(tr['pos'], tr['cell'], dt, tr['mask'])
        hops = nli * sm.gamma_for_D(D, 2.5) * tp
        err = np.log10(r['D'] / D)
        cover = abs(r['D'] - D) <= 3 * r['D_se'] if np.isfinite(r['D_se']) else False
        res.append({'D_true': D, 'D_est': r['D'], 'D_se': r['D_se'], 'dex': float(err), 'cover3se': bool(cover),
                    't_ps': tp, 'dt_ps': dt, 'n_li': nli, 'hops': float(hops)})
    for k in range(6 if quick else 20):
        D = 10 ** rng.uniform(-13, -10)
        tr = sm.trajectory(D, n_li=24, n_host=24, t_ps=100, dt_ps=0.1, seed=1000 + k)
        r = msd.diffusion(tr['pos'], tr['cell'], 0.1, tr['mask'])
        non.append({'D_true': D, 'D_est': r['D'], 'ok': r['D'] <= 1e-9})
    rs = [x for x in res if x['hops'] >= 200]
    dex = np.array([x['dex'] for x in rs])
    cov = [x['cover3se'] for x in res if x['hops'] >= 20]
    v1 = {'n': len(res), 'n_resolvable': len(rs), 'frac_within_0.15dex': float(np.mean(np.abs(dex) <= 0.15)),
          'median_bias_dex': float(np.median(dex)), 'n_cover': len(cov), 'frac_cover_3se': float(np.mean(cov))}
    v1['pass'] = v1['frac_within_0.15dex'] >= 0.9 and abs(v1['median_bias_dex']) <= 0.05 and v1['frac_cover_3se'] >= 0.8
    v2 = {'n': len(non), 'frac_ok': float(np.mean([x['ok'] for x in non]))}
    v2['pass'] = v2['frac_ok'] == 1.0
    return v1, v2, res, non


def v3_v4(quick):
    rng = np.random.default_rng(7)
    n = 8 if quick else 30
    rows = []
    for k in range(n):
        Ea = rng.uniform(0.15, 0.35)
        D1 = 10 ** rng.uniform(np.log10(2e-6), -4)
        ladder = sm.arrhenius_set(Ea, D1, seed=k, n_li=24, n_host=24, dt_ps=0.1)
        Ds = [msd.diffusion(t['pos'], t['cell'], t['dt_ps'], t['mask']) for t in ladder]
        T = [t['T'] for t in ladder]
        f = arrhenius.fit(T, [d['D'] for d in Ds], [d['D_se'] for d in Ds], n_boot=300)
        f3 = arrhenius.fit(T[:3], [d['D'] for d in Ds[:3]], [d['D_se'] for d in Ds[:3]], n_boot=300)
        p = arrhenius.predict(f3, 500)
        rows.append({'Ea': Ea, 'D1000': D1, 'Ea_est': f['Ea_eV'], 'Ea_err': f['Ea_eV'] - Ea, 'Ea_sd': f['Ea_sd'],
                     'hops500': 24 * sm.gamma_for_D(ladder[3]['D_true'], 2.5) * 180,
                     'D500_true': ladder[3]['D_true'], 'D500_pred': p['D'],
                     'dex500': float(np.log10(p['D'] / ladder[3]['D_true']))})
    rr = [r for r in rows if r['hops500'] >= 200]
    v3 = {'n': n, 'n_resolvable': len(rr),
          'frac_within_0.03eV': float(np.mean([abs(r['Ea_err']) <= 0.03 for r in rr])) if rr else float('nan'),
          'frac_within_3sd': float(np.mean([abs(r['Ea_err']) <= 3 * r['Ea_sd'] for r in rows])),
          'median_err_eV': float(np.median([r['Ea_err'] for r in rows]))}
    v3['pass'] = bool(rr) and v3['frac_within_0.03eV'] >= 0.9 and v3['frac_within_3sd'] >= 0.85
    v4 = {'n': n, 'frac_within_0.25dex': float(np.mean([abs(r['dex500']) <= 0.25 for r in rows]))}
    v4['pass'] = v4['frac_within_0.25dex'] >= 0.9
    return v3, v4, rows


def v5():
    # 32 Li in 1000 Å^3, D = 1e-5 cm^2/s, 600 K: sigma = N e^2 D / (V kB T) by hand
    hand = 32 * (1.602176634e-19) ** 2 * 1e-9 / (1e-27 * 1.380649e-23 * 600) * 10
    got = ne.sigma_mS_cm(32, 1000.0, 1e-5, 600)
    return {'hand_mS_cm': hand, 'got': got, 'pass': abs(got / hand - 1) < 1e-9}


def v6():
    w = np.linspace(0.01, 100, 200001)
    w0, lam, s = 30.0, 1.2, 0.3
    a2f = lam * w0 / 2 * np.exp(-0.5 * ((w - w0) / s) ** 2) / (s * np.sqrt(2 * np.pi))
    m = ad.moments(w, a2f)
    ok = abs(m['lambda'] / lam - 1) < 0.01 and abs(m['omega_log'] / w0 - 1) < 0.01
    return {'lambda': m['lambda'], 'omega_log': m['omega_log'], 'pass': bool(ok)}


def main():
    out = sys.argv[1]
    quick = '--quick' in sys.argv
    v1, v2, r1, r2 = v1_v2(quick)
    v3, v4, r3 = v3_v4(quick)
    rep = {'V1_msd': v1, 'V2_nondiff': v2, 'V3_arrhenius': v3, 'V4_t7_predict': v4, 'V5_nernst': v5(),
           'V6_allen_dynes': v6(), 'rows': {'v1': r1, 'v2': r2, 'v3': r3}, 'quick': quick}
    rep['all_pass'] = all(rep[k]['pass'] for k in ['V1_msd', 'V2_nondiff', 'V3_arrhenius', 'V4_t7_predict',
                                                    'V5_nernst', 'V6_allen_dynes'])
    json.dump(rep, open(out, 'w'), indent=1)
    for k in ['V1_msd', 'V2_nondiff', 'V3_arrhenius', 'V4_t7_predict', 'V5_nernst', 'V6_allen_dynes']:
        print(k, {a: b for a, b in rep[k].items()})
    print('ALL PASS' if rep['all_pass'] else 'FAIL')


if __name__ == '__main__':
    main()
