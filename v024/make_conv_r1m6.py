#!/usr/bin/env python3
"""make_conv_r1m6.py: converter revision r1-M6 (owner decision 2026-10-01), applied to a copy of the frozen mineru_paras.py.

Frozen M6 starts the body at a heading containing 'Introduction'; only Xu17 (Nano Letters) had a fallback. Nature-family papers
(Nature Communications, Scientific Reports, Communications *) have no Introduction heading, so 31 of the 100 v0.24 papers gave
zero paragraphs. Change, nothing else:
  r1-M6  if the paper has NO heading containing 'Introduction', the body starts at the first text paragraph of more than 40 words
         (the abstract or first intro paragraph). Paragraphs before the first heading have section None and are never eligible
         under levels.py C1, so only the Results/Discussion paragraphs can source items. Papers WITH an Introduction heading and
         Xu17 are processed exactly as before.
usage: make_conv_r1m6.py <frozen mineru_paras.py> <out file>"""
import hashlib, sys
src, out = sys.argv[1:3]
assert hashlib.sha256(open(src, 'rb').read()).hexdigest()[:16] == '7989ad0321104366', 'frozen mineru_paras.py changed'
s = open(src).read()
def sub(t, old, new):
    assert t.count(old) == 1, old[:40]; return t.replace(old, new)
s = sub(s, "    out, section, started = [], None, False\n",
        "    out, section, started = [], None, False\n"
        "    has_intro = any('head' in x and re.search(r'ntroduction|INTRODUCTION', x['head']) for x in paras)   # r1-M6\n")
s = sub(s, "        if started and len(t.split()) >= 5:\n",
        "        if not started and key != 'Xu17' and not has_intro and len(t.split()) > 40:   # r1-M6 no Introduction heading\n"
        "            started = True\n"
        "        if started and len(t.split()) >= 5:\n")
s = s.replace('"""mineru_paras.py:', '"""mineru_paras.py (converter revision r1-M6: body starts at the first paragraph over 40 words when a paper has no Introduction heading; see make_conv_r1m6.py):', 1)
open(out, 'w').write(s); print('r1-M6 written', hashlib.sha256(open(out, 'rb').read()).hexdigest()[:16])
