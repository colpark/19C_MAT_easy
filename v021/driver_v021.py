#!/usr/bin/env python3
"""driver_v021.py: PanelBench v0.21 = the v0.2 pipeline (MinerU -> mineru_paras.py -> frozen v0.1 item rules)
on the 869 harvested open-access papers. The frozen files are copied byte-identical into work/ and never edited.

Only two things differ from the six-paper v0.2 run, both outside the frozen files:
  1. Paper list. levels.py/open.py read the paper set from the globals KEYS and NL5. Here KEYS maps each paper
     key (P0001...) to its own folder under nl5_v021/, which links to that paper's MatMech panel store.
  2. Nano Letters handling journal-wide (owner decision 2026-10-01). Rules C1 (levels.py) and M6/M7
     (mineru_paras.py) are stated for the journal, but the code tests key == 'Xu17'. For every Nano Letters
     paper the driver passes the key 'Xu17' to exactly those code paths (mineru_paras.run, eligible), so the
     frozen Nano Letters branch runs unchanged, and then restores the real paper key.

Subcommands: setup | convert | items | stats. Prints counts only; no extracted text is shown.
"""
import collections, hashlib, importlib.util, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, 'work')
FROZEN = {'levels.py': '7477c0bbdf798157', 'open.py': '9d4e3683b9afacec', 'mineru_paras.py': '7989ad0321104366'}
KIT = os.path.expanduser('~/Documents/harbor/v02/work')
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]

def papers():
    L = json.load(open(os.path.join(HERE, 'papers_all.json')))
    L.sort(key=lambda p: p['doi'].lower())
    for i, p in enumerate(L, 1):
        p['key'] = 'P%04d' % i
    return L

def setup():
    os.makedirs(WORK, exist_ok=True)
    for f, h in FROZEN.items():
        assert sha(os.path.join(KIT, f)) == h, f'kit {f} hash changed'
        shutil.copy(os.path.join(KIT, f), os.path.join(WORK, f))
        assert sha(os.path.join(WORK, f)) == h
    L = papers()
    json.dump({p['key']: {k: p[k] for k in ('doi', 'journal', 'year', 'safe', 'matmech_folder')} for p in L},
              open(os.path.join(HERE, 'paper_keys.json'), 'w'), indent=1)
    nl5 = os.path.join(HERE, 'nl5_v021')
    for p in L:
        d = os.path.join(nl5, p['key']); os.makedirs(d, exist_ok=True)
        link = os.path.join(d, os.path.basename(p['matmech_folder']))
        if not os.path.islink(link): os.symlink(p['matmech_folder'], link)
    print('setup: frozen files copied and hash-checked', FROZEN, '| papers', len(L), '| panel-store links', len(os.listdir(nl5)))

def convert():
    spec = importlib.util.spec_from_file_location('mineru_paras', os.path.join(WORK, 'mineru_paras.py'))
    mp = importlib.util.module_from_spec(spec); spec.loader.exec_module(mp)
    c, missing = collections.Counter(), []
    for p in papers():
        cl = os.path.join(HERE, 'mineru_out', p['safe'], 'auto', p['safe'] + '_content_list.json')
        out = os.path.join(WORK, p['key'] + '.paras.json')
        if not os.path.exists(cl): missing.append(p['key']); continue
        rule_key = 'Xu17' if p['journal'] == 'Nano_Letters' else p['key']
        devnull = open(os.devnull, 'w'); so = sys.stdout; sys.stdout = devnull   # mineru_paras prints a count line
        try: mp.run(rule_key, cl, out, '2.7.6')
        finally: sys.stdout = so
        d = json.load(open(out)); d['key'] = p['key']; d['rule_key'] = rule_key; d['doi'] = p['doi']
        json.dump(d, open(out, 'w'), ensure_ascii=False)
        c['converted'] += 1; c['nano_letters_rules'] += rule_key == 'Xu17'
    print('convert:', dict(c), '| no MinerU output yet:', len(missing))

def items():
    os.chdir(WORK)
    g = {'__name__': 'v021'}
    exec(open('open.py').read().rsplit("\nif __name__ ==", 1)[0], g)   # open.py itself exec's levels.py (frozen)
    K = json.load(open(os.path.join(HERE, 'paper_keys.json')))
    have = [k for k in sorted(K) if os.path.exists(k + '.paras.json')]
    g['KEYS'] = {k: k for k in have}; g['NL5'] = os.path.join(HERE, 'nl5_v021')
    frozen_eligible = g['eligible']
    g['eligible'] = lambda paras, key: frozen_eligible(paras, 'Xu17' if K[key]['journal'] == 'Nano_Letters' else key)
    allit, err = [], {}
    for k in have:
        try: allit += g['build'](k)
        except Exception as e: err[k] = repr(e)[:200]
    c = {1: 0, 2: 0, 3: 0}
    for it in allit:
        c[it['level']] += 1; it['id'] = 'V%d-%04d' % (it['level'], c[it['level']])
        it['doi'] = K[it['paper']]['doi']; it['journal'] = K[it['paper']]['journal']; it['hand_label'] = 'unreviewed'
    json.dump({'rules': g['__doc__'], 'items': allit}, open(os.path.join(HERE, 'open_items_v021.json'), 'w'), indent=1, ensure_ascii=False)
    json.dump(err, open(os.path.join(HERE, 'item_errors.json'), 'w'), indent=1)
    print('items: papers', len(have), '| errors', len(err), '| L1', c[1], 'L2', c[2], 'L3', c[3],
          '| L1 number', sum(1 for i in allit if i.get('type') == 'number'))

def stats():
    K = json.load(open(os.path.join(HERE, 'paper_keys.json')))
    its = json.load(open(os.path.join(HERE, 'open_items_v021.json')))['items']
    per = collections.defaultdict(collections.Counter)
    for it in its: per[K[it['paper']]['journal']]['L%d' % it['level']] += 1
    words, paras, n = collections.Counter(), collections.Counter(), collections.Counter()
    for k, v in K.items():
        p = os.path.join(WORK, k + '.paras.json')
        if not os.path.exists(p): continue
        P = json.load(open(p))['paras']; j = v['journal']
        n[j] += 1; paras[j] += len(P); words[j] += sum(len(x['text'].split()) for x in P)
    print('| journal | papers | paras/paper | words/paper | L1 | L2 | L3 |\n|---|---|---|---|---|---|---|')
    for j in sorted(n, key=lambda j: -n[j]):
        print(f"| {j} | {n[j]} | {paras[j] / n[j]:.0f} | {words[j] / n[j]:.0f} | {per[j]['L1']} | {per[j]['L2']} | {per[j]['L3']} |")

if __name__ == '__main__':
    {'setup': setup, 'convert': convert, 'items': items, 'stats': stats}[sys.argv[1]]()
