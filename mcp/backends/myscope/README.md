# myscope backend (sem-sim)
Vendored SEM simulator `sem_api` 1.0.0 from myscopegit-main.zip (sha256 3bb7dd7b1da3ab5d...; numpy/scipy/Pillow only; 29/29 tests pass on node 2).
Runs as its own stdlib HTTP server on node 2 port 8106: `~/mcp/myscope/start.sh`
(`python -c "from sem_api.server import serve; serve(host='0.0.0.0', port=8106)"`). Endpoints used: GET /health, /schema, /metadata?..., POST /render?format=json.
The hub (port 8099) calls it for `sem_optics` (/metadata) and `sem_simulate` (/render?format=json); out-of-range values return the
API's boundary error unchanged (no clamp).
