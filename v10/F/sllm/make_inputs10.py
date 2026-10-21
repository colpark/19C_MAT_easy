"""V10-4 S-llm inputs per family (V7-F3 protocol with V7-E3, V7-X14, V7-X15 and the V7-E4 lesson): inputs/<FAM>/
  manual.md         the v10 fm manual as status renders it for the v10-fm arm, on one development world of the family (tuning split)
  tools.json        the v10-fm arm's tools (client10 texts and argument schemas) with RETURN SHAPES: the keys and value types of a real
                    response of each tool on a development episode, never its values (V7-E4: v7's tools.json had none and 10 of 15
                    programs never measured)
  client.py         v7's one-function client (call(tool, args)), unchanged
  INSTRUCTION.txt   v7's instruction, verbatim
The manual of every family is the same for every world of the family except the {BUDGET} and the count-scale text, which carry no
world-specific number in v10, so one development world per family renders it.
  MCENV_URL=... python F/sllm/make_inputs10.py FAM TOKEN      (TOKEN: a development episode of the family, arm v10-fm, k 98)"""
import json, os, shutil, sys, urllib.request, uuid
HERE = os.path.dirname(os.path.abspath(__file__)); V10 = os.path.join(HERE, '..', '..'); V7S = os.path.join(V10, '..', 'v7', 'F', 'sllm', 'inputs')


def call(url, tok, tool, args):
    b = json.dumps(dict(token=tok, tool=tool, args=args, rid=uuid.uuid4().hex)).encode()
    r = json.loads(urllib.request.urlopen(urllib.request.Request(url, data=b, headers={'Content-Type': 'application/json'}), timeout=600).read())
    if not r.get('ok'): raise RuntimeError(r.get('error'))
    return r['result']


def shape(v, depth=0):
    if isinstance(v, dict):
        if depth >= 3: return 'object'
        return {k: shape(x, depth + 1) for k, x in v.items() if k not in ('manual',)} | ({'manual': 'string (this manual)'} if 'manual' in v else {})
    if isinstance(v, list):
        if not v: return 'list'
        return [shape(v[0], depth + 1)] if isinstance(v[0], (dict, list)) else f'list of {type(v[0]).__name__} (length varies)'
    return type(v).__name__


def tool_specs(fam):
    os.environ['MCENV_ARM'] = 'v10-fm'; os.environ['MCENV_FAMILY'] = fam
    sys.path.insert(0, V10)
    import asyncio
    from mcenv import client10 as C10
    tools = asyncio.run(C10.mcp.list_tools())
    return [dict(name=t.name, description=t.description, arguments=t.inputSchema) for t in tools]


def main():
    fam, tok = sys.argv[1], sys.argv[2]; url = os.environ['MCENV_URL']
    out = os.path.join(HERE, 'inputs', fam); os.makedirs(out, exist_ok=True)
    st = call(url, tok, 'status', {})
    open(os.path.join(out, 'manual.md'), 'w').write(st['manual'])
    T = fam == 'T'; lib = [x['name'] for x in st['library']]; f = lib[0]
    m0 = (st['samples']['pre']['measurements'][0]['id'] if T else st['measurements'][0]['id'])
    smp = dict(sample='pre') if T else {}
    ex = dict(status=st,
              simulate=call(url, tok, 'simulate', dict(spec=dict(phases=[dict(name=f, weight=1.0)], start=30, stop=31, step=0.04))),
              peaks=call(url, tok, 'peaks', dict(measurement_id=m0)),
              fit=call(url, tok, 'fit', dict(measurement_ids=[m0], spec=dict(phases=[dict(name=f, weight=1.0)]), **smp)),
              run_python=call(url, tok, 'run_python', dict(code='print(1)')),
              energy=call(url, tok, 'energy', dict(structure_name=f)), hull=call(url, tok, 'hull', dict(structure_name=f)),
              measure=call(url, tok, 'measure', dict(start=30, stop=31, step=0.04, time_per_step=0.1, **smp)))
    ex['answer'] = dict(recorded='bool', verdict='str', note='str', call_id='str')
    specs = tool_specs(fam)
    for s in specs:
        s['returns'] = shape(ex[s['name']]) if s['name'] != 'answer' else ex['answer']
    json.dump(dict(arm_tools=specs, note='returns: the keys and value types of a response (each call returns it as a dict)'),
              open(os.path.join(out, 'tools.json'), 'w'), indent=1)
    for fn in ('client.py', 'INSTRUCTION.txt'): shutil.copy(os.path.join(V7S, fam if os.path.exists(os.path.join(V7S, fam)) else 'R', fn), out)
    print(fam, 'inputs:', sorted(os.listdir(out)), [s['name'] for s in specs])


if __name__ == '__main__':
    main()
