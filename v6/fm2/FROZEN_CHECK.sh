#!/bin/bash
# hard rule 4: the frozen files must stay byte-identical; run at every push (exit 1 on any change)
cd "$(dirname "$0")/.."
ok=0
while read -r h f; do
  [ -z "$f" ] && continue
  g=$(sha256sum "$f" | cut -c1-16)
  if [ "$g" != "$h" ]; then echo "CHANGED $f ($g, frozen $h)"; ok=1; fi
done < fm2/FROZEN.txt
[ $ok -eq 0 ] && echo "frozen files byte-identical"
exit $ok
