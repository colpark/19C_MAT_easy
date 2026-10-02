#!/usr/bin/env python3
"""make_rules_r1c1b.py: rules revision r1-C1b (owner decision 2026-10-01), applied to copies of the r1 rules (make_rules_r1.py output).

Frozen C1 (and r1) test only the nearest heading. In papers whose Results section is split into descriptive subheadings
(Nature Communications, Scientific Reports, ...) no paragraph carries 'Results' as its section, so the results were ineligible.
Change, nothing else:
  r1-C1b eligible(): a paragraph is eligible when its own section matches the frozen pattern (Result|Discussion|Conclusion|^[3-9].)
         OR it lies inside such a section: after a heading that matches the pattern and before the next top-level heading of
         another kind (Introduction, Background, Methods, Materials, Experimental, Data/Code availability, Author contributions,
         References, Acknowledgements). Xu17 keeps its own rule.
usage: make_rules_r1c1b.py <r1 dir> <out dir>"""
import hashlib, os, shutil, sys
src, out = sys.argv[1:3]
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
assert sha(os.path.join(src, 'levels.py')) == 'd871001f59464ccd' and sha(os.path.join(src, 'open.py')) == 'c81301c0c4a904da', 'r1 files changed'
L = open(os.path.join(src, 'levels.py')).read()
old = "    return [p for p in paras if p['section'] and re.search(r'Result|Discussion|Conclusion|^[3-9]\\.', p['section'], re.I)]\n"
new = ("    out, on = [], False   # r1-C1b: inside a Results/Discussion/Conclusion section, until another top-level heading\n"
       "    for p in paras:\n"
       "        s = p['section'] or ''\n"
       "        if re.search(r'Result|Discussion|Conclusion|^[3-9]\\.', s, re.I): on = True\n"
       "        elif re.match(r'^\\s*(\\d+\\.?\\s*)?(Introduction|Background|Methods?|Materials?\\b|Experimental|Data availability|Code availability|Author contributions|References|Acknowledg)', s, re.I): on = False\n"
       "        if on: out.append(p)\n"
       "    return out\n")
assert L.count(old) == 1; L = L.replace(old, new).replace('"""levels.py (rules revision r1:', '"""levels.py (rules revision r1 + r1-C1b enclosing Results section, see make_rules_r1c1b.py; r1:', 1)
os.makedirs(out, exist_ok=True); open(os.path.join(out, 'levels.py'), 'w').write(L); shutil.copy(os.path.join(src, 'open.py'), out)
print('r1-C1b written:', {f: sha(os.path.join(out, f)) for f in ('levels.py', 'open.py')})
