#!/usr/bin/env python3
"""measure_amb2.py (S4a-2): depth of one track from its top field and, when present, its bottom field (stitched with
amb2_reader.stitch on the Euler-1 maps). Returns the reader output with 'censored', 'stitched' and 'stitch' (offset, shift, corr)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import amb2_reader as R
def measure_track(top, bottom, step):
    ph, eul = top; stitched = None
    if bottom is not None:
        st = R.stitch(eul, ph, bottom[1], bottom[0])
        if st is not None:
            row, dx, cr = st; Hb = bottom[0].shape[0]; H = row + Hb; W = ph.shape[1]
            P = np.zeros((H, W)); E = np.zeros((H, W, 3)); P[:ph.shape[0]] = ph; E[:ph.shape[0]] = eul
            pb = np.roll(bottom[0], -dx, axis=1); eb = np.roll(bottom[1], -dx, axis=1); keep = ph.shape[0] - row   # rows of the bottom already covered by the top
            P[ph.shape[0]:] = pb[keep:]; E[ph.shape[0]:] = eb[keep:]; ph, eul, stitched = P, E, st
    lab, F = R.features(ph, eul, step); pool = R.classify(F); r = R.depth(ph, lab, pool, step)
    r['stitched'] = stitched is not None; r['stitch'] = list(stitched) if stitched else None
    if bottom is not None and stitched is None: r['censored'] = r['censored'] or True   # a failed stitch cannot cover the pool bottom
    return r
