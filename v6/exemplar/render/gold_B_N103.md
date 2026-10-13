**Claim.** The crystalline phase in this sample is the lowest-energy polymorph of ScPPd2.

**Plan (S0).** The claim needs two answers: which polymorph this sample holds, and which polymorph of ScPPd2 lies lowest. Measurement answers the first. The FM answers the second. S3 joins them.

**S1a predict window (simulator).**
Thought: The free scan m0 cannot separate the polymorphs (the predicted D on m0 is 1.575 for ScPPd2 (Fm-3m) and 0.669 for ScPPd2 (Immm)), so I need the window where their patterns differ. S1a uses the library, m0 and the budget of 180 min.
Action: The simulator simulates each library polymorph and searches 840 candidate plans with the local forward model.
Observation: Window 38.59 to 40.59 degrees. The plan holds one X-ray scan from 38.59 to 40.59 with step 0.01 and 20.0 s per step. Predicted D is 75.118 at 72.0 min.
Check: predicted D 75.118 ≥ 25, accepted.

**S1b measure (instrument).**
Thought: S1b buys the scan that S1a planned, because the free scan alone leaves the polymorphs unseparated.
Action: The instrument module calls measure once with the S1a plan.
Observation: One measurement, m1, at 72.0 min.
Check: S1b always accepts, accepted.

**S1c identify (fit).**
Thought: S1c fits the polymorphs to m0 and m1 together and names the favoured polymorph with its separation D. It uses the measurement from S1b.
Action: The fit module fits ScPPd2 (Fm-3m) and ScPPd2 (Immm) to both measurements, 1702 points each, with size_nm 100.
Observation: Chi2 is 1544.361 for ScPPd2 (Fm-3m) and 2460.696 for ScPPd2 (Immm). The favoured phase is ScPPd2 (Fm-3m), the runner-up is ScPPd2 (Immm), and D is 916.335.
Check: D 916.335 ≥ 25, accepted.

**S2 infer energy (FM).**
Thought: S2 answers the second subgoal and shares no edge with S1c, so it needs only the library.
Action: The fm module calls energy for ScPPd2 (Fm-3m) and ScPPd2 (Immm).
Observation: The formation energy per atom is -0.62586 eV/atom for ScPPd2 (Fm-3m) and -0.84406 eV/atom for ScPPd2 (Immm). The stated error is 0.045. The lowest polymorph is ScPPd2 (Immm), with margin 0.2182 eV/atom.
Check: margin 0.2182 ≥ 0.045, accepted.

**S2x escalate to DFT.** skipped: the FM margin 0.2182 eV/atom cleared the band 0.045.

**S3 decide (rule).**
Thought: S3 joins S1c (the sample holds ScPPd2 (Fm-3m)) and S2 (ScPPd2 (Immm) lies lowest).
Action: The rule module applies R_lowest_match to phase, lowest and lowest_dft, which is null.
Observation: The verdict is REFUTED because the sample holds ScPPd2 (Fm-3m) and FM puts ScPPd2 (Immm) lowest.
Check: S3 always accepts, accepted.

**Verdict.** REFUTED (key REFUTED).

**Why each step matters.** The validation suite has not run yet. The ablation test will blank S1a, S1b, S1c and S2 in turn and check that each blank leaves CANNOT_TELL. The measurement twin test will feed the other twin's data to S1c and check that the identified polymorph and the verdict flip. The prior twin test will flip the FM ranking with the data fixed and check that the verdict flips. The hold test will change displacement, zero offset and crystallite size and check that nothing changes.
