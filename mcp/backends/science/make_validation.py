"""Generate abTEM validation images for later tool checks: Si [110] HRTEM, Al [001] HRTEM, Si [110] diffraction."""
import sys, json, base64, numpy as np
sys.path.insert(0, "/home/aid1/mcp/science")
import worker as W
from pymatgen.core import Structure
out = "/home/aid1/mcp/science/validation"
def dset(phase, hkls):
    s = Structure.from_file(f"/home/aid1/mcp/science/structlib/{phase}.cif")
    return s.lattice.abc[0], {"".join(map(str, h)): round(float(s.lattice.d_hkl(h)), 4) for h in hkls}
cases = [
  ("si_110_hrtem", {"phase": "Si", "mode": "hrtem", "zone_axis": [1, 1, 0], "thickness_nm": 5, "energy_kv": 200},
   "Si", [(1,1,1),(0,0,2),(2,2,0),(1,1,3),(0,0,4),(2,2,2)], "Si [110] zone: {111} 3.135 A fringes, {002} (kinematically forbidden, appears dynamically), {220}"),
  ("al_001_hrtem", {"phase": "Al", "mode": "hrtem", "zone_axis": [0, 0, 1], "thickness_nm": 5, "energy_kv": 200},
   "Al", [(2,0,0),(2,2,0),(4,0,0)], "Al [001] zone: {200} 2.025 A cross fringes, {220} 1.432 A"),
  ("si_110_diffraction", {"phase": "Si", "mode": "diffraction", "zone_axis": [1, 1, 0], "thickness_nm": 5, "energy_kv": 200},
   "Si", [(1,1,1),(0,0,2),(2,2,0),(1,1,3),(0,0,4),(3,3,1),(2,2,4)], "Si [110] SAED: 111/-1-11 spots 3.135 A, 002 (dynamical), 220 1.920 A"),
]
summary = {}
for name, args, ph, hkls, note in cases:
    r = W.run_tool("simulate_tem", {"args": args, "seed": 0})
    assert r["values"] is not None, r["warnings"]
    img = list(r["images"].values())[0]
    open(f"{out}/{name}.png", "wb").write(base64.b64decode(img))
    a, d = dset(ph, hkls)
    v = r["values"]
    meta = {k: v[k] for k in v if k not in ("spots",)}
    if "spots" in v: meta["spots_top12"] = v["spots"][:12]
    summary[name] = {"png": f"{name}.png", "args": args, "lattice_a_A": round(a, 5), "known_d_spacings_A": d, "note": note,
                     "simulation": meta, "known_values_source": "d_hkl computed by pymatgen from the structlib CIF lattice (COD)", "provenance": r["provenance"]}
    print(name, r["provenance"]["duration_s"], v.get("fft_d_spacings_A") or [sp["d_A"] for sp in v["spots"][:10]])
json.dump(summary, open(f"{out}/validation.json", "w"), indent=1)
