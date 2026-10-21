# v9 log

## V9-0 (2026-10-19) — v9 opened and pre-registered
Fresh clone `~/Documents/harbor-v9` from `https://github.com/colpark/19C_MAT_easy.git`, branch
`v9/2026-10-19` cut from `a1751aaff` (`v6 V6-14`, the tip of `v6/2026-10-13`), folder `v9/`.
`v9/PREREG.md` holds David's prompt verbatim and is pushed before any data is fetched.
Kits are **not** installed. No GPU, no compute. Working data directory `~/v9_data`.

### Node reachability, one check each
| Node | Address | Reached | Hardware | Route |
|---|---|---|---|---|
| A1 (this host) | `192.168.100.10` / `130.199.95.35`, `spark-112b` | **yes**, local | 20 cores, 119 GiB, NVIDIA GB10 | local |
| A2 | `192.168.100.11`, `spark-0b70` | **yes**, ssh key, no password | 20 cores, 119 GiB | ssh from A1 over the private subnet |
| B1 | `130.199.95.15`, `wcs-180522` | **yes**, ssh key, no password | 20 cores, 121 GiB, NVIDIA GB10 | ssh from A1 over the routable network |
| fourth node | `192.168.101.11` | **no** — `Connection timed out` on port 22 from B1, and not routable from A1 | unknown | none found |

B1 displays a US Federal / BNL authorised-use banner on login. Access is via the account
owner's own key. **B1's GPU was not queried, touched or signalled; v9 needs no GPU.**

### V9-X1 — how hard rule 2 is read, and it binds the builder
Hard rule 2 forbids FM calls and **LLM contact** with any candidate peptide, sequence or record.
A Claude Code session is an LLM, so the rule binds the builder directly, not only its tool calls.
Standing consequence for all of v9:
- Record-level data (sequences, affinities, class labels) is **never printed into the session
  context**. All per-record handling is done by code; only aggregate counts are read back.
- Data files are fetched with `curl`/`wget` and never through a page-summarising fetch tool,
  which would pass the records through a language model. Page-summarising fetches are used only
  for landing pages, licence text and DOI metadata, and only where records cannot be present.
- `v9/data/twins.json` is written by code and is not read back by the builder.
This is recorded as a deviation because it constrains how the audit is carried out, though it
follows from the rule rather than departing from it.

### V9-X2 — the node list was reconstructed, not read
The prompt names four nodes. The node list lived in v8's records, which v9 may not read, so the
nodes above were identified by probing the private subnet (`192.168.100.10` to `.14`) and by
reading ssh targets out of the shell history on A1 and B1. Three nodes answered. If the fourth
node is something other than `192.168.101.11`, its address needs to come from David.

## V9-1 (2026-10-19) — five candidate datasets
`v9/data/SOURCES.md` and `v9/data/FETCH_SHEET.md`. Primary dataset acquired via Europe PMC's
supplementary-files endpoint after both pubs.acs.org (403) and pmc.ncbi.nlm.nih.gov (reCAPTCHA)
refused. Parse independently validated: 1,720 rows, all unique, all 10-mers, zero unparsed
10-mer lines, median intensity 207,584 against the paper's stated 207,500 cutoff, SI class equals
`intensity > 207500` on 1720/1720 rows. **V9-E1**: the RSC Adv. 2023 data availability statement
is not satisfied — the repository holds only the R script, and the `Q14.csv` it reads is absent.
B1 has no external DNS resolution, so all fetching runs from A1 or A2.

## V9-2 (2026-10-19) — the twin count
`v9/data/TWIN_COUNT.md`, pairs in `v9/data/twins.json`. 1,720 peptides, monoisotopic masses
820.356 to 1741.784 Da, unimodal and peaked at 1200–1250 Da. Twins at 1.0/0.5/0.1/0.05/0.01 Da:
799/420/271/134/24, with K strata 122/70/54/37/6. Nominal-mass clustering gives the tolerance
ladder a plateau: 0.5 to 0.1 Da removes only 25% of near-isobaric pairs. **Zero** permutation or
exact-mass twins, so no pair is unresolvable in principle. Panel `count(W) - count(R)` is 0.885
accurate over all 860 quartile peptides and weakens as tolerance tightens. The source publishes
**no replicate error**. Dataset 2's thesis holds 12 dodecapeptide sequences, not a dataset;
datasets 3 to 5 carry no graded peptide affinity.

## V9-3 (2026-10-19) — verdict, all three gates passed
`v9/VERDICT.md`. Gate T passed 9x over at its own tolerance and passes under both class
definitions. Gate D passed on its second clause only, with the first clause untested because no
replicate error is published anywhere in the acquired source. Gate A passed. Six named blockers,
led by the CC BY-NC-ND NoDerivatives licence on the benchmark-carrying dataset and by
contamination risk. Nothing built, no compute, no LLM contact with any record, $0.

## V9-X3 (2026-10-19) — audit of datasets 6 and 7, after the pre-registered stop
Run at David's instruction, same rules. `v9/data/AUDIT_6_7.md`. **Neither is a second truth
table.** Dataset 6 (silver array, IJMS 2020, CC BY 4.0) has 22 distinct 10-mers in its whole full
text, all at ranks 11–180 of dataset 1, none in the bottom quartile. Dataset 7 (Nanoscale Adv.
2019, CC BY-NC 3.0) Table S1 is **exactly ranks 1–200 of dataset 1** with computed MW/pI/GRAVY
rather than measurements; its Table S2 carries a genuinely independent colour measurement on 40
peptides in 4 classes of 10, but **0 of 780 pairs fall within even 1.0 Da**, so Gate T fails at
every tolerance. Gate T fails structurally on both: a set with no bottom-quartile member cannot
produce a twin. Five publications in this cluster rest on one array, so no second truth table is
available from this group at all. The audit did quantify **contamination exposure** of dataset 1:
about half of every twin set has its strong member re-published elsewhere as a known top-200 high
binder, never its weak member. Excluding every exposed twin still leaves **136 twins and 32 in the
K stratum at 0.1 Da**, so Gate T holds on a contamination-hardened set. **V9-E2**: my
`probe_table.py` counted only the first match per line and under-counted single-line XML; replaced
by `probe_tokens.py`. Dataset 1's numbers are unaffected and remain validated at 1720/1720.

## V9-4 (2026-10-19) — reserved split, dev pairs, null baselines
`v9/split/SPLIT.md` and `DEV_PAIRS.md`, pushed before the first FM call. Salted-hash split:
dev 538 (0.3128), reserved 1,182 (0.6872); the 0.3128 is hash-partition noise on a threshold fixed
at 0.30 beforehand and was **not** adjusted after the counts were seen. 17,955 dev pairs,
16,291 E / 1,664 K. FM subset 120 peptides chosen FM-blind by a second salt; 3,600 pairs, 323 K
over only **82 peptides**, which is the bootstrap denominator. **Two of three nulls are
informative**: net charge 0.674 CI [0.539, 0.806], GRAVY 0.691 CI [0.547, 0.813]; mass 0.560 CI
[0.422, 0.707]. Null direction pre-declared as the better of the two orientations, ties at 0.5.

## V9-5 (2026-10-19) — cost measured, production NOT run
`v9/fm/FM_DEV.md`. Head **oc20**, the only UMA head trained on molecular adsorbates on metal
slabs. Slab `fcc111('Au',(14,10,4))`, 560 Au, 40.39 x 24.99 A, bottom 2 of 4 layers fixed; the
longest ESMFold conformer is 29.3 A. ESMFold pLDDT mean 0.690 (0.665-0.727), disclosed as moderate.
12 of 12 conformers written, **zero validity refusals**. **V9-E3**: the first timing run capped at
200 steps and **6 of 6 evaluations hit the cap** (fmax 0.068-2.209), making its 78 s per
evaluation a lower bound; the converged cost measured with a high cap is **LBFGS 434 steps,
167.1 s**, while **FIRE failed to converge in 800 steps**. Projection: **167.1 GPU h at 120
peptides, 83.6 at 60**, against the 8-hour limit, so the second branch of the stop rule applies
and production was not run. Rigid single point costs 0.398 s, giving 0.40 GPU h for the full
120 x 30 grid.

## V9-6 (2026-10-19) — verdict 2: gates not reached
`v9/VERDICT_2.md`. **Gates M and N NOT REACHED**, neither passed nor failed: no FM accuracy
exists. Four costed options recommended to David, led by rigid single points (0.40 GPU h) then
3 conformers x 3 placements on 60 peptides (25.07 GPU h). Reserved split still unseen by any
model. **V9-X4**: existing interpreter reused read-only; UMA and ESMFold weights copied into
`~/v9_data` so no cache write lands outside v9's roots.

## V9-7 (2026-10-20) — rung 1: rigid single points. Both gates FAILED, and not a verdict.
`v9/fm/FM_RUNG1.md`. Pre-registration first: `v9/PREREG_3.md` (David's note verbatim) and
`v9/fm/PREREG_3_DECISIONS.md` pushed **before any FM call**, fixing Gate N's "best descriptor"
as **net charge at pH 7** (0.7229 on the 323 FM-subset K pairs the gate is scored on) with GRAVY
secondary, the subset sizes, and rung 2's selection **rule B** — all before rung 1 ran. Conformers:
120 peptides, 356 of 360 written, **validity check refused 4**, all conformer 0 (raw ESMFold),
heavy-atom pairs 0.70–0.99 Å; no peptide lost all three. pLDDT mean 0.692 range 0.572–0.878, so
iteration 2's 4-peptide range of 0.665–0.727 was **four times too narrow**. Slab relaxed once,
8 steps, 15.4 s, fmax 0.035. 3,916 single points at **0.3585 s, 0.39 GPU h against 0.40
projected** — the first estimate in three iterations to hold. **Gate M FAILED**: FM 0.3901 CI
[0.1996, 0.5822]. **Gate N FAILED**: primary 0.2571 CI [0.0500, 0.4909], excluding 0.5 **from
below**. FM − net charge −0.3328 [−0.5985, −0.0897], entirely below zero: significantly worse
than a one-line descriptor. Spearman(E_ads, intensity) **+0.1171**, the wrong sign. As David
wrote in advance, a rigid score's failure is **not a verdict on the model**. **V9-E5**:
`fm_gates.py` called the exclusion-from-below a PASS and mislabelled a wholly-negative interval
as "spans zero" — numbers right, labels wrong, fixed to record the side of every exclusion; the
pre-registered direction was **not** flipped, which would have turned 0.2571 into 0.7429.
**V9-X5**: the first conformer launch died with `CUDA error: out of memory` at `model.cuda()`
with 108 GB host free and the GPU at 2 percent; an identical relaunch succeeded, unexplained,
and it motivated `--resume`. Post hoc and labelled: the rigid score correlates with peptide size
the wrong way for adsorption (Spearman +0.1964) but accuracy is ~0.39 in **every** size stratum,
so the artefact is real and does not explain the result; and `gate_m_power.py` finds the
bootstrap unit is the peptide, so the bar is ~0.65 at 195 peptides, 0.70 at 82, **0.75 at 54**.

## V9-8 (2026-10-21) — rung 2: converged relaxations. Both gates FAILED. Not a power failure.
`v9/fm/FM_RUNG2.md`. 59 of the pre-registered 60 peptides (30 top, 29 bottom; the 25 GPU-hour
ceiling fired at a peptide boundary and `P119` was not run). **704 relaxations at 128.19 s each,
25.069 GPU h against 25.000 approved** — a disclosed 0.28 percent overshoot, because the budget
check stops before a peptide and cannot stop mid-peptide. 526 of 528 complex relaxations converged
to fmax ≤ 0.05; **2 cap hits** at exactly 1000 steps (`P011` 0.1054, `P106` 0.1569). Zero validity
refusals. **Gate M FAILED**: FM **0.5698** CI **[0.3529, 0.7716]** on 265 K pairs over 53 peptides.
**Gate N FAILED**: primary 0.5306 CI [0.1579, 1.0000] (n = 49 / 32, 34 ties excluded); secondary
0.6579 [0.4245, 0.8455]. **The failure is not a power failure**: on the identical pairs, peptides
and estimator, **net charge at pH 7 scores 0.7509 CI [0.5312, 0.9196] and clears the bar the FM
does not**, and the FM ties GRAVY to four decimals. David's three requirements: (1) **1 of 528**
relaxations ended above its own trajectory minimum, by 0.015 eV, and re-scoring on trajectory
minima reproduces every number — the non-monotonic **force** path is real and not UMA-specific,
but does not reach the **energy** path; (2) within-peptide SD median **2.330 eV** against
between-peptide SD of the minima **3.319 eV**, ratio **0.70**, so **within does not swamp between**
and stop state 3 is not triggered; (3) **4 of 59 undetermined** (P004, P020, P025, P117), and
dropping them, the cap-hit peptides, or both leaves 0.5785 / 0.5630 / 0.5714 with **both gates
failing in every variant**. Rung 1 was a poor proxy, as David said in advance:
Spearman(rigid, relaxed) over the same 59 peptides is **+0.2071**, minima moved from −1.47 to
−6.92 eV median, and the size artefact weakened from +0.1964 to +0.1582. Spearman(E_ads,
intensity) **+0.0717**, still the wrong sign; AUC 0.4678; dev E-pair accuracy 0.4231.

## V9-9 (2026-10-20) — MACE-MH-1 timed. Nothing more, as instructed.
`v9/fm/MACE_RATE.md`. `mace-torch 0.3.16`, checkpoint `mace-mh-1.model` (59,208,139 bytes,
sha256 `a522eb7f…cad3be47`), head **`oc20_usemppbe`**, installed `--no-deps` into
`~/v9_data/macenv` reusing v8's torch 2.13.0+cu130 read-only via a `.pth` file; **nothing written
into v8env**. On the identical 647-atom system: UMA single point 0.3585 s, relaxation 434 steps /
167.1 s; MACE float64 1.1525 s, 230 steps / 254.2 s; **MACE float32 0.4804 s, 238 steps / 102.1 s
— 1.64× cheaper per converged relaxation**, slower per step but converging in 46 percent fewer
steps. Scaled onto rung 2's realised cost, a rung-2-shape MACE float32 run is **about 15.3 GPU h**.
MACE's fmax path wanders too (0.0721 at 150, 0.0910 at 200, 0.0482 at 238), so the force-path
behaviour is LBFGS on this class of system, not a UMA quirk. **V9-E4**: my first MACE "single
point" of 0.0005 s was an ASE `check_state` cache hit; the first fix still had one because
scrambled Sobol's placement 0 equals the cold call's structure, so the loop now starts at
placement 1.
