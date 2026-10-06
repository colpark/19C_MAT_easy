#!/usr/bin/env python3
"""freeze_v4.py: sha256 entries in v4/FREEZE.md (rule I4). usage: freeze_v4.py --freeze LABEL "reason" file [file ...] | --check LABEL"""
import hashlib, os, re, sys, datetime
D = os.path.dirname(os.path.abspath(__file__)); F = f'{D}/FREEZE.md'
sha = lambda f: hashlib.sha256(open(f'{D}/{f}', 'rb').read()).hexdigest()
if sys.argv[1] == '--freeze':
    label, reason, files = sys.argv[2], sys.argv[3], sys.argv[4:]
    old = open(F).read() if os.path.exists(F) else '# v4 freeze\n\nsha256 of key-making code and frozen tables (rule I4). `freeze_v4.py --check <label>` verifies an entry.\n'
    e = f'\n## {label} ({datetime.datetime.now().astimezone().isoformat(timespec="seconds")})\n\nreason: {reason}\n\n' + ''.join(f'- `{f}` {sha(f)}\n' for f in files)
    open(F, 'w').write(old + e); print(e)
else:
    label = sys.argv[2]; txt = open(F).read(); part = txt.split(f'\n## {label} (')[-1].split('\n## ')[0]
    want = dict(re.findall(r'- `([^`]+)` ([0-9a-f]{64})', part)); bad = [f for f, h in want.items() if sha(f) != h]
    print(f'freeze check {label}:', 'PASS' if not bad else f'FAIL {bad}'); sys.exit(1 if bad else 0)
