# omnixas backend (node 2, port 8105, CPU)

Tool `xas_predict`: CIF -> M3GNet (MP-2021.2.8-PES) site embeddings -> OmniXAS XASBlock v1.1.1 -> K-edge XANES
(141 points, 0.25 eV, 35 eV window starting at OmniXAS `e_start[element]`), averaged over the selected absorber sites.
FEFF models: Ti V Cr Mn Fe Co Ni Cu. VASP models: Ti Cu. Other elements are refused (HTTP 400).

Start on node 2:  `~/mcp/omnixas/start.sh`   (venv `~/mcp/omnixas/.venv`, weights `~/mcp/omnixas/weights/`)

    curl localhost:8105/health ; curl localhost:8105/version
    POST /xas_predict  {"args": {"cif": "<cif text>", "absorber": "Cu", "site_index": "all", "source": "FEFF"}, "seed": 0}

Returns values.energy (eV), values.mu (site-averaged), values.per_site_mu, values.site_indices (0-based indices into the
parsed CIF structure). confidence is null (no UQ). Files here: worker.py, start.sh, validate.py (tutorial Cu FEFF check).
