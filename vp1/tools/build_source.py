"""VP1-0 step 4: copy the v7 code and data vP.1 needs into vp1/ and write vp1/SOURCE.md.

Server chain: every file the deployed v7 servers carry (node A2 ~/v7srv for H and T, ~/v6srv_b1 for B1's bench/), copied from the
repository at 21fce6e55 (v7/, else v6/, else v5/, the first whose sha256 equals the deployed file). A file with no equal repository copy is
taken from the frozen repository path and listed with both hashes. Runner and analysis code are copied from v7/ (and v6/bench) unchanged.
Nothing is edited.  python vp1/tools/build_source.py  (from the worktree root)"""
import hashlib, os, shutil, subprocess, sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(REPO, 'vp1')
NODE = '192.168.100.11'
SKIP = ('tuning_runs', '/validation', 'render/', 'smoke7.py', 'CODE_SHA', '.log', '__pycache__')


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def deployed(folder, prefix=''):
    out = subprocess.run(['ssh', NODE, f'cd ~/{folder} && find {prefix or "."} -type f | sort | xargs sha256sum'], capture_output=True, text=True, check=True).stdout
    rows = {}
    for l in out.splitlines():
        h, p = l.split(None, 1); p = p.strip()[2:] if p.strip().startswith('./') else p.strip()
        if not any(s in p for s in SKIP): rows[p] = h
    return rows


def main():
    dep = deployed('v7srv'); dep.update({p: h for p, h in deployed('v6srv_b1', './bench').items()
                                         if p.split('/')[-1] in ('WORLDS_B1.json', 'TOOL_TABLES_B1.json', 'library_structures_b1.json', 'MANUAL_B1.md', 'grade_b1.py')})
    rows = []
    for p, h in sorted(dep.items()):
        cands = [os.path.join(REPO, v, p if not p.startswith('bench/') else p) for v in ('v7', 'v6', 'v5')]
        src = next((c for c in cands if os.path.exists(c) and sha(c) == h), None)
        note = 'equal to deployed'
        if src is None:
            src = next(c for c in cands if os.path.exists(c))
            note = f'deployed copy differs (deployed {h[:16]})'
        dst = os.path.join(OUT, p); os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        rows.append(('server', p, os.path.relpath(src, REPO), sha(dst)[:16], note))
    # runner, authoring, replay and analysis code, frozen inputs and FM status files (unchanged)
    extra = ['F/sllm/author.py', 'F/sllm/run_sllm.py', 'F/sllm/audit_run.py', 'F/sllm/audit_authors.py', 'F/sllm/dev_tokens_G_R.txt',
             'F/sllm/dev_tokens_G_HT.txt', 'F/sllm/PROGRAMS_G.md', 'P/core.py', 'P/replay7.py', 'P/audit.py', 'analyzeF.py', 'analyzeG.py',
             'gatesF.py', 'figG.py', 'run_qwen7.py', 'F/sllm/run/worlds_B1_H.txt', 'T/run_subsets.json', 'b1/ROWS_NODFT.md', 'H/FM_CHECK.md', 'T/fm/fm_check.json', 'FREEZE.md']
    for d in ('F/sllm/inputs_G', 'F/sllm/programs_G'):
        for r, _, fs in os.walk(os.path.join(REPO, 'v7', d)):
            extra += [os.path.relpath(os.path.join(r, f), os.path.join(REPO, 'v7')) for f in fs if '__pycache__' not in r]
    for p in sorted(set(extra)):
        src = os.path.join(REPO, 'v7', p)
        dst = os.path.join(OUT, 'v7ref', p) if p == 'FREEZE.md' else os.path.join(OUT, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        rows.append(('runner/analysis', os.path.relpath(dst, OUT), os.path.relpath(src, REPO), sha(dst)[:16], 'unchanged'))
    for p in ('bench/fm/fm_check.json',):
        src = os.path.join(REPO, 'v6', p); dst = os.path.join(OUT, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)
        rows.append(('runner/analysis', p, os.path.relpath(src, REPO), sha(dst)[:16], 'unchanged'))
    L = ['# vP.1 code and data provenance (VP1-0 step 4)', '',
         'Branch `vp1/2026-10-22`, created from `origin/v7/2026-10-18` at 21fce6e556f7333c87f1ebbe35ef7980573878b2. Worktree `~/Documents/harbor/vp1` on host A.',
         'Everything below was copied unchanged by `vp1/tools/build_source.py`. v5, v6 and v7 are never edited. Hashes are sha256 prefixes (16 hex characters).', '',
         '- **Server chain.** Every file the deployed v7 servers carry (node A2 `~/v7srv` for H and T; `~/v6srv_b1` for B1\'s `bench/`), from the first of `v7/`, `v6/`, `v5/` whose sha256 equals the deployed file.',
         '- **Deployed copies that differ.** Where no repository file equals the deployed one, the frozen repository file is used; the table gives both.',
         '- **vP.1 code** (new, not copied) is listed in FREEZE.md, not here.', '',
         '| part | vp1 path | source | hash | note |', '|---|---|---|---|---|']
    L += [f'| {a} | `{b}` | `{c}` | {d} | {e} |' for a, b, c, d, e in rows]
    L += ['', '## The four files that differ from the deployed copies', '',
          '- `H/WORLDS_H.json`, `T/WORLDS_T.json`: the deployed files are the drafts copied before the freeze. They differ from the frozen files (FREEZE V7-3a c7916260949f7438, V7-2a 5fc8bb45cb8f46cd) only in bookkeeping fields the server never reads (`status`, and per world `in_bench`, `selection_rows_pass`, `bench_note`); every field `family7` reads is equal (checked by a JSON comparison, VP1-0). vP.1 serves the frozen files.',
          '- `graphexec/adapters_mcenv.py`: the repository copy adds V7-E2\'s measure rule to the executor\'s client (`Env.call`), which no server path runs.',
          '- `mcenv/run_claude.py`: host A\'s runner, not part of the server; the repository copy carries V7-X17\'s slot gate.']
    open(os.path.join(OUT, 'SOURCE.md'), 'w').write('\n'.join(L) + '\n')
    print(len(rows), 'files;', sum(1 for r in rows if 'differs' in r[4]), 'differ from deployed:', [r[1] for r in rows if 'differs' in r[4]])


if __name__ == '__main__':
    main()
