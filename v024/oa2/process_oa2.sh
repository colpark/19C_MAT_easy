#!/bin/bash
# process_oa2.sh: oa2 papers through the final v0.24 pipeline: frozen setup -> converter r1-M6 -> store (MinerU) -> detect/OCR/match ->
# matcher r1-NAT/r1-OCR -> items with rules r1 + r1-C1b (ids from 501) -> frozen r2.
set -euo pipefail; cd "$(dirname "$0")"; V=$HOME/Documents/harbor/v024
python3 driver_oa2.py setup
mkdir -p work_r1b && cp $V/work_r1b/levels.py $V/work_r1b/open.py work_r1b/
sha256sum work_r1b/levels.py | cut -c1-16
python3 - <<'PY'
import json, importlib.util
spec = importlib.util.spec_from_file_location('m', '/home/aid1/Documents/harbor/v024/conv_r1m6/mineru_paras.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
K = json.load(open('paper_keys.json')); z = 0
for k, v in K.items():
    out, _ = m.run(k, f"mineru_out/{v['safe']}/auto/{v['safe']}_content_list.json", f'work_r1b/{k}.paras.json', '2.7.6'); z += not out
print('converted (r1-M6)', len(K), '| zero-paragraph papers', z)
PY
python3 driver_oa2.py store 2>&1 | tail -4
~/panels/.venv/bin/python $V/match_r1nat/match_panels.py --root store --out-dir panel_runs/match_panels_r1nat --ocr --workers 8 > /dev/null 2>&1
python3 -c "
import json,glob,collections
print('tiers',collections.Counter((f['tier'],f['reason'][:6]) for m in glob.glob('store/**/panels/match.json',recursive=True) for f in json.load(open(m))['figures']).most_common(6))"
RULES_DIR=work_r1b ITEMS_SUFFIX=_r1 python3 driver_oa2.py items mineru
python3 apply_r2.py | grep -E "removed by any|items in set"
python3 -c "
import json,collections;I=json.load(open('open_items_mineru_r1.json'))['items'];F=json.load(open('r2_flags_oa2.json'))
k=[i for i in I if not F[i['id']]['removed_by'] and i.get('type')!='trend'];print('papers with items',len({i['paper'] for i in I}),'/ 69 | pool',len(k),dict(sorted(collections.Counter(i['level'] for i in k).items())),'papers',len({i['paper'] for i in k}))"
