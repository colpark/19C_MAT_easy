# vP.1 usage

Claude runs as Claude Code processes on David's subscription; no paid API call (I11), no Opus, no usage credits. API-equivalent cost is read from each transcript's `total_cost_usd`. Qwen3-8B runs locally at no cost.

| date | batch | model | episodes or sessions | API-equivalent $ | note |
|---|---|---|---|---|---|
| 2026-10-22 | VP1-0 setup | none | 0 | 0.00 | no agent episode or author session; this builder session runs on the subscription |
| 2026-10-22 | vp1-3 smoke (fm-late, fit-once, fm-flip; 4 each) | sonnet (claude-sonnet-5-5) | 12 episodes | 1.44 | all answered |
| 2026-10-22 | vp1-3 main (270; with the smoke 282 episodes in all) | sonnet (claude-sonnet-5-5) | 270 episodes | 30.76 | 282 of 282 answered; batch total $32.20 |

Running total: $32.20 API-equivalent (Sonnet 282 episodes; the Haiku and Qwen batches are added when they finish); $0 actual.
