"""Self-test of the V8-2 instrument. Prints PASS/FAIL per check and ALL WORLD TESTS PASSED if all pass."""
import sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sample as S, render as R, lattice as LAT, fit as F, cost as C

RESULTS = {}
LOG = []


def report(name, ok, msg):
    RESULTS[name] = bool(ok)
    line = "%s  %s  %s" % ("PASS" if ok else "FAIL", name, msg)
    LOG.append(line)
    print(line, flush=True)


def worlds(n, base=1000, hid="HRm-ea", nrep=18):
    return [S.sample_world("AB"[i % 2], hid, nrep, base + i) for i in range(n)]


def measure(w, rod_plan, lat_plan, sd=0):
    r = R.scan_rods(w, rod_plan, sd)
    seg = F.segment_rods(r["img"], r["px_nm"], w["scene"]["length_nm"])
    lf = None
    if lat_plan is not None:
        l = LAT.scan_lattice(w, lat_plan, sd)
        lf = F.fit_lattice(l["img"], l["px_nm"], lat_plan)
    return seg, lf


# (a) determinism ----------------------------------------------------------------------------------------
w1, w2 = S.sample_world("A", "HRm-ea", 18, 7), S.sample_world("A", "HRm-ea", 18, 7)
w3 = S.sample_world("A", "HRm-ea", 18, 8)
same = (np.array_equal(w1["scene"]["centres_nm"], w2["scene"]["centres_nm"]) and np.array_equal(w1["scene"]["angles_deg"], w2["scene"]["angles_deg"])
        and w1["nuisance"] == w2["nuisance"])
diff = w1["nuisance"]["azimuth_deg"] != w3["nuisance"]["azimuth_deg"]
p = C.Plan("rods", 150, 128, 1, 1)
im1, im2 = R.scan_rods(w1, p, 3)["img"], R.scan_rods(w2, p, 3)["img"]
no_overlap_ok = w1["nuisance"]["achieved_coverage"] >= 0.85 * min(w1["nuisance"]["coverage"], 0.25)   # RSA jams near 0.27
report("a_deterministic_in_seed", same and diff and np.array_equal(im1, im2) and no_overlap_ok,
       "world, nuisances and rendered scan identical for equal seed; differ for other seed; achieved coverage %.3f of target %.3f" % (w1["nuisance"]["achieved_coverage"], w1["nuisance"]["coverage"]))

# (b) azimuth hides registry (R6) -----------------------------------------------------------------------------
Ws = worlds(20, 1000)
rod_plan = C.Plan("rods", 250, 256, 1, 1)
Dnl, naive_stat = [], []
for w in Ws:
    seg, _ = measure(w, rod_plan, None)
    th = seg[:, 2]
    Dnl.append(F.fit_D(th, w["truth"]["registry"], None)["D"])
    # naive reading with the scan axes taken as the lattice (a = 0): shows the azimuth scrambles it
    naive_stat.append(F.fit_D(th, w["truth"]["registry"], dict(angle_deg=0.0, sigma_deg=0.1))["D"])
Dnl = np.array(Dnl)
report("b_no_lattice_D_below_9", (Dnl < 9).all(), "20 worlds, max D without lattice scan = %.3g (profiled lattice angle makes the registries degenerate); "
       "info: D with a wrong assumed lattice angle 0 has median %.1f, range %.1f to %.1f (wrong frame, uninformative about the registry)" % (Dnl.max(), np.median(naive_stat), min(naive_stat), max(naive_stat)))
# also: rod-angle statistics are independent of registry (azimuth uniform) - circular mean of 6 theta for A vs B
z = {"A": [], "B": []}
for w in Ws:
    t = np.radians(w["scene"]["angles_deg"] * 0 + S.to_scan_frame(w)[1])
    z[w["truth"]["registry"]].append(abs(np.mean(np.exp(6j * t))))
LOG.append("info b2: mean |<exp(6i theta)>| in scan frame: A %.3f B %.3f (the same distribution of phases, phase uniform)" % (np.mean(z["A"]), np.mean(z["B"])))

# (c) with lattice, true registry beats the alternative -------------------------------------------------------
lat_plan = C.Plan("lattice", 12, 96, 1, 1)
rod_m0 = C.m0_plan()
Wc = worlds(30, 1000)
wins, Ds, laterrs, kaps, lost = 0, [], [], [], []
for w in Wc:
    seg, lf = measure(w, rod_m0, lat_plan)
    r = F.fit_D(seg[:, 2], w["truth"]["registry"], lf)
    oth = "B" if w["truth"]["registry"] == "A" else "A"
    ok = r["ll"][w["truth"]["registry"]] > r["ll"][oth]
    wins += ok
    Ds.append(r["D"])
    laterrs.append(abs((lf["angle_deg"] - w["nuisance"]["azimuth_deg"] + 30) % 60 - 30))
    kaps.append(w["nuisance"]["kappa"])
    if not ok:
        lost.append("kappa %.2f D %.1f" % (w["nuisance"]["kappa"], r["D"]))
Ds, kaps = np.array(Ds), np.array(kaps)
report("c_true_registry_higher_likelihood", wins >= 20, "%d/30 worlds (500 nm 256 px overview + 12 nm 96 px lattice scan); D median %.1f, min %.1f, max %.1f; share with D>9: %.2f; with kappa>=3: D>0 in %d/%d; lattice error median %.2f deg; failures: %s" % (
    wins, np.median(Ds), Ds.min(), Ds.max(), np.mean(Ds > 9), int(np.sum(Ds[kaps >= 3] > 0)), int(np.sum(kaps >= 3)), np.median(laterrs), lost or "none"))

# (d) D rises with pixels and with scan time ---------------------------------------------------------------------
Wd = worlds(16, 2000)


def meanD(rp, lp):
    out = []
    for w in Wd:
        seg, lf = measure(w, rp, lp)
        out.append(F.fit_D(seg[:, 2], w["truth"]["registry"], lf)["D"])
    return float(np.mean(out)), float(np.median(out))


lp = C.Plan("lattice", 12, 96, 1, 2)
pix = []
for npx in (96, 128, 192, 256):
    pl = C.Plan("rods", 300, npx, 1, 1)
    pix.append((npx, pl.minutes(), meanD(pl, lp)))
mp = [m[2][0] for m in pix]
report("d1_D_rises_with_pixels", all(b >= a - 0.5 for a, b in zip(mp, mp[1:])) and mp[-1] > 1.5 * mp[0],
       "fov 300 nm, mean D by npx: " + ", ".join("%d px (%.1f min): %.1f" % (n, t, m[0]) for n, t, m in pix))
tm = []
for lr, fr in ((3.0, 1), (1.0, 1), (1.0, 4)):
    pl = C.Plan("rods", 480, 200, lr, fr)
    tm.append((lr, fr, pl.minutes(), meanD(pl, lp)))
mt = [m[3][0] for m in tm]
report("d2_D_rises_with_scan_time", all(b > a for a, b in zip(mt, mt[1:])),
       "px 2.4 nm rod scans, mean D by (line rate, frames, minutes): " + ", ".join("(%.1f Hz, %d, %.1f min): %.1f" % t[:3] + (t[3][0],) if False else "(%.1f Hz, %d fr, %.1f min): %.1f" % (t[0], t[1], t[2], t[3][0]) for t in tm))

# (d3) lattice orientation error falls with pixel count and scan time ----------------------------------------------
import copy
Wall = [S.sample_world('AB'[i % 2], 'HRm-ea', 18, 3000 + i, place_rods_flag=False) for i in range(40)]
# estimator-scaling check: drift switched off and noise fixed at its upper value, so the noise term is isolated;
# the drift floor of the full population is reported separately as an info line.
Wl = []
for w in Wall:
    w2 = copy.deepcopy(w)
    w2["nuisance"].update(drift_nm_min=1e-6, noise_nm=0.30)
    Wl.append(w2)


def laterr(plan, W=None):
    e, s = [], []
    for w in (Wl if W is None else W):
        l = LAT.scan_lattice(w, plan)
        f = F.fit_lattice(l["img"], l["px_nm"], plan)
        if f is None:
            return None
        e.append(abs((f["angle_deg"] - w["nuisance"]["azimuth_deg"] + 30) % 60 - 30))
        s.append(f["sigma_deg"])
    return float(np.median(e)), float(np.sqrt(np.mean(np.square(e)))), float(np.median(s))


# pixel count raised along the fast axis (64 lines, so the scan time is unchanged); time raised by averaging registered frames
lp_px = [(n, laterr(C.Plan("lattice", 12, n, n / 64.0, 1))) for n in (64, 96, 128, 256)]
lp_t = [(fr, laterr(C.Plan("lattice", 12, 64, 1, fr, nlines=32))) for fr in (1, 2, 4, 8)]
a = [v[1][1] for v in lp_px]      # rms error
b = [v[1][1] for v in lp_t]
slope_px = np.polyfit(np.log([n * n for n, _ in lp_px]), np.log(a), 1)[0]
slope_t = np.polyfit(np.log([1, 2, 4, 8]), np.log(b), 1)[0]
report("d3_lattice_error_falls_with_pixels", slope_px < -0.2 and a[-1] < 0.6 * a[0],
       "log-log slope of rms error vs pixel count %.2f (rms %.3f to %.3f deg); %d worlds, drift off, noise 0.30 nm, square scans 12 nm, line rate scaled with npx (frame time constant): " % (slope_px, a[0], a[-1], len(Wl))
       + ", ".join("%d x %d px (%.1f Hz): median %.3f, rms %.3f, est sigma %.3f" % ((n, n, n / 64.0) + v) for n, v in lp_px))
report("d3b_lattice_error_falls_with_scan_time", slope_t < -0.2 and b[-1] < 0.6 * b[0],
       "log-log slope of rms error vs frames (time) %.2f (rms %.3f to %.3f deg); 64 px x 32 lines, 1 to 8 frames (1.5 to 5.0 min): " % (slope_t, b[0], b[-1])
       + ", ".join("%d frames: median %.3f, rms %.3f, est sigma %.3f" % ((fr,) + v) for fr, v in lp_t))

# info: drift floor with the full (calibrated-noise, drift on) population
fl = laterr(C.Plan("lattice", 12, 128, 2.0, 1), Wall)
LOG.append("info d3c: full population (drift on, calibrated noise), 128 px at 2 Hz: lattice median |error| %.3f deg, rms %.3f, est sigma %.3f: error is drift-limited near 0.1 deg" % fl)
print(LOG[-1])

# (e) tiled rods aspect ----------------------------------------------------------------------------------------------
dims = json.load(open(os.path.expanduser("~/v8_data/rods/dims.json")))
asp = {k: v["aspect"] for k, v in dims.items() if k.endswith("rep")}
ok18 = all(v >= 4 for k, v in asp.items() if k.endswith("18rep"))
report("e_tiled_rods_aspect_ge_4", ok18, "aspect: " + ", ".join("%s %.2f" % (k, v) for k, v in sorted(asp.items())) +
       " (all 18-repeat rods reach >= 4; the C-design 14-repeat rods reach only %.2f, the U0 14-repeat %.2f)" % (asp["HRm-60_14rep"], asp["HRm-ea_14rep"]))

json.dump(dict(results=RESULTS, lines=LOG), open(os.path.expanduser("~/v8_data/test_world_result.json"), "w"), indent=1)
if all(RESULTS.values()):
    print("ALL WORLD TESTS PASSED")
else:
    print("SOME WORLD TESTS FAILED: " + ", ".join(k for k, v in RESULTS.items() if not v))
