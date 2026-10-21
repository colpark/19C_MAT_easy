"""a development server10 on tuning-split dev worlds at a test κ (V10_KAPPA), before v10/KAPPA.json exists or apart from it.
  MCENV_STATE=DIR MCENV_PORT=8809 V10_WORLDS=DEVDIR V10_KAPPA=0.2 ~/v5env/bin/python tests/dev_server10.py   (writes DIR/server.pid)"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from mcenv import scenarios as SC
kf = os.path.join(tempfile.mkdtemp(), 'KAPPA.json'); json.dump(dict(kappa=float(os.environ['V10_KAPPA'])), open(kf, 'w')); SC.KAPPA_FILE = kf
from mcenv import server10 as S10
from mcenv import server6 as S6
if os.environ.get('V10_DEV_FM_FROM_DFT'):                            # dev only: no FM table exists before the world freeze
    for s in list(S6._tb.get('dft', {})): S6._tb.setdefault('fm', {})[s] = S6._tb['dft'][s]
os.makedirs(os.environ['MCENV_STATE'], exist_ok=True)
open(os.path.join(os.environ['MCENV_STATE'], 'server.pid'), 'w').write(str(os.getpid()))
S10.S.main()
