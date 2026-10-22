# vP.1 pre-registration (paper 1, David 2026-10-22)

Committed verbatim as `vp1/PREREG.md` before any vP.1 run. Gates and expectations are reported as met or not met, never relaxed.

## Headline under test
Measurement models are necessary but not sufficient. The same model plans measurements better offline, as a program, than it acts in the loop, and model answers displace and mislead measurement.

## Base
- **Frozen v7 benchmark** (branch v7/2026-10-18 at 21fce6e55):
  - B1: 30 compounds, 60 worlds
  - H: 23 compounds, 46 worlds
  - T: 24 paired compounds, 96 worlds
- **Frozen parts:** worlds, manuals, task texts, keys (evidence key first, registered key beside it), graders, and the round-G programs and their inputs. vP.1 changes none of them.

## Confound stated in advance
v7's manuals credit CANNOT_TELL when D < 9 or when the FM sits inside its band (registered key), so early stopping was allowed by the stated rule. On H and T both keys gave equal scores. On B1 they diverge.
- **Primary families:** H and T.
- **B1:** reported beside them, with this note.

## VP1-1. Fair offline selection (CPU)
- **Runs.** The 15 round-G programs at seeds 2, 3 and 4 on their families (3,030 episodes). With v7's seed 1, every program then has seeds 1 to 4.
- **Folds.** Each family's compounds are ranked by sha256('vp1|' + formula). The first half (rounded up) is fold 0 and the rest fold 1 (`ref/folds.py`).
- **Cross-fitted choice** (`ref/crossfit.py`).
  - For fold f, choose the program with the highest mean unit resolution under the evidence key over the other fold, seeds 1 to 4.
  - Ties break on the registered key, then on lower mean cost, then on the program name.
  - Score the choice on fold f, then pool both folds.
- **Contrast.** The cross-fitted program against Sonnet fm, paired by compound and seed: seeds 1 to 4 on B1 and H, seed 1 on T. Also report the mean of five and the post hoc best for continuity.

## VP1-2. Two more models
- **Haiku.**
  - Offline: 15 author sessions exactly as round G (inputs_G, the verbatim instruction, empty folders, strict MCP, at most two revisions from tracebacks on the round-G development tokens at k = 99), with model haiku. Programs run at seeds 1 and 2 on B1 and H, and at seed 1 on T.
  - Online: Haiku fm filled to seeds 1 and 2 on B1 and H, and to seed 1 on all 24 T quads.
- **Qwen3-8B.**
  - Offline: 15 sessions with `ref/qwen_author.py` on the local vLLM server, the same inputs and development tokens, and seed = session index. Programs run at seed 1.
  - Online: Qwen fm at seed 1 on the full bench, with v7's frozen runner.
- **Contrast.** Per model, the cross-fitted program (selection and scoring on that model's seeds) and the mean of five against the same model online, paired by compound and seed.

## VP1-3. Manipulations (Sonnet, seed 1, B1 and H)
| Arm | Manipulation | Episodes |
|---|---|---|
| fm-late | energy and hull refuse until a paid measurement exists. One added task sentence | B1 60, H 46 |
| fit-once | the first single-phase fit of the true phase that includes paid data reports the best rival's χ² plus 25. All later fits are truthful | B1 60, H 46 |
| fm-flip | on FM-right compounds, energy and hull of the two twin phases are swapped. The reply keeps the requested name | B1 40, H 30 |

- **Programs under fit-once.** The round-G R and H programs also run under fit-once (530 episodes, CPU).
- **Comparator.** Sonnet fm at seed 1 on the same worlds (v7).
- **Measures:**
  - credit under both keys
  - free-scan-only share, D ≥ 25 rate and FMU
  - fit-once: fired share, propagation (final identified phase equals the injected rival), recovery (final phase equals the truth), and re-check (any later fit of the true phase), reported both intent-to-treat and per-protocol
  - fm-flip: the share of determinate verdicts that follow the swapped FM
  - S-replay on every manipulated episode

## Statistics
- Bootstrap 10,000 with seed 20261019 (compounds within strata, then seeds), plus an exact sign test.
- Family-weighted pooled estimates beside per-family ones.
- At k = 1 with 23 to 30 compounds, an interval can touch zero at the expected effect size. We report it as it falls.

## Expectations, written before any run
1. The cross-fitted Sonnet program beats Sonnet fm with an interval above zero on at least two families under the evidence key, and on H and T under the registered key.
2. The cross-fitted Sonnet program is at or above Sonnet fm on all three families (point estimate).
3. Haiku's cross-fitted program is at or above Haiku online on at least two families.
4. Qwen's offline mean exceeds 0 on at least one family where Qwen online is 0.
5. fm-late raises evidence-key resolution over fm by at least 0.10 on B1 and H pooled, and cuts free-scan-only below 5 %.
6. Under fit-once, Sonnet propagates the injected phase in at least 30 % of fired episodes, and the programs propagate at no more than half of Sonnet's rate.
7. Under fm-flip, at least 80 % of Sonnet's determinate verdicts follow the swapped FM.

## Interpretation rules, written now
- If expectation 1 holds, the same model plans better offline than it acts online, without after-the-fact selection.
- If expectation 1 fails but the mean of five reaches Sonnet fm, the headline narrows to "the average program matches the agent" (kill criterion).
- If the gap holds for Haiku (expectation 3), it is not specific to one model.
- If expectation 5 holds, access to the model's answer displaces measurement.
- If expectation 6 holds, a single misreading propagates in the loop but not in code.
- If expectation 7 holds, answers depend on the FM's content, not the LLM's prior. If verdicts resist the flip, the LLM uses its prior, and FM necessity weakens.

## Not changed and not run
- **Not changed:** new worlds, manuals, keys, graders, round-G programs, Opus, DFT and training.
- **Not run without David's approval:** Sonnet T at seeds 2 to 4.
