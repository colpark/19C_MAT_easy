"""vP.1 admin CLI: v7's mcenv.admin with the vP.1 server loaded (its arms registered), run on the server host only. Refuses a vP.1 arm
on a T world and fm-flip on a compound that is not FM-right (b1/ROWS_NODFT.md, H/FM_CHECK.md). Commands as mcenv.admin.
  MCENV_STATE=... python -m mcenv.admin_vp1 newplan --arms fit-once --model sonnet --ks 1 --batch vp1-... --worlds ..."""
from . import server_vp1 as SV
from . import scenarios as SC
from . import admin as A

_reg = A._register


def _register(items):
    for it in items:
        arm, w = it['arm'], int(it['world'])
        if arm in SV.VP1_ARMS:
            s = SC.WORLD_SCEN[w]
            if SV.family(s) not in ('B1', 'H'): raise SystemExit(f'{arm} runs on B1 and H only (world {w})')
            if arm == 'fm-flip' and s not in SV.FM_RIGHT: raise SystemExit(f'fm-flip runs on FM-right compounds only (world {w}, scenario {s})')
    return _reg(items)


A._register = _register

if __name__ == '__main__':
    A.main()
