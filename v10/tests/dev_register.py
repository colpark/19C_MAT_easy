"""register episodes on a dev server10's state (same worlds and test κ): stdin JSON list [{world, arm, k, model, batch}] -> tokens, one per line.
  MCENV_STATE=DIR V10_WORLDS=DEVDIR V10_KAPPA=0.2 ~/v5env/bin/python tests/dev_register.py < items.json"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..'))
from mcenv import scenarios as SC
kf = os.path.join(tempfile.mkdtemp(), 'KAPPA.json'); json.dump(dict(kappa=float(os.environ['V10_KAPPA'])), open(kf, 'w')); SC.KAPPA_FILE = kf
from mcenv import server10 as S10  # noqa: F401  (installs the worlds and arms)
from mcenv import admin as A
print('\n'.join(A._register(json.load(sys.stdin))))
