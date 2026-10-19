# v7 subscription use (API-equivalent, V7-X8)

Claude Code reports `total_cost_usd` per episode. These runs use the subscription, so the figure is an API-equivalent size, not money spent; spend is $0.
Qwen3-8B runs on local vLLM and has no cost.

| family | batch | episodes with a result | of them at k = 1 | API-equivalent USD |
|---|---|---|---|---|
| H | Sonnet noprior, fm (k 1-4; gates use k 1) | 369 | 92 | 30.00 |
| H | Haiku noprior, fm | 36 | 36 | 0.62 |
| H | Sonnet fm-planner | 16 | 16 | 1.53 |
| T | Sonnet noprior, fm | 145 | 145 | 21.07 |

**Total so far:** 53.22 USD API-equivalent.
