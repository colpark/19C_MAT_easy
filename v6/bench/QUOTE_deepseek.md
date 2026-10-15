# V6-12 quote: DeepSeek V4.1 Flash on OpenRouter beside Qwen3-8B (for David's approval)

**No API call has been made.** Nothing below used the OpenRouter API. The listed price could not be read without it: the public model page is rendered client-side, and the price listing is the API's `/models` endpoint. So the quote is the token estimate times a table of price points. **David: please confirm the listed input and output price per million tokens, or allow one unauthenticated read of OpenRouter's public `/api/v1/models` listing (no key, no charge) so I can fill it in.**

## Episodes

300 episodes, seeds world × 100 + k as for Qwen:
- v6-active-noprior and v6-active-fm: 30 compounds × 2 twins × k = 2, 240 episodes.
- v6-active-fm-planner: 30 compounds × 2 twins × k = 1, 60 episodes.

## Tokens per episode, measured on the B1 transcripts

| source | input tokens per episode (mean) | output tokens per episode (mean) | turns or tool calls |
|---|---|---|---|
| Qwen3-8B, this harness (`mcenv/run_qwen.py`; the whole conversation resent each turn) | 18,089 (no-prior), 29,596 (FM) | 3,224, 6,150 | 2.9, 4.7 turns |
| Sonnet, Claude Code (input includes Claude Code's own per-turn system and tool text) | 127,009 (no-prior), 121,375 (FM), 108,404 (planner); p90 about 170,000 | 2,871, 2,589, 2,283 | 10.5–12.0 tool calls |

- **Expected case.** DeepSeek runs the loop like Sonnet (10–12 tool calls), with Sonnet's per-episode input. That is an upper bound for this harness, which sends less fixed text per turn than Claude Code. I add 7,500 output tokens per episode for reasoning.
- **Low case.** It behaves like Qwen3-8B.
- **High case.** Sonnet's p90 input on every episode, with 15,000 output tokens each.
- **Provider caching** of the repeated prefix would lower all three; the table assumes none.

## Cost at price points (USD, 300 episodes)

| scenario | input Mtok | output Mtok | $0.10 / $0.40 per Mtok | $0.20 / $0.80 per Mtok | $0.30 / $1.20 per Mtok | $0.50 / $2.00 per Mtok |
|---|---|---|---|---|---|---|
| low (Qwen-like: 3-5 turns) | 7.2 | 1.41 | $1.28 | $2.56 | $3.83 | $6.39 |
| expected (Sonnet-like: 10-12 tool calls) | 36.3 | 3.07 | $4.86 | $9.72 | $14.58 | $24.29 |
| high (Sonnet p90 input, 15k output per episode) | 51.0 | 4.50 | $6.90 | $13.80 | $20.70 | $34.50 |

## Request

- **Approval.** One run of 300 episodes with a **hard cap of $25**. The runner (`bench/run_openrouter_b1.py`) keeps a running total of OpenRouter's billed `usage.cost` and sends no further request once the total reaches the cap. Any episode stopped by the cap is a harness void and is not graded.
- **What fits under the cap.** At up to about $0.30 / $1.20 per million tokens, the expected case is under $15 and the high case under $21. At $0.50 / $2.00 the expected case nears the cap. The cap then stops the run early, and I would report the episodes completed and ask before any further spend.
- **The key.** It stays an environment variable on host B, set by David or the operator in the shell (for example `! export OPENROUTER_API_KEY=...` in that session, or a file read by the shell profile outside the repository). It is never written to any file, log, transcript or commit; the runner reads it from the environment and sends it only as a request header.
- **Harness.** The Qwen3-8B runner with the base URL and model switched by configuration only: the same tools, manual, system prompt, structured answer, sampling, turn limit and timeouts. Two additions sit outside what the model sees: the authorization header and the spend accounting (`usage.include`). Any provider-side difference in tool-call format or reasoning fields will be logged as a deviation.
- **Compute.** The runner on host B, at 8 concurrent, against a fresh frozen copy of the B1 server code (0ca269b543eedec0), as for Qwen (V6-X20).

Stopped for approval.
