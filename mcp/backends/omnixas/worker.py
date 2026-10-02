"""OmniXAS backend worker (PanelBench MCP toolset v1, family `omnixas`).

Tool: xas_predict -- K-edge XANES prediction from a crystal structure (CIF text)
using the OmniXAS pipeline: M3GNet (MP-2021.2.8-PES) site embeddings -> XASBlock
(v1.1.1 checkpoints, one per element/source). CPU only.

Endpoints: GET /health, GET /version, POST /xas_predict
Body: {"args": {"cif": str, "absorber": "Cu", "site_index": "all"|int, "source": "FEFF"|"VASP"}, "seed": int}

Pipeline reproduced from OmniXAS (BSD-3, BNL) omnixas/utils/lightshow.py and
omnixas/featurizer/m3gnet_featurizer.py at commit 57a6282d.
"""
import os

os.environ.setdefault("DGLBACKEND", "pytorch")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".mplcache"))

import hashlib
import importlib.metadata
import json
import logging
import random
import sys
import time
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(os.environ.get("OMNIXAS_ROOT", Path(__file__).resolve().parent))
WEIGHTS = ROOT / "weights"
XASBLOCK_DIR = WEIGHTS / "xasblock" / "v1.1.1"
M3GNET_DIR = WEIGHTS / "M3GNet-MP-2021.2.8-PES"
REQUEST_LOG = ROOT / "requests.log"
PORT = int(os.environ.get("OMNIXAS_PORT", "8105"))

TOOL = "xas_predict"
TOOL_VERSION = "omnixas-worker 1.0 (OmniXAS 57a6282d, xasblock v1.1.1)"
OMNIXAS_COMMIT = "57a6282d3c6717586a1a562614c64a5d18d3ba6f"

SUPPORTED = {
    "FEFF": ["Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu"],
    "VASP": ["Ti", "Cu"],
}
# config/data/transformations.yaml: e_start per element, e_range_diff = 35 eV,
# 0.25 eV resolution -> 141 points (same window used for FEFF and VASP data).
E_START = {
    "Co": 7709.282, "Cr": 5989.168, "Cu": 8983.173, "Fe": 7111.23,
    "Mn": 6537.886, "Ni": 8332.181, "Ti": 4964.504, "V": 5464.097,
}
N_POINTS = 141
DE = 0.25
FEATURE_SCALE = 1000.0  # features *1e3 at training time (ThousandScaler)
TARGET_SCALE = 1000.0   # spectra *1e3 at training time
HIDDEN = [500, 500, 550]  # v1.1.1 widths (tunedUniversalXAS); verified from checkpoint shapes

UNAVAILABLE_ERROR: Optional[str] = None
try:
    import numpy as np
    import torch
    from torch import nn
    from pymatgen.core import Structure
    from matgl import load_model
    from matgl.ext.pymatgen import Structure2Graph
    from matgl.graph.compute import (
        compute_pair_vector_and_distance,
        compute_theta_and_phi,
        create_line_graph,
    )
    from matgl.utils.cutoff import polynomial_cutoff
    import dgl
    import matgl
    import pymatgen
    torch.set_num_threads(int(os.environ.get("OMNIXAS_THREADS", "8")))
    torch.use_deterministic_algorithms(True, warn_only=True)
except Exception as e:  # environment not buildable -> report exact error
    UNAVAILABLE_ERROR = f"{type(e).__name__}: {e}"

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

warnings.filterwarnings("ignore", category=FutureWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("omnixas-worker")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@lru_cache(maxsize=1)
def weight_hashes() -> Dict[str, str]:
    out = {}
    for p in sorted(XASBLOCK_DIR.glob("*.ckpt")):
        out[f"xasblock/v1.1.1/{p.name}"] = sha256_file(p)
    for name in ("model.json", "model.pt", "state.pt"):
        p = M3GNET_DIR / name
        if p.exists():
            out[f"M3GNet-MP-2021.2.8-PES/{name}"] = sha256_file(p)
    return out


def seed_all(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


if UNAVAILABLE_ERROR is None:

    class XASBlock(nn.Sequential):
        def __init__(self, input_dim, hidden_dims, output_dim):
            dims = [input_dim] + list(hidden_dims) + [output_dim]
            layers = []
            for i, (w1, w2) in enumerate(zip(dims[:-1], dims[1:])):
                layers.append(nn.Linear(w1, w2))
                if i < len(dims) - 2:
                    layers += [nn.BatchNorm1d(w2), nn.SiLU(), nn.Dropout(0.5)]
                else:
                    layers.append(nn.Softplus())
            super().__init__(*layers)

    @lru_cache(maxsize=1)
    def m3gnet():
        model = load_model(str(M3GNET_DIR)).model
        model.eval()
        return model

    @lru_cache(maxsize=16)
    def xasblock(element: str, source: str):
        path = XASBLOCK_DIR / f"{element}_{source}.ckpt"
        ckpt = torch.load(path, map_location="cpu")
        sd = {k[len("model."):]: v for k, v in ckpt["state_dict"].items() if k.startswith("model.")}
        hidden = [sd[f"{4 * i}.weight"].shape[0] for i in range(len(HIDDEN))]
        net = XASBlock(64, hidden, N_POINTS)
        net.load_state_dict(sd, strict=True)
        net.eval()
        return net

    def m3gnet_node_features(structure) -> "np.ndarray":
        """Node embeddings after all M3GNet graph blocks (OmniXAS M3GNetFeaturizer)."""
        model = m3gnet()
        conv = Structure2Graph(model.element_types, model.cutoff)
        g, state_attr = conv.get_graph(structure)
        node_types = g.ndata["node_type"]
        bond_vec, bond_dist = compute_pair_vector_and_distance(g)
        g.edata["bond_vec"] = bond_vec
        g.edata["bond_dist"] = bond_dist
        with torch.no_grad():
            expanded = model.bond_expansion(g.edata["bond_dist"])
            l_g = create_line_graph(g, model.threebody_cutoff)
            l_g.apply_edges(compute_theta_and_phi)
            g.edata["rbf"] = expanded
            tb_basis = model.basis_expansion(l_g)
            tb_cut = polynomial_cutoff(g.edata["bond_dist"], model.threebody_cutoff)
            node_feat, edge_feat, state_feat = model.embedding(node_types, g.edata["rbf"], state_attr)
            for i in range(model.n_blocks):
                edge_feat = model.three_body_interactions[i](g, l_g, tb_basis, tb_cut, node_feat, edge_feat)
                edge_feat, node_feat, state_feat = model.graph_layers[i](g, edge_feat, node_feat, state_feat)
        return node_feat.detach().cpu().numpy().astype(np.float32)

    def predict_from_features(feats: "np.ndarray", element: str, source: str) -> "np.ndarray":
        net = xasblock(element, source)
        with torch.no_grad():
            y = net(torch.tensor(feats * FEATURE_SCALE, dtype=torch.float32))
        return y.numpy() / TARGET_SCALE

    def energy_grid(element: str) -> "np.ndarray":
        return E_START[element] + DE * np.arange(N_POINTS)


class ToolError(Exception):
    pass


def run_xas_predict(args: Dict[str, Any], seed: int = 0) -> Dict[str, Any]:
    cif = args.get("cif")
    absorber = str(args.get("absorber", "")).strip()
    source = str(args.get("source", "FEFF")).strip().upper()
    site_index = args.get("site_index", "all")
    if not isinstance(cif, str) or not cif.strip():
        raise ToolError("args.cif must be non-empty CIF text")
    if source not in SUPPORTED:
        raise ToolError(f"source must be FEFF or VASP, got {source!r}")
    absorber = absorber[:1].upper() + absorber[1:].lower()
    if absorber not in SUPPORTED[source]:
        raise ToolError(
            f"absorber {absorber!r} not supported for source={source}; "
            f"OmniXAS v1.1.1 provides K-edge models only for {SUPPORTED[source]}"
        )
    seed_all(seed)
    warns = []
    try:
        with warnings.catch_warnings(record=True) as wlist:
            warnings.simplefilter("always")
            structure = Structure.from_str(cif, fmt="cif")
        for w in [w for w in wlist if not issubclass(w.category, (FutureWarning, DeprecationWarning))][:5]:
            warns.append(f"CIF parser: {w.message}")
    except Exception as e:
        raise ToolError(f"could not parse CIF: {type(e).__name__}: {e}")
    if not structure.is_ordered:
        raise ToolError("structure has partial occupancies; OmniXAS/M3GNet need an ordered structure")
    abs_sites = [i for i, s in enumerate(structure) if s.specie.symbol == absorber]
    if not abs_sites:
        raise ToolError(f"absorber {absorber} not present in structure ({structure.composition.reduced_formula})")
    if isinstance(site_index, str) and site_index.strip().lower() == "all":
        sel = abs_sites
    else:
        try:
            idx = int(site_index)
        except Exception:
            raise ToolError(f"site_index must be 'all' or an integer, got {site_index!r}")
        if idx not in abs_sites:
            raise ToolError(f"site_index {idx} is not a {absorber} site; {absorber} sites are {abs_sites}")
        sel = [idx]
    if len(structure) > 500:
        warns.append(f"large cell ({len(structure)} sites); featurization may be slow")
    try:
        feats = m3gnet_node_features(structure)
    except Exception as e:
        raise ToolError(f"M3GNet featurization failed: {type(e).__name__}: {e}")
    spectra = predict_from_features(feats[sel], absorber, source)
    mean = spectra.mean(axis=0)
    if source == "VASP":
        warns.append("VASP models were trained on excited-atom supercell (core-hole) spectra; "
                     "site features here come from the input cell as given")
    warns.append("no uncertainty estimate: XASBlock is a deterministic MLP (confidence=null)")
    return {
        "values": {
            "energy": [round(float(e), 4) for e in energy_grid(absorber)],
            "mu": [float(v) for v in mean],
            "edge": "K",
            "absorber": absorber,
            "source": source,
            "site_indices": sel,
            "n_sites_averaged": len(sel),
            "per_site_mu": {str(i): [float(v) for v in s] for i, s in zip(sel, spectra)} if len(sel) <= 64 else None,
            "formula": structure.composition.reduced_formula,
        },
        "units": {"energy": "eV (OmniXAS absolute grid: e_start + 0.25 eV steps, 35 eV window)",
                  "mu": "absorption cross-section, OmniXAS training-data units (FEFF mu / a0^2; VASP scaled), not edge-step normalized"},
        "confidence": None,
        "warnings": warns,
    }


app = FastAPI(title="omnixas worker")


@app.get("/health")
def health():
    if UNAVAILABLE_ERROR:
        return {"status": "unavailable", "error": UNAVAILABLE_ERROR}
    return {"status": "ok", "device": "cpu", "tools": [TOOL]}


@app.get("/version")
def version():
    v = {"tool": TOOL, "tool_version": TOOL_VERSION, "omnixas_commit": OMNIXAS_COMMIT,
         "python": sys.version.split()[0], "weights_sha256": weight_hashes()}
    if UNAVAILABLE_ERROR is None:
        v.update({"torch": torch.__version__, "dgl": dgl.__version__, "matgl": matgl.__version__,
                  "pymatgen": importlib.metadata.version("pymatgen"), "numpy": np.__version__})
    else:
        v["status"] = "unavailable"
        v["error"] = UNAVAILABLE_ERROR
    return v


def log_request(tool: str, input_sha: str, args: Dict[str, Any], duration: float, status: str):
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "tool": tool, "input_sha256": input_sha,
           "args": args, "duration_s": round(duration, 4), "status": status}
    with open(REQUEST_LOG, "a") as f:
        f.write(json.dumps(rec) + "\n")


@app.post("/" + TOOL)
def xas_predict(body: Dict[str, Any]):
    t0 = time.time()
    args = dict(body.get("args") or {})
    seed = int(body.get("seed", 0) or 0)
    cif = args.get("cif") or ""
    input_sha = hashlib.sha256(cif.encode() if isinstance(cif, str) else b"").hexdigest()
    logged_args = {k: v for k, v in args.items() if k != "cif"}
    if UNAVAILABLE_ERROR:
        log_request(TOOL, input_sha, logged_args, time.time() - t0, "unavailable")
        return {"status": "unavailable", "error": UNAVAILABLE_ERROR}
    try:
        out = run_xas_predict(args, seed)
    except ToolError as e:
        log_request(TOOL, input_sha, logged_args, time.time() - t0, "error")
        return JSONResponse(status_code=400, content={"error": str(e), "warnings": []})
    except Exception as e:
        log_request(TOOL, input_sha, logged_args, time.time() - t0, "error")
        return JSONResponse(status_code=500, content={"error": f"{type(e).__name__}: {e}"})
    absorber = out["values"]["absorber"]
    source = out["values"]["source"]
    hashes = weight_hashes()
    out["provenance"] = {
        "tool": TOOL,
        "tool_version": TOOL_VERSION,
        "backing_model": f"OmniXAS XASBlock v1.1.1 {absorber}_{source} + M3GNet-MP-2021.2.8-PES featurizer",
        "weights_sha256": {
            "xasblock": hashes.get(f"xasblock/v1.1.1/{absorber}_{source}.ckpt"),
            "m3gnet_state": hashes.get("M3GNet-MP-2021.2.8-PES/state.pt"),
        },
        "seed": seed,
        "device": "cpu",
        "input_sha256": input_sha,
        "duration_s": round(time.time() - t0, 4),
    }
    log_request(TOOL, input_sha, logged_args, time.time() - t0, "ok")
    return out


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
