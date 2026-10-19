# v8 status (updated at every push)

**Stopped for David.** Gate S passed; **Gate F1 FAILED** (0 of 4 dev systems above 0.61 sigma; the registry margin's sign is not stable across in-plane placements, risk R2), so Track 1 stopped as pre-registered. Nothing relaxed.

- V8-0 complete; UMA verified on hosts A1 and B1.
- Addenda A (V8-X2), B (V8-X3), C (V8-X5), D (V8-X6) pre-registered; rules in force in PREREG_EFFECTIVE.md.
- Gate S PASSED (truth/SUPPLY.md). Muscovite from the IFF v1.5 distribution model, cell within 0.3 % of literature.
- V8-2 instrument done (ALL WORLD TESTS PASSED; partly calibrated, V8-X9). V8-3 graph I, server, manual done; all suites pass, kits byte-identical.
- Adapters done; gold correct on both demo twins; validate_d fails the hold row only (Q7, blocks V8-4).
- Gate F1 FAILED: truth/F_REPORT.md, truth/TRUTH_TABLE.json. Gate F2, V8-4 to V8-7 not reached.
- FM blindness intact: no FM call has touched any dev or test system.

Read `v8/MORNING.md` first. Two decisions are waiting: Q7 (phase semantics for the hold row) and the scope after Gate F1 (recommendation: define truth on 14- or 18-repeat rods instead of single repeats).
