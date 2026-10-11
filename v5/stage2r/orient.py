"""Energy-as-verdict orientation (V5_SPEC D.4, X19): MACE-MP-0 energies of the two competing structures of the chosen 41 and 44
candidates, through the FM service. Writes stage2r/ORIENT.json; the claim names the structure MACE ranks higher in energy, so the
claim-false twin's structure is the one MACE ranks lower. These are the only FM calls before V5-10; they orient the wording only.
  V5_FM_URL=http://192.168.100.11:8770/relax python stage2r/orient.py"""
import json, os, random, sys, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from pymatgen.core import Lattice, Structure
from mcenv import stage2 as S2
from mcenv import stage2r as S2R
from mcenv.planner2r import abx, build_params

FM = os.environ.get('V5_FM_URL', 'http://192.168.100.11:8770/relax')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ORIENT.json')


def relax(st):
    req = urllib.request.Request(FM, data=json.dumps(dict(structure=st.as_dict())).encode(), headers={'Content-Type': 'application/json'})
    out = json.loads(urllib.request.urlopen(req, timeout=3600).read())
    if not out.get('ok'): raise RuntimeError(out.get('error'))
    r = out['result']; return r['energy_per_atom'], r['steps'], r['converged'], Structure.from_dict(r['structure']).lattice.abc


def sqs_fcc(A, B, a, seed=0):
    """2x2x2 conventional fcc supercell (32 sites), 24 A and 8 B placed at random (seed 0): the disordered A3B stand-in."""
    base = [[0, 0, 0], [.5, .5, 0], [.5, 0, .5], [0, .5, .5]]
    pos = [[(i + x) / 2, (j + y) / 2, (k + z) / 2] for i in range(2) for j in range(2) for k in range(2) for x, y, z in base]
    sp = [A] * 24 + [B] * 8; random.Random(seed).shuffle(sp)
    return Structure(Lattice.cubic(2 * a), sp, pos)


def main():
    sel = S2R._picks(); out = {}
    a = sel[41]; f = a['formula']; E = {}
    for p in a['protos']:
        pr = S2R.PROTO_NAME[p]; st = S2.build(pr, abx(f), build_params(pr))
        e, n, conv, abc = relax(st); E[p] = dict(energy_per_atom=e, steps=n, converged=conv, abc=abc, built_as=pr)
    hi = max(E, key=lambda p: E[p]['energy_per_atom'])
    out['41'] = dict(formula=f, ids=a['ids'], energies=E, higher=hi, lower=[p for p in E if p != hi][0],
                     note='claim names the higher-energy structure under MACE; the claim-false twin has the lower-energy one')
    e = sel[44]; st = S2.wbm(e['id']); comp = st.composition.get_el_amt_dict()
    A = max(comp, key=comp.get); B = min(comp, key=comp.get)
    ordered = S2.build('L1_2', dict(A=A, B=B), dict(S=1.0))
    eo = relax(ordered); ed = relax(sqs_fcc(A, B, ordered.lattice.a))
    E = dict(ordered=dict(energy_per_atom=eo[0], steps=eo[1], converged=eo[2], abc=eo[3]),
             disordered_sqs=dict(energy_per_atom=ed[0], steps=ed[1], converged=ed[2], abc=ed[3], cell='2x2x2 fcc, 24 A + 8 B, random seed 0'))
    hi = 'ordered' if eo[0] > ed[0] else 'disordered'
    out['44'] = dict(formula=f'{A}3{B}', id=e['id'], energies=E, higher=hi,
                     note='claim names the higher-energy state under MACE; the claim-false twin is the lower-energy state')
    json.dump(out, open(OUT, 'w'), indent=1); print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
