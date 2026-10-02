# science worker (node 2, port 8104)

Code only. Runtime assets stay on node 2 under `~/mcp/science/`: `.venv/`, `weights/` (MACE-MPA-0, Orb v3),
`structlib/` (43 COD CIFs + index.json), `tdb/` (3 openly licensed TDBs), `validation/` (abTEM reference images).

Start (on node 2):

    ~/mcp/science/start.sh                    # foreground, 0.0.0.0:8104, GPU if available
    SCIENCE_DEVICE=cpu ~/mcp/science/start.sh # force CPU

Endpoints: `GET /health`, `GET /version`, `POST /<tool>` with `{"args": {...}, "seed": 0}`.
Tools: xrd_simulate, xrd_phase_match (fallback peak-list matcher, not Dara/BGMN), peak_fit, xas_edge, mlip_energy,
phase_equilibria, simulate_tem. Structures can be given as `cif` (text), `phase` (structlib key) or `formula`.
Requests are logged to `~/mcp/science/requests.log`. No network at request time.

Other files: `build_structlib.py` rebuilds the COD structure library (needs network), and `make_validation.py`
regenerates `validation/` (Si [110] / Al [001] HRTEM, Si [110] diffraction, known d-spacings JSON).
See `../../env_logs/science.md` for versions, licenses and hashes.
