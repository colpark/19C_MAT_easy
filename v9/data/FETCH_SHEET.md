# V9-1 fetch sheet: what v9 could not retrieve, and exactly what is needed

## 1. Biomolecular Adsorption Database (dataset 3)
- **Where:** `https://ieee-dataport.org/documents/biomolecular-adsorption-database-bad`, doi `10.21227/ykx9-2m83`.
- **What is needed:** the page states `LOGIN TO ACCESS DATASET FILES`. The file is listed as
  "BAD Dataset (Size: 298.63 KB)", format `*.csv (zip); *.xlsx (zip)`.
- **Why v9 stopped:** v9 holds no IEEE DataPort account, will not create one, and hard rule 5
  forbids writing any credential anywhere. An IEEE member or subscriber account is required.
- **Who can get it:** anyone with an IEEE DataPort login, in one click. David, or anyone with an
  IEEE account, can download the zip and drop it in `~/v9_data/ds3_raw/`.
- **Worth it?** Low priority. BAD holds **protein** adsorption records, not a peptide library, so
  it cannot supply mass-spectrometry twin pairs whatever its contents.

## 2. The RSC paper's own quartile file `Q14.csv` (V9-E1)
- **Where it should be:** `https://github.com/jijanairo/sequencerules`, per the RSC Adv. 2023
  data availability statement.
- **What is there instead:** only `ArulesCBA`, the R script, which reads `Q14.csv`.
- **Why it does not block v9:** the continuous intensities in the ACS Omega SI reproduce the
  quartile split directly, and v9 computes it. The file is wanted only to confirm that v9's
  quartile boundaries match the ones the RSC authors used.
- **Who can get it:** the corresponding author, `jose.isagani.janairo@dlsu.edu.ph`. One email.

## 3. Tanaka et al. 2017 original supplementary data
- **Where:** Acta Biomaterialia 49, 495–506, doi `10.1016/j.actbio.2016.11.037` (Elsevier).
- **What is needed:** the original array data, specifically **whether replicate measurements and
  their spread are reported per peptide**. Gate D wants the class separation against the source's
  own replicate error, and the ACS Omega SI carries a single intensity per peptide with no error.
- **Why v9 stopped:** paywalled, and v9 spends $0. Not attempted beyond the DOI.
- **Who can get it:** anyone with an institutional Elsevier subscription. **This is the one fetch
  that would change a gate**, so it is the one worth doing.

## 4. Host B1 has no external egress
- `wcs-180522` cannot resolve any external hostname. Every external fetch must run from A1 or A2.
  Not a blocker for v9; recorded so no later iteration wastes time on it.
