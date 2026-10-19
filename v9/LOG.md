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
