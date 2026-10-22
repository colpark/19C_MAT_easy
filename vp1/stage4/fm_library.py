"""Stage 4 FM on the library (V5_SPEC I.12), after the V5-23 freeze: MACE-MP-0 relax (mcenv.fm_service.relax) of every library structure
in stage4/library_structures.json. Node A2, MACE venv.
  python stage4/fm_library.py OUT.json"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from mcenv.fm_service import relax

if __name__ == '__main__':
    L = json.load(open(os.path.join(HERE, 'library_structures.json'))); out = {}
    for mid, sd in sorted(L.items()):
        out[mid] = relax(sd); print(mid, out[mid]['energy_per_atom'], out[mid]['steps'], out[mid]['converged'], flush=True)
    json.dump(out, open(sys.argv[1], 'w'))
    print('done', len(out))
