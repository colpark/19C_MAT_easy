"""run_python sandbox (V5_SPEC 1.4, X9, V5-E3): a fresh `python -I` per call that, before running agent code,
(1) sets rlimits (CPU 30 s, address space 2 GB, file size 16 MB, no core), (2) restricts itself with Landlock (read-only: the Python
runtime and system libraries; read-write: a fresh copy of the episode's data directory; every other path and all TCP bind/connect
denied), (3) installs an audit hook that blocks sockets, subprocesses, exec, fork and ctypes. The environment is cleared.
Measurements are preloaded as `meas[id] = {'two_theta': array, 'counts': array, ...}` with numpy as np and scipy available."""
import json, os, shutil, subprocess, sys, tempfile

PY = sys.executable
RO_PATHS = sorted({os.path.realpath(p) for p in (sys.prefix, sys.base_prefix, '/usr', '/lib', '/lib64', '/etc/ld.so.cache',
                                                 '/etc/localtime', '/dev/null', '/dev/urandom', '/sys/devices/system/cpu')
                   if os.path.exists(p)})

BOOT = r'''
import ctypes, json, os, resource, sys
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
resource.setrlimit(resource.RLIMIT_AS, (2 << 30, 2 << 30))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 << 20, 16 << 20))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
import numpy as np, scipy, scipy.optimize, scipy.signal, scipy.interpolate, scipy.ndimage, scipy.stats, scipy.special, scipy.linalg
libc = ctypes.CDLL(None, use_errno=True)
SYS_create, SYS_add, SYS_restrict, PR_SET_NO_NEW_PRIVS = 444, 445, 446, 38
abi = libc.syscall(SYS_create, None, 0, 1)
assert abi >= 4, 'landlock ABI >= 4 required'
FS_ALL = (1 << 16) - 1 if abi >= 5 else (1 << 15) - 1          # every fs access right of this ABI
FS_READ = 1 | 4 | 8                                              # EXECUTE | READ_FILE | READ_DIR
NET = 1 | 2                                                      # BIND_TCP | CONNECT_TCP
class RA(ctypes.Structure): _fields_ = [('fs', ctypes.c_uint64), ('net', ctypes.c_uint64), ('scoped', ctypes.c_uint64)]
class PB(ctypes.Structure): _pack_ = 1; _fields_ = [('allowed', ctypes.c_uint64), ('fd', ctypes.c_int32)]
ra = RA(FS_ALL, NET, 0)
rs = libc.syscall(SYS_create, ctypes.byref(ra), ctypes.c_size_t(16), 0)
assert rs >= 0, 'landlock_create_ruleset failed %d' % ctypes.get_errno()
def allow(path, rights):
    fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
    is_dir = os.path.isdir(path)
    r = rights if is_dir else rights & (1 | 2 | 4 | (1 << 14) | (1 << 15))   # file-applicable rights only
    pb = PB(r, fd)
    assert libc.syscall(SYS_add, rs, 1, ctypes.byref(pb), 0) == 0, 'add_rule %s %d' % (path, ctypes.get_errno())
    os.close(fd)
for p in RO: allow(p, FS_READ)
allow(WORK, FS_ALL)
assert libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) == 0
assert libc.syscall(SYS_restrict, rs, 0) == 0, 'restrict_self %d' % ctypes.get_errno()
os.close(rs)
meas = {}
for f in sorted(os.listdir(WORK)):
    if f.endswith('.json'):
        d = json.load(open(os.path.join(WORK, f)))
        d['two_theta'] = d['start'] + d['step'] * np.arange(d['n']); d['counts'] = np.asarray(d['counts'], float); meas[d['id']] = d
BLOCK = ('socket', 'subprocess', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork', 'os.forkpty', 'ctypes', 'os.kill', 'pty')
def hook(ev, args):
    if ev.startswith(BLOCK): raise PermissionError('blocked in sandbox: ' + ev)
sys.addaudithook(hook)
del ctypes, libc, hook
os.chdir(WORK)
g = {'np': np, 'scipy': scipy, 'meas': meas, '__name__': '__main__'}
code = open(os.path.join(WORK, '.code.py')).read()
os.unlink(os.path.join(WORK, '.code.py'))
exec(compile(code, '<agent>', 'exec'), g)
'''


def run(data_dir, code, timeout=30, max_out=20000):
    work = tempfile.mkdtemp(prefix='v5sbx_', dir=os.environ.get('MCENV_SBX_TMP', None))
    try:
        for f in os.listdir(data_dir):
            if f.endswith('.json'): shutil.copy(os.path.join(data_dir, f), work)
        open(os.path.join(work, '.code.py'), 'w').write(code)
        boot = f'RO = {RO_PATHS!r}\nWORK = {work!r}\n' + BOOT
        env = {'PATH': '/usr/bin:/bin', 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1', 'HOME': work,
               'PYTHONDONTWRITEBYTECODE': '1', 'LANG': 'C.UTF-8'}
        try:
            p = subprocess.run([PY, '-I', '-c', boot], cwd=work, env=env, capture_output=True, text=True, timeout=timeout)
            out, err, rc = p.stdout, p.stderr, p.returncode
        except subprocess.TimeoutExpired as e:
            out, err, rc = (e.stdout or b'').decode(errors='replace') if isinstance(e.stdout, bytes) else (e.stdout or ''), 'timeout after %d s' % timeout, -9
        err = _scrub(err, work)
        return dict(returncode=rc, stdout=out[:max_out], stderr=err[-4000:], truncated=len(out) > max_out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _scrub(err, work):
    """hide the boot code from tracebacks (line numbers of the wrapper are irrelevant to the agent)."""
    lines = [l for l in err.splitlines() if 'File "<string>"' not in l]
    return '\n'.join(lines).replace(work, '<work>')
