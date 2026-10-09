# HTEM_MC2_RULES_v22 addendum D1: unexplained XRD peaks matching excluded elemental phases (diagnostic only)

David, 2026-10-08. Frozen before it is run. It changes no key, item, gate or census decision, and its output never enters an item, trace or manifest.

**Budget note:** CO2 has its own budget of at most 1,000 COD requests, separate from the 891 that CO1 used.

**Scope.** Every non-dev, fully cached library in an anion system (at least one of O, N, S, Se or Te) with XRD patterns. Positions in the census scope (e).

**Per position:**
1. **S4hx peaks:** the frozen `readers.xrd.read`.
2. **Strong peak:** SNR ≥ 10, and height ≥ 10 % of the position's strongest peak.
3. **Unexplained peak:** no stick of any CO2-admissible phase for the library lies within 0.3° of its centre. This counts every stick in 19-52°, not only the strongest five.
4. **Elemental match:** an unexplained strong peak lies within 0.3° of one of the 5 strongest sticks of an **elemental** phase whose element is in the system. CO2 excludes these phases in anion libraries; they come from the CO1 and CO2 sticks.

**Output:** `MC22_DIAG_ELEMENTAL.md` and `.json`.
- **Per library:** positions with an elemental match, the peak (2θ, height fraction, SNR), the elemental phase (COD id, hkl), and the share of the library's positions affected.
- **Per system and element:** library counts.
- **Totals:** strong peaks, unexplained strong peaks, and elemental matches. Several elemental phases can match one peak; all are listed.

**Reading the output.** A match is a hypothesis, not an identification: segregated metal or chalcogen, or a coincidence. Nothing in the output is keyed.
