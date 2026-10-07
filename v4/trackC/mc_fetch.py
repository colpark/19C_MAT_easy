#!/usr/bin/env python3
"""Polite fetcher for Track C deposits (PanelBench M0 fetch rules, prompt hard rule 3).

Allowed hosts only: the Materials Cloud records API (and its CINECA read-only
failover), figshare ndownloader / API, arXiv.  One request at a time, >= 2 s
apart with jitter, Retry-After honoured, error bodies kept as .bad, 404s cached
as markers, sizes logged from record metadata before any download, and any file
over 50 GB refused unless --allow-large is passed after the user approves.

Subcommands
  meta  <record_id> --out DIR        record JSON, files JSON, versions JSON
  get   <url> --out PATH [--md5 X] [--size N]
  figshare-meta <article_id> --out DIR
Every call appends one JSON line to --log (default fetch_log.jsonl).
"""
import argparse, hashlib, json, os, random, sys, time, urllib.parse
import requests

MC = "https://archive.materialscloud.org"
# read-only failover named in the Materials Cloud status page (used only when MC is down)
MC_FAILOVER = os.environ.get("MC_FAILOVER", "https://archive-ro.materialscloud.org")
ALLOWED = ("archive.materialscloud.org", "archive-ro.materialscloud.org",
           "api.figshare.com", "ndownloader.figshare.com", "figshare.com",
           "arxiv.org", "export.arxiv.org")
# storage backends the allowed endpoints redirect to; accepted only as redirect targets
REDIRECT_OK = ("rgw.cscs.ch", "pfigshare-u-files.s3.amazonaws.com", "s3-eu-west-1.amazonaws.com")
UA = "PanelBench-TrackC/0.1 (research; polite; one request at a time)"
MIN_GAP = 2.0
LARGE = 50 * 1024**3
_last = [0.0]


def _host_ok(url):
    h = urllib.parse.urlparse(url).hostname or ""
    return any(h == a or h.endswith("." + a) for a in ALLOWED)


def _redirect_ok(url):
    p = urllib.parse.urlparse(url)
    h = p.hostname or ""
    if h == "rgw.cscs.ch":
        return p.path.startswith("/mc-archive/")
    if h.endswith("amazonaws.com"):
        return "pfigshare-u-files" in (h + p.path)
    return _host_ok(url)


def _wait():
    gap = MIN_GAP + random.uniform(0.3, 1.5)
    dt = time.time() - _last[0]
    if dt < gap:
        time.sleep(gap - dt)
    _last[0] = time.time()


def _log(path, rec):
    rec["t"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    rec["host"] = os.uname().nodename
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")


def request(url, log, stream=False, tries=4):
    if not _host_ok(url):
        raise SystemExit(f"host not allowed: {url}")
    for k in range(tries):
        _wait()
        try:
            r = requests.get(url, headers={"User-Agent": UA}, stream=stream, timeout=120,
                             allow_redirects=True)
        except requests.RequestException as e:
            _log(log, {"url": url, "error": repr(e), "try": k})
            time.sleep(10 * (k + 1))
            continue
        if not _redirect_ok(r.url):
            r.close()
            raise SystemExit(f"redirected off the allowed hosts: {r.url}")
        if r.status_code in (429, 503):
            ra = r.headers.get("Retry-After", "30")
            wait = int(ra) if ra.isdigit() else 30
            _log(log, {"url": url, "status": r.status_code, "retry_after": wait})
            r.close()
            time.sleep(wait)
            continue
        return r
    raise SystemExit(f"gave up on {url}")


def _bad(path, r, log, url):
    body = r.content[:1_000_000]
    with open(path + ".bad", "wb") as f:
        f.write(body)
    _log(log, {"url": url, "status": r.status_code, "bad": path + ".bad", "len": len(body)})


def get_json(url, out, log):
    r = request(url, log)
    if r.status_code == 404:
        open(out + ".404", "w").close()
        _log(log, {"url": url, "status": 404})
        return None
    ct = r.headers.get("Content-Type", "")
    if r.status_code != 200 or "json" not in ct:
        _bad(out, r, log, url)
        return None
    with open(out, "wb") as f:
        f.write(r.content)
    _log(log, {"url": url, "status": 200, "out": out, "bytes": len(r.content),
               "sha256": hashlib.sha256(r.content).hexdigest()})
    return r.json()


def meta(rid, outdir, log):
    os.makedirs(outdir, exist_ok=True)
    base = f"{MC}/api/records/{rid}"
    rec = get_json(base, os.path.join(outdir, f"{rid}.record.json"), log)
    if rec is None:
        base = f"{MC_FAILOVER}/api/records/{rid}"
        rec = get_json(base, os.path.join(outdir, f"{rid}.record.json"), log)
    get_json(base + "/files", os.path.join(outdir, f"{rid}.files.json"), log)
    get_json(base + "/versions", os.path.join(outdir, f"{rid}.versions.json"), log)
    return rec


def download(url, out, log, md5=None, size=None, allow_large=False):
    if size is not None and size > LARGE and not allow_large:
        _log(log, {"url": url, "refused_large": size})
        raise SystemExit(f"{out}: {size} bytes > 50 GB; ask the user first")
    if os.path.exists(out) and md5:
        h = hashlib.md5()
        with open(out, "rb") as f:
            for b in iter(lambda: f.read(1 << 24), b""):
                h.update(b)
        if h.hexdigest() == md5:
            _log(log, {"url": url, "out": out, "resume": "verified", "md5": md5})
            return True
    _log(log, {"url": url, "out": out, "declared_size": size, "start": True})
    r = request(url, log, stream=True)
    if r.status_code != 200:
        _bad(out, r, log, url)
        return False
    ct = r.headers.get("Content-Type", "")
    if "text/html" in ct:  # an error or login page, never data
        _bad(out, r, log, url)
        return False
    h = hashlib.md5()
    tmp = out + ".part"
    n = 0
    with open(tmp, "wb") as f:
        for b in r.iter_content(1 << 22):
            f.write(b)
            h.update(b)
            n += len(b)
    ok = (md5 is None or h.hexdigest() == md5) and (size is None or n == size)
    if ok:
        os.replace(tmp, out)
    _log(log, {"url": url, "out": out, "bytes": n, "md5": h.hexdigest(), "md5_expected": md5,
               "ok": ok})
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["meta", "get", "figshare-meta"])
    ap.add_argument("arg")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md5")
    ap.add_argument("--size", type=int)
    ap.add_argument("--allow-large", action="store_true")
    ap.add_argument("--log", default="fetch_log.jsonl")
    a = ap.parse_args()
    if a.cmd == "meta":
        meta(a.arg, a.out, a.log)
    elif a.cmd == "figshare-meta":
        os.makedirs(a.out, exist_ok=True)
        get_json(f"https://api.figshare.com/v2/articles/{a.arg}",
                 os.path.join(a.out, f"figshare_{a.arg}.json"), a.log)
    else:
        sys.exit(0 if download(a.arg, a.out, a.log, a.md5, a.size, a.allow_large) else 1)


if __name__ == "__main__":
    main()
