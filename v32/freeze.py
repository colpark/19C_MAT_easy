#!/usr/bin/env python3
"""freeze.py: sha256 of the key-making and digitizing code into FREEZE.md (v3.2: entries F1, F2, ...) (plan rule 3).
usage: freeze.py --freeze "<reason>"   (writes a new freeze entry; the latest entry is the one checked)
       freeze.py --check               (PASS iff the three files match the latest entry; exit 1 otherwise)"""
import hashlib, re, sys, datetime
V3 = '/home/aid1/Documents/harbor/v32'; FILES = ['provenance.py', 'laws.py', 'signatures.py', 'grade.py', 'generate.py', 'gen_claims.py', 'gen_mech.py', 'render.py', 'digitize.py', 'build_matrix.py', 'readers.py', 'lattice.py', 'papers/mo21/gen_config.py', 'papers/s039/nodes.json', 'papers/s039/law_bindings.json', 'papers/s039/signatures.json', 'papers/s098/nodes.json', 'papers/s098/law_bindings.json', 'papers/s098/signatures.json', 'papers/t042/nodes.json', 'papers/t042/law_bindings.json', 'papers/t042/signatures.json', 'papers/t051/nodes.json', 'papers/t051/law_bindings.json', 'papers/t051/signatures.json', 'papers/s048/nodes.json', 'papers/s048/law_bindings.json', 'papers/s048/signatures.json'] + [f'papers/{k}/features.json' for k in ('s039', 's098', 't042', 't051', 's048')]
sha = lambda f: hashlib.sha256(open(f'{V3}/{f}', 'rb').read()).hexdigest()
if sys.argv[1:2] == ['--freeze']:
    reason = sys.argv[2] if len(sys.argv) > 2 else 'initial freeze'
    try: old = open(f'{V3}/FREEZE.md').read()
    except FileNotFoundError: old = '# v3.2 freeze\n\nsha256 of the files that make keys. The last entry is checked by `freeze.py --check`; generate.py runs on real cells only after a PASS. A change after the first freeze needs a new entry with its reason and a full regeneration.\n'
    n = len(re.findall(r'^## F\d', old, re.M)) + 1
    entry = f'\n## F{n} ({datetime.datetime.now().astimezone().isoformat(timespec="seconds")})\n\nreason: {reason}\n\n' + ''.join(f'- `{f}` {sha(f)}\n' for f in FILES)
    open(f'{V3}/FREEZE.md', 'w').write(old + entry); print(entry)
elif sys.argv[1:2] == ['--check']:
    txt = open(f'{V3}/FREEZE.md').read(); last = txt.split('\n## F')[-1]
    want = dict(re.findall(r'- `([^`]+)` ([0-9a-f]{64})', last)); bad = [f for f in FILES if want.get(f) != sha(f)]
    print('freeze check:', 'PASS' if not bad else f'FAIL {bad}', f'(entry {last.split()[0]})'); sys.exit(1 if bad else 0)
else: print(__doc__); sys.exit(1)
