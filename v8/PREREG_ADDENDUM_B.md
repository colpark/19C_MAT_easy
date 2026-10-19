# v8 pre-registration addendum B (V8-X3)

Pushed before any truth run. Verbatim from David's note below.

---

# PROMPT CHANGE: v8 amendment B (David, 2026-10-19), scope after fluorophlogopite

Log as V8-X3. Push v8/PREREG_ADDENDUM_B.md with this note verbatim before
any truth run.

1. Gate F1 on fluorophlogopite is reported as failed (no IFF parameters),
   never patched.
2. Replace fluorophlogopite with Na+ muscovite: muscovite (001) with the
   surface K+ layer exchanged for Na+, in 100 mM NaCl. Systems become
   6 test designs × 2 surface cations (K+, Na+) = 12 systems, 24 worlds.
   Gate F1 now covers both pilot fragments on K+ and Na+ muscovite.
3. Fallback, if Na+ assembly fails within the existing one-day timebox:
   12 test designs on K+ muscovite only, 24 worlds. Log which path ran.
4. Charges. Build the muscovite surface model from the IFF v1.5 repository
   with full charges. Never use the uncharged OpenKIM archive for truth.
5. CIF. Pick one muscovite CIF, check its cell and composition against the
   literature, and record the COD id, hash and reason in SUPPLY.md.
6. Update STATUS.md at every push. All other gates and expectations stay
   unchanged.
