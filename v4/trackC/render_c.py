#!/usr/bin/env python3
"""C5 panel and structure rendering (matplotlib from deposited arrays; neutral names; no EXIF/text metadata).

  msd_panel(traj_uuid, out_png)      Li MSD(t) of a deposited FPMD trajectory (msd.msd_for_panel, frozen C2proc)
  a2f_panel(x_meV, y, out_png)       Eliashberg function alpha2F(omega) from the deposited arrays
  neutral_cif(structure, out_cif)    CIF with a neutral data block, no names, no comments
Panels carry axis labels and units only: no title, legend, formula, temperature or value annotation.
"""
import io, os, re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

META = {'Software': None, 'Title': None, 'Author': None, 'Description': None, 'Comment': None}


def _save(fig, out):
    fig.savefig(out, dpi=110, metadata=META)
    plt.close(fig)


def msd_curve_from_traj(traj_uuid):
    from aiida import orm
    import msd, reconstruct as R
    n = orm.load_node(traj_uuid)
    sym = R._symbols(n)
    pos, vel = n.get_array('positions'), n.get_array('velocities')
    cell = n.get_array('cells')[0]
    if 'times' in n.get_arraynames():
        dt = float(n.base.attributes.get('timestep_in_fs'))
    else:
        dt = float(R.dt_estimate_fs(pos, vel, cell))
    mask = np.array([s == 'Li' for s in sym])
    t, m = msd.msd_for_panel(pos, cell, dt / 1000.0, mask)
    return t, m


def msd_panel(t_ps, msd_A2, out):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(t_ps, msd_A2, color='0.15', lw=1.4)
    ax.set_xlabel('Time lag t (ps)')
    ax.set_ylabel('Li MSD(t) (Å$^2$)')
    ax.set_xlim(0, float(t_ps[-1]))
    ax.set_ylim(bottom=0)
    ax.grid(True, color='0.85', lw=0.6)
    fig.tight_layout()
    _save(fig, out)


def a2f_panel(x_meV, y, out):
    fig, ax = plt.subplots(figsize=(5.2, 3.6))
    ax.plot(x_meV, y, color='0.15', lw=1.4)
    ax.set_xlabel('Phonon energy ω (meV)')
    ax.set_ylabel('α$^2$F(ω)')
    ax.set_xlim(0, float(np.max(x_meV)))
    ax.set_ylim(bottom=0)
    ax.grid(True, color='0.85', lw=0.6)
    fig.tight_layout()
    _save(fig, out)


def neutral_cif(structure, out):
    from pymatgen.io.cif import CifWriter
    s = str(CifWriter(structure))
    s = re.sub(r'^data_.*$', 'data_material', s, count=1, flags=re.M)
    s = '\n'.join(l for l in s.splitlines() if not l.lstrip().startswith('#') and '_chemical_name' not in l)
    open(out, 'w').write(s + '\n')
