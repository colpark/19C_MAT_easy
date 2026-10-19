"""Run a slice of the V8-1 truth queue sequentially on one node.

One v8 GPU job per node: each run waits for the GPU, then runs to completion before
the next starts. Finished runs (run.json present) are skipped, so a driver can be
restarted safely. Each run that dies is retried once with the same seed (addendum D
item 4.5); a second failure is recorded and the queue moves on.

Usage:
  python driver.py --specs specs.json --tag A1 [--ns 2.0] [--runs-dir ~/v8_data/runs]
"""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def gpu_busy(threshold=0.5):
    """True when another process holds more than `threshold` of GPU memory."""
    try:
        q = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                            "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=30)
    except Exception:
        return False
    total = None
    try:
        tot = subprocess.run(["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=30)
        total = float(tot.stdout.strip().splitlines()[0])
    except Exception:
        total = None
    if total is None:
        # GB10 reports no GPU memory total: host and GPU share one pool, so use MemTotal.
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal:"):
                total = float(line.split()[1]) / 1024.0
                break
    if not total:
        return False
    mine = str(os.getpid())
    used = 0.0
    for line in q.stdout.strip().splitlines():
        if not line.strip():
            continue
        f = [x.strip() for x in line.split(",")]
        if len(f) >= 2 and f[0] != mine:
            try:
                used += float(f[1])
            except ValueError:
                pass
    return used > threshold * total


def wait_for_gpu(log):
    while gpu_busy():
        print(f"{time.strftime('%FT%TZ', time.gmtime())} GPU held by another process; waiting 10 min", file=log, flush=True)
        time.sleep(600)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--specs", required=True); p.add_argument("--tag", required=True)
    p.add_argument("--ns", type=float, default=2.0)
    p.add_argument("--runs-dir", default=os.path.expanduser("~/v8_data/runs"))
    a = p.parse_args()
    specs = json.load(open(a.specs))
    os.makedirs(a.runs_dir, exist_ok=True)
    log = open(os.path.join(a.runs_dir, f"driver_{a.tag}.log"), "a")
    # the driver writes its own PID: a shell's $! can name a wrapper, not this process
    pidfile = os.path.join(a.runs_dir, f"driver_{a.tag}.pid")
    open(pidfile, "w").write(str(os.getpid()) + "\n")
    print(f"=== driver {a.tag} start {time.strftime('%FT%TZ', time.gmtime())} {len(specs)} specs ns={a.ns}", file=log, flush=True)

    for s in specs:
        tag = f"{s['unit']}_{s['cation']}_r{s['registry']}_p{s['placement']}"
        out = os.path.join(a.runs_dir, tag)
        if os.path.exists(os.path.join(out, "run.json")):
            print(f"skip {tag} (done)", file=log, flush=True)
            continue
        cmd = [sys.executable, os.path.join(HERE, "run_truth.py"),
               "--unit", s["unit"], "--cation", s["cation"], "--registry", str(s["registry"]),
               "--placement", str(s["placement"]), "--out", out, "--ns", str(a.ns),
               "--platform", "CUDA", "--seed", str(s.get("seed", 1))]
        for attempt in (1, 2):
            wait_for_gpu(log)
            t0 = time.time()
            print(f"{time.strftime('%FT%TZ', time.gmtime())} run {tag} attempt {attempt}", file=log, flush=True)
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
            ok = os.path.exists(os.path.join(out, "run.json"))
            print(f"  rc {r.returncode} ok {ok} wall {(time.time() - t0) / 60:.1f} min", file=log, flush=True)
            if not ok:
                print("  stderr tail: " + " | ".join(r.stderr.strip().splitlines()[-3:]), file=log, flush=True)
            if ok:
                tail = [l for l in r.stdout.strip().splitlines() if l.startswith("DONE")]
                print("  " + (tail[-1] if tail else "no DONE line"), file=log, flush=True)
                break
        else:
            print(f"  FAILED twice: {tag}", file=log, flush=True)
    os.remove(pidfile) if os.path.exists(pidfile) else None
    print(f"=== driver {a.tag} done {time.strftime('%FT%TZ', time.gmtime())}", file=log, flush=True)


if __name__ == "__main__":
    main()
