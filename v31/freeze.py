#!/usr/bin/env python3
"""freeze.py: sha256 of laws.py, grade.py, generate.py and render.py into FREEZE.md (plan rule 3).
usage: freeze.py --freeze "<reason>"   (writes a new freeze entry; the latest entry is the one checked)
       freeze.py --check               (PASS iff the three files match the latest entry; exit 1 otherwise)"""
import hashlib, re, sys, datetime
V3 = '/home/aid1/Documents/harbor/v31'; FILES = ['laws.py', 'grade.py', 'generate.py', 'render.py']
sha = lambda f: hashlib.sha256(open(f'{V3}/{f}', 'rb').read()).hexdigest()
if sys.argv[1:2] == ['--freeze']:
    reason = sys.argv[2] if len(sys.argv) > 2 else 'initial freeze'
    try: old = open(f'{V3}/FREEZE.md').read()
    except FileNotFoundError: old = '# v3.1 freeze\n\nsha256 of the files that make keys. The last entry is checked by `freeze.py --check`; generate.py runs on real cells only after a PASS. A change after the first freeze needs a new entry with its reason and a full regeneration.\n'
    n = len(re.findall(r'^## freeze ', old, re.M)) + 1
    entry = f'\n## freeze {n} ({datetime.datetime.now().astimezone().isoformat(timespec="seconds")})\n\nreason: {reason}\n\n' + ''.join(f'- `{f}` {sha(f)}\n' for f in FILES)
    open(f'{V3}/FREEZE.md', 'w').write(old + entry); print(entry)
elif sys.argv[1:2] == ['--check']:
    txt = open(f'{V3}/FREEZE.md').read(); last = txt.split('\n## freeze ')[-1]
    want = dict(re.findall(r'- `([^`]+)` ([0-9a-f]{64})', last)); bad = [f for f in FILES if want.get(f) != sha(f)]
    print('freeze check:', 'PASS' if not bad else f'FAIL {bad}', f'(entry {last.split()[0]})'); sys.exit(1 if bad else 0)
else: print(__doc__); sys.exit(1)
