"""VP1-0 step 7: compound folds for the cross-fitted choice (PREREG VP1-1), with kit/ref/folds.py, per family, before any score is read.
Compounds are the bench units of v7's runs: B1 (worlds 2000-2999) and H (4000-4999) from F/sllm/run/worlds_B1_H.txt (scenario = world // 10), T from
T/run_subsets.json worlds24 (scenario = world // 100). Formulas come from the frozen world files.  python vp1/folds_vp1.py -> vp1/folds.json"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'kit', 'ref'))
import folds as FO  # noqa: E402


def load():
    ws = [int(x) for x in open(os.path.join(HERE, 'F', 'sllm', 'run', 'worlds_B1_H.txt')).read().replace(',', ' ').split()]
    wt = json.load(open(os.path.join(HERE, 'T', 'run_subsets.json')))['worlds24']
    form = {}
    for p in ('bench/WORLDS_B1.json', 'H/WORLDS_H.json', 'T/WORLDS_T.json'):
        form.update({w['scen']: w['formula'] for w in json.load(open(os.path.join(HERE, p)))['worlds']})
    fam = dict(B1=sorted({w // 10 for w in ws if 2000 <= w < 3000}), H=sorted({w // 10 for w in ws if 4000 <= w < 5000}), T=sorted({w // 100 for w in wt}))
    worlds = dict(B1=sorted(w for w in ws if 2000 <= w < 3000), H=sorted(w for w in ws if 4000 <= w < 5000), T=sorted(wt))
    return fam, worlds, form


def main():
    fam, worlds, form = load()
    out = dict(rule="sha256('vp1|' + formula) rank; first ceil(n/2) fold 0, rest fold 1 (kit/ref/folds.py)", families={})
    for f, scens in fam.items():
        fo = FO.folds([form[s] for s in scens])
        out['families'][f] = dict(n_compounds=len(scens), n_worlds=len(worlds[f]), worlds=worlds[f],
                                  compounds=[dict(scen=s, formula=form[s], fold=fo[form[s]], rank=FO.rank_key(form[s])[:16]) for s in scens],
                                  fold_sizes=[sum(1 for v in fo.values() if v == k) for k in (0, 1)])
        assert len(fo) == len(scens), f'{f}: duplicate formulas'
    json.dump(out, open(os.path.join(HERE, 'folds.json'), 'w'), indent=1)
    print({f: (d['n_compounds'], d['n_worlds'], d['fold_sizes']) for f, d in out['families'].items()})


if __name__ == '__main__':
    main()
