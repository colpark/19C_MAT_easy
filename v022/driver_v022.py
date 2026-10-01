#!/usr/bin/env python3
"""driver_v022.py: PanelBench v0.22 = the v0.2 pipeline on 94 published Acta Materialia PDFs (v02/mat94.zip).

MinerU 2.7.6 -> mineru_paras.py -> frozen v0.1 item rules (levels.py, open.py copied byte-identical, hash-checked),
run against two panel stores:
  matmech  the MatMech panel store of each paper (published figures, same version as these PDFs)
  mineru   a store built from MinerU's own figures (v021/pilot/build_mineru_store.py, rules R1-R6) and run through
           the unchanged causalmat detect_panels.py / ocr_panels.py / match_panels.py
Subcommands: setup | convert | store | items <matmech|mineru>. Prints counts only.
"""
import collections, hashlib, importlib.util, json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.join(HERE, os.environ.get('RULES_DIR', 'work'))
SUFFIX = os.environ.get('ITEMS_SUFFIX', '')   # rules revision tag, e.g. _r1 with RULES_DIR=work_r1
FROZEN = {'levels.py': '7477c0bbdf798157', 'open.py': '9d4e3683b9afacec', 'mineru_paras.py': '7989ad0321104366'}
KIT = os.path.expanduser('~/Documents/harbor/v02/work')
PANELS = os.path.expanduser('~/Documents/causalmat/scripts/panels'); PY = os.path.expanduser('~/panels/.venv/bin/python')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
def K(): return json.load(open(os.path.join(HERE, 'paper_keys.json')))

def setup():
    os.makedirs(WORK, exist_ok=True)
    for f, h in FROZEN.items():
        assert sha(os.path.join(KIT, f)) == h; shutil.copy(os.path.join(KIT, f), WORK); assert sha(os.path.join(WORK, f)) == h
    R = json.load(open(os.path.join(HERE, 'papers_v022.json')))
    keys = {r['key']: {'doi': r['doi'], 'journal': 'Acta_Materialia', 'safe': r['safe'], 'matmech_folder': r['matmech_folder'],
                       'file': r['file'], 'pages': r['pages'], 'sha256': r['sha256']} for r in R}
    json.dump(keys, open(os.path.join(HERE, 'paper_keys.json'), 'w'), indent=1)
    for k, v in keys.items():
        d = os.path.join(HERE, 'nl5_matmech', k); os.makedirs(d, exist_ok=True)
        l = os.path.join(d, os.path.basename(v['matmech_folder']))
        if not os.path.islink(l): os.symlink(v['matmech_folder'], l)
    print('setup: frozen files hash-checked', FROZEN, '| papers', len(keys))

def convert():
    spec = importlib.util.spec_from_file_location('mp', os.path.join(WORK, 'mineru_paras.py'))
    mp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mp); c = collections.Counter()
    for k, v in K().items():
        cl = os.path.join(HERE, 'mineru_out', v['safe'], 'auto', v['safe'] + '_content_list.json')
        if not os.path.exists(cl): c['missing'] += 1; continue
        so = sys.stdout; sys.stdout = open(os.devnull, 'w')
        try: mp.run(k, cl, os.path.join(WORK, k + '.paras.json'), '2.7.6')
        finally: sys.stdout = so
        c['converted'] += 1
    print('convert:', dict(c))

def store():
    keys = K(); pilot = os.path.expanduser('~/Documents/harbor/v021/pilot/build_mineru_store.py')
    json.dump(sorted(keys), open(os.path.join(HERE, 'store_keys.json'), 'w'))
    subprocess.run([PY, pilot, os.path.join(HERE, 'paper_keys.json'), os.path.join(HERE, 'mineru_out'),
                    os.path.join(HERE, 'store'), os.path.join(HERE, 'store_keys.json')], check=True)
    env = dict(os.environ, OCR_CUDA='0')   # onnxruntime in ~/panels/.venv has no CUDA provider on host A
    for script, extra in (('detect_panels.py', []), ('ocr_panels.py', ['--procs', '16']), ('match_panels.py', ['--ocr', '--workers', '8'])):
        r = subprocess.run([PY, os.path.join(PANELS, script), '--root', os.path.join(HERE, 'store'),
                            '--out-dir', os.path.join(HERE, 'panel_runs', script[:-3])] + extra, env=env, capture_output=True, text=True)
        print(script, 'exit', r.returncode, '|', [l for l in r.stdout.splitlines() if 'DONE' in l or '"figures"' in l][-1:])
    for k, v in keys.items():
        d = os.path.join(HERE, 'nl5_mineru', k); os.makedirs(d, exist_ok=True)
        l = os.path.join(d, k)
        if not os.path.islink(l): os.symlink(os.path.join(HERE, 'store', 'Acta_Materialia', k), l)

def items(which):
    keys = K(); os.chdir(WORK); g = {'__name__': 'v022'}
    exec(open('open.py').read().rsplit("\nif __name__ ==", 1)[0], g)
    have = [k for k in sorted(keys) if os.path.exists(k + '.paras.json')]
    g['KEYS'] = {k: k for k in have}; g['NL5'] = os.path.join(HERE, 'nl5_' + which)
    allit, err = [], {}
    for k in have:
        try: allit += g['build'](k)
        except Exception as e: err[k] = repr(e)[:200]
    c = {1: 0, 2: 0, 3: 0}
    for it in allit:
        c[it['level']] += 1; it['id'] = 'W%d-%03d' % (it['level'], c[it['level']]); it['doi'] = keys[it['paper']]['doi']
        it['panel_store'] = which; it['hand_label'] = 'unreviewed'; it['rules'] = 'r1' if SUFFIX == '_r1' else 'frozen v3.2'
    json.dump({'rules': g['__doc__'], 'items': allit}, open(os.path.join(HERE, f'open_items_{which}{SUFFIX}.json'), 'w'), indent=1, ensure_ascii=False)
    print(f'items ({which} store, rules {os.path.basename(WORK)}): papers {len(have)} | errors {len(err)} {list(err.items())[:2]} | L1 {c[1]} L2 {c[2]} L3 {c[3]}')

if __name__ == '__main__':
    cmd = sys.argv[1]
    {'setup': setup, 'convert': convert, 'store': store}[cmd]() if cmd != 'items' else items(sys.argv[2])
