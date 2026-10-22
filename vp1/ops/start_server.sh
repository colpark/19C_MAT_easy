#!/bin/bash
# vP.1: start one vP.1 server process on node A2 (ports 8820-8829 only), from ~/vp1srv, state ~/vp1_state, BLAS caps (V6-E4).
# Writes ~/vp1_state/pids/PORT.pid. Refuses a port outside 8820-8829 or one already bound. Stop with: kill $(cat ~/vp1_state/pids/PORT.pid)
set -e
PORT=$1
[[ "$PORT" =~ ^882[0-9]$ ]] || { echo "port $PORT outside 8820-8829"; exit 1; }
if ss -ltn | grep -q "192.168.100.11:$PORT "; then echo "port $PORT already bound"; exit 1; fi
STATE=$HOME/vp1_state
mkdir -p $STATE/pids $STATE/srvlog && chmod 700 $STATE
cd $HOME/vp1srv
cat mcenv/*.py kit/ref/*.py | sha256sum | cut -c1-16 > $STATE/srvlog/CODE_SHA_$PORT
MCENV_STATE=$STATE MCENV_BIND=192.168.100.11 MCENV_PORT=$PORT OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  setsid nohup $HOME/v5env/bin/python -m mcenv.server_vp1 > $STATE/srvlog/server_$PORT.log 2>&1 < /dev/null &
echo $! > $STATE/pids/$PORT.pid
sleep 8
echo "port $PORT pid $(cat $STATE/pids/$PORT.pid) code $(cat $STATE/srvlog/CODE_SHA_$PORT)"; tail -2 $STATE/srvlog/server_$PORT.log
