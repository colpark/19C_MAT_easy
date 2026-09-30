#!/usr/bin/env python3
"""node_monitor.py: lightweight health monitor for the GB10 (DGX Spark) nodes. Read-only; needs no root.

Every INTERVAL seconds it appends one CSV row and fsyncs it, so the last readings survive a hard freeze:
  time, cpu_busy_%, load1, mem_avail_GB, page_cache_GB, swap_used_GB, gpu_temp_C, gpu_power_W, gpu_util_%,
  gpu_sm_MHz, gpu_throttle, acpi_max_C, nvme_C, nic_max_C, containers, procs
It also follows the kernel log and records events that preceded the Sep 27 and Sep 30 freezes
(NVRM NV_ERR_NO_MEMORY, fill_page_cache_func stalls) plus thermal, OOM, lockup and Xid messages.

Alerts go to alerts.log. While any alert condition holds, the file PAUSE exists; run scripts can check it
before starting a stage. Thresholds: mem_avail < 16 GB, any temperature >= 85 C, GPU hardware or thermal
slowdown flags (0xE8), or a crash-signature kernel line in the last 10 minutes.
"""
import csv, os, re, subprocess, sys, time, datetime, glob, threading, collections

OUT = os.path.dirname(os.path.abspath(__file__))
INTERVAL = int(os.environ.get('INTERVAL', 10))
MEM_MIN_GB, TEMP_MAX_C, SIG_WINDOW = 16, 85, 600
SIG = re.compile(r'NV_ERR_NO_MEMORY|fill_page_cache_func|NVRM: Xid|thermal|throttl|critical temperature|'
                 r'Out of memory|oom-kill|soft lockup|hard LOCKUP|blocked for more than|hung_task', re.I)
CRASH_SIG = re.compile(r'NV_ERR_NO_MEMORY|fill_page_cache_func|NVRM: Xid|critical temperature|soft lockup|hard LOCKUP', re.I)
recent = collections.deque()  # timestamps of crash-signature kernel lines
lock = threading.Lock()

def append(path, line):
    with open(path, 'a') as f:
        f.write(line); f.flush(); os.fsync(f.fileno())

def follow_kernel():
    p = subprocess.Popen(['journalctl', '-k', '-f', '-n', '0', '-o', 'short-iso', '--no-pager'],
                         stdout=subprocess.PIPE, text=True)
    for line in p.stdout:
        if SIG.search(line):
            append(f'{OUT}/kernel_events.log', line)
            if CRASH_SIG.search(line):
                with lock: recent.append(time.time())

def cpu_times():
    v = list(map(int, open('/proc/stat').readline().split()[1:]))
    return sum(v), v[3] + v[4]

def meminfo():
    m = {}
    for l in open('/proc/meminfo'):
        k, v = l.split(':'); m[k] = int(v.split()[0]) / 1048576
    return m

def read_temp(path):
    try: return int(open(path).read()) / 1000
    except Exception: return None

def hw_temps():
    acpi = [read_temp(f'{z}/temp') for z in glob.glob('/sys/class/thermal/thermal_zone*')]
    nvme, nic = [], []
    for h in glob.glob('/sys/class/hwmon/hwmon*'):
        name = open(f'{h}/name').read().strip()
        vals = [read_temp(t) for t in glob.glob(f'{h}/temp*_input')]
        (nvme if name == 'nvme' else nic if name == 'mlx5' else []).extend(v for v in vals if v is not None)
    mx = lambda xs: max([x for x in xs if x is not None], default=None)
    return mx(acpi), mx(nvme), mx(nic)

def gpu():
    try:
        r = subprocess.run(['nvidia-smi', '--query-gpu=temperature.gpu,power.draw,utilization.gpu,clocks.sm,'
                            'clocks_event_reasons.active', '--format=csv,noheader,nounits'],
                           capture_output=True, text=True, timeout=10).stdout.strip().split(', ')
        return [float(r[0]), float(r[1]), float(r[2]), float(r[3]), r[4]]
    except Exception:
        return [None, None, None, None, 'nvidia-smi-failed']

def containers():
    try:
        return len(subprocess.run(['sg', 'docker', '-c', 'docker ps -q'], capture_output=True, text=True,
                                  timeout=10).stdout.split())
    except Exception:
        return None

def main():
    threading.Thread(target=follow_kernel, daemon=True).start()
    day = datetime.date.today().isoformat()
    path = f'{OUT}/metrics_{day}.csv'
    if not os.path.exists(path):
        append(path, 'time,cpu_busy_pct,load1,mem_avail_GB,page_cache_GB,swap_used_GB,gpu_temp_C,gpu_power_W,'
                     'gpu_util_pct,gpu_sm_MHz,gpu_throttle,acpi_max_C,nvme_C,nic_max_C,containers,procs\n')
    t0, i0 = cpu_times(); n = 0
    while True:
        time.sleep(INTERVAL)
        t1, i1 = cpu_times(); busy = 100 * (1 - (i1 - i0) / max(t1 - t0, 1)); t0, i0 = t1, i1
        m = meminfo(); acpi, nvme, nic = hw_temps(); g = gpu()
        ctr = containers() if n % 3 == 0 else ''
        procs = len([d for d in os.listdir('/proc') if d.isdigit()])
        now = datetime.datetime.now().isoformat(timespec='seconds')
        row = [now, f'{busy:.1f}', os.getloadavg()[0], f"{m['MemAvailable']:.1f}", f"{m['Cached']:.1f}",
               f"{m['SwapTotal'] - m['SwapFree']:.1f}", *g, acpi, nvme, nic, ctr, procs]
        append(path, ','.join('' if v is None else str(v) for v in row) + '\n')
        with lock:
            while recent and recent[0] < time.time() - SIG_WINDOW: recent.popleft()
            sig = len(recent)
        temps = [v for v in (g[0], acpi, nvme, nic) if v is not None]
        reasons = []
        if m['MemAvailable'] < MEM_MIN_GB: reasons.append(f"mem_avail {m['MemAvailable']:.1f} GB < {MEM_MIN_GB}")
        if temps and max(temps) >= TEMP_MAX_C: reasons.append(f'temperature {max(temps):.0f} C >= {TEMP_MAX_C}')
        try: bad = int(g[4], 16) & 0xE8   # HwSlowdown 0x8, SwThermal 0x20, HwThermal 0x40, HwPowerBrake 0x80
        except ValueError: bad = 0
        if bad: reasons.append(f'gpu thermal/hardware slowdown {g[4]}')
        if sig: reasons.append(f'{sig} crash-signature kernel lines in last {SIG_WINDOW // 60} min')
        flag = f'{OUT}/PAUSE'
        if reasons:
            if not os.path.exists(flag): append(f'{OUT}/alerts.log', f'{now} ALERT ' + '; '.join(reasons) + '\n')
            open(flag, 'w').write(now + ' ' + '; '.join(reasons) + '\n')
        elif os.path.exists(flag):
            os.remove(flag); append(f'{OUT}/alerts.log', f'{now} CLEAR\n')
        n += 1
        if datetime.date.today().isoformat() != day:
            day = datetime.date.today().isoformat(); path = f'{OUT}/metrics_{day}.csv'
            append(path, 'time,cpu_busy_pct,load1,mem_avail_GB,page_cache_GB,swap_used_GB,gpu_temp_C,gpu_power_W,'
                         'gpu_util_pct,gpu_sm_MHz,gpu_throttle,acpi_max_C,nvme_C,nic_max_C,containers,procs\n')

if __name__ == '__main__':
    main()
