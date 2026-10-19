# V9-1 candidate datasets: what was acquired, from where, and what truth it carries

All retrievals on **2026-10-19**, from host A1 unless stated. Every file fetched with `curl`;
no record-bearing page or file was passed through a page-summarising fetch tool, and no
record-level content has entered the builder's context (V9-X1). Files live under `~/v9_data/`.

## Fetch routes actually observed

| Route | Result |
|---|---|
| A1 → github.com, raw.githubusercontent.com, api.github.com | works |
| A1 → zenodo.org (API and file content) | works |
| A1 → www.ebi.ac.uk (Europe PMC REST) | works |
| A1 → i.uestc.edu.cn | works |
| A1 → digital.lib.washington.edu | works |
| A1 → ieee-dataport.org | page works, dataset files need a login |
| A1 and A2 → pmc.ncbi.nlm.nih.gov `/articles/instance/.../bin/*.pdf` | **blocked by reCAPTCHA** (`Checking your browser`) |
| A1 → pubs.acs.org supplementary file | **HTTP 403** |
| A1 → `www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi` | **HTTP 404**, endpoint retired |
| B1 (`wcs-180522`) → any external host | **no DNS resolution**, no external egress |
| A1 → eutils.ncbi.nlm.nih.gov efetch | works |

**The route that worked for the primary dataset** was Europe PMC's supplementary-files endpoint,
`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9089360/supplementaryFiles`, after both the
publisher and the PMC article route refused. That is the route to reuse.

---

## Dataset 1 (primary): gold-binding decapeptides

**Two papers, one underlying measurement, and the prompt's description needs one correction.**

| Field | Value |
|---|---|
| Measurement source | Tanaka M., Hikiba S., Yamashita K., Muto M., Okochi M. *Array-Based Functional Peptide Screening and Characterization of Gold Nanoparticle Synthesis.* Acta Biomater. 2017, **49**, 495–506, doi `10.1016/j.actbio.2016.11.037` |
| Dataset as distributed | Supporting Information of Janairo J. I. B. *A Machine Learning Classification Model for Gold-Binding Peptides.* ACS Omega 2022, **7**(16), 14069–14076, doi `10.1021/acsomega.2c00640` |
| File | `ao2c00640_si_001.pdf`, 210,002 B, sha256 `74afc51da52f5147db7753034391de519f5be32ee5556d952b2d68226e65da67` |
| Route | Europe PMC supplementary files for `PMC9089360` |
| Licence | **CC BY-NC-ND 4.0** (the ACS Omega article; the SI carries the article's terms) |
| Parsed to | `~/v9_data/ds1_parsed/ds1.csv`, 39,267 B, sha256 `2ccc27162f2d85bfdb9231cdf7f5111ed4b9301c3b1a0d315cf9d50b96247401` |
| Truth carried | **1,720 decapeptides, each with a continuous peptide-array binding intensity and a binary class label** |

**The 1,720 figure is right and the quartile description belongs to a different paper.** The
prompt attributes ~1,720 decapeptides "divided into quartiles" to the RSC Adv. 2023 paper
(`10.1039/d3ra04269c`). That paper is Janairo, *Sequence rules for gold-binding peptides*, and it
used only **860** of the peptides — the first and fourth quartiles — as its two classes. The full
1,720-peptide table with its continuous intensities is in the **2022 ACS Omega** SI, where the
labels are a **median split** at intensity 207,500, not quartiles. v9 therefore takes the
continuous intensities from the ACS Omega SI and **computes the quartiles itself**, which is what
the RSC paper did and which is what the twin count needs.

**V9-E1 — the RSC paper's data availability statement is not satisfied.** It states "The dataset
and R script used in the study are freely available at https://github.com/jijanairo/sequencerules".
That repository contains exactly **one** file, `ArulesCBA` (1,607 B, sha256
`46c6ae2fa0c3d94b477cbb58a6056433a90b42d34ffb830a2312be81eb64abed`), which is the R script. The
script's second statement is `dataset <- read.csv("Q14.csv", header = TRUE)` and **`Q14.csv` is
not in the repository**, nor is any other data file. The quartile dataset as the RSC paper used it
is not published anywhere v9 could find. This is why v9 rebuilds the quartiles from the ACS Omega
intensities instead of using the authors' file.

**Independent validation of the parse.** 1,720 rows parsed, 1,720 unique sequences, all of length
10, and **zero** lines containing a 10-residue token that failed to parse. The parsed median
intensity is **207,584** against the paper's stated cutoff of **207,500**, and the SI's own class
label equals `intensity > 207500` on **1720 of 1720** rows. The parse is therefore faithful and
the SI label is confirmed to be the median split.

| Quantity | Value |
|---|---|
| intensity range | 203 to 384,446 (arbitrary array units) |
| Q1 / median / Q3 | 130,053 / 207,584 / 256,724 |
| mean / sd | 191,641 / 84,261 |
| SI class counts | A 861, B 859 |

---

## Dataset 2 (backup): MoS2-binding dodecapeptides

| Field | Value |
|---|---|
| Source | Jain S. S. *Predictive modelling of directed evolution for de-novo design of solid binding peptides.* MSc thesis, University of Washington, 2021, handle `1773/47383` |
| File | `thesis.pdf`, 67 pages, 2,249,514 B, sha256 `6eccd335bce1b84401d87691b53dd3d6467216d2b4cea348c5708cb1986638ac` |
| Route | `digital.lib.washington.edu/researchworks/bitstreams/176ad55e-.../download`, now open (its one-year UW embargo has expired) |
| Licence | ResearchWorks deposit; thesis author retains copyright, open access for research use |
| Truth carried | to be determined in V9-2; the thesis trains models on 12-residue MoS2-binding peptides |

## Dataset 3 (backup): Biomolecular Adsorption Database (BAD)

| Field | Value |
|---|---|
| Source | Cho M., Mahmoodi Z., Shetty P., Harrison L. R., Arias Montecillo M., Perumal A. S., Solana G., Nicolau D. V. Jr., IEEE DataPort, doi `10.21227/ykx9-2m83`; origin paper *Lab Chip* 2009, doi `10.1039/b813475h` |
| **Not acquired** | the dataset page says **`LOGIN TO ACCESS DATASET FILES`** (BAD Dataset, 298.63 KB, `*.csv (zip); *.xlsx (zip)`) |
| Mirror tried | `bionanoinfo.com/bad/` returns a description page with no direct file link; the original `dbweb.liv.ac.uk/bad/` is long dead |
| Truth it should carry | 865 protein adsorption records with protein, surface and fluid descriptors and a surface concentration |

v9 holds no IEEE DataPort credential and will not create one, so this source goes to
`FETCH_SHEET.md`. It is in any case **protein adsorption, not a peptide library**, so it cannot
supply mass-spectrometry twins.

## Dataset 4 (backup): Biopanning Data Bank (BDB)

| Field | Value |
|---|---|
| Source | BDB, HLAB, UESTC, `i.uestc.edu.cn/bdb`; release **2023-10-13** |
| Files | `bdb_full.zip` 1,935,521 B sha256 `18db0d4b0104a07c8c02b5e5f9d8c5fad80a49d7039838cf54c212963b56377b` (8 files, 9,316,954 B unpacked, including `mimoset.csv` and `mimoset.xml`); `benchmark_data.tgz` 22,934 B sha256 `b3357fb30e04af3786b9c1e5ab6e35b673242ad8f662c22d8bf492c0cb307ed8` (one `benchmark_data.xml`) |
| Route | `i.uestc.edu.cn/bdb/index.php/site/download` and `/bdb/files/benchmark_data.tgz`, both open, no login |
| Licence | **none stated.** The download page offers only a "Citation" heading. Terms of use are not published |
| Truth carried | 3,682 biopanning datasets from 1,771 papers, 34,078 peptide sequences, across many targets including inorganic ones |

BDB records which peptides were **selected** by phage or cell-surface display against a target.
That is a presence/enrichment record, not a graded affinity, so whether it can supply a truth
*class* at all is a V9-2 question.

## Dataset 5 (breadth check): protein adsorption to carbon nanotubes

| Field | Value |
|---|---|
| Source | Zenodo `10.5281/zenodo.5641450`, *Datasets for Supervised Learning Model Predicts Protein Adsorption to Carbon Nanotubes*, published 2021-11-02 |
| Licence | **CC BY 4.0** — the most permissive terms of any candidate |
| Files | 24 `.xlsx`; two fetched for inspection: `MS Proteomic Datasheet - FINAL.xlsx` 107,239 B sha256 `320260e8f4d4157b5010149ce125ad92b4c1b36396f58bc26547e25d2e33fb35`, `table1_order_data.xlsx` 10,233 B sha256 `4e6552f56683ad7e46327d0c01b68fa9217bc8fb42a5eaa890d2e2cef2c97b35`; record metadata `record.json` sha256 `383e225400c87ccd4dbaa37ab61374b32efed2d78d7e5c71b82b6e9f2a0a3021` |
| Route | `zenodo.org` API, open |
| Truth carried | LC-MS/MS proteomic abundance of plasma and CSF proteins in the corona of ssDNA-wrapped SWCNTs |

This is **whole proteins**, not a designed peptide library. Its adsorbates are hundreds of
residues long, so the mass-spectrometry twin construction in V9-2 does not apply to it: two
different proteins are never near-isobaric at any useful tolerance, and their identification does
not go through an MS1 mass ladder. Recorded for breadth; not a benchmark candidate.

## Summary

| # | Dataset | Acquired | Licence | Peptide library with a graded affinity? |
|---|---|---|---|---|
| 1 | Gold decapeptides (ACS Omega SI) | **yes** | CC BY-NC-ND 4.0 | **yes, 1,720 with continuous intensity** |
| 2 | MoS2 dodecapeptides (UW thesis) | yes, PDF | author copyright, open access | to be determined in V9-2 |
| 3 | BAD | **no**, login required | not reached | no, protein adsorption |
| 4 | BDB | yes | **none stated** | selection records, not graded affinity |
| 5 | CNT protein corona | yes, 2 of 24 files | CC BY 4.0 | no, whole proteins |
