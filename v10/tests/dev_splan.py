"""run P/splan10.py against a dev server10 (tokens minted by tests/dev_register.py with the dev worlds and test κ).
  MCENV_STATE=DIR V10_WORLDS=DEVDIR V10_KAPPA=0.2 ~/v5env/bin/python tests/dev_splan.py VARIANT FAMILY URL WORLD K BATCH"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'P'))
import splan10 as SP10
AD = SP10.AD


def new_token(self, world, arm, k):
    items = json.dumps([dict(world=world, arm=arm, k=k, model=self.model, batch=self.batch)])
    tok = subprocess.run([sys.executable, os.path.join(HERE, 'dev_register.py')], input=items, capture_output=True, text=True).stdout.split()[-1]
    self.tokens.append(dict(token=tok, world=world, arm=arm, k=k)); return tok


AD.Env.new_token = new_token
v, fam, url, w, k, b = sys.argv[1:7]
sys.argv = ['splan10.py', v, fam, url, 'local', '.', os.environ['MCENV_STATE'], w, k, b]
SP10.main()
