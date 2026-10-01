#!/usr/bin/env python3
"""make_rules_r1.py: rules revision r1 (owner decision 2026-10-01), applied to copies of the frozen v0.1 rules.

Writes <out>/levels.py and <out>/open.py from the frozen files (hash-checked first). Changes, nothing else:
  R1-C1  eligible(): the section pattern Result|Discussion|Conclusion|^[3-9]. becomes case-insensitive
         (older papers use all-caps headings such as 'RESULTS AND DISCUSSION').
  R1-C3  refs(): besides lettered references to tier-A figures, a reference to a figure WITHOUT panel letters
         ('Fig. 3') resolves when that figure is a single-panel figure (match.json tier B, reason B3_single).
         It becomes one whole-figure panel with id F<n> (empty letter).
  R1-REF0 the frozen REF pattern requires at least one panel letter, so a plain 'Fig. 2' never matched. A second
         pattern REF0 matches letterless references ('Fig. 2', 'Figure 2', 'Figs. 2 and 3'; not 'Fig. 2a', 'Fig. S2').
         refs() resolves them as R1-C3. Stems keep the reference as written ('Fig. 2'), so existing items are unchanged.
  R1-P   open.build(): a whole-figure panel takes the full figure image as its crop and the single panel's
         caption span ('definition') as its caption.
  R1-fix levels.run(): crop lookup parses panel ids with a regex so F<n> ids work (stats path only).
usage: make_rules_r1.py <frozen dir> <out dir>
"""
import hashlib, os, sys
src, out = sys.argv[1:3]
FROZEN = {'levels.py': '7477c0bbdf798157', 'open.py': '9d4e3683b9afacec'}
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16]
for f, h in FROZEN.items(): assert sha(os.path.join(src, f)) == h, f
L = open(os.path.join(src, 'levels.py')).read(); O = open(os.path.join(src, 'open.py')).read()

def sub(text, old, new, name):
    assert text.count(old) == 1, f'{name}: expected exactly one match'
    return text.replace(old, new)

L = sub(L, "re.search(r'Result|Discussion|Conclusion|^[3-9]\\.', p['section'])",
           "re.search(r'Result|Discussion|Conclusion|^[3-9]\\.', p['section'], re.I)", 'R1-C1')
L = sub(L, "def letters(body):", "REF0 = re.compile(r'\\b(?:Fig(?:ure)?s?\\.?)\\s*(\\d+)((?:\\s*(?:,|and|&)\\s*\\d+)*)(?![\\d.]*\\d)(?!\\s*\\(?[a-hA-H](?![A-Za-z]))')   # R1-REF0 letterless figure references\n\ndef letters(body):", 'R1-REF0')
L = sub(L, """            if l in labs and (n, l) not in out:
                out.append((n, l))
    return out""", """            if l in labs and (n, l) not in out:
                out.append((n, l))
    for m in REF0.finditer(s):   # R1-C3 letterless reference to a single-panel figure = whole-figure panel F<n>
        for n in [int(m.group(1))] + [int(x) for x in re.findall(r'\\d+', m.group(2))]:
            f = store.get(n)
            if f is not None and f['tier'] != 'A' and f.get('reason') == 'B3_single' and (n, '') not in out:
                out.append((n, ''))
    return out""", 'R1-C3')
# R1-ids considered and dropped: rewriting letterless references in stems would change the wording of existing items.

L = sub(L, "it['crops'] = {pid: crops[(int(re.match(r'F(\\d+)', pid).group(1)), pid[-1])] for pid in it['panels']}",
           "it['crops'] = {pid: crops.get((int(re.match(r'F(\\d+)([a-zA-Z]?)', pid).group(1)), re.match(r'F(\\d+)([a-zA-Z]?)', pid).group(2) or 'single')) for pid in it['panels']}", 'R1-fix')
L = L.replace('"""levels.py:', '"""levels.py (rules revision r1: C1 case-insensitive sections; C3 single-panel figures as whole-figure panels F<n>; see make_rules_r1.py):', 1)
O = sub(O, """    crops = {(f['figure_number'], p['label']): (folder + p['crop']) if p.get('crop') else None for f in match['figures'] for p in f['panels']}
    E = eligible(paras, key)""", """    crops = {(f['figure_number'], p['label']): (folder + p['crop']) if p.get('crop') else None for f in match['figures'] for p in f['panels']}
    for f in match['figures']:   # R1-P whole-figure panel F<n> for single-panel figures
        if f.get('reason') == 'B3_single':
            sp = next((p for p in f['panels'] if p['label'] == 'single'), {})
            defs[(f['figure_number'], '')] = sp.get('definition')
            crops[(f['figure_number'], '')] = folder + f['file']
    E = eligible(paras, key)""", 'R1-P')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'levels.py'), 'w').write(L); open(os.path.join(out, 'open.py'), 'w').write(O)
print('r1 written:', {f: sha(os.path.join(out, f)) for f in FROZEN})
