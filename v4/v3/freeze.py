#!/usr/bin/env python3
"""freeze.py: sha256 of the key-making and digitizing code into FREEZE.md (v3.2: entries F1, F2, ...) (plan rule 3).
usage: freeze.py --freeze "<reason>"   (writes a new freeze entry; the latest entry is the one checked)
       freeze.py --check               (PASS iff the three files match the latest entry; exit 1 otherwise)"""
import sys as _pb_s, os as _pb_o
_pb_d = _pb_o.path.dirname(_pb_o.path.abspath(__file__))
while not _pb_o.path.exists(_pb_o.path.join(_pb_d, 'pbroot.py')) and _pb_o.path.dirname(_pb_d) != _pb_d: _pb_d = _pb_o.path.dirname(_pb_d)
_pb_s.path.insert(0, _pb_d)
from pbroot import ROOT, HOST
import hashlib, os, re, sys, datetime
V3 = f'{ROOT}'; FILES = ['provenance.py', 'laws.py', 'signatures.py', 'grade.py', 'generate.py', 'gen_claims.py', 'gen_mech.py', 'render.py', 'digitize.py', 'build_matrix.py', 'readers.py', 'lattice.py', 'papers/mo21/gen_config.py', 'papers/s039/nodes.json', 'papers/s039/law_bindings.json', 'papers/s039/signatures.json', 'papers/s098/nodes.json', 'papers/s098/law_bindings.json', 'papers/s098/signatures.json', 'papers/t042/nodes.json', 'papers/t042/law_bindings.json', 'papers/t042/signatures.json', 'papers/t051/nodes.json', 'papers/t051/law_bindings.json', 'papers/t051/signatures.json', 'papers/s048/nodes.json', 'papers/s048/law_bindings.json', 'papers/s048/signatures.json'] + [f'papers/{k}/features.json' for k in ('s039', 's098', 't042', 't051', 's048')] + ['sd/build.py', 'pbroot.py', 'sd/bundle.py', 'sd/families.py', 'sd/shortcuts33.py'] + [f'sd/{k}/{f}' for k in ('P2', 'P3', 'P4', 'P5', 'P6') for f in ('spec.py', 'tol.json')]
FILES += ['sd/P2/physics.py', 'sd/P2/nodes.json', 'sd/P2/cells.jsonl', 'sd/P2/audit/laws.json', 'sd/P2/audit/parse.json', 'sd/P2/audit/cannot.json', 'sd/P3/physics.py', 'sd/P3/nodes.json', 'sd/P3/cells.jsonl', 'sd/P3/audit/laws.json', 'sd/P3/audit/parse.json', 'sd/P3/audit/cannot.json', 'sd/P4/physics.py', 'sd/P4/nodes.json', 'sd/P4/cells.jsonl', 'sd/P4/audit/laws.json', 'sd/P4/audit/parse.json', 'sd/P4/audit/cannot.json', 'sd/P5/physics.py', 'sd/P5/nodes.json', 'sd/P5/cells.jsonl', 'sd/P5/audit/laws.json', 'sd/P5/audit/parse.json', 'sd/P5/audit/cannot.json', 'sd/P6/physics.py', 'sd/P6/nodes.json', 'sd/P6/cells.jsonl', 'sd/P6/audit/laws.json', 'sd/P6/audit/parse.json', 'sd/P6/audit/cannot.json', 'sd/P2/signatures.json', 'sd/P6/signatures.json', 'sd/P2/audit/signatures.json', 'sd/P6/audit/signatures.json', 'sd/P2/audit/identity.json', 'sd/P6/audit/identity.json', 'audit33.py', 'sd/make_nodes33.py', 'sd/P3/tol_add33.json', 'sd/P6/tol_add33.json', 'sd/build33.py', 'sd/fuzz33.py', 'partB/make_arms33.py']   # v3.3 F10: physics tables, audited nodes, cells and the Sol gate files
sha = lambda f: hashlib.sha256(open(f'{V3}/{f}', 'rb').read()).hexdigest()
if sys.argv[1:2] == ['--freeze']:
    reason = sys.argv[2] if len(sys.argv) > 2 else 'initial freeze'
    try: old = open(f'{V3}/FREEZE.md').read()
    except FileNotFoundError: old = '# v3.2 freeze\n\nsha256 of the files that make keys. The last entry is checked by `freeze.py --check`; generate.py runs on real cells only after a PASS. A change after the first freeze needs a new entry with its reason and a full regeneration.\n'
    n = len(re.findall(r'^## F\d', old, re.M)) + 1
    label = os.environ.get('FREEZE_LABEL') or f'F{n}'   # v3.3: explicit labels (F9 definitions, F10 physics tables); entries 8, 9 = F7b, F7c
    entry = f'\n## {label} ({datetime.datetime.now().astimezone().isoformat(timespec="seconds")})\n\nreason: {reason}\n\n' + ''.join(f'- `{f}` {sha(f)}\n' for f in FILES)
    open(f'{V3}/FREEZE.md', 'w').write(old + entry); print(entry)
elif sys.argv[1:2] == ['--check']:
    txt = open(f'{V3}/FREEZE.md').read(); last = txt.split('\n## F')[-1]
    want = dict(re.findall(r'- `([^`]+)` ([0-9a-f]{64})', last)); bad = [f for f in FILES if want.get(f) != sha(f)]
    print('freeze check:', 'PASS' if not bad else f'FAIL {bad}', f'(entry {last.split()[0]})'); sys.exit(1 if bad else 0)
else: print(__doc__); sys.exit(1)
