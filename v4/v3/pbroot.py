"""pbroot.py (v3.3): the one root setting. ROOT = this code tree (or $PB_ROOT); HOST = host-only files (or $PB_HOST).
Read-only v3.2 inputs (crops, text, natives, Source Data and figure files) are symlinked into HOST; outputs are written under HOST."""
import os
ROOT = os.environ.get('PB_ROOT', os.path.dirname(os.path.abspath(__file__)))
HOST = os.environ.get('PB_HOST', '/home/aid1/Documents/harbor/v4_host/v3')
