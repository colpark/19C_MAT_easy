"""Validate OmniXAS worker against tutorial Cu FEFF data (CU_FEFF.npz)."""
import os, sys, time, json
sys.path.insert(0, os.path.expanduser("~/mcp/omnixas"))
import numpy as np
import worker as W
from pymatgen.core import Structure

T = os.path.expanduser("~/mcp/omnixas/src/tutorial_omnixas")
d = np.load(f"{T}/CU_FEFF.npz")
ids, sites, E, X, Y = d["ids"], d["sites"], d["energies"], d["features"], d["spectras"]
res = {}
res["energy_grid_match"] = bool(np.allclose(E, W.energy_grid("Cu")))
key = {f"{i}_{s}": k for k, (i, s) in enumerate(zip(ids, sites))}
test = [l.strip() for l in open(f"{T}/material_id_and_site/Cu_FEFF_test.txt")]
test_idx = [key[t] for t in test if t in key]
res["n_test"] = len(test_idx)

def mse(a, b): return float(np.mean((a - b) ** 2))
# (b) stored features -> model
P_all = W.predict_from_features(X, "Cu", "FEFF")
res["stored_feat_mse_all_x1e3"] = mse(P_all * 1e3, Y * 1e3)
res["stored_feat_mse_test_x1e3"] = mse(P_all[test_idx] * 1e3, Y[test_idx] * 1e3)
res["stored_feat_mse_test_raw"] = mse(P_all[test_idx], Y[test_idx])
# mean-model baseline on test
res["meanmodel_mse_test_x1e3"] = mse(np.tile(Y.mean(0), (len(test_idx), 1)) * 1e3, Y[test_idx] * 1e3)

# (a) full pipeline: POSCAR -> M3GNet -> XASBlock on test entries
t0 = time.time(); feats = []; preds = []; tgt = []; fd = []
cache = {}
for k in test_idx:
    mid, s = ids[k], int(sites[k])
    p = f"{T}/FEFF/Cu/{mid}/POSCAR"
    if not os.path.exists(p): continue
    if mid not in cache:
        cache[mid] = W.m3gnet_node_features(Structure.from_file(p))
    f = cache[mid][s]
    fd.append(np.max(np.abs(f - X[k])) / (np.max(np.abs(X[k])) + 1e-12))
    feats.append(f); tgt.append(Y[k])
F = np.array(feats); Yt = np.array(tgt)
P = W.predict_from_features(F, "Cu", "FEFF")
res["pipeline_n"] = len(F)
res["pipeline_time_s"] = round(time.time() - t0, 2)
res["feature_rel_maxdiff_median"] = float(np.median(fd)); res["feature_rel_maxdiff_max"] = float(np.max(fd))
res["pipeline_mse_test_x1e3"] = mse(P * 1e3, Yt * 1e3)
res["pipeline_mse_test_raw"] = mse(P, Yt)

# (c) the repo's lightshow example: mp-1005792 site 8, through CIF + run_xas_predict
st = Structure.from_file(f"{T}/FEFF/Cu/mp-1005792/POSCAR")
cif = st.to(fmt="cif")
t0 = time.time()
out = W.run_xas_predict({"cif": cif, "absorber": "Cu", "site_index": 8, "source": "FEFF"}, seed=0)
res["example_time_s"] = round(time.time() - t0, 3)
k = key.get("mp-1005792_008")
pred = np.array(out["values"]["mu"])
res["example_in_npz"] = k is not None
if k is not None:
    res["example_mse_x1e3"] = mse(pred * 1e3, Y[k] * 1e3)
    res["example_split"] = "test" if "mp-1005792_008" in test else "train/val"
out2 = W.run_xas_predict({"cif": cif, "absorber": "Cu", "site_index": "all", "source": "FEFF"}, seed=0)
res["example_all_sites"] = out2["values"]["site_indices"]
out3 = W.run_xas_predict({"cif": cif, "absorber": "Cu", "site_index": 8, "source": "FEFF"}, seed=0)
res["deterministic"] = out3["values"]["mu"] == out["values"]["mu"]
for bad in [{"absorber": "Zn", "source": "FEFF"}, {"absorber": "Fe", "source": "VASP"}]:
    try: W.run_xas_predict({"cif": cif, **bad}); res[f"refuse_{bad['absorber']}"] = "NOT REFUSED"
    except W.ToolError as e: res[f"refuse_{bad['absorber']}_{bad['source']}"] = str(e)
print(json.dumps(res, indent=1))
