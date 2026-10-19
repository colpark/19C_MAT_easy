# v8 status (updated at every push)

**Amendment E iteration under way.** Gate S passed; the first Gate F1 (solvated, paired estimator) FAILED and is kept as recorded; E changes the estimator and the reference protocol and gives v8 one further iteration.

- Addenda A, B, C, D, E pre-registered (V8-X2, X3, X5, X6, X12); rules in force in PREREG_EFFECTIVE.md.
- Q7 done (E item 1): `phase` is now the identified candidate registry; **validate_d with all rows PASSES on the demo worlds, hold row included** (V8-E15).
- Host B1's GPU still held by a 7-day vLLM process (68 GB, 96 %); never signalled. Usable GPUs: A1, A2.
- Leftover demo and adapter state deleted; server kept on 8881.
- V8-2 instrument and V8-3 graph/server/manual stand. Adapters stand.

Step 1 and step 2 done: Gate F1 FAILED at fragment scale under both estimators and both protocols. **Step 3 done: rod scoping shows about 1 GPU hour for a full set (far below 48), so no NEGATIVE_RESULT; but only U0 has a usable 18-repeat rod, since the tiled control rods clash (V8-E14).** Stopped for David per E item 5.
