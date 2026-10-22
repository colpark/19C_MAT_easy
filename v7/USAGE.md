# v7 subscription use (API-equivalent, V7-X8)

Claude Code reports `total_cost_usd` per episode. These runs use the subscription, so the figure is an API-equivalent size, not money spent; spend is $0.
Qwen3-8B runs on local vLLM and has no cost. Scripts (S-broad, S-neutron, S-plan, S-llm programs) and S-replay use no LLM.

| family | batch | episodes with a result | of them at k = 1 | API-equivalent USD |
|---|---|---|---|---|
| H | Sonnet noprior, fm (k 1-4; gates use k 1) | 369 | 92 | 30.00 |
| H | Haiku noprior, fm | 36 | 36 | 0.62 |
| H | Sonnet fm-planner | 16 | 16 | 1.53 |
| T | Sonnet noprior, fm | 195 | 195 | 28.07 |
| T | Haiku noprior, fm | 96 | 96 | 2.17 |
| T | Sonnet fm-planner | 50 | 50 | 6.51 |
| H | Sonnet fm-hint (V7-F4) | 46 | 46 | 3.94 |
| T | Sonnet fm-hint (V7-F4) | 96 | 96 | 10.80 |
| B1 | Sonnet fm-hint (V7-F4) | 60 | 60 | 4.70 |
| T | fresh T Sonnet fm + fm-hint, first run on node A2:8784 (voided, V7-E5 and V7-E6; used, not analysed) | 267 | 267 | 26.27 |
| T | fresh T Sonnet fm + fm-hint, rerun on node A2:8781 (V7-G1) | 240 | 240 | 32.94 |
| R, H, T | S-llm authoring sessions, kept (V7-F3; sessions, not episodes) | 28 | - | 4.37 |
| R, H, T | S-llm authoring sessions discarded under V7-E3 | 5 | - | 1.30 |
| R, H, T | S-llm round G authoring sessions (V7-G2; sessions, not episodes) | 29 | - | 4.81 |

**Total so far:** 158.03 USD API-equivalent.
