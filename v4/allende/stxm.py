#!/usr/bin/env python3
"""stxm.py (v4 Track B, skill M2 raw data): STXM-XAS stacks of the Allende grain (ALS COSMIC, aXis2000 .hdr + .xim).
  load(edge_dir)   energies (eV) from the header StackAxis, pixel axes (um) from PAxis/QAxis, transmission images I(E) from the .xim files in
                   index order (a000, a001, ...).
  align(stack)     drift correction: every image registered to the image nearest the stack's median energy by phase cross-correlation
                   (upsample 10) on gradient-magnitude images (contrast inverts across an edge); integer-free subpixel shifts applied by
                   Fourier shift; shifts logged. Rule: shifts above 25 % of the field are rejected (image dropped, logged).
  od(stack)        optical density OD = -ln(I / I0); I0(E) = median of the pixels in the top 5 % of the energy-averaged transmission
                   (fully transmitting region, as in the paper's Methods); hot pixels (> 5 MAD above a 3 x 3 median) replaced by the median.
  edge_jump(od,E)  mean OD over the post-edge window minus mean OD over the pre-edge window (windows per edge below).
Validated on a synthetic drifted stack (validate_stxm.py) before real use."""
import glob, os, re
import numpy as np
from scipy import ndimage as ndi
from skimage.registration import phase_cross_correlation
WINDOWS_ABS_UNUSED = {'Fe': ((693.0, 704.0), (706.0, 712.0)), 'Ni': ((840.0, 849.0), (852.0, 856.0)), 'Mg': ((1293.0, 1301.0), (1303.0, 1310.2)), 'Al': ((1540.0, 1560.0), (1565.0, 1580.25))}

def load(edge_dir):
    hdr = glob.glob(f'{edge_dir}/*.hdr')[0]; t = open(hdr).read()
    m = re.search(r'StackAxis = \{ Name = "Energy".*?Points = \((\d+), ([^)]*)\)', t, re.S); E = np.array([float(x) for x in m.group(2).split(',')])
    ax = {}
    for nm in ('PAxis', 'QAxis'):
        mm = re.search(nm + r' = \{ Name = "[^"]*"; Unit = "um"; Min = ([-\d.e+]+); Max = ([-\d.e+]+);.*?Points = \((\d+),', t, re.S)
        ax[nm] = (float(mm.group(1)), float(mm.group(2)), int(mm.group(3)))
    xims = sorted(glob.glob(f'{edge_dir}/*.xim'), key=lambda f: int(re.search(r'_a(\d+)\.xim$', f).group(1)))
    st = np.stack([np.loadtxt(f) for f in xims]).astype(float)
    n = min(len(E), len(st)); px = (ax['PAxis'][1] - ax['PAxis'][0]) / (ax['PAxis'][2] - 1)
    return E[:n], st[:n], {'um_per_px': px, 'axes': ax, 'n_energies_header': len(E), 'n_images': len(st)}

def clean(a):
    med = ndi.median_filter(a, 3); mad = np.median(np.abs(a - med)) + 1e-9; hot = np.abs(a - med) > 5 * 1.4826 * mad; a = a.copy(); a[hot] = med[hot]; return a

def align(st, E):
    st = np.stack([clean(a) for a in st])   # hot pixels removed before registration (synthetic iteration 2: hot pixels captured the correlation)
    ref_i = int(np.argmin(np.abs(E - np.median(E)))); g = lambda a: ndi.gaussian_gradient_magnitude(np.log(np.clip(a, 1, None)), 1.0)
    win = np.outer(np.hanning(st.shape[1]), np.hanning(st.shape[2]))   # apodization against wrap-around (synthetic iteration 3)
    ref = g(st[ref_i]) * win; out = []; shifts = []
    for k, a in enumerate(st):
        sh, err, _ = phase_cross_correlation(ref, g(a) * win, upsample_factor=10)
        if np.abs(sh).max() > 0.25 * min(a.shape): out.append(None); shifts.append((float('nan'),) * 2); continue
        out.append(np.real(np.fft.ifftn(ndi.fourier_shift(np.fft.fftn(a), sh)))); shifts.append(tuple(float(x) for x in sh))
    keep = [i for i, a in enumerate(out) if a is not None]
    return np.stack([out[i] for i in keep]), E[keep], shifts

def od(st):
    st = st.copy()
    for k in range(len(st)):
        med = ndi.median_filter(st[k], 3); mad = np.median(np.abs(st[k] - med)) + 1e-9; hot = np.abs(st[k] - med) > 5 * 1.4826 * mad; st[k][hot] = med[hot]
    mean_t = st.mean(0); mask = mean_t >= np.percentile(mean_t, 95)
    I0 = np.array([np.median(a[mask]) for a in st]); return -np.log(np.clip(st / I0[:, None, None], 1e-6, None)), mask

def onset(o, E):
    """edge onset = energy of the steepest rise of the grain-mean OD spectrum (grain = pixels above the 60th percentile of mean OD),
    smoothed by a 3-point running mean. The deposit's energy axes carry unknown monochromator offsets (D gap, logged): windows are set
    relative to this onset (B3; real Fe L3 at 705.0 eV against ~708.5 eV tabulated)."""
    g = o.mean(0) > np.percentile(o.mean(0), 60); sp = np.convolve(o[:, g].mean(1), np.ones(3) / 3, 'same'); d = np.gradient(sp, E)
    d[:2] = d[-2:] = -np.inf; return float(E[int(np.argmax(d))])

REL = {'Fe': ((-11.0, -3.0), (0.5, 4.0)), 'Ni': ((-9.0, -2.0), (0.0, 3.0)), 'Mg': ((-7.0, -2.0), (0.0, 4.0)), 'Al': ((-12.0, -3.0), (0.0, 6.0))}
def edge_jump(o, E, el, e0=None):
    e0 = onset(o, E) if e0 is None else e0; (a, b), (c, d) = REL[el]
    pre = (E >= e0 + a) & (E <= e0 + b); post = (E >= e0 + c) & (E <= e0 + d)
    return o[post].mean(0) - o[pre].mean(0)
