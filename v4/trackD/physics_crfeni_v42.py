# CrFeNi physics table, v4.2 additions (skill v1.4). Frozen R3b before any T7 key or gate is computed. The v4.0 table physics_crfeni.py
# (D6) is imported unchanged; nothing in it is redefined. This file only pre-registers how T7 items are built and gated under v1.4.
from physics_crfeni import *   # noqa: F401,F403  (D6, unchanged)
import physics_crfeni as _D6

# T7 one-step (Hall-Petch on the plotted means; v4.0 form). g4 band: 2 x SD of the held-out prediction under a 500-draw bootstrap (seed 7)
# over the fit cells' u (condition-mean SE of ys, method-I spacing u) and the held-out spacing u; no model error. The key tolerance is the band.
# g1: |pred - obs| <= sqrt(band^2 + (2 se_obs)^2) with method I AND method II spacings (method II prediction with its own band).
# g2: fit-set mean and the nearest condition in d^-1/2 outside the band; g3: every other condition outside the band.
# g4: band <= item tolerance (no padding), band < 3 x the T1 band of the target panel (2 % of its y span as drawn), |literature - pred| > band.
# Selection (pre-registered): held-out candidates outside the fit range in d^-1/2 first (extrapolation), then GRAIN_KEYABLE order; at most
# 2 items, all counted as one fact (one law on one sample set).
T7_ONE_STEP = {'law': 'hall_petch', 'boot_n': 500, 'seed': 7, 'max_items': 2, 'order': 'extrapolation first, then GRAIN_KEYABLE order'}

# T7 two-step candidate (one, pre-registered). Panels: the five 293 K compression curves of the fit samples (one specimen per sample: the
# specimen whose D1c yield is nearest the sample mean, as T2 draws them; same axes 0-0.3 crosshead strain, 0-800 MPa) plus one table panel of
# the five method-I mean boundary spacings (value +- u). The stem gives the held-out sample's spacing. The solver reads each 0.2 % offset
# yield on crosshead strain, fits Hall-Petch, and predicts the held-out sample's yield.
# Key: Hall-Petch fit on the D1c yields of the shown specimens (yieldproc D1c, unchanged) against the method-I spacings; prediction at the
# held-out spacing. Band: 2 x SD under a 500-draw bootstrap (seed 11) over the reading u of each yield (u = 1 % of the curve panel's stress
# span, the T1 rule: 8 MPa) and the spacing u; no model error. g1 against the held-out sample's mean D1c yield (sqrt(band^2 + (2 se)^2));
# g2, g3 as one-step (other conditions' means); g4 with the curve panels as target (T1 band 2 % of 800 MPa = 16 MPa).
# Held-out (pre-registered): the GRAIN_KEYABLE sample with the smallest method-I spacing (extrapolation). Build only if g1-g4 pass.
T7_TWO_STEP = {'law': 'hall_petch', 'held_out_rule': 'smallest method-I spacing among GRAIN_KEYABLE', 'curve_ylim': (0, 800), 'curve_xlim': (0, 0.3),
               'reading_u_frac': 0.01, 'boot_n': 500, 'seed': 11, 'specimen': 'D1c yield nearest the sample mean (T2 rule)'}
