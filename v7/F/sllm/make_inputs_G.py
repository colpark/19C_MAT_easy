"""V7-G2 corrected S-llm inputs (V7-E4): inputs_G/<FAM>/ = V7-F3's manual.md, client.py and INSTRUCTION.txt unchanged, and tools.json
with V7-F3's tool names, descriptions and argument schemas plus a RETURN SHAPE for every tool: the keys and value types of a real
response of that tool on an input-building episode of the family (the family's development world, arm as V7-F3, k = 98, batch
v7-G-sllm-inputs, used by no analysis), never its values. The answer tool's shape comes from a real answer on that episode, last.
  python F/sllm/make_inputs_G.py FAM URL TOKEN
After the build (V7-X17): the peaks shape is set from the server code (mcenv/tools_common.find_peaks), since the input episodes found no
peak; the hull decomposition shape is made generic (its keys named the development compound's phases)."""
import json, os, shutil, sys, urllib.request, uuid
HERE = os.path.dirname(os.path.abspath(__file__))


def call(url, tok, tool, args):
    b = json.dumps(dict(token=tok, tool=tool, args=args, rid=uuid.uuid4().hex)).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=b, headers={'Content-Type': 'application/json'}), timeout=600).read())
    if not r.get('ok'): raise RuntimeError(f"{tool}: {r.get('error')}")
    return r['result']


def shape(v, depth=0):
    """keys and value types, no values; lists show the shape of their first element."""
    if isinstance(v, dict):
        if depth >= 4: return 'object'
        return {k: ('string (the manual text)' if k == 'manual' else shape(x, depth + 1)) for k, x in v.items()}
    if isinstance(v, list):
        if not v: return 'list (may be empty)'
        return [shape(v[0], depth + 1)] if isinstance(v[0], (dict, list)) else f'list of {type(v[0]).__name__} (length varies)'
    return {bool: 'bool', int: 'int', float: 'float', str: 'string', type(None): 'null'}.get(type(v), type(v).__name__)


def main():
    fam, url, tok = sys.argv[1:4]
    src = os.path.join(HERE, 'inputs', fam); out = os.path.join(HERE, 'inputs_G', fam); os.makedirs(out, exist_ok=True)
    T = fam == 'T'
    st = call(url, tok, 'status', {})
    lib = [x['name'] for x in st['library']]; f = lib[0]
    m0 = st['samples']['pre']['measurements'][0]['id'] if T else st['measurements'][0]['id']
    smp = dict(sample='pre') if T else {}
    ex = dict(status=st)
    ex['simulate'] = call(url, tok, 'simulate', dict(spec=dict(phases=[dict(name=f, weight=1.0)], radiation='xray', start=30, stop=31, step=0.04)))
    ex['peaks'] = call(url, tok, 'peaks', dict(measurement_id=m0))
    ex['fit'] = call(url, tok, 'fit', dict(measurement_ids=[m0], spec=dict(phases=[dict(name=f, weight=1.0)], size_nm=100), **smp))
    ex['run_python'] = call(url, tok, 'run_python', dict(code='print(1)'))
    ex['energy'] = call(url, tok, 'energy', dict(structure_name=f)); ex['hull'] = call(url, tok, 'hull', dict(structure_name=f))
    ex['measure'] = call(url, tok, 'measure', dict(radiation='xray', start=30, stop=31, step=0.04, time_per_step=0.1, **smp))
    ans = dict(verdict='CANNOT_TELL', rationale='input building', decision_rule='input building', property_values=[])
    ans.update(dict(region_pre='', region_post='', identified_phase_pre='unknown', identified_phase_post='unknown') if T else dict(region='', identified_phase='unknown'))
    ex['answer'] = call(url, tok, 'answer', ans)
    t = json.load(open(os.path.join(src, 'tools.json')))
    for s in t['arm_tools']: s['returns'] = shape(ex[s['name']])
    t['note'] = (t['note'] + ' returns: the keys and value types of a real response of the tool (call returns it as a dict); values vary by '
                 'episode, list lengths vary, and an error raises RuntimeError with the lab message instead.')
    json.dump(t, open(os.path.join(out, 'tools.json'), 'w'), indent=1)
    for fn in ('manual.md', 'client.py', 'INSTRUCTION.txt'): shutil.copy(os.path.join(src, fn), out)
    print(fam, sorted(os.listdir(out)), [s['name'] for s in t['arm_tools']])


if __name__ == '__main__':
    main()
