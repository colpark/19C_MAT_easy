"""v7 Qwen runner (host B, V7-X8): mcenv.run_qwen unchanged except the tool-list fetch (V6-X20). run_qwen.mcp_tools sends initialize and
tools/list to the MCP client with stdin closed at once; on host B the client then exits before it answers tools/list (StopIteration).
This wrapper keeps the client's stdin open until the tools/list reply arrives, then closes it. Tool names, descriptions and schemas are
the client's own, as before; the frozen mcenv code (hash 0ca269b543eedec0) is not touched.
  PYTHONPATH=CODE python bench/run_qwen_b1.py PLAN.jsonl OUTDIR [--conc 8] [--env URL]"""
import json, os, subprocess, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
from mcenv import run_qwen as RQ


def mcp_tools(arm, stage=''):
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                                                           "clientInfo": {"name": "qwen-harness", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"}, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
    env = dict(os.environ, PYTHONPATH=RQ.REPO, MCENV_ARM=arm, MCENV_TOKEN='none', MCENV_STAGE=stage)
    p = subprocess.Popen([sys.executable, '-m', 'mcenv.client7' if arm.startswith('v7') else 'mcenv.client'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
    for m in msgs: p.stdin.write(json.dumps(m) + '\n')
    p.stdin.flush(); t0 = time.time(); tl = None
    while time.time() - t0 < 60:
        line = p.stdout.readline()
        if not line: break
        try: d = json.loads(line)
        except ValueError: continue
        if d.get('id') == 2: tl = d['result']['tools']; break
    p.stdin.close(); p.wait(timeout=30)
    if tl is None: raise RuntimeError(f'tools/list failed for {arm}')
    return [{'type': 'function', 'function': {'name': t['name'], 'description': t.get('description', ''), 'parameters': t['inputSchema']}} for t in tl]


RQ.mcp_tools = mcp_tools

if __name__ == '__main__':
    RQ.main()
