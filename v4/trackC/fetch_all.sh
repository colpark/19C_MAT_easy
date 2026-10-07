#!/bin/bash
# C0.4 download queue: one file at a time through mc_fetch.py (gap >= 2 s + jitter inside).
# Sizes and md5s come from the record metadata fetched by `mc_fetch.py meta` (logged first).
# Each record lands in its own directory under $RAW (untrusted data, no code runs there).
set -u
V4=$(cd "$(dirname "$0")/.." && pwd)
PY="$V4/.venv-trackC/bin/python -I $V4/trackC/mc_fetch.py"
RAW=${RAW:-$HOME/Documents/harbor/v4_host/trackC/raw}
LOG=${LOG:-$HOME/Documents/harbor/v4_host/trackC/fetch_log.jsonl}
MC=https://archive.materialscloud.org/api/records
mkdir -p "$RAW"/{xm-46,1c-13,figshare_21370572,arxiv}
# record  key  size  md5   (small first, large last)
while read -r rec dir key size md5; do
  [ -z "$rec" ] && continue
  $PY get "$MC/$rec/files/$key/content" --out "$RAW/$dir/$key" --size "$size" --md5 "$md5" --log "$LOG" \
    && echo "ok $dir/$key" || echo "FAIL $dir/$key"
done <<'EOF'
5zenj-34e64 xm-46 README.txt 2295 f095df76465d8cbfa7fb1680485dd381
5zenj-34e64 xm-46 fpmd_structures.aiida 152821 14c51c3917335cb116124047dec4f369
nf76v-1eh14 1c-13 README.txt 906 6bda2aadaf60bd0eca43369728d29041
nf76v-1eh14 1c-13 structures.aiida 154061 f6a417e9cd25bafc7dc9d6d8da5380db
nf76v-1eh14 1c-13 fine-tuning.xyz 31489662 480817368cb5545b7fce43409e82dd22
5zenj-34e64 xm-46 fpmd_screening_Li7NbO6.aiida 531561482 f78e4ba790f31ef7ba18dc2fb4ec3df1
EOF
$PY get https://ndownloader.figshare.com/files/38307921 --out "$RAW/figshare_21370572/jarvis_epc_data_figshare_1058.json.zip" --size 8828364 --md5 bb4a91e899458f34cbb3b9bf03e9bd56 --log "$LOG" && echo ok fs1058 || echo FAIL fs1058
$PY get https://ndownloader.figshare.com/files/38950433 --out "$RAW/figshare_21370572/jarvis_epc_data_2d.json.zip" --size 636970 --md5 721df1cc069296d02d6653bbed527229 --log "$LOG" && echo ok fs2d || echo FAIL fs2d
$PY get https://arxiv.org/pdf/2601.03151 --out "$RAW/arxiv/2601.03151.pdf" --log "$LOG" && echo ok arxiv || echo FAIL arxiv
[ "${SMALL_ONLY:-0}" = 1 ] && exit 0
while read -r rec dir key size md5; do
  [ -z "$rec" ] && continue
  $PY get "$MC/$rec/files/$key/content" --out "$RAW/$dir/$key" --size "$size" --md5 "$md5" --log "$LOG" \
    && echo "ok $dir/$key" || echo "FAIL $dir/$key"
done <<'EOF'
5zenj-34e64 xm-46 fpmd_trajectories.aiida 17114143073 88ea15082b6afda3160a205296a75221
nf76v-1eh14 1c-13 trajectories.tar.xz 23605149375 b5b0ed013cdd4c70443468d742ab96a3
EOF
