#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u); B="ssh -i $HOME/.ssh/id_ed25519_shared -o LogLevel=ERROR aid1@130.199.95.15"
cd "$(dirname "$0")"
until [ "$(systemctl --user is-active mineru-oa2)" != active ] && [ "$($B 'XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user is-active mineru-oa2' 2>/dev/null | tail -1)" != active ]; do sleep 60; done
systemctl --user stop gov-oa2; $B 'XDG_RUNTIME_DIR=/run/user/$(id -u) systemctl --user stop gov-oa2'
journalctl --user -u mineru-oa2 --no-pager | grep -E "chunk |all done" | tail -4
$B 'XDG_RUNTIME_DIR=/run/user/$(id -u) journalctl --user -u mineru-oa2 --no-pager | grep -E "chunk |all done" | tail -4; ls ~/Documents/harbor/v024/oa2/logs | grep -c failed'
rsync -a -e "ssh -i $HOME/.ssh/id_ed25519_shared -o LogLevel=ERROR" aid1@130.199.95.15:Documents/harbor/v024/oa2/mineru_out/ mineru_out/
echo "mineru_out papers: $(ls mineru_out | wc -l)"
./process_oa2.sh
