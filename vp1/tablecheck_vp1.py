"""vP.1 table check before every batch (hard rule 4, V7-E6): every listed server's in-memory table hashes (GET /tables) must equal
vp1/TABLES_FROZEN.json (hashed in FREEZE.md), and every manipulated arm's manual must equal its fm arm's. One line per check in vp1/LOG.md.
Exit status 0 only if every port passes; a runner starts a batch only after a 0.
  python vp1/tablecheck_vp1.py BATCH PORT [PORT ...]"""
import datetime, json, os, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
HOST = '192.168.100.11'
SKIP = ('pid', 'state', 'checks')


def check(batch, ports):
    frozen = {k: v for k, v in json.load(open(os.path.join(HERE, 'TABLES_FROZEN.json'))).items() if k not in SKIP}
    rows, ok = [], True
    for p in ports:
        try:
            r = json.loads(urllib.request.urlopen(f'http://{HOST}:{p}/tables', timeout=120).read())
            bad = sorted(k for k in frozen if r.get(k) != frozen[k]) + sorted(k for k, v in r.get('checks', {}).items() if not v)
            rows.append(f'{p} pid {r.get("pid")} ' + ('equal (%d tables)' % len(frozen) if not bad else 'DIFFERS: ' + ', '.join(bad)))
            ok &= not bad
        except Exception as e:
            rows.append(f'{p} UNREACHABLE ({type(e).__name__})'); ok = False
    ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')
    line = f'- {ts} table check before batch `{batch}`: ' + ('PASS' if ok else 'FAIL') + '; ' + '; '.join(rows)
    with open(os.path.join(HERE, 'LOG.md'), 'a') as f: f.write(line + '\n')
    print(line)
    return ok


if __name__ == '__main__':
    sys.exit(0 if check(sys.argv[1], [int(p) for p in sys.argv[2:]]) else 1)
