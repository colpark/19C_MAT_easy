#!/bin/bash
# kill a sweep by its PID file and its pool children (process group)
cd ~/v5sweep/stage2s/tuning_runs
for n in "$@"; do p=$(cat $n.pid 2>/dev/null); [ -n "$p" ] && kill -9 -- -$p 2>/dev/null; kill -9 $p 2>/dev/null; echo killed $n $p; done
