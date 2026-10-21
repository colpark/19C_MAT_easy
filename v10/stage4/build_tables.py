"""Stage 4 energy-tool tables (V5_SPEC I.6, I.7, X47): stage4/ENERGY_TABLES.json = {model: {library name: {e_form, e_hull, decomposition}}}
for model dft (ceiling, dftpriced), placebo, and fm (added after the V5-23 freeze from the FM batch on node A2).
  python stage4/build_tables.py dft_placebo
  python stage4/build_tables.py fm FM_LIBRARY.json        {wbm or mp id: {energy_per_atom, structure}} from stage4/fm_library.py"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from mcenv import stage4 as F
from mcenv import energy4 as E

OUT = os.path.join(HERE, 'ENERGY_TABLES.json')


def name_map():
    S = F.install(); m = {}
    for s, d in S.items():
        for mid, n in d['names_by_id'].items(): m[n] = mid
    return m


def main():
    nm = name_map(); ids = sorted(set(nm.values()))
    T = json.load(open(OUT)) if os.path.exists(OUT) else {}
    if sys.argv[1] == 'dft_placebo':
        d = E.dft_values(ids); p = E.placebo_values(ids)
        T['dft'] = {n: d[i] for n, i in nm.items()}; T['placebo'] = {n: p[i] for n, i in nm.items()}
    else:
        fm = E.fm_values(ids, json.load(open(sys.argv[2])))
        T['fm'] = {n: fm[i] for n, i in nm.items()}
    T['ids'] = nm
    json.dump(T, open(OUT, 'w'), indent=1, sort_keys=True)
    print({k: len(v) for k, v in T.items()})


if __name__ == '__main__':
    main()
