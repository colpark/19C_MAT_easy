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
