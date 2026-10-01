# OA harvest LOG

Script: oa_harvest.py (sha bd3ccd23f9e38d97). Host A spark-112b (130.199.95.35). python 3.12.3, requests 2.31.0, pdftotext version 24.02.0. Contact email in User-Agent and Unpaywall requests: <owner email> (owner go-ahead 2026-09-30).

- 2026-09-30 21:50:08 EST [spark-112b] targets: 16487 papers, 16487 unique DOIs (DOIs from MatMech data.json)
- 2026-09-30 21:54:16 EST [spark-112b] calibrate: 249 DOIs, now {'closed': 163, 'bronze': 12, 'hybrid': 21, 'green': 22, 'gold': 31} (sample: closed 163, gold 31, hybrid 21, green 22, bronze 12); mismatches 0: []
- 2026-10-01 02:30:31 EST [spark-112b] download shard 0: 1839 papers, 1839 to do, 8 workers
- 2026-10-01 02:43:04 EST [spark-112b] download shard 0 done: {'no_url': 609, 'http_error': 584, 'not_pdf': 43, 'ok': 415, 'title_mismatch': 20, 'robots_disallowed': 168}
- 2026-10-01 06:30:09 EST [spark-112b] manifest: 16487 rows; open access 3742; download {'no_url': 1233, 'http_error': 1180, 'ok': 869, 'robots_disallowed': 327, 'not_pdf': 89, 'title_mismatch': 44}; closed 12745
- 2026-10-01 06:30:10 EST [spark-112b] report written: OA 3742/16487, downloaded 869

## Host B log (lookups, plan, shard 1)
- 2026-10-01 02:54:26 UTC [wcs-180522] lookup: 16487 targets, 16487 to query
- 2026-10-01 07:29:24 UTC [wcs-180522] lookup pass 1 done: 0 errors; retrying once
- 2026-10-01 07:29:24 UTC [wcs-180522] lookup done: 0 DOIs still failing after one retry (lookup_errors.json)
- 2026-10-01 07:30:14 UTC [wcs-180522] plan: {'oa_no_url': 1233, 'closed': 12745, 'oa_with_url': 2509}; shard_0 1839, shard_1 1903
- 2026-10-01 07:30:14 UTC [wcs-180522] download shard 1: 1903 papers, 1903 to do, 8 workers
- 2026-10-01 07:41:24 UTC [wcs-180522] download shard 1 done: {'no_url': 624, 'http_error': 596, 'ok': 454, 'robots_disallowed': 159, 'title_mismatch': 24, 'not_pdf': 46}
- 2026-10-01 06:33:50 EST [spark-112b] PDFs mirrored both ways (rsync --ignore-existing): host A 415 -> 869, host B 454 -> 869; all 869 verified against oa_manifest.csv sha256 on both hosts
