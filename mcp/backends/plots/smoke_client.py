"""Smoke test of the plots worker over HTTP; prints accuracy vs synthetic ground truth."""
import base64, json, os, sys, time, urllib.request
import numpy as np

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8103"
D = os.path.expanduser("~/mcp/plots/smoke/data")
GT = json.load(open(f"{D}/ground_truth.json"))
report = {}


def call(tool, name, args=None, seed=0):
    b = base64.b64encode(open(f"{D}/{name}.png", "rb").read()).decode()
    req = urllib.request.Request(f"{URL}/{tool}", data=json.dumps({"image_b64": b, "args": args or {}, "seed": seed}).encode(),
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    r = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return r, time.time() - t


def get(p):
    return json.loads(urllib.request.urlopen(URL + p, timeout=600).read())


print("health", get("/health"))
v = get("/version"); print("version", json.dumps(v)[:2000])

# ---- read_text
def norm(s):
    return s.replace(" ", "").replace("−", "-").lower()

rt = {}
for n in ["linear", "logy", "two_series"]:
    r, dt = call("read_text", n)
    toks = [norm(t["text"]) for t in r["values"]["tokens"]]
    g = GT[n]
    exp = [g["title"], g["xlabel"], g["ylabel"]] + g["xticks"] + g["yticks"]
    exp = [norm(e.replace("\\mathdefault", "").replace("$", "").replace("^", "").replace("{", "").replace("}", "")) for e in exp if e]
    hit = [e for e in exp if any(e == t or e in t for t in toks)]
    rt[n] = {"recall": f"{len(hit)}/{len(exp)}", "missed": [e for e in exp if e not in hit], "s": round(dt, 2)}
    rt[n]["device"] = r["provenance"]["device"]
report["read_text"] = rt
print("read_text", json.dumps(rt))

# ---- read_scale_bar
sb = {}
for n in ["sem_10um", "sem_500nm"]:
    r, dt = call("read_scale_bar", n)
    val = r["values"]; g = GT[n]
    if not val:
        sb[n] = {"result": None, "warnings": r["warnings"]}; continue
    e = {"bar_px": val["bar_length_px"], "gt_bar_px": g["bar_length_px"],
         "bar_err_pct": round(100 * (val["bar_length_px"] - g["bar_length_px"]) / g["bar_length_px"], 2),
         "label": f'{val.get("label_value")} {val.get("label_unit")}', "gt_label": f'{g["label_value"]} {g["label_unit"]}',
         "px_per_um": val.get("px_per_um"), "px_per_nm": val.get("px_per_nm"), "method": val.get("method"),
         "length_source": val.get("bar_length_source"), "label_source": val.get("label_source"),
         "warnings": r["warnings"], "s": round(dt, 2), "device": r["provenance"]["device"]}
    sb[n] = e
for n in ["sem_10um", "sem_500nm"]:
    r, dt = call("read_scale_bar", n, {"method": "fallback"})
    val = r["values"]; g = GT[n]
    sb["fallback:" + n] = None if not val else {"bar_px": val["bar_length_px"], "gt_bar_px": g["bar_length_px"],
        "bar_err_pct": round(100 * (val["bar_length_px"] - g["bar_length_px"]) / g["bar_length_px"], 2),
        "label": f'{val.get("label_value")} {val.get("label_unit")}', "px_per_um": val.get("px_per_um"),
        "method": val.get("method"), "s": round(dt, 2)}
report["read_scale_bar"] = sb
print("read_scale_bar", json.dumps(sb, indent=1))

# ---- chart_to_table
ct = {}
for n in ["bar", "linear", "two_series", "logy"]:
    r, dt = call("chart_to_table", n)
    tab = r["values"]["table"]; g = GT[n]
    errs = []
    if n == "bar":
        got = {row[0]: float(row[1]) for row in tab["rows"] if len(row) > 1}
        errs = [abs(got.get(c, np.nan) - v) / v for c, v in zip(g["categories"], g["values"])]
    else:
        xs_pred = tab["numeric_columns"].get(tab["header"][0] if tab["header"] else "col0", [])
        for j, (sname, s) in enumerate(g["series"].items()):
            col = tab["header"][j + 1] if len(tab["header"]) > j + 1 else None
            ys_pred = tab["numeric_columns"].get(col, []) if col else []
            for xp, yp in zip(xs_pred, ys_pred):
                if xp is None or yp is None:
                    continue
                yt = float(np.interp(xp, s["x"], s["y"]))
                errs.append(abs(yp - yt) / max(abs(yt), 1e-9))
    ct[n] = {"raw": r["values"]["raw_table"][:300], "mean_rel_err": round(float(np.nanmean(errs)), 4) if errs else None,
             "n_values": len(errs), "s": round(dt, 2), "device": r["provenance"]["device"]}
report["chart_to_table"] = ct
print("chart_to_table", json.dumps(ct, indent=1))

# ---- digitize_curve
dc = {}
for method in ["lineformer", "color"]:
    for n in ["linear", "logy", "two_series"]:
        r, dt = call("digitize_curve", n, {"method": method})
        ser = r["values"]["series"]; g = GT[n]["pixel_polylines"]
        res = {}
        for sname, gp in g.items():
            gp = np.array(gp)
            best = None
            for k, s in enumerate(ser):
                p = np.array(s["points"])
                if len(p) < 2:
                    continue
                order = np.argsort(p[:, 0]); p = p[order]
                # evaluate at dense GT x positions within overlap
                xs = np.linspace(gp[:, 0].min(), gp[:, 0].max(), 200)
                yt = np.interp(xs, gp[:, 0], gp[:, 1])
                inside = (xs >= p[0, 0]) & (xs <= p[-1, 0])
                if inside.sum() < 20:
                    continue
                yp = np.interp(xs[inside], p[:, 0], p[:, 1])
                mae = float(np.mean(np.abs(yp - yt[inside]))); cov = float(inside.mean())
                if best is None or mae < best[0]:
                    best = (mae, cov, k)
            res[sname] = {"mean_abs_px_err": round(best[0], 2), "x_coverage": round(best[1], 3), "series_idx": best[2]} if best else None
        dc[f"{method}:{n}"] = {"n_series_pred": len(ser), "n_series_gt": len(g), "per_series": res, "s": round(dt, 2),
                               "device": r["provenance"]["device"], "backing": r["provenance"]["backing_model"]}
report["digitize_curve"] = dc
print("digitize_curve", json.dumps(dc, indent=1))

# determinism check
a, _ = call("chart_to_table", "two_series", seed=1); b, _ = call("chart_to_table", "two_series", seed=1)
c, _ = call("digitize_curve", "two_series", seed=1); d, _ = call("digitize_curve", "two_series", seed=1)
report["determinism"] = {"chart_to_table_repeat_equal": a["values"] == b["values"],
                         "digitize_curve_repeat_equal": c["values"] == d["values"]}
print("determinism", report["determinism"])
json.dump(report, open(os.path.expanduser("~/mcp/plots/smoke/smoke_report.json"), "w"), indent=1)
