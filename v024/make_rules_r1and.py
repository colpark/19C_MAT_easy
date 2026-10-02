#!/usr/bin/env python3
"""make_rules_r1and.py: rules revision r1-AND (2026-10-01, found while diagnosing Bioactive Materials), applied to copies of the r1-C1b rules.
Frozen letters() collected every a-h in the reference body, so 'Fig. 2a and b' gave panels a, a, d, b (the 'a', 'd' of 'and'): a cited
'X and Y' could add a phantom panel d. Change, nothing else: the words 'and' / 'to' are removed before letters are collected
(range detection still uses the original body). usage: make_rules_r1and.py <r1-C1b dir> <out dir>"""
import hashlib, os, shutil, sys
src, out = sys.argv[1:3]; sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert sha(os.path.join(src, 'levels.py')) == '0cfd80a41565f716', 'r1-C1b levels.py changed'
L = open(os.path.join(src, 'levels.py')).read()
old = "    L = re.findall(r'[a-h]', body.lower())\n"
assert L.count(old) == 1
L = L.replace(old, "    L = re.findall(r'[a-h]', re.sub(r'\\b(?:and|to)\\b', ' ', body, flags=re.I).lower())   # r1-AND\n")
L = L.replace('"""levels.py (rules revision r1 + r1-C1b', '"""levels.py (rules revision r1 + r1-C1b + r1-AND letters of and/to ignored', 1)
os.makedirs(out, exist_ok=True); open(os.path.join(out, 'levels.py'), 'w').write(L); shutil.copy(os.path.join(src, 'open.py'), out)
print('r1-AND written:', {f: sha(os.path.join(out, f)) for f in ('levels.py', 'open.py')})
