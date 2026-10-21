"""V7-G2 input check: fails (exit 1) unless every tool of every family's inputs_G/tools.json has an argument schema and a return shape
(a non-empty object or list of keys and types, not the V7-F3 placeholder), and manual.md, client.py and INSTRUCTION.txt are byte-identical
to V7-F3's.
  python F/sllm/check_inputs_G.py"""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); bad = []
for fam in ('R', 'H', 'T'):
    d = os.path.join(HERE, 'inputs_G', fam)
    try: t = json.load(open(os.path.join(d, 'tools.json')))
    except Exception as e: bad.append(f'{fam}: tools.json unreadable ({e})'); continue
    for s in t['arm_tools']:
        r = s.get('returns')
        if not isinstance(r, (dict, list)) or not r or 'see the description' in json.dumps(r): bad.append(f"{fam}/{s['name']}: no return shape")
        if not isinstance(s.get('arguments'), dict): bad.append(f"{fam}/{s['name']}: no argument schema")
    for fn in ('manual.md', 'client.py', 'INSTRUCTION.txt'):
        h = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
        if h(os.path.join(d, fn)) != h(os.path.join(HERE, 'inputs', fam, fn)): bad.append(f'{fam}/{fn}: differs from V7-F3')
print('FAIL' if bad else 'PASS', bad)
sys.exit(1 if bad else 0)
