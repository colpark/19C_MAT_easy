#!/bin/bash
# Freezes the ollama-qwen user service (SIGSTOP) when any sensor reaches HOT C, resumes (SIGCONT) at or below COOL C.
# Sensors: ACPI thermal zones, hwmon (nvme, mlx5), GPU (nvidia-smi). Log: governor.log next to this script.
HOT=${HOT:-80}; COOL=${COOL:-65}; UNIT=${UNIT:-ollama-qwen}; LOG=$(dirname "$0")/governor.log
export XDG_RUNTIME_DIR=/run/user/$(id -u)
state=running
maxtemp() { local m=0 t; for f in /sys/class/thermal/thermal_zone*/temp /sys/class/hwmon/hwmon*/temp*_input; do t=$(( $(cat $f 2>/dev/null || echo 0) / 1000 )); [ $t -gt $m ] && m=$t; done
  t=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -1); [ -n "$t" ] && [ "$t" -gt $m ] 2>/dev/null && m=$t; echo $m; }
echo "$(date -Is) governor start HOT=$HOT COOL=$COOL unit=$UNIT" >> $LOG
while true; do
  m=$(maxtemp)
  if [ $state = running ] && [ $m -ge $HOT ]; then systemctl --user kill -s SIGSTOP $UNIT && state=frozen && echo "$(date -Is) FREEZE at ${m}C" >> $LOG
  elif [ $state = frozen ] && [ $m -le $COOL ]; then systemctl --user kill -s SIGCONT $UNIT && state=running && echo "$(date -Is) RESUME at ${m}C" >> $LOG; fi
  sleep 5
done
