"""V10-3: a frozen v10 world (family10 install of build10 output) holds the same truth as the pilot/selection Lab (qual10.Lab) for the
same unit, N and κ: recipe D of every recipe on every twin (T: every sample sub-world) must agree to 1e-6 relative.
  V10_WORLDS=DIR V10_KAPPA=k ~/v5env/bin/python tests/test_world_equality.py"""
import json, os, sys, tempfile
for _v in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..')
sys.path.insert(0, V10); sys.path.insert(0, os.path.join(V10, 'pilot')); sys.path.insert(0, os.path.join(V10, 'graphexec'))
from mcenv import scenarios as SC
kap = float(os.environ['V10_KAPPA']) if os.environ.get('V10_KAPPA') else None
if kap is not None:
    kf = os.path.join(tempfile.mkdtemp(), 'KAPPA.json'); json.dump(dict(kappa=kap), open(kf, 'w')); SC.KAPPA_FILE = kf
from mcenv import separation as SP
from mcenv import family10 as F10
from mcenv import family7 as F7
import qual10 as Q
import recipes10 as RC


def main():
    S = F10.install(); kap_ = SC.kappa(); worst = 0.0
    for s, d in sorted(S.items()):
        W = F10.RECORDS[s]; fam = F10.FAMILY[s]
        u = dict(id=f"{fam}|{W['formula']}", family=fam, formula=W['formula'], poly_ids=W['polymorph_ids'], seed_scen=W['seed_scen'])
        if fam == 'T': u.update(L=W['L'], H=W['H']); pairs = []
        else: u.update(A=W['a'], B=W['b'])
        lab = Q.Lab(u); lab.set(W['N'], kap_)
        if fam == 'T':
            tw = {v['base_cell']: v for v in F7.T_SCEN.values() if v['scen'] == s and v['hold'] == 0}
            pairs = [(lab.sub[('L', 'pre')], tw[2]['pre']), (lab.sub[('L', 'post')], tw[2]['post']), (lab.sub[('H', 'pre')], tw[3]['pre']),
                     (lab.sub[('H', 'post')], tw[3]['post'])]
        else:
            pairs = [(Q.SID * 10 + 1, s * 10 + 1), (Q.SID * 10 + 2, s * 10 + 2)]
        for r in RC.NAMES:
            ms = Q.recipe_meas(r, lab.B)
            for wl, wb in pairs:
                a = lab.D(wl, ms); b = float(SP.separation(wb, [SP.DEFAULT] + ms))
                rel = abs(a - b) / max(1.0, abs(a)); worst = max(worst, rel)
                if rel > 1e-6: print('MISMATCH', s, fam, r, wl, wb, a, b)
        print(s, fam, W['formula'], 'checked', len(pairs) * len(RC.NAMES), 'recipe D values')
    print(f'worst relative difference {worst:.2e}'); print('WORLD EQUALITY TEST PASSED' if worst <= 1e-6 else 'WORLD EQUALITY TEST FAILED')
    sys.exit(0 if worst <= 1e-6 else 1)


if __name__ == '__main__':
    main()
