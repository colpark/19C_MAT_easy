#!/usr/bin/env python3
"""validate_stxm.py (v4 Track B, rule I7): synthetic STXM stack (64 x 64, 80 energies across an absorption edge) with two phases (one with
the element, one without), a fully transmitting corner region, a random-walk drift up to 6 px, Poisson noise at 2000 counts I0, and 3 hot
pixels per image. Gates (frozen with stxm.py): residual drift after align <= 0.5 px rms; edge-jump map separates the phases (phase-mean
contrast >= 5 x the in-phase standard deviation); recovered edge-jump (window-mean difference, as defined) of the element phase within 15 % of truth. Output validate_stxm.json."""
import json, os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import stxm as S
rng = np.random.default_rng(11); H = W = 64; E = np.linspace(693, 733, 80); OFFSETS = [-4.0, -2.5, 0.0, 1.5, -3.5]   # unknown monochromator offsets (B3)
yy, xx = np.mgrid[0:H, 0:W]; grain = ((yy - 34) ** 2 + (xx - 30) ** 2) < 22 ** 2; phaseA = grain & (xx > 30)
mu_pre = 0.3; step = 0.6   # OD of the grain below / extra OD of phase A above the edge
res_rows = []
for trial in range(5):
    drift = np.cumsum(rng.normal(0, 0.8, (len(E), 2)), 0); drift -= drift[len(E) // 2]; drift = np.clip(drift, -6, 6)
    st = []
    for k, e in enumerate(E):
        odv = grain * mu_pre + phaseA * step * (1 / (1 + np.exp(-(e - (708 + OFFSETS[trial])) / 0.6)))
        I = 2000 * np.exp(-ndi.gaussian_filter(odv, 0.7)); I = ndi.shift(I, drift[k], order=1, mode='nearest'); I = rng.poisson(I).astype(float)
        hp = rng.integers(0, H, (3, 2)); I[hp[:, 0], hp[:, 1]] = 1e5; st.append(I)
    st = np.stack(st); al, E2, sh = S.align(st, E)
    ref_i = int(np.argmin(np.abs(E - np.median(E)))); resid = np.array(sh) + (drift - drift[ref_i]); rms = float(np.sqrt(np.nanmean(resid ** 2)))   # relative to the reference image
    o, mask = S.od(al); j = S.edge_jump(o, E2, 'Fe')
    inner = ndi.binary_erosion(phaseA, iterations=7); other = ndi.binary_erosion(grain & ~phaseA, iterations=7)
    contrast = (j[inner].mean() - j[other].mean()) / max(j[inner].std(), j[other].std())
    e0 = S.onset(o, E2); sig = 1 / (1 + np.exp(-(E2 - (708 + OFFSETS[trial])) / 0.6)); (a_, b_), (c_, d_) = S.REL['Fe']
    truth = step * (sig[(E2 >= e0 + c_) & (E2 <= e0 + d_)].mean() - sig[(E2 >= e0 + a_) & (E2 <= e0 + b_)].mean())   # window-mean difference as defined
    res_rows_onset = abs(e0 - (708 + OFFSETS[trial]))
    res_rows.append({'drift_rms_residual_px': rms, 'contrast_sigma': float(contrast), 'jump_A': float(j[inner].mean()), 'truth_jump': float(truth), 'onset_error_eV': float(res_rows_onset)})
res = {'rows': res_rows, 'gates': {'drift': all(r['drift_rms_residual_px'] <= 0.5 for r in res_rows), 'contrast': all(r['contrast_sigma'] >= 5 for r in res_rows),
                                    'jump': all(abs(r['jump_A'] - r['truth_jump']) / r['truth_jump'] <= 0.15 for r in res_rows), 'onset': all(r['onset_error_eV'] <= 1.0 for r in res_rows)}}
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'validate_stxm.json'), 'w'), indent=1); print(res)
