"""V6-2 fast path (V6-X7): MACE-MP-0 relax (mcenv.fm_service.relax) of the short-list structures. Node A2, MACE venv.
  python fm_relax.py IN.json OUT.json"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
from mcenv.fm_service import relax
if __name__ == '__main__':
    L = json.load(open(sys.argv[1])); out = {}
    for mid, sd in sorted(L.items()):
        out[mid] = relax(sd); print(mid, out[mid]['energy_per_atom'], out[mid]['converged'], flush=True)
    json.dump(out, open(sys.argv[2], 'w')); print('done', len(out))
