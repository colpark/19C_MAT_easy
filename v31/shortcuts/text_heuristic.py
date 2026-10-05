#!/usr/bin/env python3
"""text_heuristic.py: entry point named in the v3.1 plan; the scoring lives in shortcuts.py (one pass scores all three shortcuts and writes
shortcuts/scores.json). usage: text_heuristic.py [items.jsonl] [tasks dir]"""
import os, runpy, sys
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shortcuts.py'), run_name='__main__')
